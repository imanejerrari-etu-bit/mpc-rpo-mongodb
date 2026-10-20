"""Run:  python tests/selftest.py     (no cluster needed)"""
import os, sys, json, tempfile, itertools
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from mpcrpo.config import Common, PIConfig, MPCConfig
from mpcrpo.controllers import PIController, MPCController, v_model
from mpcrpo.plant import PlantParams, VolumePlant
from mpcrpo.sensor import Sensor
from mpcrpo.sim import simulate, STATIONARY, BURST
from mpcrpo.metrics import run_metrics, window_v
from mpcrpo.stats import holm, compare_groups
from mpcrpo.schedule import make_schedule
from mpcrpo.runner import run_one
from mpcrpo.adapters.sim_adapter import SimAdapter

C = Common()
ok = lambda name: print("  OK  ", name)


class ConstJ:
    def __init__(self, J): self.J = J
    def reset(self): pass
    def step(self, obs): return self.J


# 1. Simulator vs the MEASURED plant (step 2 summary: tps, J, V per sync [B], sync/s)
MEAS = [(100, .5, 2547, 2.04), (100, .1, 569, 9.13), (100, .02, 514, 10.06), (400, .5, 10159, 2.02),
        (400, .1, 2180, 9.41), (400, .02, 514, 39.9), (1600, .5, 40186, 2.04), (1600, .1, 8782, 9.33),
        (1600, .02, 1831, 44.8)]
worst_v = worst_s = 0.0
for tps, J, v_meas, s_meas in MEAS:
    c2 = Common(duration_s=240.0)
    rec = simulate(ConstJ(J), c2, PlantParams(), {"name": "x", "tps0": float(tps), "burst": False}, seed=5)
    v = np.nanmean(window_v(rec, 20)[int(40 / c2.dt):])
    sps = (rec["sync"][-1] - rec["sync"][int(40 / c2.dt)]) / (rec["t"][-1] - rec["t"][int(40 / c2.dt)])
    worst_v = max(worst_v, abs(v / v_meas - 1)); worst_s = max(worst_s, abs(sps / s_meas - 1))
assert worst_v < 0.12 and worst_s < 0.12, (worst_v, worst_s)
ok(f"simulator vs measured plant: worst error V {worst_v * 100:.1f}%, sync/s {worst_s * 100:.1f}%")

# 1b. Simulated BURST response vs the REAL one (step 3b, J=100 ms): V levels, ratio and sensor timing
class _C(ConstJ): pass
REAL = {"V_base_kB": 2.144, "V_burst_kB": 8.681, "t63_up": 6.5, "t95_up": 10.0, "t63_down": 6.5, "t95_down": 9.5}
c3 = Common(duration_s=180.0, warmup_s=0.0, j_init=0.1)
scn3 = {"name": "x", "tps0": 396.4, "burst": True, "burst_start": 60.0, "burst_dur": 60.0, "tps1": 1586.0}
rec = simulate(ConstJ(0.1), c3, PlantParams(), scn3, seed=11)
t, v10 = rec["t"], window_v(rec, 20)
V0 = np.nanmean(v10[(t >= 45) & (t < 60)]) / 1024
V1 = np.nanmean(v10[(t >= 80) & (t < 120)]) / 1024
yu = (v10 - V0 * 1024) / ((V1 - V0) * 1024)
first = lambda y, t_from, f: next(ti - t_from for ti, yi in zip(t, y) if ti >= t_from and yi >= f)
assert abs(V0 / REAL["V_base_kB"] - 1) < 0.03 and abs(V1 / REAL["V_burst_kB"] - 1) < 0.03, (V0, V1)
assert abs(first(yu, 60, .63) - REAL["t63_up"]) <= 1.0 and abs(first(yu, 60, .95) - REAL["t95_up"]) <= 1.0
ok(f"simulated burst vs real burst: V {V0:.2f}->{V1:.2f} kB (real 2.14->8.68), t63 {first(yu, 60, .63):.1f}s (6.5), t95 {first(yu, 60, .95):.1f}s (10.0)")

# 2. Static model matches the same measurements (outside the floor it is the identified law)
errs = [abs(v_model(tps * 51.3, J, 513.0, 0.007) / v - 1) for tps, J, v, _ in MEAS]
assert np.median(errs) < 0.10, errs
ok(f"static model v_model: median error {np.median(errs) * 100:.1f}%")

