# mpc_rpo v0.2 — MPC vs PI sur le volume de données exposé (MongoDB), papier MPC uniquement

Aucun fichier d'un autre papier. Tout paramètre est dans `mpcrpo/config.py` ; chaque JSON de run
enregistre sa configuration complète + `config_hash` + la ligne du plan + la graine.

## Grandeur contrôlée (identifiée à l'étape 2, sur le vrai MongoDB 8.0.32)
- V = octets journalisés / nombre de syncs sur 10 s  (compteurs `log bytes written`, `log sync operations`)
- Actionneur : J = journalCommitInterval (20 ms – 500 ms). Perturbation : débit d'écriture R (octets/s).
- Modèle statique : V = R·(J + p·L)/p ,  p = min(1, R·J/b0) ;  en logs : ln V ≈ ln R + ln(J + pL)
  (additif, gain ≈ 1 : justifie l'Eq. (4) du papier). Plancher b0 ≈ 513 octets (un lot d'écriture).
- Capteur : fenêtre de 10 s -> retard mesuré sur une rafale réelle : t63 ≈ 6,5 s, t95 ≈ 10 s (étape 3b). Le débit R est observable à 0,5 s (bruit 0,6–2 % à ≥ 400 doc/s).

## Calibrage
Le simulateur est comparé aux mesures réelles : plante statique (9 points, étape 2) et rafale 400 -> 1 600 doc/s
(étape 3b) : niveaux de V à 1-3 %, temps de réponse du capteur à 0,5 s près, bruit du même ordre.
Écart connu : l'autocorrélation du débit par tick est plus négative en simulation qu'en réel.

## Structure
- `mpcrpo/plant.py`      simulateur événementiel des compteurs du journal (calibré sur les mesures de l'étape 2)
- `mpcrpo/sensor.py`     compteurs -> (V, R_fast, R_tick) ; même code en simulation et sur le cluster
- `mpcrpo/controllers.py` PI (anti-windup none/clamp/backcalc, filtre, feedforward optionnel, observateur de biais),
                          MPC (persistence/ma/arima sur ln R, coût asymétrique, solveur continu)
- `mpcrpo/metrics.py`    erreur, pic, récupération, coût en syncs/s, chatter, saturation
- `mpcrpo/stats.py`      Mann-Whitney, permutation, Cliff's delta, IC bootstrap, Holm
- `mpcrpo/schedule.py`   blocs randomisés ENTRELACÉS ; `runner.py` écriture atomique, reprise, jamais d'écrasement
- `mpcrpo/adapters/`     `sim_adapter.py` ; `mongo_adapter.py` (MongoDB réel : compteurs, setParameter, charge, validité du run)
- `experiments/`         `tune_sim.py`, `make_schedule.py`, `run_schedule.py`, `smoke_cluster.py`
- `docs/PLAN_ETUDE.md`   décisions fixées et plan d'analyse pré-spécifié ; `docs/AMENDEMENT_1.md` (après le pilote)
- `experiments/analyze_runs.py`  métriques par run, 7 contrastes (Mann-Whitney, Holm), équivalence (TOST)
- `experiments/make_sensitivity.py`, `analyze_sensitivity.py`  analyse de sensibilité (docs/AMENDEMENT_2.md)
- `experiments/make_topup.py`    complète chaque cellule jusqu'à son effectif cible (le pilote compte)
- `tests/selftest.py`    11 auto-tests dont le calibrage du simulateur contre les mesures réelles
- `tests/test_mongo_adapter_fake.py`  teste le code de l'adaptateur réel contre un faux MongoDB (~40 s)

## Démarrage (PowerShell)
    cd mpc_rpo
    pip install -r requirements.txt
    python tests\selftest.py
    python tests\test_mongo_adapter_fake.py
    python experiments\smoke_cluster.py          (cluster : port-forward + MONGO_USER/MONGO_PASSWORD)
    python experiments\tune_sim.py --budget 30 --tune-seeds 3 --test-seeds 15

## Réglage
`experiments/tune_sim.py` : 60 tirages par famille, réglage robuste (nominal + stress), détection des optima au bord ;
résultat dans `tuned_specs.json` (utilisé par `make_schedule.py --specs tuned_specs.json`).

## Régénérer le manuscrit (chiffres, tableaux, figures)
    python experiments\analyze_runs.py --raw data\raw --out analysis_P --max-rep 20
    python experiments\analyze_runs.py --raw data\raw --out analysis_S --max-rep 20 --exclude-stall-s 5
    python experiments\analyze_runs.py --raw data\raw --out analysis_all
    python paper\make_tables.py --primary analysis_P --sens analysis_S --all analysis_all --step2 step2_summary.json --step3b step3b_ticks.jsonl --specs tuned_specs.json --out paper
    python paper\make_figures.py --raw data\raw --step2 step2_summary.json --out paper\figures
    cd paper ; pdflatex main.tex ; pdflatex main.tex
(ne jamais éditer les chiffres à la main dans main.tex : ils viennent de numbers.tex et des tab_*.tex)

## Règles
1. Un résultat de simulation n'est JAMAIS une preuve pour le papier.
2. Chaque famille de contrôleurs reçoit le même budget de réglage ; réglage et test sur des graines distinctes.
3. Le signal ne lit jamais la valeur commandée (voir `adapters/base.py`).
4. Après chaque campagne : copie de `data\raw` sur un 2e support + `git commit`.

## Réplication sur une seconde plateforme (sans matériel supplémentaire)
`.github/workflows/replicate.yml` + `experiments/make_replication.py` + `docs/AMENDEMENT_3.md` : 24 runs sur un runner Linux gratuit
(dépôt public). Voir `docs/PUBLISH_GITHUB.md`.
