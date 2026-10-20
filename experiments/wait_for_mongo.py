"""Wait until MongoDB accepts an AUTHENTICATED connection from this machine (not just a ping inside the container).
The official image first starts a temporary server to create the root user, then restarts it: a ping made too early
succeeds against the temporary server. Exit code 0 when ready, 1 on timeout.

    MONGO_URI=mongodb://localhost:27017 MONGO_USER=bench MONGO_PASSWORD=... python experiments/wait_for_mongo.py --timeout 180
"""
import argparse, os, sys, time
from pymongo import MongoClient

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=float, default=180.0)
    a = ap.parse_args()
    uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    kw = dict(serverSelectionTimeoutMS=2000, directConnection=True)
    if os.environ.get("MONGO_USER"):
        kw.update(username=os.environ["MONGO_USER"], password=os.environ.get("MONGO_PASSWORD"), authSource="admin")
    t0, last = time.time(), ""
    while time.time() - t0 < a.timeout:
        try:
            c = MongoClient(uri, **kw)
            c.admin.command("serverStatus")
            print(f"MongoDB ready after {time.time() - t0:.0f} s, version {c.server_info()['version']}")
            sys.exit(0)
        except SystemExit:
            raise
        except Exception as e:  # noqa
            last = f"{type(e).__name__}: {str(e)[:120]}"
            time.sleep(2)
    print(f"TIMEOUT after {a.timeout:.0f} s; last error: {last}")
    sys.exit(1)
