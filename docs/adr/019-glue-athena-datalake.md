# 019 — Data lake S3 : Glue Catalog et Athena pour le requêtage serverless

## Contexte

La roadmap Phase 3 prévoyait Glue Catalog et Athena comme brique
complémentaire à DuckDB, permettant d'interroger les données directement
sur S3 sans les charger dans une base locale — dernière brique non
abordée de cette phase.

## Décision

Ajout de `common.io.sauvegarder_parquet_s3`, qui écrit un DataFrame
Polars directement en Parquet sur S3 (sans étape intermédiaire locale),
en recevant un dictionnaire `storage_options` explicite en paramètre
plutôt que de laisser Polars détecter automatiquement les identifiants
depuis l'environnement — choix motivé par la testabilité et la clarté
de débogage, cohérent avec le principe d'injection de dépendance déjà
appliqué à `uploader_s3` et `client_s3`.

Structure S3 étendue avec un dossier `processed/`, organisé par table
(`processed/poi/`, `processed/connections/`), au même niveau que `raw/`
— une table Glue = un dossier S3, condition nécessaire au bon
fonctionnement du Crawler.

Un Glue Crawler (`electric-mobility-crawler`) scanne `processed/` et
détecte automatiquement les schémas des fichiers Parquet (pas de
déduction nécessaire, contrairement à du CSV ou JSON, le schéma étant
déjà encodé dans le format Parquet), créant les tables dans la base
`electric_mobility_catalog`. Un rôle IAM dédié
(`electric-mobility-glue-crawler-role`) a été créé, distinct du rôle
Lambda existant, avec une politique en lecture seule strictement
limitée à `s3:GetObject`/`s3:ListBucket` sur `processed/*` — le Crawler
ne devant jamais écrire sur S3, contrairement au rôle Lambda qui
nécessite `PutObject`.

Athena est utilisé en mode interactif via la console (workgroup
`primary`), sans rôle IAM dédié : les requêtes s'exécutent avec les
permissions de l'utilisateur connecté (`emp-admin`, AdministratorAccess)
plutôt qu'un rôle de service, cette distinction ayant été clarifiée en
session (un rôle de service est nécessaire pour un traitement autonome
sans utilisateur humain, pas pour un usage interactif direct). Le
dossier de résultats de requêtes Athena a été configuré au même niveau
hiérarchique que `raw/`/`processed/` (`athena-results/`), les résultats
de calcul n'étant ni de la donnée brute ni de la donnée nettoyée.

## Pourquoi

Le Crawler à la demande (pas de planification automatique) reproduit
le principe déjà appliqué à Lambda : valider manuellement avant
d'automatiser. Le choix de storage_options explicite plutôt que la
détection automatique par l'environnement privilégie la testabilité et
la clarté de débogage au prix d'une légère verbosité supplémentaire —
un compromis assumé compte tenu du niveau de confort actuel avec le
débogage d'authentification cloud.

## Conséquences

Le pipeline dispose désormais de deux moyens équivalents d'interroger
les données nettoyées : DuckDB en local (rapide, mono-utilisateur) et
Athena sur S3 (serverless, accessible à quiconque a les permissions
IAM adéquates) — les deux coexistent sans que l'un ne remplace l'autre.
La table `meteo` n'a pas encore été migrée vers `processed/` (le
DataFrame correspondant n'était pas disponible en session) ; `sessions`
reste volontairement absente de S3, cohérent avec la décision de ne
pas exposer de données simulées sur cette architecture pour l'instant.
Si le Crawler doit être exécuté fréquemment, une planification via
EventBridge (sur le modèle déjà en place pour les fonctions Lambda)
sera à envisager.
