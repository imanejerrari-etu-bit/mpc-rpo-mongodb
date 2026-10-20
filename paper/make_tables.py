"""Tables and numbers of the manuscript, generated from the analysis outputs (no hand-typed results).
    python experiments/analyze_runs.py --raw data/raw --out analysis_primary --max-rep 20
    python experiments/analyze_runs.py --raw data/raw --out analysis_sens --max-rep 20 --exclude-stall-s 5
    python paper/make_tables.py --primary analysis_primary --sens analysis_sens --step2 step2_summary.json --out paper
Writes paper/numbers.tex (macros), paper/tab_*.tex.
"""
import argparse, csv, collections, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from mpcrpo.controllers import v_model

KEY = {"PI_default": "PID", "PI_tuned": "PIT", "PI_FF": "PIFF", "FF_obs": "FFO", "MPC_persist": "MPCP", "MPC_ma": "MPCM", "MPC_arima": "MPCA"}
NAME = {"PI_default": "PI (default gains)", "PI_tuned": "PI (tuned)", "PI_FF": "PI + feedforward", "FF_obs": "FF + observer",
        "MPC_persist": "MPC, persistence", "MPC_ma": "MPC, moving average", "MPC_arima": "MPC, ARIMA(1,1,0)"}
SHORTN = {"PI_default": "PI-def.", "PI_tuned": "PI", "PI_FF": "PI-FF", "FF_obs": "FF+obs", "MPC_persist": "MPC-pers.", "MPC_ma": "MPC-MA", "MPC_arima": "MPC-ARIMA"}
ORDER = list(KEY)


def runs(path):
    return list(csv.DictReader(open(os.path.join(path, "runs_metrics.csv"))))


def stats(rs, scn, c, m):
    v = np.array([float(r[m]) for r in rs if r["scenario"] == scn and r["controller"] == c and r[m] not in ("", "nan")], float)
    return len(v), (v.mean() if len(v) else float("nan")), (v.std(ddof=1) if len(v) > 1 else float("nan"))


def f(x, d=2):
    return "--" if x != x else f"{x:.{d}f}"


