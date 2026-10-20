"""Top-up schedule: brings every (scenario, controller) cell to its TARGET number of valid runs.
Existing valid runs (pilot included, same protocol, same tuned specs -> same config_hash) are counted and
never repeated. New runs get the next repetition numbers; each block (one repetition index) is randomised.

    python experiments/make_topup.py --raw data/raw --specs tuned_specs.json --out schedule_topup.csv
"""
import argparse, csv, glob, json, os, random, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mpcrpo.schedule import write_schedule
from mpcrpo.sim import STATIONARY, BURST, LOW_LOAD
from make_schedule import controllers_from_tuned

SCN = {"stationary": STATIONARY, "burst": BURST, "lowload": LOW_LOAD}
# Amendment 1 (after the pilot): total valid runs wanted per cell (pilot runs count)
TARGETS = {
    "burst":      {"PI_default": 3, "PI_tuned": 6, "PI_FF": 15, "FF_obs": 15, "MPC_persist": 15, "MPC_ma": 10, "MPC_arima": 10},
    "lowload":    {"PI_default": 3, "PI_tuned": 6, "PI_FF": 6, "FF_obs": 6, "MPC_persist": 6, "MPC_ma": 6, "MPC_arima": 6},
    "stationary": {"PI_default": 3, "PI_tuned": 3, "PI_FF": 3, "FF_obs": 3, "MPC_persist": 3, "MPC_ma": 3, "MPC_arima": 3},
}


def existing(raw_dirs):
    have = collections.defaultdict(set)
    for d in raw_dirs:
        for f in glob.glob(os.path.join(d, "*.json")):
            if ".INVALID_" in f:
                continue
            j = json.load(open(f))
            if j.get("complete") and j.get("valid", True):
                p = j["run_uid"].split("_")
                have[(p[1], "_".join(p[2:-1]))].add(int(p[-1][3:]))
    return have


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", nargs="+", required=True); ap.add_argument("--specs", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--seed", type=int, default=2027)
    ap.add_argument("--targets", default=None, help="optional JSON file overriding TARGETS")
    a = ap.parse_args()
    targets = json.load(open(a.targets)) if a.targets else TARGETS
    ctl = controllers_from_tuned(a.specs)
    have = existing(a.raw)
    rng = random.Random(a.seed)
    need = {}
    for scn, cells in targets.items():
        for c, n in cells.items():
            k = len(have.get((scn, c), ()))
            if n > k:
                nxt = max(have.get((scn, c), {0})) + 1
                need[(scn, c)] = list(range(nxt, nxt + n - k))
    rows, order = [], 0
    for scn in targets:
        reps = sorted({r for (s, c), rs in need.items() if s == scn for r in rs})
        for rep in reps:
            block = [c for (s, c), rs in need.items() if s == scn and rep in rs]
            rng.shuffle(block)
            for c in block:
                order += 1
                rows.append({"order": order, "run_uid": f"mongodb_{scn}_{c}_rep{rep:02d}", "engine": "mongodb",
                             "scenario": scn, "controller": c, "rep": rep, "cooldown_s": 30,
                             "spec": json.dumps(ctl[c], sort_keys=True), "scn": json.dumps(SCN[scn], sort_keys=True),
                             "seed": rng.randrange(10 ** 9)})
    if not rows:
        sys.exit("Rien a faire : toutes les cellules ont atteint leur cible.")
    # blocks of different scenarios are run sequentially; interleave scenarios coarsely by keeping order as built
    write_schedule(rows, a.out)
    by = collections.Counter(r["scenario"] for r in rows)
    print(f"{len(rows)} runs -> {a.out} : {dict(by)}  (~{len(rows) * 5.7 / 60:.1f} h)")
