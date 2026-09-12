"""Types and data structures for the simulator and policy interface."""
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class DistrictParams:
    b: int
    a: float
    g: float
    capacity: int

@dataclass
class MonthData:
    month: int
    demand: Dict[int, int]  # district_id -> demand
    allocations: Dict[int, int] # district_id -> allocation
    unmet_demand: Dict[int, int] # district_id -> unmet

@dataclass
class PolicyInput:
    month: int
    historical_demand: Dict[int, List[int]]  # district_id -> list of historical demands
    historical_allocations: Dict[int, List[int]] # district_id -> list of historical allocations
    capacities: Dict[int, int]
    global_reserve: int

@dataclass
class PolicyOutput:
    forecasts: Dict[int, float]
    allocations: Dict[int, int]
    expected_shortage: Dict[int, float]
    anomaly_scores: Dict[int, float]

@dataclass
class EvaluationRecord:
    month: int
    district: int
    forecast: float
    actual_demand: int
    capacity: int
    allocation: int
    unmet_demand: int
    anomaly_score: float
    expected_shortage: float
