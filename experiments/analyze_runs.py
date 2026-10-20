"""Analysis of real runs (pilot or campaign): per-run metrics, group summaries, the PRE-SPECIFIED contrasts
(Mann-Whitney + permutation + Cliff's delta + bootstrap CI of the difference, Holm over contrasts x primary
criteria) and equivalence tests (TOST, Welch) for the pairs where 'no difference' is the claim.

    python experiments/analyze_runs.py --raw data/raw [more dirs] --out analysis
Outputs: analysis/runs_metrics.csv, analysis/summary.csv, analysis/contrasts.csv, analysis/report.md
Only runs with valid=true are analysed (INVALID_* files are ignored).
"""
import argparse, csv, glob, json, os, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from scipy import stats as sps
from mpcrpo.config import Common
from mpcrpo.metrics import run_metrics
from mpcrpo.stats import holm, cliffs_delta, bootstrap_diff_ci, perm_test

ORDER = ["PI_default", "PI_tuned", "PI_FF", "FF_obs", "MPC_persist", "MPC_ma", "MPC_arima"]
CONTRASTS = [("PI_tuned", "PI_FF"), ("PI_FF", "FF_obs"), ("FF_obs", "MPC_persist"), ("PI_FF", "MPC_persist"),
             ("MPC_persist", "MPC_ma"), ("MPC_persist", "MPC_arima"), ("PI_tuned", "MPC_persist")]
EQUIV = [("FF_obs", "MPC_persist"), ("MPC_persist", "MPC_arima")]            # claim = "no practical difference"
PRIMARY = {"burst": [("mae_burst_pct", 0.7), ("peak_ratio", 0.10)]}           # (metric, equivalence margin)
SECONDARY = {"stationary": ["mae_pct", "chatter", "sync_per_s"], "burst": ["mae_burst_pct", "peak_ratio", "mae_pct", "recovery_s", "sync_per_s", "chatter", "max_sync_gap_s"],
             "lowload": ["mae_pct", "mae_burst_pct", "sat_frac", "recovery_s"]}


def max_sync_gap(rec, common):
    """Longest stretch (s) with NO journal sync while bytes keep being written and J <= 250 ms (after warm-up)."""
    t, S, B, J = rec["t"], rec["sync"], rec["bytes"], rec["J"]
    best = cur = 0.0
    for i in range(1, len(t)):
        stalled = (S[i] == S[i - 1]) and (B[i] > B[i - 1]) and J[i - 1] <= 0.25 and t[i] >= common.warmup_s
        cur = cur + (t[i] - t[i - 1]) if stalled else 0.0
        best = max(best, cur)
    return best


def load(dirs):
    out = []
    for d in dirs:
        for f in sorted(glob.glob(os.path.join(d, "*.json"))):
            if ".INVALID_" in f:
                continue
            j = json.load(open(f))
            if not (j.get("complete") and j.get("valid", True)):
                continue
            parts = j["run_uid"].split("_")
            rec = {k: np.array(j[k], float) for k in ("t", "flush", "sync", "bytes", "J", "tps")}
            cm = Common(**j["config"]["Common"])
            m = run_metrics(rec, cm, j["config"]["scenario"])
            m["max_sync_gap_s"] = max_sync_gap(rec, cm)
            out.append({"run_uid": j["run_uid"], "scenario": parts[1], "controller": "_".join(parts[2:-1]),
                        "rep": int(parts[-1][3:]), "hash": j["config_hash"], **m})
    return out


