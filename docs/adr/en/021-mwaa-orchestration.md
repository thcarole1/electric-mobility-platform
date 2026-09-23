# 021 - Airflow/MWAA orchestration: setting up and resolving a chain of network and application blockers

## Context

Following ADR-020 (the `run_pipeline.py` script) and the Phase 3
roadmap, Airflow/MWAA remained the last cloud orchestration building
block not yet addressed. Unlike the other services in the project
(Lambda, Glue, Athena), MWAA turned out to be the longest and most
complex undertaking of the entire project, spread across 6 sessions
(08/17 to 08/25), with about ten environment creation attempts.

## Decision

Translation of the pipeline (`run_pipeline.py`) into an Airflow DAG
(`mwaa_dags/pipeline_electric_mobility.py`), with 4 sequential tasks
(Open Charge Map ingestion, cleaning + S3 upload, weather ingestion,
assembly + S3 upload), passing data between tasks through XCom (S3
paths) rather than through in-memory DataFrames. Deployment on an
MWAA environment (`mw1.micro`, Airflow 2.10.3) inside a private VPC
with no direct Internet access.

## Timeline of blockers and fixes

### 1. Dynamic internal VPC endpoints (undocumented)

Beyond the standard VPC endpoints (S3, ECR, KMS, SQS, monitoring,
logs, airflow.api/env/ops), MWAA generates two endpoints **specific to
each creation attempt**, whose service name only exists once
provisioning has started
(`DatabaseVpcEndpointService`/`WebserverVpcEndpointService`,
retrievable via `aws mwaa get-environment`). Their absence blocks the
environment in `PENDING` status indefinitely, a behavior documented
only in the SDK reference, never mentioned in standard configuration
guides.

### 2. Module name collision (`common/io.py`)

The project's `common/io.py` module collided with Python's standard
`io` module, causing cascading import errors across all of Airflow.
Fixed by a full rename (`common` to `emp_common`, `io.py` to
`storage.py`).

### 3. Execution role created with no policy attached

A creation attempt failed immediately
(`Provided role does not have sufficient permissions`): MWAA had
created the requested IAM role but without attaching a policy to it
(`aws iam list-role-policies` returned an empty list). Fixed by
manually attaching the standard MWAA policy.

### 4. Incremental build script (a collision leftover)

The `build_mwaa_plugins.sh` script ran a `zip -r` on an already
existing `plugins.zip` file, accumulating the old `common/io.py` and
the new `emp_common/storage.py` in the same archive. Fixed by adding a
systematic `rm -f plugins.zip` before rebuilding.

### 5. pip install conflict (`sqlalchemy`/`distutils`)

