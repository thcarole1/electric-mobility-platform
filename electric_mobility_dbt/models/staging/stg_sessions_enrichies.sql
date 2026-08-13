SELECT
    s.session_id,
    s.connection_id,
    s.debut,
    s.fin,
    s.energie_kwh,
    c.connection_type,
    c.power_kw,
    c.is_fast_charge_capable,
    p.poi_id,
    p.town_normalisee
FROM {{ source('electric_mobility', 'sessions') }} s
JOIN {{ source('electric_mobility', 'connections') }} c ON s.connection_id = c.connection_id
JOIN {{ source('electric_mobility', 'poi') }} p ON c.poi_id = p.poi_id
