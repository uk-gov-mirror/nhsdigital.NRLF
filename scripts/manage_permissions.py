#!/usr/bin/env python

import os

import fire
from aws_session_assume import get_boto_session

nrl_env = os.getenv("ENV", "dev")
nrl_auth_bucket_name = os.getenv(
    "NRL_AUTH_BUCKET_NAME", f"nhsd-nrlf--{nrl_env}-authorization-store"
)


def _list_s3_files(file_key_prefix: str) -> list[str]:
    # This function would contain the logic to list files in S3
    print(f"Listing files in S3 with prefix {file_key_prefix}...")
    return []


def _get_perms_from_s3(file_key: str) -> list[str]:
    # This function would contain the logic to get permissions from S3
    print(f"Getting permissions from S3 for {file_key}...")
    return []


def list_apps() -> list[str]:
    # This function would contain the logic to list apps
    print("Listing all apps...")
    return []


def list_orgs(app_id: str) -> list[str]:
    # This function would contain the logic to list organizations
    print(f"Listing organizations for {app_id}...")
    return []


def get(app_id: str, org_ods: str) -> list[str]:
    # This function would contain the logic to show current permissions
    print(f"The current permissions for {app_id}/{org_ods} are:")
    return []


def set(app_id: str, org_ods: str, pointer_types: list[str]) -> list[str]:
    # This function would contain the logic to set permissions
    print(f"Setting permissions for {app_id}/{org_ods} to {pointer_types}...")
    return []


if __name__ == "__main__":
    fire.Fire()
