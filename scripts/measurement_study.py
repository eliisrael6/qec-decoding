import csv
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from surface import crossing, logical_error_rate, make_circuit

SHOTS = 300_000
distances = [3, 5, 7]
# p range per ratio, chosen to bracket the d = 5 / d = 7 crossing, which
# moves down as readout gets noisier
p_ranges = {
    0.5: (0.005, 0.011),
    1: (0.005, 0.010),
    2: (0.0045, 0.009),
    5: (0.0035, 0.0085),
}
N_P = 8

rates = {}  # (ratio, d) -> array of logical rates over that ratio's p values
start = time.time()
for ratio, (p_lo, p_hi) in p_ranges.items():
    p_values = np.geomspace(p_lo, p_hi, N_P)
    for d in distances:
        rates[ratio, d] = np.array([
            logical_error_rate(make_circuit(d, p, ratio), SHOTS, seed=42) for p in p_values
        ])
        print(f"meas_ratio = {ratio}  d = {d}  done ({time.time() - start:.0f}s)")

thresholds = {}
for ratio, (p_lo, p_hi) in p_ranges.items():
    p_values = np.geomspace(p_lo, p_hi, N_P)
    thresholds[ratio] = crossing(p_values, rates[ratio, 5], rates[ratio, 7])
    print(f"meas_ratio = {ratio}  threshold ~ {thresholds[ratio]:.5f}")

csv_out = ROOT / "results" / "measurement_study.csv"
csv_out.parent.mkdir(exist_ok=True)
with open(csv_out, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["meas_ratio", "d", "p", "logical_error_rate", "shots"])
    for ratio, (p_lo, p_hi) in p_ranges.items():
        p_values = np.geomspace(p_lo, p_hi, N_P)
        for d in distances:
            for p, rate in zip(p_values, rates[ratio, d]):
                writer.writerow([ratio, d, p, rate, SHOTS])
print(f"saved {csv_out}")

fig, (ax_th, ax_curves) = plt.subplots(1, 2, figsize=(12, 5))

ratios = list(p_ranges)
ax_th.plot(ratios, [thresholds[r] for r in ratios], "o-")
ax_th.set_xscale("log")
ax_th.minorticks_off()
ax_th.set_xticks(ratios, [str(r) for r in ratios])
ax_th.set_xlabel("Measurement error / gate error (meas_ratio)")
ax_th.set_ylabel("Threshold p (d = 5 / d = 7 crossing)")
# start at zero so the size of the drop isn't exaggerated
ax_th.set_ylim(bottom=0)
ax_th.set_title("Threshold vs readout noise")
ax_th.grid(True, which="both", alpha=0.3)

ratio = 5
p_values = np.geomspace(*p_ranges[ratio], N_P)
for d in distances:
    r = rates[ratio, d]
    # 1 sigma binomial error bars
    err = np.sqrt(r * (1 - r) / SHOTS)
    ax_curves.errorbar(p_values, r, yerr=err, fmt="o-", ms=4, label=f"d = {d}")
ax_curves.axvline(thresholds[ratio], color="k", ls="--", lw=1, label="d = 5 / 7 crossing")
ax_curves.set_xscale("log")
ax_curves.set_yscale("log")
ax_curves.set_xlabel("Gate error rate p")
ax_curves.set_ylabel("Logical error rate (per d rounds)")
ax_curves.set_title(f"meas_ratio = {ratio}")
ax_curves.legend(fontsize=8)
ax_curves.grid(True, which="both", alpha=0.3)

fig_out = ROOT / "figures" / "measurement_study.png"
fig_out.parent.mkdir(exist_ok=True)
fig.tight_layout()
fig.savefig(fig_out, dpi=150)
print(f"saved {fig_out}")
