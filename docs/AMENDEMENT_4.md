# Amendement n°4 : PI sur estimation rapide de V (déclaré AVANT de lancer les runs)

Motif : le PI réglé agit sur V mesuré sur une fenêtre de 10 s, alors que les contrôleurs à anticipation utilisent le débit instantané.
L'écart observé mesure donc au moins en partie la valeur d'un signal rapide, pas celle de la structure du contrôleur (limite déjà écrite dans
le manuscrit). Cet amendement ajoute le contrôleur qui sépare les deux effets.

## Contrôleur ajouté : `PI_fast`
PI sur e = ln V* - ln V_hat, avec V_hat = v_model(R_fast, J_prev) * exp(b) : modèle statique du procédé évalué au débit instantané et au
dernier intervalle appliqué, corrigé par le même observateur de biais que FF_obs. Pas de terme d'anticipation (ff = false), pas de prédiction.
Même actionneur, mêmes bornes, mêmes anti-windup possibles. Implémentation : `PIConfig.fast_v` dans `mpcrpo/config.py`, `PIController.step`.

## Réglage
Même protocole que les autres familles : 60 candidats aléatoires, simulateur calibré, objectif robuste (plant nominal + plant dégradé avec
1 tick de retard), graines de réglage 1000-1002 distinctes des graines de test. Aucun réglage des autres familles n'est refait
(`tuned_specs.json` : les six spécifications existantes sont inchangées, PI_fast est ajouté). Aucun paramètre de PI_fast au bord de l'espace de recherche.
Spécification retenue : kp = 2,748 ; ki = 0,976 ; anti-windup backcalc ; filter_alpha = 0,25 ; bias_alpha = 0,6 ; ff_alpha = 0,6.
Les résultats simulés ne constituent pas une preuve ; ils ne servent qu'à valider le protocole.

## Plan expérimental
Scénario rafale, un bloc contemporain : PI_fast, PI_tuned et FF_obs, 10 répétitions valides chacun = 30 runs (~2,9 h), chaque répétition
contient les trois contrôleurs dans un ordre aléatoire (entrelacé). Mêmes critères de validité (redémarrage de pod, débit acquitté, erreurs
d'insertion). Les runs invalides sont refaits. Les numéros de répétition continuent après les runs existants. La comparaison principale utilise
uniquement ce bloc (témoins contemporains) ; les runs antérieurs servent de contexte, sans être regroupés avec lui.

## Contrastes et critères déclarés à l'avance
Mêmes critères principaux que l'étude (erreur de rafale, pic d'exposition), mêmes tests directs, intervalles bootstrap et correction de Holm.
Contrastes : PI_fast contre PI_tuned ; PI_fast contre FF_obs. Équivalence avec les marges de l'étude (0,7 point sur l'erreur de rafale, 0,10 sur le pic).
Trois lectures, fixées avant les données :
(a) PI_fast équivalent à FF_obs : l'écart au PI réglé vient de la vitesse du signal, pas de la structure ;
(b) PI_fast significativement entre les deux : la vitesse du signal explique une partie de l'écart, l'anticipation explicite le reste ;
(c) PI_fast équivalent à PI_tuned : la structure compte, pas seulement le signal.
Tout autre résultat est rapporté tel quel. Le manuscrit sera mis à jour dans les trois cas, y compris le résumé et la liste des limites.

## Ce que cette expérience ne démontre pas
Elle ne change pas le périmètre : un moteur, un nœud, une rafale en échelon, un signal d'exposition et non une perte de données observée.
