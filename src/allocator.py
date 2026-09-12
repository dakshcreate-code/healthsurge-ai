"""Allocation policies."""
from typing import Dict, Optional
from .types import PolicyInput

class Allocator:
    def __init__(self, always_use_all: bool = True):
        self.always_use_all = always_use_all

    def allocate(self, policy_input: PolicyInput, forecasts: Dict[int, float], anomaly_scores: Optional[Dict[int, float]] = None) -> Dict[int, int]:
        raise NotImplementedError

class EqualAllocator(Allocator):
    def allocate(self, policy_input: PolicyInput, forecasts: Dict[int, float], anomaly_scores: Optional[Dict[int, float]] = None) -> Dict[int, int]:
        n = len(policy_input.capacities)
        if not self.always_use_all:
            # If not always using all, only use what is needed based on expected shortage
            shortages = {d: max(0.0, forecasts[d] - policy_input.capacities[d]) for d in range(n)}
            if sum(shortages.values()) <= 0:
                return {d: 0 for d in range(n)}
                
        alloc_per_district = policy_input.global_reserve // n
        remainder = policy_input.global_reserve % n
        allocations = {d: alloc_per_district + (1 if d < remainder else 0) for d in range(n)}
        return allocations

class ExpectedShortageAllocator(Allocator):
    def allocate(self, policy_input: PolicyInput, forecasts: Dict[int, float], anomaly_scores: Optional[Dict[int, float]] = None) -> Dict[int, int]:
        n = len(policy_input.capacities)
        expected_shortages = {d: max(0.0, forecasts[d] - policy_input.capacities[d]) for d in range(n)}
        
        allocations = {d: 0 for d in range(n)}
        remaining = policy_input.global_reserve
        current_shortages = expected_shortages.copy()
        
        while remaining > 0 and any(s > 0 for s in current_shortages.values()):
            max_d = max(current_shortages.keys(), key=lambda d: current_shortages[d])
            if current_shortages[max_d] <= 0:
                break
            
            allocations[max_d] += 1
            current_shortages[max_d] -= 1
            remaining -= 1
            
        if self.always_use_all and remaining > 0:
            for d in range(remaining):
                allocations[d % n] += 1
                
        return allocations

class ProportionalShortageAllocator(Allocator):
    def allocate(self, policy_input: PolicyInput, forecasts: Dict[int, float], anomaly_scores: Optional[Dict[int, float]] = None) -> Dict[int, int]:
        n = len(policy_input.capacities)
        expected_shortages = {d: max(0.0, forecasts[d] - policy_input.capacities[d]) for d in range(n)}
        total_shortage = sum(expected_shortages.values())
        
        allocations = {d: 0 for d in range(n)}
        
        if total_shortage > 0:
            remaining = policy_input.global_reserve
            
            # Proportional floor
            for d in range(n):
                prop = (expected_shortages[d] / total_shortage) * policy_input.global_reserve
                allocations[d] = int(prop)
                remaining -= allocations[d]
                expected_shortages[d] -= allocations[d]
                
            # Distribute remaining based on largest remaining shortage
            while remaining > 0 and any(s > 0 for s in expected_shortages.values()):
                max_d = max(expected_shortages.keys(), key=lambda d: expected_shortages[d])
                if expected_shortages[max_d] <= 0:
                    break
                allocations[max_d] += 1
                expected_shortages[max_d] -= 1
                remaining -= 1
                
            if self.always_use_all and remaining > 0:
                for d in range(remaining):
                    allocations[d % n] += 1
        elif self.always_use_all:
            alloc_per = policy_input.global_reserve // n
            rem = policy_input.global_reserve % n
            for d in range(n):
                allocations[d] = alloc_per + (1 if d < rem else 0)
                
        return allocations

class RiskWeightedAllocator(Allocator):
    def __init__(self, always_use_all: bool = True, risk_weight: float = 1.0):
        super().__init__(always_use_all)
        self.risk_weight = risk_weight

    def allocate(self, policy_input: PolicyInput, forecasts: Dict[int, float], anomaly_scores: Optional[Dict[int, float]] = None) -> Dict[int, int]:
        n = len(policy_input.capacities)
        anomaly_scores = anomaly_scores or {d: 0.0 for d in range(n)}
        
        risk_scores = {}
        for d in range(n):
            shortage = max(0.0, forecasts[d] - policy_input.capacities[d])
            # Add anomaly score scaled by risk_weight to the shortage
            risk_scores[d] = shortage + self.risk_weight * anomaly_scores[d]
            
        allocations = {d: 0 for d in range(n)}
        remaining = policy_input.global_reserve
        current_scores = risk_scores.copy()
        
        while remaining > 0 and any(s > 0 for s in current_scores.values()):
            max_d = max(current_scores.keys(), key=lambda d: current_scores[d])
            if current_scores[max_d] <= 0:
                break
            
            allocations[max_d] += 1
            current_scores[max_d] -= 1
            remaining -= 1
            
        if self.always_use_all and remaining > 0:
            for d in range(remaining):
                allocations[d % n] += 1
                
        return allocations

class WorstDistrictProtectionAllocator(Allocator):
    def allocate(self, policy_input: PolicyInput, forecasts: Dict[int, float], anomaly_scores: Optional[Dict[int, float]] = None) -> Dict[int, int]:
        # Tries to balance the service ratio instead of just expected shortage.
        # R_d = 1 - Unmet / Actual. We want to maximize the min R_d.
        # Since we don't know Actual, we use Expected Actual (Forecast).
        # Expected Unmet = max(0, Forecast - Capacity - Alloc)
        # Expected R_d = 1 - Expected Unmet / max(Forecast, 1)
        
        n = len(policy_input.capacities)
        allocations = {d: 0 for d in range(n)}
        remaining = policy_input.global_reserve
        
        def expected_rd(d, alloc):
            f = max(forecasts[d], 1.0)
            c = policy_input.capacities[d]
            unmet = max(0.0, forecasts[d] - c - alloc)
            return 1.0 - (unmet / f)

        # We greedily give 1 unit to the district with the lowest expected_rd
        while remaining > 0:
            # Check if all districts are at 1.0
            rds = {d: expected_rd(d, allocations[d]) for d in range(n)}
            if all(r >= 1.0 for r in rds.values()):
                break # All expected demand is met
                
            min_d = min(rds.keys(), key=lambda d: rds[d])
            allocations[min_d] += 1
            remaining -= 1
            
        if self.always_use_all and remaining > 0:
            for d in range(remaining):
                allocations[d % n] += 1
                
        return allocations
