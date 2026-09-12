from src.simulator import Simulator
from src.config import EVAL_HORIZON_START, EVAL_HORIZON_END

def test_policy_cannot_access_future():
    sim = Simulator(42)
    # The policy input at EVAL_HORIZON_START should only contain history
    pin = sim.get_policy_input(EVAL_HORIZON_START)
    
    for d in range(12):
        assert len(pin.historical_demand[d]) == EVAL_HORIZON_START
        
    # Step one month
    alloc = {d: 0 for d in range(12)}
    sim.step(EVAL_HORIZON_START, alloc)
    
    # The policy input for START + 1 should now contain one more month
    pin2 = sim.get_policy_input(EVAL_HORIZON_START + 1)
    for d in range(12):
        assert len(pin2.historical_demand[d]) == EVAL_HORIZON_START + 1

    # Check that modifying pin doesn't modify the simulator's internal state
    pin2.historical_demand[0].append(999)
    assert len(sim.history_demand[0]) == EVAL_HORIZON_START + 1
