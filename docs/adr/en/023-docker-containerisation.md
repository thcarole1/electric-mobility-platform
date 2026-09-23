# 023 - Containerizing the pipeline with Docker

## Context

After setting up Terraform (ADR-022), the second building block of
Phase 5 (industrialization) was to containerize the local pipeline
(`run_pipeline.py`), to demonstrate a reproducible containerization
skill, independent of the execution environment.

## Decision

Building a two-stage `Dockerfile` (multi-stage build): a first stage
(`builder`) installs the project and its Python dependencies, a second
stage, starting from a minimal image, only retrieves the result of
that installation. AWS credentials and the API key are never copied
into the image; they are injected at runtime via
`docker run --env-file`, with a local file excluded from the
repository (`.gitignore` broadened to `.env*`).

## Why

Multi-stage build is a standard image size reduction practice, tested
in this project: the observed gain was marginal (842 MB versus
827 MB), because the main libraries (`polars`, `duckdb`, `pyarrow`)
are distributed as precompiled wheels, with no build tools needing to
be removed between the two stages. The technique is kept despite this
limited gain, as a recognized good practice rather than for its
measured benefit here alone.

Injecting credentials at runtime rather than including them in the
image follows the same security principle applied across the whole
project: no secret should ever be part of a built or versioned
artifact.

## Consequences

Two adjustments were needed compared to running in a classic local
environment:
- `python-dotenv`, present only in the project's development
  dependencies, had to be explicitly added to the image, since the
  source code calls `load_dotenv()` unconditionally
- The `data/raw/` and `data/warehouse/` folders, never created by the
  code itself (`sauvegarder_local` assumes they already exist), had to
  be explicitly created in the `Dockerfile`, a behavior already
  identified and documented during the initial deployment of the
  Lambda functions

A diagnostic incident also illustrated a source of error outside the
code and Docker configuration itself: an active VPN on the host
machine caused a systematic SSL handshake timeout toward the weather
API from the container, while DNS resolution and the TCP connection
succeeded normally. Disabling the VPN immediately fixed the problem,
confirming that the cause was environmental, not application-related.

The containerized pipeline produces results strictly identical to the
local run (50 POI, 99 connections, 6000 weather rows, 455 sessions),
validating the reproducibility sought by this containerization.
