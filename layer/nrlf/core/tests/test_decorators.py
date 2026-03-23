import json
import warnings
from typing import Any

import pytest
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from pydantic import BaseModel
from pytest_mock import MockerFixture

from nrlf.core.codes import SpineErrorConcept
from nrlf.core.config import Config
from nrlf.core.constants import (
    PERMISSION_ALLOW_ALL_POINTER_TYPES,
    X_REQUEST_ID_HEADER,
    AccessControls,
    ConsumerApiInteractions,
    PointerTypes,
    ProducerApiInteractions,
    V2Headers,
)
from nrlf.core.decorators import (
    _parse_function_name,
    deprecated,
    error_handler,
    header_handler,
    load_connection_metadata,
    logger_initialiser,
    request_handler,
    verify_request_ids,
)
from nrlf.core.errors import OperationOutcomeError
from nrlf.core.logger import LogReference
from nrlf.core.response import Response
from nrlf.tests.events import (
    create_headers,
    create_mock_context,
    create_test_api_gateway_event,
    default_response_headers,
)


def test_error_handler_decorator():
    @error_handler
    def decorated_function():
        return {"message": "Hello, World!"}

    result = decorated_function()
    assert result == {"message": "Hello, World!"}


def test_operation_outcome_error():
    @error_handler
    def decorated_function():
        raise OperationOutcomeError(
            status_code="401",
            severity="error",
            code="unauthorized",
            details=SpineErrorConcept.from_code("AUTHOR_CREDENTIALS_ERROR"),
            diagnostics="The requested DocumentReference cannot be read because it belongs to another organisation",
        )

    result = decorated_function()

    assert result["statusCode"] == "401"
    assert result["headers"] == {}
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "unauthorized",
                "details": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                            "code": "AUTHOR_CREDENTIALS_ERROR",
                            "display": "Author credentials error",
                        }
                    ]
                },
                "diagnostics": "The requested DocumentReference cannot be read because it belongs to another organisation",
            }
        ],
    }


def test_error_handler_decorator_error_handling():
    @error_handler
    def decorated_function():
        raise Exception("Something went wrong")

    result = decorated_function()

    assert result["statusCode"] == "500"
    assert result["headers"] == {}
    assert result["isBase64Encoded"] is False

    # The body is a JSON string, so we need to parse it to compare the contents
    parsed_body = json.loads(result["body"])

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "exception",
                "details": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                            "code": "INTERNAL_SERVER_ERROR",
                            "display": "Unexpected internal server error",
                        }
                    ]
                },
                "diagnostics": "Something went wrong",
            }
        ],
    }


def test_header_handler_happy_path():
    @header_handler
    def decorated_function(event):
        return {
            "headers": {
                "Content-Type": "application/json",
            }
        }

    test_event = create_test_api_gateway_event()
    event = APIGatewayProxyEvent(test_event)

    response = decorated_function(event)

    assert response["headers"] == {
        **default_response_headers(),
        "Content-Type": "application/json",
    }


def test_header_handler_when_correlation_id_is_also_present():
    @header_handler
    def decorated_function(event):
        return {
            "headers": {
                "Content-Type": "application/json",
            }
        }

    test_event = create_test_api_gateway_event(
        headers={
            **create_headers(),
            "X-Correlation-Id": "test_correlation_id",
        }
    )
    event = APIGatewayProxyEvent(test_event)

    response = decorated_function(event)

    assert response["headers"] == {
        **default_response_headers(),
        "Content-Type": "application/json",
        "X-Correlation-Id": "test_correlation_id",
    }


def test_header_handler_when_no_response_headers():
    @header_handler
    def decorated_function(event):
        return {}

    test_event = create_test_api_gateway_event()
    event = APIGatewayProxyEvent(test_event)

    response = decorated_function(event)

    assert response["headers"] == default_response_headers()


def test_header_handler_when_no_echoed_headers():
    @header_handler
    def decorated_function(event):
        return {
            "headers": {
                "Content-Type": "application/json",
            }
        }

    test_event = create_test_api_gateway_event(headers={"X-None-Echoed-Header": "test"})
    event = APIGatewayProxyEvent(test_event)

    response = decorated_function(event)

    assert response["headers"] == {
        "Content-Type": "application/json",
    }


