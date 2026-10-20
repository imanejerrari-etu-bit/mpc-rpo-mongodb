"""Runs ONE scheduled run, stores counters per tick, writes the JSON atomically (tmp + rename).
Never overwrites an existing result; stores config, hash, schedule row and seed. Resume-safe."""
import json, os, time, platform
from .config import Common, to_dict, config_hash
from .controllers import build_controller
from .sensor import Sensor


def out_path(out_dir, row):
    return os.path.join(out_dir, row["run_uid"] + ".json")


def is_complete(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("complete") is True
    except Exception:
        return False


def run_one(row, adapter, common: Common, out_dir):
    path = out_path(out_dir, row)
    if os.path.exists(path):
        if is_complete(path):
            return "skipped"
        raise FileExistsError(f"{path} exists but is incomplete: move it away manually, never overwrite")
    spec, scn = json.loads(row["spec"]), json.loads(row["scn"])
    over = json.loads(row.get("common") or "{}")
    if over:                                        # per-run override (sensitivity analysis); stored in the JSON config
        from dataclasses import replace
        common = replace(common, **over)
    ctl, sensor = build_controller(common, spec), Sensor(common)
    ctl.reset()
    cfg = {"Common": to_dict(common)["Common"], "controller_spec": spec, "scenario": scn}
    n = int(common.duration_s / common.dt)
    adapter.start(row, scn, common)
    rec = {k: [] for k in ("t", "flush", "sync", "bytes", "J", "tps")}
    J = common.j_init
    t0 = time.time()
    try:
        for k in range(n):
            tk = k * common.dt
            ctr, tps = adapter.measure(tk)
            obs = sensor.update(ctr)
            for key, val in (("t", tk), ("flush", ctr["flush"]), ("sync", ctr["sync"]), ("bytes", ctr["bytes"]),
                             ("J", J), ("tps", tps)):
                rec[key].append(val)
            for key, val in ctr.items():                 # optional diagnostics (x_*), stored as-is
                if key.startswith("x_"):
                    rec.setdefault(key, []).append(val)
            if tk >= common.warmup_s:
                J = ctl.step(obs)
                adapter.actuate(J)
            adapter.wait_next_tick(tk, common.dt)
    finally:
        adapter.stop()          # always: stop load, restore J, check restarts
    report = adapter.report() if hasattr(adapter, "report") else {"valid": True}
    valid = bool(report.get("valid", True))
    doc = {"run_uid": row["run_uid"], "schedule_row": row, "config": cfg, "config_hash": config_hash(cfg),
           "seed": int(row["seed"]), "host": platform.node(), "python": platform.python_version(),
           "started_unix": t0, "wall_s": time.time() - t0, "n_ticks": n, "complete": True,
           "valid": valid, "adapter_report": report, **rec}
    if not valid:                                   # keep it for transparency, but the run must be repeated
        path = path[:-5] + f".INVALID_{int(time.time())}.json"
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f)
    os.replace(tmp, path)
    return "done" if valid else "invalid"
