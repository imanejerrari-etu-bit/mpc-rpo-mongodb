"""Single source of truth for every parameter. Each run JSON stores these + a hash.

Controlled variable: V = journal bytes per sync cycle (bytes), measured from engine counters over a
10 s window:  V = d(log bytes written) / d(log sync operations).
Actuator: J = journalCommitInterval (seconds).  Disturbance: write byte-rate R.
Identified static plant (see step 2):  V ~ R*(J + p*L)/p ,  p = min(1, R*J/b0).
"""
from dataclasses import dataclass, asdict
import hashlib, json


@dataclass
class Common:
    v_star_B: float = 4096.0     # target exposed volume (bytes)
    dt: float = 0.5              # control period (s)
    duration_s: float = 300.0
    warmup_s: float = 20.0       # sensor window fill + settling; controller starts after this
    j_min: float = 0.02          # actuator bounds (s)
    j_max: float = 0.5
    j_init: float = 0.1          # MongoDB default journalCommitInterval
    window_ticks: int = 20       # sensor window (10 s)
    r_alpha: float = 0.5         # EWMA of the per-tick byte rate (fast load estimate)
    b0_B: float = 513.0          # bytes of one write batch (static-model floor)
    L0_s: float = 0.007          # mean sync latency (static model)


@dataclass
class PIConfig:
    kp: float = 0.3
    ki: float = 0.05
    i_max: float = 5.0           # integrator clamp (log units * s)
    antiwindup: str = "clamp"    # none | clamp | backcalc
    kt: float = 1.0
    filter_alpha: float = 1.0    # filter on ln V (1.0 = none)
    ff: bool = False             # feedforward from the fast load estimate R
    bias_alpha: float = 0.0      # >0: model-bias observer (EWMA) used inside the feedforward
    ff_alpha: float = 0.5        # EWMA smoothing of the per-tick byte rate used by the feedforward (1.0 = raw)


@dataclass
class MPCConfig:
    horizon: int = 6
    gamma: float = 0.85          # w_i = gamma**(i-1)
    lam: float = 0.05            # move penalty on (ln J - ln J_prev)^2
    under_weight: float = 1.0    # weight when V is BELOW the target (safe side); 1.0 = symmetric
    predictor: str = "persistence"   # persistence | ma | arima   (forecast of ln R)
    window: int = 20
    ewma_alpha: float = 0.3
    bias_alpha: float = 0.1      # model-bias observer (EWMA)


def to_dict(*objs):
    return {type(o).__name__: asdict(o) for o in objs}


def config_hash(d: dict) -> str:
    return hashlib.sha1(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()[:12]
