# 010 - Widening weather coverage to all POIs

## Context

ADR-009 limited weather coverage to a sample of 5 POIs, a deliberate
pedagogical choice for the initial design of the poi/meteo join. This
limit had been flagged as a point to lift if the project needed to
cover more cases.

## Decision

Widening weather ingestion to all 50 POIs in the database, with no
sampling. No architecture change: the same ingestion loop, applied to
the full poi_df rather than to a sample.

## Why

This widening was triggered by the design of the charging session
simulator (Phase 2), which needs to be able to generate realistic
sessions across the entire set of connectors in the database, not just
those of 5 POIs. Postponing this widening until after building the
simulator would have required regenerating every session already
produced. Widening it upstream avoids this duplicate work. The cost
(50 API calls instead of 5) remains negligible against Open-Meteo's
free quota of 10,000 requests per day.

## Consequences

data/warehouse/electric_mobility.duckdb now contains a meteo table
covering all POIs (6000 rows, 50 x 120 hours). The charging session
simulator can rely on complete weather coverage, with no special case
to handle for a POI with no weather data available.
