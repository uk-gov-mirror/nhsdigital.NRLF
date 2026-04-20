import json
from unittest.mock import patch

from moto import mock_aws

from api.consumer.searchDocumentReference.search_document_reference import handler
from nrlf.consumer.fhir.r4.model import CodeableConcept, Identifier
from nrlf.core.constants import (
    CATEGORY_ATTRIBUTES,
    CLIENT_RP_DETAILS,
    TYPE_ATTRIBUTES,
    Categories,
    PointerTypes,
    V2Headers,
)
from nrlf.core.dynamodb.repository import DocumentPointer, DocumentPointerRepository
from nrlf.tests.data import load_document_reference
from nrlf.tests.dynamodb import mock_repository
from nrlf.tests.events import (
    create_headers,
    create_mock_context,
    create_test_api_gateway_event,
    default_response_headers,
)


@mock_aws
@mock_repository
def test_search_document_reference_happy_path(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
        },
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "200",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    assert parsed_body == {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [
            {
                "relation": "self",
                "url": "https://pytest.api.service.nhs.uk/record-locator/consumer/FHIR/R4/DocumentReference?subject:identifier=https://fhir.nhs.uk/Id/nhs-number|6700028191",
            }
        ],
        "total": 1,
        "entry": [{"resource": doc_ref.model_dump(exclude_none=True)}],
    }


@mock_aws
@mock_repository
@patch("nrlf.core.decorators.get_pointer_permissions_v2")
def test_search_document_reference_happy_path_v2(
    get_pointer_permissions_mock, repository: DocumentPointerRepository
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    v2_headers = create_headers(
        additional_headers={
            V2Headers.NHSD_END_USER_ORGANISATION_ODS: "Y05868",
            V2Headers.X_PROXYGEN_APP_NRL_APP_ID: "Y05868-TestApp-12345678",
        }
    )
    v2_headers.pop(CLIENT_RP_DETAILS)

    get_pointer_permissions_mock.return_value = {
        "access_controls": [],
        "types": ["http://snomed.info/sct|736253002"],
    }

    event = create_test_api_gateway_event(
        headers=v2_headers,
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
        },
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "200",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [
            {
                "relation": "self",
                "url": "https://pytest.api.service.nhs.uk/record-locator/consumer/FHIR/R4/DocumentReference?subject:identifier=https://fhir.nhs.uk/Id/nhs-number|6700028191",
            }
        ],
        "total": 1,
        "entry": [{"resource": doc_ref.model_dump(exclude_none=True)}],
    }


@mock_aws
@mock_repository
def test_search_document_reference_accession_number_in_pointer(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.identifier = [
        Identifier(
            type=CodeableConcept(text="Accession-Number"), value="Y05868.123456789"
        )
    ]
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
        },
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "200",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": 1,
        "link": [
            {
                "relation": "self",
                "url": "https://pytest.api.service.nhs.uk/record-locator/consumer/FHIR/R4/DocumentReference?subject:identifier=https://fhir.nhs.uk/Id/nhs-number|6700028191",
            }
        ],
        "entry": [{"resource": doc_ref.model_dump(exclude_none=True)}],
    }

    created_doc_pointer = repository.get_by_id("Y05868-99999-99999-999999")

    assert created_doc_pointer is not None
    assert json.loads(created_doc_pointer.document)["identifier"] == [
        {"type": {"text": "Accession-Number"}, "value": "Y05868.123456789"}
    ]


@mock_aws
@mock_repository
def test_search_document_reference_happy_path_with_custodian(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
            "custodian:identifier": "https://fhir.nhs.uk/Id/ods-organization-code|Y05868",
        },
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "200",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [
            {
                "relation": "self",
                "url": "https://pytest.api.service.nhs.uk/record-locator/consumer/FHIR/R4/DocumentReference?subject:identifier=https://fhir.nhs.uk/Id/nhs-number|6700028191&custodian:identifier=https://fhir.nhs.uk/Id/ods-organization-code|Y05868",
            }
        ],
        "total": 1,
        "entry": [{"resource": doc_ref.model_dump(exclude_none=True)}],
    }


@mock_aws
@mock_repository
def test_search_document_reference_happy_path_with_type(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
            "type": "http://snomed.info/sct|736253002",
        },
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "200",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [
            {
                "relation": "self",
                "url": "https://pytest.api.service.nhs.uk/record-locator/consumer/FHIR/R4/DocumentReference?subject:identifier=https://fhir.nhs.uk/Id/nhs-number|6700028191&type=http://snomed.info/sct|736253002",
            }
        ],
        "total": 1,
        "entry": [{"resource": doc_ref.model_dump(exclude_none=True)}],
    }