`requirements.txt` failed with `Cannot uninstall a distutils
installed project: 'sqlalchemy'`, a known pip behavior since version
10 (pypa/pip issue #5247) when facing a package pre-installed at the
system level in the MWAA base image.

### 6. Startup script: no network access at startup

A startup script attempting `pip install` failed with `Network is
unreachable`, since the script runs before the component's network
connectivity is stable. A simple `sleep 60` at the start unblocked the
installation on the Webserver component.

### 7. Full isolation of Python environments per component

Discovered through an exhaustive search in CloudWatch logs (no
occurrence of `pip3` in the Worker/DAGProcessing logs, despite a
confirmed success on the Webserver): **each MWAA component has a
fully isolated Python environment**, with no propagation between
them. Confirmed by AWS support. On `mw1.micro`, the environment
variable `MWAA_AIRFLOW_COMPONENT` equals `hybrid` (not `worker`) for
the combined scheduler+worker container, information not documented
anywhere, discovered by having the variable print itself.

### 8. Structurally blocked public network access

The constraints file (`raw.githubusercontent.com`) and PyPI packages
(`pypi.org`) are public resources outside AWS, unreachable from a
private VPC with no NAT Gateway, the same limitation as for the Open
Charge Map API itself (`api.openchargemap.io`). Worked around at
first for Python dependencies by pre-downloading the wheels locally
and hosting them on S3 (reachable through the Gateway endpoint already
in place), with a conditional startup script
(`if MWAA_AIRFLOW_COMPONENT == "hybrid"`) that downloads them via
`boto3` (more reliable than assuming `aws-cli` is available) and
installs them with `pip3 install --no-index --find-links=...`.

**For the actual call to the Open Charge Map API**, this workaround
was not enough, a real Internet egress was needed. Resolved by adding
a **NAT Gateway** (public subnet, Elastic IP, `0.0.0.0/0` route added
to the private route table).

### 9. Incomplete S3 permissions

The execution role only had read permissions (`s3:GetObject*`),
originally designed for accessing DAG files only. The DAG itself needs
to write (`s3:PutObject`) for ingestion. Policy completed manually.

### 10. Invalid `storage_options` for Polars on MWAA

Unlike `boto3.client("s3")`, which automatically uses the IAM role's
credentials, Polars needs explicit `storage_options`. The DAG used
`os.environ.get("AWS_ACCESS_KEY_ID")`, a variable that does not exist
on MWAA (consistent with the principle of never hardcoding AWS keys).
Fixed by retrieving the role's temporary credentials via
`boto3.Session().get_credentials()`.

## Diagnostic tools that made progress possible

- **`verify_env.py`** (aws-support-tools, with a local fix for a
  `NameError` bug on `self.check_service_vpc_endpoints`)
- **`AWSSupport-TroubleshootMWAAEnvironmentCreation`** (Systems Manager
  Automation), a real connectivity test between ENIs
- **AWS Support Case** (AI assistant, then potentially human), which
  provided the discovery of the dynamic internal endpoints and
  confirmed the full isolation of Python environments per component

## Why

Each fix addressed a real, verified constraint, never an untested
assumption. The method consistently was: reproduce the error, look
for evidence in the logs (with particular effort on reading
reliability, plain text pasted directly proved more reliable than
attachments in this conversation), form a hypothesis, verify it before
acting. This rigor paid off: after an intermediate network setback
(the NAT Gateway), the pipeline worked end to end starting with the
very next fix.

## Consequences

The `electric_mobility_pipeline` DAG runs successfully on the MWAA
cloud (confirmed on 08/25/2026), producing up-to-date Parquet files on
S3 exactly like `run_pipeline.py` locally. The MWAA environment and
the NAT Gateway were deleted after validation, consistent with the
principle already established (continuous billing, keep resources
only for the duration of the demonstration). To attempt a future
demonstration again, follow the cheat sheet
`01_TECHNIQUE/ressources-apprentissage/Pense-bete-MWAA.md` in the
Obsidian vault, which documents the entire timeline with the exact
commands for each fix.

This undertaking represented, by far, the largest time investment of
the project, but also the most complete demonstration of a complex
network/cloud diagnostic skill, potentially the most valuable one in a
technical interview.

## Appendix, key points to remember for any future MWAA project

The full detail, including exact commands and a startup checklist, is
captured in a standalone, reusable guide:
`Guide_MWAA_Bonnes_Pratiques.md` (Obsidian vault,
`02_REFERENCES_TECHNIQUES/`). Summary of the most critical points:

- **A private VPC with no NAT Gateway can never reach the public
  Internet** (neither PyPI, nor GitHub, nor any third-party API), an
  architecture decision to make before any creation, not a fix to add
  afterward.
- **Two internal VPC endpoints are dynamically generated** at every
  environment creation (`DatabaseVpcEndpointService`,
  `WebserverVpcEndpointService`), retrievable only via
  `aws mwaa get-environment`, their absence blocks the environment in
  `PENDING` indefinitely.
- **Each MWAA component (Webserver, Scheduler/Worker, DAG Processor)
  has a fully isolated Python environment**, no propagation of
  `requirements.txt` between them, to be checked component by
  component via CloudWatch logs.
- **The startup script runs before the network is stable**, never
  make a direct network call without a preceding `sleep`.
- **Always test locally with `aws-mwaa-local-runner` before any cloud
  deployment**, a local test cycle takes a few minutes, a cloud cycle
  takes 20 to 90.
