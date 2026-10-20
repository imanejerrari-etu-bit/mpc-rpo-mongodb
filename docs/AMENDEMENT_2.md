# Amendement n°2 : analyse de sensibilité (rédigé AVANT de la lancer ; campagne principale déjà analysée)

Motif : le Reviewer 1 reproche que ni les paramètres du PI ni ceux du MPC ne soient jamais variés. Cette phase
vérifie que les conclusions de la campagne principale ne dépendent pas d'un point de réglage unique ni d'une
cible V* particulière. Elle est descriptive (3 répétitions par variante, pas de p-values) : on rapporte des rapports
et des plages, pas des tests.

## Plan (81 runs, ~7,7 h, scénario rafale, blocs randomisés entrelacés)
- Perturbations une à la fois, x0,5 et x1,5 (bornées aux plages valides ; un paramètre égal à 1 ne peut que baisser) :
  PI_tuned (kp, ki) ; PI_FF (kp, ki, ff_alpha) ; FF_obs (bias_alpha, ff_alpha) ;
  MPC_persist (lam, under_weight, bias_alpha, ewma_alpha). L'horizon H n'est pas varié : avec une prévision plate il
  est redondant avec lam (H·e² + lam·Δ² équivaut à e² + (lam/H)·Δ²).
- Cible V* = 2048 et 8192 octets pour PI_FF, FF_obs, MPC_persist (V* = 2048 est inatteignable en rafale : J < 20 ms).
- 3 témoins nominaux concurrents par contrôleur (répétitions 21 à 23, même nuit) pour contrôler la dérive ; ils
  sont exclus de l'analyse principale (`--max-rep 20`).

## Critères déclarés à l'avance
- C1 robustesse aux paramètres : pire rapport erreur de rafale (variante / témoin concurrent), par contrôleur.
- C2 robustesse du classement : l'erreur de rafale (et le pic) de la PIRE variante de {PI_FF, FF_obs, MPC_persist}
  reste inférieure à celle de la MEILLEURE variante de PI_tuned.
- C3 robustesse à la cible : erreur et pic à V* = 2048 et 8192.
Si C2 est faux, l'écrire tel quel : la conclusion « l'anticipation sur la charge domine la rétroaction » serait
limitée au réglage nominal.

## Hors périmètre
Aucun changement de scénario, de moteur, de durée ni de protocole.
