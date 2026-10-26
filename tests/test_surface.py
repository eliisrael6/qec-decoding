from surface import logical_error_rate, make_circuit


def test_no_noise_no_errors():
    assert logical_error_rate(make_circuit(3, 0.0), 1000) == 0.0


def test_bigger_distance_helps_below_threshold():
    # p = 0.003 is well below the ~0.7% threshold, so d = 5 should win clearly
    shots = 100_000
    rate3 = logical_error_rate(make_circuit(3, 0.003), shots, seed=1)
    rate5 = logical_error_rate(make_circuit(5, 0.003), shots, seed=2)
    assert rate5 < rate3
