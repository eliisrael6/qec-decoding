import csv
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pymatching

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from peeling import decode_repetition
from repetition import exact_rate, sample_errors, syndrome

ACC_SHOTS = 200_000
acc_distances = [3, 5, 7, 9]
p_values = np.geomspace(0.02, 0.4, 8)

SPEED_P = 0.1
speed_distances = [5, 11, 21, 51, 101]
# shots used to time each decoder, fewer for the slow one
UF_SHOTS = 5_000
SINGLE_SHOTS = 20_000
BATCH_SHOTS = 100_000

rng = np.random.default_rng(42)


def check_matrix(d):
    # check i compares bits i and i + 1, so bits 0 and d - 1 sit on one check each
    h = np.zeros((d - 1, d), dtype=np.uint8)
    for i in range(d - 1):
        h[i, i] = h[i, i + 1] = 1
    return h


def uf_decode_all(synd, d):
    return np.array([decode_repetition(s, d) for s in synd])


rows = []
start = time.time()

# accuracy: both decoders see exactly the same syndromes
for d in acc_distances:
    matcher = pymatching.Matching(check_matrix(d))
    for p in p_values:
        errors = sample_errors(d, p, ACC_SHOTS, rng)
        synd = syndrome(errors).astype(np.uint8)
        uf = uf_decode_all(synd, d)
        pm = matcher.decode_batch(synd).astype(bool)

        # any bit left over means a logical error (it is all or nothing here)
        uf_rate = (uf ^ errors).any(axis=1).mean()
        pm_rate = (pm ^ errors).any(axis=1).mean()
        mismatches = int((uf != pm).any(axis=1).sum())
        rows.append({"study": "accuracy", "d": d, "p": p, "shots": ACC_SHOTS,
                     "uf_rate": uf_rate, "pm_rate": pm_rate, "exact_rate": exact_rate(d, p),
                     "mismatches": mismatches})
        print(f"d = {d}  p = {p:.3f}  uf = {uf_rate:.5f}  pm = {pm_rate:.5f}  "
              f"mismatches = {mismatches}  ({time.time() - start:.0f}s)")


TIMING_REPEATS = 5


def per_shot_us(fn, synd):
    # median over several runs, since a single timing is noisy
    times = []
    for _ in range(TIMING_REPEATS):
        t = time.perf_counter()
        fn(synd)
        times.append((time.perf_counter() - t) / len(synd) * 1e6)
    return np.median(times)


# speed: per shot time at fixed p
for d in speed_distances:
    matcher = pymatching.Matching(check_matrix(d))
    synd = syndrome(sample_errors(d, SPEED_P, BATCH_SHOTS, rng)).astype(np.uint8)

    uf_us = per_shot_us(lambda s: [decode_repetition(x, d) for x in s], synd[:UF_SHOTS])
    single_us = per_shot_us(lambda s: [matcher.decode(x) for x in s], synd[:SINGLE_SHOTS])
    batch_us = per_shot_us(matcher.decode_batch, synd)
    rows.append({"study": "speed", "d": d, "p": SPEED_P, "uf_us": uf_us,
                 "pm_single_us": single_us, "pm_batch_us": batch_us})
    print(f"d = {d}  uf = {uf_us:.2f} us  pm single = {single_us:.2f} us  "
          f"pm batch = {batch_us:.3f} us  ({time.time() - start:.0f}s)")

total = sum(r["mismatches"] for r in rows if r["study"] == "accuracy")
print(f"total mismatched corrections: {total}")

csv_out = ROOT / "results" / "uf_benchmark.csv"
csv_out.parent.mkdir(exist_ok=True)
fields = ["study", "d", "p", "shots", "uf_rate", "pm_rate", "exact_rate", "mismatches",
          "uf_us", "pm_single_us", "pm_batch_us"]
with open(csv_out, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
print(f"saved {csv_out}")

fig, (ax_acc, ax_speed) = plt.subplots(1, 2, figsize=(12, 5))

p_fine = np.geomspace(0.02, 0.4, 200)
for d in acc_distances:
    acc = [r for r in rows if r["study"] == "accuracy" and r["d"] == d]
    uf = np.array([r["uf_rate"] for r in acc])
    pm = np.array([r["pm_rate"] for r in acc])
    # 1 sigma binomial error bars
    err = np.sqrt(uf * (1 - uf) / ACC_SHOTS)

    line = ax_acc.plot(p_fine, [exact_rate(d, p) for p in p_fine], lw=1, label=f"d = {d} (exact)")
    colour = line[0].get_color()
    ax_acc.errorbar(p_values, uf, yerr=err, fmt="o", ms=5, color=colour)
    ax_acc.plot(p_values, pm, "x", ms=8, color=colour)

# marker key, shared by every distance
ax_acc.plot([], [], "o", color="grey", label="union find")
ax_acc.plot([], [], "x", color="grey", label="PyMatching")
ax_acc.set_xscale("log")
ax_acc.set_yscale("log")
ax_acc.set_xticks([0.02, 0.05, 0.1, 0.2, 0.4], ["0.02", "0.05", "0.1", "0.2", "0.4"])
ax_acc.xaxis.set_minor_formatter(plt.NullFormatter())
ax_acc.set_xlabel("Physical error rate p")
ax_acc.set_ylabel("Logical error rate")
ax_acc.set_title("Repetition code, same syndromes for both decoders")
ax_acc.legend(fontsize=8)
ax_acc.grid(True, which="both", alpha=0.3)

speed = [r for r in rows if r["study"] == "speed"]
ax_speed.plot(speed_distances, [r["uf_us"] for r in speed], "o-", label="union find")
ax_speed.plot(speed_distances, [r["pm_single_us"] for r in speed], "s-",
              label="PyMatching, single shot decode")
ax_speed.plot(speed_distances, [r["pm_batch_us"] for r in speed], "^-",
              label="PyMatching, decode_batch")
ax_speed.set_xscale("log")
ax_speed.set_yscale("log")
ax_speed.set_xlabel("Distance d")
ax_speed.set_ylabel("Time per shot (µs)")
ax_speed.set_title(f"Decoding time at p = {SPEED_P}")
ax_speed.legend(fontsize=8)
ax_speed.grid(True, which="both", alpha=0.3)

fig_out = ROOT / "figures" / "uf_benchmark.png"
fig_out.parent.mkdir(exist_ok=True)
fig.tight_layout()
fig.savefig(fig_out, dpi=150)
print(f"saved {fig_out}")
