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

from nrlf.core.constants import CATEGORY_ATTRIBUTES, TYPE_ATTRIBUTES, AccessControls

nrl_env = os.getenv("ENV", "dev")
nrl_auth_bucket_name = os.getenv(
    "NRL_AUTH_BUCKET_NAME", f"nhsd-nrlf--{nrl_env}-authorization-store"
)
COMPARE_AND_CONFIRM = (
    True
    if nrl_env == "prod"
    else os.getenv("COMPARE_AND_CONFIRM", "false").lower() == "true"
)

currently_supported_access_controls = [
    AccessControls.ALLOW_ALL_TYPES.value,
    AccessControls.ALLOW_OVERRIDE_CREATION_DATETIME.value,
    AccessControls.ALLOW_SUPERSEDE_WITH_DELETE_FAILURE.value,
]


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


def _build_lookup_path(supplier_type: str, app_id: str, org_ods: str | None) -> str:
    if supplier_type.lower() not in SupplierType.list():
        print(f"Error: invalid supplier {supplier_type}")
        return
    if not app_id:
        print("Error: please provide an app_id")
        return

    if org_ods:
        return f"{supplier_type}/{app_id}/{org_ods}.json"
    return f"{supplier_type}/{app_id}.json"


def _load_or_setup_perms(lookup_path: str) -> dict:
    perms_ugly = _get_perms_from_s3(lookup_path)
    if not perms_ugly:
        print("Setting up new permissions file...")
        return {}
    return json.loads(perms_ugly)


def _confirm_proceed(
    prompt: str = "Do you want to proceed with these changes? (yes/NO): ",
) -> bool:
    """
    If COMPARE_AND_CONFIRM enabled, ask the user to confirm before writing changes.
    """
    if not COMPARE_AND_CONFIRM:
        return True
    print()
    confirm = input(prompt).strip().lower()
    if confirm != "yes":
        print("Operation cancelled at user request.")
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
    print(f"{success_message.strip()} for {lookup_path}")

    print()
    show_perms(supplier_type, app_id, org_ods)


def list_apps(supplier_type: SupplierType) -> None:
    """
    List all consumer or producer applications for a given supplier type

    Specifies which apps have app-level or org-level permissions
        list_apps consumer
        list_apps producer
    """
    if supplier_type.lower() not in SupplierType.list():
        print(f"Error: invalid supplier {supplier_type}")
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
    print()


def list_orgs(supplier_type: SupplierType, app_id: str) -> None:
    """
    List all organizations for a specific consumer or producer application.

        list_orgs consumer <app_id>
        list_orgs producer <app_id>
    """
    if supplier_type.lower() not in SupplierType.list():
        print(f"Error: invalid supplier {supplier_type}")
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
    # if not perm_to_print:
    #     return
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
        print(f"No permissions file found for {lookup_path}.")
        return

    perms_pretty = json.loads(perms_ugly)
    if not perms_pretty:
        print(f"No permissions found in file for {lookup_path}.")
        return

    print(f"{lookup_path} is allowed access to the following...")

    _print_perm_with_lookup(
        "pointer type", perms_pretty.get("types", []), TYPE_ATTRIBUTES
    )

    # _print_perm_with_lookup(
    #     "pointer categories", perms_pretty.get("categories", []), CATEGORY_ATTRIBUTES
    # )

    _print_perm(
        "access control",
        perms_pretty.get("access_controls", []),
    )

    # _print_perm(
    #     "API interaction",
    #     perms_pretty.get("interaction", []),
    # )

    # _print_perm(
    #     "Produce for authors",
    #     perms_pretty.get("produce_for_authors", []),
    # )

    # _print_perm(
    #     "Produce for custodians",
    #     perms_pretty.get("produce_for_custodians", []),
    # )


