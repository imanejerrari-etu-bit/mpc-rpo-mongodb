"""Randomised block design: in every (engine, scenario, repetition) block each controller runs once,
in random order -> controllers are interleaved in time, so cluster drift cannot masquerade as an effect."""
import csv, json, random


def make_schedule(engines, scenarios, controllers: dict, n_reps, seed: int, cooldown_s: int = 30):
    """n_reps: int, or dict scenario_name -> repetitions."""
    rng = random.Random(seed)
    rows, order = [], 0
    for eng in engines:
        for scn in scenarios:
            n = n_reps[scn['name']] if isinstance(n_reps, dict) else n_reps
            for rep in range(1, n + 1):
                names = list(controllers)
                rng.shuffle(names)
                for name in names:
                    order += 1
                    rows.append({"order": order, "run_uid": f"{eng['name']}_{scn['name']}_{name}_rep{rep:02d}",
                                 "engine": eng["name"], "scenario": scn["name"], "controller": name, "rep": rep,
                                 "cooldown_s": cooldown_s, "spec": json.dumps(controllers[name], sort_keys=True),
                                 "scn": json.dumps(scn, sort_keys=True), "seed": rng.randrange(10 ** 9)})
    return rows


def write_schedule(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def read_schedule(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
