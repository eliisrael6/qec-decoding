import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from repetition import exact_rate, logical_error_rate

SHOTS = 1_000_000
distances = [3, 5, 7]
p_values = np.geomspace(0.05, 0.5, 12)
p_fine = np.geomspace(0.05, 0.5, 200)

rng = np.random.default_rng(42)
fig, ax = plt.subplots(figsize=(7, 5))

for d in distances:
    sim = np.array([logical_error_rate(d, p, SHOTS, rng) for p in p_values])
    # 1 sigma binomial error bars
    err = np.sqrt(sim * (1 - sim) / SHOTS)

    line = ax.plot(p_fine, [exact_rate(d, p) for p in p_fine], label=f"d = {d} (exact)")
    ax.errorbar(p_values, sim, yerr=err, fmt="o", ms=4, color=line[0].get_color(),
                label=f"d = {d} (simulated)")

ax.plot(p_fine, p_fine, "k--", lw=1, label="no encoding")

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Physical error rate p")
ax.set_ylabel("Logical error rate")
ax.set_title("Repetition code, bit flip noise, decoder sees syndrome only")
ax.legend(fontsize=8)
ax.grid(True, which="both", alpha=0.3)

out = Path(__file__).resolve().parent.parent / "figures" / "repetition_threshold.png"
out.parent.mkdir(exist_ok=True)
fig.tight_layout()
fig.savefig(out, dpi=150)
print(f"saved {out}")
