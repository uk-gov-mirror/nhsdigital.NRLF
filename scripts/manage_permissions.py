#!/usr/bin/env python

import json
import os

import fire
from aws_session_assume import get_boto_session

from nrlf.core.constants import TYPE_ATTRIBUTES

nrl_env = os.getenv("ENV", "dev")
nrl_auth_bucket_name = os.getenv(
    "NRL_AUTH_BUCKET_NAME", f"nhsd-nrlf--{nrl_env}-authorization-store"
)

print(f"Using NRL environment: {nrl_env}")
print(f"Using NRL auth bucket: {nrl_auth_bucket_name}")
print()


def _get_s3_client():
    boto_session = get_boto_session(nrl_env)
    return boto_session.client("s3")


def _list_s3_keys(file_key_prefix: str) -> list[str]:
    s3 = _get_s3_client()
    paginator = s3.get_paginator("list_objects_v2")

    params = {
        "Bucket": nrl_auth_bucket_name,
        "Prefix": file_key_prefix,
    }

    page_iterator = paginator.paginate(**params)
    keys = []
    for page in page_iterator:
        if "Contents" in page:
            keys.extend([item["Key"] for item in page["Contents"]])

    if not keys:
        print(f"No files found with prefix: {file_key_prefix}")
        return []

    return keys


def _get_perms_from_s3(file_key: str) -> list[str]:
    s3 = _get_s3_client()

    item = s3.get_object(Bucket=nrl_auth_bucket_name, Key=file_key)

    if not item:
        print(f"No permissions found for {file_key}.")
        return []

    return item["Body"].read().decode("utf-8")


def list_apps() -> set[str]:
    keys = _list_s3_keys("")
    apps = set([key.split("/")[0] for key in keys])

    if not apps:
        print("No applications found in the bucket.")
        return set()

    print(f"Listing all {len(apps)} apps in bucket...")
    return apps


def list_orgs(app_id: str) -> set[str]:
    keys = _list_s3_keys(f"{app_id}/")
    orgs = [
        key.split("/", maxsplit=2)[1].removesuffix(".json")
        for key in keys
        if key and key.endswith(".json")
    ]

    if not orgs:
        print(f"No organizations found for app {app_id}.")
        return set()

    print(f"Listing {len(orgs)} organizations for {app_id}...")
    return orgs


def get_perms(app_id: str, org_ods: str) -> list[str]:
    perms = _get_perms_from_s3(f"{app_id}/{org_ods}.json")

    if not perms:
        print(f"No permissions file found for {app_id}/{org_ods}.")
        return []

    pointertype_perms = json.loads(perms)
    if not pointertype_perms:
        print(f"No pointer-types found in permission file for {app_id}/{org_ods}.")
        return []

    type_data = {
        pointertype_perm: TYPE_ATTRIBUTES.get(
            pointertype_perm, {"display": "Unknown type"}
        )
        for pointertype_perm in pointertype_perms
    }
    types = [
        f"{type_data[pointertype_perm]['display']} ({pointertype_perm})"
        for pointertype_perm in pointertype_perms
    ]

    print(f"The current permissions for {app_id}/{org_ods} are:")
    return types


def set_perms(app_id: str, org_ods: str, pointer_types: list[str]) -> list[str]:
    # This function would contain the logic to set permissions
    print(f"Setting permissions for {app_id}/{org_ods} to {pointer_types}...")
    return []


if __name__ == "__main__":
    fire.Fire()
