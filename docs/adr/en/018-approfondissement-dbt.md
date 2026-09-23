# 018 - Going further with dbt: model composition, custom tests, documentation

## Context

Following the introduction of dbt (ADR-016) with two simple staging
models, this session aimed to practice the tool's more advanced
capabilities: model composition, custom business tests, automatically
generated documentation.

## Decision

Added two new models forming a composition chain:
`stg_sessions_enrichies` (a join of sessions/connections/poi,
referenced via `source()`) and `indicateurs_par_type_connecteur`
(`models/marts/`), which aggregates the first one via
`{{ ref('stg_sessions_enrichies') }}` rather than duplicating the
join. A custom test (`tests/assert_fin_apres_debut.sql`) checks that
no session has an end date earlier than its start date, a physical
property of the simulator (ADR-011) verified manually until now,
never formalized as a reproducible automated test.

dbt documentation (`dbt docs generate` / `dbt docs serve`) was
generated and explored, revealing the project's full lineage graph
(sources -> stg_sessions_enrichies -> indicateurs_par_type_connecteur).

A configuration bug was found and fixed: an empty `models:` section in
`dbt_project.yml` (a leftover from cleaning up the `example/` folder
in ADR-016) prevented dbt from correctly detecting dependencies
through `ref()`, with a misleading error message ("ref() placed
within a conditional block") unrelated to the real cause.

## Why

Model composition through `ref()` is dbt's most distinctive
mechanism, separate from simply declaring sources: it allows factoring
out a shared transformation (the sessions/connections/poi join) for
multiple future indicators, with no duplicated SQL logic, the SQL
equivalent of the principle already applied in Python with
`common/io.py`. A custom test complements the generic tests
(`not_null`, `unique`) to express a business rule specific to the
domain, one that no standard test could capture.

## Consequences

This session was carried out directly on `main`, with no dedicated
branch, a minor deviation from the project's usual discipline, with no
real consequence given the low-risk nature of the changes (additional
dbt models, no modification of the production Python pipeline). The
dbt project now has 4 models and 4 tests, with documentation
reproducible at any time via `dbt docs generate`. Other mart models
can follow the same composition pattern (reusing
`stg_sessions_enrichies` for other analysis angles: by town, by hour,
by temperature) without rewriting the base join.
