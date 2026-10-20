"""SMOKE TEST on the real MongoDB: two short closed-loop runs (PI_FF then MPC_persist), ~4 min.
It checks the whole chain (counters -> sensor -> controller -> setParameter -> load) before the pilot.
Prerequisites: kubectl port-forward svc/mongodb 27018:27017 open ; MONGO_USER / MONGO_PASSWORD loaded ;
pods stable (kubectl get pods).

    python experiments/smoke_cluster.py
"""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from mpcrpo.config import Common
from mpcrpo.runner import run_one
from mpcrpo.metrics import window_v

SPECS = {"PI_FF": {"type": "pi", "ff": True, "bias_alpha": 0.1, "kp": 0.3, "ki": 0.05, "antiwindup": "backcalc"},
         "MPC_persist": {"type": "mpc", "predictor": "persistence"}}
SCN = {"name": "smoke", "tps0": 400.0, "burst": True, "burst_start": 45.0, "burst_dur": 25.0, "tps1": 1600.0}


def main(adapter_factory=None, out="data/smoke", cooldown=20, duration=95.0):
    if adapter_factory is None:
        from mpcrpo.adapters.mongo_adapter import MongoAdapter as adapter_factory
    C = Common(duration_s=duration, warmup_s=20.0)
    os.makedirs(out, exist_ok=True)
    stamp = time.strftime("%H%M%S")
    for name, spec in SPECS.items():
        row = {"run_uid": f"smoke_{name}_{stamp}", "seed": "1", "spec": json.dumps(spec), "scn": json.dumps(SCN)}
        print(f"\n=== {name} ({duration:.0f} s) ...", flush=True)
        ad = adapter_factory()
        status = run_one(row, ad, C, out)
        rep = ad.report()
        path = os.path.join(out, row["run_uid"] + ".json")
        if status == "invalid":
            import glob
            path = sorted(glob.glob(os.path.join(out, row["run_uid"] + ".INVALID_*.json")))[-1]
        d = json.load(open(path))
        rec = {k: np.array(d[k], float) for k in ("t", "flush", "sync", "bytes", "J", "tps")}
        v10 = window_v(rec, 20) / C.v_star_B
        t = rec["t"]
        seg = lambda a, b: float(np.nanmean(v10[(t >= a) & (t < b)]))
        print(f"statut: {status} | valide: {rep['valid']} {rep.get('reasons') or ''}")
        print(f"acked/offered {rep['acked_over_offered']} | erreurs d'insertion {rep['insert_errors']} | "
              f"redemarrages {rep['restarts_before']}->{rep['restarts_after']} | actuations {rep['actuations']} | "
              f"retard max d'un tick {rep['max_tick_lag_s']} s")
        print(f"V(10 s)/V* : avant rafale [35,45) {seg(35, 45):.2f} | rafale [60,70) {seg(60, 70):.2f} | "
              f"apres [85,95) {seg(85, 95):.2f}   (cible 1.00)")
        print(f"J : {rec['J'][t >= 20].min() * 1000:.0f} a {rec['J'][t >= 20].max() * 1000:.0f} ms "
              f"(attendu ~196 ms en base, ~43 ms en rafale)")
        print(f"fichier : {path}", flush=True)
        time.sleep(cooldown)


if __name__ == "__main__":
    main()