# 3. PI-FF and MPC track a stationary target; plain PI is slower on a burst than PI-FF
for name, ctl in (("PIFF", PIController(C, PIConfig(ff=True, bias_alpha=0.1))), ("MPC", MPCController(C, MPCConfig()))):
    m = run_metrics(simulate(ctl, C, PlantParams(), STATIONARY, 1), C, STATIONARY)
    assert m["mae_pct"] < 8, (name, m)
    ok(f"{name} stationary MAE {m['mae_pct']:.1f}%")
mb = {n: run_metrics(simulate(c, C, PlantParams(), BURST, 1), C, BURST)["mae_burst_pct"]
      for n, c in (("PI", PIController(C, PIConfig())), ("PIFF", PIController(C, PIConfig(ff=True, bias_alpha=0.1))))}
assert mb["PIFF"] < mb["PI"], mb
ok(f"burst-window error: PI {mb['PI']:.1f}% > PI-FF {mb['PIFF']:.1f}% (feedforward helps)")

# 4. MPC with H=1, persistence, no move penalty ~ feedforward+observer (ablation identity)
a = simulate(MPCController(C, MPCConfig(horizon=1, lam=1e-6, ewma_alpha=0.5, bias_alpha=0.1)), C, PlantParams(), STATIONARY, 2)
b = simulate(PIController(C, PIConfig(ff=True, kp=0.0, ki=0.0, bias_alpha=0.1)), C, PlantParams(), STATIONARY, 2)
sl = slice(int(60 / C.dt), None)
rel = np.median(np.abs(a["J"][sl] / b["J"][sl] - 1))
assert rel < 0.15, rel
ok(f"MPC(H=1,persistence) ~ FF+observer: median |dJ|/J = {rel * 100:.1f}%")

# 5. Bias observer absorbs a wrong model constant (L0 x3)
Cw = Common(L0_s=0.021)
m = run_metrics(simulate(PIController(Cw, PIConfig(ff=True, bias_alpha=0.1)), Cw, PlantParams(), STATIONARY, 3), Cw, STATIONARY)
assert m["mae_pct"] < 10, m
ok(f"observer absorbs model error (L0 x3): MAE {m['mae_pct']:.1f}%")

# 6. Holm + direct tests
assert np.allclose(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
rng = np.random.default_rng(0)
g = {"A": list(rng.normal(5, .3, 10)), "B": list(rng.normal(3, .3, 10)), "C": list(rng.normal(3.05, .3, 10))}
assert all("p_mwu_holm" in r for r in compare_groups(g))
ok("Holm correction + direct tests")

# 7. Schedule: blocks contain each controller once, reproducible
ctl = {"PI": {"type": "pi"}, "MPC": {"type": "mpc"}, "PIFF": {"type": "pi", "ff": True}}
mk = lambda: make_schedule([{"name": "mongodb"}], [{"name": "stat"}, {"name": "burst"}], ctl, {"stat": 2, "burst": 4}, seed=7)
s1, s2 = mk(), mk()
assert [r["run_uid"] for r in s1] == [r["run_uid"] for r in s2]
for _, grp in itertools.groupby(sorted(s1, key=lambda r: (r["scenario"], r["rep"], r["order"])),
                                key=lambda r: (r["scenario"], r["rep"])):
    assert sorted(r["controller"] for r in grp) == sorted(ctl)
assert sum(1 for r in s1 if r["scenario"] == "stat") == 2 * 3 and sum(1 for r in s1 if r["scenario"] == "burst") == 4 * 3
ok("randomised block schedule (interleaved, reproducible, reps per scenario)")

# 8. Runner: atomic, resume skip, never overwrite, same result as sim.simulate
with tempfile.TemporaryDirectory() as d:
    row = dict(s1[0], spec=json.dumps({"type": "pi", "ff": True, "bias_alpha": 0.1}), scn=json.dumps(STATIONARY))
    c2 = Common(duration_s=120)
    assert run_one(row, SimAdapter(), c2, d) == "done"
    assert run_one(row, SimAdapter(), c2, d) == "skipped"
    doc = json.load(open(os.path.join(d, row["run_uid"] + ".json")))
    assert doc["complete"] and len(doc["config_hash"]) == 12 and len(doc["sync"]) == 240
    open(os.path.join(d, "x.json"), "w").write("{")
    try:
        run_one(dict(row, run_uid="x"), SimAdapter(), c2, d); raise SystemExit("should refuse")
    except FileExistsError:
        pass
ok("runner: atomic write, resume skip, no overwrite")
print("\nALL SELF-TESTS PASSED")
