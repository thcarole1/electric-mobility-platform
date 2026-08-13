SELECT
    town_normalisee,
    COUNT(*) AS nb_poi
FROM {{ source('electric_mobility', 'poi') }}
GROUP BY town_normalisee
ORDER BY nb_poi DESC
