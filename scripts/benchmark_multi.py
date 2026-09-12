"""Multi-scenario benchmark."""
import sys
import os
import json
import csv
import time
import numpy as np
from typing import List, Dict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.simulator import Simulator
from src.policies import Policy
from src.forecast import NaiveSeasonalForecast, RegressionForecast
from src.allocator import EqualAllocator, ExpectedShortageAllocator, ProportionalShortageAllocator, RiskWeightedAllocator, WorstDistrictProtectionAllocator
from src.anomaly import BasicAnomalyDetector, ZScoreAnomalyDetector
from src.evaluation import evaluate_policy

def run_multi_benchmark():
    # 20 seeds
    seeds = [
        20260911, 20260912, 20260913, 20260914, 20260915,
        20260916, 20260917, 20260918, 20260919, 20260920,
        20260921, 20260922, 20260923, 20260924, 20260925,
        20260926, 20260927, 20260928, 20260929, 20260930
    ]
    
    # 10 dev identical surge scenarios + 10 randomized surge scenarios
    scenarios = []
    for i, seed in enumerate(seeds):
        randomize = (i >= 10)  # half and half
        scenarios.append({"seed": seed, "randomize": randomize})
        
    policies = [
        ("Naive + Equal (Always Use)", lambda: Policy(NaiveSeasonalForecast(), EqualAllocator(always_use_all=True))),
        ("Regression + Expected Shortage (Always Use)", lambda: Policy(RegressionForecast(), ExpectedShortageAllocator(always_use_all=True))),
        ("Regression + Expected Shortage (Save)", lambda: Policy(RegressionForecast(), ExpectedShortageAllocator(always_use_all=False))),
        ("Regression + Proportional (Always Use)", lambda: Policy(RegressionForecast(), ProportionalShortageAllocator(always_use_all=True))),
        ("Regression + Worst-District (Always Use)", lambda: Policy(RegressionForecast(), WorstDistrictProtectionAllocator(always_use_all=True))),
        ("Regression + Risk-Weighted (ZScore, Always Use)", lambda: Policy(RegressionForecast(), RiskWeightedAllocator(always_use_all=True, risk_weight=1.5), ZScoreAnomalyDetector())),
    ]
    
    results = []
    
    print(f"{'Policy Name':<50} | {'Uforecast':<10} | {'Uservice':<10} | {'Uworst':<10} | {'Score':<10} | {'Unmet(Mean)':<12} | {'Valid'}")
    print("-" * 130)
    
    for name, policy_factory in policies:
        u_forecasts = []
        u_services = []
        u_worsts = []
        scores = []
        unmets = []
        runtimes = []
        valid = True
        
        for sc in scenarios:
            sim = Simulator(seed=sc["seed"], randomize_surge=sc["randomize"])
            policy = policy_factory()
            
            metrics, records = evaluate_policy(sim, policy)
            
            u_forecasts.append(metrics["Uforecast"])
            u_services.append(metrics["Uservice"])
            u_worsts.append(metrics["Uworst"])
            scores.append(metrics["internal_weighted_score"])
            unmets.append(metrics["total_unmet_demand"])
            runtimes.append(metrics["runtime"])
            
            if not (metrics["integer_compliance"] and metrics["allocation_compliance"]):
                valid = False
                
        # Aggregate
        agg = {
            "policy": name,
            "mean_Uforecast": float(np.mean(u_forecasts)),
            "mean_Uservice": float(np.mean(u_services)),
            "mean_Uworst": float(np.mean(u_worsts)),
            "mean_score": float(np.mean(scores)),
            "mean_unmet": float(np.mean(unmets)),
            "median_unmet": float(np.median(unmets)),
            "worst_Uservice": float(np.min(u_services)),
            "worst_Uworst": float(np.min(u_worsts)),
            "std_score": float(np.std(scores)),
            "total_runtime": float(np.sum(runtimes)),
            "valid": valid
        }
        results.append(agg)
        
        print(f"{name:<50} | {agg['mean_Uforecast']:<10.4f} | {agg['mean_Uservice']:<10.4f} | {agg['mean_Uworst']:<10.4f} | {agg['mean_score']:<10.4f} | {agg['mean_unmet']:<12.1f} | {'Yes' if valid else 'No'}")
        
    print("-" * 130)
    
    # Sort by Uservice desc, Uworst desc
    results.sort(key=lambda x: (x["mean_Uservice"], x["mean_Uworst"], x["mean_Uforecast"]), reverse=True)
    
    # Save to json and csv
    os.makedirs("healthsurge_ai/results", exist_ok=True)
    with open("healthsurge_ai/results/benchmark_results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    with open("healthsurge_ai/results/benchmark_summary.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

if __name__ == "__main__":
    run_multi_benchmark()
