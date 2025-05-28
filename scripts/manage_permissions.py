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


def _get_perms_from_s3(file_key: str) -> str | None:
    s3 = _get_s3_client()

    try:
        item = s3.get_object(Bucket=nrl_auth_bucket_name, Key=file_key)
    except s3.exceptions.NoSuchKey:
        print(f"Permissions file {file_key} does not exist in the bucket.")
        return None

    if "Body" not in item:
        print(f"No body found for permissions file {file_key}.")
        return None

    return item["Body"].read().decode("utf-8")


def list_apps() -> list[str]:
    keys = _list_s3_keys("")
    apps = [key.split("/")[0] for key in keys]

    if not apps:
        print("No applications found in the bucket.")
        return []

    print(f"Listing all {len(apps)} apps in bucket...")
    return apps


def list_orgs(app_id: str) -> list[str]:
    keys = _list_s3_keys(f"{app_id}/")
    orgs = [
        key.split("/", maxsplit=2)[1].removesuffix(".json")
        for key in keys
        if key and key.endswith(".json")
    ]

    if not orgs:
        print(f"No organizations found for app {app_id}.")
        return []

    print(f"Listing {len(orgs)} organizations for {app_id}...")
    return orgs


def get(app_id: str, org_ods: str) -> list[str]:
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


def set(app_id: str, org_ods: str, *pointer_types: str) -> list[str]:
    if not pointer_types:
        print(
            "No pointer types provided. Please specify at least one pointer type or use clear_perms command."
        )
        return []

    unknown_types = [pt for pt in pointer_types if pt not in TYPE_ATTRIBUTES]
    if unknown_types:
        print(f"Warning: Unknown pointer types provided: {', '.join(unknown_types)}")
        print()

    permissions_content = json.dumps(pointer_types, indent=4)
    s3 = _get_s3_client()
    s3.put_object(
        Bucket=nrl_auth_bucket_name,
        Key=f"{app_id}/{org_ods}.json",
        Body=permissions_content,
        ContentType="application/json",
    )

    return get(app_id, org_ods)


def clear(app_id: str, org_ods: str) -> None:
    s3 = _get_s3_client()
    s3.put_object(
        Bucket=nrl_auth_bucket_name,
        Key=f"{app_id}/{org_ods}.json",
        Body="[]",
        ContentType="application/json",
    )
    print(f"Cleared permissions for {app_id}/{org_ods}.")


if __name__ == "__main__":
    fire.Fire()
