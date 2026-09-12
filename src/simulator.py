"""Simulator that manages the hidden ground truth and exposes the sequential environment."""
import numpy as np
import math
from typing import Dict, List, Tuple, Optional
from .config import NUM_DISTRICTS, GLOBAL_RESERVE, EVAL_HORIZON_START, EVAL_HORIZON_END
from .types import DistrictParams, PolicyInput
from .rng import get_generator

class Simulator:
    def __init__(self, seed: int, randomize_surge: bool = False):
        self.rng = get_generator(seed)
        self.randomize_surge = randomize_surge
        
        self.params: Dict[int, DistrictParams] = {}
        self.history_demand: Dict[int, List[int]] = {d: [] for d in range(NUM_DISTRICTS)}
        self.history_allocations: Dict[int, List[int]] = {d: [] for d in range(NUM_DISTRICTS)}
        self.hidden_demand: Dict[int, List[int]] = {d: [] for d in range(NUM_DISTRICTS)}
        
        self._generate_scenario()
        
    def _generate_scenario(self):
        # 1. Generate base parameters
        for d in range(NUM_DISTRICTS):
            b = int(self.rng.integers(60, 161))
            a = float(self.rng.uniform(10, 40))
            g = float(self.rng.uniform(-0.5, 1.5))
            c = round(0.90 * b)
            self.params[d] = DistrictParams(b=b, a=a, g=g, capacity=c)
            
        # 2. Determine surge parameters
        if self.randomize_surge:
            # Pick 2 distinct districts
            surge_districts = self.rng.choice(NUM_DISTRICTS, size=2, replace=False)
            # Pick start month so that 3 months fit in [36, 41], so start in [36, 39]
            surge_start = int(self.rng.integers(36, 40))
        else:
            surge_districts = [2, 9]
            surge_start = 38
            
        surge_months = [surge_start, surge_start + 1, surge_start + 2]
            
        # 3. Generate demand
        for d in range(NUM_DISTRICTS):
            b = self.params[d].b
            a = self.params[d].a
            g = self.params[d].g
            
            demands = []
            for t in range(EVAL_HORIZON_END + 1):
                mu = b + a * math.sin(2 * math.pi * t / 12 + d * math.pi / 6) + g * t
                epsilon = float(self.rng.normal(0, 8))
                y = mu + epsilon
                
                # Apply surge
                if d in surge_districts and t in surge_months:
                    y += 35
                
                demands.append(max(0, round(y)))
            
            self.hidden_demand[d] = demands
            self.history_demand[d] = demands[:EVAL_HORIZON_START]
            self.history_allocations[d] = [0] * EVAL_HORIZON_START
            
    def get_policy_input(self, month: int) -> PolicyInput:
        """Returns only the information available to the policy at the start of `month`."""
        hist_demand = {d: list(self.history_demand[d]) for d in range(NUM_DISTRICTS)}
        hist_alloc = {d: list(self.history_allocations[d]) for d in range(NUM_DISTRICTS)}
        capacities = {d: self.params[d].capacity for d in range(NUM_DISTRICTS)}
        
        return PolicyInput(
            month=month,
            historical_demand=hist_demand,
            historical_allocations=hist_alloc,
            capacities=capacities,
            global_reserve=GLOBAL_RESERVE
        )
        
    def step(self, month: int, allocations: Dict[int, int]) -> Dict[int, int]:
        total_alloc = sum(allocations.values())
        if total_alloc > GLOBAL_RESERVE:
            raise ValueError(f"Total allocations {total_alloc} exceed global reserve {GLOBAL_RESERVE}")
            
        actual_demands = {}
        for d in range(NUM_DISTRICTS):
            alloc = allocations.get(d, 0)
            if not isinstance(alloc, int) or alloc < 0:
                raise ValueError(f"Allocation for district {d} must be a non-negative integer, got {alloc}")
                
            actual_d = self.hidden_demand[d][month]
            actual_demands[d] = actual_d
            
            self.history_demand[d].append(actual_d)
            self.history_allocations[d].append(alloc)
            
        return actual_demands
