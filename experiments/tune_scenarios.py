"""Amendment 5: equal-budget re-tuning of the four compared families for EACH new cell (disturbance profile x actuation delay),
on the calibrated simulator, same protocol as tune_sim.py (60 random candidates, same family generators and RNG seed, tuning seeds disjoint from
test seeds, robust objective: half nominal plant, half stress plant with one more tick of delay). Objective = 0.5 * stationary error + 0.5 * error
over the disturbance window of the target scenario. Simulated results are NOT evidence.

    python experiments\\tune_scenarios.py --budget 60 --tune-seeds 3 --out tuned_specs_scn.json
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from mpcrpo.config import Common
from mpcrpo.plant import PlantParams
from mpcrpo.sim import STATIONARY, RAMP, PERIODIC
from tune_sim import FAMILIES, STRESS, evaluate, edge_flags

CELLS = {"ramp": (RAMP, 0), "periodic": (PERIODIC, 0), "periodicd1": (PERIODIC, 2)}      # name -> (scenario, delay in ticks of 0.5 s)
FAMS = {"PI_tuned": "PI", "FF_obs": "FF_obs", "MPC_persist": "MPC_persist", "MPC_arima": "MPC_arima"}


def obj(spec, C, pp, seeds, scn, delay):
    o = evaluate(spec, C, pp, seeds, [STATIONARY, scn], delay=delay)
    return 0.5 * np.mean(o["stationary"]["mae"]) + 0.5 * np.mean(o[scn["name"]]["mae_burst"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=60); ap.add_argument("--tune-seeds", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--out", default="tuned_specs_scn.json")
    ap.add_argument("--cells", nargs="+", default=list(CELLS)); ap.add_argument("--fams", nargs="+", default=list(FAMS))
    a = ap.parse_args()
    C, pp, seeds, t0 = Common(), PlantParams(), list(range(1000, 1000 + a.tune_seeds)), time.time()
    doc = json.load(open(a.out)) if os.path.exists(a.out) else {"budget": a.budget, "tune_seeds": seeds, "specs": {}, "edge_flags": {}}
    doc["cells"] = {c: {"scenario": CELLS[c][0], "delay_ticks": CELLS[c][1]} for c in CELLS}
    for cell in a.cells:                                       # resumable: a finished (cell, family) is kept and skipped
        scn, d = CELLS[cell]
        for lab in a.fams:
            if lab in doc["specs"].get(cell, {}):
                print(f"{cell:10s} {lab:12s} deja fait, ignore", flush=True)
                continue
            rng = np.random.default_rng(a.seed)
            cands = [FAMILIES[FAMS[lab]](rng) for _ in range(a.budget)]
            scored = sorted(((0.5 * obj(c, C, pp, seeds, scn, d) + 0.5 * obj(c, C, STRESS, seeds, scn, d + 1), c) for c in cands), key=lambda x: x[0])
            doc["specs"].setdefault(cell, {})[lab], doc["edge_flags"].setdefault(cell, {})[lab] = scored[0][1], edge_flags(scored[0][1])
            json.dump(doc, open(a.out, "w"), indent=1)
            print(f"{cell:10s} {lab:12s} score {scored[0][0]:6.2f} {json.dumps(scored[0][1])}  ({time.time() - t0:.0f} s)", flush=True)
            if doc["edge_flags"][cell][lab]:
                print(f"   ATTENTION optimum au bord : {', '.join(doc['edge_flags'][cell][lab])}", flush=True)
    print(f"termine -> {a.out}")
