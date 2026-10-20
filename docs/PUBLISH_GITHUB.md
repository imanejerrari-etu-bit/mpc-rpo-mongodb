# Publier le code et les données (obligatoire pour la déclaration de disponibilité)

Le dépôt actuel (`imanejerrari-etu-bit/mpc-rpo-controller`) contient d'autres travaux et un README à compléter : ne le réutilisez pas
tel quel. Créez un **nouveau dépôt public**, par exemple `mpc-rpo-mongodb`.

## 1. Préparer le dossier
1. Dossier `mpc_rpo` (zip v12). Copiez dedans, dans `data\raw`, **tous les JSON** : pilote (63), campagne (71), remplacement (1),
   sensibilité (81) = 216 fichiers (dézippez les trois archives `raw*.zip` dans `data\raw` ; les noms sont uniques).
2. Vérifiez qu'aucun mot de passe n'apparaît : les JSON n'en contiennent pas ; ne publiez jamais vos variables d'environnement.
3. Ajoutez une licence (par exemple MIT pour le code, CC-BY 4.0 pour les données) : choix des auteurs.
4. Si la revue est en double aveugle, publiez d'abord un dépôt anonyme (anonymous.4open.science) et mettez le vrai dépôt à la fin.

## 2. Créer le dépôt (PowerShell, Git installé)
```powershell
cd C:\MPC\mpc_rpo
git init
git add .
git commit -m "MPC vs PI control of the MongoDB journal commit interval: code, schedules, data, manuscript"
git branch -M main
git remote add origin https://github.com/imanejerrari-etu-bit/mpc-rpo-mongodb.git
git push -u origin main
```
(Créez d'abord le dépôt vide sur github.com, sans README.)

## 3. DOI permanent (recommandé)
Zenodo (gratuit) : liez votre compte GitHub, créez une *release* `v1.0` : Zenodo délivre un DOI à citer dans le papier.

## 4. Réplication gratuite sur une seconde plateforme
Dépôt **public** : l'onglet *Actions* permet de lancer `Second-platform replication`. Faites un essai avec `smoke = true`
(~25 min), puis lancez les 6 répétitions (~2,5 h). Téléchargez l'artefact `replication-ci` et envoyez-le moi.
Le workflow n'a pas été testé sur GitHub : il peut demander un ou deux ajustements.

## 5. Dans le papier
Remplacez le `TODO` de *Data and code availability* par l'URL (ou le DOI) et listez : code `mpcrpo`, 216+ fichiers de runs, plans
(`schedule_*.csv`), spécifications réglées (`tuned_specs.json`), scripts d'analyse, amendements (`docs/`).
