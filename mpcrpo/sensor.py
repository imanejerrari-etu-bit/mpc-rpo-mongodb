"""Turns raw counters into what controllers see. Same code for simulation and for the real engine."""
from collections import deque
from .config import Common


class Sensor:
    def __init__(self, c: Common):
        self.c = c
        self.hist = deque(maxlen=c.window_ticks + 1)
        self.prev, self.R_fast, self.V = None, None, None

    def update(self, ctr: dict) -> dict:
        c = self.c
        R_tick = 0.0 if self.prev is None else (ctr["bytes"] - self.prev["bytes"]) / c.dt
        if self.prev is not None:
            self.R_fast = R_tick if self.R_fast is None else c.r_alpha * R_tick + (1 - c.r_alpha) * self.R_fast
        self.prev = ctr
        self.hist.append(ctr)
        if len(self.hist) == self.hist.maxlen:
            dS = self.hist[-1]["sync"] - self.hist[0]["sync"]
            dB = self.hist[-1]["bytes"] - self.hist[0]["bytes"]
            if dS > 0 and dB > 0:
                self.V = dB / dS
        return {"R_tick": R_tick, "R_fast": self.R_fast, "V": self.V}
