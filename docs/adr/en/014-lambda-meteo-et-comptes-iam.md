# 014 - Deploying weather ingestion to Lambda and clarifying IAM accounts

## Context

Following the successful deployment of Open Charge Map ingestion to
Lambda (ADR-012) and the automation of its trigger (ADR-013), the
roadmap planned replicating this pattern for the weather source.
During this session, a mix-up was also identified between several AWS
identities used to administer the project.

## Decision, weather Lambda deployment

Full reuse of the infrastructure already in place for Open Charge Map:
the same Lambda Layer (`electric-mobility-ingestion-deps`, requests
only, `ingestion/meteo.py` needs no additional dependency), the same
execution IAM role (`electric-mobility-lambda-role`), the same S3
bucket. A new handler (`lambda_functions/meteo_handler.py`) invokes
`ingerer_meteo` on a single fixed POI (poi_id 7008, consistent with
the principle of starting simple before widening), with the date range
computed dynamically (`date.today()`) rather than hardcoded, to stay
relevant on every future automatic run. No environment variable is
needed, since Open-Meteo requires no authentication key.

## Decision, clarifying AWS identities

Three distinct identities are now clearly established for this
project:
- **`electric-mobility-pipeline`** (IAM user, minimal S3 access only):
  used exclusively by the application code (local boto3), never to
  browse the console.
- **The root account**: reserved for the rare actions that strictly
  require it (billing, account closure), never used for day-to-day
  administration.
- **`emp-admin`** (new IAM user, AdministratorAccess policy): account
  dedicated to routine human administration of the project (creating
  Lambda/IAM/EventBridge resources), replacing the accidental use of
  the root account that had been happening until now without this
  being identified.

## Why

The weather Lambda deployment confirmed the value of reusing already
proven infrastructure (Layer, role): unlike the first deployment
(ADR-012), no bug was encountered, the function succeeding on its
first test. The distinction between the root account and a dedicated
administrator account follows AWS's standard recommendation (do not
use root for daily tasks); the unintentional use of root until this
session, while with no concrete negative consequence, was an
unidentified deviation from this recommendation. An administrator
account explicitly named for the project rather than an anonymous root
also allows immediate identification of the working context in the
console interface.

## Consequences

Two Lambda functions now run in production on this project, sharing
the same Layer and the same execution role. The habit of
systematically checking the AWS region and the connected identity
before any console action is now explicit. Automating the trigger for
the weather Lambda (EventBridge Scheduler, following the same model as
ADR-013) is still to be set up, not addressed in this session.
