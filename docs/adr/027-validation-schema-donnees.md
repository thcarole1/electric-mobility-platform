# 027 — Validation de schéma à la source

## Contexte

L'incident documenté dans l'ADR-026 (contamination de type sur
`poi_id`, causée par la sérialisation JSON du mécanisme XCom
d'Airflow) n'avait été détecté qu'au moment de son exploitation dans
Athena, plusieurs jours après sa production effective. Aucun
mécanisme n'existait pour intercepter ce type d'incohérence au
moment où elle se produit, avant qu'une donnée corrompue n'atteigne
le data lake.

## Décision

Ajout d'un module de validation (`src/validation/schema.py`),
proposant une fonction générique `valider_schema` qui compare le
schéma réel d'un DataFrame Polars à un schéma attendu, et lève une
exception explicite (`SchemaValidationError`) en cas d'écart de type
ou de colonne manquante. Cette validation est appliquée juste avant
l'écriture du DataFrame météo, dans les deux chemins d'exécution du
pipeline (`run_pipeline.py` et le DAG MWAA), immédiatement après sa
construction.

## Pourquoi

La validation a été positionnée à la **source**, avant l'écriture des
données, plutôt qu'en aval sous forme de tests dbt sur les données déjà
présentes dans le data lake. Ce choix reflète directement la leçon de
l'incident précédent : une détection après coup aurait permis de
constater le problème plus vite qu'un utilisateur final tombant dessus
par hasard, mais n'aurait pas empêché une donnée corrompue de
transiter par S3 et d'être potentiellement consommée avant
correction. Une validation à la source arrête le pipeline avant que le
problème ne se propage, avec un message d'erreur qui identifie
précisément la colonne et l'écart de type en cause.

Une fonction générique, plutôt que des validations spécifiques par
table, a été retenue pour limiter la duplication et faciliter son
application à d'autres tables du projet si nécessaire, sans réécrire
de logique de comparaison de schéma à chaque fois.

## Conséquences

L'intégration au DAG MWAA a nécessité une vérification supplémentaire
: le nouveau module `validation/` devait être ajouté explicitement au
script `build_mwaa_plugins.sh`, celui-ci copiant chaque module source
individuellement plutôt que l'intégralité de `src/`. Cette
vérification a permis d'éviter une régression qui n'aurait été visible
qu'au moment d'un futur déploiement MWAA, un délai de détection
comparable à celui de l'incident initial que cette validation cherche
justement à éviter.

Un test reproduisant explicitement les conditions de l'incident
d'origine (une clé de dictionnaire fournie sous forme de chaîne de
caractères, simulant le comportement de XCom) a été ajouté à la suite
de test, garantissant qu'une régression future sur ce point précis
serait détectée avant tout déploiement, via la CI déjà en place
(ADR-024).

Ce périmètre reste limité à la table météo, seule concernée par
l'incident ayant motivé cette décision. Une extension à `poi` et
`connections` n'a pas été jugée nécessaire dans l'immédiat, ces deux
tables n'étant jamais transmises via un mécanisme de sérialisation
intermédiaire comparable à XCom.
