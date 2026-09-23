# 015 - Automating the weather ingestion trigger

## Context

Following the deployment of the weather Lambda function (ADR-014),
its trigger still needed to be automated, following the model already
established for Open Charge Map (ADR-013).

## Decision

Creation of the `electric-mobility-ingestion-meteo-daily` schedule,
with exactly the same configuration as the Open Charge Map one: daily
cron at 4:00am Paris time (`cron(0 4 * * ? *)`), 15-minute flexibility
window, retry policy of 2 attempts, IAM role created automatically by
EventBridge Scheduler. Unlike the Open Charge Map trigger, no
immediate manual test was performed after creating the schedule, the
first automatic run the following day was accepted as sufficient
validation, since the mechanism had already been proven.

Both sources (Open Charge Map, weather) are triggered at the same
time, with no technical reason to synchronize or stagger them: the two
functions are independent, with no data dependency at execution time.

## Why

Replicating an already validated pattern, with no unnecessary
variation, reduces the risk of error and the configuration cognitive
load. The absence of an immediate manual test reflects confidence
gained after the successful validation of the same mechanism on Open
Charge Map (ADR-013): checking it again identically would have
brought no new information.

## Consequences

Both data sources of the project now run entirely autonomously, with
no daily manual intervention. Verifying the first automatic run
(expected on 08/14/2026 at 4:00am) still needs to be confirmed in a
future session, by checking CloudWatch Logs or the content of the S3
bucket.
