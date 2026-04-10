#!/usr/bin/env python
"""
Manage app and organisation v2 permissions for NRLF apps in a given environment ENV

```sh
ENV=dev \
COMPARE_AND_CONFIRM=true \
poetry run python ./scripts/manage_permissions.py <command> <args>
```
"""
import json
import os
from enum import Enum

import fire
from aws_session_assume import get_boto_session

from nrlf.core.constants import (
    CATEGORY_ATTRIBUTES,
    PERMISSION_KEY_ATTRIBUTES,
    TYPE_ATTRIBUTES,
    AccessControls,
    Categories,
    PointerTypes,
    V2PermissionKey,
)

nrl_env = os.getenv("ENV", "dev")
nrl_auth_bucket_name = os.getenv(
    "NRL_AUTH_BUCKET_NAME", f"nhsd-nrlf--{nrl_env}-authorization-store"
)
COMPARE_AND_CONFIRM = (
    True
    if nrl_env == "prod"
    else os.getenv("COMPARE_AND_CONFIRM", "false").lower() == "true"
)


class SupplierType(Enum):
    PRODUCER = "producer"
    CONSUMER = "consumer"

    @staticmethod
    def list():
        return [supplier.value for supplier in SupplierType]


currently_supported_permission_keys = [
    V2PermissionKey.TYPES.value,
    V2PermissionKey.ACCESS_CONTROLS.value,
    # V2PermissionKey.CATEGORIES.value,
]

currently_supported_access_controls = [
    AccessControls.ALLOW_ALL_TYPES.value,
    AccessControls.ALLOW_OVERRIDE_CREATION_DATETIME.value,
    AccessControls.ALLOW_SUPERSEDE_WITH_DELETE_FAILURE.value,
]


print(f"📚 Using NRL environment: {nrl_env}")
print(f"🪣  Using NRL auth bucket: {nrl_auth_bucket_name}")
print(f"🔍 Compare and confirm mode: {COMPARE_AND_CONFIRM}")
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
        print(f"👀 No files found with prefix: {file_key_prefix}")
        return []

    return keys


def _get_perms_from_s3(file_key: str) -> str | None:
    s3 = _get_s3_client()

    try:
        item = s3.get_object(Bucket=nrl_auth_bucket_name, Key=file_key)
    except s3.exceptions.NoSuchKey:
        print(f"👀 Permissions file {file_key} does not exist in the bucket.")
        return None

    if "Body" not in item:
        print(f"❌ Error: no body found for permissions file {file_key}.")
        return None

    return item["Body"].read().decode("utf-8")


def _build_lookup_path(
    supplier_type: str, app_id: str, org_ods: str | None
) -> str | None:
    if supplier_type.lower() not in SupplierType.list():
        print(f"❌ Error: invalid supplier {supplier_type}")
        return
    if not app_id:
        print("❌ Error: please provide an app_id")
        return

    if org_ods:
        return f"{supplier_type}/{app_id}/{org_ods}.json"
    return f"{supplier_type}/{app_id}.json"


def _load_or_setup_perms(lookup_path: str) -> dict:
    print(f"⏳ Looking up permissions for {lookup_path}")
    perms_ugly = _get_perms_from_s3(lookup_path)
    if not perms_ugly:
        print("✨ Setting up new permissions file...")
        return {}
    print()
    return json.loads(perms_ugly)


def _confirm_proceed(
    prompt: str = "❓ Do you want to proceed with these changes?",
) -> bool:
    """
    If COMPARE_AND_CONFIRM=true, ask the user to confirm before writing changes.
    """
    if not COMPARE_AND_CONFIRM:
        return True
    print()
    confirm = input(f"{prompt} (yes/NO): ").strip().lower()
    if confirm != "yes":
        print("❌ Operation cancelled at user request.")
        return False
    return True


