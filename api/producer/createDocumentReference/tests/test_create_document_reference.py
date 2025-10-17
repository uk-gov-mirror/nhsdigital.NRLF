import json
from unittest.mock import Mock, patch

from freeze_uuid import freeze_uuid
from freezegun import freeze_time
from moto import mock_aws
from pytest import mark

from api.producer.createDocumentReference.create_document_reference import (
    _set_create_time_fields,
    handler,
)
from nrlf.core.constants import SNOMED_SYSTEM_URL
from nrlf.core.dynamodb.repository import DocumentPointer, DocumentPointerRepository
from nrlf.producer.fhir.r4.model import (
    DocumentReferenceRelatesTo,
    Identifier,
    Reference,
)
from nrlf.tests.data import load_document_reference, load_document_reference_data
from nrlf.tests.dynamodb import mock_repository
from nrlf.tests.events import (
    create_headers,
    create_mock_context,
    create_test_api_gateway_event,
    default_response_headers,
)


@mock_aws
@mock_repository
@freeze_time("2024-03-21T12:34:56.789")
@freeze_uuid("00000000-0000-0000-0000-000000000001")
def test_create_document_reference_happy_path(repository: DocumentPointerRepository):
    doc_ref_data = load_document_reference_data("Y05868-736253002-Valid")

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref_data,
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {
            "Location": "/DocumentReference/Y05868-00000000-0000-0000-0000-000000000001",
            **default_response_headers(),
        },
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "information",
                "code": "informational",
                "details": {
                    "coding": [
                        {
                            "code": "RESOURCE_CREATED",
                            "display": "Resource created",
                            "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                        }
                    ],
                },
                "diagnostics": "The document has been created",
            }
        ],
    }

    created_doc_pointer = repository.get_by_id(
        "Y05868-00000000-0000-0000-0000-000000000001"
    )

    assert created_doc_pointer is not None
    assert created_doc_pointer.created_on == "2024-03-21T12:34:56.789Z"
    assert created_doc_pointer.updated_on is None
    assert json.loads(created_doc_pointer.document) == {
        **json.loads(doc_ref_data),
        "meta": {
            "lastUpdated": "2024-03-21T12:34:56.789Z",
        },
        "date": "2024-03-21T12:34:56.789Z",
        "id": "Y05868-00000000-0000-0000-0000-000000000001",
    }


@mock_aws
@mock_repository
@freeze_time("2024-03-21T12:34:56.789")
@freeze_uuid("00000000-0000-0000-0000-000000000001")
def test_create_document_reference_happy_path_with_ssp(
    repository: DocumentPointerRepository,
):
    doc_ref_data = load_document_reference_data(
        "Y05868-736253002-Valid-with-ssp-content"
    )

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref_data,
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {
            "Location": "/DocumentReference/Y05868-00000000-0000-0000-0000-000000000001",
            **default_response_headers(),
        },
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "information",
                "code": "informational",
                "details": {
                    "coding": [
                        {
                            "code": "RESOURCE_CREATED",
                            "display": "Resource created",
                            "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                        }
                    ],
                },
                "diagnostics": "The document has been created",
            }
        ],
    }

    created_doc_pointer = repository.get_by_id(
        "Y05868-00000000-0000-0000-0000-000000000001"
    )

    assert created_doc_pointer is not None
    assert created_doc_pointer.created_on == "2024-03-21T12:34:56.789Z"
    assert created_doc_pointer.updated_on is None
    assert json.loads(created_doc_pointer.document) == {
        **json.loads(doc_ref_data),
        "meta": {
            "lastUpdated": "2024-03-21T12:34:56.789Z",
        },
        "date": "2024-03-21T12:34:56.789Z",
        "id": "Y05868-00000000-0000-0000-0000-000000000001",
    }


@mock_aws
@mock_repository
@freeze_time("2024-03-21T12:34:56.789")
@freeze_uuid("00000000-0000-0000-0000-000000000001")
def test_create_document_reference_without_related_value_exception(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid-with-ssp-content")
    doc_ref.context = {
        "practiceSetting": {
            "coding": [
                {
                    "system": SNOMED_SYSTEM_URL,
                    "code": "788002001",
                    "display": "Adult mental health service",
                }
            ]
        },
        "sourcePatientInfo": {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/nhs-number",
                "value": "6700028191",
            }
        },
        "related": [{"identifier": {"system": "https://fhir.nhs.uk/Id/nhsSpineASID"}}],
    }

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "422",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "business-rule",
                "details": {
                    "coding": [
                        {
                            "code": "UNPROCESSABLE_ENTITY",
                            "display": "Unprocessable Entity",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "Invalid ASID value ''. A single ASID consisting of 12 digits can be provided in the context.related field.",
                "expression": ["context.related[0].identifier.value"],
            }
        ],
    }


