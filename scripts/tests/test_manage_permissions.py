import json
from unittest.mock import MagicMock, patch

import pytest
from manage_permissions import (
    add_perm,
    clear_perms,
    list_apps,
    list_orgs,
    remove_perm,
    show_perms,
)

from nrlf.core.constants import AccessControls, PointerTypes

MODULE = "manage_permissions"

APP_ID = "test-app-001"
ORG_ODS = "X26"
BUCKET = "nhsd-nrlf--dev-authorization-store"

SAMPLE_POINTER_TYPES = [
    PointerTypes.MENTAL_HEALTH_PLAN.value,
    PointerTypes.ADVANCE_CARE_PLAN.value,
]
SAMPLE_ACCESS_CONTROLS = [
    AccessControls.ALLOW_ALL_TYPES.value,
    AccessControls.ALLOW_OVERRIDE_CREATION_DATETIME.value,
]

_NoSuchKey = type("NoSuchKey", (Exception,), {})


def _make_s3_mock(
    body: bytes | None = None, raise_no_such_key: bool = False
) -> MagicMock:
    s3 = MagicMock()
    s3.exceptions.NoSuchKey = _NoSuchKey
    if raise_no_such_key:
        s3.get_object.side_effect = _NoSuchKey("key not found")
    elif body is not None:
        import io

        s3.get_object.return_value = {"Body": io.BytesIO(body)}
    return s3


def _make_paginator(pages: list[dict]) -> MagicMock:
    paginator = MagicMock()
    paginator.paginate.return_value = pages
    return paginator


# ---------------------------------------------------------------------------
# show_perms
# ---------------------------------------------------------------------------


@patch(f"{MODULE}._get_s3_client")
def test_show_perms_prints_all_permissions(mock_get_s3, capsys):
    existing_perms = {
        "types": SAMPLE_POINTER_TYPES,
        "access_controls": SAMPLE_ACCESS_CONTROLS,
    }
    mock_get_s3.return_value = _make_s3_mock(body=json.dumps(existing_perms).encode())

    show_perms("consumer", APP_ID, ORG_ODS)

    output = capsys.readouterr().out
    for pointer_type in SAMPLE_POINTER_TYPES:
        assert pointer_type in output
    for control in SAMPLE_ACCESS_CONTROLS:
        assert control in output


@patch(f"{MODULE}._get_s3_client")
def test_show_perms_prints_no_file_message_when_missing(mock_get_s3, capsys):
    s3 = _make_s3_mock(raise_no_such_key=True)
    mock_get_s3.return_value = s3

    show_perms("consumer", APP_ID, ORG_ODS)

    assert "No permissions file found" in capsys.readouterr().out


@patch(f"{MODULE}._get_s3_client")
def test_show_perms_prints_no_perms_message_when_empty_json(mock_get_s3, capsys):
    perms = {}
    s3 = _make_s3_mock(body=json.dumps(perms).encode())
    mock_get_s3.return_value = s3

    show_perms("producer", APP_ID, ORG_ODS)

    assert "No permissions found" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# add_perm
# ---------------------------------------------------------------------------


@patch(f"{MODULE}._get_s3_client")
def test_add_perm_adds_new_type(mock_get_s3):
    existing_perms = {"types": [SAMPLE_POINTER_TYPES[0]]}
    s3 = _make_s3_mock(body=json.dumps(existing_perms).encode())
    mock_get_s3.return_value = s3

    add_perm("types", "producer", APP_ID, None, SAMPLE_POINTER_TYPES[1])

    s3.put_object.assert_called_once_with(
        Bucket=BUCKET,
        Key=f"producer/{APP_ID}.json",
        Body=json.dumps({"types": SAMPLE_POINTER_TYPES}, indent=4),
        ContentType="application/json",
    )


