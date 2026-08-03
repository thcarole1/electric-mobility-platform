# 009 — Jointure poi/meteo : de la proximité géographique à une clé exacte

## Contexte

L'ADR-008 anticipait une jointure poi/meteo par date et proximité
géographique, la table météo n'ayant à l'origine qu'un seul point de
référence (centre de Paris) alors que chaque poi a ses propres
coordonnées précises.

## Décision

Plutôt que d'implémenter un calcul de distance géographique (ex : haversine
en SQL) pour rapprocher a posteriori deux tables indépendantes, l'API
météo est appelée directement sur les coordonnées de chaque poi
concerné (un échantillon de 5 poi, sélection aléatoire avec graine fixe
pour la reproductibilité). Chaque ligne météo porte donc dès
l'ingestion un poi_id exact, éliminant le besoin d'une jointure de
proximité.

La table meteo utilise une clé primaire composite (poi_id, time), avec
poi_id en clé étrangère vers poi(poi_id) — la jointure finale entre poi
et meteo est une jointure exacte sur poi_id, structurellement identique
à celle entre poi et connections.

Architecture ajoutée : common.io.generer_nom_fichier (déjà généralisée
en ADR-007) réutilisée pour nommer chaque extraction météo par poi ;
ingestion.meteo.ingerer_meteo modifiée pour renvoyer le nom de fichier
généré (str | None plutôt que None), permettant à l'appelant de
construire une correspondance {poi_id: nom_fichier} sans reconstruire
cette information depuis le nom du fichier (approche jugée fragile et
écartée). cleaning.meteo.assembler_meteo_multi_poi assemble les
fichiers de plusieurs poi en une seule table plate, en réutilisant
extraire_meteo sans la modifier. warehouse.duckdb_loader.
charger_meteo_dans_duckdb orchestre la création et le chargement de la
table meteo, séparément de charger_openchargemap_dans_duckdb — deux
fonctions distinctes par source de données, cohérent avec la séparation
déjà établie via common/io.py, plutôt qu'une fonction unique mêlant les
deux sources.

## Pourquoi

Le calcul de proximité géographique n'a de valeur que si les points
météo et les poi sont réellement indépendants. En choisissant d'interroger
l'API météo directement aux coordonnées de chaque poi concerné, cette
indépendance disparaît : la correspondance devient triviale et exacte,
sans perte de précision par rapport à une jointure de proximité (qui
aurait de toute façon approximé la position réelle du poi par le point
météo le plus proche). Cette décision a été prise après plusieurs
échanges qui ont exploré, puis écarté, une clé temporelle au niveau du
poi (les poi étant des entités statiques sans horodatage d'usage réel)
— la dimension temporelle reste pertinente uniquement pour une future
jointure entre météo et sessions de recharge simulées (Phase 2, non
construite à ce stade), pas pour la jointure poi/meteo elle-même.

## Conséquences

Cette approche ne s'étend pas telle quelle à un très grand nombre de
poi (un appel API par poi, contre une quota de 10 000 requêtes/jour
chez Open-Meteo) — l'échantillon de 5 poi reste un choix pédagogique
pour ce stade du projet. Si le projet élargit un jour la zone
géographique ou le nombre de poi couverts par la météo, une vraie
jointure de proximité (ou un système de grille de points météo
partagés) redeviendra pertinente et devra être conçue séparément.
