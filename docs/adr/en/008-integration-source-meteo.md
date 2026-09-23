# 008 - Integrating a second data source: weather (Open-Meteo)

## Context

The Phase 2 roadmap planned to enrich the project with an additional
data source, to prepare future cross-analyses and practice a join
between two different APIs. Weather was chosen over electricity
production, as the simplest option to integrate and the most directly
usable for this pedagogical goal.

## Decision

Integration of the Open-Meteo API (Historical Weather API, /v1/archive
endpoint), chosen among the alternatives (Meteo-France Open Data,
Weatherbit) for its total lack of authentication and its simplicity of
use, a real gain compared to Open Charge Map, which requires a key.

A manual exploration in a notebook preceded any final code (response
structure, error cases, edge cases: reversed dates, out-of-range
dates, invalid coordinates), confirming that every observed error case
returns a 400 code with an explicit message, never requiring manual
parameter validation ahead of the call.

Architecture: ingestion/meteo.py (API call with retry, orchestration)
and cleaning/meteo.py (extraction into a flat table). The generic
functions already proven on Open Charge Map (generer_nom_fichier,
sauvegarder_local, uploader_s3) were reused as is from common/io.py,
with no duplication (see ADR-007).

The extraction function (extraire_meteo) handles an arbitrary number
of weather variables through zip(*listes_valeurs) combined with
dict(zip(noms_variables, valeurs)), rather than a fixed two-argument
zip(), since Open-Meteo's response structure is organized in columns
(one list per variable) rather than in rows like Open Charge Map.

## Why

Choosing Open-Meteo minimizes integration complexity (no key, no
account) for a specific pedagogical goal: practicing a join between
two heterogeneous sources in Phase 2, without authentication
complexity distracting from that goal. The systematic exploration of
edge cases before writing code confirms the method already established
on Open Charge Map: never assume an API's behavior without having
observed it.

## Consequences

data/raw/ now contains two distinct families of files
(*_extract.json for Open Charge Map, *_meteo.json for weather),
distinguished by the suffix parameter of generer_nom_fichier. The join
between the two sources (by date and geographic proximity) is still to
be designed. It will require handling different granularities (hourly
for weather, instantaneous for stations) and a non-trivial join key,
unlike the exact poi_id key used between poi and connections.
