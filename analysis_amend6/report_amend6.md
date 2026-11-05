# Amendement 6 : analyse (72 runs valides sur 72)


## Bloc A : confirmation sur le periodique (reps 9 a 20)

| controleur | n | erreur de perturbation (%) | pic (xV*) | recup (s) | erreur stationnaire (%) | sync/s |
|---|---|---|---|---|---|---|
| FF_obs | 12 | 2.26 (0.15) | 1.13 (0.02) | 1.00 (0.00) | 1.81 (0.12) | 8.63 (0.01) |
| MPC_arima | 12 | 1.85 (0.28) | 1.13 (0.03) | 1.00 (0.00) | 1.74 (0.18) | 8.65 (0.02) |

Contraste declare MPC_arima - FF_obs : -0.40 points, IC95 bootstrap [-0.56, -0.21], delta de Cliff -0.83, p (Mann-Whitney, bilateral) = 0.000592, p permutation = 0.00035 -> CONFIRME (critere declare : p < 0,05 et MPC_arima plus bas)
Pic (descriptif) : -0.001 [-0.018, 0.016]

## Bloc B : baselines d'operateur (moyenne (sd))

| cellule | controleur | n | mae_burst_pct | peak_ratio | recovery_s | mae_pct | sync_per_s | max_sync_gap_s |
|---|---|---|---|---|---|---|---|---|
| burst | Static | 8 | 89.38 (1.72) | 2.24 (0.04) | nan (nan) | 60.44 (0.16) | 9.39 (0.12) | 0.00 (0.00) |
| burst | Threshold | 8 | 18.28 (1.79) | 2.16 (0.05) | 31.12 (37.38) | 11.32 (0.75) | 8.51 (0.09) | 0.00 (0.00) |
| burst | FF_obs | 8 | 1.76 (0.30) | 1.35 (0.03) | 1.50 (0.46) | 1.42 (0.16) | 8.62 (0.01) | 0.00 (0.00) |
| periodic | Static | 8 | 50.89 (0.80) | 2.24 (0.12) | nan (nan) | 49.11 (0.31) | 9.39 (0.09) | 0.00 (0.00) |
| periodic | Threshold | 8 | 24.09 (1.13) | 2.05 (0.07) | nan (nan) | 17.20 (1.74) | 10.00 (0.22) | 0.00 (0.00) |
| periodic | FF_obs | 8 | 2.52 (0.33) | 1.20 (0.12) | 1.00 (0.00) | 2.05 (0.21) | 8.62 (0.06) | 0.00 (0.00) |

### Contrastes (A - B, IC bootstrap 95 %, Holm sur 8 tests)

| cellule | critere | A - B | diff | IC95 | Cliff d | p (MWU) | p Holm |
|---|---|---|---|---|---|---|---|
| burst | mae_burst_pct | Static - FF_obs | 87.61 | [86.56, 88.80] | 1.00 | 0.00016 | 0.0012 |
| burst | mae_burst_pct | Threshold - FF_obs | 16.52 | [15.50, 17.80] | 1.00 | 0.00016 | 0.0012 |
| burst | peak_ratio | Static - FF_obs | 0.89 | [0.85, 0.92] | 1.00 | 0.0009 | 0.0036 |
| burst | peak_ratio | Threshold - FF_obs | 0.81 | [0.77, 0.85] | 1.00 | 0.00089 | 0.0036 |
| periodic | mae_burst_pct | Static - FF_obs | 48.38 | [47.82, 48.93] | 1.00 | 0.00016 | 0.0012 |
| periodic | mae_burst_pct | Threshold - FF_obs | 21.58 | [20.88, 22.39] | 1.00 | 0.00016 | 0.0012 |
| periodic | peak_ratio | Static - FF_obs | 1.04 | [0.93, 1.15] | 1.00 | 0.00091 | 0.0036 |
| periodic | peak_ratio | Threshold - FF_obs | 0.85 | [0.75, 0.94] | 1.00 | 0.00091 | 0.0036 |