def test_create_document_reference_no_body():
    event = create_test_api_gateway_event(
        headers=create_headers(),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "code": "BAD_REQUEST",
                            "display": "Bad request",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ],
                },
                "diagnostics": "Request body is required",
            }
        ],
    }


def test_create_document_reference_invalid_body():
    event = create_test_api_gateway_event(
        headers=create_headers(),
        body="{}",
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ],
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
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ],
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
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ],
                },
                "diagnostics": "Request body could not be parsed (type: Field required)",
                "expression": ["type"],
            },
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ],
                },
                "diagnostics": "Request body could not be parsed (category: Field required)",
                "expression": ["category"],
            },
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ],
                },
                "diagnostics": "Request body could not be parsed (author: Field required)",
                "expression": ["author"],
            },
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ],
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


def test_create_document_reference_empty_fields_in_body():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.author = []
    doc_ref.custodian = {"identifier": {}, "reference": None}
    doc_ref.category = [{"coding": [{"system": "", "code": None}]}]
    doc_ref.text = ""

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )
    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ],
                },
                "diagnostics": "Request body could not be parsed (DocumentReference: Value error, The following fields are empty: text, author, custodian.reference, custodian.identifier, category[0].coding[0].system, category[0].coding[0].code)",
                "expression": ["DocumentReference"],
            }
        ],
    }


def test_create_document_reference_invalid_resource():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.custodian = None

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "422",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "business-rule",
                "details": {
                    "coding": [
                        {
                            "code": "UNPROCESSABLE_ENTITY",
                            "display": "Unprocessable Entity",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ],
                },
                "diagnostics": "The required field 'custodian' is missing",
                "expression": ["custodian"],
            },
        ],
    }


def test_create_document_reference_with_no_custodian():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.custodian = None

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "422",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "business-rule",
                "details": {
                    "coding": [
                        {
                            "code": "UNPROCESSABLE_ENTITY",
                            "display": "Unprocessable Entity",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ],
                },
                "diagnostics": "The required field 'custodian' is missing",
                "expression": ["custodian"],
            },
        ],
    }


def test_create_document_reference_with_no_practiceSetting():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.context.practiceSetting = None

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ],
                },
                "diagnostics": "Request body could not be parsed (context.practiceSetting: Field required)",
                "expression": ["context.practiceSetting"],
            },
        ],
    }


def test_create_document_reference_with_invalid_docStatus():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.docStatus = "invalid"

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ],
                },
                "diagnostics": "Request body could not be parsed (docStatus: Input should be 'entered-in-error', 'amended', 'preliminary' or 'final')",
                "expression": ["docStatus"],
            },
        ],
    }


def test_create_document_reference_invalid_custodian_id():
    doc_ref = load_document_reference("Y05868-736253002-Valid")

    assert doc_ref.custodian and doc_ref.custodian.identifier
    doc_ref.custodian.identifier.value = "X26"

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "422",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "business-rule",
                "details": {
                    "coding": [
                        {
                            "code": "UNPROCESSABLE_ENTITY",
                            "display": "Unprocessable Entity",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "The custodian of the provided DocumentReference does not match the expected ODS code for this organisation",
                "expression": ["custodian.identifier.value"],
            }
        ],
    }


def test_create_document_reference_invalid_pointer_type():
    doc_ref = load_document_reference("Y05868-736253002-Valid")

    assert doc_ref.type and doc_ref.type.coding
    doc_ref.type.coding[0].code = "invalid"

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "422",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "business-rule",
                "details": {
                    "coding": [
                        {
                            "code": "UNPROCESSABLE_ENTITY",
                            "display": "Unprocessable Entity",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "Invalid type code: invalid Type must be a member of the England-NRLRecordType value set (https://fhir.nhs.uk/England/CodeSystem/England-NRLRecordType)",
                "expression": ["type.coding[0].code"],
            }
        ],
    }


