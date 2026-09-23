# 024 - Continuous integration and remote Terraform backend

## Context

After Terraform (ADR-022) and Docker (ADR-023), the last building
block of Phase 5 (industrialization) was to set up continuous
integration via GitHub Actions, to automate checking the code and the
infrastructure on every change.

## Decision

Two GitHub Actions workflows were set up:

**`tests.yml`**, runs the project's 63 unit tests on every push to
`main` and on every Pull Request targeting `main`. A branch protection
rule (ruleset) was configured to prevent any merge until this check
passes.

**`terraform-plan.yml`**, runs `terraform init` and `terraform plan`
on every Pull Request modifying files in the `terraform/` folder,
giving an automatic preview of the impact of an infrastructure change
before merging. No `terraform apply` is run automatically: applying
changes remains a manual action, deliberately not automated for this
sensitive infrastructure.

Setting up this second workflow required migrating the Terraform
State, until now local and unreachable by GitHub Actions, to a remote
backend: a dedicated (versioned) S3 bucket, with native S3 locking
(`use_lockfile`), replacing the earlier DynamoDB table approach, which
has been deprecated since Terraform 1.10.

The AWS credentials used by these workflows are those of the
administrator account (`emp-admin`), stored as encrypted GitHub
secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `OCM_API_KEY`),
never in plain text in the code.

## Why

A local State cannot, by nature, be shared between the local
development environment and GitHub Actions' remote execution
environment. A remote backend is the standard industry practice as
soon as a Terraform infrastructure needs to be viewed or modified from
several environments, regardless of the number of people involved.

The deliberate absence of an automatic `terraform apply` reflects a
common professional practice: an infrastructure plan must be visible
and checked before any real application, particularly for IAM,
network, or security resources where a poorly anticipated change can
have cascading consequences, as illustrated by the security group
incident already documented (ADR-022).

Using the `emp-admin` credentials rather than a restricted IAM role
dedicated to CI was an accepted choice, driven by the session's time
constraint, with the corresponding risk explicitly identified: a
compromise of these secrets would expose full administrator access to
the AWS account, rather than access limited to what is strictly
needed.

## Consequences

A first attempt of the `terraform-plan.yml` workflow failed with a
missing-credentials error on the `terraform init` step: the AWS
environment variables were only declared at the level of the
`terraform plan` step, while `init` itself needs access to the
backend's S3 bucket. The fix consisted of moving the credentials
declaration to the level of the whole job, making them available to
all of its steps.

The scope of the CI/CD put in place remains deliberately partial:
still outside this scope are automatic Lambda code deployment (still
handled by the existing build scripts, run manually), publishing a
Docker image to a registry, and any automated `terraform apply`
mechanism, even with prior approval. This scope was judged sufficient
to demonstrate the targeted skills without a disproportionate time
investment relative to the project's other priorities.
