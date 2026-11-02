"""Coup d'oeil sur les runs deja termines (aucun test statistique, aucune exclusion) :
    python experiments\\quick_look.py --raw data\\raw --controllers PI_fast PI_tuned FF_obs --min-rep 24
"""
import argparse, glob, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from mpcrpo.config import Common
from mpcrpo.metrics import run_metrics

ap = argparse.ArgumentParser()
ap.add_argument("--raw", default="data/raw"); ap.add_argument("--controllers", nargs="+", default=["PI_fast", "PI_tuned", "FF_obs"])
ap.add_argument("--min-rep", type=int, default=1)
a = ap.parse_args()
rows = {}
for f in sorted(glob.glob(os.path.join(a.raw, "mongodb_burst_*.json"))):
    if ".INVALID_" in f:
        continue
    j = json.load(open(f))
    if not (j.get("complete") and j.get("valid", True)):
        continue
    p = j["run_uid"].split("_"); ctl, rep = "_".join(p[2:-1]), int(p[-1][3:])
    if ctl not in a.controllers or rep < a.min_rep:
        continue
    rec = {k: np.asarray(j[k]) for k in ("t", "flush", "sync", "bytes", "J", "tps") if k in j}
    m = run_metrics(rec, Common(), j["config"]["scenario"])
    rows.setdefault(ctl, []).append((rep, m))
for ctl in a.controllers:
    r = rows.get(ctl, [])
    print(f"\n{ctl}: {len(r)} run(s) valides")
    for rep, m in sorted(r):
        print(f"  rep{rep:02d}  erreur rafale {m['mae_burst_pct']:6.2f} %   pic {m['peak_ratio']:5.2f} x V*   recup {m['recovery_s']:5.1f} s   saturation {100 * m['sat_frac']:4.1f} %")
    if r:
        print(f"  moyenne erreur rafale {np.mean([m['mae_burst_pct'] for _, m in r]):.2f} %   pic {np.mean([m['peak_ratio'] for _, m in r]):.2f}")