@mock_aws
@mock_repository
@patch("nrlf.core.decorators.parse_permissions_file")
def test_create_document_reference_pointer_type_not_allowed(
    parse_permissions_mock, repository: DocumentPointerRepository
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")

    assert doc_ref.type and doc_ref.type.coding

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    parse_permissions_mock.return_value = ["invalid"]
    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "403",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "forbidden",
                "details": {
                    "coding": [
                        {
                            "code": "AUTHOR_CREDENTIALS_ERROR",
                            "display": "Author credentials error",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "The type of the provided DocumentReference is not in the list of allowed types for this organisation",
                "expression": ["type.coding[0].code"],
            }
        ],
    }


def test_create_document_reference_invalid_category_type():
    doc_ref = load_document_reference("Y05868-736253002-Valid")

    assert doc_ref.category and doc_ref.category[0].coding
    doc_ref.category[0].coding[0].code = "1102421000000108"
    doc_ref.category[0].coding[0].display = "Observations"

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "422",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "business-rule",
                "details": {
                    "coding": [
                        {
                            "code": "UNPROCESSABLE_ENTITY",
                            "display": "Unprocessable Entity",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "The Category code of the provided document 'http://snomed.info/sct|1102421000000108' must match the allowed category for pointer type 'http://snomed.info/sct|736253002' with a category value of 'http://snomed.info/sct|734163000'",
                "expression": ["category.coding[0].code"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_create_document_reference_cannot_set_status_to_not_current(repository):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    doc_ref.status = "somethingElse"

    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())

    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }
    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "Request body could not be parsed (status: String should match pattern '^current$')",
                "expression": ["status"],
            }
        ],
    }


def test_create_document_reference_no_relatesto_target():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(code="transforms", target=Reference())
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ],
                },
                "diagnostics": "Request body could not be parsed (DocumentReference: Value error, The following fields are empty: relatesTo[0].target)",
                "expression": ["DocumentReference"],
            }
        ],
    }


