"""Execute a schedule. Resume-safe: re-run the same command after any interruption.
Invalid / failed runs (pod restart, acked < 95 %, error) are repeated at the end (2 extra passes).

    python experiments/run_schedule.py --schedule schedule_pilot.csv --out data/raw --adapter sim
    python experiments/run_schedule.py --schedule schedule_pilot.csv --out data/raw --adapter mongo
"""
import argparse, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mpcrpo.config import Common
from mpcrpo.schedule import read_schedule
from mpcrpo.runner import run_one, out_path, is_complete

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--schedule", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--adapter", choices=["sim", "mongo"], default="sim")
    ap.add_argument("--duration", type=float, default=300.0)
    a = ap.parse_args()
    if a.adapter == "mongo" and not (os.environ.get("MONGO_USER") and os.environ.get("MONGO_PASSWORD")):
        sys.exit("MONGO_USER / MONGO_PASSWORD non charges dans CETTE fenetre PowerShell. Lancez d'abord :\n"
                 "  $e = kubectl exec deploy/mongodb -- printenv MONGO_INITDB_ROOT_USERNAME MONGO_INITDB_ROOT_PASSWORD\n"
                 "  $env:MONGO_USER = $e[0]; $env:MONGO_PASSWORD = $e[1]\n"
                 "et verifiez que kubectl port-forward svc/mongodb 27018:27017 tourne dans une autre fenetre.")
    os.makedirs(a.out, exist_ok=True)
    common = Common(duration_s=a.duration)
    if a.adapter == "sim":
        from mpcrpo.adapters.sim_adapter import SimAdapter as A
    else:
        from mpcrpo.adapters.mongo_adapter import MongoAdapter as A
    rows = sorted(read_schedule(a.schedule), key=lambda r: int(r["order"]))
    consecutive_fail = 0
    for pass_no in range(3):
        todo = [r for r in rows if not is_complete(out_path(a.out, r))]
        if not todo:
            break
        print(f"--- passe {pass_no + 1}: {len(todo)} run(s) a faire", flush=True)
        for i, row in enumerate(todo, 1):
            try:
                status = run_one(row, A(), common, a.out)
                consecutive_fail = 0 if status != "invalid" else consecutive_fail
            except Exception as e:  # noqa
                status = f"ERREUR {type(e).__name__}: {str(e)[:100]}"
                consecutive_fail += 1
            print(f"[{i}/{len(todo)}] {row['run_uid']}: {status}", flush=True)
            if consecutive_fail >= 3:
                sys.exit("3 echecs consecutifs : verifier le port-forward, Docker, le pod (kubectl get pods).")
            if a.adapter == "mongo" and status != "skipped":
                time.sleep(int(row["cooldown_s"]))
    left = [r["run_uid"] for r in rows if not is_complete(out_path(a.out, r))]
    print("TERMINE" if not left else f"RESTE {len(left)} run(s) non valides : {left[:5]}")
