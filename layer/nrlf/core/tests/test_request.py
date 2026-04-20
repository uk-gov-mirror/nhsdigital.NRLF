import json

import pytest

from nrlf.core.errors import OperationOutcomeError, ParseError
from nrlf.core.logger import LogReference, logger
from nrlf.core.request import _fetch_v2_ods_app_id_headers, parse_body, parse_headers
from nrlf.producer.fhir.r4.model import DocumentReference
from nrlf.tests.data import load_document_reference_data

test_cases = [
    (
        {
            "NHSD-end-USER-organISAtion-oDs": "ODS123",
            "x-proxygen-app-nrl-app-id": "This-is-an-app-id",
        },
        "ODS123",
        "This-is-an-app-id",
        None,
    ),
    (
        {
            "NHSD-end-USER-organISAtion-oDs": "ODS123",
        },
        "ODS123",
        None,
        {
            "code": LogReference.HANDLER003b,
            "headers_names": ["nhsd-end-user-organisation-ods"],
        },
    ),
    (
        {
            "x-pROXyGen-aPp-nRl-ApP-Id": "This-is-an-app-id",
        },
        None,
        "This-is-an-app-id",
        {
            "code": LogReference.HANDLER003a,
            "headers_names": ["x-proxygen-app-nrl-app-id"],
        },
    ),
    (
        {},
        None,
        None,
        {
            "code": LogReference.HANDLER003b,
            "headers_names": [],
        },
    ),
]


@pytest.mark.parametrize(
    "headers,expected_ods,expected_app_id,expected_log", test_cases
)
def test_fetch_ods_app_id_headers(
    headers, expected_ods, expected_app_id, expected_log, mocker
):
    spy = mocker.spy(logger, "log")
    ods_code, nrl_app_id = _fetch_v2_ods_app_id_headers(headers)

    assert ods_code == expected_ods
    assert nrl_app_id == expected_app_id

    if expected_log:
        spy.assert_called_with(**expected_log)


def test_parse_headers_empty_headers():
    headers = {}

    with pytest.raises(OperationOutcomeError) as error:
        parse_headers(headers)

    exc = error.value

    assert exc.status_code == "401"
    assert exc.operation_outcome.model_dump(exclude_none=True) == {
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


def test_parse_headers_valid_headers():
    headers = {
        "nhsd-connection-metadata": json.dumps(
            {
                "nrl.pointer-types": ["pointer_type"],
                "nrl.ods-code": "X26",
                "nrl.permissions": ["permission1", "permission2"],
                "nrl.app-id": "X26-TestApp-12345",
            }
        ),
        "nhsd-client-rp-details": json.dumps(
            {
                "developer.app.name": "TestApp",
                "developer.app.id": "12345",
            }
        ),
    }

    metadata = parse_headers(headers)

    assert metadata.pointer_types == ["pointer_type"]
    assert metadata.ods_code == "X26"
    assert metadata.nrl_app_id == "X26-TestApp-12345"
    assert metadata.nrl_permissions == ["permission1", "permission2"]
    assert metadata.client_rp_details.developer_app_name == "TestApp"
    assert metadata.client_rp_details.developer_app_id == "12345"


def test_parse_headers_invalid_headers():
    headers = {
        "nhsd-connection-metadata": "invalid",
        "nhsd-client-rp-details": "invalid",
    }

    with pytest.raises(OperationOutcomeError) as error:
        parse_headers(headers)

    exc = error.value

    assert exc.status_code == "401"
    assert exc.operation_outcome.model_dump(exclude_none=True) == {
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
                    ],
                },
                "diagnostics": "Unable to parse metadata about the requesting application. Contact the onboarding team.",
            }
        ],
    }


def test_parse_headers_case_insensitive():
    headers = {
        "NHSD-Connection-Metadata": json.dumps(
            {
                "nrl.pointer-types": ["pointer_type"],
                "nrl.ods-code": "X26",
                "nrl.permissions": ["permission1", "permission2"],
                "nrl.app-id": "X26-App-12345",
            }
        ),
        "NHSD-Client-RP-Details": json.dumps(
            {
                "developer.app.name": "TestApp",
                "developer.app.id": "12345",
            }
        ),
    }

    metadata = parse_headers(headers)

    assert metadata.pointer_types == ["pointer_type"]
    assert metadata.ods_code == "X26"
    assert metadata.nrl_app_id == "X26-App-12345"
    assert metadata.nrl_permissions == ["permission1", "permission2"]
    assert metadata.client_rp_details.developer_app_name == "TestApp"
    assert metadata.client_rp_details.developer_app_id == "12345"