@patch(f"{MODULE}._get_s3_client")
def test_add_perm_all_keyword_adds_all_types(mock_get_s3):
    existing_perms = {}
    s3 = _make_s3_mock(body=json.dumps(existing_perms).encode())
    mock_get_s3.return_value = s3

    add_perm("types", "consumer", APP_ID, ORG_ODS, "all")

    s3.put_object.assert_called_once_with(
        Bucket=BUCKET,
        Key=f"consumer/{APP_ID}/{ORG_ODS}.json",
        Body=json.dumps({"types": PointerTypes.list()}, indent=4),
        ContentType="application/json",
    )


@patch(f"{MODULE}._get_s3_client")
@patch(f"{MODULE}.COMPARE_AND_CONFIRM", True)
@patch("builtins.input", return_value="yes")
def test_add_perm_adds_access_control(mock_input, mock_get_s3):
    existing_perms = {}
    s3 = _make_s3_mock(body=json.dumps(existing_perms).encode())
    mock_get_s3.return_value = s3

    add_perm(
        "access_controls",
        "producer",
        APP_ID,
        None,
        AccessControls.ALLOW_ALL_TYPES.value,
    )

    s3.put_object.assert_called_once_with(
        Bucket=BUCKET,
        Key=f"producer/{APP_ID}.json",
        Body=json.dumps(
            {"access_controls": [AccessControls.ALLOW_ALL_TYPES.value]}, indent=4
        ),
        ContentType="application/json",
    )


@patch(f"{MODULE}._get_s3_client")
def test_add_perm_rejects_already_assigned_items(mock_get_s3, capsys):
    existing_perms = {"types": SAMPLE_POINTER_TYPES}
    mock_get_s3.return_value = _make_s3_mock(body=json.dumps(existing_perms).encode())

    add_perm("types", "consumer", APP_ID, None, SAMPLE_POINTER_TYPES[0])

    assert "already assigned" in capsys.readouterr().out


@patch(f"{MODULE}._get_s3_client")
@patch(f"{MODULE}.COMPARE_AND_CONFIRM", True)
@patch("builtins.input", return_value="no")
def test_add_perm_cancelled_by_user_does_not_save(mock_input, mock_get_s3):
    existing_perms = {}
    s3 = _make_s3_mock(body=json.dumps(existing_perms).encode())
    mock_get_s3.return_value = s3

    add_perm("types", "consumer", APP_ID, None, SAMPLE_POINTER_TYPES[0])

    s3.put_object.assert_not_called()


def test_add_perm_rejects_invalid_permission_key(capsys):
    add_perm("invalid_key", "consumer", APP_ID, None, SAMPLE_POINTER_TYPES[0])

    assert "invalid permission" in capsys.readouterr().out.lower()


def test_add_perm_rejects_no_items(capsys):
    add_perm("types", "producer", APP_ID, ORG_ODS)

    assert "no pointer types provided" in capsys.readouterr().out


def test_add_perm_rejects_unknown_items(capsys):
    add_perm("types", "consumer", APP_ID, None, "http://unknown.example.com|999")

    assert "Unknown pointer types provided" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# remove_perm
# ---------------------------------------------------------------------------


@patch(f"{MODULE}._get_s3_client")
def test_remove_perm_removes_type(mock_get_s3):
    existing_perms = {"types": SAMPLE_POINTER_TYPES}
    s3 = _make_s3_mock(body=json.dumps(existing_perms).encode())
    mock_get_s3.return_value = s3

    type_to_remove = SAMPLE_POINTER_TYPES[0]

    remove_perm("types", "consumer", APP_ID, ORG_ODS, type_to_remove)

    saved_perms = s3.put_object.call_args[1]["Body"]
    assert type_to_remove not in saved_perms
    assert SAMPLE_POINTER_TYPES[1] in saved_perms


@patch(f"{MODULE}._get_s3_client")
def test_remove_perm_removes_access_control(mock_get_s3):
    existing_perms = {"access_controls": SAMPLE_ACCESS_CONTROLS}
    s3 = _make_s3_mock(body=json.dumps(existing_perms).encode())
    mock_get_s3.return_value = s3

    control_to_remove = SAMPLE_ACCESS_CONTROLS[0]

    remove_perm("access_controls", "producer", APP_ID, None, control_to_remove)

    saved_perms = s3.put_object.call_args[1]["Body"]
    assert control_to_remove not in saved_perms
    assert SAMPLE_ACCESS_CONTROLS[1] in saved_perms


