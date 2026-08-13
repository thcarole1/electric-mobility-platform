# 015 — Automatisation du déclenchement de l'ingestion météo

## Contexte

Suite au déploiement de la fonction Lambda météo (ADR-014), il restait
à automatiser son déclenchement, sur le modèle déjà établi pour Open
Charge Map (ADR-013).

## Décision

Création du schedule `electric-mobility-ingestion-meteo-daily`, avec
exactement la même configuration que celui d'Open Charge Map : cron
quotidien à 4h00 heure de Paris (`cron(0 4 * * ? *)`), fenêtre de
flexibilité de 15 minutes, retry policy à 2 tentatives, rôle IAM créé
automatiquement par EventBridge Scheduler. Contrairement au
déclenchement d'Open Charge Map, aucun test manuel immédiat n'a été
effectué après la création du schedule — la première exécution
automatique du lendemain a été acceptée comme validation suffisante,
le mécanisme ayant déjà été éprouvé.

Les deux sources (Open Charge Map, météo) sont déclenchées au même
horaire, sans raison technique de les synchroniser ou de les espacer :
les deux fonctions sont indépendantes, sans dépendance de données à
l'exécution.

## Pourquoi

Répliquer un schéma déjà validé, sans variation inutile, réduit le
risque d'erreur et la charge cognitive de configuration. L'absence de
test manuel immédiat reflète une confiance acquise après la validation
réussie du même mécanisme sur Open Charge Map (ADR-013) — vérifier à
nouveau à l'identique n'aurait apporté aucune information nouvelle.

## Conséquences

Les deux sources de données du projet tournent désormais de façon
entièrement autonome, sans intervention manuelle quotidienne. La
vérification de la première exécution automatique (attendue le
14/08/2026 à 4h00) reste à confirmer lors d'une prochaine session, en
consultant CloudWatch Logs ou le contenu du bucket S3.
