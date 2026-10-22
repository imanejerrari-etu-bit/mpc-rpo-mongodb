"""Second-platform replication: checks the criteria R1-R3 declared in docs/AMENDEMENT_3.md and writes the report,
the LaTeX macros and the table of the manuscript.

    python experiments/analyze_replication.py --raw data/raw_ci --env analysis_ci --lab analysis_S --out paper
"""
import argparse, csv, os, sys, glob, json
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from scipy import stats as sps
from analyze_runs import load, welch_tost
from mpcrpo.stats import cliffs_delta, bootstrap_diff_ci, holm

NAMES = {"PI_tuned": "PI (tuned)", "PI_FF": "PI + feedforward", "FF_obs": "FF + observer", "MPC_persist": "MPC, persistence"}
KEY = {"PI_tuned": "PIT", "PI_FF": "PIFF", "FF_obs": "FFO", "MPC_persist": "MPCP"}


def rd(path):
    try:
        return open(path, encoding="utf-8").read().strip()
    except OSError:
        return "n/a"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True); ap.add_argument("--env", required=True)
    ap.add_argument("--lab", required=True, help="analysis dir of the main platform (runs_metrics.csv, stall excluded)")
    ap.add_argument("--out", default="paper")
    a = ap.parse_args()
    runs = [r for r in load([a.raw]) if r["scenario"] == "burst"]
    g = {c: {m: np.array([r[m] for r in runs if r["controller"] == c], float) for m in ("mae_burst_pct", "peak_ratio", "chatter", "sync_per_s", "recovery_s")} for c in NAMES}
    lab = [r for r in csv.DictReader(open(os.path.join(a.lab, "runs_metrics.csv"))) if r["scenario"] == "burst" and int(r["rep"]) <= 20]
    labm = {c: np.array([float(r["mae_burst_pct"]) for r in lab if r["controller"] == c], float) for c in NAMES}
    rep = ["# Replication on a second platform\n"]
    env = {k: rd(os.path.join(a.env, f)) for k, f in (("kernel", "kernel.txt"), ("image", "mongo_image.txt"), ("version", "mongo_version.txt"))}
    cpu = [l.split(":", 1)[1].strip() for l in rd(os.path.join(a.env, "environment.txt")).splitlines() if l.startswith("Model name")]
    mem = [l.split()[1] for l in rd(os.path.join(a.env, "environment.txt")).splitlines() if l.startswith("Mem:")]
    rep.append(f"Kernel {env['kernel']} ; {env['image']} ; {env['version']} ; CPU {cpu[0] if cpu else 'n/a'} ; RAM {mem[0] if mem else 'n/a'} MB\n")
    reports = [json.load(open(f))["adapter_report"] for f in glob.glob(os.path.join(a.raw, "*.json"))]
    rep.append(f"{len(runs)} valid runs ; acknowledged/offered {min(r['acked_over_offered'] for r in reports):.3f}-{max(r['acked_over_offered'] for r in reports):.3f} ; "
               f"insertion errors {sum(r['insert_errors'] for r in reports)} ; max sync gap {max(r['max_sync_gap_s'] for r in runs):.1f} s\n")
    rep.append("| controller | n | burst error % | peak | chatter | syncs/s | lab-platform burst error % |\n|---|---|---|---|---|---|---|")
    mac = [f"\\newcommand{{\\CIKernel}}{{{env['kernel'].replace('_','\\_')}}}", f"\\newcommand{{\\CIImage}}{{{env['image'].replace('image: ','').replace(':','\\string:')}}}",
           f"\\newcommand{{\\CICpu}}{{{(cpu[0] if cpu else 'n/a').replace('_','\\_')}}}", f"\\newcommand{{\\CIRam}}{{{(int(mem[0])/1024 if mem else 0):.0f}}}",
           f"\\newcommand{{\\CIN}}{{{len(runs)}}}"]
    tab = ["\\begin{table}[t]\\centering\\small",
           "\\caption{Replication on a second platform (shared Linux runner, MongoDB in plain Docker), burst scenario, mean (sd) over 6 runs; last column: same controller on the main platform.}\\label{tab:ci}",
           "\\resizebox{\\columnwidth}{!}{\\begin{tabular}{lccccc}\\toprule", "Controller & Error (\\%) & Peak ($\\times V^*$) & $|\\Delta\\ln J|$ & syncs/s & Main platform (\\%)\\\\\\midrule"]
    for c in NAMES:
        e, p, ch, sy = g[c]["mae_burst_pct"], g[c]["peak_ratio"], g[c]["chatter"], g[c]["sync_per_s"]
        rep.append(f"| {c} | {len(e)} | {e.mean():.2f} ({e.std(ddof=1):.2f}) | {p.mean():.2f} ({p.std(ddof=1):.2f}) | {ch.mean():.3f} | {sy.mean():.2f} | {labm[c].mean():.2f} |")
        tab.append(f"{NAMES[c]} & {e.mean():.2f} ({e.std(ddof=1):.2f}) & {p.mean():.2f} ({p.std(ddof=1):.2f}) & {ch.mean():.3f} & {sy.mean():.2f} & {labm[c].mean():.2f}\\\\")
        mac += [f"\\newcommand{{\\CIMae{KEY[c]}}}{{{e.mean():.2f}}}", f"\\newcommand{{\\CIPeak{KEY[c]}}}{{{p.mean():.2f}}}", f"\\newcommand{{\\CIChat{KEY[c]}}}{{{ch.mean():.3f}}}"]
    tab += ["\\bottomrule\\end{tabular}}\\end{table}"]
    open(os.path.join(a.out, "tab_ci.tex"), "w").write("\n".join(tab) + "\n")
    # criteria declared before the data
    others = ["PI_FF", "FF_obs", "MPC_persist"]
    ratios = {c: g["PI_tuned"]["mae_burst_pct"].mean() / g[c]["mae_burst_pct"].mean() for c in others}
    R1 = all(r >= 3 for r in ratios.values())
    d1, lo1, hi1, ok1 = welch_tost(g["FF_obs"]["mae_burst_pct"], g["MPC_persist"]["mae_burst_pct"], 0.7)
    d2, lo2, hi2, ok2 = welch_tost(g["FF_obs"]["peak_ratio"], g["MPC_persist"]["peak_ratio"], 0.10)
    R2 = ok1 and ok2
    R3 = all(g["PI_tuned"]["peak_ratio"].mean() > g[c]["peak_ratio"].mean() for c in others)
    rep.append(f"\n## Criteria declared before the data (docs/AMENDEMENT_3.md)\n- R1 (PI error >= 3x each load-aware controller): ratios " + ", ".join(f"{c} {r:.2f}" for c, r in ratios.items()) + f" -> **{'SATISFIED' if R1 else 'NOT satisfied'}**")
    rep.append(f"- R2 (FF_obs ~ MPC_persist): error diff {d1:+.2f} [{lo1:+.2f}, {hi1:+.2f}] (margin 0.7) ; peak diff {d2:+.2f} [{lo2:+.2f}, {hi2:+.2f}] (margin 0.10) -> **{'SATISFIED' if R2 else 'NOT satisfied'}**")
    rep.append(f"- R3 (PI peak highest): PI {g['PI_tuned']['peak_ratio'].mean():.2f} vs " + ", ".join(f"{c} {g[c]['peak_ratio'].mean():.2f}" for c in others) + f" -> **{'SATISFIED' if R3 else 'NOT satisfied'}**")
    for nm, ok in (("R1", R1), ("R2", R2), ("R3", R3)):
        mac.append(f"\\newcommand{{\\CI{ {'R1': 'Rone', 'R2': 'Rtwo', 'R3': 'Rthree'}[nm] }}}{{{'satisfied' if ok else 'not satisfied'}}}")
    for c in others:
        mac.append(f"\\newcommand{{\\CIRatio{KEY[c]}}}{{{ratios[c]:.1f}}}")
    mac += [f"\\newcommand{{\\CIeqMaeD}}{{{d1:+.2f}}}", f"\\newcommand{{\\CIeqMaeLo}}{{{lo1:+.2f}}}", f"\\newcommand{{\\CIeqMaeHi}}{{{hi1:+.2f}}}",
            f"\\newcommand{{\\CIeqPeakD}}{{{d2:+.2f}}}", f"\\newcommand{{\\CIeqPeakLo}}{{{lo2:+.2f}}}", f"\\newcommand{{\\CIeqPeakHi}}{{{hi2:+.2f}}}"]
    # exploratory: does the lab-platform advantage of PI-FF over MPC replicate?
    x, y = g["PI_FF"]["mae_burst_pct"], g["MPC_persist"]["mae_burst_pct"]
    d, lo, hi = bootstrap_diff_ci(x, y)
    p_raw = sps.mannwhitneyu(x, y, alternative="two-sided").pvalue
    labx, laby = labm["PI_FF"], labm["MPC_persist"]
    dl, lol, hil = bootstrap_diff_ci(labx, laby)
    rep.append(f"\n## Exploratory (not a criterion): PI-FF minus MPC on the burst error\n- second platform: {d:+.2f} [{lo:+.2f}, {hi:+.2f}] pp (raw p {p_raw:.3g})\n- main platform: {dl:+.2f} [{lol:+.2f}, {hil:+.2f}] pp -> the sign **{'is the same' if np.sign(d)==np.sign(dl) else 'differs'}**")
    mac += [f"\\newcommand{{\\CIPIFFvsMPCD}}{{{d:+.2f}}}", f"\\newcommand{{\\CIPIFFvsMPCLo}}{{{lo:+.2f}}}", f"\\newcommand{{\\CIPIFFvsMPCHi}}{{{hi:+.2f}}}",
            f"\\newcommand{{\\CIPIFFvsMPCSame}}{{{'is the same' if np.sign(d)==np.sign(dl) else 'differs'}}}"]
    open(os.path.join(a.out, "numbers_ci.tex"), "w").write("\n".join(mac) + "\n")
    open(os.path.join(a.env, "replication_report.md"), "w").write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