@patch(f"{MODULE}._get_s3_client")
def test_remove_perm_skips_update_if_all_items_not_currently_assigned(
    mock_get_s3, capsys
):
    existing_perms = {"types": [SAMPLE_POINTER_TYPES[0]]}
    mock_get_s3.return_value = _make_s3_mock(body=json.dumps(existing_perms).encode())

    remove_perm("types", "consumer", APP_ID, None, SAMPLE_POINTER_TYPES[1])

    assert (
        "Skipping: None of the requested pointer types are assigned"
        in capsys.readouterr().out
    )
    mock_get_s3.put_object.assert_not_called()


@patch(f"{MODULE}._get_s3_client")
def test_remove_perm_skips_items_not_currently_assigned(mock_get_s3, capsys):
    existing_perms = {"access_controls": [SAMPLE_ACCESS_CONTROLS[0]]}
    s3 = _make_s3_mock(body=json.dumps(existing_perms).encode())
    mock_get_s3.return_value = s3

    remove_perm(
        "access_controls",
        "producer",
        APP_ID,
        ORG_ODS,
        SAMPLE_ACCESS_CONTROLS[0],
        SAMPLE_ACCESS_CONTROLS[1],
    )

    assert "Skipping access controls not already assigned" in capsys.readouterr().out
    s3.put_object.assert_called_once_with(
        Bucket=BUCKET,
        Key=f"producer/{APP_ID}/{ORG_ODS}.json",
        Body=json.dumps({"access_controls": []}, indent=4),
        ContentType="application/json",
    )


@patch(f"{MODULE}._get_s3_client")
def test_remove_perm_returns_early_if_no_perms_file(mock_get_s3, capsys):
    mock_get_s3.return_value = _make_s3_mock(raise_no_such_key=True)

    remove_perm("types", "consumer", APP_ID, ORG_ODS, SAMPLE_POINTER_TYPES[0])

    assert "does not exist" in capsys.readouterr().out


@patch(f"{MODULE}._get_s3_client")
@patch(f"{MODULE}.COMPARE_AND_CONFIRM", True)
@patch("builtins.input", return_value="no")
def test_remove_perm_cancelled_by_user_does_not_save(mock_input, mock_get_s3):
    existing_perms = {"types": SAMPLE_POINTER_TYPES}
    s3 = _make_s3_mock(body=json.dumps(existing_perms).encode())
    mock_get_s3.return_value = s3

    remove_perm("types", "consumer", APP_ID, None, SAMPLE_POINTER_TYPES[0])

    mock_get_s3.put_object.assert_not_called()


def test_remove_perm_rejects_invalid_permission_key(capsys):
    remove_perm("invalid_key", "consumer", APP_ID, None, SAMPLE_POINTER_TYPES[0])

    assert "invalid permission" in capsys.readouterr().out.lower()


def test_remove_perm_rejects_no_items(capsys):
    remove_perm("types", "producer", APP_ID)

    assert "No pointer types provided" in capsys.readouterr().out


def test_remove_perm_rejects_unknown_items(capsys):
    remove_perm("types", "consumer", APP_ID, ORG_ODS, "http://unknown.example.com|999")

    assert "Unknown pointer types provided" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# clear_perms
# ---------------------------------------------------------------------------


@patch(f"{MODULE}._get_s3_client")
def test_clear_perms_saves_empty_dict(mock_get_s3):
    existing_perms = {
        "types": SAMPLE_POINTER_TYPES,
        "access_controls": SAMPLE_ACCESS_CONTROLS,
    }
    s3 = _make_s3_mock(body=json.dumps(existing_perms).encode())
    mock_get_s3.return_value = s3

    clear_perms("consumer", APP_ID)

    saved_perms = s3.put_object.call_args[1]["Body"]
    assert saved_perms == "{}"


