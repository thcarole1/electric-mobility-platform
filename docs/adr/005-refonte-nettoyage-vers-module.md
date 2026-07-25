# 005 — Refonte du notebook de nettoyage en module Python testé

## Contexte

La logique de nettoyage (extraction des tables poi et connections,
normalisation du champ town) vivait entièrement dans le notebook
02_nettoyage_openchargemap.ipynb. Cette logique était stabilisée depuis
plusieurs sessions, mais restait non testable unitairement et couplée
à l'exécution manuelle du notebook.

## Décision

Migration vers src/cleaning/openchargemap.py, découpé en cinq fonctions
à responsabilité unique (extraction poi, extraction connections,
normalisation de town, sauvegarde Parquet, orchestration), avec une
suite de 6 tests unitaires (tests/test_cleaning_openchargemap.py).
Le notebook original est conservé, simplifié pour n'appeler que la
fonction d'orchestration nettoyer_openchargemap et la fonction de
sauvegarde — il sert désormais d'exemple d'usage, plus de lieu
d'implémentation.

Contrairement au module ingestion (refonte précédente, ADR-004), ce
module n'a aucune dépendance externe (pas de réseau, pas de secrets,
pas de service AWS) : ses fonctions sont pures, ce qui a rendu les
tests unitaires nettement plus simples à écrire, sans mocking de
bibliothèques externes — seul le test de l'orchestration nécessite de
mocker les sous-fonctions internes, pour les mêmes raisons d'isolation
que sur le module ingestion.

La génération du nom de fichier horodaté n'a volontairement pas été
factorisée avec la fonction équivalente du module ingestion : les deux
modules ne doivent pas dépendre l'un de l'autre, et un seul point
d'usage actuel ne justifie pas une extraction prématurée vers un module
partagé.

## Pourquoi

Même raisonnement que pour le module ingestion (ADR-004) : le code
stabilisé en notebook n'est ni testable unitairement, ni réutilisable
en dehors de ce notebook précis. La migration suit le même workflow
"notebook → module → tests" prévu dès le Cahier des charges.

## Conséquences

Le prochain notebook à migrer (03_chargement_duckdb) suivra la même
approche. Si un troisième module a un jour besoin d'un nommage de
fichier horodaté similaire, ce sera le bon moment pour envisager un
module utilitaire partagé (par exemple src/utils.py) — pas avant.
