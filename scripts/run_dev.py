"""Run development simulation with a specific policy."""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import DEFAULT_SEED
from src.simulator import Simulator
from src.policies import Policy
from src.forecast import RegressionForecast
from src.allocator import ExpectedShortageAllocator
from src.evaluation import evaluate_policy

def main():
    print(f"Running development simulation with seed {DEFAULT_SEED}...")
    sim = Simulator(DEFAULT_SEED)
    policy = Policy(RegressionForecast(), ExpectedShortageAllocator())
    
    metrics, records = evaluate_policy(sim, policy)
    
    print("\nMetrics:")
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
