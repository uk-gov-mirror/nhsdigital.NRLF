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


def _write_v1_permission_file(folder_path, ods_code, pointer_types):
    folder_path.mkdir(parents=True, exist_ok=True)
    with open(folder_path / f"{ods_code}.json", "w") as f:
        json.dump(pointer_types, f)


def add_feature_test_files(local_path):
    """Bake in v2 permissions for the feature test application so that the
    v2 permissions model can be proven via feature tests without
    requiring a dynamic layer rebuild between test setup and test execution.
    """

    print("Adding feature test v2 permissions to temporary directory...")
    org_permissions = {
        "consumer": [
            (
                "v2-z00z-y11y-x22x",
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
                "v2-z00z-y11y-x22x",
                "4LLTYP35C",
                [],
                [AccessControls.ALLOW_ALL_TYPES.value],
            ),
        ],
        "producer": [
            (
                "v2-z00z-y11y-x22x",
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
                "v2-z00z-y11y-x22x",
                "4LLTYP35P",
                [],
                [
                    AccessControls.ALLOW_ALL_TYPES.value,
                    AccessControls.ALLOW_OVERRIDE_CREATION_DATETIME.value,
                    AccessControls.ALLOW_SUPERSEDE_WITH_DELETE_FAILURE.value,
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

    print("Adding feature test v1 permissions to temporary directory...")
    v1_permissions = [
        (
            "v2-z00z-y11y-x22x",
            "V1ONLY0D5",
            [PointerTypes.LLOYD_GEORGE_FOLDER.value],
        ),  # http://snomed.info/sct|16521000000101
    ]
    [
        _write_v1_permission_file(
            Path.joinpath(local_path, app_id),
            ods_code,
            pointer_types,
        )
        for app_id, ods_code, pointer_types in v1_permissions
    ]


def add_smoke_test_files(secretsmanager, local_path, env_name):
    """Bake in v2 permissions for the smoke test application so that the
    v2 permissions model can be proven via smoke tests without
    requiring a dynamic layer rebuild between test setup and test execution.
    """

    parameters_name = f"nhsd-nrlf--{env_name}--smoke-test-parameters"

    secret_value = secretsmanager.get_secret_value(SecretId=parameters_name)
    parameters = json.loads(secret_value["SecretString"])
    smoke_test_app_id = parameters.get("nrlf_app_id")

    print("Adding smoke test v2 permissions to temporary directory...")
    org_permissions = {
        "consumer": [
            (
                smoke_test_app_id,
                "SMOKETEST",
                [
                    PointerTypes.MENTAL_HEALTH_PLAN.value
                ],  # http://snomed.info/sct|736253002
                [],
            ),
        ],
        "producer": [
            (
                smoke_test_app_id,
                "SMOKETEST",
                [
                    PointerTypes.MENTAL_HEALTH_PLAN.value
                ],  # http://snomed.info/sct|736253002
                [],
            ),
            (
                # For public tests - don't have a separate apigee app for 1DSync
                smoke_test_app_id,
                "SMOKETEST1DSYNC",
                [],
                [AccessControls.ALLOW_ALL_TYPES.value],
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
        "producer": [
            (
                "SMOKETEST1DSYNC",
                [],
                [AccessControls.ALLOW_ALL_TYPES.value],
            ),
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

    print("Adding smoke test v1 permissions to temporary directory...")
    v1_permissions = [
        (  # not needed, won't hit this file
            "SMOKETEST1DSYNCV1",
            "SMOKETEST",
            [],
        ),
        (
            smoke_test_app_id,
            "SMOKETESTV1",
            [PointerTypes.MENTAL_HEALTH_PLAN.value],  # http://snomed.info/sct|736253002
        ),
    ]
    [
        _write_v1_permission_file(
            Path.joinpath(local_path, app_id),
            ods_code,
            pointer_types,
        )
        for app_id, ods_code, pointer_types in v1_permissions
    ]


def add_sandbox_files(local_path):
    """Add the permissions required for the sandbox environments.
    Only call this function if your want to add sandbox permissions.
    These permissions are taken from the existing permissions in the API repos.
    """
    sandbox_app_id = "NRL-SANDBOX-APP"
    nrl_sandbox_perms = {
        "RJ11": [
            PointerTypes.MENTAL_HEALTH_PLAN.value,  # http://snomed.info/sct|736253002
        ],
        # These ones are needed for the Seed data
        "Y05868": [
            PointerTypes.MENTAL_HEALTH_PLAN.value,  # http://snomed.info/sct|736253002
            PointerTypes.EMERGENCY_HEALTHCARE_PLAN.value,  # http://snomed.info/sct|887701000000100
            PointerTypes.NEWS2_CHART.value,  # http://snomed.info/sct|1363501000000100
            PointerTypes.EOL_COORDINATION_SUMMARY.value,  # http://snomed.info/sct|861421000000109
        ],
        "8J008": [
            PointerTypes.NEWS2_CHART.value
        ],  # http://snomed.info/sct|1363501000000100
        "RY26A": [
            PointerTypes.EOL_COORDINATION_SUMMARY.value
        ],  # http://snomed.info/sct|861421000000109
        # This one is needed for Smoke Tests
        "RM559": [
            PointerTypes.MENTAL_HEALTH_PLAN.value
        ],  # http://snomed.info/sct|736253002
    }

    for ods_code, snomed_codes in nrl_sandbox_perms.items():
        _write_permission_file(
            Path.joinpath(local_path, "producer", sandbox_app_id),
            ods_code,
            snomed_codes,
        )
        _write_permission_file(
            Path.joinpath(local_path, "consumer", sandbox_app_id),
            ods_code,
            snomed_codes,
        )
        _write_v1_permission_file(
            Path.joinpath(local_path, sandbox_app_id),
            ods_code,
            snomed_codes,
        )


def download_files(
    s3_client, bucket_name, local_path, file_names, folders, secretsmanager, env_name
):
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
    add_smoke_test_files(secretsmanager, local_path, env_name)

    if env_name in ["dev-sandbox", "qa-sandbox", "int-sandbox"]:
        add_sandbox_files(local_path)


def main(use_shared_resources: str, env: str, workspace: str, path_to_store: str):
    stack_name = env if use_shared_resources else workspace

    bucket = f"nhsd-nrlf--{stack_name}-authorization-store"
    boto_session = get_boto_session(env)

    s3 = boto_session.client("s3")
    files, folders = get_file_folders(s3, bucket)

    secretsmanager = boto_session.client("secretsmanager", region_name="eu-west-2")
    download_files(
        s3,
        bucket,
        path.abspath(path.join(path_to_store + "/nrlf_permissions")),
        files,
        folders,
        secretsmanager,
        env_name=env,
    )
    print("Downloaded S3 permissions...")


if __name__ == "__main__":
    fire.Fire(main)
