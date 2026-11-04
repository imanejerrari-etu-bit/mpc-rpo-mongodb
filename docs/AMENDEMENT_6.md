# Amendement n°6 : confirmation sur le périodique et baselines d'opérateur (déclaré AVANT de lancer les runs)

Motif. (1) L'amendement 5 a donné un indice non confirmé : sur la charge périodique sans retard, MPC ARIMA a une erreur de perturbation plus basse que FF+obs
(1,95 % contre 2,47 %, différence 0,53 point, IC95 [0,26 ; 0,79], p Mann-Whitney 0,0047, p corrigé par Holm sur 18 tests 0,084, donc non significatif selon le critère déclaré).
Un bloc de confirmation sur de nouvelles données tranche. (2) Ni l'étude principale ni l'amendement 5 ne comparent les contrôleurs à ce que font les opérateurs
(valeur par défaut, règles à seuils) ; l'ajout situe le bénéfice du contrôle.

## Bloc A : confirmation (24 runs, ~2,3 h)
Cellule `periodic` de l'amendement 5 (profil, spécifications FF+obs et MPC ARIMA identiques, fichier `tuned_specs_scn.json`). 12 nouveaux runs valides par contrôleur,
répétitions 9 à 20 ; les répétitions 1 à 8 de l'amendement 5 ne sont pas réutilisées. UN contraste déclaré : MPC ARIMA moins FF+obs sur l'erreur moyenne sur la fenêtre de
perturbation, test de Mann-Whitney bilatéral, alpha = 0,05, sans correction (contraste unique). Confirmé si et seulement si p < 0,05 ET MPC ARIMA est plus bas.
Pic, récupération, erreur stationnaire et coût d'E/S (syncs par seconde) sont descriptifs. Analyse sur ces 24 runs seuls.

## Bloc B : baselines d'opérateur (48 runs, ~4,6 h)
Cellules : échelon (`burst`, même scénario que l'étude principale) et `periodic`. Trois contrôleurs, 8 runs valides chacun : `Static` (J = 100 ms, valeur par défaut du moteur, jamais modifiée),
`Threshold` (règles à seuils : si V/V* dépasse `hi`, J est multiplié par `down` ; si V/V* est sous `lo`, J est multiplié par `up` ; sinon J est maintenu ; une action au plus tous les
`cooldown` ticks ; J borné), et un FF+obs contemporain servant de référence. `Threshold` est réglé par cellule avec le même protocole que les autres familles (60 candidats, graine 0, graines de réglage 1000-1002,
objectif robuste) ; fichier `tuned_specs_base.json` (script `experiments/tune_baselines.py`). Contrastes déclarés : Static contre FF+obs et Threshold contre FF+obs,
sur l'erreur de perturbation et le pic, dans chaque cellule, Holm sur 8 tests. Aucune hypothèse de direction n'est nécessaire : l'écart attendu est très grand.
Le coût d'E/S est rapporté pour tous.

## Plan
72 runs dans un seul plan randomisé et entrelacé (`schedule_amend6.csv`, script `experiments/make_block_amend6.py`). Mêmes critères de validité que le reste de l'étude.
Analyse : `experiments/analyze_amend6.py`. Les résultats sont rapportés quel qu'en soit le sens, y compris si le bloc A infirme l'indice de l'amendement 5.

## Ce que cette expérience ne démontre pas
Les baselines ne représentent pas toutes les pratiques d'opérateur (pas d'autoscaler propriétaire ni de réglage manuel par un administrateur). Un seul moteur, un nœud, un profil périodique
de période 40 s. Le réglage est fait sur le simulateur.

## Réglage obtenu (ajouté avant les runs, après `tune_baselines.py`, fichier `tuned_specs_base.json`)
Threshold, échelon : hi 1,44 ; lo 0,93 ; down 0,18 ; up 1,41 ; cooldown 16 ticks (score simulé 13,58). Threshold, périodique : hi 1,18 ; lo 0,82 ; down 0,57 ; up 1,17 ; cooldown 4 ticks (score 17,06).
Alertes de bord : sur l'échelon, `down` = 0,18 est proche du bas de sa plage (0,15) et `cooldown` = 16 est le plus long du jeu. Un facteur `down` inférieur à 0,2 ramène J à son plancher (20 ms) en une action
depuis 100 ms, donc étendre la plage ne changerait pas le comportement ; en revanche un `cooldown` plus long que 16 ticks (8 s) n'a pas été essayé, limite à écrire dans le manuscrit.
Les plages de recherche avaient été élargies une fois avant cet amendement, car l'optimum du premier essai se trouvait sur leur bord. Les scores simulés (13,6 et 17,1) sont à comparer à ceux de FF+obs (1 à 2) : l'écart attendu est très grand ; il ne constitue pas une preuve.
Numérotation du plan : FF_obs échelon rep34-41 ; FF_obs et MPC_arima périodique rep09-20 (bloc A) ; FF_obs périodique rep21-28 (bloc B) ; Static et Threshold rep01-08 (échelon) et rep21-28 (périodique).
