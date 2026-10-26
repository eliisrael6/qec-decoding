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


def make_circuit(d, p):
    # the same p for every noise channel stim offers on this circuit
    return stim.Circuit.generated(
        "surface_code:rotated_memory_z",
        distance=d,
        rounds=d,
        after_clifford_depolarization=p,
        after_reset_flip_probability=p,
        before_measure_flip_probability=p,
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