def welch_tost(a, b, margin):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = a.mean() - b.mean()
    va, vb = a.var(ddof=1) / a.size, b.var(ddof=1) / b.size
    se = np.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (a.size - 1) + vb ** 2 / (b.size - 1))
    t = sps.t.ppf(0.95, df)
    lo, hi = d - t * se, d + t * se                       # 90 % CI  <->  TOST at alpha = 0.05
    return d, lo, hi, bool(lo > -margin and hi < margin)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", nargs="+", required=True); ap.add_argument("--out", default="analysis")
    ap.add_argument("--max-rep", type=int, default=None,
                    help="keep only repetitions <= this (main analysis: 20, excludes the sensitivity-phase controls rep 21+)")
    ap.add_argument("--exclude-stall-s", type=float, default=None,
                    help="SENSITIVITY analysis: drop runs whose longest journal-sync gap is >= this many seconds")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    runs = load(a.raw)
    if a.max_rep is not None:
        runs = [r for r in runs if r["rep"] <= a.max_rep]
    dropped = []
    if a.exclude_stall_s is not None:
        dropped = [r["run_uid"] for r in runs if r["max_sync_gap_s"] >= a.exclude_stall_s]
        runs = [r for r in runs if r["max_sync_gap_s"] < a.exclude_stall_s]
    metrics = sorted({k for r in runs for k in r if k not in ("run_uid", "scenario", "controller", "rep", "hash")})
    with open(os.path.join(a.out, "runs_metrics.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["run_uid", "scenario", "controller", "rep", "hash"] + metrics, extrasaction="ignore")
        w.writeheader(); w.writerows(runs)
    g = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in runs:
        for m in metrics:
            if m in r:
                g[(r["scenario"], r["controller"])][m].append(r[m])
    rep = [f"# Analyse ({len(runs)} runs valides)\n"]
    if a.exclude_stall_s is not None:
        rep.append(f"**ANALYSE DE SENSIBILITE (post hoc)** : runs exclus car arret du sync >= {a.exclude_stall_s} s : {dropped}\n")
    with open(os.path.join(a.out, "summary.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["scenario", "controller", "n", "metric", "mean", "sd", "median"])
        for (scn, c), d in sorted(g.items()):
            for m, v in d.items():
                v = np.array(v, float)
                w.writerow([scn, c, len(v), m, np.nanmean(v), np.nanstd(v, ddof=1) if len(v) > 1 else "", np.nanmedian(v)])
    for scn, ms in SECONDARY.items():
        rep.append(f"\n## {scn} : moyenne (sd) [n]\n")
        rep.append("| controleur | n | " + " | ".join(ms) + " |\n|---|---|" + "---|" * len(ms))
        for c in ORDER:
            if (scn, c) in g:
                cells = []
                for m in ms:
                    v = np.array(g[(scn, c)].get(m, [np.nan]), float)
                    cells.append(f"{np.nanmean(v):.2f} ({np.nanstd(v, ddof=1) if len(v) > 1 else float('nan'):.2f})")
                rep.append(f"| {c} | {len(g[(scn, c)][ms[0]])} | " + " | ".join(cells) + " |")
    rows = []
    for scn, crit in PRIMARY.items():
        for metric, margin in crit:
            for x, y in CONTRASTS:
                va, vb = g.get((scn, x), {}).get(metric), g.get((scn, y), {}).get(metric)
                if not va or not vb or len(va) < 2 or len(vb) < 2:
                    continue
                d, lo, hi = bootstrap_diff_ci(va, vb)
                rows.append({"scenario": scn, "metric": metric, "A": x, "B": y, "nA": len(va), "nB": len(vb),
                             "meanA": np.mean(va), "meanB": np.mean(vb), "diff": d, "ci_lo": lo, "ci_hi": hi,
                             "p_mwu": sps.mannwhitneyu(va, vb, alternative="two-sided").pvalue,
                             "p_perm": perm_test(va, vb), "cliffs_delta": cliffs_delta(va, vb)})
    adj = holm([r["p_mwu"] for r in rows]) if rows else []
    for r, q in zip(rows, adj):
        r["p_mwu_holm"] = q
    eq = []
    for scn, crit in PRIMARY.items():
        for metric, margin in crit:
            for x, y in EQUIV:
                va, vb = g.get((scn, x), {}).get(metric), g.get((scn, y), {}).get(metric)
                if va and vb and len(va) > 1 and len(vb) > 1:
                    d, lo, hi, ok = welch_tost(va, vb, margin)
                    eq.append({"scenario": scn, "metric": metric, "A": x, "B": y, "margin": margin, "diff": d,
                               "ci90_lo": lo, "ci90_hi": hi, "equivalent": ok})
    if rows:
        with open(os.path.join(a.out, "contrasts.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        rep.append("\n## Contrastes pre-specifies (criteres primaires, rafale) : Mann-Whitney, Holm sur "
                   f"{len(rows)} tests\n")
        rep.append("| metrique | A vs B | nA/nB | diff [IC95 bootstrap] | Cliff | p brut | p Holm |\n|---|---|---|---|---|---|---|")
        for r in rows:
            rep.append(f"| {r['metric']} | {r['A']} vs {r['B']} | {r['nA']}/{r['nB']} | {r['diff']:+.2f} "
                       f"[{r['ci_lo']:+.2f}, {r['ci_hi']:+.2f}] | {r['cliffs_delta']:+.2f} | {r['p_mwu']:.3g} | {r['p_mwu_holm']:.3g} |")
        min_p = min(r["p_mwu"] for r in rows)
        rep.append(f"\nNote : avec n petit, le plus petit p de Mann-Whitney possible est limite par n "
                   f"(ici p minimal observe {min_p:.3g}) ; pour n=3 vs 3 il vaut 0,1 : aucun contraste ne peut passer Holm.")
    if eq:
        with open(os.path.join(a.out, "equivalence.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(eq[0])); w.writeheader(); w.writerows(eq)
        rep.append("\n## Equivalence (TOST, IC90 de Welch dans +/- marge)\n")
        rep.append("| metrique | A vs B | marge | diff [IC90] | equivalents ? |\n|---|---|---|---|---|")
        for r in eq:
            rep.append(f"| {r['metric']} | {r['A']} vs {r['B']} | {r['margin']} | {r['diff']:+.2f} "
                       f"[{r['ci90_lo']:+.2f}, {r['ci90_hi']:+.2f}] | {'oui' if r['equivalent'] else 'non concluant'} |")
    open(os.path.join(a.out, "report.md"), "w", encoding="utf-8").write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
