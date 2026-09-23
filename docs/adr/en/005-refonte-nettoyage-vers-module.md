# 005 - Refactoring the cleaning notebook into a tested Python module

## Context

The cleaning logic (extracting the poi and connections tables,
normalizing the town field) lived entirely inside the notebook
02_nettoyage_openchargemap.ipynb. This logic had been stable for
several sessions, but remained impossible to unit test and was
coupled to manually running the notebook.

## Decision

Migration to src/cleaning/openchargemap.py, split into five
single-responsibility functions (poi extraction, connections
extraction, town normalization, Parquet save, orchestration), with a
suite of 6 unit tests (tests/test_cleaning_openchargemap.py). The
original notebook is kept, simplified to only call the orchestration
function nettoyer_openchargemap and the save function. It now serves
as a usage example rather than an implementation location.

Unlike the ingestion module (previous refactor, ADR-004), this module
has no external dependencies (no network, no secrets, no AWS
service). Its functions are pure, which made the unit tests
noticeably simpler to write, with no mocking of external libraries
needed. Only the orchestration test requires mocking the internal
sub-functions, for the same isolation reasons as in the ingestion
module.

Generating the timestamped file name was intentionally not factored
out into a shared function with the equivalent one in the ingestion
module. The two modules should not depend on each other, and a single
current use case does not justify an early extraction into a shared
module.

## Why

Same reasoning as for the ingestion module (ADR-004): code stabilized
in a notebook is neither unit testable nor reusable outside that
specific notebook. The migration follows the same "notebook to module
to tests" workflow already planned in the project specification.

## Consequences

The next notebook to migrate (03_chargement_duckdb) will follow the
same approach. If a third module ever needs similar timestamped file
naming, that will be the right moment to consider a shared utility
module (for example src/utils.py), not before.
