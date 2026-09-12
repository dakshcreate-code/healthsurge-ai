"""Combine forecasting, anomaly detection, and allocation into a Policy."""
from typing import Dict, List
from .types import PolicyInput, PolicyOutput
from .forecast import ForecastModel
from .allocator import Allocator
from .anomaly import AnomalyDetector

class Policy:
    def __init__(self, forecaster: ForecastModel, allocator: Allocator, anomaly_detector: AnomalyDetector = None):
        from .anomaly import BasicAnomalyDetector
        self.forecaster = forecaster
        self.allocator = allocator
        self.anomaly_detector = anomaly_detector or BasicAnomalyDetector()
        
        # Track our own forecasts for anomaly detection
        self._past_forecasts: Dict[int, List[float]] = {}
        
    def act(self, policy_input: PolicyInput) -> PolicyOutput:
        n = len(policy_input.capacities)
        forecasts = {}
        expected_shortage = {}
        anomaly_scores = {}
        
        for d in range(n):
            if d not in self._past_forecasts:
                self._past_forecasts[d] = []
                
            history = policy_input.historical_demand[d]
            # Forecast for the current month
            f = self.forecaster.forecast(d, history, policy_input.month)
            forecasts[d] = f
            
            # Anomaly score based on history before this month
            # Note: past_forecasts has forecasts for months < policy_input.month
            score = self.anomaly_detector.detect(d, history, self._past_forecasts[d])
            anomaly_scores[d] = score
            
            expected_shortage[d] = max(0.0, f - policy_input.capacities[d])
            
        allocations = self.allocator.allocate(policy_input, forecasts, anomaly_scores)
        
        # Update our internal record of forecasts for next time
        for d in range(n):
            self._past_forecasts[d].append(forecasts[d])
            
        return PolicyOutput(
            forecasts=forecasts,
            allocations=allocations,
            expected_shortage=expected_shortage,
            anomaly_scores=anomaly_scores
        )
