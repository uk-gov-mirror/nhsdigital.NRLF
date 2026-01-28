#!/usr/bin/env python
"""
Manage organisation pointer type permissions for NRLF apps in a given environment ENV
"""

import json
import os

import fire
from aws_session_assume import get_boto_session

from nrlf.core.constants import TYPE_ATTRIBUTES

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


def list_apps() -> None:
    """
    List all applications in the NRL environment.
    """
    keys = _list_s3_keys("")
    apps = {key.split("/")[0] for key in keys}

    if not apps:
        print("No applications found in the bucket.")
        return

    print(f"There are {len(apps)} apps in {nrl_env} env:")
    for app in apps:
        print(f"- {app}")


def list_orgs(app_id: str) -> None:
    """
    List all organizations for a specific application.
    """
    keys = _list_s3_keys(f"{app_id}/")
    orgs = [
        key.split("/", maxsplit=2)[1].removesuffix(".json")
        for key in keys
        if key and key.endswith(".json")
    ]

    if not orgs:
        print(f"No organizations found for app {app_id}.")

    print(f"There are {len(orgs)} organizations for app {app_id}:")
    for org in orgs:
        print(f"- {org}")


def list_allowed_types() -> None:
    """
    List all pointer types that can be used in permissions.
    """
    print("The following pointer-types are allowed:")

    for pointer_type, attributes in TYPE_ATTRIBUTES.items():
        print("- %-45s (%s)" % (pointer_type, attributes["display"][:45]))


def show_perms(app_id: str, org_ods: str) -> None:
    """
    Show the permissions for a specific application and organization.
    """
    perms = _get_perms_from_s3(f"{app_id}/{org_ods}.json")

    if not perms:
        print(f"No permissions file found for {app_id}/{org_ods}.")
        return

    pointertype_perms = json.loads(perms)
    if not pointertype_perms:
        print(f"No pointer-types found in permission file for {app_id}/{org_ods}.")
        return

    type_data = {
        pointertype_perm: TYPE_ATTRIBUTES.get(
            pointertype_perm, {"display": "Unknown type"}
        )
        for pointertype_perm in pointertype_perms
    }
    types = [
        "%-45s (%s)" % (type_data[pointertype_perm]["display"][:44], pointertype_perm)
        for pointertype_perm in pointertype_perms
    ]

    print(f"{app_id}/{org_ods} is allowed to access these pointer-types:")
    for type_display in types:
        print(f"- {type_display}")


def set_perms(app_id: str, org_ods: str, *pointer_types: str) -> None:
    """
    Set permissions for an application and organization to access specific pointer types.
    """
    if not pointer_types:
        print(
            "No pointer types provided. Please specify at least one pointer type or use clear_perms command."
        )
        return

    if len(pointer_types) == 1 and pointer_types[0] == "all":
        print("Setting permissions for access to all pointer types.")
        pointer_types = tuple(TYPE_ATTRIBUTES.keys())

    unknown_types = [pt for pt in pointer_types if pt not in TYPE_ATTRIBUTES]
    if unknown_types:
        print(f"Error: Unknown pointer types provided: {', '.join(unknown_types)}")
        print()
        return

    permissions_content = json.dumps(pointer_types, indent=4)

    if COMPARE_AND_CONFIRM:
        current_perms = _get_perms_from_s3(f"{app_id}/{org_ods}.json")
        if current_perms == permissions_content:
            print(
                f"No changes needed for {app_id}/{org_ods}. Current permissions match the new ones."
            )
            return

        print()
        print(f"Current permissions for {app_id}/{org_ods}:")
        print(current_perms if current_perms else "No permissions set.")

        print()
        print("New permissions to be set to:")
        print(f"{permissions_content}")

        print()
        confirm = (
            input("Do you want to proceed with these changes? (yes/NO): ")
            .strip()
            .lower()
        )
        if confirm != "yes":
            print("Operation cancelled at user request.")
            return

    s3 = _get_s3_client()
    s3.put_object(
        Bucket=nrl_auth_bucket_name,
        Key=f"{app_id}/{org_ods}.json",
        Body=permissions_content,
        ContentType="application/json",
    )

    print()
    print(f"Set permissions for {app_id}/{org_ods}")

    print()
    show_perms(app_id, org_ods)


def clear_perms(app_id: str, org_ods: str) -> None:
    """
    Clear permissions for an application and organization.
    This will remove all permissions for the specified app and org.
    """
    if COMPARE_AND_CONFIRM:
        current_perms = _get_perms_from_s3(f"{app_id}/{org_ods}.json")
        if not current_perms or current_perms == "[]":
            print(
                f"No need to clear permissions for {app_id}/{org_ods} as it currently has no permissions set."
            )
            return

        print()
        print(f"Current permissions for {app_id}/{org_ods}:")
        print(current_perms)

        print()
        confirm = (
            input("Are you SURE you want to clear these permissions? (yes/NO): ")
            .strip()
            .lower()
        )
        if confirm != "yes":
            print("Operation cancelled at user request.")
            return

    s3 = _get_s3_client()
    s3.put_object(
        Bucket=nrl_auth_bucket_name,
        Key=f"{app_id}/{org_ods}.json",
        Body="[]",
        ContentType="application/json",
    )
    print(f"Cleared permissions for {app_id}/{org_ods}.")


if __name__ == "__main__":
    fire.Fire(
        {
            "list_apps": list_apps,
            "list_orgs": list_orgs,
            "list_allowed_types": list_allowed_types,
            "show_perms": show_perms,
            "set_perms": set_perms,
            "clear_perms": clear_perms,
        }
    )