def test_parse_headers_valid_headers_v2_permissions():
    headers = {
        "nhsd-connection-metadata": json.dumps(
            {
                "nrl.pointer-types": ["pointer_type"],
                "nrl.ods-code": "overwrite me",
                "nrl.permissions": ["permission1", "permission2"],
                "nrl.app-id": "overwrite me",
            }
        ),
        "nhsd-client-rp-details": json.dumps(
            {
                "developer.app.name": "TestApp",
                "developer.app.id": "12345",
            }
        ),
        "nhsd-end-user-organisation-ods": "X26",
        "x-proxygen-app-nrl-app-id": "X26-TestApp-12345",
    }

    metadata = parse_headers(headers)

    assert metadata.pointer_types == ["pointer_type"]
    assert metadata.ods_code == "X26"
    assert metadata.nrl_app_id == "X26-TestApp-12345"
    assert metadata.nrl_permissions == ["permission1", "permission2"]
    assert metadata.client_rp_details.developer_app_name == "X26-TestApp-12345"
    assert metadata.client_rp_details.developer_app_id == "X26-TestApp-12345"


def test_parse_body_no_model_no_body():
    body = None
    model = None

    result = parse_body(model, body)

    assert result is None


def test_parse_body_valid_docref():
    model = DocumentReference
    docref_body = load_document_reference_data("Y05868-736253002-Valid")

    result = parse_body(model, docref_body)

    assert isinstance(result, DocumentReference)


# another test similar to test_parse_body_valid_docref but with a duplicate key
def test_parse_body_valid_docref_with_duplicate_key():
    model = DocumentReference
    docref_body = load_document_reference_data("Y05868-736253002-Valid")

    str_to_duplicate = '"docStatus": "final",'
    docref_body = docref_body.replace(str_to_duplicate, str_to_duplicate * 2)

    with pytest.raises(OperationOutcomeError) as error:
        parse_body(model, docref_body)

    response = error.value.response

    assert response.statusCode == "400"
    assert json.loads(response.body) == {
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
                "diagnostics": "Duplicate keys found in FHIR document: ['docStatus']",
                "expression": ["DocumentReference.docStatus"],
            }
        ],
    }


def test_parse_body_no_body():
    model = DocumentReference
    body = None

    with pytest.raises(OperationOutcomeError) as error:
        parse_body(model, body)

    exc = error.value

    assert exc.status_code == "400"
    assert exc.operation_outcome.model_dump(exclude_none=True) == {
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
                    ],
                },
                "diagnostics": "Request body is required",
            }
        ],
    }


def test_parse_body_invalid_docref_json():
    model = DocumentReference
    docref_body = load_document_reference_data("Y05868-736253002-Valid")

    docref_body = docref_body.replace('unstructured"', "unstructured")

    with pytest.raises(ParseError) as error:
        parse_body(model, docref_body)

    response = error.value.response.model_dump()

    assert response["statusCode"] == "400"
    assert json.loads(response["body"]) == {
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
                    ],
                },
                "diagnostics": "Request body could not be parsed (DocumentReference: Invalid JSON: control character (\\u0000-\\u001F) found while parsing a string at line 72 column 0)",
                "expression": ["DocumentReference"],
            }
        ],
    }


def test_parse_body_invalid_json():
    model = DocumentReference
    body = '{ "type": "is-not-a-docref" }'

    with pytest.raises(ParseError) as error:
        parse_body(model, body)

    response = error.value.response.model_dump()

    assert response["statusCode"] == "400"
    assert json.loads(response["body"]) == {
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
                "diagnostics": "Request body could not be parsed (resourceType: Field required)",
                "expression": ["resourceType"],
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
                    ]
                },
                "diagnostics": "Request body could not be parsed (status: Field required)",
                "expression": ["status"],
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
                    ]
                },
                "diagnostics": "Request body could not be parsed (type: Input should be an object)",
                "expression": ["type"],
            },
            {
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        },
                    ],
                },
                "diagnostics": "Request body could not be parsed (category: Field required)",
                "expression": [
                    "category",
                ],
                "severity": "error",
            },
            {
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        },
                    ],
                },
                "diagnostics": "Request body could not be parsed (author: Field required)",
                "expression": [
                    "author",
                ],
                "severity": "error",
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
                    ]
                },
                "diagnostics": "Request body could not be parsed (content: Field required)",
                "expression": ["content"],
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
                    ]
                },
                "diagnostics": "Request body could not be parsed (context: Field required)",
                "expression": ["context"],
            },
        ],
    }


def test_parse_body_not_json():
    model = DocumentReference
    body = "is not json"

    with pytest.raises(ParseError) as error:
        parse_body(model, body)

    response = error.value.response

    assert response.statusCode == "400"
    assert json.loads(response.body) == {
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
                "diagnostics": "Request body could not be parsed (DocumentReference: Invalid JSON: expected value at line 1 column 1)",
                "expression": ["DocumentReference"],
            }
        ],
    }
