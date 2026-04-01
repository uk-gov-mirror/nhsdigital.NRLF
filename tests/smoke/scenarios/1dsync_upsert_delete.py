import pytest

from nrlf.core.constants import PERMISSION_ALLOW_ALL_POINTER_TYPES, V2Headers
from tests.smoke.environment import ConnectMode, EnvironmentConfig, SmokeTestParameters
from tests.smoke.setup import build_document_reference
from tests.utilities.api_clients import ConnectionMetadata, ProducerTestClient

v2_1dsync_app_id = "SMOKETEST_1DSYNC_V1"


@pytest.fixture
def producer_client_1dsync(
    environment_config: EnvironmentConfig, smoke_test_parameters: SmokeTestParameters
) -> ProducerTestClient:
    client_config = environment_config.to_client_config(smoke_test_parameters)

    if environment_config.connect_mode == ConnectMode.INTERNAL.value:
        # Use app-level perms in internal mode
        connection_metadata = ConnectionMetadata.model_validate(
            {
                "nrl.permissions": [PERMISSION_ALLOW_ALL_POINTER_TYPES],
                "nrl.app-id": v2_1dsync_app_id,
                "nrl.ods-code": smoke_test_parameters.ods_code,
                "client_rp_details": {
                    "developer.app.name": smoke_test_parameters.apigee_app_name,
                    "developer.app.id": smoke_test_parameters.apigee_app_id,
                },
            }
        )
        client_config.connection_metadata = connection_metadata
        client_config.custom_headers[V2Headers.X_PROXYGEN_APP_NRL_APP_ID] = (
            v2_1dsync_app_id
        )
    else:
        # Can't use app-level perms here without setting up another apigee app, use ODS instead
        client_config.custom_headers["NHSD-End-User-Organisation-ODS"] = (
            "SMOKETEST1DSYNC"
        )

    return ProducerTestClient(config=client_config)


def test_smoke_1dsync_upsert_delete(
    producer_client_1dsync: ProducerTestClient,
    smoke_test_parameters: SmokeTestParameters,
    test_nhs_numbers: list[str],
):
    """
    Smoke test scenario for 1dsync upsert and delete behaviour
    """
    test_ods_code = producer_client_1dsync.config.custom_headers.get(
        "NHSD-End-User-Organisation-ODS"
    )
    test_docref = build_document_reference(
        nhs_number=test_nhs_numbers[0], custodian=test_ods_code
    )

    for attempts in range(0, 5):
        try:
            test_docref.id = (
                f"{test_ods_code}-smoketest_1dsync_upsert_delete_pointer_{attempts}"
            )
            upsert_response = producer_client_1dsync.upsert(
                test_docref.model_dump(exclude_none=True)
            )
            assert upsert_response.ok
            assert upsert_response.headers["Location"].split("/")[-1] == test_docref.id
        finally:
            delete_response = producer_client_1dsync.delete(test_docref.id)

            assert (
                delete_response.ok
            ), f"Failed to delete document reference with ID: {test_docref.id}. It will need to be deleted manually if it still exists."

            read_response = producer_client_1dsync.read(test_docref.id)
            assert read_response.status_code == 404
