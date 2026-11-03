# Amendement 5 : rampe, charge périodique, retard d'actionnement (PowerShell)

Étape 1 - copier les fichiers de l'archive dans ton dépôt (chemins conservés), puis vérifier :
    python tests\selftest.py
    python tests\test_amendment5.py
    python tests\test_mongo_adapter_fake.py

Étape 2 - régler les 4 familles pour les 3 cellules sur le simulateur (60 candidats, 3 graines). Il reprend là où il s'est arrêté si tu l'interromps.
Compte 30 à 60 minutes, sans cluster :
    python experiments\tune_scenarios.py --budget 60 --tune-seeds 3 --out tuned_specs_scn.json

Étape 3 - AVANT de lancer les runs, commit (l'amendement doit être daté avant les données) :
    git add docs\AMENDEMENT_5.md docs\GUIDE_SCENARIOS.md tuned_specs_scn.json experiments mpcrpo tests
    git commit -m "Amendement 5: rampe, periodique, retard d'actionnement, declare avant les runs"

Étape 4 - planning (96 runs, environ 9,1 h) :
    python experiments\make_block_scenarios.py --specs tuned_specs_scn.json --n 8 --out schedule_scenarios.csv
    git add schedule_scenarios.csv; git commit -m "Planning amendement 5"

Étape 5 - lancer (cluster actif, port-forward dans une autre fenêtre, MONGO_USER / MONGO_PASSWORD chargés), en une ou plusieurs soirées :
    powercfg /change standby-timeout-ac 0
    python experiments\run_schedule.py --schedule schedule_scenarios.csv --out data\raw --adapter mongo
Reprise : relancer la même commande. Contrôle après les premiers runs :
    python experiments\quick_look.py --raw data\raw --scenario periodicd1 --controllers PI_tuned FF_obs MPC_persist MPC_arima

Étape 6 - analyse : python experiments\analyze_scenarios.py --raw data\raw --schedule schedule_scenarios.csv --out analysis_scenarios
