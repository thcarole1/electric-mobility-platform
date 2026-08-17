# 020 — Script d'orchestration locale du pipeline complet

## Contexte

L'exécution du pipeline (ingestion, nettoyage, chargement DuckDB,
météo, sessions) reposait entièrement sur l'exécution manuelle,
notebook par notebook, dans un ordre connu de l'auteur seul mais non
formalisé — un gap identifié explicitement lors d'une session
précédente (voir decisions-log.md, 16/08/2026), distinct de
l'automatisation Lambda/EventBridge qui ne couvre que l'étape
d'ingestion.

## Décision

Création de `run_pipeline.py`, à la racine du dépôt, qui enchaîne
l'intégralité du pipeline : ingestion Open Charge Map (nouvel appel
API, pas de réutilisation d'un fichier existant), nettoyage, chargement
poi/connections dans DuckDB, ingestion météo (boucle sur chaque POI du
DataFrame nettoyé, pas d'échantillonnage), assemblage et chargement
météo, génération et chargement de 455 sessions simulées.

Le chemin de la base DuckDB cible est paramétrable via un argument en
ligne de commande (`--db`), avec la base de production comme valeur
par défaut. Ce paramètre permet de tester le script sur une base
isolée sans affecter les données de production — utilisé pour la
validation initiale de ce script (base `test_pipeline.duckdb`,
supprimée après vérification, jamais versionnée).

## Pourquoi

Ce script sert un double objectif : combler immédiatement le gap
d'orchestration identifié sans attendre la mise en place plus lourde
de MWAA (qui nécessite une remise à niveau sur le networking AWS non
encore entreprise), et constituer une base de traduction naturelle vers
un futur DAG Airflow — chaque étape du script correspond à une tâche
candidate. Le paramétrage du chemin de base répond au principe déjà
appliqué ailleurs dans le projet : toujours valider une modification
sur des données isolées avant de la considérer comme fiable pour la
production.

## Conséquences

Le pipeline complet peut désormais s'exécuter d'une seule commande
(`python run_pipeline.py`), en environ 40 secondes de bout en bout,
constatée en conditions réelles lors du test de validation (50 POI, 99
connexions, 6000 lignes météo, 455 sessions). Ce script reste un outil
local, sans exécution automatisée ni planification — contrairement aux
fonctions Lambda, il doit être lancé manuellement. Sa traduction en DAG
Airflow/MWAA, ou son intégration à une planification EventBridge,
reste à faire dans une future session.
