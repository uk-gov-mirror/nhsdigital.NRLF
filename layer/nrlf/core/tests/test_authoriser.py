from nrlf.core.authoriser import get_pointer_permissions_v2, parse_permissions_file
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


v2_test_lookup_path = "layer/test_permissions/v2"


def test_authoriser_get_v2_permissions_with_pointer_types():
    connection_metadata = parse_headers(
        create_headers(ods_code="ODS123", nrl_app_id="ODS123-app-id")
    )

    result = get_pointer_permissions_v2(
        connection_metadata=connection_metadata,
        request_path="/producer/DocumentReference/_search",
        lookup_path=v2_test_lookup_path,
    )

    assert result.get("types") == ["http://snomed.info/sct|736253001"]


def test_authoriser_parse_v2_permission_file_with_no_permission_file():
    metadata_result = get_pointer_permissions_v2(
        connection_metadata=parse_headers(create_headers(ods_code="NotFound")),
        request_path="/consumer/_status",
        lookup_path=v2_test_lookup_path,
    )

    assert metadata_result == {}
