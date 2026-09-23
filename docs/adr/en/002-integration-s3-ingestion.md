# 002 - Integrating S3 into the ingestion pipeline

## Context

The pipeline only saved raw JSON locally (data/raw/). The roadmap
planned the introduction of AWS starting from Phase 1, not deferred
to a later phase.

## Decision

After the local save, the raw JSON is also uploaded to S3 (prefix
raw/ in the bucket), via boto3. A dedicated IAM user, restricted to
the s3:PutObject and s3:GetObject actions on this specific bucket, is
used instead of root credentials or broader access.

## Why

- Consistency with the target architecture defined from the Project
  Brief onward
- The least-privilege principle limits the damage in case of leaked
  credentials: only this bucket is exposed, and only for read/write
- IAM Roles Anywhere (temporary credentials) was considered but set
  aside for now, since its setup complexity is disproportionate for
  a portfolio MVP

## Consequences

Raw JSON now exists in two copies (local + S3). Local storage remains
the reference for now; S3 could become the source of truth if the
project evolves toward real automation (Lambda, EventBridge). Rotating
access keys or migrating to IAM Roles Anywhere remains a future
improvement to consider if the project moves closer to a production
context.
