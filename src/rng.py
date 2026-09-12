"""Random number generator initialization."""
import numpy as np

def get_generator(seed: int = 20260911) -> np.random.Generator:
    """Returns a deterministic NumPy generator using PCG64."""
    return np.random.Generator(np.random.PCG64(seed))
