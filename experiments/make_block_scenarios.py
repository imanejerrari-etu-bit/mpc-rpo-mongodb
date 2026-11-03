"""Amendment 5 schedule: 3 cells (ramp; periodic; periodic with 1 s actuation delay) x 4 controllers x n valid runs, ONE randomised interleaved
design: every repetition contains all 12 (cell, controller) combinations in random order, 30 s apart.

    python experiments\\make_block_scenarios.py --specs tuned_specs_scn.json --n 8 --out schedule_scenarios.csv
"""
import argparse, json, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mpcrpo.schedule import write_schedule

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--specs", required=True); ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--seed", type=int, default=2029); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    sp = json.load(open(a.specs))
    rng, rows, order = random.Random(a.seed), [], 0
    combos = [(cell, c) for cell in sp["cells"] for c in sp["specs"][cell]]
    for rep in range(1, a.n + 1):
        rng.shuffle(combos)
        for cell, c in combos:
            order += 1
            scn = dict(sp["cells"][cell]["scenario"]); scn["name"] = cell
            scn["act_delay_s"] = sp["cells"][cell]["delay_ticks"] * 0.5
            rows.append({"order": order, "run_uid": f"mongodb_{cell}_{c}_rep{rep:02d}", "engine": "mongodb", "scenario": cell, "controller": c,
                         "rep": rep, "cooldown_s": 30, "spec": json.dumps(sp["specs"][cell][c], sort_keys=True),
                         "scn": json.dumps(scn, sort_keys=True), "seed": rng.randrange(10 ** 9)})
    write_schedule(rows, a.out)
    print(f"{len(rows)} runs -> {a.out}  (~{len(rows) * 5.7 / 60:.1f} h)")
