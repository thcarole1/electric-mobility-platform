# 017 — Correction de la normalisation de town : liste blanche de villes connues

## Contexte

L'ADR-016 avait révélé, via le premier modèle dbt exploratoire
(`stg_villes_check`), qu'un POI était incorrectement classé avec
`town_normalisee = "SAEMES"` — SAEMES étant un opérateur de parking
parisien, pas une ville. La normalisation introduite en ADR-003
supposait que tout texte précédant le motif `" | "` dans `title` était
une ville, hypothèse invalidée par ce cas.

## Décision

Ajout d'une liste blanche (`VILLES_CONNUES`, actuellement `["Paris"]`)
dans `ajouter_town_normalisee` (`cleaning/openchargemap.py`) : une
valeur extraite depuis `title` n'est acceptée comme ville que si elle
figure dans cette liste. Le cas SAEMES retombe désormais dans le même
traitement que le cas "pompidou" déjà connu — `town_normalisee` reste
`null` plutôt que d'accepter une valeur non vérifiée.

La base DuckDB a été entièrement régénérée (poi, connections, meteo,
sessions) plutôt que mise à jour de façon incrémentale, suite à une
limitation de DuckDB rencontrée lors de la tentative d'upsert sur
`connections` : une contrainte de clé étrangère (`sessions` référençant
`connections`) a empêché l'upsert d'une ligne déjà référencée ailleurs,
avec une erreur `ConstraintException` distincte du cas déjà documenté
en ADR-001. Régénérer entièrement la base depuis les fichiers sources
(`data/raw/`, `data/processed/`) était plus sûr qu'un contournement
fragile de cette limitation.

## Pourquoi

Une liste blanche plutôt qu'une liste d'exclusion (option écartée en
discussion) : plus robuste face à de futurs cas problématiques
inconnus, au prix d'un entretien manuel si le projet élargit sa
couverture géographique au-delà de Paris. Le coût de cette liste reste
minime à l'échelle actuelle du projet (une seule entrée), le principe
de ne pas sur-ingénierer une solution générique (ex : référentiel
INSEE des communes) pour un seul cas réel restant appliqué.

## Conséquences

`town_normalisee` compte désormais 2 valeurs `null` (pompidou et
SAEMES) plutôt qu'une classification erronée. Si le projet élargit sa
zone géographique, `VILLES_CONNUES` devra être étendue en conséquence
— point à surveiller plutôt qu'automatiser tant que le volume de
communes reste faible. La limitation DuckDB sur les upserts avec clé
étrangère référencée par une autre table est à garder en mémoire pour
toute future modification du pipeline de chargement : une régénération
complète reste la solution la plus fiable dans ce cas, les données
étant toujours reconstructibles depuis les sources.
