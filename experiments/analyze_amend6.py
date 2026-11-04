"""Analysis of amendment 6.
Block A (confirmation): ONE declared contrast, periodic cell, reps 9..20 only: MPC_arima vs FF_obs on the disturbance-window error (two-sided Mann-Whitney,
alpha = 0.05, no correction; confirmed iff p < 0.05 AND MPC_arima is lower). Peak and the other metrics are descriptive.
Block B (operator baselines): per cell (burst, periodic) Static and Threshold against the contemporaneous FF_obs; Holm over 2 contrasts x 2 criteria x 2 cells = 8 tests.

    python experiments\\analyze_amend6.py --raw data\\raw --schedule schedule_amend6.csv --out analysis_amend6
"""
import argparse, csv, os, sys, collections
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from scipy import stats as sps
from mpcrpo.stats import holm, cliffs_delta, bootstrap_diff_ci, perm_test
from analyze_runs import load

M = ["mae_burst_pct", "peak_ratio", "recovery_s", "mae_pct", "sync_per_s", "max_sync_gap_s"]
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", nargs="+", required=True); ap.add_argument("--schedule", required=True); ap.add_argument("--out", default="analysis_amend6")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    uids = {r["run_uid"] for r in csv.DictReader(open(a.schedule, newline="", encoding="utf-8"))}
    runs = [r for r in load(a.raw) if r["run_uid"] in uids]
    out = [f"# Amendement 6 : analyse ({len(runs)} runs valides sur {len(uids)})\n"]
    # ---- block A
    A = collections.defaultdict(list)
    for r in runs:
        if r["scenario"] == "periodic" and r["controller"] in ("FF_obs", "MPC_arima") and 9 <= r["rep"] <= 20:
            A[r["controller"]].append(r)
    out.append("\n## Bloc A : confirmation sur le periodique (reps 9 a 20)\n")
    out += ["| controleur | n | erreur de perturbation (%) | pic (xV*) | recup (s) | erreur stationnaire (%) | sync/s |", "|---|---|---|---|---|---|---|"]
    for c in ("FF_obs", "MPC_arima"):
        v = lambda m: [r[m] for r in A[c]]
        out.append(f"| {c} | {len(A[c])} | " + " | ".join(f"{np.mean(v(m)):.2f} ({np.std(v(m), ddof=1):.2f})" for m in ("mae_burst_pct", "peak_ratio", "recovery_s", "mae_pct", "sync_per_s")) + " |")
    va, vb = [r["mae_burst_pct"] for r in A["MPC_arima"]], [r["mae_burst_pct"] for r in A["FF_obs"]]
    if len(va) > 1 and len(vb) > 1:
        d, lo, hi = bootstrap_diff_ci(va, vb); p = float(sps.mannwhitneyu(va, vb, alternative="two-sided").pvalue)
        out.append(f"\nContraste declare MPC_arima - FF_obs : {d:.2f} points, IC95 bootstrap [{lo:.2f}, {hi:.2f}], delta de Cliff {cliffs_delta(va, vb):.2f}, "
                   f"p (Mann-Whitney, bilateral) = {p:.3g}, p permutation = {perm_test(va, vb):.3g} -> "
                   + ("CONFIRME" if (p < 0.05 and d < 0) else "NON CONFIRME") + " (critere declare : p < 0,05 et MPC_arima plus bas)")
        pa, pb = [r["peak_ratio"] for r in A["MPC_arima"]], [r["peak_ratio"] for r in A["FF_obs"]]
        dp, plo, phi = bootstrap_diff_ci(pa, pb)
        out.append(f"Pic (descriptif) : {dp:.3f} [{plo:.3f}, {phi:.3f}]")
    # ---- block B
    B = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in runs:
        if r["controller"] in ("Static", "Threshold") or (r["controller"] == "FF_obs" and (r["scenario"] == "burst" or (r["scenario"] == "periodic" and r["rep"] >= 21))):
            for m in M:
                B[(r["scenario"], r["controller"])][m].append(r[m])
    out.append("\n## Bloc B : baselines d'operateur (moyenne (sd))\n")
    out += ["| cellule | controleur | n | " + " | ".join(M) + " |", "|---|---|---|" + "---|" * len(M)]
    for cell in ("burst", "periodic"):
        for c in ("Static", "Threshold", "FF_obs"):
            d = B[(cell, c)]
            if d["mae_burst_pct"]:
                out.append(f"| {cell} | {c} | {len(d['mae_burst_pct'])} | " + " | ".join(f"{np.mean(d[m]):.2f} ({np.std(d[m], ddof=1) if len(d[m]) > 1 else float('nan'):.2f})" for m in M) + " |")
    rows = []
    for cell in ("burst", "periodic"):
        for metric in ("mae_burst_pct", "peak_ratio"):
            for x in ("Static", "Threshold"):
                va, vb = B[(cell, x)][metric], B[(cell, "FF_obs")][metric]
                if len(va) < 2 or len(vb) < 2:
                    continue
                dd, lo, hi = bootstrap_diff_ci(va, vb)
                rows.append({"cell": cell, "metric": metric, "A": x, "B": "FF_obs", "nA": len(va), "nB": len(vb), "meanA": np.mean(va), "meanB": np.mean(vb), "diff": dd,
                             "ci_lo": lo, "ci_hi": hi, "p_mwu": float(sps.mannwhitneyu(va, vb, alternative="two-sided").pvalue), "p_perm": perm_test(va, vb),
                             "cliffs_delta": cliffs_delta(va, vb)})
    for r, q in zip(rows, holm([r["p_mwu"] for r in rows]) if rows else []):
        r["p_mwu_holm"] = float(q)
    if rows:
        with open(os.path.join(a.out, "contrasts_amend6.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    out += [f"\n### Contrastes (A - B, IC bootstrap 95 %, Holm sur {len(rows)} tests)\n", "| cellule | critere | A - B | diff | IC95 | Cliff d | p (MWU) | p Holm |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['cell']} | {r['metric']} | {r['A']} - FF_obs | {r['diff']:.2f} | [{r['ci_lo']:.2f}, {r['ci_hi']:.2f}] | {r['cliffs_delta']:.2f} | {r['p_mwu']:.2g} | {r['p_mwu_holm']:.2g} |")
    open(os.path.join(a.out, "report_amend6.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))
