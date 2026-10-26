import csv
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from surface import logical_error_rate, make_circuit

SHOTS = 500_000
distances = [3, 5, 7]
p_values = np.geomspace(0.003, 0.015, 8)

rows = []
start = time.time()
for d in distances:
    for p in p_values:
        rate = logical_error_rate(make_circuit(d, p), SHOTS, seed=42)
        rows.append((d, p, rate))
        print(f"d = {d}  p = {p:.4f}  logical = {rate:.5f}  ({time.time() - start:.0f}s)")

csv_out = ROOT / "results" / "surface_threshold.csv"
csv_out.parent.mkdir(exist_ok=True)
with open(csv_out, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["d", "p", "logical_error_rate", "shots"])
    for d, p, rate in rows:
        writer.writerow([d, p, rate, SHOTS])
print(f"saved {csv_out}")

fig, ax = plt.subplots(figsize=(7, 5))

for d in distances:
    rates = np.array([rate for dd, _, rate in rows if dd == d])
    # 1 sigma binomial error bars
    err = np.sqrt(rates * (1 - rates) / SHOTS)
    ax.errorbar(p_values, rates, yerr=err, fmt="o-", ms=4, label=f"d = {d}")

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Physical error rate p")
ax.set_ylabel("Logical error rate (per d rounds)")
ax.set_title("Rotated surface code, circuit level noise, MWPM decoder")
ax.legend(fontsize=8)
ax.grid(True, which="both", alpha=0.3)

fig_out = ROOT / "figures" / "surface_threshold.png"
fig_out.parent.mkdir(exist_ok=True)
fig.tight_layout()
fig.savefig(fig_out, dpi=150)
print(f"saved {fig_out}")
