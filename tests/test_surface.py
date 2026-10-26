import numpy as np

from surface import crossing, logical_error_rate, make_circuit


def test_meas_ratio_one_is_default():
    assert make_circuit(5, 0.004, meas_ratio=1.0) == make_circuit(5, 0.004)


def test_crossing_of_straight_lines():
    # on log-log axes these are lines of slope 2 and 3 meeting at p = 0.01
    p = np.array([0.004, 0.008, 0.016, 0.032])
    small = (p / 0.01) ** 2
    large = (p / 0.01) ** 3
    assert np.isclose(crossing(p, small, large), 0.01)


def test_no_noise_no_errors():
    assert logical_error_rate(make_circuit(3, 0.0), 1000) == 0.0


def test_bigger_distance_helps_below_threshold():
    # p = 0.003 is well below the ~0.7% threshold, so d = 5 should win clearly
    shots = 100_000
    rate3 = logical_error_rate(make_circuit(3, 0.003), shots, seed=1)
    rate5 = logical_error_rate(make_circuit(5, 0.003), shots, seed=2)
    assert rate5 < rate3
