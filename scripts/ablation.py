"""Ablation study: decompose contribution of each policy component."""
import sys
import os
import json
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.simulator import Simulator
from src.policies import Policy
from src.forecast import RegressionForecast
from src.allocator import (
    ExpectedShortageAllocator,
    RiskWeightedAllocator,
    WorstDistrictProtectionAllocator,
)
from src.anomaly import BasicAnomalyDetector, ZScoreAnomalyDetector
from src.evaluation import evaluate_policy

SEEDS = [
    20260911, 20260912, 20260913, 20260914, 20260915,
    20260916, 20260917, 20260918, 20260919, 20260920,
    20260921, 20260922, 20260923, 20260924, 20260925,
    20260926, 20260927, 20260928, 20260929, 20260930,
]

SCENARIOS = [{"seed": s, "randomize": (i >= 10)} for i, s in enumerate(SEEDS)]


def run_scenarios(name, policy_factory):
    u_forecasts, u_services, u_worsts, scores, unmets = [], [], [], [], []
    for sc in SCENARIOS:
        sim = Simulator(seed=sc["seed"], randomize_surge=sc["randomize"])
        policy = policy_factory()
        metrics, _ = evaluate_policy(sim, policy)
        u_forecasts.append(metrics["Uforecast"])
        u_services.append(metrics["Uservice"])
        u_worsts.append(metrics["Uworst"])
        scores.append(metrics["internal_weighted_score"])
        unmets.append(metrics["total_unmet_demand"])
    return {
        "policy": name,
        "mean_Uforecast": float(np.mean(u_forecasts)),
        "mean_Uservice": float(np.mean(u_services)),
        "mean_Uworst": float(np.mean(u_worsts)),
        "mean_score": float(np.mean(scores)),
        "mean_unmet": float(np.mean(unmets)),
        "worst_Uservice": float(np.min(u_services)),
        "worst_Uworst": float(np.min(u_worsts)),
        "std_score": float(np.std(scores)),
    }


def main():
    ablations = [
        (
            "Baseline: Regression + ExpShortage (always-use)",
            lambda: Policy(RegressionForecast(), ExpectedShortageAllocator(always_use_all=True)),
        ),
        (
            "+ ZScore Anomaly -> Risk-Weighted (rw=1.5)",
            lambda: Policy(
                RegressionForecast(),
                RiskWeightedAllocator(always_use_all=True, risk_weight=1.5),
                ZScoreAnomalyDetector(),
            ),
        ),
        (
            "+ ZScore Anomaly -> Risk-Weighted (rw=3.0)",
            lambda: Policy(
                RegressionForecast(),
                RiskWeightedAllocator(always_use_all=True, risk_weight=3.0),
                ZScoreAnomalyDetector(),
            ),
        ),
        (
            "+ Worst-District Protection",
            lambda: Policy(RegressionForecast(), WorstDistrictProtectionAllocator(always_use_all=True)),
        ),
        (
            "+ Basic Anomaly -> Risk-Weighted (rw=1.5)",
            lambda: Policy(
                RegressionForecast(),
                RiskWeightedAllocator(always_use_all=True, risk_weight=1.5),
                BasicAnomalyDetector(),
            ),
        ),
        (
            "Baseline: Regression + ExpShortage (save unused)",
            lambda: Policy(RegressionForecast(), ExpectedShortageAllocator(always_use_all=False)),
        ),
    ]

    print("\n=== ABLATION STUDY ===\n")
    header = (
        f"{'Variant':<52} | {'Uservice':>9} | {'Uworst':>9} | "
        f"{'Score':>9} | {'Unmet':>7} | {'dUservice':>10} | {'dUworst':>9}"
    )
    print(header)
    print("-" * 128)

    results = []
    baseline_row = None
    for name, factory in ablations:
        print(f"  Running: {name}...")
        row = run_scenarios(name, factory)
        results.append(row)
        if baseline_row is None:
            baseline_row = row

    print("-" * 128)
    for row in results:
        delta_svc = row["mean_Uservice"] - baseline_row["mean_Uservice"]
        delta_worst = row["mean_Uworst"] - baseline_row["mean_Uworst"]
        marker = "  <- BASELINE" if row["policy"] == baseline_row["policy"] else ""
        sign_svc = "+" if delta_svc >= 0 else ""
        sign_worst = "+" if delta_worst >= 0 else ""
        print(
            f"{row['policy']:<52} | {row['mean_Uservice']:>9.4f} | {row['mean_Uworst']:>9.4f} | "
            f"{row['mean_score']:>9.4f} | {row['mean_unmet']:>7.1f} | "
            f"{sign_svc}{delta_svc:>9.4f} | {sign_worst}{delta_worst:>8.4f}{marker}"
        )

    print("-" * 128)
    print("\nConclusions:")
    best = max(results, key=lambda r: (r["mean_Uservice"], r["mean_Uworst"]))
    print(f"  Best by Uservice+Uworst: {best['policy']}")
    print(f"  Uservice={best['mean_Uservice']:.4f}, Uworst={best['mean_Uworst']:.4f}, Score={best['mean_score']:.4f}")

    os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'results'), exist_ok=True)
    out_path = os.path.join(os.path.dirname(__file__), '..', 'results', 'ablation_results.json')
    with open(out_path, "w") as f:
        json.dump(results, f, indent=4)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
