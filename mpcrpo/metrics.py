"""Per-run metrics computed from the stored COUNTERS (works identically for real runs)."""
import numpy as np
from .config import Common


def window_v(rec, w):
    B, S = rec["bytes"], rec["sync"]
    v = np.full(len(B), np.nan)
    for i in range(w, len(B)):
        dS = S[i] - S[i - w]
        if dS > 0:
            v[i] = (B[i] - B[i - w]) / dS
    return v


def run_metrics(rec: dict, common: Common, scn: dict) -> dict:
    t, vs = rec["t"], common.v_star_B
    v10, v4 = window_v(rec, 20), window_v(rec, 8)
    steady = t >= common.warmup_s + 30
    ok = steady & ~np.isnan(v10)
    out = {"mae_pct": float(np.nanmean(np.abs(v10[ok] / vs - 1)) * 100),
           "viol_frac": float(np.nanmean(v4[steady & ~np.isnan(v4)] > 1.25 * vs)),
           "sync_per_s": float((rec["sync"][-1] - rec["sync"][np.argmax(steady)]) / (t[-1] - t[np.argmax(steady)])),
           "chatter": float(np.mean(np.abs(np.diff(np.log(rec["J"][steady]))))),
           "sat_frac": float(np.mean((rec["J"][steady] <= common.j_min * 1.0001) | (rec["J"][steady] >= common.j_max * 0.9999)))}
    if scn.get("burst"):
        b0, b1 = scn["burst_start"], scn["burst_start"] + scn["burst_dur"]
        m = (t >= b0) & (t < b1 + 20) & ~np.isnan(v10)
        out["mae_burst_pct"] = float(np.mean(np.abs(v10[m] / vs - 1)) * 100)
        mm = (t >= b0) & (t < b1 + 20) & ~np.isnan(v4)
        out["peak_ratio"] = float(np.max(v4[mm]) / vs)
        within = np.abs(v10 / vs - 1) < 0.15
        need = 40
        rec_t = np.nan
        for k in range(len(t) - need):
            if t[k] >= b0 + 1 and within[k:k + need].all():
                rec_t = float(t[k] - b0)
                break
        out["recovery_s"] = rec_t
    return out
