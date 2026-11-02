"""Schedule of the PI-on-fast-V block (amendment 4).

One contemporaneous, randomised, interleaved block on the BURST scenario: PI_fast (new) against its two
references PI_tuned (feedback only, windowed V) and FF_obs (feedforward + observer). Each block repetition runs the
three controllers once in random order, so drift of the cluster cannot masquerade as an effect. Repetition numbers
continue after the valid runs already in data/raw (existing runs are never repeated or overwritten).

    python experiments\\make_block_pifast.py --raw data\\raw --specs tuned_specs.json --n 10 --out schedule_pifast.csv
"""
import argparse, json, os, random, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mpcrpo.schedule import write_schedule
from mpcrpo.sim import BURST
from make_schedule import controllers_from_tuned
from make_topup import existing

CTRL = ("PI_fast", "PI_tuned", "FF_obs")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", nargs="+", required=True); ap.add_argument("--specs", required=True)
    ap.add_argument("--n", type=int, default=10, help="valid runs per controller in this block")
    ap.add_argument("--seed", type=int, default=2028); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ctl = controllers_from_tuned(a.specs)
    if "PI_fast" not in ctl:
        sys.exit("PI_fast absent de tuned_specs.json : lancez d'abord tune_sim.py --only PI_fast --reuse ...")
    have = existing(a.raw)
    nxt = {c: max(have.get(("burst", c), {0})) + 1 for c in CTRL}
    rng = random.Random(a.seed)
    rows, order = [], 0
    for k in range(a.n):
        block = list(CTRL); rng.shuffle(block)
        for c in block:
            order += 1
            rows.append({"order": order, "run_uid": f"mongodb_burst_{c}_rep{nxt[c] + k:02d}", "engine": "mongodb",
                         "scenario": "burst", "controller": c, "rep": nxt[c] + k, "cooldown_s": 30,
                         "spec": json.dumps(ctl[c], sort_keys=True), "scn": json.dumps(BURST, sort_keys=True),
                         "seed": rng.randrange(10 ** 9)})
    write_schedule(rows, a.out)
    print(f"{len(rows)} runs -> {a.out}  (~{len(rows) * 5.7 / 60:.1f} h) ; premiers rep : {nxt}")
