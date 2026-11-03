# Amendement n°5 : autres perturbations et retard d'actionnement (déclaré AVANT de lancer les runs)

Motif : la conclusion « prévoir n'aide pas » ne vaut que pour un échelon de charge avec un actionneur quasi instantané (limites x et xi du manuscrit).
Cet amendement teste (i) deux autres profils de charge, (ii) un retard d'actionnement, situation réaliste d'une boucle de gestion qui passe par un
opérateur ou une API. Un prédicteur n'a une chance de servir que sur une perturbation structurée ou avec un retard à compenser.

## Cellules (3)
- `ramp` : 400 -> 1600 -> 400 documents/s, triangle linéaire sur 120 s à partir de t = 100 s (60 s de montée, 60 s de descente). Sans retard.
- `periodic` : 400 + 600 (1 - cos(2 pi (t - 100) / 40)) documents/s, soit trois périodes de 40 s entre 400 et 1600 documents/s, de t = 100 s à 220 s. Sans retard.
- `periodicd1` : même profil périodique, avec 1 s de retard d'actionnement : la commande calculée au tick k est appliquée 2 ticks (1 s) plus tard.
Le contrôleur n'est pas informé du retard (comme un opérateur réel) ; l'observateur de biais et le MPC utilisent leur propre dernière commande.
Les runs durent 300 s, échauffement 20 s, comme le reste de l'étude. Implémentation : `mpcrpo/sim.py` (profils), `mpcrpo/runner.py` (retard),
`tests/test_amendment5.py`.

## Contrôleurs (4) et réglage
PI réglé, FF+obs, MPC persistance, MPC ARIMA(1,1,0). Chaque famille est RE-RÉGLÉE pour chaque cellule, même protocole que l'étude : 60 candidats
aléatoires (mêmes générateurs et même graine), graines de réglage 1000-1002, objectif robuste (moitié plant nominal avec le retard de la cellule, moitié
plant dégradé avec un tick de retard en plus), objectif = 0,5 x erreur stationnaire + 0,5 x erreur sur la fenêtre de perturbation de la cellule.
Fichier : `tuned_specs_scn.json` (script `experiments/tune_scenarios.py`). Le MPC moyenne mobile n'est pas inclus : il n'était pas meilleur que la
persistance dans l'étude principale et réduit le budget.

## Plan expérimental
8 runs valides par (cellule, contrôleur) = 96 runs (~9,1 h). Un seul plan randomisé et entrelacé : chaque répétition contient les 12 combinaisons
dans un ordre aléatoire, 30 s d'écart. Mêmes critères de validité. Les runs invalides sont refaits. Analyse sans regroupement avec d'autres campagnes.

## Critères et contrastes déclarés à l'avance
Critères principaux : erreur moyenne sur la fenêtre de perturbation (jusqu'à 20 s après sa fin) et pic d'exposition, mêmes définitions que l'étude.
Contrastes, dans chaque cellule : FF+obs contre MPC persistance ; FF+obs contre MPC ARIMA ; MPC persistance contre MPC ARIMA ; PI contre FF+obs
(rappel). Tests directs (Mann-Whitney, permutation, delta de Cliff, IC bootstrap), correction de Holm sur les trois premiers contrastes x deux critères x
trois cellules = 18 tests. Équivalence TOST avec les marges de l'étude (0,7 point ; 0,10) pour FF+obs contre MPC persistance.
Trois lectures fixées avant les données :
(a) aucun prédicteur ne bat FF+obs dans aucune cellule : la conclusion « prévoir n'aide pas » s'étend aux profils testés ;
(b) un prédicteur (ARIMA attendu) bat FF+obs sur le profil périodique, avec ou sans retard : la prévision aide sur une perturbation structurée ;
(c) un prédicteur bat FF+obs seulement avec le retard : la prévision aide quand l'actionnement est lent.
Tout autre résultat est rapporté tel quel, y compris si FF+obs est pire que le PI dans une cellule.

## Ce que cette expérience ne démontre pas
Un seul moteur, un nœud, une période et une amplitude de charge, un seul retard (1 s). Le réglage est fait sur le simulateur ; l'aperçu simulé ne vaut pas preuve.

## Réglage obtenu (ajouté avant les runs, après l'exécution de `tune_scenarios.py`, 48 minutes, fichier `tuned_specs_scn.json`)
Scores d'objectif simulés (plus bas = mieux) :
| cellule | PI | FF+obs | MPC persistance | MPC ARIMA |
|---|---|---|---|---|
| rampe | 3,12 | 0,71 | 0,70 | 0,81 |
| périodique | 6,03 | 1,74 | 1,74 | 1,52 |
| périodique + retard 1 s | 9,87 | 3,99 | 4,00 | 3,80 |
Alertes de bord (arrêts de l'espace de recherche, comme dans l'étude principale) : aucun paramètre continu (kp, ki, lambda, poids de sous-estimation) n'est au bord,
sauf kp = 0 et ki = 0 pour FF+obs, qui valent 0 par construction. Les alertes restantes portent sur les valeurs extrêmes des jeux discrets : filter_alpha = 1 (pas de filtre) ;
pour le MPC, gamma, ewma_alpha et bias_alpha aux extrêmes de leur jeu, et un horizon de 20 ticks (10 s, le plus long du jeu) pour le MPC persistance sur la rampe et le
périodique, ainsi que pour le MPC ARIMA sur la rampe. Le jeu d'horizons n'a pas été étendu pour garder le budget égal : cette limite est à écrire dans le manuscrit.
Lecture prudente de l'aperçu simulé : les écarts entre FF+obs et MPC sont de 0 à 13 % de l'objectif et ne constituent pas une preuve ; seuls les runs sur le cluster comptent.
