# Analyse (24 runs valides)


## stationary : moyenne (sd) [n]

| controleur | n | mae_pct | chatter | sync_per_s |
|---|---|---|---|---|

## burst : moyenne (sd) [n]

| controleur | n | mae_burst_pct | peak_ratio | mae_pct | recovery_s | sync_per_s | chatter | max_sync_gap_s |
|---|---|---|---|---|---|---|---|---|
| PI_tuned | 6 | 9.36 (0.27) | 1.86 (0.11) | 4.96 (0.21) | 10.50 (0.00) | 8.54 (0.01) | 0.04 (0.00) | 0.00 (0.00) |
| PI_FF | 6 | 1.52 (0.06) | 1.38 (0.06) | 1.60 (0.07) | 1.00 (0.00) | 8.70 (0.00) | 0.05 (0.00) | 0.00 (0.00) |
| FF_obs | 6 | 1.45 (0.32) | 1.37 (0.03) | 1.26 (0.09) | 1.67 (0.52) | 8.63 (0.01) | 0.02 (0.01) | 0.00 (0.00) |
| MPC_persist | 6 | 1.33 (0.12) | 1.37 (0.03) | 1.20 (0.09) | 1.58 (0.49) | 8.63 (0.01) | 0.02 (0.00) | 0.00 (0.00) |

## lowload : moyenne (sd) [n]

| controleur | n | mae_pct | mae_burst_pct | sat_frac | recovery_s |
|---|---|---|---|---|---|

## Contrastes pre-specifies (criteres primaires, rafale) : Mann-Whitney, Holm sur 10 tests

| metrique | A vs B | nA/nB | diff [IC95 bootstrap] | Cliff | p brut | p Holm |
|---|---|---|---|---|---|---|
| mae_burst_pct | PI_tuned vs PI_FF | 6/6 | +7.84 [+7.65, +8.04] | +1.00 | 0.00216 | 0.0216 |
| mae_burst_pct | PI_FF vs FF_obs | 6/6 | +0.07 [-0.19, +0.25] | +0.61 | 0.0931 | 0.465 |
| mae_burst_pct | FF_obs vs MPC_persist | 6/6 | +0.13 [-0.08, +0.41] | +0.17 | 0.699 | 1 |
| mae_burst_pct | PI_FF vs MPC_persist | 6/6 | +0.20 [+0.10, +0.30] | +0.89 | 0.00866 | 0.0519 |
| mae_burst_pct | PI_tuned vs MPC_persist | 6/6 | +8.04 [+7.82, +8.26] | +1.00 | 0.00216 | 0.0216 |
| peak_ratio | PI_tuned vs PI_FF | 6/6 | +0.48 [+0.39, +0.58] | +1.00 | 0.0047 | 0.0376 |
| peak_ratio | PI_FF vs FF_obs | 6/6 | +0.01 [-0.04, +0.05] | +0.44 | 0.224 | 0.896 |
| peak_ratio | FF_obs vs MPC_persist | 6/6 | +0.00 [-0.03, +0.03] | +0.06 | 0.934 | 1 |
| peak_ratio | PI_FF vs MPC_persist | 6/6 | +0.01 [-0.04, +0.05] | +0.39 | 0.292 | 0.896 |
| peak_ratio | PI_tuned vs MPC_persist | 6/6 | +0.50 [+0.41, +0.58] | +1.00 | 0.00492 | 0.0376 |

Note : avec n petit, le plus petit p de Mann-Whitney possible est limite par n (ici p minimal observe 0.00216) ; pour n=3 vs 3 il vaut 0,1 : aucun contraste ne peut passer Holm.

## Equivalence (TOST, IC90 de Welch dans +/- marge)

| metrique | A vs B | marge | diff [IC90] | equivalents ? |
|---|---|---|---|---|
| mae_burst_pct | FF_obs vs MPC_persist | 0.7 | +0.13 [-0.14, +0.39] | oui |
| peak_ratio | FF_obs vs MPC_persist | 0.1 | +0.00 [-0.03, +0.03] | oui |
