"""Benchmark multiple policies."""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import DEFAULT_SEED
from src.simulator import Simulator
from src.policies import Policy
from src.forecast import NaiveSeasonalForecast, RegressionForecast, StatsmodelsForecast
from src.allocator import EqualAllocator, ExpectedShortageAllocator
from src.evaluation import evaluate_policy

def main():
    print("Benchmarking Policies...")
    
    scenarios = [
        ("Naive + Equal", Policy(NaiveSeasonalForecast(), EqualAllocator())),
        ("Regression + Equal", Policy(RegressionForecast(), EqualAllocator())),
        ("Regression + Expected-Shortage", Policy(RegressionForecast(), ExpectedShortageAllocator())),
        # ("Statsmodels + Expected-Shortage", Policy(StatsmodelsForecast(), ExpectedShortageAllocator())),
    ]
    
    print("-" * 110)
    print(f"{'Policy Name':<35} | {'Uforecast':<10} | {'Uservice':<10} | {'Uworst':<10} | {'Unmet':<8} | {'Error':<8} | {'Valid'}")
    print("-" * 110)
    
    for name, policy in scenarios:
        sim = Simulator(DEFAULT_SEED)
        metrics, records = evaluate_policy(sim, policy)
        valid = metrics["integer_compliance"] and metrics["allocation_compliance"]
        valid_str = "Yes" if valid else "No"
        
        print(f"{name:<35} | {metrics['Uforecast']:<10.4f} | {metrics['Uservice']:<10.4f} | {metrics['Uworst']:<10.4f} | {metrics['total_unmet_demand']:<8} | {metrics['total_forecast_error']:<8.1f} | {valid_str}")
    
    print("-" * 110)

if __name__ == "__main__":
    main()