def test_header_handler_with_overwritten_response_headers():
    @header_handler
    def decorated_function(event):
        return {
            "headers": {
                "Content-Type": "application/json",
                "X-Request-Id": "test_request_id_overwrite_me",
                "X-Correlation-Id": "test_correlation_id_overwrite_me",
            }
        }

    test_event = create_test_api_gateway_event(
        headers={
            **create_headers(),
            "X-Correlation-Id": "test_correlation_id",
        }
    )
    event = APIGatewayProxyEvent(test_event)

    response = decorated_function(event)

    assert response["headers"] == {
        "Content-Type": "application/json",
        "X-Request-Id": "test_request_id",
        "X-Correlation-Id": "test_correlation_id",
    }


def test_header_handler_when_response_header_checks_fail(mocker: MockerFixture):
    @header_handler
    def decorated_function(event):
        return {
            "headers": {
                "Content-Type": "application/json",
                "X-Request-Id": "test_request_id_not_overwritten",
                "X-Correlation-Id": "test_correlation_id_not_overwritten",
            }
        }

    event = mocker.MagicMock()
    event.get_header_value.side_effect = Exception("Test exception")

    response = decorated_function(event)

    assert response["headers"] == {
        "Content-Type": "application/json",
        "X-Request-Id": "test_request_id_not_overwritten",
        "X-Correlation-Id": "test_correlation_id_not_overwritten",
    }


def test_logger_initialiser_happy_path(mocker: MockerFixture):
    mock_logger = mocker.patch("nrlf.core.decorators.logger")

    @logger_initialiser
    def decorated_function(event):
        return {}

    test_event = create_test_api_gateway_event()
    event = APIGatewayProxyEvent(test_event)

    decorated_function(event)

    mock_logger.set_correlation_id.assert_called_once_with("test_correlation_id")


def test_logger_initialiser_no_correlation_id(mocker: MockerFixture):
    mock_logger = mocker.patch("nrlf.core.decorators.logger")

    @logger_initialiser
    def decorated_function(event):
        return {}

    test_event = create_test_api_gateway_event(
        headers={
            **create_headers(),
            "NHSD-Correlation-Id": None,
        }
    )
    event = APIGatewayProxyEvent(test_event)

    decorated_function(event)

    mock_logger.set_correlation_id.assert_not_called()
    mock_logger.log.assert_called_once_with(
        LogReference.HANDLER017,
        id_header="NHSD-Correlation-Id",
        headers=test_event["headers"],
    )


def test_log_includes_client_cert_details(mocker: MockerFixture):
    @request_handler()
    def decorated_function() -> Response:
        return Response(
            statusCode="200",
            body=json.dumps({"message": "Hello, World!"}),
            headers={"Content-Type": "application/json"},
        )

    test_event = create_test_api_gateway_event()
    event = APIGatewayProxyEvent(test_event)

    mock_logger = mocker.patch("nrlf.core.decorators.logger")

    decorated_function(event, create_mock_context())

    assert any(
        call[1]["code"].name == "HANDLER000"
        for call in mock_logger.log.call_args_list
        if call[1]
    )

    logged_cert_info: dict[str, Any] = [
        call[1:][0]
        for call in mock_logger.log.call_args_list
        if call[1] and "code" in call[1] and call[1]["code"].name == "HANDLER000"
    ][0]["client_cert_info"]

    client_cert = event.request_context.identity.client_cert
    assert logged_cert_info == {
        "subject_dn": client_cert.subject_dn,
        "issuer_dn": client_cert.issuer_dn,
        "serial_number": client_cert.serial_number,
    }


def test_log_includes_client_cert_details_when_no_cert(mocker: MockerFixture):
    @request_handler()
    def decorated_function() -> Response:
        return Response(
            statusCode="200",
            body=json.dumps({"message": "Hello, World!"}),
            headers={"Content-Type": "application/json"},
        )

    test_event = create_test_api_gateway_event()
    test_event["requestContext"]["identity"]["clientCert"] = None
    event = APIGatewayProxyEvent(test_event)

    mock_logger = mocker.patch("nrlf.core.decorators.logger")

    decorated_function(event, create_mock_context())

    assert any(
        call[1]["code"].name == "HANDLER000"
        for call in mock_logger.log.call_args_list
        if call[1]
    )

    logged_cert_info: dict[str, Any] = [
        call[1:][0]
        for call in mock_logger.log.call_args_list
        if call[1] and "code" in call[1] and call[1]["code"].name == "HANDLER000"
    ][0]["client_cert_info"]

    assert logged_cert_info == "No client certificate provided"


