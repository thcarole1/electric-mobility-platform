# 017 - Fixing town normalization: a whitelist of known towns

## Context

ADR-016 had revealed, through the first exploratory dbt model
(`stg_villes_check`), that a POI was incorrectly classified with
`town_normalisee = "SAEMES"`, SAEMES being a Parisian parking
operator, not a town. The normalization introduced in ADR-003 assumed
that any text preceding the `" | "` pattern in `title` was a town, an
assumption invalidated by this case.

## Decision

Added a whitelist (`VILLES_CONNUES`, currently `["Paris"]`) in
`ajouter_town_normalisee` (`cleaning/openchargemap.py`): a value
extracted from `title` is only accepted as a town if it appears in
this list. The SAEMES case now falls into the same handling as the
already known "pompidou" case: `town_normalisee` stays `null` rather
than accepting an unverified value.

The DuckDB database was fully regenerated (poi, connections, meteo,
sessions) rather than incrementally updated, following a DuckDB
limitation encountered while attempting an upsert on `connections`: a
foreign key constraint (`sessions` referencing `connections`)
prevented the upsert of a row already referenced elsewhere, with a
`ConstraintException` error distinct from the case already documented
in ADR-001. Fully regenerating the database from the source files
(`data/raw/`, `data/processed/`) was safer than a fragile workaround
for this limitation.

## Why

A whitelist rather than an exclusion list (an option set aside during
discussion): more robust against future unknown problematic cases, at
the cost of manual upkeep if the project widens its geographic
coverage beyond Paris. The cost of this list remains minimal at the
project's current scale (a single entry), keeping with the principle
of not over-engineering a generic solution (for example the INSEE
municipality reference) for a single real case.

## Consequences

`town_normalisee` now has 2 `null` values (pompidou and SAEMES)
instead of one wrong classification. If the project widens its
geographic area, `VILLES_CONNUES` will need to be extended
accordingly, a point to watch rather than automate as long as the
number of towns stays low. The DuckDB limitation on upserts with a
foreign key referenced by another table is worth keeping in mind for
any future change to the loading pipeline: a full regeneration remains
the most reliable solution in this case, since the data is always
reconstructible from the sources.