def _save_updated_perms(
    lookup_path: str,
    updated_perms: dict,
    supplier_type: str,
    app_id: str,
    org_ods: str | None,
    success_message="Set permissions",
) -> None:
    """
    Write updated permissions to S3 and display the new state.
    """
    s3 = _get_s3_client()
    s3.put_object(
        Bucket=nrl_auth_bucket_name,
        Key=lookup_path,
        Body=json.dumps(updated_perms, indent=4),
        ContentType="application/json",
    )
    print()
    print(f"🎉 {success_message.strip()} for {lookup_path}")

    print()
    show_perms(supplier_type, app_id, org_ods)

    print("💡 Remember to update the lambda layer for these changes to take effect")
    print()


json_file_ending = ".json"


def list_apps(supplier_type: SupplierType) -> None:
    """
    List all consumer or producer applications for a given supplier type

    Specifies which apps have app-level or org-level permissions
        list_apps consumer
        list_apps producer
    """
    if supplier_type.lower() not in SupplierType.list():
        print(f"❌ Error: invalid supplier {supplier_type}")
        return

    keys = _list_s3_keys(f"{supplier_type}/")
    apps = {key.split("/")[1] for key in keys[1:]}
    app_level_perm_files = {
        key.removesuffix(json_file_ending)
        for key in apps
        if key and key.endswith(json_file_ending)
    }
    apps_with_orgs = {key for key in apps if key and not key.endswith(json_file_ending)}

    if not apps:
        print(f"👀 No applications found in the {nrl_env} bucket.")
        return

    def there_are_x_apps(app_count: int):
        is_are = "is" if app_count == 1 else "are"
        s = "" if app_count == 1 else "s"
        return f"There {is_are} {app_count} app{s}"

    print(f"{there_are_x_apps(len(apps))} in the {nrl_env} env")

    print()
    print(f"{there_are_x_apps(len(apps_with_orgs))} containing org-level permissions:")
    for app_with_orgs in apps_with_orgs:
        print(f"- {app_with_orgs}")

    print()
    print(f"{there_are_x_apps(len(app_level_perm_files))} with app-level permissions:")
    for app_level in app_level_perm_files:
        print(f"- {app_level}")
    print()


def list_orgs(supplier_type: SupplierType, app_id: str) -> None:
    """
    List all organizations for a specific consumer or producer application.

        list_orgs consumer <app_id>
        list_orgs producer <app_id>
    """
    if supplier_type.lower() not in SupplierType.list():
        print(f"❌ Error: invalid supplier {supplier_type}")
        return

    keys = _list_s3_keys(f"{supplier_type}/{app_id}/")
    orgs = [
        key.split("/", maxsplit=2)[2].removesuffix(json_file_ending)
        for key in keys
        if key and key.endswith(json_file_ending)
    ]

    if not orgs:
        print()
        print(f"👀 No organizations found for {supplier_type} app {app_id}.")
        return

    org_count = len(orgs)
    is_are = "is" if org_count == 1 else "are"
    s = "" if org_count == 1 else "s"
    print(f"There {is_are} {org_count} organization{s} for app {app_id}:")
    for org in orgs:
        print(f"- {org}")
    print()


def list_available_pointer_types() -> None:
    """
    List all pointer types that can be used in permissions.
    """
    print("The following pointer-types can be assigned:")

    for pointer_type, attributes in TYPE_ATTRIBUTES.items():
        print("- %-45s (%s)" % (pointer_type, attributes["display"][:45]))
    print()


def list_available_access_controls() -> None:
    """
    List all access controls that can be assigned in permissions.
    """
    print("The following access controls can be assigned:")

    for control in currently_supported_access_controls:
        print(f"- {control}")
    print()


def _print_perm(
    perm_pretty_name: str,
    perm_to_print: list,
):
    print()
    if perm_pretty_name:
        plural = (
            perm_pretty_name
            if perm_pretty_name.endswith("s")
            else f"{perm_pretty_name}s"
        )
        print(f"{plural.upper()} ({len(perm_to_print)})")
    for perm in perm_to_print:
        print(f"- {perm}")


def _print_perm_with_lookup(
    perm_pretty_name: str,
    perm_to_print: list,
    attribute_lookup: dict[str, dict[str, str]],
):
    """
    Lookup human-readable names for a permission and print
    """
    if not attribute_lookup:
        _print_perm(perm_pretty_name, perm_to_print)
        return

    printable = []
    for perm_item in perm_to_print:
        display_name = attribute_lookup.get(
            perm_item, {"display": f"Unknown {perm_pretty_name.lower()}"}
        )["display"]
        printable_perm_and_display_name = "%-45s (%s)" % (
            display_name[:44],
            perm_item,
        )
        printable.append(printable_perm_and_display_name)
    _print_perm(perm_pretty_name, printable)


