import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from surface import crossing

rng = np.random.default_rng(0)


def load(name):
    with open(ROOT / "results" / name) as f:
        return list(csv.DictReader(f))


def curves(rows, key=None):
    out = {}
    for r in rows:
        k = (r.get(key), int(r["d"])) if key else int(r["d"])
        out.setdefault(k, []).append((float(r["p"]), float(r["logical_error_rate"]), int(r["shots"])))
    return {k: np.array(sorted(v)) for k, v in out.items()}


def boot(p, a, b, shots, n=2000):
    # resample each point binomially and redo the crossing
    xs = []
    for _ in range(n):
        ra = rng.binomial(shots, a) / shots
        rb = rng.binomial(shots, b) / shots
        xs.append(crossing(p, ra, rb))
    xs = np.array(xs)
    return np.nanstd(xs), np.isnan(xs).mean(), xs


print("first sweep")
c = curves(load("surface_threshold.csv"))
p = c[3][:, 0]
shots = int(c[3][0, 2])
for d in (3, 5, 7):
    print(d, [f"{x:.5f}" for x in c[d][:, 1]])
for a, b in ((3, 5), (3, 7), (5, 7)):
    x = crossing(p, c[a][:, 1], c[b][:, 1])
    sd, nanf, _ = boot(p, c[a][:, 1], c[b][:, 1], shots)
    print(f"cross {a}/{b}: {x:.5f} +- {sd:.5f}")

print("measurement study")
c = curves(load("measurement_study.csv"), "meas_ratio")
samples = {}
for ratio in ("0.5", "1", "2", "5"):
    p = c[ratio, 5][:, 0]
    shots = int(c[ratio, 5][0, 2])
    x = crossing(p, c[ratio, 5][:, 1], c[ratio, 7][:, 1])
    sd, nanf, xs = boot(p, c[ratio, 5][:, 1], c[ratio, 7][:, 1], shots)
    samples[ratio] = xs
    print(f"ratio {ratio}: {x:.5f} +- {sd:.5f} (nan frac {nanf}) p range {p[0]:.4f}-{p[-1]:.4f} shots {shots}")
diff = samples["1"] - samples["0.5"]
print("1 minus 0.5:", np.nanmean(diff), np.nanstd(diff))
