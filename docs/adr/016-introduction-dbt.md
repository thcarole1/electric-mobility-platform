# 016 — Introduction de dbt pour structurer les transformations SQL

## Contexte

La roadmap Phase 3 prévoyait dbt comme outil de transformation SQL
versionnée, suite à l'analyse du marché de l'emploi Data Engineer
France 2026 (dbt cité aux côtés d'Airflow parmi les compétences les
plus recherchées).

## Décision

Initialisation d'un projet dbt (`electric_mobility_dbt/`) connecté
directement à la base DuckDB déjà en production
(`data/warehouse/electric_mobility.duckdb`), via l'adapter `dbt-duckdb`.
dbt vient s'ajouter en couche de transformation par-dessus les tables
déjà chargées par `warehouse/duckdb_loader.py` — il ne remplace ni
DuckDB ni le pipeline Python existant, il structure les analyses SQL
qui étaient jusqu'ici écrites à la main dans des notebooks.

Deux premiers modèles staging créés : `stg_villes_check` (exploratoire,
a révélé une donnée non anticipée — un opérateur "SAEMES" mal classé
comme ville dans `town_normalisee`, cas limite non couvert par la
normalisation de l'ADR-003) et `stg_connecteurs_par_type` (indicateur
fiable, sans dépendance à une donnée fragile), accompagné de tests
génériques dbt (`not_null`, `unique`).

`dbt-duckdb` a été ajouté aux dépendances `dev` du `pyproject.toml`,
jamais utilisé par le code de production de `src/` — cohérent avec le
principe déjà appliqué à `jupyterlab` et `python-dotenv`.

## Pourquoi

dbt matérialise ses modèles par défaut en vues plutôt qu'en tables
(aucune donnée dupliquée, toujours à jour), un choix conservé pour ces
premiers modèles exploratoires ; la matérialisation en table reste
disponible si la performance devait le justifier plus tard. Le premier
modèle (`stg_villes_check`) a confirmé la valeur de dbt au-delà de la
seule structuration : une simple requête d'exploration a immédiatement
révélé une donnée mal classée qui serait passée inaperçue dans un usage
ad hoc en notebook.

## Conséquences

Le projet dbt vit dans son propre sous-dossier, avec sa configuration
de connexion (`~/.dbt/profiles.yml`) volontairement non versionnée,
comme les autres secrets/configurations locales du projet. Le cas
"SAEMES" identifié dans `stg_villes_check` reste à corriger (soit dans
la normalisation Python existante, soit par une règle dbt dédiée) —
non traité dans cette session, noté comme point ouvert. D'autres
modèles pourront suivre au fil des besoins d'analyse, sans obligation
de tout migrer d'un coup depuis les notebooks existants.
