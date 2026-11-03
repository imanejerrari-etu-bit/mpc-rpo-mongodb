"""Analysis of amendment 5 (ramp / periodic / periodic with 1 s actuation delay; PI, FF+obs, MPC persistence, MPC ARIMA).
Only the runs of schedule_scenarios.csv; no pooling with other campaigns. Declared contrasts per cell: FF_obs vs MPC_persist, FF_obs vs MPC_arima,
MPC_persist vs MPC_arima (Holm over 3 contrasts x 2 criteria x 3 cells = 18 tests); PI_tuned vs FF_obs as a reminder; TOST for FF_obs vs MPC_persist.

    python experiments\\analyze_scenarios.py --raw data\\raw --schedule schedule_scenarios.csv --out analysis_scenarios
"""
import argparse, csv, os, sys, collections
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from scipy import stats as sps
from mpcrpo.stats import holm, cliffs_delta, bootstrap_diff_ci, perm_test
from analyze_runs import load, welch_tost

CRIT = [("mae_burst_pct", 0.7), ("peak_ratio", 0.10)]
DECL = [("FF_obs", "MPC_persist"), ("FF_obs", "MPC_arima"), ("MPC_persist", "MPC_arima")]
REMIND = ("PI_tuned", "FF_obs")
CELLS = ["ramp", "periodic", "periodicd1"]
LAB = {"ramp": "rampe", "periodic": "periodique", "periodicd1": "periodique + retard 1 s"}
CTL = ["PI_tuned", "FF_obs", "MPC_persist", "MPC_arima"]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", nargs="+", required=True); ap.add_argument("--schedule", required=True)
    ap.add_argument("--out", default="analysis_scenarios"); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    uids = {r["run_uid"] for r in csv.DictReader(open(a.schedule, newline="", encoding="utf-8"))}
    runs = [r for r in load(a.raw) if r["run_uid"] in uids]
    g = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in runs:
        for k, v in r.items():
            if isinstance(v, float):
                g[(r["scenario"], r["controller"])][k].append(v)
    out = [f"# Amendement 5 : analyse ({len(runs)} runs valides sur {len(uids)})\n"]
    for cell in CELLS:
        out += [f"\n## {LAB[cell]} : moyenne (sd)\n", "| controleur | n | erreur de perturbation (%) | pic (xV*) | recup (s) | erreur stationnaire (%) | sync/s | arret sync max (s) |", "|---|---|---|---|---|---|---|---|"]
        for c in CTL:
            d = g[(cell, c)]
            if d["mae_burst_pct"]:
                out.append(f"| {c} | {len(d['mae_burst_pct'])} | " + " | ".join(f"{np.mean(d[m]):.2f} ({np.std(d[m], ddof=1) if len(d[m]) > 1 else float('nan'):.2f})" for m in ("mae_burst_pct", "peak_ratio", "recovery_s", "mae_pct", "sync_per_s", "max_sync_gap_s")) + " |")
    rows = []
    for cell in CELLS:
        for metric, margin in CRIT:
            for x, y in DECL + [REMIND]:
                va, vb = g[(cell, x)][metric], g[(cell, y)][metric]
                if len(va) < 2 or len(vb) < 2:
                    continue
                dd, lo, hi = bootstrap_diff_ci(va, vb)
                _, elo, ehi, eq = welch_tost(va, vb, margin)
                rows.append({"cell": cell, "metric": metric, "A": x, "B": y, "nA": len(va), "nB": len(vb), "meanA": np.mean(va), "meanB": np.mean(vb),
                             "diff": dd, "ci_lo": lo, "ci_hi": hi, "p_mwu": float(sps.mannwhitneyu(va, vb, alternative="two-sided").pvalue),
                             "p_perm": perm_test(va, vb), "cliffs_delta": cliffs_delta(va, vb), "equiv_margin": margin, "equiv_ci90_lo": elo,
                             "equiv_ci90_hi": ehi, "equivalent": eq, "declared": (x, y) in DECL})
    dec = [i for i, r in enumerate(rows) if r["declared"]]
    for i, q in zip(dec, holm([rows[i]["p_mwu"] for i in dec])):
        rows[i]["p_mwu_holm"] = float(q)
    if rows:
        with open(os.path.join(a.out, "contrasts_scenarios.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]) + ["p_mwu_holm"]); w.writeheader(); w.writerows(rows)
    out += [f"\n## Contrastes (A - B, IC bootstrap 95 %, Holm sur {len(dec)} tests declares)\n", "| cellule | critere | A - B | diff | IC95 | Cliff d | p (MWU) | p Holm | equivalent (marge) |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {LAB[r['cell']]} | {r['metric']} | {r['A']} - {r['B']}{'' if r['declared'] else ' (rappel)'} | {r['diff']:.2f} | [{r['ci_lo']:.2f}, {r['ci_hi']:.2f}] | "
                   f"{r['cliffs_delta']:.2f} | {r['p_mwu']:.2g} | {r.get('p_mwu_holm', float('nan')):.2g} | {'oui' if r['equivalent'] else 'non'} ({r['equiv_margin']}) |")
    out.append("\n## Controles de coherence (derive avec l'ordre des runs, erreur de perturbation)\n")
    byrep = collections.defaultdict(list)
    for r in runs:
        byrep[(r["scenario"], r["controller"])].append((r["rep"], r["mae_burst_pct"]))
    for k, v in sorted(byrep.items()):
        if len(v) >= 4:
            rho, p = sps.spearmanr([x for x, _ in v], [y for _, y in v])
            out.append(f"- {k[0]} / {k[1]} : Spearman rho = {rho:.2f} (p = {p:.2g})")
    open(os.path.join(a.out, "report_scenarios.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))
