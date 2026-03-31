from typing import Any, Generator

import pytest

from tests.smoke.environment import SmokeTestParameters
from tests.smoke.setup import build_document_reference, upsert_test_pointer
from tests.utilities.api_clients import ConsumerTestClient, ProducerTestClient


@pytest.fixture
def test_data_v1(
    test_nhs_numbers: list[str],
    producer_client_v1: ProducerTestClient,
    smoke_test_parameters: SmokeTestParameters,
) -> Generator[str, Any, None]:
    test_ods_code = smoke_test_parameters.v1_ods_code
    test_pointers = [
        upsert_test_pointer(
            f"{test_ods_code}-smoketest_consumer_search_read_pointer_{n}",
            docref=build_document_reference(
                nhs_number=test_nhs_numbers[0], custodian=test_ods_code
            ),
            producer_client=producer_client_v1,
        )
        for n in range(0, 5)
    ]

    test_data_v1 = {
        "patient_nhs_number": test_nhs_numbers[0],
        "pointers": test_pointers,
    }

    yield test_data_v1

    for test_pointer in test_pointers:
        producer_client_v1.delete(test_pointer.id)


def test_smoke_consumer_search_read(
    consumer_client: ConsumerTestClient, test_data_v1: dict
):
    """
    Smoke test scenario for a consumer search and read behavior
    """
    patient_id = test_data_v1["patient_nhs_number"]
    test_pointers = test_data_v1["pointers"]

    # Search
    search_response = consumer_client.search(patient_id)
    assert search_response.ok
    assert search_response.json()["total"] >= len(test_pointers)

    # Search with POST
    search_response = consumer_client.search_post(patient_id)
    assert search_response.ok
    assert search_response.json()["total"] >= len(test_pointers)

    # Read
    read_response = consumer_client.read(test_pointers[0].id)
    assert read_response.ok
    assert read_response.json()["id"] == test_pointers[0].id
    assert read_response.json()["subject"]["identifier"]["value"] == patient_id
    assert read_response.json()["status"] == "current"
