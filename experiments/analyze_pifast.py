"""Analyse du bloc PI_fast (amendement 4) : comparaison CONTEMPORAINE PI_fast / PI_tuned / FF_obs sur la rafale.
Uniquement les runs du planning schedule_pifast.csv (aucun regroupement avec les campagnes anterieures).
Memes criteres principaux, memes tests directs (Mann-Whitney, permutation, Cliff's delta, IC bootstrap), Holm sur les contrastes
declares x criteres principaux, equivalence TOST (marges de l'etude).

    python experiments\\analyze_pifast.py --raw data\\raw --schedule schedule_pifast.csv --out analysis_pifast
"""
import argparse, csv, os, sys, collections
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from scipy import stats as sps
from mpcrpo.stats import holm, cliffs_delta, bootstrap_diff_ci, perm_test
from analyze_runs import load, welch_tost

CRIT = [("mae_burst_pct", 0.7), ("peak_ratio", 0.10)]
CONTR = [("PI_fast", "PI_tuned"), ("PI_fast", "FF_obs")]          # declares dans l'amendement 4
REF = ("PI_tuned", "FF_obs")                                       # rappel : l'ecart total, dans le meme bloc
SECOND = ["recovery_s", "mae_pct", "chatter", "sync_per_s", "max_sync_gap_s"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", nargs="+", required=True); ap.add_argument("--schedule", required=True)
    ap.add_argument("--out", default="analysis_pifast"); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    uids = {r["run_uid"] for r in csv.DictReader(open(a.schedule, newline="", encoding="utf-8"))}
    runs = [r for r in load(a.raw) if r["run_uid"] in uids]
    g = collections.defaultdict(lambda: collections.defaultdict(list)); rep = collections.defaultdict(list)
    for r in runs:
        for k, v in r.items():
            if isinstance(v, float):
                g[r["controller"]][k].append(v)
        rep[r["controller"]].append((r["rep"], r["mae_burst_pct"]))
    out = ["# Bloc PI_fast (amendement 4) : analyse contemporaine\n", f"Runs valides du planning : {len(runs)} / {len(uids)} ; par controleur : "
           + ", ".join(f"{c} n={len(g[c]['mae_burst_pct'])}" for c in ("PI_fast", "PI_tuned", "FF_obs")) + "\n"]
    out += ["\n## Moyennes (sd)\n", "| controleur | " + " | ".join(m for m, _ in CRIT) + " | " + " | ".join(SECOND) + " |", "|---|" + "---|" * (len(CRIT) + len(SECOND))]
    for c in ("PI_tuned", "PI_fast", "FF_obs"):
        out.append(f"| {c} | " + " | ".join(f"{np.mean(g[c][m]):.2f} ({np.std(g[c][m], ddof=1):.2f})" for m in [x for x, _ in CRIT] + SECOND) + " |")
    rows = []
    for metric, margin in CRIT:
        for x, y in CONTR + [REF]:
            va, vb = g[x][metric], g[y][metric]
            d, lo, hi = bootstrap_diff_ci(va, vb)
            _, elo, ehi, eq = welch_tost(va, vb, margin)
            rows.append({"metric": metric, "A": x, "B": y, "nA": len(va), "nB": len(vb), "meanA": np.mean(va), "meanB": np.mean(vb), "diff": d,
                         "ci_lo": lo, "ci_hi": hi, "p_mwu": float(sps.mannwhitneyu(va, vb, alternative="two-sided").pvalue),
                         "p_perm": perm_test(va, vb), "cliffs_delta": cliffs_delta(va, vb), "equiv_margin": margin,
                         "equiv_ci90_lo": elo, "equiv_ci90_hi": ehi, "equivalent": eq, "declared": (x, y) in CONTR})
    dec = [i for i, r in enumerate(rows) if r["declared"]]
    for i, q in zip(dec, holm([rows[i]["p_mwu"] for i in dec])):
        rows[i]["p_mwu_holm"] = float(q)
    with open(os.path.join(a.out, "contrasts_pifast.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) + ["p_mwu_holm"]); w.writeheader(); w.writerows(rows)
    out += ["\n## Contrastes (difference de moyennes A - B, IC bootstrap 95 %, Holm sur les 4 contrastes declares)\n",
            "| critere | A - B | diff | IC95 | Cliff d | p (MWU) | p Holm | equivalent (marge) |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['metric']} | {r['A']} - {r['B']}{'' if r['declared'] else ' (rappel)'} | {r['diff']:.2f} | [{r['ci_lo']:.2f}, {r['ci_hi']:.2f}] | "
                   f"{r['cliffs_delta']:.2f} | {r['p_mwu']:.2g} | {r.get('p_mwu_holm', float('nan')):.2g} | {'oui' if r['equivalent'] else 'non'} ({r['equiv_margin']}) |")
    # part de l'ecart PI_tuned -> FF_obs recuperee par le signal rapide
    out.append("\n## Part de l'ecart recuperee par le signal rapide : (PI_tuned - PI_fast) / (PI_tuned - FF_obs)\n")
    rng = np.random.default_rng(0)
    for metric, _ in CRIT:
        a1, a2, a3 = (np.asarray(g[c][metric], float) for c in ("PI_tuned", "PI_fast", "FF_obs"))
        pt = (a1.mean() - a2.mean()) / (a1.mean() - a3.mean())
        bs = [(rng.choice(a1, a1.size).mean() - rng.choice(a2, a2.size).mean()) / (rng.choice(a1, a1.size).mean() - rng.choice(a3, a3.size).mean()) for _ in range(10000)]
        out.append(f"- {metric} : {100 * pt:.0f} % (IC95 bootstrap {100 * np.percentile(bs, 2.5):.0f} a {100 * np.percentile(bs, 97.5):.0f} %)")
    out.append("\n## Controles de coherence\n")
    for c in ("PI_fast", "PI_tuned", "FF_obs"):
        rr = sorted(rep[c]); rho, p = sps.spearmanr([x for x, _ in rr], [y for _, y in rr])
        out.append(f"- {c} : derive de l'erreur de rafale avec la repetition, Spearman rho = {rho:.2f} (p = {p:.2g}) ; arret de sync max = {max(g[c]['max_sync_gap_s']):.1f} s")
    open(os.path.join(a.out, "report_pifast.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
