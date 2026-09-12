"""Evaluation metrics."""
from typing import List
from .types import EvaluationRecord

class MetricsCalculator:
    def __init__(self, records: List[EvaluationRecord]):
        self.records = records
        
    def _clip(self, val: float) -> float:
        return max(0.0, min(1.0, val))

    def compute_metrics(self) -> dict:
        total_abs_error = 0.0
        total_unmet = 0
        total_actual = 0
        total_forecast = 0.0
        
        district_unmet = {}
        district_actual = {}
        
        reserve_usage = 0
        alloc_non_negative = True
        alloc_integer = True
        
        # Monthly reserve tracking
        monthly_alloc = {}
        
        for r in self.records:
            total_abs_error += abs(r.forecast - r.actual_demand)
            total_unmet += r.unmet_demand
            total_actual += max(r.actual_demand, 1)
            total_forecast += r.forecast
            
            district_unmet[r.district] = district_unmet.get(r.district, 0) + r.unmet_demand
            district_actual[r.district] = district_actual.get(r.district, 0) + max(r.actual_demand, 1)
            
            reserve_usage += r.allocation
            
            if not isinstance(r.allocation, int):
                alloc_integer = False
            if r.allocation < 0:
                alloc_non_negative = False
                
            monthly_alloc[r.month] = monthly_alloc.get(r.month, 0) + r.allocation

        u_forecast = self._clip(1.0 - total_abs_error / total_actual) if total_actual > 0 else 0.0
        u_service = self._clip(1.0 - total_unmet / total_actual) if total_actual > 0 else 0.0
        
        r_ds = []
        for d in district_actual:
            rd = 1.0 - district_unmet[d] / district_actual[d]
            r_ds.append(rd)
            
        u_worst = min(r_ds) if r_ds else 0.0
        
        alloc_compliance = alloc_integer and alloc_non_negative
        for m, tot in monthly_alloc.items():
            if tot > 60:
                alloc_compliance = False
                
        compliance_score = 1.0 if alloc_compliance else 0.0
        # Assume runtime reproducibility score is 1.0 here, we can adjust later or keep simple
        internal_weighted_score = 0.30 * u_forecast + 0.45 * u_service + 0.15 * u_worst + 0.05 * compliance_score + 0.05 * 1.0

        return {
            "Uforecast": u_forecast,
            "Uservice": u_service,
            "Uworst": u_worst,
            "internal_weighted_score": internal_weighted_score,
            "total_unmet_demand": total_unmet,
            "total_forecast_error": total_abs_error,
            "total_demand": sum(r.actual_demand for r in self.records),
            "reserve_usage": reserve_usage,
            "integer_compliance": alloc_integer,
            "allocation_compliance": alloc_compliance
        }
