# 010 — Élargissement de la couverture météo à l'ensemble des POI

## Contexte

L'ADR-009 limitait la couverture météo à un échantillon de 5 POI,
choix pédagogique assumé pour la conception initiale de la jointure
poi/meteo. Cette limite a été identifiée comme un point à lever si le
projet devait couvrir davantage de cas.

## Décision

Élargissement de l'ingestion météo aux 50 POI de la base, sans
échantillonnage. Aucun changement d'architecture : la même boucle
d'ingestion, appliquée à poi_df complet plutôt qu'à un échantillon.

## Pourquoi

Cet élargissement a été déclenché par la conception du simulateur de
sessions de recharge (Phase 2), qui doit pouvoir générer des sessions
réalistes sur l'ensemble des connecteurs de la base, pas seulement sur
ceux de 5 POI. Reporter cet élargissement à après la construction du
simulateur aurait nécessité de régénérer toutes les sessions déjà
produites — l'élargissement en amont évite ce travail en double. Le
coût (50 appels API au lieu de 5) reste négligeable face au quota
gratuit de 10 000 requêtes/jour d'Open-Meteo.

## Conséquences

data/warehouse/electric_mobility.duckdb contient désormais une table
meteo couvrant tous les POI (6000 lignes, 50 x 120 heures). Le
simulateur de sessions de recharge peut s'appuyer sur une couverture
météo complète, sans cas particulier à gérer pour un POI sans donnée
météo disponible.
