SELECT
    session_id,
    debut,
    fin
FROM {{ ref('stg_sessions_enrichies') }}
WHERE fin < debut
