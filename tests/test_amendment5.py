"""Run:  python tests/test_amendment5.py   (no cluster needed): ramp / periodic profiles and the actuation delay of the runner."""
import os, sys, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import mpcrpo.runner as runner
from mpcrpo.config import Common
from mpcrpo.sim import tps_at, RAMP, PERIODIC

ok = lambda name: print("  OK  ", name)

# 1. profiles
assert tps_at(RAMP, 99.9) == 400 and tps_at(RAMP, 100) == 400 and abs(tps_at(RAMP, 130) - 1000) < 1e-9
assert abs(tps_at(RAMP, 159.5) - 1590) < 1e-9 and tps_at(RAMP, 220) == 400
assert tps_at(PERIODIC, 100) == 400 and abs(tps_at(PERIODIC, 120) - 1600) < 1e-9 and abs(tps_at(PERIODIC, 140) - 400) < 1e-9
assert tps_at(PERIODIC, 220) == 400
ok("ramp (triangular, 400->1600->400 over 120 s) and periodic (raised cosine, 40 s) profiles")


# 2. actuation delay: the command computed at tick k is applied delay ticks later, initial value j_init in the meantime
class Seq:
    def __init__(self): self.k = 0
    def reset(self): self.k = 0
    def step(self, obs):
        self.k += 1
        return 0.01 * self.k


class Stub:
    def __init__(self): self.act = []
    def start(self, row, scn, common): pass
    def measure(self, t): return {"flush": 0, "sync": 0, "bytes": 0}, 400.0
    def actuate(self, J): self.act.append(round(J, 4))
    def wait_next_tick(self, t, dt): pass
    def stop(self): pass
    def report(self): return {"valid": True}


runner.build_controller = lambda common, spec: Seq()
C = Common(duration_s=30.0)
res = {}
for d in (0.0, 1.0):
    st = Stub()
    with tempfile.TemporaryDirectory() as tmp:
        row = {"run_uid": f"x_{int(d)}", "spec": "{}", "scn": json.dumps({"name": "t", "tps0": 400.0, "act_delay_s": d}), "seed": "1"}
        assert runner.run_one(row, st, C, tmp) == "done"
        doc = json.load(open(os.path.join(tmp, row["run_uid"] + ".json")))
    res[d] = (st.act, doc["J"])
a0, a1 = res[0.0][0], res[1.0][0]
assert a0 == [round(0.01 * (k + 1), 4) for k in range(len(a0))]
assert a1[:2] == [round(C.j_init, 4)] * 2 and a1[2:] == a0[:-2], (a1[:5], a0[:5])
ok("actuation delay of 1 s = 2 ticks: applied J(k) = commanded J(k-2), j_init before; no delay unchanged")
print("\nAMENDMENT 5 TESTS PASSED")
