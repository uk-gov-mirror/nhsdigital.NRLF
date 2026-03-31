from tests.utilities.api_clients import ConsumerTestClient, ProducerTestClient


def test_smoke_read_api_capability_statements_v1(
    consumer_client_v1: ConsumerTestClient, producer_client_v1: ProducerTestClient
):
    """
    Smoke test scenario for reading the API capability statements
    """
    read_response = consumer_client_v1.read_capability_statement()
    assert read_response.ok

    read_response = producer_client_v1.read_capability_statement()
    assert read_response.ok
