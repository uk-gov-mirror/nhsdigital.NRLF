#!/usr/bin/env python
import json
from os import path
from pathlib import Path

import fire
from aws_session_assume import get_boto_session

from nrlf.core.constants import AccessControls, PointerTypes


def get_file_folders(s3_client, bucket_name, prefix=""):

    print("Getting file folders to download...")
    file_names = []
    folders = []

    default_kwargs = {"Bucket": bucket_name, "Prefix": prefix}
    next_token = ""

    while next_token is not None:
        updated_kwargs = default_kwargs.copy()
        if next_token != "":
            updated_kwargs["ContinuationToken"] = next_token

        response = s3_client.list_objects_v2(**updated_kwargs)
        contents = response.get("Contents")

        for result in contents:
            key = result.get("Key")
            if key[-1] == "/":
                folders.append(key)
            else:
                file_names.append(key)

        next_token = response.get("NextContinuationToken")

    return file_names, folders


def add_test_files(folder, file_name, local_path):
    print("Adding test files to temporary directory...")
    folder_path = Path.joinpath(local_path, folder)
    # Create all folders in the path
    folder_path.mkdir(parents=True, exist_ok=True)
    file_path = Path.joinpath(folder_path, file_name)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(PointerTypes.list(), f)


def _write_permission_file(folder_path, ods_code, pointer_types, access_controls=None):
    folder_path.mkdir(parents=True, exist_ok=True)
    with open(folder_path / f"{ods_code}.json", "w") as f:
        json.dump({"access_controls": access_controls or [], "types": pointer_types}, f)


def add_feature_test_files(local_path):
    """Bake in v2 permissions for the feature test application so that the
    v2 permissions model can be proven via feature tests without
    requiring a dynamic layer rebuild between test setup and test execution.
    """

    print("Adding feature test v2 permissions to temporary directory...")
    org_permissions = {
        "consumer": [
            (
                "z00z-y11y-x22x",
                "RX898",
                [PointerTypes.MENTAL_HEALTH_PLAN.value],
                [],
            ),  # http://snomed.info/sct|736253002
            (
                "app-t004",
                "ODS1",
                [PointerTypes.PERSONALISED_CARE_AND_SUPPORT_PLAN.value],
                [],
            ),
            (
                "z00z-y11y-x22x",
                "4LLTYP35C",
                [],
                [AccessControls.ALLOW_ALL_TYPES.value],
            ),
        ],
        "producer": [
            (
                "z00z-y11y-x22x",
                "RX898",
                [PointerTypes.EOL_CARE_PLAN.value],
                [],
            ),  # http://snomed.info/sct|736373009
            (
                "app-t004",
                "ODS1",
                [PointerTypes.PERSONALISED_CARE_AND_SUPPORT_PLAN.value],
                [],
            ),
            (
                "z00z-y11y-x22x",
                "4LLTYP35P",
                [],
                [
                    AccessControls.ALLOW_ALL_TYPES.value,
                    AccessControls.ALLOW_OVERRIDE_CREATION_DATETIME.value,
                ],
            ),
        ],
    }
    [
        _write_permission_file(
            Path.joinpath(local_path, actor_type, app_id),
            ods_code,
            pointer_types,
            access_controls,
        )
        for actor_type, entries in org_permissions.items()
        for app_id, ods_code, pointer_types, access_controls in entries
    ]
    app_permissions = {
        "consumer": [
            ("app-t001", [PointerTypes.MENTAL_HEALTH_PLAN.value], []),
            (
                "app-t002",
                [
                    PointerTypes.ADVANCE_CARE_PLAN.value,
                    PointerTypes.EMERGENCY_HEALTHCARE_PLAN.value,
                    PointerTypes.NEWS2_CHART.value,
                ],
                [],
            ),
            ("app-t004", [PointerTypes.APPOINTMENT.value], []),
        ],
        "producer": [
            ("app-t001", [PointerTypes.EOL_COORDINATION_SUMMARY.value], []),
            (
                "app-t003",
                [
                    PointerTypes.ADVANCE_CARE_PLAN.value,
                    PointerTypes.EMERGENCY_HEALTHCARE_PLAN.value,
                    PointerTypes.NEWS2_CHART.value,
                ],
                [],
            ),
            ("app-t004", [PointerTypes.APPOINTMENT.value], []),
        ],
    }
    [
        _write_permission_file(
            Path.joinpath(local_path, actor_type),
            app_id,
            pointer_types,
            access_controls,
        )
        for actor_type, entries in app_permissions.items()
        for app_id, pointer_types, access_controls in entries
    ]


def download_files(s3_client, bucket_name, local_path, file_names, folders):
    print(f"Downloading {len(file_names)} S3 files to temporary directory...")
    local_path = Path(local_path)

    for folder in folders:
        folder_path = Path.joinpath(local_path, folder)
        # Create all folders in the path
        folder_path.mkdir(parents=True, exist_ok=True)

    for file_name in file_names:
        file_path = Path.joinpath(local_path, file_name)
        # Create folder for parent directory
        file_path.parent.mkdir(parents=True, exist_ok=True)
        s3_client.download_file(bucket_name, file_name, str(file_path))

    add_test_files("K6PerformanceTest", "Y05868.json", local_path)
    add_feature_test_files(local_path)


def main(use_shared_resources: str, env: str, workspace: str, path_to_store: str):
    stack_name = env if use_shared_resources else workspace

    bucket = f"nhsd-nrlf--{stack_name}-authorization-store"
    boto_session = get_boto_session(env)

    s3 = boto_session.client("s3")
    files, folders = get_file_folders(s3, bucket)

    download_files(
        s3,
        bucket,
        path.abspath(path.join(path_to_store + "/nrlf_permissions")),
        files,
        folders,
    )
    print("Downloaded S3 permissions...")


if __name__ == "__main__":
    fire.Fire(main)
