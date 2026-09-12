"""Anomaly / surge detection."""
import numpy as np
from typing import List

class AnomalyDetector:
    def detect(self, district: int, history: List[int], forecast_history: List[float]) -> float:
        raise NotImplementedError

class BasicAnomalyDetector(AnomalyDetector):
    def detect(self, district: int, history: List[int], forecast_history: List[float]) -> float:
        if len(history) < 3 or len(forecast_history) < 3:
            return 0.0
            
        recent_actual = history[-3:]
        recent_forecast = forecast_history[-3:]
        
        errors = [max(0, a - f) for a, f in zip(recent_actual, recent_forecast)]
        return float(np.mean(errors))

class ZScoreAnomalyDetector(AnomalyDetector):
    def detect(self, district: int, history: List[int], forecast_history: List[float]) -> float:
        """Computes z-score of the most recent residual based on historical residuals."""
        if len(history) < 6 or len(forecast_history) < 6:
            return 0.0
            
        # Historical residuals
        residuals = [a - f for a, f in zip(history, forecast_history)]
        
        past_residuals = residuals[:-1]
        current_residual = residuals[-1]
        
        std = np.std(past_residuals)
        if std == 0:
            std = 1.0
            
        mean_res = np.mean(past_residuals)
        z_score = (current_residual - mean_res) / std
        return float(max(0.0, z_score))
