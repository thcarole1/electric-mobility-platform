# 006 - Refactoring the DuckDB loading notebook into a tested Python module

## Context

The loading logic (creating the poi and connections tables, upsert
with foreign key constraint handling) lived entirely inside the
notebook 03_chargement_duckdb.ipynb. This logic had been stable for
several sessions, but remained impossible to unit test.

## Decision

Migration to src/warehouse/duckdb_loader.py, split into five
single-responsibility functions (separate creation and insertion for
poi and connections, plus one orchestration function), with a suite
of 8 unit tests (tests/test_warehouse_duckdb_loader.py). The original
notebook is kept, simplified to only call the orchestration function
charger_openchargemap_dans_duckdb. It now serves as a usage example
rather than an implementation location.

The DuckDB connection (con) is received as a parameter by every
function, never created internally, following the same dependency
injection principle already used for the API key and the S3 client in
the ingestion module.

A reflection on object-oriented design preceded this refactor: a
class could have grouped the connection and the loading methods
together, but this was set aside at this stage. Too few methods and a
single shared state (the connection) did not justify this paradigm
shift, and a functional style remains simpler to test.

Unlike network calls and S3 (ingestion module), an in-memory DuckDB
connection (:memory:) is fast, local, and low risk: the tests
therefore use a real DuckDB connection through a custom pytest
fixture, rather than a mock. The criterion used to decide whether to
mock a dependency is not its position (internal or external to the
function), but its nature: slow, remote, or costly means mock; fast,
local, and reliable means a real instance.

## Why

Same reasoning as for the ingestion (ADR-004) and cleaning (ADR-005)
modules: code stabilized in a notebook is neither unit testable nor
reusable outside that specific notebook. The migration follows the
same "notebook to module to tests" workflow already planned in the
project specification.

## Consequences

The three notebooks of the current pipeline (ingestion, cleaning,
loading) are now all backed by tested modules. The mocking criterion
established here (nature of the dependency, not its position) applies
to any future module in the project, including future AWS building
blocks (Lambda, Athena) where the same question will come up again.
