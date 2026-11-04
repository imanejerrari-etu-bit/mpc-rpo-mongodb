# Amendement 6 (PowerShell)

1. Copier les fichiers de l'archive (chemins conservés), puis : python tests\selftest.py ; python tests\test_amendment5.py ; python tests\test_mongo_adapter_fake.py
2. Régler le contrôleur à seuils (2 à 3 minutes, sans cluster) :
       python experiments\tune_baselines.py --budget 60 --tune-seeds 3 --out tuned_specs_base.json
3. Planning (doit afficher 72 runs, ~6,8 h ; périodique FF_obs et MPC_arima à partir de rep09) :
       python experiments\make_block_amend6.py --scn-specs tuned_specs_scn.json --base-specs tuned_specs_base.json --raw data\raw --out schedule_amend6.csv
4. COMMIT AVANT LES RUNS :
       git add docs\AMENDEMENT_6.md docs\GUIDE_AMEND6.md tuned_specs_base.json schedule_amend6.csv experiments mpcrpo tests
       git commit -m "Amendement 6: confirmation periodique + baselines operateur, declare avant les runs"; git push
5. Lancer (cluster actif, port-forward, MONGO_USER / MONGO_PASSWORD) ; reprise = relancer la même commande :
       powercfg /change standby-timeout-ac 0
       python experiments\run_schedule.py --schedule schedule_amend6.csv --out data\raw --adapter mongo
6. Analyse : python experiments\analyze_amend6.py --raw data\raw --schedule schedule_amend6.csv --out analysis_amend6
