"""
Repetition code under independent bit flip noise.

One logical bit is stored in d physical bits. Each bit flips with
probability p. The decoder only gets to see the syndrome (parities of
neighbouring bits), never the bits themselves, which is the same
constraint a real quantum decoder works under.
"""

from math import comb

import numpy as np


def sample_errors(d, p, shots, rng):
    # each row is one shot, True means that bit flipped
    return rng.random((shots, d)) < p


def syndrome(errors):
    # parity of each neighbouring pair: s_i = e_i XOR e_(i+1)
    return errors[:, :-1] ^ errors[:, 1:]


def decode(synd):
    """
    Work out a correction from the syndrome alone.

    The syndrome fixes the error pattern up to a global flip, so there
    are always exactly two candidates: one starting with e_0 = 0 and its
    complement. Pick whichever has fewer flips (the more likely one when
    p < 0.5).
    """
    shots, n_checks = synd.shape
    d = n_checks + 1

    candidate = np.zeros((shots, d), dtype=bool)
    # e_k = s_0 XOR s_1 XOR ... XOR s_(k-1), assuming e_0 = 0
    candidate[:, 1:] = np.cumsum(synd, axis=1) % 2 == 1

    too_heavy = candidate.sum(axis=1) > d // 2
    candidate[too_heavy] = ~candidate[too_heavy]
    return candidate


def logical_error_rate(d, p, shots, rng=None):
    if rng is None:
        rng = np.random.default_rng()

    errors = sample_errors(d, p, shots, rng)
    correction = decode(syndrome(errors))

    # error and correction have the same syndrome, so what's left over is
    # either nothing (success) or every bit flipped (logical error)
    leftover = errors ^ correction
    return leftover[:, 0].mean()


def exact_rate(d, p):
    # decoder fails when more than half the bits flip
    return sum(comb(d, k) * p**k * (1 - p) ** (d - k) for k in range(d // 2 + 1, d + 1))
