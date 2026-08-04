# 011 — Conception du simulateur de sessions de recharge

## Contexte

La roadmap Phase 2 prévoyait un simulateur de sessions de recharge
réalistes, avec puissance selon la borne, durée cohérente, consommation
influencée par la température, et fréquentation variable.

## Décision

Une session simulée est définie par : un connecteur opérationnel tiré
aléatoirement (connection_id, filtré sur is_operational), une heure de
début tirée selon une distribution pondérée (pic 17h-20h, creux nocturne),
une date tirée uniformément dans la plage couverte par les données
météo, une énergie cible tirée uniformément entre 5 et 30 kWh, et une
durée calculée à partir de l'énergie, de la puissance du connecteur et
d'un facteur d'efficacité dépendant de la température (1.0 si >= 20°C,
0.9 si >= 0°C, 0.75 en dessous).

La fréquentation n'est pas une colonne stockée : elle est une propriété
émergente de la distribution des sessions générées, observable par
agrégation (COUNT GROUP BY heure), pas modélisée explicitement.

Architecture : src/simulation/sessions.py, neuf fonctions séparant
logique déterministe (facteur_efficacite, calculer_duree,
combiner_date_heure) et logique aléatoire (generer_heure_debut,
generer_date_session, generer_energie_cible, generer_session).
warehouse.duckdb_loader.charger_sessions_dans_duckdb charge la table
sessions (session_id auto-incrémenté via séquence DuckDB, connection_id
en clé étrangère, INSERT simple sans upsert — un session_id généré ne
peut jamais entrer en conflit).

Le batch de démonstration comprend 455 sessions, dimensionné via le
problème du collectionneur de coupons (n × ln(n) avec n = 99 connecteurs
opérationnels ≈ 455), pour obtenir une bonne probabilité de couverture
de l'ensemble des connecteurs sans viser une exhaustivité coûteuse.
Résultat observé : 78 connecteurs distincts sur 79 disponibles.

## Pourquoi

Le scénario retenu (bornes publiques parisiennes, pic d'activité en
soirée) a été choisi après plusieurs itérations de conception, en
écartant un premier scénario incohérent (pic matinal, plus pertinent
pour des bornes d'entreprise que pour des bornes de rue). La distribution
uniforme de l'énergie cible a été retenue faute de donnée réelle
justifiant une autre forme de distribution — un choix honnête plutôt
qu'une modélisation non justifiable. La température est prise au début
de la session uniquement, jamais moyennée sur sa durée, pour éviter une
circularité (la durée dépendrait d'une température qui dépendrait de la
durée) — limite documentée comme piste d'amélioration future plutôt
qu'implémentée prématurément.

## Conséquences

data/warehouse/electric_mobility.duckdb contient une quatrième table,
sessions, reliée à connections (donc indirectement à poi et meteo par
jointure). Ce jeu de données constitue le prérequis du futur volet Data
Science de la roadmap (détection d'anomalies, prévision de
fréquentation). Toute régénération future du batch de sessions peut
réutiliser generer_session telle quelle ; le nombre de sessions à
générer devra être recalculé si le nombre de connecteurs opérationnels
change significativement.
