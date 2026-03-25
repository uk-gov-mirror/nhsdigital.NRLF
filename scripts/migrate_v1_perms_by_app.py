#!/usr/bin/env python3
"""
Reads JSON files from a given source folder in the environment's S3 authorization
bucket, transforms each from a flat array into {"types": [...]} format, and
writes the results to both the consumer and producer folders in the same bucket
under a sub-folder matching the source folder name.

Usage:
    python scripts/migrate_v1_perms_by_app.py <env> <folder>

Arguments:
    env     - NRLF environment name (e.g. dev, qa, int, prod)
    folder  - Source folder name within the authorization bucket
              (e.g. an app identifier)

Example:
    python scripts/migrate_v1_perms_by_app.py dev my-app-folder

The script reads from:
    s3://nhsd-nrlf--<env>-authorization-store/<folder>/*.json

And writes to:
    s3://nhsd-nrlf--<env>-authorization-store/consumer/<folder>/<filename>.json
    s3://nhsd-nrlf--<env>-authorization-store/producer/<folder>/<filename>.json

The bucket name defaults to nhsd-nrlf--<env>-authorization-store and can be
overridden via the NRL_AUTH_BUCKET_NAME environment variable.
"""

import json
import os
import sys

from aws_session_assume import get_boto_session
from botocore.exceptions import ClientError

CONSUMER_OR_PRODUCER = ("consumer", "producer")


def _get_bucket_name(env: str) -> str:
    return os.getenv("NRL_AUTH_BUCKET_NAME", f"nhsd-nrlf--{env}-authorization-store")


def _get_s3_client(env: str):
    return get_boto_session(env).client("s3")


def _list_json_files(s3, bucket: str, folder: str) -> list[str]:
    paginator = s3.get_paginator("list_objects_v2")
    return sorted(
        item["Key"]
        for page in paginator.paginate(Bucket=bucket, Prefix=f"{folder}/")
        for item in page.get("Contents", [])
        if item["Key"].endswith(".json")
    )


def _read_and_transform(s3, bucket: str, file_path: str) -> tuple[str, int]:
    try:
        response = s3.get_object(Bucket=bucket, Key=file_path)
    except ClientError as e:
        raise RuntimeError(
            f"Failed to read s3://{bucket}/{file_path}: {e.response['Error']['Message']}"
        ) from e
    data = json.loads(response["Body"].read())

    if not isinstance(data, list):
        raise ValueError(
            f"{file_path}: Expected a JSON array, got {type(data).__name__}"
        )

    return json.dumps({"types": data}, indent=2), len(data)


def _write_v2_consumer_and_producer_files(
    s3, bucket: str, file_path: str, body: str, entry_count: int
) -> None:
    for actor_type in CONSUMER_OR_PRODUCER:
        dest_filepath = f"{actor_type}/{file_path}"
        try:
            s3.put_object(Bucket=bucket, Key=dest_filepath, Body=body)
        except ClientError as e:
            raise RuntimeError(
                f"Failed to write s3://{bucket}/{dest_filepath}: {e.response['Error']['Message']}"
            ) from e
        print(f"  Written {entry_count} entries → s3://{bucket}/{dest_filepath}")


def migrate_v1_perms_by_app(env: str, app_id_folder: str) -> None:
    bucket = _get_bucket_name(env)
    s3 = _get_s3_client(env)

    print(f"Source bucket : {bucket}")
    print(f"Source folder : {app_id_folder}/")

    json_file_paths = _list_json_files(s3, bucket, app_id_folder)
    if not json_file_paths:
        print(f"No JSON files found under s3://{bucket}/{app_id_folder}/")
        return
    print(f"Found {len(json_file_paths)} JSON files in s3://{bucket}/{app_id_folder}/:")

    for file_path in json_file_paths:
        body, entry_count = _read_and_transform(s3, bucket, file_path)
        print(f"  Transforming {file_path} → {entry_count} entries")

        _write_v2_consumer_and_producer_files(s3, bucket, file_path, body, entry_count)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <env> <folder>")
        sys.exit(1)

    migrate_v1_perms_by_app(sys.argv[1], sys.argv[2])
