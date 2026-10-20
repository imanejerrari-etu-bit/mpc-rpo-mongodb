"""Sensitivity analysis report (descriptive: n=3 per variant, no p-values; effect sizes and ranges).

    python experiments/analyze_runs.py --raw data/raw --out analysis_all          # all runs, incl. variants
    python experiments/analyze_sensitivity.py --runs analysis_all/runs_metrics.csv --out sensitivity.md

Pre-specified criteria (docs/AMENDEMENT_2.md):
 C1 parameter robustness : worst-case ratio (variant / concurrent nominal) of the burst error, per controller.
 C2 ranking robustness   : max burst error over all perturbed PI_FF / FF_obs / MPC_persist variants  <  min over
                           all perturbed PI_tuned variants ?  (same for the exposure peak)
 C3 target robustness    : burst error and peak at V* = 2048 and 8192 for each controller.
"""
import argparse, csv, collections, numpy as np

BASES = ["PI_tuned", "PI_FF", "FF_obs", "MPC_persist"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True); ap.add_argument("--out", default="sensitivity.md")
    a = ap.parse_args()
    rows = [r for r in csv.DictReader(open(a.runs)) if r["scenario"] == "burst"]
    g = collections.defaultdict(list)
    for r in rows:
        g[r["controller"]].append(r)
    val = lambda name, m, rs=None: np.array([float(r[m]) for r in (rs if rs is not None else g.get(name, []))], float)
    # concurrent nominal controls = runs with rep >= 21 of the base controller
    nom = {b: [r for r in g.get(b, []) if int(r["rep"]) >= 21] for b in BASES}
    out = ["# Analyse de sensibilite (rafale, descriptive, n=3 par variante)\n"]
    out.append("## Temoins nominaux concurrents (repetitions 21-23, meme nuit que les variantes)\n")
    out.append("| controleur | n | erreur de rafale % | pic (x cible) |\n|---|---|---|---|")
    nm = {}
    for b in BASES:
        if nom[b]:
            e, p = val(b, "mae_burst_pct", nom[b]), val(b, "peak_ratio", nom[b])
            nm[b] = (e.mean(), p.mean())
            out.append(f"| {b} | {len(e)} | {e.mean():.2f} ({e.std(ddof=1) if len(e) > 1 else float('nan'):.2f}) | {p.mean():.2f} |")
    out.append("\n## C1 : perturbations des parametres (x0,5 / x1,5)\n")
    out.append("| variante | n | erreur de rafale % | rapport / nominal | pic | rapport / nominal | chatter |\n|---|---|---|---|---|---|---|")
    worst, perturbed = {}, collections.defaultdict(list)
    for name in sorted(g):
        if "__V" in name or "__" not in name:
            continue
        b = name.split("__")[0]
        if b not in nm:
            continue
        e, p, ch = val(name, "mae_burst_pct"), val(name, "peak_ratio"), val(name, "chatter")
        re, rp = e.mean() / nm[b][0], p.mean() / nm[b][1]
        worst[b] = max(worst.get(b, 0), re)
        perturbed[b].append((e.mean(), p.mean()))
        out.append(f"| {name} | {len(e)} | {e.mean():.2f} | {re:.2f} | {p.mean():.2f} | {rp:.2f} | {ch.mean():.3f} |")
    out.append("\nPire rapport erreur(variante)/erreur(nominal) par controleur : " +
               ", ".join(f"{b} x{w:.2f}" for b, w in worst.items()))
    out.append("\n## C2 : le classement survit-il aux perturbations ?\n")
    if perturbed.get("PI_tuned"):
        pi_min_e = min(x[0] for x in perturbed["PI_tuned"]); pi_min_p = min(x[1] for x in perturbed["PI_tuned"])
        ff = [x for b in ("PI_FF", "FF_obs", "MPC_persist") for x in perturbed.get(b, [])]
        ff_max_e, ff_max_p = max(x[0] for x in ff), max(x[1] for x in ff)
        out.append(f"- Erreur de rafale : pire variante (PI_FF, FF_obs, MPC_persist) = {ff_max_e:.2f} % ; meilleure variante de PI_tuned = "
                   f"{pi_min_e:.2f} % -> classement conserve : **{'OUI' if ff_max_e < pi_min_e else 'NON'}**")
        out.append(f"- Pic d'exposition : pire variante = {ff_max_p:.2f} ; meilleure variante de PI_tuned = {pi_min_p:.2f} -> "
                   f"classement conserve : **{'OUI' if ff_max_p < pi_min_p else 'NON'}**")
        fam = {b: (min(x[0] for x in v), max(x[0] for x in v)) for b, v in perturbed.items()}
        out.append("- Plages de l'erreur de rafale sous perturbation : " + "; ".join(f"{b} [{lo:.2f} ; {hi:.2f}]" for b, (lo, hi) in fam.items()))
    out.append("\n## C3 : changement de la cible V*\n")
    out.append("| controleur | V* | n | erreur de rafale % | pic | sync/s |\n|---|---|---|---|---|---|")
    for b in BASES:
        for name in [b] + [f"{b}__V2048", f"{b}__V8192"]:
            if name in g or name == b:
                rs = nom[b] if name == b else g[name]
                if not rs:
                    continue
                vs = "4096 (nominal)" if name == b else name.split("__V")[1]
                out.append(f"| {b} | {vs} | {len(rs)} | {val(name,'mae_burst_pct',rs).mean():.2f} | {val(name,'peak_ratio',rs).mean():.2f} | {val(name,'sync_per_s',rs).mean():.2f} |")
    out.append("\nNote : a V* = 2048 la cible est inatteignable en rafale (il faudrait J < 20 ms) : une erreur residuelle est attendue.")
    open(a.out, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