def test_create_document_reference_invalid_relatesto_target_producer_id():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="transforms",
            target=Reference(identifier=Identifier(value="X26-99999-99999-999999")),
        )
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "422",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "business-rule",
                "details": {
                    "coding": [
                        {
                            "code": "UNPROCESSABLE_ENTITY",
                            "display": "Unprocessable Entity",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "The relatesTo target identifier value does not include the expected ODS code for this organisation",
                "expression": ["relatesTo[0].target.identifier.value"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_create_document_reference_invalid_relatesto_not_exists(repository):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="transforms",
            target=Reference(
                identifier=Identifier(value="Y05868-123456-123456-123456"),
            ),
        )
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "422",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "business-rule",
                "details": {
                    "coding": [
                        {
                            "code": "UNPROCESSABLE_ENTITY",
                            "display": "Unprocessable Entity",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "The relatesTo target document does not exist",
                "expression": ["relatesTo[0].target.identifier.value"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_create_document_reference_invalid_relatesto_nhs_number(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    # Change document ID and NHS number
    doc_ref.id = "Y05868-99999-99999-123456"

    assert doc_ref.subject and doc_ref.subject.identifier
    doc_ref.subject.identifier.value = "9999999999"
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="transforms",
            target=Reference(identifier=Identifier(value="Y05868-99999-99999-999999")),
        )
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "422",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "business-rule",
                "details": {
                    "coding": [
                        {
                            "code": "UNPROCESSABLE_ENTITY",
                            "display": "Unprocessable Entity",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "The relatesTo target document NHS number does not match the NHS number in the request",
                "expression": ["relatesTo[0].target.identifier.value"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_create_document_reference_invalid_relatesto_type(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    # Change document ID and NHS number
    doc_ref.id = "Y05868-99999-99999-123456"

    assert doc_ref.type and doc_ref.type.coding
    doc_ref.type.coding[0].code = "861421000000109"
    doc_ref.type.coding[0].display = "End of life care coordination summary"
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="transforms",
            target=Reference(identifier=Identifier(value="Y05868-99999-99999-999999")),
        )
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(
            app_id="123456",
        ),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "422",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "business-rule",
                "details": {
                    "coding": [
                        {
                            "code": "UNPROCESSABLE_ENTITY",
                            "display": "Unprocessable Entity",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "The relatesTo target document type does not match the type in the request",
                "expression": ["relatesTo[0].target.identifier.value"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_create_document_reference_with_no_context_related_for_ssp_url(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid-with-ssp-content")

    del doc_ref.context.related

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "422",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "business-rule",
                "details": {
                    "coding": [
                        {
                            "code": "UNPROCESSABLE_ENTITY",
                            "display": "Unprocessable Entity",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "Missing context.related. It must be provided and contain a single valid ASID identifier when content contains an SSP URL",
                "expression": ["context.related"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_create_document_reference_with_no_asid_in_for_ssp_url(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid-with-ssp-content")

    doc_ref.context.related = [
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/not-an-asid",
                "value": "some-other-value",
            }
        }
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "422",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "business-rule",
                "details": {
                    "coding": [
                        {
                            "code": "UNPROCESSABLE_ENTITY",
                            "display": "Unprocessable Entity",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "Missing ASID identifier. context.related must contain a single valid ASID identifier when content contains an SSP URL",
                "expression": ["context.related"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_create_document_reference_with_invalid_asid_for_ssp_url(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid-with-ssp-content")

    doc_ref.context.related = [
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/nhsSpineASID",
                "value": "not-a-valid-asid",
            }
        }
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "422",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "business-rule",
                "details": {
                    "coding": [
                        {
                            "code": "UNPROCESSABLE_ENTITY",
                            "display": "Unprocessable Entity",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "Invalid ASID value 'not-a-valid-asid'. A single ASID consisting of 12 digits can be provided in the context.related field.",
                "expression": ["context.related[0].identifier.value"],
            }
        ],
    }


@mock_aws
@mock_repository
@freeze_uuid("00000000-0000-0000-0000-000000000001")
def test_create_document_reference_supersede_deletes_old_pointers_replace(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    # Change document ID and NHS number
    doc_ref.id = "Y05868-99999-99999-123456"
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="replaces",
            target=Reference(identifier=Identifier(value="Y05868-99999-99999-999999")),
        )
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {
            "Location": "/DocumentReference/Y05868-00000000-0000-0000-0000-000000000001",
            **default_response_headers(),
        },
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "information",
                "code": "informational",
                "details": {
                    "coding": [
                        {
                            "code": "RESOURCE_SUPERSEDED",
                            "display": "Resource created and resource(s) deleted",
                            "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                        }
                    ]
                },
                "diagnostics": "The document has been superseded by a new version",
            }
        ],
    }

    old_doc_pointer = repository.get_by_id("Y05868-99999-99999-999999")
    assert old_doc_pointer is None


@mock_aws
@mock_repository
@freeze_uuid("00000000-0000-0000-0000-000000000001")
def test_create_document_reference_supersede_succeeds_with_toggle(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")

    # Add reference to a non-existing pointer
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="replaces",
            target=Reference(identifier=Identifier(value="Y05868-99999-99999-000000")),
        )
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(nrl_permissions=["supersede-ignore-delete-fail"]),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {
            "Location": "/DocumentReference/Y05868-00000000-0000-0000-0000-000000000001",
            **default_response_headers(),
        },
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "information",
                "code": "informational",
                "details": {
                    "coding": [
                        {
                            "code": "RESOURCE_SUPERSEDED",
                            "display": "Resource created and resource(s) deleted",
                            "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                        }
                    ]
                },
                "diagnostics": "The document has been superseded by a new version",
            }
        ],
    }

    non_existent_pointer = repository.get_by_id("Y05868-99999-99999-000000")
    assert non_existent_pointer is None


@mock_aws
@mock_repository
def test_create_document_reference_supersede_fails_without_toggle(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")

    # Add reference to a non-existing pointer
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="replaces",
            target=Reference(identifier=Identifier(value="Y05868-99999-99999-000000")),
        )
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "422",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "business-rule",
                "details": {
                    "coding": [
                        {
                            "code": "UNPROCESSABLE_ENTITY",
                            "display": "Unprocessable Entity",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "The relatesTo target document does not exist",
                "expression": ["relatesTo[0].target.identifier.value"],
            }
        ],
    }


@mock_aws
@mock_repository
@freeze_uuid("00000000-0000-0000-0000-000000000001")
def test_create_document_reference_create_relatesto_not_replaces(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    # Change document ID and NHS number
    doc_ref.id = "Y05868-99999-99999-123456"
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="transforms",
            target=Reference(identifier=Identifier(value="Y05868-99999-99999-999999")),
        )
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {
            "Location": "/DocumentReference/Y05868-00000000-0000-0000-0000-000000000001",
            **default_response_headers(),
        },
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "information",
                "code": "informational",
                "details": {
                    "coding": [
                        {
                            "code": "RESOURCE_CREATED",
                            "display": "Resource created",
                            "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                        }
                    ]
                },
                "diagnostics": "The document has been created",
            }
        ],
    }

    old_doc_pointer = repository.get_by_id("Y05868-99999-99999-999999")
    assert old_doc_pointer is not None


@mock_aws
@mock_repository
@freeze_time("2024-03-21T12:34:56.789")
@freeze_uuid("00000000-0000-0000-0000-000000000001")
def test_create_document_reference_with_date_ignored(
    repository: DocumentPointerRepository,
):
    doc_ref_data = load_document_reference_data("Y05868-736253002-Valid-with-date")

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref_data,
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {
            "Location": "/DocumentReference/Y05868-00000000-0000-0000-0000-000000000001",
            **default_response_headers(),
        },
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "information",
                "code": "informational",
                "details": {
                    "coding": [
                        {
                            "code": "RESOURCE_CREATED",
                            "display": "Resource created",
                            "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                        }
                    ],
                },
                "diagnostics": "The document has been created",
            }
        ],
    }

    created_doc_pointer = repository.get_by_id(
        "Y05868-00000000-0000-0000-0000-000000000001"
    )

    assert created_doc_pointer is not None
    assert created_doc_pointer.created_on == "2024-03-21T12:34:56.789Z"
    assert created_doc_pointer.updated_on is None
    assert json.loads(created_doc_pointer.document) == {
        **json.loads(doc_ref_data),
        "meta": {
            "lastUpdated": "2024-03-21T12:34:56.789Z",
        },
        "date": "2024-03-21T12:34:56.789Z",
        "id": "Y05868-00000000-0000-0000-0000-000000000001",
    }


@mock_aws
@mock_repository
@freeze_time("2024-03-21T12:34:56.789")
@freeze_uuid("00000000-0000-0000-0000-000000000001")
def test_create_document_reference_with_date_and_meta_lastupdated_ignored(
    repository: DocumentPointerRepository,
):
    doc_ref_data = load_document_reference_data(
        "Y05868-736253002-Valid-with-date-and-meta-lastupdated"
    )

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref_data,
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {
            "Location": "/DocumentReference/Y05868-00000000-0000-0000-0000-000000000001",
            **default_response_headers(),
        },
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "information",
                "code": "informational",
                "details": {
                    "coding": [
                        {
                            "code": "RESOURCE_CREATED",
                            "display": "Resource created",
                            "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                        }
                    ],
                },
                "diagnostics": "The document has been created",
            }
        ],
    }

    created_doc_pointer = repository.get_by_id(
        "Y05868-00000000-0000-0000-0000-000000000001"
    )

    assert created_doc_pointer is not None
    assert created_doc_pointer.created_on == "2024-03-21T12:34:56.789Z"
    assert created_doc_pointer.updated_on is None
    assert json.loads(created_doc_pointer.document) == {
        **json.loads(doc_ref_data),
        "meta": {
            "lastUpdated": "2024-03-21T12:34:56.789Z",
        },
        "date": "2024-03-21T12:34:56.789Z",
        "id": "Y05868-00000000-0000-0000-0000-000000000001",
    }


@mock_aws
@mock_repository
@freeze_time("2024-03-21T12:34:56.789")
@freeze_uuid("00000000-0000-0000-0000-000000000001")
def test_create_document_reference_with_date_overidden(
    repository: DocumentPointerRepository,
):
    doc_ref_data = load_document_reference_data("Y05868-736253002-Valid-with-date")

    event = create_test_api_gateway_event(
        headers=create_headers(nrl_permissions=["audit-dates-from-payload"]),
        body=doc_ref_data,
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {
            "Location": "/DocumentReference/Y05868-00000000-0000-0000-0000-000000000001",
            **default_response_headers(),
        },
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "information",
                "code": "informational",
                "details": {
                    "coding": [
                        {
                            "code": "RESOURCE_CREATED",
                            "display": "Resource created",
                            "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                        }
                    ],
                },
                "diagnostics": "The document has been created",
            }
        ],
    }

    created_doc_pointer = repository.get_by_id(
        "Y05868-00000000-0000-0000-0000-000000000001"
    )

    assert created_doc_pointer is not None
    assert created_doc_pointer.created_on == "2024-03-21T12:34:56.789Z"
    assert created_doc_pointer.updated_on is None
    assert json.loads(created_doc_pointer.document) == {
        **json.loads(doc_ref_data),
        "meta": {
            "lastUpdated": "2024-03-21T12:34:56.789Z",
        },
        "date": "2024-03-20T00:00:01.000Z",
        "id": "Y05868-00000000-0000-0000-0000-000000000001",
    }


@freeze_time("2024-03-25")
@mark.parametrize(
    "doc_ref_name",
    [
        "Y05868-736253002-Valid",
        "Y05868-736253002-Valid-with-date",
        "Y05868-736253002-Valid-with-date-and-meta-lastupdated",
    ],
)
def test__set_create_time_fields(doc_ref_name: str):
    test_time = "2024-03-24T12:34:56.789Z"
    test_doc_ref = load_document_reference(doc_ref_name)
    test_perms = []

    response = _set_create_time_fields(test_time, test_doc_ref, test_perms)

    assert response.model_dump(exclude_none=True) == {
        **test_doc_ref.model_dump(exclude_none=True),
        "meta": {
            "lastUpdated": "2024-03-24T12:34:56.789Z",
        },
        "date": "2024-03-24T12:34:56.789Z",
    }


@freeze_time("2024-03-25")
@mark.parametrize(
    "doc_ref_name",
    [
        "Y05868-736253002-Valid-with-date",
        "Y05868-736253002-Valid-with-date-and-meta-lastupdated",
    ],
)
def test__set_create_time_fields_when_doc_has_date_and_perms(doc_ref_name: str):
    test_time = "2024-03-24T12:34:56.789Z"
    test_doc_ref = load_document_reference(doc_ref_name)
    test_perms = ["audit-dates-from-payload"]

    response = _set_create_time_fields(test_time, test_doc_ref, test_perms)

    assert response.model_dump(exclude_none=True) == {
        **test_doc_ref.model_dump(exclude_none=True),
        "meta": {
            "lastUpdated": test_time,
        },
        "date": test_doc_ref.date,
    }


@freeze_time("2024-03-25")
def test__set_create_time_fields_when_no_date_but_perms():
    test_time = "2024-03-24T12:34:56.789Z"
    test_doc_ref = load_document_reference("Y05868-736253002-Valid")
    test_perms = ["audit-dates-from-payload"]

    response = _set_create_time_fields(test_time, test_doc_ref, test_perms)

    assert response.model_dump(exclude_none=True) == {
        **test_doc_ref.model_dump(exclude_none=True),
        "meta": {
            "lastUpdated": test_time,
        },
        "date": test_time,
    }


@mock_aws
@mock_repository
@freeze_uuid("00000000-0000-0000-0000-000000000001")
@patch("api.producer.createDocumentReference.create_document_reference.logger")
def test_create_logs_for_unexpected_multi_pointer(
    mock_logger: Mock,
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid-with-master-id")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {
            "Location": "/producer/FHIR/R4/DocumentReference/Y05868-00000000-0000-0000-0000-000000000001",
            **default_response_headers(),
        },
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "information",
                "code": "informational",
                "details": {
                    "coding": [
                        {
                            "code": "RESOURCE_CREATED",
                            "display": "Resource created",
                            "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                        }
                    ]
                },
                "diagnostics": "The document has been created",
            }
        ],
    }

    assert any(
        call[0][0].name == "PROCREATE012" for call in mock_logger.log.call_args_list
    )

    assert {
        "existing_pointers_count": 1,
        "nhs_number": (
            doc_ref.subject.identifier.value
            if doc_ref.subject and doc_ref.subject.identifier
            else None
        ),
        "pointer_type": (
            f"{doc_ref.type.coding[0].system}|{doc_ref.type.coding[0].code}"
            if doc_ref.type and doc_ref.type.coding
            else None
        ),
        "custodian": (
            doc_ref.custodian.identifier.value
            if doc_ref.custodian and doc_ref.custodian.identifier
            else None
        ),
        "new_pointer_master_id": (
            doc_ref.masterIdentifier.value if doc_ref.masterIdentifier else None
        ),
    } == [
        call[1:][0]
        for call in mock_logger.log.call_args_list
        if call[0][0].name == "PROCREATE012"
    ][
        0
    ]


@mock_aws
@mock_repository
@freeze_uuid("00000000-0000-0000-0000-000000000001")
@patch("api.producer.createDocumentReference.create_document_reference.logger")
def test_create_logs_for_expected_multi_pointer(
    mock_logger: Mock,
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-Appointment-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {
            "Location": "/producer/FHIR/R4/DocumentReference/Y05868-00000000-0000-0000-0000-000000000001",
            **default_response_headers(),
        },
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "information",
                "code": "informational",
                "details": {
                    "coding": [
                        {
                            "code": "RESOURCE_CREATED",
                            "display": "Resource created",
                            "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                        }
                    ]
                },
                "diagnostics": "The document has been created",
            }
        ],
    }

    assert not any(
        call[0][0].name == "PROCREATE012" for call in mock_logger.log.call_args_list
    )
