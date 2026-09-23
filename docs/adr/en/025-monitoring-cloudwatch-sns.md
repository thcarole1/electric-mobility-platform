# 025 - Pipeline observability: CloudWatch Alarms and SNS notifications

## Context

Until now, no mechanism made it possible to know whether the daily
ingestion (Lambda functions triggered by EventBridge) had failed,
short of manually checking CloudWatch logs or the content of the data
lake. This lack of active monitoring was a significant limitation
compared to the practices expected of a production pipeline.

## Decision

Setup of a dedicated Terraform module, `monitoring`, distinct from the
`ingestion` module it watches: two CloudWatch alarms (one per Lambda
function) triggered as soon as a run fails (`metric_name = "Errors"`,
threshold strictly greater than zero, one-hour evaluation window),
linked to a single SNS topic with an email subscription. The names of
the Lambda functions to watch are passed to the `monitoring` module
through the output/variable mechanism already used between the `iam`
and `ingestion` modules, rather than redeclared as hardcoded values.

## Why

The separation into a distinct module follows the principle already
applied across the whole infrastructure: a module groups resources
that are born and evolve together. Monitoring has no functional
dependency on ingestion: removing it would not affect the execution of
the Lambda functions themselves in any way, only the visibility into
their proper functioning. This split guarantees that an error in the
monitoring configuration can never compromise the operation of the
pipeline it watches.

The trigger threshold (any error, no tolerance) was chosen in line
with how often these functions run (once a day): unlike a
high-frequency service where a few isolated errors would be
tolerable, each missed daily run represents a data loss that cannot be
automatically recovered, justifying an immediate alert on the very
first occurrence.

## Consequences

The full mechanism was validated end to end by manually triggering the
alarm (`aws cloudwatch set-alarm-state`), confirming actual receipt of
the email notification before resetting it to normal state, a check
judged necessary rather than assuming the Alarm to SNS to email chain
worked with no concrete proof.

This scope remains deliberately limited to detecting execution
failures (`Errors`): the duration (`Duration`) and throttling
(`Throttles`) metrics, also natively available for Lambda, were not
instrumented, this type of anomaly being judged less critical than a
complete execution failure for this pipeline. No monitoring was
otherwise set up on the MWAA environment or the Glue Crawler, these
components not running continuously within the current scope of the
project.

## Incident: orphaned state lock caused by a variable with no value passed to CI

Integrating this module revealed an incident related to the existing
`terraform-plan.yml` workflow (ADR-024): the `alert_email` variable,
with no default value and provided only through `terraform.tfvars` (a
local file, never versioned), was not passed to the CI workflow.
Terraform, receiving no value for this required variable, attempted an
interactive prompt that is impossible in an automated execution
environment, blocking the run with no explicit error message for over
ten minutes.

This blockage had a secondary consequence: the native S3 State lock
(`terraform.tfstate.tflock`), acquired at the start of the run, was
never released by the stuck process, preventing any new run, local or
via CI, until it was manually deleted after checking that no
legitimate operation was in progress. Fixed by passing the variable to
the workflow through a new GitHub secret (`ALERT_EMAIL`), following
the same mechanism already in place for `ocm_api_key`. This incident
highlights the need to systematically check, whenever a new Terraform
variable is added, that its value is actually reachable from every
execution environment (local and CI), not just the one used when it
was introduced.
