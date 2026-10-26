"""
Rotated surface code memory experiment under circuit level noise.

Stim builds the full syndrome extraction circuit (d rounds of stabiliser
measurements on a distance d patch) and samples it. PyMatching decodes
the detection events with minimum weight perfect matching, using the
error model Stim derives from the circuit itself.
"""

import numpy as np
import pymatching
import stim


def make_circuit(d, p, meas_ratio=1.0):
    # p for every noise channel stim offers, except readout which is scaled
    # by meas_ratio to model measurement being worse (or better) than gates
    return stim.Circuit.generated(
        "surface_code:rotated_memory_z",
        distance=d,
        rounds=d,
        after_clifford_depolarization=p,
        after_reset_flip_probability=p,
        before_measure_flip_probability=meas_ratio * p,
        before_round_data_depolarization=p,
    )


def logical_error_rate(circuit, shots, seed=None):
    sampler = circuit.compile_detector_sampler(seed=seed)
    detections, observables = sampler.sample(shots, separate_observables=True)

    # decompose_errors splits hyperedges into graph edges so matching can use them
    dem = circuit.detector_error_model(decompose_errors=True)
    matcher = pymatching.Matching.from_detector_error_model(dem)
    predictions = matcher.decode_batch(detections)

    # a shot fails when the decoder's guess for the logical flip is wrong
    wrong = np.any(predictions != observables, axis=1)
    return wrong.mean()


def crossing(p_values, rates_small, rates_large):
    """
    Estimate the threshold as the p where two distances' curves cross.

    Below threshold the larger code has the lower rate, above it the
    higher rate. Find the first pair of neighbouring p values where that
    flips and interpolate log(rate) against log(p) linearly between them.
    Returns nan if the curves don't cross inside the sweep.
    """
    log_p = np.log(p_values)
    # log of the ratio is negative below threshold and positive above
    gap = np.log(rates_large) - np.log(rates_small)

    for i in range(len(gap) - 1):
        if gap[i] < 0 <= gap[i + 1]:
            # where the straight line between the two points hits zero
            frac = -gap[i] / (gap[i + 1] - gap[i])
            return np.exp(log_p[i] + frac * (log_p[i + 1] - log_p[i]))
    return np.nan
