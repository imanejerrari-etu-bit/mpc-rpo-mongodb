"""Closed-loop simulation. Same tick loop as the real runner (sensor -> controller -> actuator)."""
import numpy as np
from .config import Common
from .plant import PlantParams, VolumePlant
from .sensor import Sensor

STATIONARY = {"name": "stationary", "tps0": 400.0, "burst": False}
BURST = {"name": "burst", "tps0": 400.0, "burst": True, "burst_start": 100.0, "burst_dur": 60.0, "tps1": 1600.0}
LOW_LOAD = {"name": "lowload", "tps0": 100.0, "burst": True, "burst_start": 100.0, "burst_dur": 60.0, "tps1": 400.0}


# Extra disturbance profiles (amendment 5). The window [burst_start, burst_start + burst_dur) is where the disturbance acts, so the
# burst-window metrics apply unchanged. "ramp": triangular pulse tps0 -> tps1 -> tps0 (linear up for burst_dur/2, linear down for burst_dur/2).
# "periodic": raised cosine between tps0 and tps1 with period "period_s" inside the window.
RAMP = {"name": "ramp", "tps0": 400.0, "burst": True, "burst_start": 100.0, "burst_dur": 120.0, "tps1": 1600.0, "profile": "ramp"}
PERIODIC = {"name": "periodic", "tps0": 400.0, "burst": True, "burst_start": 100.0, "burst_dur": 120.0, "tps1": 1600.0,
            "profile": "periodic", "period_s": 40.0}


def tps_at(scn, t):
    if scn.get("burst") and scn["burst_start"] <= t < scn["burst_start"] + scn["burst_dur"]:
        prof = scn.get("profile", "step")
        u = (t - scn["burst_start"]) / scn["burst_dur"]
        if prof == "ramp":
            return scn["tps0"] + (scn["tps1"] - scn["tps0"]) * (2 * u if u < 0.5 else 2 * (1 - u))
        if prof == "periodic":
            return scn["tps0"] + (scn["tps1"] - scn["tps0"]) * 0.5 * (1 - np.cos(2 * np.pi * (t - scn["burst_start"]) / scn["period_s"]))
        return scn["tps1"]
    return scn["tps0"]


def simulate(controller, common: Common, pp: PlantParams, scn: dict, seed: int, delay_ticks: int = 0) -> dict:
    controller.reset()
    plant, sensor = VolumePlant(pp, seed, common.j_init), Sensor(common)
    n = int(common.duration_s / common.dt)
    t = np.arange(n) * common.dt
    out = {k: np.zeros(n) for k in ("flush", "sync", "bytes", "J", "tps")}
    J = common.j_init
    pending = [common.j_init] * delay_ticks      # actuator delay (stress tests only; real delay ~5 ms)
    for k in range(n):
        tps = tps_at(scn, t[k])                       # offered load now (logged)
        J_eff = pending.pop(0) if delay_ticks else J
        ctr = plant.advance(J_eff, tps_at(scn, t[k] - common.dt), common.dt)   # counters cover [t_k - dt, t_k)
        obs = sensor.update(ctr)
        out["flush"][k], out["sync"][k], out["bytes"][k], out["J"][k], out["tps"][k] = \
            ctr["flush"], ctr["sync"], ctr["bytes"], J, tps
        if delay_ticks:
            pending.append(J)
        if t[k] >= common.warmup_s:
            J = controller.step(obs)
    out["t"] = t
    return out