@pytest.mark.parametrize(
    ("long_function_name", "expected"),
    [
        (
            "nhsd-nrlf--anjal-dev--api--producer--deleteDocumentReference",
            ProducerApiInteractions.DELETE_DOCUMENT_REFERENCE.value,
        ),
        (
            "nhsd-nrlf--dev-1--api--consumer--readDocumentReference",
            ConsumerApiInteractions.READ_DOCUMENT_REFERENCE.value,
        ),
        (
            "nhsd-nrlf--int-1--api--consumer--searchPostDocumentReference",
            ConsumerApiInteractions.SEARCH_POST_DOCUMENT_REFERENCE.value,
        ),
        (
            "nhsd-nrlf--dev-sandbox-2--api--producer--updateDocumentReference",
            ProducerApiInteractions.UPDATE_DOCUMENT_REFERENCE.value,
        ),
        (
            "nhsd-nrlf--3d9729--api--producer--upsertDocumentReference",
            ProducerApiInteractions.UPSERT_DOCUMENT_REFERENCE.value,
        ),
        (
            "nhsd-nrlf--ref-2--api--producer--searchPostDocumentReference",
            ProducerApiInteractions.SEARCH_POST_DOCUMENT_REFERENCE.value,
        ),
        (
            "nhsd-nrlf--qa-sandbox-2--api--producer--readDocumentReference",
            ProducerApiInteractions.READ_DOCUMENT_REFERENCE.value,
        ),
        # (
        #     "nhsd-nrlf--perftest-1--api--producer--searchPostDocumentReferenc",  # uh oh
        #     ProducerApiInteractions.SEARCH_DOCUMENT_REFERENCE.value,
        # ),
    ],
)
def test_parse_function_name(long_function_name, expected):
    result = _parse_function_name(long_function_name)

    assert result == expected


def test_verify_request_id_happy_path():
    test_event = create_test_api_gateway_event()

    event = APIGatewayProxyEvent(test_event)
    verify_request_ids(event)


def test_verify_request_id_no_request_id():
    test_event = create_test_api_gateway_event()
    test_event["headers"].pop(X_REQUEST_ID_HEADER)

    event = APIGatewayProxyEvent(test_event)
    with pytest.raises(OperationOutcomeError) as err:
        verify_request_ids(event)

    assert err.value.status_code == "400"
    assert err.value.operation_outcome.resourceType == "OperationOutcome"
    assert err.value.operation_outcome.issue[0].severity == "error"
    assert err.value.operation_outcome.issue[0].code == "invalid"
    assert err.value.operation_outcome.issue[0].details == SpineErrorConcept.from_code(
        "MISSING_OR_INVALID_HEADER"
    )
    assert (
        err.value.operation_outcome.issue[0].diagnostics
        == "The X-Request-Id header is missing or invalid"
    )
    assert err.value.operation_outcome.issue[0].expression == None


def test_verify_request_id_no_correlation_id():
    test_event = create_test_api_gateway_event()
    test_event["headers"].pop("NHSD-Correlation-Id")

    event = APIGatewayProxyEvent(test_event)
    with pytest.raises(OperationOutcomeError) as err:
        verify_request_ids(event)

    assert err.value.status_code == "400"
    assert err.value.operation_outcome.resourceType == "OperationOutcome"
    assert err.value.operation_outcome.issue[0].severity == "error"
    assert err.value.operation_outcome.issue[0].code == "invalid"
    assert err.value.operation_outcome.issue[0].details == SpineErrorConcept.from_code(
        "MISSING_OR_INVALID_HEADER"
    )
    assert (
        err.value.operation_outcome.issue[0].diagnostics
        == "The NHSD-Correlation-Id header is missing or invalid"
    )
    assert err.value.operation_outcome.issue[0].expression == None


