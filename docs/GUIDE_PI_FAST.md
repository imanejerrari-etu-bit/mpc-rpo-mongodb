# PI sur estimation rapide de V : étapes (PowerShell)

Étape 1 - appliquer les fichiers (depuis la racine de ton dépôt local) : copier les fichiers de l'archive en gardant les chemins
(mpcrpo\config.py, mpcrpo\controllers.py, experiments\*.py, tuned_specs.json, schedule_pifast.csv, docs\AMENDEMENT_4.md).
Sauvegarde d'abord ton tuned_specs.json actuel : `Copy-Item tuned_specs.json tuned_specs_v1.json`.

Étape 2 - vérifier le code :
    python tests\selftest.py
    python tests\test_mongo_adapter_fake.py

Étape 3 - (optionnel) refaire le réglage chez toi, il doit redonner la même spécification (3 à 4 minutes) :
    python experiments\tune_sim.py --budget 60 --tune-seeds 3 --test-seeds 15 --only PI_fast --reuse tuned_specs_v1.json

Étape 4 - régénérer le planning si tu veux vérifier (il continue après tes runs existants) :
    python experiments\make_block_pifast.py --raw data\raw --specs tuned_specs.json --n 10 --out schedule_pifast.csv

Étape 5 - lancer (cluster actif, port-forward dans une autre fenêtre, MONGO_USER / MONGO_PASSWORD chargés) :
    python experiments\run_schedule.py --schedule schedule_pifast.csv --out data\raw --adapter mongo
Reprise possible : relancer la même commande après une interruption. Environ 2,9 h.

Étape 6 - analyse : on adapte analyze_runs.py ensemble (le filtre --max-rep 20 exclurait les nouveaux runs, numérotés à partir de 24).
