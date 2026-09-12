"""
FastAPI service wrapping the HealthSurge AI deterministic engine.

Run with:
    uvicorn main:app --reload --port 8000

From the healthsurge_ai/ directory.
"""
import sys
import os
import time
import math

# Ensure the src package is importable
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from src.simulator import Simulator
from src.policies import Policy
from src.forecast import RegressionForecast
from src.allocator import WorstDistrictProtectionAllocator
from src.anomaly import ZScoreAnomalyDetector
from src.evaluation import evaluate_policy
from src.config import DEFAULT_SEED, EVAL_HORIZON_START, EVAL_HORIZON_END, NUM_DISTRICTS

app = FastAPI(title="HealthSurge AI Engine", version="1.0.0")

# Allow calls from the Next.js dev server and Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────

class SimulateRequest(BaseModel):
    seed: int = DEFAULT_SEED
    randomize_surge: bool = False


class MonthlyResultItem(BaseModel):
    month: int
    district_index: int
    forecast: float
    actual_demand: int
    capacity: int
    allocation: int
    unmet_demand: int
    anomaly_score: float


class DistrictResultItem(BaseModel):
    district_index: int
    capacity: int
    total_demand: int
    total_forecast_error: float
    total_unmet: int
    service_utility: float


class SimulationResponse(BaseModel):
    seed: int
    status: str
    forecast_utility: float
    service_utility: float
    worst_district_utility: float
    total_unmet: int
    runtime_seconds: float
    district_results: List[DistrictResultItem]
    monthly_results: List[MonthlyResultItem]


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Liveness check."""
    return {"status": "ok", "engine": "HealthSurge AI v1.0"}


@app.post("/simulate", response_model=SimulationResponse)
def simulate(req: SimulateRequest):
    """
    Run one full simulation with the validated winning policy:
      RegressionForecast + WorstDistrictProtectionAllocator
    
    Returns metrics and per-district / per-month records.
    The policy NEVER receives future demand (enforced by the Simulator boundary).
    """
    t0 = time.perf_counter()
    try:
        sim = Simulator(seed=req.seed, randomize_surge=req.randomize_surge)
        policy = Policy(
            forecaster=RegressionForecast(),
            allocator=WorstDistrictProtectionAllocator(always_use_all=True),
            anomaly_detector=ZScoreAnomalyDetector(),
        )
        metrics, records = evaluate_policy(sim, policy)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {exc}")

    runtime = time.perf_counter() - t0

    # Build per-district aggregates
    district_demand: dict = {}
    district_error: dict = {}
    district_unmet: dict = {}
    district_capacity: dict = {}

    for r in records:
        d = r.district
        district_demand[d] = district_demand.get(d, 0) + r.actual_demand
        district_error[d] = district_error.get(d, 0.0) + abs(r.forecast - r.actual_demand)
        district_unmet[d] = district_unmet.get(d, 0) + r.unmet_demand
        district_capacity[d] = r.capacity  # fixed per district

    district_results = []
    for d in range(NUM_DISTRICTS):
        denom = max(district_demand[d], 1)
        su = max(0.0, min(1.0, 1.0 - district_unmet[d] / denom))
        district_results.append(
            DistrictResultItem(
                district_index=d,
                capacity=district_capacity[d],
                total_demand=district_demand[d],
                total_forecast_error=round(district_error[d], 4),
                total_unmet=district_unmet[d],
                service_utility=round(su, 6),
            )
        )

    monthly_results = [
        MonthlyResultItem(
            month=r.month,
            district_index=r.district,
            forecast=round(r.forecast, 4),
            actual_demand=r.actual_demand,
            capacity=r.capacity,
            allocation=r.allocation,
            unmet_demand=r.unmet_demand,
            anomaly_score=round(r.anomaly_score, 4),
        )
        for r in records
    ]

    return SimulationResponse(
        seed=req.seed,
        status="completed",
        forecast_utility=round(metrics["Uforecast"], 6),
        service_utility=round(metrics["Uservice"], 6),
        worst_district_utility=round(metrics["Uworst"], 6),
        total_unmet=int(metrics["total_unmet_demand"]),
        runtime_seconds=round(runtime, 4),
        district_results=district_results,
        monthly_results=monthly_results,
    )
