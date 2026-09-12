import os
import json
from src.simulator import Simulator
from src.policies import Policy
from src.forecast import RegressionForecast
from src.allocator import WorstDistrictProtectionAllocator
from src.anomaly import ZScoreAnomalyDetector
from scripts.benchmark_multi import run_multi_benchmark

def test_different_surge_locations_and_months():
    # If randomize_surge=True, simulator should generate different surge parameters for different seeds
    sim1 = Simulator(seed=42, randomize_surge=True)
    sim2 = Simulator(seed=43, randomize_surge=True)
    
    # Check that they differ (in hidden_demand, some districts should have higher peaks)
    # It's highly probable they differ across two random seeds
    assert sim1.hidden_demand != sim2.hidden_demand

def test_anomaly_detector_no_future_leakage():
    det = ZScoreAnomalyDetector()
    history = [10, 11, 12, 10, 11, 12]
    forecasts = [10, 10, 10, 10, 10, 10]
    
    # Score should only depend on provided lists, not any hidden global
    score1 = det.detect(0, history, forecasts)
    
    history.append(100) # an anomaly
    forecasts.append(10)
    score2 = det.detect(0, history, forecasts)
    
    assert score2 > score1

def test_policy_ranking_reproducibility():
    # Run benchmark twice and ensure the output JSON is identical
    run_multi_benchmark()
    with open("healthsurge_ai/results/benchmark_results.json", "r") as f:
        res1 = json.load(f)
        
    run_multi_benchmark()
    with open("healthsurge_ai/results/benchmark_results.json", "r") as f:
        res2 = json.load(f)
        
    for r in res1:
        r.pop("total_runtime", None)
    for r in res2:
        r.pop("total_runtime", None)
        
    assert res1 == res2
