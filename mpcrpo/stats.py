"""Direct two-sample tests (not 'non-overlapping CIs'), effect sizes, Holm correction."""
import itertools
import numpy as np
from scipy import stats as sps


def bootstrap_diff_ci(a, b, n=10000, seed=0):
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = np.array([rng.choice(a, a.size).mean() - rng.choice(b, b.size).mean() for _ in range(n)])
    return float(a.mean() - b.mean()), *np.percentile(d, [2.5, 97.5])


def perm_test(a, b, n=20000, seed=0):
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a, float), np.asarray(b, float)
    obs = abs(a.mean() - b.mean())
    pool = np.concatenate([a, b])
    cnt = 0
    for _ in range(n):
        rng.shuffle(pool)
        cnt += abs(pool[:a.size].mean() - pool[a.size:].mean()) >= obs
    return (cnt + 1) / (n + 1)


def cliffs_delta(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    gt = sum((x > b).sum() for x in a)
    lt = sum((x < b).sum() for x in a)
    return float((gt - lt) / (a.size * b.size))


def holm(pvals):
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    m = len(p)
    adj, run = np.empty(m), 0.0
    for rank, idx in enumerate(order):
        run = max(run, (m - rank) * p[idx])
        adj[idx] = min(1.0, run)
    return adj


def compare_groups(groups: dict, pairs=None):
    names = list(groups)
    pairs = pairs or list(itertools.combinations(names, 2))
    rows = []
    for x, y in pairs:
        a, b = groups[x], groups[y]
        mw = sps.mannwhitneyu(a, b, alternative="two-sided").pvalue
        diff, lo, hi = bootstrap_diff_ci(a, b)
        rows.append({"A": x, "B": y, "meanA": float(np.mean(a)), "meanB": float(np.mean(b)), "diff": diff,
                     "ci_lo": lo, "ci_hi": hi, "p_mwu": float(mw), "p_perm": perm_test(a, b),
                     "cliffs_delta": cliffs_delta(a, b)})
    adj = holm([r["p_mwu"] for r in rows])
    for r, q in zip(rows, adj):
        r["p_mwu_holm"] = float(q)
    return rows
