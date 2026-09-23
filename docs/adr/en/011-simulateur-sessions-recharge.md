# 011 - Design of the charging session simulator

## Context

The Phase 2 roadmap planned a simulator of realistic charging
sessions, with power depending on the station, a coherent duration,
consumption influenced by temperature, and variable attendance.

## Decision

A simulated session is defined by: an operational connector drawn at
random (connection_id, filtered on is_operational), a start time drawn
from a weighted distribution (peak at 5-8pm, low overnight), a date
drawn uniformly across the range covered by the weather data, a target
energy drawn uniformly between 5 and 30 kWh, and a duration calculated
from the energy, the connector's power, and an efficiency factor
depending on temperature (1.0 if >= 20°C, 0.9 if >= 0°C, 0.75 below).

Attendance is not a stored column: it is an emergent property of the
distribution of generated sessions, observable by aggregation (COUNT
GROUP BY hour), not explicitly modeled.

Architecture: src/simulation/sessions.py, nine functions separating
deterministic logic (facteur_efficacite, calculer_duree,
combiner_date_heure) from random logic (generer_heure_debut,
generer_date_session, generer_energie_cible, generer_session).
warehouse.duckdb_loader.charger_sessions_dans_duckdb loads the
sessions table (session_id auto-incremented via a DuckDB sequence,
connection_id as a foreign key, simple INSERT with no upsert: a
generated session_id can never conflict).

The demonstration batch includes 455 sessions, sized using the coupon
collector problem (n x ln(n) with n = 99 operational connectors ≈
455), to obtain a good probability of covering the full set of
connectors without aiming for a costly exhaustiveness. Observed
result: 78 distinct connectors out of 79 available.

## Why

The chosen scenario (public Parisian stations, evening activity peak)
was selected after several design iterations, setting aside an
initial inconsistent scenario (morning peak, more relevant for
workplace stations than for street stations). The uniform distribution
of the target energy was retained for lack of real data justifying
another distribution shape, an honest choice rather than an
unjustifiable model. Temperature is taken only at the start of the
session, never averaged over its duration, to avoid circularity (the
duration would depend on a temperature that would depend on the
duration), a limitation documented as a future improvement rather than
implemented prematurely.

## Consequences

data/warehouse/electric_mobility.duckdb now contains a fourth table,
sessions, linked to connections (and thus indirectly to poi and meteo
through joins). This dataset constitutes the prerequisite for the
future Data Science part of the roadmap (anomaly detection, attendance
forecasting). Any future regeneration of the session batch can reuse
generer_session as is; the number of sessions to generate will need to
be recalculated if the number of operational connectors changes
significantly.
