# 013 — Automatisation du déclenchement via EventBridge Scheduler

## Contexte

La fonction Lambda d'ingestion Open Charge Map (ADR-012) ne pouvait
jusqu'ici être invoquée que manuellement, depuis la console AWS. La
roadmap Phase 3 prévoyait une orchestration planifiée (EventBridge ou
Airflow/MWAA).

## Décision

Mise en place d'un déclenchement quotidien automatique via **EventBridge
Scheduler** (le service moderne dédié à la planification, préféré aux
"EventBridge Rules" classiques qui ciblent plutôt la réaction à de vrais
événements). Le schedule (`electric-mobility-ingestion-openchargemap-daily`)
invoque la fonction Lambda tous les jours à 4h00, heure de Paris
(`cron(0 4 * * ? *)`), avec une fenêtre de flexibilité de 15 minutes
(le service AWS ne garantit pas un déclenchement à la seconde près, par
design, pour répartir la charge sur sa plateforme).

Une politique de retry légère (2 tentatives, âge maximum de l'événement
24h) est configurée côté EventBridge, distincte et complémentaire du
retry déjà géré dans `appeler_api_openchargemap` : EventBridge retente
si l'invocation elle-même échoue (Lambda indisponible), le code Python
retente si l'appel à l'API Open Charge Map échoue temporairement
(5xx/429) — deux niveaux de résilience, à deux étages différents de la
chaîne.

Le service a créé automatiquement un rôle IAM dédié
(`Amazon_EventBridge_Scheduler_LAMBDA_...`), distinct du rôle
d'exécution de la fonction Lambda elle-même (`electric-mobility-lambda-role`) —
ce rôle n'autorise qu'à invoquer la fonction cible, sans aucun accès à
S3 ou aux autres services.

## Pourquoi

EventBridge Scheduler a été préféré aux Rules classiques pour sa
simplicité d'usage (raisonnement direct en heure locale plutôt qu'en
UTC, interface dédiée à la planification pure). La séparation entre
retry applicatif et retry d'infrastructure reflète une distinction
réelle : un échec réseau vers l'API tierce n'a rien à voir avec un
échec d'invocation Lambda, les deux méritent une gestion indépendante.
Aucune dead-letter queue n'a été mise en place à ce stade — jugée
disproportionnée pour ce volume d'invocations (une par jour), notée
comme amélioration future si le besoin de traçabilité des échecs
augmentait.

## Conséquences

Le pipeline d'ingestion Open Charge Map tourne désormais de façon
totalement autonome, sans intervention manuelle — validé en conditions
réelles le 12/08/2026 (fichier `2026-08-12_131843_paris_extract.json`
créé automatiquement sur S3 lors d'un test avec cron temporairement
ajusté, avant remise à la valeur définitive de 4h00).

Une erreur de région a été commise lors de la première tentative de
création de la fonction Lambda (déployée par défaut en us-east-1
N. Virginia au lieu de eu-west-3 Paris, la région du reste de
l'infrastructure) — détectée seulement au moment de connecter le
Schedule à sa cible, la fonction étant invisible depuis une région
différente. La fonction et sa Layer ont été recréées dans la bonne
région ; la ressource erronée a été supprimée. Point de vigilance pour
toute future ressource AWS : vérifier la région affichée en console
avant de créer quoi que ce soit, pas seulement au moment de connecter
les ressources entre elles.

La même approche (EventBridge Scheduler, retry à deux niveaux) sera
réutilisée si l'ingestion météo est déployée sur Lambda à son tour.
