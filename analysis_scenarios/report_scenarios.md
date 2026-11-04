# Amendement 5 : analyse (96 runs valides sur 96)


## rampe : moyenne (sd)

| controleur | n | erreur de perturbation (%) | pic (xV*) | recup (s) | erreur stationnaire (%) | sync/s | arret sync max (s) |
|---|---|---|---|---|---|---|---|
| PI_tuned | 8 | 4.93 (0.21) | 1.20 (0.10) | 1.00 (0.00) | 3.56 (0.08) | 8.61 (0.00) | 0.00 (0.00) |
| FF_obs | 8 | 1.49 (0.73) | 1.13 (0.15) | 4.31 (9.37) | 1.47 (0.41) | 8.63 (0.02) | 0.06 (0.18) |
| MPC_persist | 8 | 1.16 (0.10) | 1.07 (0.02) | 1.00 (0.00) | 1.24 (0.11) | 8.63 (0.01) | 0.00 (0.00) |
| MPC_arima | 8 | 1.20 (0.23) | 1.08 (0.02) | 1.00 (0.00) | 1.31 (0.09) | 8.63 (0.01) | 0.00 (0.00) |

## periodique : moyenne (sd)

| controleur | n | erreur de perturbation (%) | pic (xV*) | recup (s) | erreur stationnaire (%) | sync/s | arret sync max (s) |
|---|---|---|---|---|---|---|---|
| PI_tuned | 8 | 10.06 (0.11) | 1.30 (0.04) | 46.31 (6.65) | 6.57 (0.10) | 8.52 (0.00) | 0.00 (0.00) |
| FF_obs | 8 | 2.47 (0.36) | 1.15 (0.04) | 1.00 (0.00) | 1.94 (0.23) | 8.64 (0.01) | 0.00 (0.00) |
| MPC_persist | 8 | 2.21 (0.22) | 1.13 (0.03) | 1.00 (0.00) | 1.80 (0.20) | 8.64 (0.01) | 0.06 (0.18) |
| MPC_arima | 8 | 1.95 (0.18) | 1.12 (0.04) | 1.00 (0.00) | 1.64 (0.18) | 8.66 (0.01) | 0.00 (0.00) |

## periodique + retard 1 s : moyenne (sd)

| controleur | n | erreur de perturbation (%) | pic (xV*) | recup (s) | erreur stationnaire (%) | sync/s | arret sync max (s) |
|---|---|---|---|---|---|---|---|
| PI_tuned | 8 | 17.17 (0.17) | 1.67 (0.05) | 125.56 (0.32) | 10.95 (0.25) | 8.62 (0.01) | 0.00 (0.00) |
| FF_obs | 8 | 6.25 (0.16) | 1.31 (0.03) | 1.00 (0.00) | 4.10 (0.11) | 8.78 (0.01) | 0.00 (0.00) |
| MPC_persist | 8 | 6.48 (1.05) | 1.35 (0.17) | 7.19 (17.50) | 4.30 (0.52) | 8.79 (0.02) | 0.19 (0.37) |
| MPC_arima | 8 | 5.64 (1.01) | 1.41 (0.27) | 7.00 (16.97) | 3.88 (0.61) | 8.86 (0.04) | 0.00 (0.00) |

## Contrastes (A - B, IC bootstrap 95 %, Holm sur 18 tests declares)

