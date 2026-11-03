import numpy as np

from peeling import decode_repetition, spanning_forest
from repetition import decode
from uf_decoder import grow, repetition_graph


def test_spanning_forest_roots_at_boundary():
    # d = 5, error on bit 0: grown edges are 0 (boundary to check 0) and 1
    n_nodes, edges, boundary = repetition_graph(5)
    _, grown = grow(n_nodes, edges, boundary, defects=[0])
    order, parent_edge = spanning_forest(n_nodes, edges, grown, boundary)
    assert order[0] == boundary
    assert parent_edge[boundary] is None
    assert parent_edge[0] == 0 and parent_edge[1] == 1


def test_no_error_no_correction():
    assert not decode_repetition(np.zeros(4, dtype=bool), 5).any()


def test_every_single_error_is_corrected():
    for d in (3, 5, 7):
        for i in range(d):
            error = np.zeros(d, dtype=bool)
            error[i] = True
            syndrome = error[:-1] ^ error[1:]
            assert np.array_equal(decode_repetition(syndrome, d), error)


def test_correction_always_explains_the_syndrome():
    # whatever the error, the correction must produce the same syndrome
    rng = np.random.default_rng(0)
    for d in (3, 5, 7):
        for _ in range(300):
            error = rng.random(d) < 0.3
            syndrome = error[:-1] ^ error[1:]
            c = decode_repetition(syndrome, d)
            assert np.array_equal(c[:-1] ^ c[1:], syndrome)


def test_agrees_with_phase1_decoder():
    # the phase 1 decoder is optimal for this code, so union find should match it
    rng = np.random.default_rng(1)
    for d in (3, 5, 7):
        errors = rng.random((300, d)) < 0.2
        syndromes = errors[:, :-1] ^ errors[:, 1:]
        expected = decode(syndromes)
        for k in range(300):
            assert np.array_equal(decode_repetition(syndromes[k], d), expected[k])