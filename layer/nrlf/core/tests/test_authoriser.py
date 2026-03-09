from unittest.mock import mock_open, patch

from nrlf.core.authoriser import get_pointer_permissions_v2, parse_permissions_file
from nrlf.core.logger import LogReference, logger
from nrlf.core.request import parse_headers
from nrlf.tests.events import create_headers


def test_authoriser_parse_permission_file_with_no_permission_file():
    metadata_result = parse_permissions_file(
        connection_metadata=parse_headers(create_headers(ods_code="SomeCode")),
    )

    assert metadata_result == []


def test_authoriser_parse_permission_file_with_permission_file():
    metadata_result = parse_permissions_file(
        connection_metadata=parse_headers(create_headers(ods_code="TestCode")),
    )

    assert metadata_result == ["http://snomed.info/sct|736253001"]


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data='{"types": ["http://snomed.info/sct|736253001"]}',
)
def test_authoriser_get_v2_permissions_with_org_pointer_types(mock_file, mocker):
    spy = mocker.spy(logger, "log")

    expected_lookup_key = "producer/ODS123-app-id/ODS123.json"
    connection_metadata = parse_headers(
        create_headers(ods_code="ODS123", nrl_app_id="ODS123-app-id")
    )
    result = get_pointer_permissions_v2(
        connection_metadata=connection_metadata,
        request_path="/producer/DocumentReference/_search",
    )

    mock_file.assert_called_once_with(
        f"/opt/python/nrlf_permissions/{expected_lookup_key}"
    )
    assert result.get("types") == ["http://snomed.info/sct|736253001"]

    spy.assert_called_with(LogReference.V2PERMISSIONS011, key=expected_lookup_key)


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data='{"types": ["http://snomed.info/sct|736253001"]}',
)
@patch("os.path.isfile")
def test_authoriser_get_v2_permissions_with_app_pointer_types(
    mock_isfile, mock_file, mocker
):
    spy = mocker.spy(logger, "log")
    mock_isfile.return_value = True

    expected_lookup_key = "producer/ODS123-app-id.json"
    connection_metadata = parse_headers(
        create_headers(ods_code="ODS123", nrl_app_id="ODS123-app-id")
    )
    result = get_pointer_permissions_v2(
        connection_metadata=connection_metadata,
        request_path="/producer/DocumentReference/_search",
    )

    mock_file.assert_called_once_with(
        f"/opt/python/nrlf_permissions/{expected_lookup_key}"
    )
    assert result.get("types") == ["http://snomed.info/sct|736253001"]

    spy.assert_called_with(LogReference.V2PERMISSIONS011, key=expected_lookup_key)


def test_authoriser_parse_v2_permission_file_with_no_permission_file(mocker):
    spy = mocker.spy(logger, "log")
    expected_lookup_key = "consumer/NotAnApp/NotFound.json"

    metadata_result = get_pointer_permissions_v2(
        connection_metadata=parse_headers(
            create_headers(ods_code="NotFound", nrl_app_id="NotAnApp")
        ),
        request_path="/consumer/_status",
    )

    assert metadata_result == {}

    spy.assert_any_call(LogReference.V2PERMISSIONS011, key=expected_lookup_key)
