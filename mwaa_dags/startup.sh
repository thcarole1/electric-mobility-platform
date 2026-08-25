#!/bin/bash
if [[ "${MWAA_AIRFLOW_COMPONENT}" == "hybrid" ]]; then
  mkdir -p /tmp/wheels
  python3 -c "
import boto3
s3 = boto3.client('s3')
paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket='electric-mobility-platform-thierry', Prefix='airflow-dags/wheels/'):
    for obj in page.get('Contents', []):
        key = obj['Key']
        filename = key.split('/')[-1]
        if filename:
            s3.download_file('electric-mobility-platform-thierry', key, f'/tmp/wheels/{filename}')
"
  pip3 install --no-index --find-links=/tmp/wheels/ \
    polars duckdb boto3 botocore jmespath s3transfer \
    requests charset-normalizer idna urllib3 certifi \
    polars-runtime-32 \
    --quiet
fi
