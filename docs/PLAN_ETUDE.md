# Plan d'étude (à figer AVANT l'essai pilote) — papier MPC, MongoDB uniquement

## 1. Question et périmètre
Contrôler le volume V de données exposées entre deux syncs du journal MongoDB en ajustant
journalCommitInterval J. Question : sous rafale de charge, un MPC (avec prévision de la charge) fait-il mieux
qu'un PI correctement conçu, y compris un PI avec anticipation (feedforward) ? Périmètre : **un seul moteur
(MongoDB 8.0.32, pod unique), un seul hôte (Kind sous WSL2)**. Aucune revendication sur MySQL/Redis.

## 2. Plante identifiée (mesures réelles, étapes 2 et 3b)
V ≈ R·(J + p·L)/p, p = min(1, R·J/b0) ; en logs : ln V ≈ ln R + ln(J + pL) (gain ≈ 1, additif).
Capteur : fenêtre 10 s -> t63 ≈ 6,5 s, t95 ≈ 10 s. Débit R visible en ~2 s. Actionneur : 4,9 ms (max 6,4 ms).

## 3. Décisions fixées
| Paramètre | Valeur | Raison |
|---|---|---|
| Cible V* | 4096 octets | atteignable sur toute la plage : J ≈ 196 ms à 400 doc/s, ≈ 43 ms à 1 600 doc/s, dans [20 ; 500] ms ; très au-dessus du plancher (513 octets) |
| Scénarios | stationnaire 400 doc/s ; rafale 400 -> 1 600 -> 400 (t = 100–160 s) ; faible charge 100 -> 400 | rafale x4 ; faible charge : V* inatteignable au départ (J > 500 ms) = saturation de l'actionneur |
| Durée d'un run | 300 s (warm-up 20 s) | 250 s de régime établi, 60 s de rafale, 140 s de récupération ; plus de runs vaut mieux que des runs longs |
| Lots d'écriture | 10 documents (plancher 513 octets) | déjà calibré ; plancher = 12,5 % de V* |
| J | [20 ; 500] ms, départ 100 ms | plage de l'actionneur ; valeur par défaut de MongoDB |
| Pause entre runs | 30 s | J restauré, base supprimée |

## 4. Contrôleurs (7) et réglage
PI_default (gains naïfs) ; PI_tuned (anti-windup, filtre) ; PI_FF (PI + anticipation sur la charge + observateur de biais) ;
**FF_obs (anticipation + observateur, sans rétroaction ni prédiction : baseline minimal)** ; MPC_persist ; MPC_ma ; MPC_arima. **Même budget de réglage pour chaque famille** (60 tirages aléatoires), réglage **robuste** (moitié plante nominale,
moitié plante de stress : sync plus lente, plus de gigue, 1 tick de retard), graines de réglage distinctes des
graines de test, mêmes tirages de candidats pour les trois MPC. Règle : tout optimum au bord de l'espace de
recherche impose de l'élargir. **Leçon (simulation)** : un lissage différent du débit de charge entre familles avait
fait croire que le MPC battait le PI avec anticipation ; une fois le lissage réglé pour chaque famille, l'écart a
disparu. Tous les contrôleurs reçoivent donc les mêmes entrées brutes et règlent leur propre lissage. Réglage en simulation calibrée, puis vérification sur
l'essai pilote ; si le pilote contredit le simulateur, recalibrage avant la campagne.

## 5. Plan d'expérience
Blocs randomisés entrelacés (graine enregistrée). Pilote : 3 répétitions par cellule = 63 runs (~6 h).
Campagne : stationnaire 5, rafale 10, faible charge 6 répétitions x 7 contrôleurs = 147 runs (~14 h).
Un run est exclu et répété si : un pod redémarre, le débit acquitté < 95 % du débit demandé, ou le run
est interrompu. Les exclusions sont listées dans l'article.

## 6. Critères de jugement (déclarés à l'avance)
Primaires (rafale) : erreur moyenne pendant la rafale (mae_burst_pct) ; pic d'exposition (peak_ratio).
Secondaires : erreur en régime établi, temps de récupération, coût en syncs/s, chatter de J, fraction de
saturation, erreur en faible charge.

## 7. Analyse (pré-spécifiée)
Contrastes (7) : PI_tuned vs PI_FF ; PI_FF vs FF_obs ; FF_obs vs MPC_persist ; PI_FF vs MPC_persist ;
MPC_persist vs MPC_ma ; MPC_persist vs MPC_arima ; PI_tuned vs MPC_persist. Test de Mann-Whitney bilatéral + Cliff's delta + IC bootstrap de la différence,
correction de Holm sur les 7 contrastes x 2 critères primaires. Jamais « IC non chevauchants ».
Un effet est rapporté d'abord par sa taille, puis par son p.

## 8. Sensibilité (après la campagne)
V* in {2, 8} kB ; gains des contrôleurs retenus +/- 50 % ; (optionnel) lots d'un document.

## 9. Ce qu'on ne revendique pas
Pas de mesure de perte de données réelle (pas de crash test). Un seul moteur, un seul hôte. V est un
composite de deux compteurs, pas une mesure directe. Les résultats de simulation ne sont pas des preuves.
Si MPC ~ FF_obs (ce que la simulation annonce), la conclusion est : l'optimisation et la prévision n'apportent rien
au-delà de l'anticipation sur la charge observée avec un observateur de biais.

## 10. Données
Copie de data/raw sur un 2e support après chaque campagne ; git commit ; chaque JSON porte son config_hash.
