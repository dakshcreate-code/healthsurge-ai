import numpy as np
from src.rng import get_generator

def test_rng_reproducibility():
    gen1 = get_generator(42)
    gen2 = get_generator(42)
    assert gen1.integers(0, 100) == gen2.integers(0, 100)
    assert np.allclose(gen1.normal(0, 1, 10), gen2.normal(0, 1, 10))

def test_uses_pcg64():
    gen = get_generator(42)
    assert isinstance(gen.bit_generator, np.random.PCG64)
