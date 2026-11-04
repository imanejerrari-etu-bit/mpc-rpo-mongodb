"""Amendment 6 schedule (72 runs, ~6.8 h), ONE randomised interleaved design:
 block A (confirmation, periodic cell, no delay): FF_obs and MPC_arima, 12 new valid runs each, reps 9..20 (reps 1..8 are amendment 5, not reused);
 block B (operator baselines): Static (J = 100 ms), Threshold (rule-based) and a contemporaneous FF_obs, on `burst` and `periodic`, 8 runs each.
Every repetition group contains its runs in random order, 30 s apart.

    python experiments\\make_block_amend6.py --scn-specs tuned_specs_scn.json --base-specs tuned_specs_base.json --raw data\\raw --out schedule_amend6.csv
"""
import argparse, json, os, random, sys
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mpcrpo.schedule import write_schedule
from mpcrpo.sim import BURST, PERIODIC
from make_topup import existing

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scn-specs", required=True); ap.add_argument("--base-specs", required=True); ap.add_argument("--raw", nargs="+", required=True)
    ap.add_argument("--seed", type=int, default=2030); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    scn_sp, base = json.load(open(a.scn_specs))["specs"]["periodic"], json.load(open(a.base_specs))["specs"]
    have = existing(a.raw)
    used = {}                                                    # next free rep number per (scenario, controller)
    def nxt(scn, c, start=1):
        k = (scn, c)
        used[k] = max(used.get(k, 0), max(have.get(k, {0})), start - 1) + 1
        return used[k]
    scn_of = {"burst": BURST, "periodic": PERIODIC}
    groups = []
    for i in range(12):                                          # block A: 12 reps
        g = [("periodic", "FF_obs", scn_sp["FF_obs"], nxt("periodic", "FF_obs", 9)), ("periodic", "MPC_arima", scn_sp["MPC_arima"], nxt("periodic", "MPC_arima", 9))]
        groups.append(g)
    for i in range(8):                                           # block B: 8 reps, 6 combos
        groups[i] = groups[i] + [(cell, c, base[cell][c], nxt(cell, c, 21 if cell == "periodic" else 1)) for cell in ("burst", "periodic")
                                 for c in ("Static", "Threshold", "FF_obs")]
    rng, rows, order = random.Random(a.seed), [], 0
    for g in groups:
        rng.shuffle(g)
        for cell, c, spec, rep in g:
            order += 1
            scn = dict(scn_of[cell]); scn["name"] = cell
            rows.append({"order": order, "run_uid": f"mongodb_{cell}_{c}_rep{rep:02d}", "engine": "mongodb", "scenario": cell, "controller": c,
                         "rep": rep, "cooldown_s": 30, "spec": json.dumps(spec, sort_keys=True), "scn": json.dumps(scn, sort_keys=True),
                         "seed": rng.randrange(10 ** 9)})
    uids = [r["run_uid"] for r in rows]
    assert len(set(uids)) == len(uids)
    write_schedule(rows, a.out)
    print(f"{len(rows)} runs -> {a.out}  (~{len(rows) * 5.7 / 60:.1f} h)")
    print("derniere repetition par (scenario, controleur) : " + ", ".join(f"{k[0]}/{k[1]} -> rep{v:02d}" for k, v in sorted(used.items())))