@mock_aws
@mock_repository
def test_search_document_reference_happy_path_with_category(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    # Second pointer different category
    doc_ref2 = load_document_reference("Y05868-736253002-Valid")
    doc_ref2.id = "Y05868-736253002-Valid2"
    doc_ref2.type.coding[0].code = PointerTypes.NEWS2_CHART.coding_value()
    doc_ref2.type.coding[0].display = TYPE_ATTRIBUTES.get(
        PointerTypes.NEWS2_CHART.value
    ).get("display")
    doc_ref2.category[0].coding[0].code = Categories.OBSERVATIONS.coding_value()
    doc_ref2.category[0].coding[0].display = CATEGORY_ATTRIBUTES.get(
        Categories.OBSERVATIONS.value
    ).get("display")
    repository.create(DocumentPointer.from_document_reference(doc_ref2))

    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
            "category": "http://snomed.info/sct|734163000",
        },
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "200",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }
    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [
            {
                "relation": "self",
                "url": "https://pytest.api.service.nhs.uk/record-locator/consumer/FHIR/R4/DocumentReference?subject:identifier=https://fhir.nhs.uk/Id/nhs-number|6700028191&category=http://snomed.info/sct|734163000",
            }
        ],
        "total": 1,
        "entry": [{"resource": doc_ref.model_dump(exclude_none=True)}],
    }


@mock_aws
@mock_repository
def test_search_document_reference_happy_path_with_category_and_type(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    # Second pointer different category
    doc_ref2 = load_document_reference("Y05868-736253002-Valid")
    doc_ref2.id = "Y05868-736253002-Valid2"
    doc_ref2.type.coding[0].code = PointerTypes.NEWS2_CHART.coding_value()
    doc_ref2.type.coding[0].display = TYPE_ATTRIBUTES.get(
        PointerTypes.NEWS2_CHART.value
    ).get("display")
    doc_ref2.category[0].coding[0].code = Categories.OBSERVATIONS.coding_value()
    doc_ref2.category[0].coding[0].display = CATEGORY_ATTRIBUTES.get(
        Categories.OBSERVATIONS.value
    ).get("display")
    repository.create(DocumentPointer.from_document_reference(doc_ref2))

    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
            "category": "http://snomed.info/sct|734163000",
            "type": "http://snomed.info/sct|736253002",
        },
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "200",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }
    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [
            {
                "relation": "self",
                "url": "https://pytest.api.service.nhs.uk/record-locator/consumer/FHIR/R4/DocumentReference?subject:identifier=https://fhir.nhs.uk/Id/nhs-number|6700028191&type=http://snomed.info/sct|736253002&category=http://snomed.info/sct|734163000",
            }
        ],
        "total": 1,
        "entry": [{"resource": doc_ref.model_dump(exclude_none=True)}],
    }


@mock_aws
@mock_repository
def test_search_document_reference_happy_path_with_category_and_type_no_results(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    # Second pointer different category
    doc_ref2 = load_document_reference("Y05868-736253002-Valid")
    doc_ref2.id = "Y05868-736253002-Valid2"
    doc_ref2.type.coding[0].code = PointerTypes.NEWS2_CHART.coding_value()
    doc_ref2.type.coding[0].display = TYPE_ATTRIBUTES.get(
        PointerTypes.NEWS2_CHART.value
    ).get("display")
    doc_ref2.category[0].coding[0].code = Categories.OBSERVATIONS.coding_value()
    doc_ref2.category[0].coding[0].display = CATEGORY_ATTRIBUTES.get(
        Categories.OBSERVATIONS.value
    ).get("display")
    repository.create(DocumentPointer.from_document_reference(doc_ref2))

    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
            "category": "http://snomed.info/sct|1102421000000108",
            "type": "http://snomed.info/sct|736253002",
        },
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "200",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }
    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [
            {
                "relation": "self",
                "url": "https://pytest.api.service.nhs.uk/record-locator/consumer/FHIR/R4/DocumentReference?subject:identifier=https://fhir.nhs.uk/Id/nhs-number|6700028191&type=http://snomed.info/sct|736253002&category=http://snomed.info/sct|1102421000000108",
            }
        ],
        "total": 0,
        "entry": [],
    }


