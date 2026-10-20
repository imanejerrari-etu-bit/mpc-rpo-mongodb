"""Event-level simulator of the MongoDB journal counters, calibrated on the identified plant.
Regular write batches arrive at rate lam = tps/batch_docs.  The journal flushes every J seconds;
a flush syncs only if a batch arrived since the last sync, and a sync adds a latency L to the cycle.
Counters returned per tick: flush, sync, bytes.  This reproduces the measured floor (V -> one batch),
p = fraction of flushes that sync, and the count quantisation noise -- it is NOT evidence for the paper."""
from dataclasses import dataclass
import numpy as np


@dataclass
class PlantParams:
    batch_docs: int = 10
    batch_bytes: float = 513.0
    L_lo_s: float = 0.0025     # mean sync latency at J <= 20 ms (measured ~2.1-2.7 ms)
    L_hi_s: float = 0.008      # mean sync latency at J >= 100 ms (measured ~7-9 ms)
    L_cv: float = 0.25
    timing_jitter_s: float = 0.007   # counter-read / thread timing jitter on the bytes counter (measured R cv)


class VolumePlant:
    def __init__(self, p: PlantParams, seed: int, j0: float):
        self.p, self.rng = p, np.random.default_rng(seed)
        self.t, self.Lam = 0.0, 0.0
        self.phase = float(self.rng.random())
        self.arr_synced, self.flush, self.sync = 0, 0, 0
        self.bytes_rep = 0.0
        self.next_flush = float(self.rng.random()) * j0

    def _A(self, lam_cum):
        return int(np.floor(lam_cum + self.phase))

    def advance(self, J: float, tps: float, dt: float) -> dict:
        lam = tps / self.p.batch_docs
        t0, t1, L0 = self.t, self.t + dt, self.Lam
        while self.next_flush < t1:
            tf = self.next_flush
            A = self._A(L0 + lam * (tf - t0))
            self.flush += 1
            if A > self.arr_synced:
                self.sync += 1
                self.arr_synced = A
                w = min(1.0, max(0.0, (J - 0.02) / 0.08))
                Lm = self.p.L_lo_s + (self.p.L_hi_s - self.p.L_lo_s) * w
                L = Lm * np.exp(self.p.L_cv * self.rng.standard_normal() - 0.5 * self.p.L_cv ** 2)
                self.next_flush = tf + J + L
            else:
                self.next_flush = tf + J
        self.Lam, self.t = L0 + lam * dt, t1
        jit = lam * self.p.timing_jitter_s * float(self.rng.standard_normal())
        rep = max(self.bytes_rep, self._A(self.Lam + jit) * self.p.batch_bytes)   # counter stays monotone
        self.bytes_rep = rep
        return {"flush": self.flush, "sync": self.sync, "bytes": rep}