def sci(p):
    return f"{p:.1e}".replace("e-0", "\\!\\times\\!10^{-").replace("e-", "\\!\\times\\!10^{-") + "}" if p < 1e-3 else f"{p:.3f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--primary", required=True); ap.add_argument("--sens", required=True)
    ap.add_argument("--step2", required=True); ap.add_argument("--out", default="paper")
    ap.add_argument("--step3b", required=True, help="step3b_ticks.jsonl (real burst step test)")
    ap.add_argument("--specs", required=True, help="tuned_specs.json")
    ap.add_argument("--all", required=True, help="analysis dir of ALL runs (incl. sensitivity variants) for tab_sens")
    a = ap.parse_args()
    P, S = runs(a.primary), runs(a.sens)
    mac = []
    # ---- per-controller numbers (S = excluding the stalled run; P = all valid runs) -----------------------
    for tag, rs in (("S", S), ("P", P)):
        for c in ORDER:
            for scn, m, nm in (("burst", "mae_burst_pct", "Mae"), ("burst", "peak_ratio", "Peak"), ("burst", "chatter", "Chat"),
                               ("stationary", "mae_pct", "Stat"), ("lowload", "mae_pct", "Low"), ("lowload", "recovery_s", "LowRec"),
                               ("lowload", "mae_burst_pct", "LowBurst"), ("burst", "sync_per_s", "Sync")):
                n, mu, sd = stats(rs, scn, c, m)
                mac += [f"\\newcommand{{\\{nm}{KEY[c]}{tag}}}{{{f(mu, 3 if nm=='Chat' else 2)}}}", f"\\newcommand{{\\{nm}Sd{KEY[c]}{tag}}}{{{f(sd, 2)}}}",
                        f"\\newcommand{{\\N{nm}{KEY[c]}{tag}}}{{{n}}}"]
    # ---- contrasts and equivalence -------------------------------------------------------------------------
    CT = {}
    for tag, d in (("P", a.primary), ("S", a.sens)):
        for r in csv.DictReader(open(os.path.join(d, "contrasts.csv"))):
            CT[(tag, r["metric"], r["A"], r["B"])] = r
            k = f"{KEY[r['A']]}{KEY[r['B']]}"
            mt = "Mae" if r["metric"] == "mae_burst_pct" else "Peak"
            for nm, col, dd in (("D", "diff", 2), ("Lo", "ci_lo", 2), ("Hi", "ci_hi", 2), ("Cliff", "cliffs_delta", 2)):
                mac.append(f"\\newcommand{{\\c{nm}{mt}{k}{tag}}}{{{float(r[col]):.{dd}f}}}")
            mac.append(f"\\newcommand{{\\cA{mt}{k}{tag}}}{{{abs(float(r['diff'])):.2f}}}")
            mac.append(f"\\newcommand{{\\cPH{mt}{k}{tag}}}{{{sci(float(r['p_mwu_holm']))}}}")
        for r in csv.DictReader(open(os.path.join(d, "equivalence.csv"))):
            k = f"{KEY[r['A']]}{KEY[r['B']]}"; mt = "Mae" if r["metric"] == "mae_burst_pct" else "Peak"
            for nm, col in (("Lo", "ci90_lo"), ("Hi", "ci90_hi"), ("D", "diff")):
                mac.append(f"\\newcommand{{\\e{nm}{mt}{k}{tag}}}{{{float(r[col]):+.2f}}}")
            mac.append(f"\\newcommand{{\\eOK{mt}{k}{tag}}}{{{'equivalent' if r['equivalent']=='True' else 'inconclusive'}}}")
    # ---- main results table (analysis excluding the one stalled run) ----------------------------------------
    L = ["\\begin{table*}[t]\\centering\\small",
         "\\caption{Burst scenario (400$\\to$1600 documents/s for 60 s): primary criteria and secondary measures, mean (sd) over $n$ valid runs "
         "(pilot included). The single run with a journal-sync stall $\\geq 5$\\,s (FF + observer) is excluded here; all contrasts are also "
         "reported with it (Table~\\ref{tab:contrasts}). Peak = maximum exposure over 2\\,s windows relative to the target $V^*$.}\\label{tab:main}",
         "\\resizebox{0.92\\textwidth}{!}{\\begin{tabular}{lrcccc}\\toprule", "Controller & $n$ & Burst error (\\%) & Peak ($\\times V^*$) & Steady error (\\%) & $|\\Delta\\ln J|$ per tick\\\\\\midrule"]
    for c in ORDER:
        n, mu, sd = stats(S, "burst", c, "mae_burst_pct"); _, pk, pks = stats(S, "burst", c, "peak_ratio")
        _, ms, mss = stats(S, "burst", c, "mae_pct"); _, ch, chs = stats(S, "burst", c, "chatter")
        L.append(f"{NAME[c]} & {n} & {f(mu)} ({f(sd)}) & {f(pk)} ({f(pks)}) & {f(ms)} ({f(mss)}) & {f(ch,3)} ({f(chs,3)})\\\\")
    L += ["\\bottomrule\\end{tabular}}\\end{table*}"]
    open(os.path.join(a.out, "tab_main.tex"), "w").write("\n".join(L) + "\n")
    # ---- contrasts table ----------------------------------------------------------------------------------------
    L = ["\\begin{table*}[t]\\centering\\small",
         "\\caption{Pre-specified contrasts (Mann--Whitney U, two-sided; Holm correction over the 14 tests = 7 contrasts $\\times$ 2 primary "
         "criteria). Difference = mean(A) $-$ mean(B) with 95\\% bootstrap CI; $\\delta$ = Cliff's delta. ``All runs'' includes the stalled run; "
         "``excl.'' removes it (post hoc sensitivity analysis).}\\label{tab:contrasts}",
         "\\resizebox{\\textwidth}{!}{\\begin{tabular}{llccccc}\\toprule", " & Contrast (A vs B) & Difference [95\\% CI] (all runs) & $\\delta$ & $p_{\\text{Holm}}$ (all) & Difference [CI] (excl.) & $p_{\\text{Holm}}$ (excl.)\\\\\\midrule"]
    for metric, lab, dd in (("mae_burst_pct", "Burst error (pp)", 2), ("peak_ratio", "Peak ($\\times V^*$)", 2)):
        L.append(f"\\multicolumn{{7}}{{l}}{{\\emph{{{lab}}}}}\\\\")
        for (t, m, A, B), r in CT.items():
            if t != "P" or m != metric:
                continue
            s = CT[("S", m, A, B)]
            L.append(f" & {SHORTN[A]} vs {SHORTN[B]} & {float(r['diff']):+.2f} [{float(r['ci_lo']):+.2f}, {float(r['ci_hi']):+.2f}] & {float(r['cliffs_delta']):+.2f} & ${sci(float(r['p_mwu_holm']))}$ "
                     f"& {float(s['diff']):+.2f} [{float(s['ci_lo']):+.2f}, {float(s['ci_hi']):+.2f}] & ${sci(float(s['p_mwu_holm']))}$\\\\")
    L += ["\\bottomrule\\end{tabular}}\\end{table*}"]
    open(os.path.join(a.out, "tab_contrasts.tex"), "w").write("\n".join(L) + "\n")
    # ---- equivalence table --------------------------------------------------------------------------------------
    EQ = {}
    for tag, d in (("P", a.primary), ("S", a.sens)):
        for r in csv.DictReader(open(os.path.join(d, "equivalence.csv"))):
            EQ[(tag, r["metric"], r["A"], r["B"])] = r
    L = ["\\begin{table}[t]\\centering\\small",
         "\\caption{Equivalence tests (TOST, Welch 90\\% CI inside $\\pm$ margin; margins 0.7\\,pp on the burst error and 0.10 on the peak).}\\label{tab:equiv}",
         "\\resizebox{\\columnwidth}{!}{\\begin{tabular}{lccc}\\toprule", "Pair, criterion & 90\\% CI (excl.) & verdict (excl.) & verdict (all)\\\\\\midrule"]
    for (t, m, A, B), r in EQ.items():
        if t != "S":
            continue
        pall = EQ.get(("P", m, A, B), {})
        lab = f"{SHORTN[A]} vs {SHORTN[B]}, {'error' if m=='mae_burst_pct' else 'peak'}"
        L.append(f"{lab} & [{float(r['ci90_lo']):+.2f}, {float(r['ci90_hi']):+.2f}] & {'equivalent' if r['equivalent']=='True' else 'inconclusive'} & "
                 f"{'equivalent' if pall.get('equivalent')=='True' else 'inconclusive'}\\\\")
    L += ["\\bottomrule\\end{tabular}}\\end{table}"]
    open(os.path.join(a.out, "tab_equiv.tex"), "w").write("\n".join(L) + "\n")
    # ---- low load / stationary table ---------------------------------------------------------------------------------
    L = ["\\begin{table}[t]\\centering\\small",
         "\\caption{Stationary (400 documents/s) and low-load (100$\\to$400 documents/s, target unreachable at the start) scenarios, mean over $n$ runs.}\\label{tab:other}",
         "\\resizebox{\\columnwidth}{!}{\\begin{tabular}{lcccc}\\toprule", "Controller & Stat. err. (\\%) & Low-load err. (\\%) & Recov. (s) & $n$\\\\\\midrule"]
    for c in ORDER:
        _, st, _ = stats(S, "stationary", c, "mae_pct"); n, lo, _ = stats(S, "lowload", c, "mae_pct"); _, rc, _ = stats(S, "lowload", c, "recovery_s")
        L.append(f"{SHORTN[c]} & {f(st)} & {f(lo)} & {f(rc,1)} & {n}\\\\")
    L += ["\\bottomrule\\end{tabular}}\\end{table}"]
    open(os.path.join(a.out, "tab_other.tex"), "w").write("\n".join(L) + "\n")
    # ---- static plant table (step 2) ----------------------------------------------------------------------------------
    Sm = json.load(open(a.step2))
    L = ["\\begin{table}[t]\\centering\\small",
         "\\caption{Static plant: measured exposed volume $V$ (kB per sync) versus the model $V=R(J+pL_0)/p$, $p=\\min(1,RJ/b_0)$, $b_0=513$\\,B, $L_0=7$\\,ms.}\\label{tab:plant}",
         "\\begin{tabular}{rrrrrr}\\toprule", "Load (docs/s) & $J$ (ms) & $R$ (kB/s) & $V$ meas. & $V$ model & err. (\\%)\\\\\\midrule"]
    errs = []
    for s in Sm:
        R = s["bytes_per_s"]; V = s["V_per_sync_B"]; Vm = float(v_model(R, s["J_ms"] / 1000, 513.0, 0.007)); errs.append(abs(Vm / V - 1) * 100)
        L.append(f"{s['tps_nominal']:.0f} & {s['J_ms']} & {R/1024:.1f} & {V/1024:.2f} & {Vm/1024:.2f} & {(Vm/V-1)*100:+.1f}\\\\")
    L += ["\\bottomrule\\end{tabular}\\end{table}"]
    open(os.path.join(a.out, "tab_plant.tex"), "w").write("\n".join(L) + "\n")

    # ---- measurement noise (step 2 grid + step 3b ticks) ---------------------------------------------------------
    cv = {}
    L = ["\\begin{table}[t]\\centering\\small",
         "\\caption{Measurement noise of the 10\\,s signal $V$ (relative standard deviation over a 60\\,s segment, open loop) and syncs per window.}\\label{tab:noise}",
         "\\begin{tabular}{rrrr}\\toprule", "Load (docs/s) & $J$ (ms) & $\\mathrm{sd}(V)/V$ (\\%) & syncs per 10\\,s\\\\\\midrule"]
    for s2 in Sm:
        c_ = s2["V10s_sd_B"] / s2["V10s_mean_B"] * 100
        cv.setdefault(s2["J_ms"], []).append(c_)
        L.append(f"{s2['tps_nominal']:.0f} & {s2['J_ms']} & {c_:.1f} & {s2['sync_per_s']*10:.0f}\\\\")
    L += ["\\bottomrule\\end{tabular}\\end{table}"]
    open(os.path.join(a.out, "tab_noise.tex"), "w").write("\n".join(L) + "\n")
    for J_, nm in ((500, "FiveHundred"), (100, "Hundred"), (20, "Twenty")):
        mac.append(f"\\newcommand{{\\vcvMin{nm}}}{{{min(cv[J_]):.1f}}}")
        mac.append(f"\\newcommand{{\\vcvMax{nm}}}{{{max(cv[J_]):.1f}}}")
    ticks = [json.loads(l) for l in open(a.step3b) if l.strip()]
    rc = collections.defaultdict(list); ac = collections.defaultdict(list)
    for J_ in sorted({t["J_ms"] for t in ticks}):
        rs = [t for t in ticks if t["J_ms"] == J_]
        tt = np.array([t["t"] for t in rs]); B = np.array([t["bytes"] for t in rs], float)
        R = np.diff(B) / 0.5; t2 = tt[1:]
        for ph, (lo, hi) in (("base", (25, 60)), ("burst", (80, 120))):
            x = R[(t2 >= lo) & (t2 < hi)]
            rc[ph].append(x.std() / x.mean() * 100)
            xx = x - x.mean(); ac[ph].append(float((xx[:-1] @ xx[1:]) / (xx @ xx)))
    for ph in ("base", "burst"):
        mac.append(f"\\newcommand{{\\rcv{ph.capitalize()}Min}}{{{min(rc[ph]):.1f}}}")
        mac.append(f"\\newcommand{{\\rcv{ph.capitalize()}Max}}{{{max(rc[ph]):.1f}}}")
        mac.append(f"\\newcommand{{\\racf{ph.capitalize()}Min}}{{{min(ac[ph]):+.2f}}}")
        mac.append(f"\\newcommand{{\\racf{ph.capitalize()}Max}}{{{max(ac[ph]):+.2f}}}")
    # ---- parameters table ----------------------------------------------------------------------------------------------
    sp = json.load(open(a.specs))
    spec = sp["specs"]
    def g(d, k, fmt="{:g}"):
        return fmt.format(d[k]) if k in d else "--"
    L = ["\\begin{table*}[t]\\centering\\small",
         f"\\caption{{Controller parameters used in all runs (random search, {sp['budget']} candidates per family, robust objective; "
         "nominal values from the repository file \\texttt{tuned\\_specs.json}). PI-default is the naive reference (no tuning). "
         "Dashes: parameter not used by the family.}\\label{tab:params}",
         "\\resizebox{\\textwidth}{!}{\\begin{tabular}{lccccccccccc}\\toprule",
         "Controller & $K_p$ & $K_i$ & anti-windup & $\\alpha_V$ & feedforward & $\\alpha_{R}$ & bias $\\alpha_b$ & $H$ & $\\gamma$ & $\\lambda$ & $w$ (below target)\\\\\\midrule",
         "PI-default & 0.3 & 0.05 & clamp & 1 & no & -- & -- & -- & -- & -- & --\\\\"]
    for key, nm in (("PI", "PI (tuned)"), ("PI_FF", "PI-FF"), ("FF_obs", "FF+obs")):
        d = spec[key]
        L.append(f"{nm} & {g(d,'kp','{:.2f}')} & {g(d,'ki','{:.2f}')} & {d.get('antiwindup','--')} & {g(d,'filter_alpha')} & {'yes' if d.get('ff') else 'no'} & {g(d,'ff_alpha')} & {g(d,'bias_alpha')} & -- & -- & -- & --\\\\")
    for key, nm in (("MPC_persist", "MPC persistence"), ("MPC_ma", "MPC moving average"), ("MPC_arima", "MPC ARIMA(1,1,0)")):
        d = spec[key]
        L.append(f"{nm} & -- & -- & -- & -- & -- & {g(d,'ewma_alpha')} & {g(d,'bias_alpha')} & {d['horizon']} & {d['gamma']:g} & {d['lam']:.3f} & {d['under_weight']:.2f}\\\\")
    L += ["\\bottomrule\\end{tabular}}",
          "\\\\[2pt]{\\footnotesize Common: $V^*=4096$\\,B, period 0.5\\,s, $J\\in[20,500]$\\,ms, $J_0=100$\\,ms, window 10\\,s, $b_0=513$\\,B, $L_0=7$\\,ms; "
          "MA/ARIMA window 5 / 5 samples (persistence ignores it). $\\alpha_V$: filter on $\\ln V$; $\\alpha_R$: smoothing of the load estimate; "
          "$\\alpha_b$: bias observer.}\\end{table*}"]
    open(os.path.join(a.out, "tab_params.tex"), "w").write("\n".join(L) + "\n")

    # ---- sensitivity (descriptive; concurrent nominal controls = repetitions >= 21) -------------------------------------------
    AL = [r for r in csv.DictReader(open(os.path.join(a.all, "runs_metrics.csv"))) if r["scenario"] == "burst"]
    G = collections.defaultdict(list)
    for r in AL:
        G[r["controller"]].append(r)
    mv = lambda rs, m: np.array([float(r[m]) for r in rs], float)
    BASES = ["PI_tuned", "PI_FF", "FF_obs", "MPC_persist"]
    nom = {b: [r for r in G[b] if int(r["rep"]) >= 21] for b in BASES}
    nm_ = {b: (mv(nom[b], "mae_burst_pct").mean(), mv(nom[b], "peak_ratio").mean()) for b in BASES}
    LBL = {"kpx0p5": "$K_p\\times0.5$", "kpx1p5": "$K_p\\times1.5$", "kix0p5": "$K_i\\times0.5$", "kix1p5": "$K_i\\times1.5$",
           "ff_alphax0p5": "$\\alpha_R\\times0.5$", "bias_alphax0p5": "$\\alpha_b\\times0.5$", "lamx0p5": "$\\lambda\\times0.5$",
           "lamx1p5": "$\\lambda\\times1.5$", "under_weightx0p5": "$w\\times0.5$", "under_weightx1p5": "$w\\times1.5$", "ewma_alphax0p5": "$\\alpha_R\\times0.5$"}
    L = ["\\begin{table}[t]\\centering\\small",
         "\\caption{Sensitivity to controller parameters (burst scenario, $n=3$ per variant, one-at-a-time, descriptive). Ratios are relative to "
         "3 concurrent nominal runs of the same controller. Nominal: PI \\MaeSensPITnom\\,\\%, PI-FF \\MaeSensPIFFnom\\,\\%, FF+obs \\MaeSensFFOnom\\,\\%, MPC \\MaeSensMPCPnom\\,\\%.}\\label{tab:sens}",
         "\\resizebox{\\columnwidth}{!}{\\begin{tabular}{llcccc}\\toprule", "Controller & Variant & Error (\\%) & Ratio & Peak ($\\times V^*$) & $|\\Delta\\ln J|$\\\\\\midrule"]
    worst, per, pk = {}, collections.defaultdict(list), collections.defaultdict(list)
    for b in BASES:
        for name in sorted(k for k in G if k.startswith(b + "__") and "__V" not in k):
            e, p_, ch = mv(G[name], "mae_burst_pct"), mv(G[name], "peak_ratio"), mv(G[name], "chatter")
            var = name.split("__")[1]
            ratio = e.mean() / nm_[b][0]
            worst[b] = max(worst.get(b, 0), ratio); per[b].append(e.mean()); pk[b].append(p_.mean())
            L.append(f"{SHORTN[b]} & {LBL.get(var, var)} & {e.mean():.2f} & {ratio:.2f} & {p_.mean():.2f} & {ch.mean():.3f}\\\\")
    L += ["\\bottomrule\\end{tabular}}\\end{table}"]
    open(os.path.join(a.out, "tab_sens.tex"), "w").write("\n".join(L) + "\n")
    L = ["\\begin{table}[t]\\centering\\small",
         "\\caption{Change of the target $V^*$ (burst, $n=3$): error, peak and journal syncs per second. At $V^*=2048$\\,B the target is unreachable during the burst ($J$ would be below 20\\,ms).}\\label{tab:vstar}",
         "\\begin{tabular}{llccc}\\toprule", "Controller & $V^*$ (B) & Error (\\%) & Peak & syncs/s\\\\\\midrule"]
    for b in ["PI_FF", "FF_obs", "MPC_persist"]:
        for vv, rs in (("2048", G.get(f"{b}__V2048", [])), ("4096", nom[b]), ("8192", G.get(f"{b}__V8192", []))):
            if rs:
                L.append(f"{SHORTN[b]} & {vv} & {mv(rs,'mae_burst_pct').mean():.2f} & {mv(rs,'peak_ratio').mean():.2f} & {mv(rs,'sync_per_s').mean():.2f}\\\\")
    L += ["\\bottomrule\\end{tabular}\\end{table}"]
    open(os.path.join(a.out, "tab_vstar.tex"), "w").write("\n".join(L) + "\n")
    K = {"PI_tuned": "PIT", "PI_FF": "PIFF", "FF_obs": "FFO", "MPC_persist": "MPCP"}
    for b in BASES:
        mac.append(f"\\newcommand{{\\MaeSens{K[b]}nom}}{{{nm_[b][0]:.2f}}}")
        mac.append(f"\\newcommand{{\\SensWorst{K[b]}}}{{{worst[b]:.2f}}}")
        mac.append(f"\\newcommand{{\\SensMaxPeak{K[b]}}}{{{max(pk[b]):.2f}}}")
        mac.append(f"\\newcommand{{\\SensMinPeak{K[b]}}}{{{min(pk[b]):.2f}}}")
        mac.append(f"\\newcommand{{\\SensMinMae{K[b]}}}{{{min(per[b]):.2f}}}")
        mac.append(f"\\newcommand{{\\SensMaxMae{K[b]}}}{{{max(per[b]):.2f}}}")
    lo_aware = [x for b in ("PI_FF", "FF_obs", "MPC_persist") for x in per[b]]
    mac.append(f"\\newcommand{{\\SensWorstAwareErr}}{{{max(lo_aware):.2f}}}")
    mac.append(f"\\newcommand{{\\SensBestPIErr}}{{{min(per['PI_tuned']):.2f}}}")
    kp = mv(G["PI_FF__kpx1p5"], "peak_ratio").mean(); kpe = mv(G["PI_FF__kpx1p5"], "mae_burst_pct").mean()
    mac.append(f"\\newcommand{{\\SensPIFFkpPeak}}{{{kp:.2f}}}")
    mac.append(f"\\newcommand{{\\SensPIFFkpErr}}{{{kpe:.2f}}}")
    for nm_k, name in (("FFO", "FF_obs__ff_alphax0p5"), ("MPCP", "MPC_persist__ewma_alphax0p5"), ("PIFF", "PI_FF__ff_alphax0p5")):
        b = {"FFO": "FF_obs", "MPCP": "MPC_persist", "PIFF": "PI_FF"}[nm_k]
        mac.append(f"\\newcommand{{\\SensSmooth{nm_k}}}{{{mv(G[name], 'mae_burst_pct').mean() / nm_[b][0]:.2f}}}")
    mac.append(f"\\newcommand{{\\plantMedErr}}{{{np.median(errs):.1f}}}")
    mac.append(f"\\newcommand{{\\plantMaxErr}}{{{max(errs):.1f}}}")
    open(os.path.join(a.out, "numbers.tex"), "w").write("\n".join(mac) + "\n")
    print(len(mac), "macros;", sorted(f for f in os.listdir(a.out) if f.endswith(".tex")))


if __name__ == "__main__":
    main()