def test_request_handler_defaults():
    @request_handler()
    def decorated_function() -> Response:
        return Response(
            statusCode="200",
            body=json.dumps({"message": "Hello, World!"}),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(headers=create_headers())
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "200"
    assert result["headers"] == {
        "Content-Type": "application/json",
        **default_response_headers(),
    }
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])
    assert parsed_body == {"message": "Hello, World!"}


def test_request_handler_with_params():
    class MockParams(BaseModel):
        param1: str
        param2: int

    @request_handler(params=MockParams)
    def decorated_function(params) -> Response:
        return Response(
            statusCode="200",
            body=params.model_dump_json(exclude_none=True),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={"param1": "test", "param2": "123"},
    )

    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "200"
    assert result["headers"] == {
        "Content-Type": "application/json",
        **default_response_headers(),
    }
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])
    assert parsed_body == {"param1": "test", "param2": 123}


def test_request_handler_with_params_missing_params():
    class MockParams(BaseModel):
        param1: str
        param2: int

    @request_handler(params=MockParams)
    def decorated_function(params) -> Response:
        return Response(
            statusCode="200",
            body=params.model_dump_json(exclude_none=True),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(
        headers=create_headers(), query_string_parameters=None
    )
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "400"
    assert result["headers"] == default_response_headers()
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                            "code": "INVALID_PARAMETER",
                            "display": "Invalid parameter",
                        }
                    ]
                },
                "diagnostics": "Invalid query parameter (param1: Field required)",
                "expression": ["param1"],
            },
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                            "code": "INVALID_PARAMETER",
                            "display": "Invalid parameter",
                        }
                    ]
                },
                "diagnostics": "Invalid query parameter (param2: Field required)",
                "expression": ["param2"],
            },
        ],
    }


def test_request_handler_with_body():
    class MockBody(BaseModel):
        param1: str
        param2: int

    @request_handler(body=MockBody)
    def decorated_function(event, context, config, metadata, body) -> Response:
        return Response(
            statusCode="200",
            body=body.model_dump_json(exclude_none=True),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(
        headers=create_headers(), body=json.dumps({"param1": "test", "param2": 123})
    )
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "200"
    assert result["headers"] == {
        "Content-Type": "application/json",
        **default_response_headers(),
    }
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])
    assert parsed_body == {"param1": "test", "param2": 123}


def test_request_handler_with_body_missing_body():
    class MockBody(BaseModel):
        param1: str
        param2: int

    @request_handler(body=MockBody)
    def decorated_function(event, context, config, metadata, body) -> Response:
        return Response(
            statusCode="200",
            body=body.model_dump_json(exclude_none=True),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(headers=create_headers(), body=None)
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "400"
    assert result["headers"] == default_response_headers()
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                            "code": "BAD_REQUEST",
                            "display": "Bad request",
                        }
                    ]
                },
                "diagnostics": "Request body is required",
            }
        ],
    }


def test_request_handler_with_body_invalid_body():
    class MockBody(BaseModel):
        param1: str
        param2: int

    @request_handler(body=MockBody)
    def decorated_function(event, context, config, metadata, body) -> Response:
        return Response(
            statusCode="200",
            body=body.model_dump_json(exclude_none=True),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=json.dumps({"param1": {"invalid": "value"}, "param2": "invalid"}),
    )
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "400"
    assert result["headers"] == default_response_headers()
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                        }
                    ]
                },
                "diagnostics": "Request body could not be parsed (param1: Input should be a valid string)",
                "expression": ["param1"],
            },
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                        }
                    ],
                },
                "diagnostics": "Request body could not be parsed (param2: Input should be a valid integer, unable to parse string as an integer)",
                "expression": ["param2"],
            },
        ],
    }


def test_request_handler_with_request_verification(mocker: MockerFixture):
    parse_headers_mock = mocker.patch("nrlf.core.decorators.parse_headers")

    @request_handler(skip_request_verification=True)
    def decorated_function(event, context) -> Response:
        return Response(
            statusCode="200",
            body=json.dumps({"message": "Hello, World!"}),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event()
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "200"
    assert result["headers"] == {
        "Content-Type": "application/json",
        **default_response_headers(),
    }
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])
    assert parsed_body == {"message": "Hello, World!"}

    assert parse_headers_mock.called is False


