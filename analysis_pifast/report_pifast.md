# Bloc PI_fast (amendement 4) : analyse contemporaine

Runs valides du planning : 30 / 30 ; par controleur : PI_fast n=10, PI_tuned n=10, FF_obs n=10


## Moyennes (sd)

| controleur | mae_burst_pct | peak_ratio | recovery_s | mae_pct | chatter | sync_per_s | max_sync_gap_s |
|---|---|---|---|---|---|---|---|
| PI_tuned | 9.62 (0.22) | 1.87 (0.07) | 11.00 (0.00) | 4.88 (0.16) | 0.04 (0.00) | 8.53 (0.01) | 0.00 (0.00) |
| PI_fast | 5.01 (0.75) | 1.62 (0.04) | 8.75 (0.86) | 2.60 (0.48) | 0.01 (0.00) | 8.58 (0.01) | 0.05 (0.16) |
| FF_obs | 1.93 (0.43) | 1.41 (0.04) | 2.00 (0.41) | 1.42 (0.25) | 0.03 (0.01) | 8.62 (0.01) | 0.10 (0.32) |

## Contrastes (difference de moyennes A - B, IC bootstrap 95 %, Holm sur les 4 contrastes declares)

| critere | A - B | diff | IC95 | Cliff d | p (MWU) | p Holm | equivalent (marge) |
|---|---|---|---|---|---|---|---|
| mae_burst_pct | PI_fast - PI_tuned | -4.61 | [-5.00, -4.09] | -1.00 | 0.00018 | 0.00071 | non (0.7) |
| mae_burst_pct | PI_fast - FF_obs | 3.09 | [2.62, 3.62] | 1.00 | 0.00018 | 0.00071 | non (0.7) |
| mae_burst_pct | PI_tuned - FF_obs (rappel) | 7.70 | [7.39, 7.96] | 1.00 | 0.00018 | nan | non (0.7) |
| peak_ratio | PI_fast - PI_tuned | -0.25 | [-0.29, -0.20] | -1.00 | 0.00018 | 0.00071 | non (0.1) |
| peak_ratio | PI_fast - FF_obs | 0.21 | [0.18, 0.24] | 1.00 | 0.00018 | 0.00071 | non (0.1) |
| peak_ratio | PI_tuned - FF_obs (rappel) | 0.45 | [0.41, 0.50] | 1.00 | 0.00018 | nan | non (0.1) |

## Part de l'ecart recuperee par le signal rapide : (PI_tuned - PI_fast) / (PI_tuned - FF_obs)

- mae_burst_pct : 60 % (IC95 bootstrap 53 a 66 %)
- peak_ratio : 55 % (IC95 bootstrap 44 a 67 %)

## Controles de coherence

- PI_fast : derive de l'erreur de rafale avec la repetition, Spearman rho = 0.82 (p = 0.0038) ; arret de sync max = 0.5 s
- PI_tuned : derive de l'erreur de rafale avec la repetition, Spearman rho = 0.55 (p = 0.098) ; arret de sync max = 0.0 s
- FF_obs : derive de l'erreur de rafale avec la repetition, Spearman rho = 0.15 (p = 0.68) ; arret de sync max = 1.0 s
