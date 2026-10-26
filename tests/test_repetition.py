import numpy as np

from repetition import decode, exact_rate, logical_error_rate, syndrome


def test_syndrome_single_flip():
    # flip on the middle bit of d=5 should light up the two checks either side
    errors = np.array([[False, False, True, False, False]])
    assert syndrome(errors).tolist() == [[False, True, True, False]]


def test_every_single_flip_is_corrected():
    d = 7
    for i in range(d):
        errors = np.zeros((1, d), dtype=bool)
        errors[0, i] = True
        assert np.array_equal(decode(syndrome(errors)), errors)


def test_no_noise_no_errors():
    assert logical_error_rate(5, 0.0, 1000) == 0.0


def test_d1_is_unprotected():
    # one bit means no checks, so the logical rate should just be p
    rng = np.random.default_rng(1)
    rate = logical_error_rate(1, 0.2, 200_000, rng)
    assert abs(rate - 0.2) < 0.005


def test_simulation_matches_exact():
    rng = np.random.default_rng(2)
    shots = 200_000
    for d in (3, 5, 7):
        for p in (0.05, 0.2, 0.4):
            expected = exact_rate(d, p)
            sim = logical_error_rate(d, p, shots, rng)
            sigma = np.sqrt(expected * (1 - expected) / shots)
            assert abs(sim - expected) < 5 * sigma + 1e-6


def test_exact_d3():
    # 3p^2(1-p) + p^3 from the notes
    p = 0.1
    assert np.isclose(exact_rate(3, p), 3 * p**2 * (1 - p) + p**3)
