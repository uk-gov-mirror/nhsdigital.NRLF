#!/usr/bin/env python
"""
Manage app ans organisation v2 permissions for NRLF apps in a given environment ENV
"""
import json
import os
from enum import Enum

import fire
from aws_session_assume import get_boto_session

from nrlf.core.constants import TYPE_ATTRIBUTES, AccessControls

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
    app_level_perm_files = {
        key.removesuffix(".json") for key in apps if key and key.endswith(".json")
    }
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


def list_orgs(supplier_type: SupplierType, app_id: str) -> None:
    """
    List all organizations for a specific consumer or producer application.
    """
    if supplier_type.lower() not in SupplierType.list():
        print("Usage: list organisations for a given app and supplier type")
        print("  list_orgs consumer <app_id>")
        print("  list_orgs producer <app_id>")
        return

    keys = _list_s3_keys(f"{supplier_type}/{app_id}/")
    orgs = [
        key.split("/", maxsplit=2)[2].removesuffix(".json")
        for key in keys
        if key and key.endswith(".json")
    ]

    if not orgs:
        print(f"No organizations found for {supplier_type} app {app_id}.")

    print(f"There are {len(orgs)} organizations for app {app_id}:")
    for org in orgs:
        print(f"- {org}")


def list_available_pointer_types() -> None:
    """
    List all pointer types that can be used in permissions.
    """
    print("The following pointer-types can be assigned:")

    for pointer_type, attributes in TYPE_ATTRIBUTES.items():
        print("- %-45s (%s)" % (pointer_type, attributes["display"][:45]))


def list_available_access_controls() -> None:
    """
    List all access controls that can be assigned in permissions.
    """
    print("The following access controls can be assigned:")

    currently_supported_access_controls = [
        AccessControls.ALLOW_ALL_TYPES,
        AccessControls.ALLOW_OVERRIDE_CREATION_DATETIME,
        AccessControls.ALLOW_SUPERSEDE_WITH_DELETE_FAILURE,
    ]
    for control in currently_supported_access_controls:
        print(f"- {control}")


def _print_perm(
    perms_pretty: dict, lookup_path: str, perm_pretty_name: str, perm_key: str
):
    print()
    access_controls = perms_pretty.get(perm_key, [])
    if access_controls:
        print(f"{lookup_path} has these {perm_pretty_name}s:")
        for control in access_controls:
            print(f"- {control}")
    else:
        print(f"{lookup_path} has no {perm_pretty_name}s")


def show_perms(supplier_type: SupplierType, app_id: str, org_ods=None) -> None:
    """
    Show the permissions for a given application or organization.
    """
    if supplier_type.lower() not in SupplierType.list() or not app_id:
        print("Usage: show permissions for a given organisation or app")
        print("  show_perms consumer <app_id> <org_ods>")
        print("  show_perms producer <app_id> <org_ods>")
        print("  show_perms consumer <app_id>")
        print("  show_perms producer <app_id>")
        return

    if org_ods:
        lookup_path = f"{supplier_type}/{app_id}/{org_ods}.json"
    else:
        lookup_path = f"{supplier_type}/{app_id}.json"

    perms_ugly = _get_perms_from_s3(lookup_path)

    if not perms_ugly:
        print(f"No permissions file found for {lookup_path}.")
        return

    perms_pretty = json.loads(perms_ugly)
    if not perms_pretty:
        print(f"No pointer-types found in permission file for {lookup_path}.")
        return

    pretty_type_data = {
        pointertype_perm: TYPE_ATTRIBUTES.get(
            pointertype_perm, {"display": "Unknown type"}
        )
        for pointertype_perm in perms_pretty.get("types")
    }
    types = [
        "%-45s (%s)"
        % (pretty_type_data[pointertype_perm]["display"][:44], pointertype_perm)
        for pointertype_perm in perms_pretty.get("types")
    ]
    print(f"{lookup_path} is allowed to access these pointer-types:")
    for type_display in types:
        print(f"- {type_display}")

    _print_perm(
        perms_pretty,
        lookup_path,
        perm_pretty_name="access control",
        perm_key="access_controls",
    )

    # _print_perm(
    #     perms_pretty,
    #     lookup_path,
    #     perm_pretty_name="API interaction",
    #     perm_key="interaction",
    # )


if __name__ == "__main__":
    fire.Fire(
        {
            "list_apps": list_apps,
            "list_orgs": list_orgs,
            "list_available_pointer_types": list_available_pointer_types,
            "list_available_access_controls": list_available_access_controls,
            "show_perms": show_perms,
            # "set_perms": set_perms,
            # "clear_perms": clear_perms,
        }
    )
