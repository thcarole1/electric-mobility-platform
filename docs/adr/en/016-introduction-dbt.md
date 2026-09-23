# 016 - Introducing dbt to structure SQL transformations

## Context

The Phase 3 roadmap planned dbt as a versioned SQL transformation
tool, following an analysis of the France 2026 Data Engineer job
market (dbt cited alongside Airflow among the most sought-after
skills).

## Decision

Initialization of a dbt project (`electric_mobility_dbt/`) connected
directly to the DuckDB database already in production
(`data/warehouse/electric_mobility.duckdb`), via the `dbt-duckdb`
adapter. dbt is added as a transformation layer on top of the tables
already loaded by `warehouse/duckdb_loader.py`. It replaces neither
DuckDB nor the existing Python pipeline; it structures the SQL
analyses that were until now written by hand in notebooks.

Two initial staging models were created: `stg_villes_check`
(exploratory, revealed an unanticipated data issue, an operator named
"SAEMES" wrongly classified as a town in `town_normalisee`, an edge
case not covered by the normalization from ADR-003) and
`stg_connecteurs_par_type` (a reliable indicator, with no dependency
on fragile data), along with generic dbt tests (`not_null`, `unique`).

`dbt-duckdb` was added to the `dev` dependencies of `pyproject.toml`,
never used by the production code in `src/`, consistent with the
principle already applied to `jupyterlab` and `python-dotenv`.

## Why

dbt materializes its models as views by default rather than tables (no
duplicated data, always up to date), a choice kept for these first
exploratory models; materializing as a table remains available if
performance were to justify it later. The first model
(`stg_villes_check`) confirmed the value of dbt beyond mere
structuring: a simple exploration query immediately revealed
mis-classified data that would have gone unnoticed in an ad hoc
notebook usage.

## Consequences

The dbt project lives in its own subfolder, with its connection
configuration (`~/.dbt/profiles.yml`) intentionally not versioned,
like the other local secrets/configurations of the project. The
"SAEMES" case identified in `stg_villes_check` still needs to be
fixed (either in the existing Python normalization, or through a
dedicated dbt rule), not addressed in this session, noted as an open
item. Other models can follow as analysis needs arise, with no
obligation to migrate everything from the existing notebooks at once.
