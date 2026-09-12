# HealthSurge AI — HC-05: District Health Surge Forecast and Allocation

Deterministic Python competition engine for the HC-05 problem.

---

## Problem

12 synthetic health districts each have noisy, trended, seasonal demand.  
A 60-unit global reserve must be allocated monthly across all districts during a 6-month evaluation horizon (months 36–41).  
A local surge of +35 demand units hits 2 districts for 3 consecutive months.

---

## Package Architecture

```
healthsurge_ai/
  src/
    config.py          -- Global constants (NUM_DISTRICTS, GLOBAL_RESERVE, seeds…)
    types.py           -- Dataclasses: DistrictParams, PolicyInput, PolicyOutput, EvaluationRecord
    rng.py             -- NumPy PCG64 seeded generator
    simulator.py       -- Ground-truth generator + strict online information boundary
    forecast.py        -- NaiveSeasonalForecast, RegressionForecast, StatsmodelsForecast
    allocator.py       -- Equal, ExpectedShortage, Proportional, RiskWeighted, WorstDistrictProtection
    anomaly.py         -- BasicAnomalyDetector, ZScoreAnomalyDetector
    policies.py        -- Policy class composing forecaster + allocator + anomaly detector
    metrics.py         -- Official Uforecast, Uservice, Uworst + internal weighted score
    evaluation.py      -- Sequential evaluation runner
  tests/
    test_rng.py
    test_simulator.py
    test_forecast.py
    test_allocator.py
    test_information_boundary.py
    test_benchmark.py
  scripts/
    run_dev.py         -- Single dev simulation
    benchmark.py       -- Single-seed policy comparison
    benchmark_multi.py -- 20-seed multi-scenario ranking table
    ablation.py        -- Component ablation study
  results/
    benchmark_results.json
    benchmark_summary.csv
    ablation_results.json
```

---

## Generator (HC-05 Spec)

- **Seed**: `np.random.Generator(np.random.PCG64(20260911))`
- **Generation order per district d**:
  1. `b_d ~ Integer[60, 160]`
  2. `a_d ~ Uniform[10, 40]`
  3. `g_d ~ Uniform[-0.5, 1.5]`
  4. For each `t` in `0..41`: `epsilon ~ Normal(0, 64)`, demand = `max(0, round(mu + epsilon))`
- Local development surge: districts **2 and 9**, months **38, 39, 40** (`+35`)

---

## Information Boundary (Critical)

The `Simulator` maintains all ground truth internally. `get_policy_input(month=t)` returns **only**:
- `historical_demand[d]` — observations for months `0..t-1` (deepcopy)
- `historical_allocations[d]` — prior allocations
- `capacities` — fixed nominal capacity per district
- `global_reserve = 60`

**No future demand, noise, surge identity, or generator state is ever exposed to the policy.**  
Tests in `test_information_boundary.py` and `test_benchmark.py` explicitly verify this.

---

## Forecasting Models

| Model | Description |
|---|---|
| `NaiveSeasonalForecast` | Same month last year (12-month lag) |
| `RegressionForecast` | OLS with intercept + trend + sin(2πt/12) + cos(2πt/12) |
| `StatsmodelsForecast` | Holt-Winters ETS (requires ≥24 months; falls back to Regression) |

---

## Allocation Policies

| Policy | Description |
|---|---|
| `EqualAllocator` | Divide 60 units equally across districts |
| `ExpectedShortageAllocator` | Greedy: allocate to highest `max(0, forecast − capacity)` first |
| `ProportionalShortageAllocator` | Proportional floor + greedy remainder |
| `RiskWeightedAllocator` | Expected shortage + weighted anomaly score |
| `WorstDistrictProtectionAllocator` | Greedy by lowest expected service ratio |

All allocators accept `always_use_all: bool` — either use all 60 units or stop when shortages are covered.

---

## Official Metrics

```
Uforecast = clip(1 - sum|forecast - actual| / sum(max(actual, 1)), 0, 1)
Uservice  = clip(1 - sum(unmet) / sum(max(actual, 1)), 0, 1)
r_d       = 1 - sum_unmet_d / sum(max(actual_d, 1))
Uworst    = min(r_d)

Internal score = 0.30·Uforecast + 0.45·Uservice + 0.15·Uworst + 0.05·compliance + 0.05·1.0
```

> **Note**: The last two terms (compliance + runtime) use our internal normalization.  
> The official organizer formula for those components is not fully specified.

---

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest tests -v

# Dev simulation (seed 20260911, Regression + WorstDistrict)
python scripts/run_dev.py

# Single-seed benchmark table
python scripts/benchmark.py

# 20-scenario multi-seed benchmark (saves JSON + CSV)
python scripts/benchmark_multi.py

# Ablation study (component contribution)
python scripts/ablation.py
```

---

## Reproducibility

Running `benchmark_multi.py` twice produces bit-identical results (tested in `test_policy_ranking_reproducibility`).  
Runtime is excluded from reproducibility checks since wall-clock time varies.
