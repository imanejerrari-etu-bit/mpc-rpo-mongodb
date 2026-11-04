"""Amendment 6, block B: tuning of the operator-style rule-based baseline (`Threshold`) for the two cells (step burst, periodic), same protocol as the other
families (60 random candidates, RNG seed 0, tuning seeds 1000-1002, robust objective = half nominal plant, half stress plant with one more tick of delay;
objective = 0.5 x stationary error + 0.5 x error over the disturbance window). The static default (J = 100 ms) has nothing to tune. FF+obs specs are
taken from the earlier tuning files (burst: tuned_specs.json; periodic: tuned_specs_scn.json). Simulated results are NOT evidence.

    python experiments\\tune_baselines.py --budget 60 --tune-seeds 3 --out tuned_specs_base.json
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from mpcrpo.config import Common
from mpcrpo.plant import PlantParams
from mpcrpo.sim import BURST, PERIODIC
from tune_sim import STRESS
from tune_scenarios import obj

CELLS = {"burst": BURST, "periodic": PERIODIC}
RNG_RANGES = {"hi": (1.05, 2.0), "lo": (0.4, 0.98), "down": (0.15, 0.95), "up": (1.02, 1.5)}
COOLDOWNS = [2, 4, 8, 16]


def draw(r):
    s = {"type": "threshold"}
    for k, (a, b) in RNG_RANGES.items():
        s[k] = float(r.uniform(a, b))
    s["cooldown"] = int(r.choice(COOLDOWNS))
    return s


def flags(s):
    out = [f"{k}={s[k]:.3g} (bord)" for k, (a, b) in RNG_RANGES.items() if not 0.05 <= (s[k] - a) / (b - a) <= 0.95]
    if s["cooldown"] in (COOLDOWNS[0], COOLDOWNS[-1]):
        out.append(f"cooldown={s['cooldown']} (extreme du jeu)")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=60); ap.add_argument("--tune-seeds", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--out", default="tuned_specs_base.json")
    ap.add_argument("--main", default="tuned_specs.json"); ap.add_argument("--scn", default="tuned_specs_scn.json")
    a = ap.parse_args()
    C, pp, seeds, t0 = Common(), PlantParams(), list(range(1000, 1000 + a.tune_seeds)), time.time()
    ff = {"burst": json.load(open(a.main))["specs"]["FF_obs"], "periodic": json.load(open(a.scn))["specs"]["periodic"]["FF_obs"]}
    doc = {"budget": a.budget, "tune_seeds": seeds, "specs": {}, "edge_flags": {}}
    for cell, scn in CELLS.items():
        rng = np.random.default_rng(a.seed)
        cands = [draw(rng) for _ in range(a.budget)]
        scored = sorted(((0.5 * obj(c, C, pp, seeds, scn, 0) + 0.5 * obj(c, C, STRESS, seeds, scn, 1), c) for c in cands), key=lambda x: x[0])
        best = scored[0][1]
        doc["specs"][cell] = {"Threshold": best, "FF_obs": ff[cell], "Static": {"type": "static"}}
        doc["edge_flags"][cell] = flags(best)
        print(f"{cell:9s} Threshold score {scored[0][0]:6.2f} {json.dumps(best)}  ({time.time() - t0:.0f} s)", flush=True)
        if doc["edge_flags"][cell]:
            print(f"   ATTENTION optimum au bord : {', '.join(doc['edge_flags'][cell])}", flush=True)
    json.dump(doc, open(a.out, "w"), indent=1)
    print(f"termine -> {a.out}")