def test_request_handler_with_missing_request_id(mocker: MockerFixture):
    parse_headers_mock = mocker.patch("nrlf.core.decorators.parse_headers")

    @request_handler(skip_request_verification=False)
    def decorated_function(event, context) -> Response:
        return Response(
            statusCode="200",
            body=json.dumps({"message": "Hello, World!"}),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event()
    context = create_mock_context()

    event["headers"].pop(X_REQUEST_ID_HEADER)

    result = decorated_function(event, context)

    assert result["statusCode"] == "400"
    assert result["headers"] == {}
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                            "code": "MISSING_OR_INVALID_HEADER",
                            "display": "There is a required header missing or invalid",
                        }
                    ]
                },
                "diagnostics": "The X-Request-Id header is missing or invalid",
            }
        ],
    }

    assert parse_headers_mock.called is False


def test_request_handler_with_invalid_headers():
    @request_handler()
    def decorated_function(event, context, config, metadata) -> Response:
        return Response(
            statusCode="200",
            body=json.dumps({"message": "Hello, World!"}),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(
        headers={
            **create_headers(),
            "nhsd-connection-metadata": "invalid",
            "nhsd-client-rp-details": "invalid",
        }
    )
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "401"
    assert result["headers"] == default_response_headers()
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                            "code": "MISSING_OR_INVALID_HEADER",
                            "display": "There is a required header missing or invalid",
                        }
                    ]
                },
                "diagnostics": "Unable to parse metadata about the requesting application. Contact the onboarding team.",
            }
        ],
    }


def test_request_load_connection_metadata_with_permission_headers():
    expected_metadata = load_connection_metadata(
        headers=create_headers(nrl_permissions=[PERMISSION_ALLOW_ALL_POINTER_TYPES]),
        config=Config(),
    )

    assert expected_metadata.pointer_types == PointerTypes.list()


def test_request_load_connection_metadata_with_no_permission_lookup_or_file():
    expected_metadata = load_connection_metadata(
        headers=create_headers(nrl_app_id="someId"), config=Config()
    )

    assert expected_metadata.pointer_types == []


missing_headers = [
    ["nhsd-connection-metadata"],
    ["nhsd-connection-metadata", "nhsd-client-rp-details"],
    ["nhsd-client-rp-details"],
]


@pytest.mark.parametrize("headers_missing_from_request", missing_headers)
def test_request_load_connection_with_missing_headers_gets_v2_permissions(
    headers_missing_from_request,
):
    headers = create_headers(
        additional_headers={
            V2Headers.NHSD_END_USER_ORGANISATION_ODS: "Y05868",
            V2Headers.NHSD_NRL_APP_ID: "Y05868-TestApp-12345678",
        }
    )
    for header_name in headers_missing_from_request:
        headers.pop(header_name)

    expected_metadata = load_connection_metadata(
        headers=headers, config=Config(), path="/producer/DocumentReference"
    )

    assert expected_metadata.pointer_types == []
    assert expected_metadata.ods_code == "Y05868"
    assert expected_metadata.nrl_app_id == "Y05868-TestApp-12345678"


def _create_v2_headers() -> dict:
    """Create headers that trigger the v2 permissions model (missing nhsd-client-rp-details)."""
    headers = create_headers(
        additional_headers={
            V2Headers.NHSD_END_USER_ORGANISATION_ODS: "Y05868",
            V2Headers.NHSD_NRL_APP_ID: "Y05868-TestApp-12345678",
        }
    )
    headers.pop("nhsd-client-rp-details")
    return headers


def test_load_v2_connection_metadata_allow_all_types(mocker: MockerFixture):
    mocker.patch(
        "nrlf.core.decorators.get_pointer_permissions_v2",
        return_value={
            "access_controls": [AccessControls.ALLOW_ALL_TYPES.value],
            "types": [],
        },
    )

    metadata = load_connection_metadata(
        headers=_create_v2_headers(),
        config=Config(),
        path="/producer/DocumentReference",
    )

    assert metadata.nrl_permissions_policy.types == PointerTypes.list()


def test_load_v2_connection_metadata_specific_types(mocker: MockerFixture):
    specific_types = [
        "http://snomed.info/sct|736253002",
        "http://snomed.info/sct|735324008",
    ]
    mocker.patch(
        "nrlf.core.decorators.get_pointer_permissions_v2",
        return_value={
            "access_controls": [],
            "types": specific_types,
        },
    )

    metadata = load_connection_metadata(
        headers=_create_v2_headers(),
        config=Config(),
        path="/producer/DocumentReference",
    )

    assert metadata.nrl_permissions_policy.types == specific_types


