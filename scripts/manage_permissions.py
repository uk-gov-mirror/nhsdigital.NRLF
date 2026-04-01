#!/usr/bin/env python
"""
Manage app ans organisation v2 permissions for NRLF apps in a given environment ENV
"""
import os
from enum import Enum

import fire
from aws_session_assume import get_boto_session

nrl_env = os.getenv("ENV", "dev")
nrl_auth_bucket_name = os.getenv(
    "NRL_AUTH_BUCKET_NAME", f"nhsd-nrlf--{nrl_env}-authorization-store"
)

COMPARE_AND_CONFIRM = (
    True
    if nrl_env == "prod"
    else os.getenv("COMPARE_AND_CONFIRM", "false").lower() == "true"
)

print(f"Using NRL environment: {nrl_env}")
print(f"Using NRL auth bucket: {nrl_auth_bucket_name}")
print(f"Compare and confirm mode: {COMPARE_AND_CONFIRM}")
print()


class SupplierType(Enum):
    PRODUCER = "producer"
    CONSUMER = "consumer"

    @staticmethod
    def list():
        return [supplier.value for supplier in SupplierType]


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
    keys: list[str] = []
    for page in page_iterator:
        if "Contents" in page:
            keys.extend([item["Key"] for item in page["Contents"]])

    if not keys:
        print(f"No files found with prefix: {file_key_prefix}")
        return []

    return keys


def list_apps(supplier_type: SupplierType) -> None:
    """
    List all consumer or producer applications in the NRL environment.

    Apps ending in .json have app-level permissions
    """
    if supplier_type.lower() not in SupplierType.list():
        print("Usage: list apps for a given supplier type")
        print("  list_apps consumer")
        print("  list_apps producer")
        return

    keys = _list_s3_keys(f"{supplier_type}/")
    apps = {key.split("/")[1] for key in keys[1:]}
    app_level_perm_files = {key for key in apps if key and key.endswith(".json")}
    apps_with_orgs = {key for key in apps if key and not key.endswith(".json")}

    if not apps:
        print("No applications found in the bucket.")
        return

    print(f"There are {len(apps)} apps in {nrl_env} env")

    print()
    print(f"There are {len(apps_with_orgs)} apps containing org-level permissions:")
    for app_with_orgs in apps_with_orgs:
        print(f"- {app_with_orgs}")

    print()
    print(f"There are {len(app_level_perm_files)} apps with app-level permissions:")
    for app_level in app_level_perm_files:
        print(f"- {app_level}")


if __name__ == "__main__":
    fire.Fire(
        {
            "list_apps": list_apps,
            # "list_orgs": list_orgs,
            # "list_allowed_types": list_allowed_types,
            # "show_perms": show_perms,
            # "set_perms": set_perms,
            # "clear_perms": clear_perms,
        }
    )
