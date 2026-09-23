# 004 - Refactoring the ingestion notebook into a tested Python module

## Context

The ingestion logic (API call, local save, S3 upload) lived entirely
inside the notebook 01_exploration_openchargemap.ipynb. This logic had
been stable for several sessions, but remained impossible to unit
test and not reusable as is, for example not callable from a future
Lambda function.

## Decision

Migration to `src/ingestion/openchargemap.py`, split into five
single-responsibility functions (file name generation, API call with
retry, local save, S3 upload, orchestration), with a suite of 12 unit
tests (`tests/test_openchargemap.py`) covering the success and failure
cases of each function. The original notebook is kept, simplified to
only call the orchestration function. It now serves as a usage
example rather than an implementation location.

Two guiding principles shaped this refactor:
- No function in the module loads its own secrets (API key, AWS
  credentials) or configures its own logging. Everything is received
  as a parameter or delegated to the caller, to stay testable and
  portable to other execution contexts, Lambda in particular.
- The retry logic for temporary errors (5xx, 429) lives inside the
  API call function itself, not in the orchestration, so it stays
  reusable independently of the calling context.

## Why

Code stabilized in a notebook is neither unit testable nor reusable
outside that specific notebook, nor compatible with future execution
on Lambda. The migration follows the "notebook to module to tests"
workflow already planned in the project specification.

## Consequences

The next notebooks (02_nettoyage, 03_chargement_duckdb) will follow
the same migration once their logic stabilizes. Any new testable
feature must now follow this same dependency injection principle
(secrets, external clients) rather than loading them internally.