def test_load_v2_connection_metadata_missing_access_controls(mocker: MockerFixture):
    specific_types = ["http://snomed.info/sct|736253002"]
    mocker.patch(
        "nrlf.core.decorators.get_pointer_permissions_v2",
        return_value={
            "types": specific_types,
        },
    )

    metadata = load_connection_metadata(
        headers=_create_v2_headers(),
        config=Config(),
        path="/producer/DocumentReference",
    )

    assert metadata.nrl_permissions_policy.types == specific_types


def test_request_handler_with_custom_repository(mocker: MockerFixture):
    repository_mock = mocker.Mock()

    @request_handler(repository=repository_mock)
    def decorated_function(event, context, config, metadata, repository) -> Response:
        return Response(
            statusCode="200",
            body=json.dumps({"message": "Hello, World!"}),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(headers=create_headers())
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "200"
    assert result["headers"] == {
        "Content-Type": "application/json",
        **default_response_headers(),
    }
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])
    assert parsed_body == {"message": "Hello, World!"}

    repository_mock.assert_called_once()
    assert repository_mock.call_args.kwargs == {
        "table_name": "unit-test-document-pointer",
    }


def test_request_handler_interaction_allowed_when_function_in_v2_interactions(
    mocker: MockerFixture,
):
    mocker.patch(
        "nrlf.core.decorators.get_pointer_permissions_v2",
        return_value={
            "types": ["http://snomed.info/sct|736253002"],
            "interactions": ["test_function"],
        },
    )

    @request_handler()
    def decorated_function() -> Response:
        return Response(
            statusCode="200",
            body=json.dumps({"message": "Hello, World!"}),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(headers=_create_v2_headers())
    context = create_mock_context(function_name="test_function")

    result = decorated_function(event, context)

    assert result["statusCode"] == "200"


def test_request_handler_interaction_forbidden_when_function_not_in_v2_interactions(
    mocker: MockerFixture,
):
    mocker.patch(
        "nrlf.core.decorators.get_pointer_permissions_v2",
        return_value={
            "types": ["http://snomed.info/sct|736253002"],
            "interactions": ["someOtherFunction"],
        },
    )

    @request_handler()
    def decorated_function() -> Response:
        return Response(
            statusCode="200",
            body=json.dumps({"message": "Hello, World!"}),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(headers=_create_v2_headers())
    context = create_mock_context(function_name="theOgFunction")
    mock_logger = mocker.patch("nrlf.core.decorators.logger")

    result = decorated_function(event, context)

    assert result["statusCode"] == "403"
    parsed_body = json.loads(result["body"])
    assert parsed_body["issue"][0]["code"] == "forbidden"
    assert (
        "'Y05868' does not have permission to access this resource"
        in parsed_body["issue"][0]["diagnostics"]
    )
    assert any(
        args and args[0] == LogReference.HANDLER005a
        for args, _ in mock_logger.log.call_args_list
    )


def test_request_handler_interaction_forbidden_when_v2_interactions_empty(
    mocker: MockerFixture,
):
    mocker.patch(
        "nrlf.core.decorators.get_pointer_permissions_v2",
        return_value={
            "types": ["http://snomed.info/sct|736253002"],
            "interactions": [],
        },
    )

    @request_handler()
    def decorated_function() -> Response:
        return Response(
            statusCode="200",
            body=json.dumps({"message": "Hello, World!"}),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(headers=_create_v2_headers())
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "403"
    parsed_body = json.loads(result["body"])
    assert parsed_body["issue"][0]["code"] == "forbidden"


def test_deprecated_decorator():
    @deprecated("This function is deprecated.")
    def deprecated_function():
        """This function is deprecated."""

    with warnings.catch_warnings(record=True) as warning_list:
        deprecated_function()

        assert len(warning_list) == 1
        assert issubclass(warning_list[0].category, DeprecationWarning)
        assert (
            str(warning_list[0].message)
            == "Call to deprecated function deprecated_function. This function is deprecated."
        )
