# 027 - Schema validation at the source

## Context

The incident documented in ADR-026 (type contamination on `poi_id`,
caused by the JSON serialization of Airflow's XCom mechanism) had only
been detected when queried in Athena, several days after it was
actually produced. No mechanism existed to catch this kind of
inconsistency at the moment it occurs, before corrupted data reaches
the data lake.

## Decision

Added a validation module (`src/validation/schema.py`), providing a
generic `valider_schema` function that compares the actual schema of a
Polars DataFrame to an expected schema, and raises an explicit
exception (`SchemaValidationError`) on a type mismatch or a missing
column. This validation is applied right before writing the weather
DataFrame, on both execution paths of the pipeline (`run_pipeline.py`
and the MWAA DAG), immediately after it is built.

## Why

The validation was placed at the **source**, before writing the data,
rather than downstream as dbt tests on data already present in the
data lake. This choice directly reflects the lesson from the previous
incident: detecting it after the fact would have allowed noticing the
problem faster than an end user stumbling on it by chance, but would
not have prevented corrupted data from passing through S3 and
potentially being consumed before a fix. Validating at the source
stops the pipeline before the problem spreads, with an error message
that precisely identifies the column and the type mismatch involved.

A generic function, rather than table-specific validations, was
chosen to limit duplication and make it easy to apply to other tables
in the project if needed, without rewriting schema comparison logic
each time.

## Consequences

Integrating this into the MWAA DAG required an additional check: the
new `validation/` module had to be explicitly added to the
`build_mwaa_plugins.sh` script, which copies each source module
individually rather than all of `src/`. This check helped avoid a
regression that would only have become visible at the time of a
future MWAA deployment, a detection delay comparable to the one from
the original incident that this validation is precisely meant to
avoid.

A test explicitly reproducing the conditions of the original incident
(a dictionary key provided as a string, simulating XCom's behavior)
was added to the test suite, guaranteeing that a future regression on
this specific point would be caught before any deployment, through the
CI already in place (ADR-024).

This scope remains limited to the weather table, the only one
involved in the incident that motivated this decision. Extending it
to `poi` and `connections` was not judged necessary for now, since
neither of these two tables is ever passed through an intermediate
serialization mechanism comparable to XCom.
