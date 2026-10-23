# Liste de contrôle avant soumission

## Bloquants (à faire absolument)
- [ ] Dépôt public `mpc-rpo-mongodb` à jour avec les runs (principal, sensibilité, réplication) et **release `v1.0`** créée ; ajouter son hash de commit dans *Data and code availability* (`paper/main.tex`). Pas de Zenodo : la release figée en tient lieu.
- [ ] Ajouter un fichier `LICENSE` (sans licence, personne n'a le droit légal de réutiliser le code ; MIT pour le code et CC-BY 4.0 pour les données sont des choix courants : décision des auteurs).
- [ ] Déclaration d'usage d'outils d'IA, selon la politique de la revue (ce travail a été fait avec l'assistance d'un modèle de langage : code, analyses, rédaction).
- [ ] Relecture complète par le co-auteur ; accord écrit sur la liste d'auteurs et l'ordre.
- [ ] Relecture de l'anglais par une personne (les formulations des limites et de la discussion en particulier).
- [ ] Remplacer le titre de l'ancien dépôt (`mpc-rpo-controller`) ou nettoyer : il contient d'autres travaux et un README à compléter.

## À adapter à la revue choisie
- [ ] Classe LaTeX / gabarit (le brouillon utilise `svjour3`), longueur maximale, format des références, mots-clés, résumé (nombre de mots).
- [ ] Politique sur les données, sur les préprints, sur les versions antérieures rejetées ailleurs ; double aveugle ou non (dépôt anonyme si oui).
- [ ] Lettre d'accompagnement (`docs/COVER_LETTER.md`) : insérer la revue, l'URL, la déclaration d'IA ; joindre `docs/RESPONSE_TO_REVIEWERS.md` si la revue accepte les rapports antérieurs.

## Vérifications scientifiques
- [ ] Régénérer tous les chiffres avec les scripts (README, section « Régénérer le manuscrit ») ; ne rien éditer à la main dans `numbers*.tex` / `tab_*.tex`.
- [ ] Les trois amendements (`docs/AMENDEMENT_1..3.md`) sont datés avant les données qu'ils concernent : ne pas les réécrire après coup.
- [ ] Le texte ne revendique ni perte de données mesurée, ni généralisation à d'autres moteurs ou topologies.
- [ ] Le run avec arrêt du journal (FF_obs, rep04) est présenté avec et sans (analyse primaire et de sensibilité).
- [ ] L'écart `GLIBC_TUNABLES` de la réplication est déclaré dans le texte.

## Spécifique à *Computing* (Springer) — ce que j'ai pu vérifier, et ce qui reste à contrôler vous-même
Vérifié (pages de présentation et extraits des consignes, à reconfirmer sur la page de soumission) :
- [x] Portée : calcul adaptatif, autonomique et fiable ; calcul de services et de cloud : le sujet correspond.
- [x] Gabarit : LaTeX **une colonne**, option `smallextended` (c'est ce que le brouillon utilise désormais) ; Springer recommande aussi son gabarit LaTeX « Springer Nature ».
- [x] Politique de données Springer Nature : *Data Availability Statement* pour les articles originaux (présent dans *Declarations*).
- [x] Adresse e-mail professionnelle ou institutionnelle obligatoire (les soumissions avec une adresse privée seraient renvoyées) : les deux adresses du brouillon sont institutionnelles.
- [x] Auteurs : l'ordre et la liste doivent être corrects dès la soumission, tous les auteurs doivent avoir approuvé le manuscrit.
À contrôler (la page des consignes détaillées ne s'est pas chargée lors de ma vérification) :
- [ ] Longueur maximale du résumé et du manuscrit, nombre de mots-clés (le résumé fait environ 200 mots).
- [ ] **Frais de publication** (page « Fees and funding » de la revue) : Springer Nature a introduit des frais obligatoires sur au moins une autre revue en 2026 (signalé pour *Statistics and Computing*) ; je n'ai pas vérifié si c'est le cas pour *Computing*.
- [ ] Politique sur l'IA : l'usage est documenté dans la méthode (section 5) et dans *Declarations*, selon ma connaissance de la politique de Springer Nature, à reconfirmer.
- [ ] Politique sur la soumission d'un manuscrit rejeté dans une autre revue du même éditeur (la lettre le déclare).
- [ ] Lire la section « Ethical Responsibilities of Authors » de la revue.
