# 006 — Refonte du notebook de chargement DuckDB en module Python testé

## Contexte

La logique de chargement (création des tables poi et connections, upsert
avec gestion de la contrainte de clé étrangère) vivait entièrement dans
le notebook 03_chargement_duckdb.ipynb. Cette logique était stabilisée
depuis plusieurs sessions, mais restait non testable unitairement.

## Décision

Migration vers src/warehouse/duckdb_loader.py, découpé en cinq fonctions
à responsabilité unique (création et insertion séparées pour poi et
connections, plus une orchestration), avec une suite de 8 tests
unitaires (tests/test_warehouse_duckdb_loader.py). Le notebook original
est conservé, simplifié pour n'appeler que la fonction d'orchestration
charger_openchargemap_dans_duckdb — il sert désormais d'exemple d'usage,
plus de lieu d'implémentation.

La connexion DuckDB (con) est reçue en paramètre par chaque fonction,
jamais créée en interne — même principe d'injection de dépendance que
pour la clé API et le client S3 dans le module ingestion.

Une réflexion sur la programmation orientée objet a précédé cette
refonte : une classe aurait pu regrouper la connexion et les méthodes
de chargement, mais a été écartée à ce stade — trop peu de méthodes et
un seul état partagé (la connexion) pour justifier ce changement de
paradigme, et le style fonctionnel reste plus simple à tester.

Contrairement aux appels réseau et à S3 (module ingestion), DuckDB en
mémoire (:memory:) est rapide, locale et sans risque : les tests
utilisent donc une vraie connexion DuckDB via une fixture pytest
personnalisée, plutôt qu'un mock. Le critère retenu pour décider de
mocker ou non une dépendance n'est pas sa position (interne/externe à
la fonction), mais sa nature : lente, distante ou coûteuse → mock ;
rapide, locale et fiable → vraie instance.

## Pourquoi

Même raisonnement que pour les modules ingestion (ADR-004) et cleaning
(ADR-005) : le code stabilisé en notebook n'est ni testable
unitairement, ni réutilisable en dehors de ce notebook précis. La
migration suit le même workflow "notebook → module → tests" prévu dès
le Cahier des charges.

## Conséquences

Les trois notebooks du pipeline actuel (ingestion, nettoyage,
chargement) sont désormais tous adossés à des modules testés. Le
critère de mocking établi ici (nature de la dépendance, pas sa
position) s'applique à tout futur module du projet — y compris les
futures briques AWS (Lambda, Athena) où la même question se reposera.
