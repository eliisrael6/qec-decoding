# qec-decoding

Simulations of the repetition code and the rotated surface code, and a union find decoder written for this project. The surface code study uses Stim and PyMatching to estimate thresholds, including how the threshold changes when measurement error is larger than gate error. The union find decoder is benchmarked against PyMatching on the repetition code.

## Motivation

Quantum error correction caught my attention because of one question. If quantum information is so fragile, how can it be protected and recovered without directly observing the errors?

The decoder is where that question gets answered. It has to work out what most likely went wrong using only syndrome measurements, even though those measurements can themselves be unreliable. I wanted to understand how decoders make that call, how their performance changes as noise increases and what limits them. This repo is the first stage. It covers the repetition code, surface code thresholds and a union find decoder of my own.

## What's here

- `src/`: the repetition code with its syndrome decoder and exact formula (`repetition.py`), surface code circuit construction, sampling and threshold estimation (`surface.py`), and the union find decoder (`union_find.py`, `uf_decoder.py`, `peeling.py`).
- `scripts/`: one script per study, each writing a figure to `figures/` and, where relevant, a CSV to `results/`.
- `tests/`: pytest checks for every part, including zero logical errors at p = 0, a smaller logical error rate at larger distance below threshold, and agreement between the union find decoder and PyMatching.

## Results

### (a) Repetition code

One logical bit is stored in d physical bits, each flipping independently with
probability p. The decoder sees only the syndrome (the parities of neighbouring
bits), not the bits themselves. The syndrome determines the error up to a
global flip, so there are two candidate errors, and the decoder picks the one
with fewer flips. Decoding fails exactly when more than half the bits flip, so
the logical error rate is

P_L = Σ_{k > d/2} C(d, k) p^k (1 − p)^(d − k).

The simulation used d = 3, 5, 7 and 12 values of p from 0.05 to 0.5, with
1,000,000 shots per point. It matches this formula within shot noise. All 36
points lie within 2.5σ of the exact value, and χ² = 40.4 over 36 points.

![Repetition code: logical against physical error rate, simulation and exact formula](figures/repetition_threshold.png)

### (b) Surface code threshold

Setup:

- Stim's `surface_code:rotated_memory_z` experiment with rounds = d, for d = 3, 5, 7.
- Uniform circuit level noise at p:
  - depolarising noise after every Clifford gate and on every data qubit at the start of each round
  - bit flips after reset and before measurement
- A minimum weight perfect matching decoder from PyMatching, built from the detector error model that Stim derives from the circuit.

Logical error rates are per d rounds. Each is the probability that the whole
d round memory experiment ends with the wrong logical outcome.

**Threshold estimate: about 0.75%.** This is the d = 5 / d = 7 crossing at
meas_ratio = 1 from the measurement study in (c), which samples p more finely
near the crossing.

Shot noise on this estimate is about 0.01 percentage points. That figure comes
from a parametric bootstrap that resamples each point binomially and repeats
the interpolation. The choice of p grid matters more. The first sweep shown
below used a coarser grid and gave about 0.7% (0.709% for the d = 5 / d = 7
crossing), about 0.04 percentage points lower. So only two significant figures
are reliable. The crossings between other pairs in the first sweep were 0.641%
(d = 3 / d = 5) and 0.669% (d = 3 / d = 7).

Below threshold, larger distance helps. At p = 0.3%, the logical error rate is
0.653% for d = 3, 0.335% for d = 5 and 0.152% for d = 7.

![Surface code: logical against physical error rate for d = 3, 5, 7](figures/surface_threshold.png)

The first sweep used 8 values of p from 0.003 to 0.015, with 500,000 shots per
point. The 1σ binomial error bars are smaller than the markers.

### (c) Measurement error study

Readout is often noisier than gates on current superconducting devices. To
model this, the measurement flip probability is set to meas_ratio × p, and all
other noise stays at p. This applies to the check qubit measurement in every
round and to the final data qubit readout.

The threshold is taken as the point where the d = 5 and d = 7 curves cross.
It is found by interpolating log(logical rate) against log(p) between the two
sampled points either side of the crossing. Each ratio uses 8 values of p,
chosen to bracket its crossing, with 300,000 shots per point.

| meas_ratio | Threshold p | p range sampled |
|---|---|---|
| 0.5 | 0.76% | 0.50% to 1.10% |
| 1 | 0.75% | 0.50% to 1.00% |
| 2 | 0.71% | 0.45% to 0.90% |
| 5 | 0.65% | 0.35% to 0.85% |

![Left: threshold against meas_ratio. Right: logical error curves at meas_ratio = 5](figures/measurement_study.png)

Raising meas_ratio from 1 to 5 lowers the threshold from 0.75% to 0.65%, a
fall of about 13%. This fall is larger than both shot noise and the grid
effect described in (b), but the steps between neighbouring ratios are less
certain. The drop is small because measurement is only one of several noise
locations in each round. A weight four check qubit undergoes four
two qubit gates, each followed by two qubit depolarising noise at p, as well
as a reset with its own flip. Every data qubit is also depolarised once per
round. Measurement adds one flip per check qubit per round, so increasing it
fivefold raises the total noise per round by much less than a fivefold
increase in gate error would.

The 0.5 and 1 results differ by less than 0.02 percentage points, which is about 1σ of shot noise, so they are within noise of each other.

### (d) Union find decoder

A union find decoder for the repetition code, in `src/union_find.py`, `src/uf_decoder.py` and `src/peeling.py`. Clusters grow around each defect and merge until each one holds an even number of defects or reaches the boundary, then peeling picks the correction inside each cluster.

**Accuracy.** It chose the same correction as PyMatching on all 6.4 million sampled shots (d = 3 to 9, p = 0.02 to 0.4) and on every possible syndrome for d = 3 to 11, and both match the exact formula from (a). This is the easy case, since minimum weight decoding is optimal for this code. On the surface code, union find is expected to lose a little accuracy to matching.

**Speed.** Median time per shot over 5 runs, at p = 0.1:

| d | Union find | PyMatching, single call | PyMatching, batch |
|---|---|---|---|
| 5 | 6.2 µs | 2.5 µs |