"""Equal-budget random search for EVERY controller family on the SIMULATED plant (calibrated on the
measured one), tuning on BURST + STATIONARY with tuning seeds, then testing on FRESH seeds and on an
UNSEEN scenario (low load). Direct tests + Holm. It validates the protocol; real tuning repeats it on the
cluster. Simulated results are NOT evidence for the paper.

    python experiments/tune_sim.py --budget 30 --tune-seeds 3 --test-seeds 15
"""
import argparse, os, sys, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from mpcrpo.config import Common
from mpcrpo.controllers import build_controller
from mpcrpo.plant import PlantParams
from mpcrpo.sim import simulate, STATIONARY, BURST, LOW_LOAD
from mpcrpo.metrics import run_metrics
from mpcrpo.stats import compare_groups


RANGES = {"kp": (0.02, 4.0, "lin"), "ki": (0.0, 1.5, "lin"), "lam": (1e-4, 1.0, "log"), "under_weight": (0.05, 1.0, "lin")}
SETS = {"ff_alpha": [1.0, 0.6, 0.3], "filter_alpha": [1.0, 0.5, 0.25, 0.1], "bias_alpha_pi": [0.0, 0.05, 0.1, 0.3, 0.6, 1.0],
        "horizon": [1, 3, 6, 10, 20], "gamma": [0.7, 0.85, 1.0], "ewma_alpha": [1.0, 0.6, 0.3, 0.15],
        "bias_alpha_mpc": [0.05, 0.1, 0.3, 0.6, 1.0], "window": [5, 10, 20, 30]}


def d_pi(r, ff):
    s = {"type": "pi", "kp": float(r.uniform(*RANGES["kp"][:2])), "ki": float(r.uniform(*RANGES["ki"][:2])),
         "antiwindup": str(r.choice(["clamp", "backcalc"])), "filter_alpha": float(r.choice(SETS["filter_alpha"]))}
    if ff:
        s.update(ff=True, bias_alpha=float(r.choice(SETS["bias_alpha_pi"])), ff_alpha=float(r.choice(SETS["ff_alpha"])))
    return s


def d_mpc(r, pred):
    lo, hi = np.log10(RANGES["lam"][0]), np.log10(RANGES["lam"][1])
    return {"type": "mpc", "predictor": pred, "horizon": int(r.choice(SETS["horizon"])),
            "gamma": float(r.choice(SETS["gamma"])), "lam": float(10 ** r.uniform(lo, hi)),
            "under_weight": float(r.uniform(*RANGES["under_weight"][:2])),
            "ewma_alpha": float(r.choice(SETS["ewma_alpha"])),
            "bias_alpha": float(r.choice(SETS["bias_alpha_mpc"])), "window": int(r.choice(SETS["window"]))}


def edge_flags(spec):
    """Parameters of the best spec lying within 5 % of the edge of the search range (continuous) or equal to
    an extreme of the set (discrete). An optimum on the edge means the range was too narrow."""
    out = []
    for k, (lo, hi, kind) in RANGES.items():
        if k in spec:
            v, a, b = spec[k], lo, hi
            if kind == "log":
                v, a, b = np.log10(v), np.log10(lo), np.log10(hi)
            z = (v - a) / (b - a)
            if z < 0.05 or z > 0.95:
                out.append(f"{k}={spec[k]:.3g} (bord)")
    discrete = {"ff_alpha": "ff_alpha", "filter_alpha": "filter_alpha", "horizon": "horizon", "gamma": "gamma", "ewma_alpha": "ewma_alpha",
                "window": "window"}
    for k, setname in discrete.items():
        if k in spec and spec[k] in (min(SETS[setname]), max(SETS[setname])) and not (k == "window" and spec.get("predictor") == "persistence"):
            out.append(f"{k}={spec[k]} (extreme du jeu)")
    if "bias_alpha" in spec:
        st = SETS["bias_alpha_mpc"] if spec["type"] == "mpc" else SETS["bias_alpha_pi"]
        if spec["bias_alpha"] in (min(st), max(st)):
            out.append(f"bias_alpha={spec['bias_alpha']} (extreme du jeu)")
    return out


def d_ffobs(r):
    """Minimal baseline: feedforward from the fast load estimate + model-bias observer, NO feedback, NO prediction."""
    return {"type": "pi", "ff": True, "kp": 0.0, "ki": 0.0, "antiwindup": "clamp", "filter_alpha": 1.0,
            "bias_alpha": float(r.choice([0.05, 0.1, 0.3, 0.6, 1.0])), "ff_alpha": float(r.choice(SETS["ff_alpha"]))}


FAMILIES = {"PI": lambda r: d_pi(r, False), "PI_FF": lambda r: d_pi(r, True), "FF_obs": d_ffobs,
            "MPC_persist": lambda r: d_mpc(r, "persistence"), "MPC_ma": lambda r: d_mpc(r, "ma"),
            "MPC_arima": lambda r: d_mpc(r, "arima")}


STRESS = PlantParams(L_lo_s=0.004, L_hi_s=0.012, timing_jitter_s=0.012)   # + 1 tick of actuator delay


