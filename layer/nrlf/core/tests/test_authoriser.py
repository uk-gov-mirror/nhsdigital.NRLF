from nrlf.core.authoriser import get_pointer_permissions, parse_permissions_file
from nrlf.core.config import Config
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


def test_authoriser_get_pointer_permissions_first_pass():
    connection_metadata = parse_headers(
        create_headers(ods_code="ODS123", nrl_app_id="ODS123-app-id")
    )

    result = get_pointer_permissions(
        connection_metadata=connection_metadata,
        config=Config(AUTH_STORE="auth-store-i-promise"),
        request_path="/producer/DocumentReference/_search",
    )

    assert result == {"types": ["http://snomed.info/sct|736253001"]}