@mock_aws
@mock_repository
def test_search_document_reference_happy_path_with_multiple_categories_and_type(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    # Second pointer different category
    doc_ref2 = load_document_reference("Y05868-736253002-Valid")
    doc_ref2.id = "Y05868-736253002-Valid2"
    doc_ref2.type.coding[0].code = PointerTypes.NEWS2_CHART.coding_value()
    doc_ref2.type.coding[0].display = TYPE_ATTRIBUTES.get(
        PointerTypes.NEWS2_CHART.value
    ).get("display")
    doc_ref2.category[0].coding[0].code = Categories.OBSERVATIONS.coding_value()
    doc_ref2.category[0].coding[0].display = CATEGORY_ATTRIBUTES.get(
        Categories.OBSERVATIONS.value
    ).get("display")
    repository.create(DocumentPointer.from_document_reference(doc_ref2))

    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
            "category": "http://snomed.info/sct|734163000,http://snomed.info/sct|1102421000000108",
            "type": "http://snomed.info/sct|736253002",
        },
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "200",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }
    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [
            {
                "relation": "self",
                "url": "https://pytest.api.service.nhs.uk/record-locator/consumer/FHIR/R4/DocumentReference?subject:identifier=https://fhir.nhs.uk/Id/nhs-number|6700028191&type=http://snomed.info/sct|736253002&category=http://snomed.info/sct|734163000,http://snomed.info/sct|1102421000000108",
            }
        ],
        "total": 1,
        "entry": [{"resource": doc_ref.model_dump(exclude_none=True)}],
    }


@mock_aws
@mock_repository
def test_search_document_reference_happy_path_with_multiple_categories(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    # Second pointer different category
    doc_ref2 = load_document_reference("Y05868-736253002-Valid")
    doc_ref2.id = "Y05868-736253002-Valid2"
    doc_ref2.type.coding[0].code = PointerTypes.NEWS2_CHART.coding_value()
    doc_ref2.type.coding[0].display = TYPE_ATTRIBUTES.get(
        PointerTypes.NEWS2_CHART.value
    ).get("display")
    doc_ref2.category[0].coding[0].code = Categories.OBSERVATIONS.coding_value()
    doc_ref2.category[0].coding[0].display = CATEGORY_ATTRIBUTES.get(
        Categories.OBSERVATIONS.value
    ).get("display")
    repository.create(DocumentPointer.from_document_reference(doc_ref2))

    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
            "category": "http://snomed.info/sct|734163000,http://snomed.info/sct|1102421000000108",
        },
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "200",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [
            {
                "relation": "self",
                "url": "https://pytest.api.service.nhs.uk/record-locator/consumer/FHIR/R4/DocumentReference?subject:identifier=https://fhir.nhs.uk/Id/nhs-number|6700028191&category=http://snomed.info/sct|734163000,http://snomed.info/sct|1102421000000108",
            }
        ],
        "total": 2,
        "entry": [
            {"resource": doc_ref2.model_dump(exclude_none=True)},
            {"resource": doc_ref.model_dump(exclude_none=True)},
        ],
    }


@mock_aws
@mock_repository
def test_search_document_reference_happy_path_with_nicip_type(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.type.coding[0].code = "MAULR"
    doc_ref.type.coding[0].system = "https://nicip.nhs.uk"
    doc_ref.type.coding[0].display = "MRA Upper Limb Rt"
    doc_ref.category[0].coding[0].code = "721981007"
    doc_ref.category[0].coding[0].display = "Diagnostic Studies Report"
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)

    repository.create(doc_pointer)

    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
            "type": "https://nicip.nhs.uk|MAULR",
        },
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "200",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [
            {
                "relation": "self",
                "url": "https://pytest.api.service.nhs.uk/record-locator/consumer/FHIR/R4/DocumentReference?subject:identifier=https://fhir.nhs.uk/Id/nhs-number|6700028191&type=https://nicip.nhs.uk|MAULR",
            }
        ],
        "total": 1,
        "entry": [{"resource": doc_ref.model_dump(exclude_none=True)}],
    }


@mock_aws
@mock_repository
def test_search_document_reference_no_results(
    repository: DocumentPointerRepository,
):
    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
        },
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "200",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [
            {
                "relation": "self",
                "url": "https://pytest.api.service.nhs.uk/record-locator/consumer/FHIR/R4/DocumentReference?subject:identifier=https://fhir.nhs.uk/Id/nhs-number|6700028191",
            }
        ],
        "total": 0,
        "entry": [],
    }


