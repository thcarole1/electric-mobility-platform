SELECT
    connection_type,
    COUNT(*) AS nb_sessions,
    ROUND(SUM(energie_kwh), 1) AS energie_totale_kwh,
    ROUND(AVG(energie_kwh), 1) AS energie_moyenne_kwh
FROM {{ ref('stg_sessions_enrichies') }}
GROUP BY connection_type
ORDER BY nb_sessions DESC
