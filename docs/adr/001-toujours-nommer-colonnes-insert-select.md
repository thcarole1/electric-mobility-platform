# 011 — Toujours nommer les colonnes explicitement dans INSERT ... SELECT

## Contexte

Lors du chargement de la table `connections` dans DuckDB, une requête
`INSERT INTO connections SELECT * FROM connections_df` a fait correspondre
les colonnes par position plutôt que par nom. L'ordre des colonnes dans
`connections_df` (poi_id, connection_id, ...) ne correspondait pas à
l'ordre déclaré dans la table SQL (connection_id, poi_id, ...), ce qui a
provoqué une violation de contrainte de clé étrangère.

## Décision

Toujours lister explicitement les colonnes des deux côtés d'un
`INSERT ... SELECT`, plutôt que d'utiliser `SELECT *`.

## Pourquoi

`SELECT *` fait correspondre les colonnes par position, pas par nom.
Si le DataFrame source et la table cible n'ont pas exactement le même
ordre de colonnes, les données sont insérées dans les mauvaises colonnes
— parfois silencieusement, sans erreur visible si aucune contrainte ne
détecte l'incohérence.

## Conséquences

Chaque futur INSERT devra lister les colonnes explicitement des deux
côtés. Légèrement plus verbeux, mais élimine ce risque de désalignement
silencieux.
