# 008 — Intégration d'une deuxième source de données : météo (Open-Meteo)

## Contexte

La roadmap Phase 2 prévoyait l'enrichissement du projet avec une source
de données supplémentaire, pour préparer de futures analyses croisées
et pratiquer une jointure entre deux sources API différentes. Météo a
été retenue plutôt que production électrique, comme option la plus
simple à intégrer et la plus directement exploitable pour cet objectif
pédagogique.

## Décision

Intégration de l'API Open-Meteo (Historical Weather API, endpoint
/v1/archive), choisie parmi les alternatives (Météo-France Open Data,
Weatherbit) pour son absence totale d'authentification et sa simplicité
d'usage — un vrai gain face à Open Charge Map qui nécessite une clé.

Une exploration manuelle en notebook a précédé toute écriture de code
définitif (structure de réponse, cas d'erreur, cas limites : dates
inversées, dates hors plage, coordonnées invalides), confirmant que
tous les cas d'erreur observés renvoient un code 400 avec message
explicite, sans jamais nécessiter de validation manuelle des paramètres
en amont de l'appel.

Architecture : ingestion/meteo.py (appel API avec retry, orchestration)
et cleaning/meteo.py (extraction en table plate). Les fonctions
génériques déjà éprouvées sur Open Charge Map (generer_nom_fichier,
sauvegarder_local, uploader_s3) ont été réutilisées telles quelles
depuis common/io.py, sans duplication (voir ADR-007).

La fonction d'extraction (extraire_meteo) gère un nombre arbitraire de
variables météo grâce à zip(*listes_valeurs) combiné à
dict(zip(noms_variables, valeurs)), plutôt qu'un zip() à deux arguments
fixes — la structure de réponse d'Open-Meteo étant organisée en
colonnes (une liste par variable) et non en lignes comme Open Charge
Map.

## Pourquoi

Le choix d'Open-Meteo minimise la complexité d'intégration (pas de
clé, pas de compte) pour un objectif pédagogique précis : pratiquer une
jointure entre deux sources hétérogènes en Phase 2, sans que la
complexité d'authentification ne détourne l'attention de cet objectif.
L'exploration systématique des cas limites avant l'écriture du code
confirme la méthode déjà établie sur Open Charge Map : ne jamais
supposer le comportement d'une API sans l'avoir observé.

## Conséquences

data/raw/ contient désormais deux familles de fichiers distincts
(*_extract.json pour Open Charge Map, *_meteo.json pour la météo),
distingués par le paramètre suffixe de generer_nom_fichier. La
jointure entre les deux sources (par date et proximité géographique)
reste à concevoir — elle nécessitera de traiter des granularités
différentes (horaire pour la météo, instantané pour les bornes) et une
clé de jointure non triviale, contrairement à la clé exacte poi_id
utilisée entre poi et connections.
