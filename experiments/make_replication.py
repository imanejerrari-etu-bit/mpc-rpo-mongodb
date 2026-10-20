"""Second-platform replication schedule: burst scenario, the 4 key controllers, interleaved, engine tag 'mongodbci'.
    python experiments/make_replication.py --specs tuned_specs.json --reps 6 --out schedule_ci.csv
"""
import argparse, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mpcrpo.schedule import make_schedule, write_schedule
from mpcrpo.sim import BURST
from make_schedule import controllers_from_tuned

KEY = ["PI_tuned", "PI_FF", "FF_obs", "MPC_persist"]
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--specs", required=True); ap.add_argument("--reps", type=int, default=6)
    ap.add_argument("--seed", type=int, default=2029); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ctl = {k: v for k, v in controllers_from_tuned(a.specs).items() if k in KEY}
    rows = make_schedule([{"name": "mongodbci"}], [BURST], ctl, a.reps, a.seed)
    write_schedule(rows, a.out)
    print(f"{len(rows)} runs -> {a.out} (~{len(rows) * 5.7 / 60:.1f} h)")
