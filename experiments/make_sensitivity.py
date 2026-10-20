"""Sensitivity analysis schedule (answers Reviewer 1: 'parameters of PI and MPC are never varied').
One-at-a-time perturbations (x0.5 / x1.5, clipped to valid ranges) of every continuous parameter of
PI_tuned, PI_FF, FF_obs and MPC_persist, plus a change of the target V* (2048 and 8192 bytes), burst scenario,
3 repetitions each, plus 3 CONCURRENT nominal runs per controller (drift control). Randomised blocks.

    python experiments/make_sensitivity.py --specs tuned_specs.json --out schedule_sensitivity.csv
"""
import argparse, json, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mpcrpo.schedule import write_schedule
from mpcrpo.sim import BURST
from make_schedule import controllers_from_tuned

PARAMS = {"PI_tuned": ["kp", "ki"], "PI_FF": ["kp", "ki", "ff_alpha"], "FF_obs": ["bias_alpha", "ff_alpha"],
          "MPC_persist": ["lam", "under_weight", "bias_alpha", "ewma_alpha"]}
ALPHAS = {"bias_alpha", "ff_alpha", "ewma_alpha"}          # in (0, 1] : only x0.5 is possible when the value is 1
VSTARS = {"PI_FF": [2048, 8192], "FF_obs": [2048, 8192], "MPC_persist": [2048, 8192]}


def fmt(x):
    return f"{x:g}".replace(".", "p")


def variants(ctl):
    out = []                                                # (name, base, spec, common_override)
    for base, params in PARAMS.items():
        for k in params:
            for f in (0.5, 1.5):
                v = ctl[base][k] * f
                if k in ALPHAS and v > 1.0:
                    continue
                if k == "bias_alpha" and ctl[base][k] == 0.0:
                    continue
                spec = dict(ctl[base]); spec[k] = v
                out.append((f"{base}__{k}x{fmt(f)}", base, spec, {}))
    for base, vs in VSTARS.items():
        for v in vs:
            out.append((f"{base}__V{v}", base, dict(ctl[base]), {"v_star_B": float(v)}))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--specs", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=3); ap.add_argument("--seed", type=int, default=2028)
    a = ap.parse_args()
    ctl = controllers_from_tuned(a.specs)
    items = variants(ctl)
    for base in PARAMS:                                    # concurrent nominal controls (reps 21..)
        items.append((base, base, dict(ctl[base]), {}))
    rng = random.Random(a.seed)
    rows, order = [], 0
    for rep in range(1, a.reps + 1):
        block = list(items)
        rng.shuffle(block)
        for name, base, spec, over in block:
            order += 1
            rn = rep + 20 if name in PARAMS else rep        # nominal controls use rep 21.. (no collision with the campaign)
            rows.append({"order": order, "run_uid": f"mongodb_burst_{name}_rep{rn:02d}", "engine": "mongodb",
                         "scenario": "burst", "controller": name, "rep": rn, "cooldown_s": 30,
                         "spec": json.dumps(spec, sort_keys=True), "scn": json.dumps(BURST, sort_keys=True),
                         "common": json.dumps(over, sort_keys=True), "seed": rng.randrange(10 ** 9)})
    write_schedule(rows, a.out)
    print(f"{len(items)} variantes/controles x {a.reps} = {len(rows)} runs -> {a.out}  (~{len(rows) * 5.7 / 60:.1f} h)")
    print("exemples :", ", ".join(n for n, *_ in items[:6]))