def show_perms(supplier_type: SupplierType, app_id: str, org_ods=None) -> None:
    """
    Show permissions for a given application or organization.

        show_perms consumer <app_id> <org_ods>
        show_perms producer <app_id> <org_ods>
        show_perms consumer <app_id>
        show_perms producer <app_id>
    """
    lookup_path = _build_lookup_path(supplier_type, app_id, org_ods)
    if not lookup_path:
        return

    perms_ugly = _get_perms_from_s3(lookup_path)

    if not perms_ugly:
        print(f"👀 No permissions file found for {lookup_path}.")
        return

    perms_pretty = json.loads(perms_ugly)
    if not perms_pretty:
        print(f"👀 No permissions found in file for {lookup_path}.")
        return

    print(f"{lookup_path} is allowed access to the following...")

    for perm in currently_supported_permission_keys:
        _print_perm_with_lookup(
            perm,
            perms_pretty.get(perm, []),
            PERMISSION_KEY_ATTRIBUTES.get(perm)["attribute_lookup"],
        )


def add_perm(
    permission_key: str,
    supplier_type: SupplierType,
    app_id: str,
    org_ods=None,
    *items_to_add: str,
) -> None:
    """
    Add items to any permission for a given app or org.
        add_perm <permission_key> <supplier_type> <app_id> <permission_items>

    Add pointer types to a consumer org:
        add_perm types consumer <app_id> <org_ods> http://snomed.info/sct|736253002 http://snomed.info/sct|887701000000100

    Add all current pointer types to a producer org:
        add_perm types producer <app_id> <org_ods> all

    Add access controls to a producer app:
        add_perm access_controls producer <app_id> allow_all_types allow_supersede_with_delete_failure
    """
    if permission_key not in currently_supported_permission_keys:
        print(f"❌ Error: invalid permission being set: {permission_key}")
        print(f"Supported permission keys: {currently_supported_permission_keys}")
        return

    lookup_path = _build_lookup_path(supplier_type, app_id, org_ods)
    if not lookup_path:
        return

    (
        permission_name,
        permission_name_singular,
        permission_lookup,
        all_assignable_permission_items,
    ) = PERMISSION_KEY_ATTRIBUTES.get(permission_key).values()

    if not items_to_add:
        print(
            f"❌ Error: no {permission_name} provided. Please specify at least one {permission_name_singular}."
        )
        return

    if len(items_to_add) == 1 and items_to_add[0] == "all":
        print(f"📚 Setting permissions for access to all {permission_name}.")
        items_to_add = all_assignable_permission_items

    unknown_items = [
        item for item in items_to_add if item not in all_assignable_permission_items
    ]
    if unknown_items:
        print(
            f"❌ Error: Unknown {permission_name} provided: {', '.join(unknown_items)}"
        )
        print()
        return

    current_perms = _load_or_setup_perms(lookup_path)
    current_permission_items: list = current_perms.get(permission_key, [])

    already_added_items = [
        item for item in items_to_add if item in current_permission_items
    ]
    if already_added_items:
        print(
            f"❌ Error: Unable to add {permission_name}. These {permission_name} are already assigned to {lookup_path}:"
        )
        _print_perm_with_lookup("", already_added_items, permission_lookup)
        print()
        return

    proposed_permission_items = current_permission_items + list(items_to_add)
    _print_perm_with_lookup(
        f"proposed {permission_name}",
        proposed_permission_items,
        permission_lookup,
    )

    add_count = len(items_to_add)
    if not _confirm_proceed(
        f"❓ Do you want to proceed with these changes and add {add_count} {permission_name_singular if add_count == 1 else permission_name}?"
    ):
        return

    current_perms[permission_key] = proposed_permission_items
    _save_updated_perms(lookup_path, current_perms, supplier_type, app_id, org_ods)


