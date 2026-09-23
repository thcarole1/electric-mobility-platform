# 020 - Local orchestration script for the full pipeline

## Context

Running the pipeline (ingestion, cleaning, DuckDB loading, weather,
sessions) relied entirely on manual execution, notebook by notebook,
in an order known only to the author and never formalized, a gap
explicitly identified in a previous session (see decisions-log.md,
08/16/2026), distinct from the Lambda/EventBridge automation, which
only covers the ingestion step.

## Decision

Creation of `run_pipeline.py`, at the root of the repository, which
chains the entire pipeline: Open Charge Map ingestion (a new API
call, not reusing an existing file), cleaning, loading poi/connections
into DuckDB, weather ingestion (looping over every POI in the cleaned
DataFrame, no sampling), weather assembly and loading, generation and
loading of 455 simulated sessions.

The path of the target DuckDB database can be set via a command-line
argument (`--db`), with the production database as the default value.
This parameter allows testing the script on an isolated database
without affecting production data, used for the initial validation of
this script (`test_pipeline.duckdb` database, deleted after
verification, never versioned).

## Why

This script serves a dual purpose: immediately closing the
orchestration gap identified without waiting for the heavier setup of
MWAA (which requires a refresher on AWS networking not yet undertaken),
and forming a natural basis for translation into a future Airflow DAG,
each step of the script corresponding to a candidate task. Making the
database path configurable follows the principle already applied
elsewhere in the project: always validate a change on isolated data
before considering it reliable for production.

## Consequences

The full pipeline can now run with a single command
(`python run_pipeline.py`), in about 40 seconds end to end, observed
under real conditions during the validation test (50 POI, 99
connections, 6000 weather rows, 455 sessions). This script remains a
local tool, with no automated execution or scheduling; unlike the
Lambda functions, it must be launched manually. Translating it into an
Airflow/MWAA DAG, or integrating it into an EventBridge schedule,
remains to be done in a future session.