def evaluate(spec, C, pp, seeds, scns, delay=0):
    out = {s["name"]: {"mae": [], "mae_burst": [], "peak": [], "sync": []} for s in scns}
    for sd in seeds:
        for s in scns:
            m = run_metrics(simulate(build_controller(C, spec), C, pp, s, sd, delay_ticks=delay), C, s)
            o = out[s["name"]]
            o["mae"].append(m["mae_pct"]); o["sync"].append(m["sync_per_s"])
            if s.get("burst"):
                o["mae_burst"].append(m["mae_burst_pct"]); o["peak"].append(m["peak_ratio"])
    return out


def score(o):
    return 0.5 * np.mean(o["stationary"]["mae"]) + 0.5 * np.mean(o["burst"]["mae_burst"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=30); ap.add_argument("--tune-seeds", type=int, default=3)
    ap.add_argument("--test-seeds", type=int, default=15); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--duration", type=float, default=300.0)
    ap.add_argument("--only", nargs="+", default=None, help="tune only these families")
    ap.add_argument("--reuse", default=None, help="tuned_specs.json providing the other families (same seeds/plants)")
    a = ap.parse_args()
    C, pp = Common(duration_s=a.duration), PlantParams()
    tune_seeds = list(range(1000, 1000 + a.tune_seeds))
    test_seeds = list(range(5000, 5000 + a.test_seeds))        # disjoint from tuning seeds
    best, flags, t0 = {}, {}, time.time()
    if a.reuse:
        prev = json.load(open(a.reuse))
        best, flags = dict(prev["specs"]), dict(prev.get("edge_flags", {}))
    for fam, draw in FAMILIES.items():
        if a.only and fam not in a.only:
            continue
        rng = np.random.default_rng(a.seed)
        cands = [draw(rng) for _ in range(a.budget)]
        # robust tuning for EVERY family: half nominal plant, half stress plant (slower sync, more jitter, 1-tick delay)
        scored = sorted(((0.5 * score(evaluate(c, C, pp, tune_seeds, [STATIONARY, BURST]))
                          + 0.5 * score(evaluate(c, C, STRESS, tune_seeds, [STATIONARY, BURST], delay=1)), c)
                         for c in cands), key=lambda x: x[0])
        best[fam] = scored[0][1]
        flags[fam] = edge_flags(scored[0][1])
        print(f"{fam:12s} best tuning score {scored[0][0]:6.2f}  {json.dumps(scored[0][1])}", flush=True)
        if flags[fam]:
            print(f"   ATTENTION optimum au bord de l'espace de recherche : {', '.join(flags[fam])}", flush=True)
    print(f"(tuning took {time.time() - t0:.0f} s)")
    with open("tuned_specs.json", "w") as f:
        json.dump({"budget": a.budget, "tune_seeds": tune_seeds, "plant": "simulated (calibrated on steps 2 and 3b)",
                   "specs": best, "edge_flags": flags}, f, indent=1)
    res = {fam: evaluate(spec, C, pp, test_seeds, [STATIONARY, BURST, LOW_LOAD]) for fam, spec in best.items()}
    res_s = {fam: evaluate(spec, C, STRESS, test_seeds, [STATIONARY, BURST], delay=1) for fam, spec in best.items()}
    summary = {fam: {"nominal": {sc: {m: float(np.mean(v)) for m, v in res[fam][sc].items() if v} for sc in res[fam]},
                     "stress": {sc: {m: float(np.mean(v)) for m, v in res_s[fam][sc].items() if v} for sc in res_s[fam]}}
               for fam in res}
    with open("tuned_specs.json") as f:
        td = json.load(f)
    td["test_summary"] = summary
    with open("tuned_specs.json", "w") as f:
        json.dump(td, f, indent=1)
    for tag, R_, scn, metric in (("nominal", res, "stationary", "mae"), ("nominal", res, "burst", "mae_burst"),
                                 ("nominal", res, "burst", "peak"), ("nominal", res, "lowload", "mae"),
                                 ("STRESS", res_s, "burst", "mae_burst"), ("STRESS", res_s, "burst", "peak")):
        print(f"\n[{tag} | {scn} / {metric}] mean over {a.test_seeds} fresh seeds")
        for fam in R_:
            print(f"  {fam:12s} {np.mean(R_[fam][scn][metric]):7.2f}   (sync/s {np.mean(R_[fam][scn]['sync']):.2f})")
        rows = compare_groups({f: R_[f][scn][metric] for f in R_})
        sig = [r for r in rows if r["p_mwu_holm"] < 0.05]
        print(f"  pairs with Holm p<0.05: {len(sig)}/{len(rows)}")
        for r in sorted(rows, key=lambda r: r["p_mwu_holm"])[:4]:
            print(f"    {r['A']:11s} vs {r['B']:11s} diff={r['diff']:+7.2f} [{r['ci_lo']:+.2f},{r['ci_hi']:+.2f}] "
                  f"p_holm={r['p_mwu_holm']:.3g} cliff={r['cliffs_delta']:+.2f}")
    print("\nNOTE: simulated plant (calibrated on step-2 data). Tests the protocol, not the paper's claims.")