def add_pointer_type_perms(
    supplier_type: SupplierType, app_id: str, org_ods=None, *pointer_types_to_add: str
) -> None:
    """
    Add permissions for a given list of pointer types to an app or org.

    Specify pointer_types=all to add all (current) pointer types.

        add_pointer_type_perms consumer <app_id> <org_ods> <pointer_types>
        add_pointer_type_perms producer <app_id> <org_ods> <pointer_types>
        add_pointer_type_perms consumer <app_id> <pointer_types>
        add_pointer_type_perms producer <app_id> <pointer_types>

    TODO:
    highlight new additions in proposed pointer types list e.g. [NEW]
    """

    lookup_path = _build_lookup_path(supplier_type, app_id, org_ods)
    if not lookup_path:
        return

    if not pointer_types_to_add:
        print("No pointer types provided. Please specify at least one pointer type.")
        return

    if len(pointer_types_to_add) == 1 and pointer_types_to_add[0] == "all":
        print("Setting permissions for access to all pointer types.")
        pointer_types_to_add = tuple(TYPE_ATTRIBUTES.keys())

    unknown_types = [
        pointer_type
        for pointer_type in pointer_types_to_add
        if pointer_type not in TYPE_ATTRIBUTES
    ]
    if unknown_types:
        print(f"Error: Unknown pointer types provided: {', '.join(unknown_types)}")
        print()
        return

    current_perms = _load_or_setup_perms(lookup_path)
    current_pointer_types: list = current_perms.get("types", [])

    already_added_types = [
        pointer_type
        for pointer_type in pointer_types_to_add
        if pointer_type in current_pointer_types
    ]
    if already_added_types:
        print(
            f"Error: Unable to add pointer types. These pointer types are already assigned to {lookup_path}:"
        )
        _print_perm_with_lookup("", already_added_types, TYPE_ATTRIBUTES)
        print()
        return

    proposed_pointer_types = current_pointer_types + list(pointer_types_to_add)
    _print_perm_with_lookup(
        "proposed pointer types", proposed_pointer_types, TYPE_ATTRIBUTES
    )

    if not _confirm_proceed():
        return

    current_perms["types"] = proposed_pointer_types
    _save_updated_perms(lookup_path, current_perms, supplier_type, app_id, org_ods)


def add_access_control_perms(
    supplier_type: SupplierType, app_id: str, org_ods=None, *access_controls_to_add: str
) -> None:
    """
    Add permissions for a given list of access controls to an app or org.

        add_access_control_perms consumer <app_id> <org_ods> <access_controls>
        add_access_control_perms producer <app_id> <org_ods> <access_controls>
        add_access_control_perms consumer <app_id> <access_controls>
        add_access_control_perms producer <app_id> <access_controls>

    TODO:
    highlight new additions in proposed access controls list e.g. [NEW]
    """
    lookup_path = _build_lookup_path(supplier_type, app_id, org_ods)
    if not lookup_path:
        return

    if not access_controls_to_add:
        print(
            "No access controls provided. Please specify at least one access control."
        )
        return

    unknown_access_controls = [
        access_control
        for access_control in access_controls_to_add
        if access_control not in currently_supported_access_controls
    ]
    if unknown_access_controls:
        print(
            f"Error: Unknown or unsupported access controls provided: {', '.join(unknown_access_controls)}"
        )
        print()
        list_available_access_controls()
        return

    current_perms = _load_or_setup_perms(lookup_path)
    current_access_controls: list = current_perms.get("access_controls", [])

    already_added_access_controls = [
        access_control
        for access_control in access_controls_to_add
        if access_control in current_access_controls
    ]
    if already_added_access_controls:
        print(
            f"Error: Unable to add access controls. These access controls are already assigned to {lookup_path}:"
        )
        _print_perm("", already_added_access_controls)
        print()
        return

    proposed_access_controls = current_access_controls + list(access_controls_to_add)
    _print_perm("proposed access controls", proposed_access_controls)

    if not _confirm_proceed():
        return

    current_perms["access_controls"] = proposed_access_controls
    _save_updated_perms(lookup_path, current_perms, supplier_type, app_id, org_ods)


