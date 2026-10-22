"""Block diagram of the control structure (matplotlib: deterministic size, no TikZ dependency).
    python paper/make_scheme.py --out paper/figures"""
import argparse, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

def box(ax, x, y, w, h, text, fs=6.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.02", fc="white", ec="black", lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)

def arrow(ax, p, q, lw=0.8, ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=7, lw=lw, ls=ls, color="black", shrinkA=0, shrinkB=0))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="paper/figures"); a = ap.parse_args()
    fig, ax = plt.subplots(figsize=(3.4, 2.3)); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    box(ax, 0.02, 0.60, 0.43, 0.24, "MongoDB journal\nV ~ R (J + pL) / p")
    box(ax, 0.57, 0.60, 0.41, 0.24, "counters -> 10 s window\ngives V-hat and R-hat", fs=6.0)
    box(ax, 0.02, 0.04, 0.96, 0.32, "bias observer b  ->  feedforward\nJ_ff = V* exp(-b) / R-hat - L0\n+ PI correction   or   MPC (forecast of ln R)", fs=6.3)
    ax.text(0.235, 0.95, "load R", ha="center", va="center", fontsize=6.5)
    arrow(ax, (0.235, 0.92), (0.235, 0.84)); arrow(ax, (0.45, 0.72), (0.57, 0.72))
    arrow(ax, (0.775, 0.60), (0.775, 0.36)); ax.text(0.80, 0.48, "V-hat, R-hat", fontsize=6, va="center")
    ax.plot([0.02, 0.0, 0.0], [0.21, 0.21, 0.72], color="black", lw=0.8); arrow(ax, (0.0, 0.72), (0.02, 0.72))
    ax.text(0.03, 0.47, "J", fontsize=6.5, va="center")
    os.makedirs(a.out, exist_ok=True); fig.savefig(os.path.join(a.out, "fig_scheme.pdf"), bbox_inches="tight"); print("ok")