def remove_perm(
    permission_key: str,
    supplier_type: SupplierType,
    app_id: str,
    org_ods=None,
    *items_to_remove: str,
):
    """
    Remove items from any permission for a given app or org.
        remove_perm <permission_key> <supplier_type> <app_id> <permission_items>

    Remove pointer types from a consumer org:
        remove_perm types consumer <app_id> <org_ods> http://snomed.info/sct|736253002 http://snomed.info/sct|887701000000100

    Remove access controls from a producer app:
        remove_perm access_controls producer <app_id> allow_all_types allow_supersede_with_delete_failure
    """
    if permission_key not in currently_supported_permission_keys:
        print(f"❌ Error: invalid permission being set: {permission_key}")
        print(f"Supported permission keys: {currently_supported_permission_keys}")
        return

    lookup_path = _build_lookup_path(supplier_type, app_id, org_ods)
    if not lookup_path:
        return

    (
        permission_name,
        permission_name_singular,
        permission_lookup,
        all_assignable_permission_items,
    ) = PERMISSION_KEY_ATTRIBUTES.get(permission_key).values()

    if not items_to_remove:
        print(
            f"👀 No {permission_name} provided. Please specify at least one {permission_name_singular}."
        )
        return

    unknown_items = [
        item for item in items_to_remove if item not in all_assignable_permission_items
    ]
    if unknown_items:
        print(
            f"❌ Error: Unknown {permission_name} provided: {', '.join(unknown_items)}"
        )
        print()
        return

    print(f"⏳ Looking up permissions for {lookup_path}")
    perms_ugly = _get_perms_from_s3(lookup_path)
    if not perms_ugly:
        return
    print()

    current_perms = json.loads(perms_ugly)
    current_permission_items: list = current_perms.get(permission_key, [])

    # Cannot remove permission items that aren't already assigned
    items_not_assigned = [
        item for item in items_to_remove if item not in current_permission_items
    ]
    if items_not_assigned:
        print(
            f"❌ Error: Unable to remove {permission_name}. These {permission_name} aren't assigned to {lookup_path}:"
        )
        _print_perm("", items_not_assigned)
        print()
        return

    proposed_permission_items = [
        item for item in current_permission_items if item not in items_to_remove
    ]
    _print_perm_with_lookup(
        f"proposed {permission_name}",
        proposed_permission_items,
        permission_lookup,
    )

    remove_count = len(items_to_remove)
    if not _confirm_proceed(
        f"❓ Do you want to proceed with these changes and remove {remove_count} {permission_name_singular if remove_count == 1 else permission_name}?"
    ):
        return

    current_perms[permission_key] = proposed_permission_items
    _save_updated_perms(lookup_path, current_perms, supplier_type, app_id, org_ods)


def clear_perms(supplier_type: SupplierType, app_id: str, org_ods=None) -> None:
    """
    Clear permissions for an application or organization.

    This will remove ALL permissions for the specified app or org.

        clear_perms consumer <app_id> <org_ods>
        clear_perms producer <app_id> <org_ods>
        clear_perms consumer <app_id>
        clear_perms producer <app_id>
    """

    lookup_path = _build_lookup_path(supplier_type, app_id, org_ods)
    if not lookup_path:
        return

    current_perms = _get_perms_from_s3(lookup_path)
    if not current_perms or current_perms == "{}":
        print(
            f"⏭️ No need to clear permissions for {lookup_path} as it currently has no permissions set."
        )
        return

    if COMPARE_AND_CONFIRM:
        print()
        print(f"Current permissions for {lookup_path}:")
        print(current_perms)

        if not _confirm_proceed("Are you SURE you want to clear these permissions?"):
            return

    _save_updated_perms(
        lookup_path,
        {},
        supplier_type,
        app_id,
        org_ods,
        success_message="Cleared permissions",
    )


if __name__ == "__main__":
    fire.Fire(
        {
            "list_apps": list_apps,
            "list_orgs": list_orgs,
            "list_available_pointer_types": list_available_pointer_types,
            "list_available_access_controls": list_available_access_controls,
            "show_perms": show_perms,
            "add_perm": add_perm,
            "remove_perm": remove_perm,
            "clear_perms": clear_perms,
        }
    )