@patch(f"{MODULE}._get_s3_client")
@patch(f"{MODULE}.COMPARE_AND_CONFIRM", True)
@patch("builtins.input", return_value="no")
def test_clear_perms_cancelled_by_user_does_not_save(mock_input, mock_get_s3):
    existing_perms = {"types": SAMPLE_POINTER_TYPES}
    s3 = _make_s3_mock(body=json.dumps(existing_perms).encode())
    mock_get_s3.return_value = s3

    clear_perms("consumer", APP_ID)

    s3.put_object.assert_not_called()


@patch(f"{MODULE}._get_s3_client")
def test_clear_perms_skips_when_no_perms_exist(mock_get_s3, capsys):
    mock_get_s3.return_value = _make_s3_mock(raise_no_such_key=True)

    clear_perms("consumer", APP_ID)

    assert "no permissions" in capsys.readouterr().out.lower()


@patch(f"{MODULE}._get_s3_client")
def test_clear_perms_skips_when_perms_is_empty_json(mock_get_s3, capsys):
    mock_get_s3.return_value = _make_s3_mock(body=json.dumps({}).encode())

    clear_perms("producer", APP_ID, ORG_ODS)

    assert "no permissions" in capsys.readouterr().out.lower()


# ---------------------------------------------------------------------------
# list_apps
# ---------------------------------------------------------------------------


@patch(f"{MODULE}._get_s3_client")
def test_list_apps_groups_app_level_and_org_level(mock_get_s3, capsys):
    s3 = MagicMock()
    mock_get_s3.return_value = s3
    # Simulate: first key is the folder itself, then org-level and app-level perms
    s3.get_paginator.return_value = _make_paginator(
        [
            {
                "Contents": [
                    {"Key": "consumer/"},
                    {"Key": "consumer/app-with-org-perms/"},
                    {"Key": "consumer/app-with-only-app-perms.json"},
                ]
            },
        ]
    )

    list_apps("consumer")

    output = capsys.readouterr().out
    assert "org-level permissions:\n- app-with-org-perms" in output
    assert "app-level permissions:\n- app-with-only-app-perms" in output


@patch(f"{MODULE}._get_s3_client")
def test_list_apps_no_apps_found(mock_get_s3, capsys):
    s3 = MagicMock()
    mock_get_s3.return_value = s3
    s3.get_paginator.return_value = _make_paginator([{}])

    list_apps("consumer")

    output = capsys.readouterr().out
    assert "No applications found" in output


@patch(f"{MODULE}._get_s3_client")
def test_list_apps_invalid_supplier_type_prints_error(mock_get_s3, capsys):
    list_apps("invalid")

    mock_get_s3.assert_not_called()
    assert "invalid supplier" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# list_orgs
# ---------------------------------------------------------------------------


@patch(f"{MODULE}._get_s3_client")
def test_list_orgs_invalid_supplier_prints_error(mock_get_s3, capsys):
    list_orgs("invalid", APP_ID)

    mock_get_s3.assert_not_called()
    assert "invalid supplier" in capsys.readouterr().out


@patch(f"{MODULE}._get_s3_client")
def test_list_orgs_no_orgs_found(mock_get_s3, capsys):
    s3 = MagicMock()
    mock_get_s3.return_value = s3
    s3.get_paginator.return_value = _make_paginator([{}])

    list_orgs("producer", APP_ID)

    assert "No organizations found" in capsys.readouterr().out


@patch(f"{MODULE}._get_s3_client")
def test_list_orgs_lists_org_codes(mock_get_s3, capsys):
    s3 = MagicMock()
    mock_get_s3.return_value = s3
    # Simulate: first key is the folder itself, then org-level and app-level perms
    s3.get_paginator.return_value = _make_paginator(
        [
            {
                "Contents": [
                    {"Key": "producer/"},
                    {
                        "Key": f"producer/{APP_ID}/X26.json",
                    },
                    {
                        "Key": f"producer/{APP_ID}/Y27.json",
                    },
                ]
            },
        ]
    )

    list_orgs("producer", APP_ID)

    output = capsys.readouterr().out
    assert "There are 2 organizations for app test-app-001:\n- X26\n- Y27" in output