@mock_aws
@mock_repository
def test_search_document_reference_missing_nhs_number(
    repository: DocumentPointerRepository,
):
    event = create_test_api_gateway_event(headers=create_headers())

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
                            "code": "INVALID_PARAMETER",
                            "display": "Invalid parameter",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "Invalid query parameter (subject:identifier: Field required)",
                "expression": ["subject:identifier"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_search_document_reference_invalid_nhs_number(
    repository: DocumentPointerRepository,
):
    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|123"
        },
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
                            "code": "INVALID_NHS_NUMBER",
                            "display": "Invalid NHS number",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "A valid NHS number is required to search for document references",
                "expression": ["subject:identifier"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_search_document_reference_invalid_type(
    repository: DocumentPointerRepository,
):
    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
            "type": "https://fhir.nhs.uk/CodeSystem/Document-Type|invalid",
        },
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
                "code": "code-invalid",
                "details": {
                    "coding": [
                        {
                            "code": "INVALID_CODE_SYSTEM",
                            "display": "Invalid code system",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "Invalid query parameter (The provided type does not match the allowed types for this organisation)",
                "expression": ["type"],
            }
        ],
    }


@mock_aws
@mock_repository
@patch("nrlf.core.decorators.get_pointer_permissions_v2")
def test_search_document_reference_invalid_type_v2(
    get_pointer_permissions_mock, repository: DocumentPointerRepository
):
    v2_headers = create_headers(
        additional_headers={
            V2Headers.NHSD_END_USER_ORGANISATION_ODS: "Y05868",
            V2Headers.X_PROXYGEN_APP_NRL_APP_ID: "Y05868-TestApp-12345678",
        }
    )
    v2_headers.pop(CLIENT_RP_DETAILS)

    get_pointer_permissions_mock.return_value = {
        "access_controls": [],
        "types": ["http://snomed.info/sct|736253002"],
    }

    event = create_test_api_gateway_event(
        headers=v2_headers,
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
            "type": "http://snomed.info/sct|861421000000109",
        },
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
                "code": "code-invalid",
                "details": {
                    "coding": [
                        {
                            "code": "INVALID_CODE_SYSTEM",
                            "display": "Invalid code system",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "Invalid query parameter (The provided type does not match the allowed types for this organisation)",
                "expression": ["type"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_search_document_reference_invalid_category(
    repository: DocumentPointerRepository,
):
    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
            "category": "https://fhir.nhs.uk/CodeSystem/Document-Type|invalid",
        },
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
                "code": "code-invalid",
                "details": {
                    "coding": [
                        {
                            "code": "INVALID_CODE_SYSTEM",
                            "display": "Invalid code system",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "Invalid query parameter (The provided category is not valid)",
                "expression": ["category"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_search_document_reference_filters_by_summary_count(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
            "_summary": "count",
        },
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "200",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": 1,
        "link": [
            {
                "relation": "self",
                "url": "https://pytest.api.service.nhs.uk/record-locator/consumer/FHIR/R4/DocumentReference?subject:identifier=https://fhir.nhs.uk/Id/nhs-number|6700028191&_summary=count",
            }
        ],
    }


@mock_aws
@mock_repository
@patch("api.consumer.searchDocumentReference.search_document_reference.logger")
def test_search_document_reference_invalid_json(
    mock_logger, repository: DocumentPointerRepository
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    doc_pointer_invalid = DocumentPointer.from_document_reference(doc_ref)
    doc_pointer_invalid.id = "Y05868-11111-99999-999992"
    doc_pointer_invalid.document = "invalid json"

    repository.create(doc_pointer_invalid)
    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191"
        },
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "200",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)

    expected_operation_outcome = {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "exception",
                "details": {
                    "coding": [
                        {
                            "code": "INTERNAL_SERVER_ERROR",
                            "display": "Unexpected internal server error",
                            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                        }
                    ]
                },
                "diagnostics": "An error occurred whilst parsing the document reference search results",
            }
        ],
    }

    assert parsed_body == {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [
            {
                "relation": "self",
                "url": "https://pytest.api.service.nhs.uk/record-locator/consumer/FHIR/R4/DocumentReference?subject:identifier=https://fhir.nhs.uk/Id/nhs-number|6700028191",
            }
        ],
        "total": 2,
        "entry": [
            {"resource": doc_ref.model_dump(exclude_none=True)},
            {"resource": expected_operation_outcome},
        ],
    }

    assert any(
        call[0][0].name == "CONSEARCH005" for call in mock_logger.log.call_args_list
    )
