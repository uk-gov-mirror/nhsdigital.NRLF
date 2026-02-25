from nrlf.core.authoriser import parse_permissions_file
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


# @mock_aws
# def test_authoriser_get_pointer_permissions_first_pass(mocker):
#     # Spy on key used to lookup in s3?
#     spy = mocker.spy(logger, "log")

#     # conn = boto3.resource("s3", region_name="eu-west-2")
#     # # We need to create the bucket since this is all in Moto's 'virtual' AWS account
#     # conn.create_bucket(Bucket="auth-store-i-promise")

#     rp_deets = ClientRpDetails.model_validate(
#         {"developer.app.name": "ODS123-app-id", "developer.app.id": "ODS123-app-id"}
#     )

#     conn = ConnectionMetadata.model_validate(
#         {
#             "nrl.ods-code": "ODS123",
#             "nrl.app-id": "ODS123-app-id",
#             "client_rp_details": rp_deets,
#         }
#     )

#     get_pointer_permissions(
#         connection_metadata=conn,  # fix this guy
#         config=Config(AUTH_STORE="auth-store-i-promise"),
#         request_path="/producer/DocumentReference/_search",
#     )

#     expected_path = "producer/ODS123-app-id/ODS123.json"

#     spy.assert_called_with(LogReference.S3PERMISSIONS011, expected_path)
