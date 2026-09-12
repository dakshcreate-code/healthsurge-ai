"""Forecasting models."""
import numpy as np
import math
from typing import List, Dict

class ForecastModel:
    def forecast(self, district: int, history: List[int], target_month: int) -> float:
        raise NotImplementedError

class NaiveSeasonalForecast(ForecastModel):
    def forecast(self, district: int, history: List[int], target_month: int) -> float:
        """Forecast based on the same month last year."""
        if len(history) >= 12:
            return float(history[-12])
        if len(history) > 0:
            return float(np.mean(history))
        return 0.0

class RegressionForecast(ForecastModel):
    def forecast(self, district: int, history: List[int], target_month: int) -> float:
        """Regression with intercept, trend, sin(2*pi*t/12), cos(2*pi*t/12)."""
        n = len(history)
        if n < 4:
            return float(history[-1]) if n > 0 else 0.0
            
        # Build design matrix
        # Columns: intercept, t, sin(2*pi*t/12), cos(2*pi*t/12)
        X = []
        for t in range(n):
            X.append([
                1.0,
                t,
                math.sin(2 * math.pi * t / 12),
                math.cos(2 * math.pi * t / 12)
            ])
            
        X = np.array(X)
        y = np.array(history)
        
        # OLS
        try:
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
        except np.linalg.LinAlgError:
            return float(history[-1])
            
        # Predict target_month
        x_target = np.array([
            1.0,
            target_month,
            math.sin(2 * math.pi * target_month / 12),
            math.cos(2 * math.pi * target_month / 12)
        ])
        
        pred = np.dot(x_target, beta)
        return max(0.0, float(pred))

class StatsmodelsForecast(ForecastModel):
    def forecast(self, district: int, history: List[int], target_month: int) -> float:
        """Use Exponential Smoothing from statsmodels."""
        if len(history) < 24: # Need enough data for seasonal ETS
            # fallback to regression
            return RegressionForecast().forecast(district, history, target_month)
            
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        try:
            # We assume history represents t=0..n-1. 
            # We want to forecast target_month. If target_month == n, we forecast 1 step.
            steps = target_month - len(history) + 1
            if steps <= 0:
                steps = 1
                
            model = ExponentialSmoothing(
                history, 
                trend='add', 
                seasonal='add', 
                seasonal_periods=12,
                initialization_method='estimated'
            )
            fit = model.fit(optimized=True)
            forecast_vals = fit.forecast(steps)
            return max(0.0, float(forecast_vals.iloc[-1]))
        except Exception:
            # fallback
            return RegressionForecast().forecast(district, history, target_month)
