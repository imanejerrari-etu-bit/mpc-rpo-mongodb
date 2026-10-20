# Amendement n°3 : réplication sur une seconde plateforme (déclarée AVANT de la lancer)

Motif : toutes les données viennent d'un seul hôte (Kind sous WSL2). La réplication utilise un runner Linux
hébergé gratuitement (GitHub Actions, workflow `.github/workflows/replicate.yml`) : MongoDB en Docker simple, sans
WSL2, matériel et système de fichiers différents. Elle ne remplace pas l'étude principale.

## Plan
Scénario rafale, 4 contrôleurs (PI_tuned, PI_FF, FF_obs, MPC_persist), mêmes spécifications réglées (aucun
réglage refait), 6 répétitions chacune = 24 runs (~2,5 h), blocs randomisés entrelacés, mêmes critères de validité
(redémarrage du conteneur, débit acquitté, erreurs d'insertion). Cache WiredTiger limité à 1 Go ; l'environnement
(processeur, mémoire, disque, version de MongoDB) est enregistré. La plateforme est partagée et peut être bruitée.

## Écart au protocole connu avant le lancement
Le runner a un noyau Linux >= 6.19, avec lequel MongoDB 8.x ne démarre pas (SERVER-121912). Le contournement de la communauté
`GLIBC_TUNABLES=glibc.pthread.rseq=1` est appliqué au conteneur ; ce n'est pas un correctif officiel. Il concerne l'allocateur
mémoire, pas le chemin du journal, mais son effet sur les mesures n'est pas vérifié : il est déclaré comme écart. La version
de MongoDB visée est 8.0.32 (celle du cluster principal), avec repli sur 8.0 si l'étiquette n'existe pas ; la version réelle
et le noyau sont enregistrés (`analysis_ci/mongo_image.txt`, `kernel.txt`).

## Critères de réussite déclarés à l'avance (descriptifs, n = 6)
- R1 : l'erreur de rafale de PI_tuned est au moins 3 fois celle de chacun des trois contrôleurs à anticipation.
- R2 : FF_obs et MPC_persist sont équivalents sur l'erreur de rafale (marge 0,7 point) et sur le pic (marge 0,10).
- R3 : le pic d'exposition de PI_tuned dépasse celui des trois autres.
Si un critère n'est pas satisfait, on l'écrit tel quel : la conclusion serait limitée à la plateforme d'origine.
Aucune conclusion sur le PI avec anticipation ne sera tirée de cette réplication au-delà des faits observés.

## Ce qu'elle ne démontre pas
Ni un cluster multi-nœuds, ni un jeu de réplication, ni la perte de données réelle.
