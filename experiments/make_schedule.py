"""Create the randomised, interleaved schedule. Replace CONTROLLERS by the TUNED specs (tune_sim.py).

    python experiments/make_schedule.py --engine mongodb --pilot --out schedule_pilot.csv     (n=3 per cell)
    python experiments/make_schedule.py --engine mongodb --out schedule_main.csv              (5 / 10 / 6)
"""
import argparse, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mpcrpo.schedule import make_schedule, write_schedule
from mpcrpo.sim import STATIONARY, BURST, LOW_LOAD

CONTROLLERS = {                      # placeholders: replace with the tuned specs
    "PI_default":  {"type": "pi", "kp": 0.3, "ki": 0.05, "antiwindup": "clamp"},
    "PI_tuned":    {"type": "pi", "kp": 0.3, "ki": 0.05, "antiwindup": "backcalc", "filter_alpha": 0.5},
    "PI_FF":       {"type": "pi", "ff": True, "bias_alpha": 0.1, "kp": 0.3, "ki": 0.05, "antiwindup": "backcalc"},
    "FF_obs":      {"type": "pi", "ff": True, "bias_alpha": 0.3, "kp": 0.0, "ki": 0.0},
    "MPC_persist": {"type": "mpc", "predictor": "persistence"},
    "MPC_ma":      {"type": "mpc", "predictor": "ma"},
    "MPC_arima":   {"type": "mpc", "predictor": "arima"},
}
def controllers_from_tuned(path):
    """PI_default = untuned gains (naive baseline); PI_tuned / PI_FF / MPC_* = best spec of each family (equal budget)."""
    import json
    sp = json.load(open(path))["specs"]
    return {"PI_default": CONTROLLERS["PI_default"], "PI_tuned": sp["PI"], "PI_FF": sp["PI_FF"], "FF_obs": sp["FF_obs"],
            "MPC_persist": sp["MPC_persist"], "MPC_ma": sp["MPC_ma"], "MPC_arima": sp["MPC_arima"]}


MAIN_REPS = {"stationary": 5, "burst": 10, "lowload": 6}
PILOT_REPS = {"stationary": 3, "burst": 3, "lowload": 3}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default="mongodb"); ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--seed", type=int, default=2026); ap.add_argument("--out", required=True)
    ap.add_argument("--specs", default=None, help="tuned_specs.json produced by tune_sim.py")
    a = ap.parse_args()
    if a.specs:
        CONTROLLERS = controllers_from_tuned(a.specs)
    reps = PILOT_REPS if a.pilot else MAIN_REPS
    rows = make_schedule([{"name": a.engine}], [STATIONARY, BURST, LOW_LOAD], CONTROLLERS, reps, a.seed)
    print("controleurs :", ", ".join(CONTROLLERS))
    write_schedule(rows, a.out)
    print(f"{len(rows)} runs -> {a.out}  (~{len(rows) * 5.7 / 60:.1f} h : 300 s + 30 s cooldown + overhead)")
