import numpy as np
import pymatching

from peeling import decode_repetition


def check_matrix(d):
    h = np.zeros((d - 1, d), dtype=np.uint8)
    for i in range(d - 1):
        h[i, i] = h[i, i + 1] = 1
    return h


def test_same_correction_as_pymatching():
    rng = np.random.default_rng(3)
    for d in (3, 5, 7):
        matcher = pymatching.Matching(check_matrix(d))
        for _ in range(200):
            synd = (rng.random(d - 1) < 0.5).astype(np.uint8)
            expected = matcher.decode(synd).astype(bool)
            assert np.array_equal(decode_repetition(synd, d), expected), (d, synd)