| cellule | critere | A - B | diff | IC95 | Cliff d | p (MWU) | p Holm | equivalent (marge) |
|---|---|---|---|---|---|---|---|---|
| rampe | mae_burst_pct | FF_obs - MPC_persist | 0.33 | [-0.04, 0.88] | 0.41 | 0.19 | 1 | non (0.7) |
| rampe | mae_burst_pct | FF_obs - MPC_arima | 0.29 | [-0.12, 0.86] | 0.22 | 0.51 | 1 | non (0.7) |
| rampe | mae_burst_pct | MPC_persist - MPC_arima | -0.04 | [-0.20, 0.12] | -0.09 | 0.8 | 1 | oui (0.7) |
| rampe | mae_burst_pct | PI_tuned - FF_obs (rappel) | 3.45 | [2.88, 3.86] | 1.00 | 0.00016 | nan | non (0.7) |
| rampe | peak_ratio | FF_obs - MPC_persist | 0.06 | [-0.01, 0.17] | 0.30 | 0.34 | 1 | non (0.1) |
| rampe | peak_ratio | FF_obs - MPC_arima | 0.04 | [-0.02, 0.15] | 0.08 | 0.83 | 1 | non (0.1) |
| rampe | peak_ratio | MPC_persist - MPC_arima | -0.01 | [-0.03, 0.01] | -0.52 | 0.091 | 1 | oui (0.1) |
| rampe | peak_ratio | PI_tuned - FF_obs (rappel) | 0.07 | [-0.06, 0.18] | 0.75 | 0.013 | nan | non (0.1) |
| periodique | mae_burst_pct | FF_obs - MPC_persist | 0.26 | [-0.02, 0.54] | 0.41 | 0.19 | 1 | oui (0.7) |
| periodique | mae_burst_pct | FF_obs - MPC_arima | 0.53 | [0.26, 0.79] | 0.81 | 0.0047 | 0.084 | non (0.7) |
| periodique | mae_burst_pct | MPC_persist - MPC_arima | 0.27 | [0.09, 0.46] | 0.62 | 0.038 | 0.57 | oui (0.7) |
| periodique | mae_burst_pct | PI_tuned - FF_obs (rappel) | 7.59 | [7.34, 7.83] | 1.00 | 0.00016 | nan | non (0.7) |
| periodique | peak_ratio | FF_obs - MPC_persist | 0.02 | [-0.01, 0.05] | 0.36 | 0.25 | 1 | oui (0.1) |
| periodique | peak_ratio | FF_obs - MPC_arima | 0.03 | [-0.01, 0.07] | 0.53 | 0.083 | 1 | oui (0.1) |
| periodique | peak_ratio | MPC_persist - MPC_arima | 0.01 | [-0.02, 0.04] | 0.33 | 0.29 | 1 | oui (0.1) |
| periodique | peak_ratio | PI_tuned - FF_obs (rappel) | 0.14 | [0.11, 0.17] | 1.00 | 0.00091 | nan | non (0.1) |
| periodique + retard 1 s | mae_burst_pct | FF_obs - MPC_persist | -0.23 | [-1.01, 0.24] | 0.38 | 0.23 | 1 | non (0.7) |
| periodique + retard 1 s | mae_burst_pct | FF_obs - MPC_arima | 0.61 | [-0.13, 1.15] | 0.75 | 0.01 | 0.17 | non (0.7) |
| periodique + retard 1 s | mae_burst_pct | MPC_persist - MPC_arima | 0.84 | [-0.10, 1.82] | 0.78 | 0.007 | 0.12 | non (0.7) |
| periodique + retard 1 s | mae_burst_pct | PI_tuned - FF_obs (rappel) | 10.92 | [10.78, 11.08] | 1.00 | 0.00016 | nan | non (0.7) |
| periodique + retard 1 s | peak_ratio | FF_obs - MPC_persist | -0.05 | [-0.17, 0.03] | 0.03 | 0.96 | 1 | non (0.1) |
| periodique + retard 1 s | peak_ratio | FF_obs - MPC_arima | -0.10 | [-0.30, 0.02] | -0.20 | 0.53 | 1 | non (0.1) |
| periodique + retard 1 s | peak_ratio | MPC_persist - MPC_arima | -0.05 | [-0.29, 0.14] | -0.28 | 0.37 | 1 | non (0.1) |
| periodique + retard 1 s | peak_ratio | PI_tuned - FF_obs (rappel) | 0.36 | [0.32, 0.40] | 1.00 | 0.00092 | nan | non (0.1) |

## Controles de coherence (derive avec l'ordre des runs, erreur de perturbation)

- periodic / FF_obs : Spearman rho = 0.10 (p = 0.82)
- periodic / MPC_arima : Spearman rho = 0.17 (p = 0.69)
- periodic / MPC_persist : Spearman rho = -0.48 (p = 0.23)
- periodic / PI_tuned : Spearman rho = 0.38 (p = 0.35)
- periodicd1 / FF_obs : Spearman rho = -0.19 (p = 0.65)
- periodicd1 / MPC_arima : Spearman rho = 0.05 (p = 0.91)
- periodicd1 / MPC_persist : Spearman rho = 0.48 (p = 0.23)
- periodicd1 / PI_tuned : Spearman rho = -0.12 (p = 0.78)
- ramp / FF_obs : Spearman rho = -0.12 (p = 0.78)
- ramp / MPC_arima : Spearman rho = -0.24 (p = 0.57)
- ramp / MPC_persist : Spearman rho = 0.07 (p = 0.87)
- ramp / PI_tuned : Spearman rho = -0.12 (p = 0.78)
