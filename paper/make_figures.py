"""Figures of the manuscript, generated from the raw run files (no hand-typed data).
    python paper/make_figures.py --raw data/raw [more dirs] --step2 step2_summary.json --out paper/figures
"""
import argparse, glob, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpcrpo.config import Common
from mpcrpo.metrics import run_metrics, window_v

plt.rcParams.update({"font.size": 8, "axes.grid": True, "grid.alpha": 0.3, "figure.dpi": 150})
CTL = [("PI_tuned", "PI (tuned)", "tab:red"), ("PI_FF", "PI + feedforward", "tab:orange"),
       ("FF_obs", "FF + observer", "tab:green"), ("MPC_persist", "MPC (persistence)", "tab:blue")]


SHORT = {"PI_tuned": "PI", "PI_FF": "PI-FF", "FF_obs": "FF-obs", "MPC_persist": "MPC"}


def SHORT_LABELS(names):
    return [SHORT[c[0]] for c in names]


def load_burst(dirs, stall_s=5.0):
    runs = {}
    for d in dirs:
        for f in sorted(glob.glob(os.path.join(d, "*burst*.json"))):
            if ".INVALID_" in f:
                continue
            j = json.load(open(f))
            if not (j.get("complete") and j.get("valid", True)):
                continue
            p = j["run_uid"].split("_")
            name = "_".join(p[2:-1])
            if name not in [c[0] for c in CTL] or int(p[-1][3:]) > 20:
                continue
            rec = {k: np.array(j[k], float) for k in ("t", "flush", "sync", "bytes", "J", "tps")}
            sync_gap = 0.0
            cur = 0.0
            for i in range(1, len(rec["t"])):
                st = rec["sync"][i] == rec["sync"][i - 1] and rec["bytes"][i] > rec["bytes"][i - 1] and rec["J"][i - 1] <= 0.25 and rec["t"][i] >= 20
                cur = cur + 0.5 if st else 0.0
                sync_gap = max(sync_gap, cur)
            if sync_gap >= stall_s:
                continue
            cm = Common(**j["config"]["Common"])
            m = run_metrics(rec, cm, j["config"]["scenario"])
            runs.setdefault(name, []).append((rec, m))
    return runs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", nargs="+", required=True); ap.add_argument("--step2", required=True)
    ap.add_argument("--out", default="paper/figures")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    # Fig 1: static plant (step 2) -----------------------------------------------------------------------
    S = json.load(open(a.step2))
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    marks = {100: "o", 400: "s", 1600: "^"}
    for tps in (100, 400, 1600):
        pts = [s for s in S if s["tps_nominal"] == tps]
        ax.plot([p["J_ms"] for p in pts], [p["V_per_sync_B"] / 1024 for p in pts], marks[tps], label=f"{tps} docs/s (measured)")
        J = np.logspace(np.log10(15), np.log10(550), 100) / 1000
        R = np.mean([p["bytes_per_s"] for p in pts]); b0, L0 = 513.0, 0.007
        p_ = np.minimum(1, R * J / b0)
        ax.plot(J * 1000, R * (J + p_ * L0) / p_ / 1024, "-", color="gray", lw=0.8)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("journalCommitInterval J (ms)"); ax.set_ylabel("exposed volume V (kB)")
    ax.legend(fontsize=6); fig.tight_layout(); fig.savefig(os.path.join(a.out, "fig_plant.pdf")); plt.close(fig)
    # Fig 2: burst trajectories (median over runs) ----------------------------------------------------------
    runs = load_burst(a.raw)
    fig, axs = plt.subplots(2, 1, figsize=(3.4, 4.0), sharex=True)
    vs = 4096.0
    for name, label, col in CTL:
        if name not in runs:
            continue
        V = np.array([window_v(r, 20) / vs for r, _ in runs[name]]); J = np.array([r["J"] * 1000 for r, _ in runs[name]])
        t = runs[name][0][0]["t"]
        axs[0].plot(t, np.nanmedian(V, 0), color=col, lw=0.9, label=f"{label} (n={len(V)})")
        axs[1].plot(t, np.median(J, 0), color=col, lw=0.9)
    for ax in axs:
        ax.axvspan(100, 160, color="gray", alpha=0.12)
    axs[0].axhline(1.0, color="k", lw=0.6, ls="--"); axs[0].set_ylabel("V (10 s window) / V*"); axs[0].set_ylim(0.4, 2.3)
    axs[0].legend(fontsize=6, loc="upper left"); axs[1].set_ylabel("J (ms), median"); axs[1].set_yscale("log"); axs[1].set_xlabel("time (s)")
    fig.tight_layout(); fig.savefig(os.path.join(a.out, "fig_burst.pdf")); plt.close(fig)
    # Fig 3: boxplots of the two primary criteria ------------------------------------------------------------
    fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.5))
    names = [c for c in CTL if c[0] in runs]
    for ax, key, ttl in ((axs[0], "mae_burst_pct", "burst error (%)"), (axs[1], "peak_ratio", "exposure peak (x target)")):
        data = [[m[key] for _, m in runs[c[0]]] for c in names]
        bp = ax.boxplot(data, tick_labels=SHORT_LABELS(names), showfliers=True, widths=0.6)
        for patch, c in zip(bp["boxes"], names):
            patch.set_color(c[2])
        ax.set_ylabel(ttl)
        if key == "mae_burst_pct":
            ax.set_yscale("log")
    fig.tight_layout(); fig.savefig(os.path.join(a.out, "fig_primary.pdf")); plt.close(fig)
    print("figures:", sorted(os.listdir(a.out)), {k: len(v) for k, v in runs.items()})


if __name__ == "__main__":
    main()
