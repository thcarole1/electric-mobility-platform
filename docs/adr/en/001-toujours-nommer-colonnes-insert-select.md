# 011 - Always name columns explicitly in INSERT ... SELECT

## Context

While loading the `connections` table into DuckDB, a query of the
form `INSERT INTO connections SELECT * FROM connections_df` matched
columns by position rather than by name. The column order in
`connections_df` (poi_id, connection_id, ...) did not match the order
declared in the SQL table (connection_id, poi_id, ...), which caused
a foreign key constraint violation.

## Decision

Always list the columns explicitly on both sides of an
`INSERT ... SELECT`, rather than using `SELECT *`.

## Why

`SELECT *` matches columns by position, not by name. If the source
DataFrame and the target table do not have exactly the same column
order, data gets inserted into the wrong columns, sometimes silently,
with no visible error if no constraint catches the mismatch.

## Consequences

Every future INSERT must list columns explicitly on both sides.
Slightly more verbose, but it removes this risk of silent
misalignment.