def remove_pointer_type_perms(
    supplier_type: SupplierType,
    app_id: str,
    org_ods=None,
    *pointer_types_to_remove: str,
) -> None:
    """
    Remove pointer type permissions for a given organisation or app.

        remove_pointer_type_perms consumer <app_id> <org_ods> <pointer_types>
        remove_pointer_type_perms producer <app_id> <org_ods> <pointer_types>
        remove_pointer_type_perms consumer <app_id> <pointer_types>
        remove_pointer_type_perms producer <app_id> <pointer_types>
    """
    lookup_path = _build_lookup_path(supplier_type, app_id, org_ods)
    if not lookup_path:
        return

    if not pointer_types_to_remove:
        print(
            "No pointer types provided. Please specify at least one pointer type or use clear_perms command."
        )
        return

    unknown_types = [
        pointer_type
        for pointer_type in pointer_types_to_remove
        if pointer_type not in TYPE_ATTRIBUTES
    ]
    if unknown_types:
        print(f"Error: Unknown pointer types provided: {', '.join(unknown_types)}")
        print()
        return

    perms_ugly = _get_perms_from_s3(lookup_path)
    if not perms_ugly:
        return

    current_perms = json.loads(perms_ugly)
    current_pointer_types: list = current_perms.get("types", [])

    # Cannot remove pointer types that aren't already assigned
    types_not_assigned = [
        pointer_type
        for pointer_type in pointer_types_to_remove
        if pointer_type not in current_pointer_types
    ]
    if types_not_assigned:
        print(
            f"Error: Unable to remove pointer types. These pointer types aren't assigned to {lookup_path}:"
        )
        _print_perm_with_lookup("", types_not_assigned, TYPE_ATTRIBUTES)
        print()
        return

    proposed_pointer_types = [
        pointer_type
        for pointer_type in current_pointer_types
        if pointer_type not in pointer_types_to_remove
    ]
    _print_perm_with_lookup(
        "proposed pointer types", proposed_pointer_types, TYPE_ATTRIBUTES
    )

    if not _confirm_proceed():
        return

    current_perms["types"] = proposed_pointer_types
    _save_updated_perms(lookup_path, current_perms, supplier_type, app_id, org_ods)


def remove_access_control_perms(
    supplier_type: SupplierType,
    app_id: str,
    org_ods=None,
    *access_controls_to_remove: str,
) -> None:
    """
    Remove access controls for a given an app or org.

        remove_access_control_perms consumer <app_id> <org_ods> <access_controls>
        remove_access_control_perms producer <app_id> <org_ods> <access_controls>
        remove_access_control_perms consumer <app_id> <access_controls>
        remove_access_control_perms producer <app_id> <access_controls>
    """
    lookup_path = _build_lookup_path(supplier_type, app_id, org_ods)
    if not lookup_path:
        return

    if not access_controls_to_remove:
        print(
            "No access controls provided. Please specify at least one access control or use clear_perms command."
        )
        return

    unknown_access_controls = [
        access_control
        for access_control in access_controls_to_remove
        if access_control not in currently_supported_access_controls
    ]
    if unknown_access_controls:
        print(
            f"Error: Unknown or unsupported access controls provided: {', '.join(unknown_access_controls)}"
        )
        print()
        return

    perms_ugly = _get_perms_from_s3(lookup_path)
    if not perms_ugly:
        return

    current_perms = json.loads(perms_ugly)
    current_access_controls: list = current_perms.get("access_controls", [])

    # Cannot remove access controls that aren't already assigned
    access_controls_not_assigned = [
        access_control
        for access_control in access_controls_to_remove
        if access_control not in current_access_controls
    ]
    if access_controls_not_assigned:
        print(
            f"Error: Unable to remove access controls. These access controls aren't assigned to {lookup_path}:"
        )
        _print_perm("", access_controls_not_assigned)
        print()
        return

    proposed_access_controls = [
        access_control
        for access_control in current_access_controls
        if access_control not in access_controls_to_remove
    ]
    _print_perm("proposed access controls", proposed_access_controls)

    if not _confirm_proceed():
        return

    current_perms["access_controls"] = proposed_access_controls
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
            f"No need to clear permissions for {lookup_path} as it currently has no permissions set."
        )
        return

    if COMPARE_AND_CONFIRM:
        print()
        print(f"Current permissions for {lookup_path}:")
        print(current_perms)

        if not _confirm_proceed(
            "Are you SURE you want to clear these permissions? (yes/NO): "
        ):
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
            "add_pointer_type_perms": add_pointer_type_perms,
            "add_access_control_perms": add_access_control_perms,
            "remove_pointer_type_perms": remove_pointer_type_perms,
            "remove_access_control_perms": remove_access_control_perms,
            "clear_perms": clear_perms,
        }
    )
