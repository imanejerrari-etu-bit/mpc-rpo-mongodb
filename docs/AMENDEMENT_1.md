# Amendement n°1 au plan d'étude (rédigé APRÈS le pilote, avant la campagne)

Le pilote (63 runs, 3 répétitions par cellule, 7 contrôleurs x 3 scénarios) est terminé : 63/63 runs valides,
aucun redémarrage de pod, aucune erreur d'insertion, débit acquitté/demandé entre 1,000 et 1,002, durée 300,1–302,2 s.
Les spécifications des contrôleurs n'ont PAS été modifiées après le pilote (même config_hash) : les runs du pilote
sont donc **inclus** dans l'analyse finale (même protocole).

## Ce que le pilote a montré (descriptif, n=3 par cellule)
- Le classement réel des contrôleurs sur l'erreur de rafale est identique à celui du simulateur (Spearman = 1,00) ;
  rapport réel/simulé de 0,80 à 1,09 sur l'erreur de rafale, 0,90 à 1,02 sur le pic.
- Écarts du simulateur : le bruit de mesure en régime établi est sous-estimé (MAE réel 1,2–1,5 % contre 0,5–0,95 %)
  et la variabilité entre runs en rafale est ~5 fois plus faible en simulation qu'en réel (sd ~0,4 contre ~0,08 pour
  FF_obs). Le simulateur sert à régler et à concevoir, jamais à conclure.
- Avec n=3 par cellule, le plus petit p de Mann-Whitney possible est 0,1 : aucun contraste ne peut passer Holm.

## Modifications du plan
1. **Effectifs** (runs valides totaux par cellule, pilote compris). Rafale : PI_FF, FF_obs, MPC_persist 15 ; MPC_ma,
   MPC_arima 10 ; PI_tuned 6 ; PI_default 3. Faible charge : 6 (PI_default 3). Stationnaire : 3 (descriptif : tous les
   contrôleurs réglés sont au plancher de bruit). 71 runs à ajouter (~6,7 h). Dimensionnement : variabilité réelle du
   pilote ; puissance simulée à alpha de Holm = 0,05/14 : ~0,8 pour PI_FF vs MPC_persist / FF_obs, ~0,9 pour MA vs
   persistance, ~1,0 pour PI_tuned vs les autres.
2. **Tests d'équivalence** pour les paires où « pas de différence » est l'affirmation : FF_obs vs MPC_persist et
   MPC_persist vs MPC_arima. TOST de Welch (IC90 dans la marge), marge = 0,7 point de pourcentage sur l'erreur de rafale
   (environ la moitié du plancher de bruit de 1,3 %) et 0,10 sur le pic d'exposition. On ne conclut JAMAIS à
   l'équivalence à partir d'un test de différence non significatif.
3. **Ré-estimation aveugle de l'effectif** après le complément : si l'écart-type intra-groupe poolé de l'erreur de rafale
   (PI_FF, FF_obs, MPC_persist) dépasse 0,5 point, on porte ces trois contrôleurs à n=20 (+15 runs). Règle fixée ici,
   fondée uniquement sur la variance, pas sur les différences entre groupes.
4. **PI_default** (gains naïfs) est une référence, pas un PI équitable : 26 % d'erreur même en régime établi (non convergé
   en 300 s). Il n'entre pas dans les contrastes ; le PI équitable est PI_tuned.
5. Les critères primaires, les 7 contrastes et la correction de Holm (7 x 2) restent inchangés.

## Ce qui n'est pas modifié
Cible V*, scénarios, durée, contrôleurs réglés, critères d'exclusion, un seul moteur, un seul hôte.
