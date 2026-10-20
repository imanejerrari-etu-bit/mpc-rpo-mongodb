"""Test of the REAL adapter code path against a fake MongoDB (~40 s, real time).
    python tests/test_mongo_adapter_fake.py
"""
import os, sys, json, glob, tempfile, threading, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from mpcrpo.config import Common
from mpcrpo.runner import run_one
from mpcrpo.adapters.mongo_adapter import MongoAdapter

state = {"docs": 0, "lock": threading.Lock()}


class Admin:
    def __init__(self): self.J, self.last, self.f, self.s, self.sets = 100, time.time(), 0.0, 0.0, []
    def command(self, cmd, *a, **k):
        if cmd == "ping": return {"ok": 1}
        if "getParameter" in cmd: return {"journalCommitInterval": self.J, "ok": 1}
        if "setParameter" in cmd: self.J = cmd["journalCommitInterval"]; self.sets.append(self.J); return {"ok": 1}
        if "serverStatus" in cmd:
            now = time.time(); dt = now - self.last; self.last = now
            self.f += dt * 1000 / self.J; self.s += dt / (self.J / 1000 + 0.008)
            with state["lock"]: B = state["docs"] * 50.4
            return {"wiredTiger": {"log": {"log flush operations": int(self.f), "log sync operations": int(self.s),
                                           "log bytes written": int(B)}}}
        raise ValueError(cmd)


class Coll:
    def insert_many(self, docs, ordered=False):
        time.sleep(0.002)
        with state["lock"]: state["docs"] += len(docs)


class DB:
    def get_collection(self, n, write_concern=None): return Coll()


class Client:
    admin_obj = None
    def __init__(self, *a, **k): Client.admin_obj = self.admin = Admin()
    def __getitem__(self, n): return DB()
    def drop_database(self, n): pass
    def close(self): pass


scn = {"name": "smoke", "tps0": 200.0, "burst": True, "burst_start": 8.0, "burst_dur": 6.0, "tps1": 800.0}
C = Common(duration_s=16.0, warmup_s=4.0)
spec = json.dumps({"type": "pi", "ff": True, "bias_alpha": 0.1})
row = {"run_uid": "fake_ok", "seed": "1", "spec": spec, "scn": json.dumps(scn)}

with tempfile.TemporaryDirectory() as d:
    # 1. valid run
    t0 = time.time()
    ad = MongoAdapter(client_factory=Client, restart_probe=lambda: 14)
    st = run_one(row, ad, C, d)
    rep = ad.report()
    assert st == "done" and rep["valid"], rep
    doc = json.load(open(os.path.join(d, "fake_ok.json")))
    assert doc["valid"] and len(doc["bytes"]) == 32 and doc["adapter_report"]["acked_over_offered"] > 0.95, doc["adapter_report"]
    assert Client.admin_obj.J == 100, "J not restored"
    assert max(doc["tps"]) == 800.0 and doc["bytes"][-1] > doc["bytes"][0]
    print(f"  OK   valid run: acked/offered {rep['acked_over_offered']}, actuations {rep['actuations']}, "
          f"max tick lag {rep['max_tick_lag_s']} s, J restored to {Client.admin_obj.J} ms ({time.time() - t0:.0f} s)")
    # 2. restart during the run -> INVALID file, main file absent (run will be repeated)
    cnt = {"n": 0}
    def probe():
        cnt["n"] += 1
        return 14 if cnt["n"] == 1 else 15
    ad2 = MongoAdapter(client_factory=Client, restart_probe=probe)
    st2 = run_one(dict(row, run_uid="fake_restart"), ad2, C, d)
    assert st2 == "invalid" and not os.path.exists(os.path.join(d, "fake_restart.json"))
    assert glob.glob(os.path.join(d, "fake_restart.INVALID_*.json"))
    print("  OK   pod restart -> run stored as INVALID, will be repeated")
    # 3. failure during the run still restores J and stops the load
    class Bad(Client):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            orig = self.admin.command
            n = {"i": 0}
            def cmd(c, *a, **k):
                if isinstance(c, dict) and "serverStatus" in c:
                    n["i"] += 1
                    if n["i"] > 6: raise RuntimeError("connection lost")
                return orig(c, *a, **k)
            self.admin.command = cmd
    try:
        run_one(dict(row, run_uid="fake_fail"), MongoAdapter(client_factory=Bad, restart_probe=lambda: 14), C, d)
        raise SystemExit("should have raised")
    except RuntimeError:
        pass
    assert not os.path.exists(os.path.join(d, "fake_fail.json"))
    print("  OK   connection loss -> exception, no result file, adapter cleaned up")
    # 4. missing credentials -> clear message, nothing touched
    class NoAuth(Client):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            orig = self.admin.command
            def cmd(c, *a, **k):
                if isinstance(c, dict) and "serverStatus" in c:
                    raise RuntimeError("Command serverStatus requires authentication")
                return orig(c, *a, **k)
            self.admin.command = cmd
    try:
        run_one(dict(row, run_uid="fake_noauth"), MongoAdapter(client_factory=NoAuth, restart_probe=lambda: 14), C, d)
        raise SystemExit("should have raised")
    except RuntimeError as e:
        assert "MONGO_USER" in str(e)
    print("  OK   missing credentials -> clear message")
print("\nADAPTER TEST PASSED")
