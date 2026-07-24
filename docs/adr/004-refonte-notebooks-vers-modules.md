# 004 — Refonte du notebook d'ingestion en module Python testé

## Contexte

La logique d'ingestion (appel API, sauvegarde locale, upload S3) vivait
entièrement dans le notebook 01_exploration_openchargemap.ipynb. Cette
logique était stabilisée (aucun changement depuis plusieurs sessions),
mais restait non testable unitairement et non réutilisable telle quelle
(par exemple, non appelable depuis une future fonction Lambda).

## Décision

Migration vers `src/ingestion/openchargemap.py`, découpé en cinq
fonctions à responsabilité unique (génération de nom de fichier, appel
API avec retry, sauvegarde locale, upload S3, orchestration), avec une
suite de 12 tests unitaires (`tests/test_openchargemap.py`) couvrant les
cas de succès et d'échec de chaque fonction. Le notebook original est
conservé, simplifié pour n'appeler que la fonction d'orchestration —
il sert désormais d'exemple d'usage, plus de lieu d'implémentation.

Deux principes structurants ont guidé cette refonte :
- Aucune fonction du module ne charge ses propres secrets (clé API,
  identifiants AWS) ou ne configure son propre logging — tout est reçu
  en paramètre ou délégué à l'appelant, pour rester testable et portable
  vers d'autres contextes d'exécution (Lambda, notamment).
- La logique de retry sur erreurs temporaires (5xx, 429) vit dans la
  fonction d'appel API elle-même, pas dans l'orchestration, pour rester
  réutilisable indépendamment du contexte d'appel.

## Pourquoi

Le code stabilisé en notebook n'est ni testable unitairement, ni
réutilisable ailleurs que dans ce notebook précis, ni compatible avec
une future exécution sur Lambda. La migration correspond au workflow
"notebook → module → tests" prévu dès le Cahier des charges.

## Conséquences

Les prochains notebooks (02_nettoyage, 03_chargement_duckdb) suivront
la même migration une fois leur logique stabilisée. Toute nouvelle
fonctionnalité testable doit désormais suivre ce même principe
d'injection de dépendances (secrets, clients externes) plutôt que de
les charger en interne.
