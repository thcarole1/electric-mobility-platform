SELECT
    connection_type,
    COUNT(*) AS nb_connecteurs,
    ROUND(AVG(power_kw), 1) AS puissance_moyenne_kw,
    SUM(CASE WHEN is_operational THEN 1 ELSE 0 END) AS nb_operationnels
FROM {{ source('electric_mobility', 'connections') }}
GROUP BY connection_type
ORDER BY nb_connecteurs DESC
