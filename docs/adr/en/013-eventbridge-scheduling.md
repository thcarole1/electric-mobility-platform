# 013 - Automating triggering via EventBridge Scheduler

## Context

The Open Charge Map ingestion Lambda function (ADR-012) could until
now only be invoked manually, from the AWS console. The Phase 3
roadmap planned a scheduled orchestration (EventBridge or
Airflow/MWAA).

## Decision

Setup of an automatic daily trigger via **EventBridge Scheduler** (the
modern service dedicated to scheduling, preferred over classic
"EventBridge Rules", which target reacting to real events instead).
The schedule
(`electric-mobility-ingestion-openchargemap-daily`) invokes the Lambda
function every day at 4:00am Paris time (`cron(0 4 * * ? *)`), with a
15-minute flexibility window (the AWS service does not guarantee
second-precise triggering, by design, to spread the load across its
platform).

A light retry policy (2 attempts, maximum event age of 24h) is
configured on the EventBridge side, distinct and complementary to the
retry already handled in `appeler_api_openchargemap`: EventBridge
retries if the invocation itself fails (Lambda unavailable), the
Python code retries if the call to the Open Charge Map API fails
temporarily (5xx/429), two levels of resilience, at two different
stages of the chain.

The service automatically created a dedicated IAM role
(`Amazon_EventBridge_Scheduler_LAMBDA_...`), distinct from the
execution role of the Lambda function itself
(`electric-mobility-lambda-role`). This role only allows invoking the
target function, with no access to S3 or other services.

## Why

EventBridge Scheduler was preferred over classic Rules for its ease of
use (direct reasoning in local time rather than UTC, an interface
dedicated purely to scheduling). The separation between application
retry and infrastructure retry reflects a real distinction: a network
failure toward the third-party API has nothing to do with a Lambda
invocation failure, both deserve independent handling. No dead-letter
queue was set up at this stage, judged disproportionate for this
volume of invocations (one per day), noted as a future improvement if
the need for failure traceability grew.

## Consequences

The Open Charge Map ingestion pipeline now runs completely
autonomously, with no manual intervention, validated under real
conditions on 08/12/2026 (file
`2026-08-12_131843_paris_extract.json` automatically created on S3
during a test with the cron temporarily adjusted, before resetting it
to the final value of 4:00am).

A region mistake was made during the first attempt to create the
Lambda function (deployed by default in us-east-1 N. Virginia instead
of eu-west-3 Paris, the region of the rest of the infrastructure),
detected only when connecting the Schedule to its target, since the
function was invisible from a different region. The function and its
Layer were recreated in the right region; the wrong resource was
deleted. Point of caution for any future AWS resource: check the
region shown in the console before creating anything, not only when
connecting resources together.

The same approach (EventBridge Scheduler, two-level retry) will be
reused if weather ingestion is deployed to Lambda in turn.
