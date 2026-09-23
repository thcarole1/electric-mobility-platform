# 012 - Deploying Open Charge Map ingestion to AWS Lambda

## Context

The Phase 3 roadmap planned to run ingestion on AWS Lambda, the first
step in extending the pipeline toward a more automated, cloud-native
architecture, in preparation for the planned orchestration
(EventBridge/Airflow).

## Decision

Deployment of `ingestion/openchargemap.py` (and its shared module
`common/io.py`) to a Lambda function
(`electric-mobility-ingestion-openchargemap`, Python 3.12 runtime),
with no modification to the business code. Only a new
`lambda_function.py` file (the handler) was added, which builds the S3
client and calls `ingerer_openchargemap(...)` with parameters adapted
to the Lambda environment.

Components put in place:
- A dedicated IAM role (`electric-mobility-lambda-role`), reusing the
  S3 policy already created for the laptop's IAM user
  (`electric-mobility-s3-readwrite`), plus the managed policy
  `AWSLambdaBasicExecutionRole` for writing CloudWatch logs.
- A Lambda Layer (`electric-mobility-ingestion-deps`, 588 KB)
  containing only `requests`, the dependency strictly needed by
  `ingestion/openchargemap.py`. `polars` was explicitly excluded from
  this Layer (219 MB on its own), not being used by this module. A
  separate Layer will be created if `cleaning/` or `warehouse/` are
  ever deployed to Lambda.
- The Open Charge Map API key (`OCM_API_KEY`) is provided via a
  Lambda environment variable, rather than a `.env` file (not
  available natively on Lambda) or AWS Secrets Manager (set aside at
  this stage of the project, like the classic IAM key rotation
  documented previously).
- AWS credentials for `boto3.client("s3")` are no longer provided
  explicitly: the IAM role attached to the function injects them
  automatically into the execution environment.
- Intermediate local storage uses `/tmp` (ephemeral space specific to
  Lambda), explicitly created at handler startup
  (`mkdir(parents=True, exist_ok=True)`), rather than the repository's
  `data/raw/`, which does not exist in this environment.
- The function timeout was raised from 3 seconds (default value) to
  30 seconds, to cover an API call with a possible retry.

## Why

The dependency injection principle applied since the start of the
project (secrets and external clients always received as a parameter,
never built inside business functions) allowed deployment with no
modification at all to `ingestion/openchargemap.py` itself, only the
way these parameters are built changed between the local environment
and Lambda. This deployment also revealed a regression bug that had
stayed invisible locally: `ingerer_openchargemap` never returned the
generated file name (unlike `ingerer_meteo`, already fixed earlier),
the two functions having drifted apart with no test catching it, for
lack of an assertion on the first function's return value.

## Consequences

Two fixes were made to `ingestion/openchargemap.py`, independent of
the Lambda work itself but discovered on this occasion: removal of a
dead import (`from dotenv import load_dotenv`, never called, which
made the import fail on Lambda for lack of this dependency in the
Layer) and addition of the missing `return nom_fichier` (with the
signature updated to `str | None` and the associated tests updated,
following the model of `ingerer_meteo`).

Natural next step: automatic triggering via EventBridge (recurring
schedule), rather than manual invocation from the console. The same
pattern (lightweight Layer, dedicated IAM role, environment variables
for third-party secrets) will be reused if `ingestion/meteo.py` is
deployed to Lambda in turn.
