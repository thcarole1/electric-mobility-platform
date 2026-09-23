# 019 - S3 data lake: Glue Catalog and Athena for serverless querying

## Context

The Phase 3 roadmap planned Glue Catalog and Athena as a building
block complementary to DuckDB, allowing data to be queried directly on
S3 without loading it into a local database, the last building block
of this phase not yet addressed.

## Decision

Added `common.io.sauvegarder_parquet_s3`, which writes a Polars
DataFrame directly to Parquet on S3 (with no intermediate local step),
receiving an explicit `storage_options` dictionary as a parameter
rather than letting Polars automatically detect credentials from the
environment, a choice motivated by testability and debugging clarity,
consistent with the dependency injection principle already applied to
`uploader_s3` and `client_s3`.

The S3 structure was extended with a `processed/` folder, organized
by table (`processed/poi/`, `processed/connections/`), at the same
level as `raw/`: one Glue table equals one S3 folder, a necessary
condition for the Crawler to work properly.

A Glue Crawler (`electric-mobility-crawler`) scans `processed/` and
automatically detects the schemas of the Parquet files (no inference
needed, unlike CSV or JSON, since the schema is already encoded in the
Parquet format), creating the tables in the `electric_mobility_catalog`
database. A dedicated IAM role (`electric-mobility-glue-crawler-role`)
was created, distinct from the existing Lambda role, with a read-only
policy strictly limited to `s3:GetObject`/`s3:ListBucket` on
`processed/*`, since the Crawler must never write to S3, unlike the
Lambda role, which requires `PutObject`.

Athena is used interactively through the console (workgroup
`primary`), with no dedicated IAM role: queries run with the
permissions of the connected user (`emp-admin`, AdministratorAccess)
rather than a service role, a distinction clarified during the
session (a service role is needed for autonomous processing with no
human user, not for direct interactive use). The Athena query results
folder was configured at the same hierarchical level as
`raw/`/`processed/` (`athena-results/`), since computed results are
neither raw data nor cleaned data.

## Why

The on-demand Crawler (no automatic scheduling) reproduces the
principle already applied to Lambda: validate manually before
automating. Choosing explicit storage_options over automatic detection
by the environment favors testability and debugging clarity at the
cost of slightly more verbosity, an accepted trade-off given the
current comfort level with cloud authentication debugging.

## Consequences

The pipeline now has two equivalent ways to query the cleaned data:
DuckDB locally (fast, single-user) and Athena on S3 (serverless,
accessible to anyone with the right IAM permissions), both coexisting
with neither replacing the other. The `meteo` table was migrated to
`processed/meteo/` in a later session (08/16/2026), completing the
three real tables of the data lake (poi, connections, meteo). A
three-way join across the three tables was validated through Athena.
`sessions` intentionally remains absent from S3, consistent with the
decision not to expose simulated data on this architecture for now.
If the Crawler needs to run frequently, scheduling through EventBridge
(following the model already in place for the Lambda functions) will
be worth considering.
