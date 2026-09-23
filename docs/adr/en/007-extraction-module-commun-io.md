# 007 - Extracting a shared module for generic I/O functions

## Context

When starting the ingestion of a second data source (weather, via
Open-Meteo), three functions already written for Open Charge Map
turned out to be needed identically: generer_nom_fichier,
sauvegarder_local, uploader_s3. They contained no reference specific
to Open Charge Map. Their genericity was already proven by their own
code, not an assumption.

## Decision

Extraction of these three functions into src/common/io.py, imported
from ingestion/openchargemap.py rather than duplicated. The function
generer_nom_fichier was generalized with default-valued suffix and
extension parameters, to stay compatible with existing calls while
allowing a different usage, for example a "meteo" suffix rather than
"extract".

## Why

The general rule on this project is not to factor code out before a
third proven use case, to avoid guessing an abstraction based on an
assumption. Here, the situation is different: the functions already
existed in an already generic, already tested form. The choice was
therefore not "guessing an abstraction", but "stop coupling already
generic code to a module that should not own it". Duplicating this
code into ingestion/meteo.py would have been a cost with no benefit,
since duplication here brings no value, unlike premature factoring on
unproven code.

## Consequences

Any new data source (weather, then future sources) imports its
generic I/O functions from src/common/io.py rather than duplicating
them or importing them from another source module. The associated
tests live in tests/test_common_io.py, separate from the tests
specific to each source.
