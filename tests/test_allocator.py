import pytest
from src.allocator import EqualAllocator, ExpectedShortageAllocator
from src.types import PolicyInput

def test_equal_allocator():
    a = EqualAllocator()
    pin = PolicyInput(
        month=1,
        historical_demand={},
        historical_allocations={},
        capacities={i: 100 for i in range(12)},
        global_reserve=60
    )
    alloc = a.allocate(pin, {})
    assert sum(alloc.values()) == 60
    for v in alloc.values():
        assert v == 5
        assert isinstance(v, int)
        assert v >= 0

def test_expected_shortage_allocator():
    a = ExpectedShortageAllocator()
    pin = PolicyInput(
        month=1,
        historical_demand={},
        historical_allocations={},
        capacities={0: 10, 1: 10, 2: 10},
        global_reserve=5
    )
    # 0 expects 15 (shortage 5), 1 expects 10 (shortage 0), 2 expects 12 (shortage 2)
    forecasts = {0: 15, 1: 10, 2: 12}
    alloc = a.allocate(pin, forecasts)
    assert sum(alloc.values()) == 5
    # Total reserve is 5.
    # Expected shortages: 0: 5, 1: 0, 2: 2.
    # Allocations will favor 0 and 2.
    assert alloc[0] + alloc[2] == 5
    assert alloc[1] == 0
    
    for v in alloc.values():
        assert isinstance(v, int)
        assert v >= 0
