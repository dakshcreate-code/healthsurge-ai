"""Evaluation runner."""
import time
from typing import List, Tuple
from .config import EVAL_HORIZON_START, EVAL_HORIZON_END
from .simulator import Simulator
from .policies import Policy
from .types import EvaluationRecord
from .metrics import MetricsCalculator

def evaluate_policy(simulator: Simulator, policy: Policy) -> Tuple[dict, List[EvaluationRecord]]:
    records = []
    start_time = time.time()
    
    for month in range(EVAL_HORIZON_START, EVAL_HORIZON_END + 1):
        # 1. Get available info
        policy_input = simulator.get_policy_input(month)
        
        # 2. Policy acts
        output = policy.act(policy_input)
        
        # 3. Simulator steps and reveals actual
        actual_demands = simulator.step(month, output.allocations)
        
        # 4. Record everything
        for d in range(len(policy_input.capacities)):
            capacity = policy_input.capacities[d]
            alloc = output.allocations.get(d, 0)
            actual = actual_demands[d]
            unmet = max(0, actual - capacity - alloc)
            
            record = EvaluationRecord(
                month=month,
                district=d,
                forecast=output.forecasts.get(d, 0.0),
                actual_demand=actual,
                capacity=capacity,
                allocation=alloc,
                unmet_demand=unmet,
                anomaly_score=output.anomaly_scores.get(d, 0.0),
                expected_shortage=output.expected_shortage.get(d, 0.0)
            )
            records.append(record)
            
    end_time = time.time()
    
    # Calculate metrics
    calc = MetricsCalculator(records)
    metrics = calc.compute_metrics()
    metrics["runtime"] = end_time - start_time
    
    return metrics, records
