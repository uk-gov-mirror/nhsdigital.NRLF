from unittest.mock import Mock

import pytest

from nrlf.core.constants import (
    CATEGORY_ATTRIBUTES,
    ODS_SYSTEM,
    TYPE_ATTRIBUTES,
    TYPE_CATEGORIES,
    PointerTypes,
)
from nrlf.core.errors import ParseError
from nrlf.core.validators import (
    DocumentReferenceValidator,
    ValidationResult,
    validate_type,
)
from nrlf.producer.fhir.r4.model import (
    DocumentReference,
    OperationOutcomeIssue,
    RequestQueryType,
)
from nrlf.tests.data import load_document_reference_json


def test_validate_type_valid():
    type_ = RequestQueryType(root=PointerTypes.MENTAL_HEALTH_PLAN.value)
    pointer_types = [
        PointerTypes.MENTAL_HEALTH_PLAN.value,
        PointerTypes.EOL_CARE_PLAN.value,
    ]
    assert validate_type(type_, pointer_types) is True


def test_validate_type_invalid_system():
    type_ = RequestQueryType(root="http://snomed.info/invalid|736373009")
    pointer_types = [
        PointerTypes.EOL_CARE_PLAN.value,
        PointerTypes.EOL_CARE_PLAN.value,
    ]
    assert validate_type(type_, pointer_types) is False


def test_validate_type_invalid_code():
    type_ = RequestQueryType(root=PointerTypes.MRA_UPPER_LIMB_ARTERY.value)
    pointer_types = [
        PointerTypes.MENTAL_HEALTH_PLAN.value,
        PointerTypes.EOL_CARE_PLAN.value,
    ]
    assert validate_type(type_, pointer_types) is False


def test_validate_type_empty():
    type_ = None
    pointer_types: list[str] = []
    assert validate_type(type_, pointer_types) is True


def test_validation_result_reset():
    validation_result = ValidationResult(
        resource=DocumentReference.model_construct(id="example_resource"),
        issues=[OperationOutcomeIssue.model_construct()],
    )

    assert validation_result.resource.id == "example_resource"

    validation_result.reset()
    assert validation_result.resource.id is None
    assert validation_result.issues == []


def test_validation_result_add_error():
    validation_result = ValidationResult(
        resource=DocumentReference.model_construct(), issues=[]
    )

    issue_code = "issue_code"
    error_code = "BAD_REQUEST"
    diagnostics = "diagnostics"
    field = "field"

    validation_result.add_error(issue_code, error_code, diagnostics, field)

    assert len(validation_result.issues) == 1
    assert validation_result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "issue_code",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "BAD_REQUEST",
                    "display": "Bad request",
                }
            ],
        },
        "diagnostics": "diagnostics",
        "expression": ["field"],
    }


def test_validation_result_add_error_no_error_code():
    validation_result = ValidationResult(
        resource=DocumentReference.model_construct(), issues=[]
    )

    issue_code = "issue_code"
    diagnostics = "diagnostics"
    field = "field"

    validation_result.add_error(
        issue_code=issue_code, diagnostics=diagnostics, field=field
    )

    assert len(validation_result.issues) == 1
    assert validation_result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "issue_code",
        "diagnostics": "diagnostics",
        "expression": ["field"],
    }


def test_validation_result_is_valid():
    validation_result = ValidationResult(
        resource=DocumentReference.model_construct(), issues=[]
    )

    assert validation_result.is_valid is True

    validation_result.issues = [
        OperationOutcomeIssue.model_construct(severity="information"),
    ]

    assert validation_result.is_valid is True

    validation_result.issues = [
        OperationOutcomeIssue.model_construct(severity="error"),
    ]
    assert validation_result.is_valid is False

    validation_result.issues = [
        OperationOutcomeIssue.model_construct(severity="fatal"),
    ]
    assert validation_result.is_valid is False


def test_document_reference_validator_init():
    validator = DocumentReferenceValidator()
    assert validator.result.resource.id is None
    assert validator.result.issues == []


def test_document_reference_validator_parse_valid():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    result = validator.parse(document_ref_data)

    assert result.id == "Y05868-99999-99999-999999"
    assert result.status == "current"
    assert result.type
    assert result.type.coding
    assert result.type.coding[0].code == "736253002"


def test_document_reference_validator_parse_invalid():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["id"] = {"value": "invalid"}
    document_ref_data["type"] = "invalid"

    with pytest.raises(ParseError) as error:
        validator.parse(document_ref_data)

    exc = error.value

    assert len(exc.issues) == 2
    assert exc.issues[0].model_dump(exclude_none=True) == {
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
        "diagnostics": "Failed to parse DocumentReference resource (id: Input should be a valid string)",
        "expression": ["id"],
    }
    assert exc.issues[1].model_dump(exclude_none=True) == {
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
        "diagnostics": "Failed to parse DocumentReference resource (type: Input should be a valid dictionary or instance of NRLCodeableConcept)",
        "expression": ["type"],
    }


def test_validate_document_reference_valid():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    result = validator.validate(document_ref_data)

    assert result.is_valid is True
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert result.issues == []


def test_validate_document_reference_missing_fields():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    del document_ref_data["id"]
    del document_ref_data["custodian"]
    del document_ref_data["subject"]

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id is None
    assert len(result.issues) == 3
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "The required field 'custodian' is missing",
        "expression": ["custodian"],
    }

    diagnostics = [issue.diagnostics for issue in result.issues]
    assert diagnostics == [
        "The required field 'custodian' is missing",
        "The required field 'id' is missing",
        "The required field 'subject' is missing",
    ]


def test_validate_document_reference_missing_fields_stops_validation():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    validator._validate_no_extra_fields = Mock()
    validator._validate_identifiers = Mock()
    validator._validate_relates_to = Mock()

    del document_ref_data["custodian"]
    result = validator.validate(document_ref_data)

    assert result.is_valid is False

    assert validator._validate_no_extra_fields.call_count == 0
    assert validator._validate_identifiers.call_count == 0
    assert validator._validate_relates_to.call_count == 0


def test_validate_document_reference_extra_fields():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["extra_field"] = "extra_value"

    with pytest.raises(ParseError) as error:
        validator.validate(document_ref_data)

    exc = error.value
    assert len(exc.issues) == 1
    assert exc.issues[0].model_dump(exclude_none=True) == {
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
        "diagnostics": "Failed to parse DocumentReference resource (extra_field: Extra inputs are not permitted)",
        "expression": ["extra_field"],
    }


def test_validate_document_reference_extra_fields_content():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["content"][0]["extra_field"] = "extra_value"

    with pytest.raises(ParseError) as error:
        validator.validate(document_ref_data)

    exc = error.value
    assert len(exc.issues) == 1
    assert exc.issues[0].model_dump(exclude_none=True) == {
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
        "diagnostics": "Failed to parse DocumentReference resource (content[0].extra_field: Extra inputs are not permitted)",
        "expression": ["content[0].extra_field"],
    }


def test_validate_category_too_many_category():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["category"].append(
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "734163000",
                    "display": "Care plan",
                }
            ]
        }
    )

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid category length: 2 Category must only contain a single value",
        "expression": ["category"],
    }


@pytest.mark.parametrize(
    "category_code, category_display",
    [
        (category_str.split("|")[1], display_dict["display"])
        for category_str, display_dict in CATEGORY_ATTRIBUTES.items()
    ],
)
def test_validate_category_coding_display_mismatch(
    category_code: str, category_display: str
):
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["category"][0] = {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": category_code,
                "display": "some random display name",
            }
        ]
    }

    # Find the type string that matches the type code to avoid that error
    category_str = f"http://snomed.info/sct|{category_code}"
    matching_type_str = next(
        (
            type_str
            for type_str in TYPE_CATEGORIES
            if TYPE_CATEGORIES[type_str] == category_str
        ),
        None,
    )
    if matching_type_str:
        type_parts = matching_type_str.split("|")
        type_system = type_parts[0]
        type_code = type_parts[1]
        document_ref_data["type"] = {
            "coding": [
                {
                    "system": type_system,
                    "code": type_code,
                    "display": TYPE_ATTRIBUTES[matching_type_str]["display"],
                }
            ]
        }

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": f"category code '{category_code}' must have a display value of '{category_display}'",
        "expression": ["category[0].coding[0].display"],
    }


def test_validate_category_coding_invalid_code():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["category"][0] = {
        "coding": [
            {"system": "http://snomed.info/sct", "code": "1234", "display": "Care plan"}
        ]
    }

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid category code: 1234 Category must be a member of the England-NRLRecordCategory value set (https://fhir.nhs.uk/England/CodeSystem/England-NRLRecordCategory)",
        "expression": ["category[0].coding[0].code"],
    }


def test_validate_category_coding_invalid_system():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["category"][0] = {
        "coding": [
            {
                "system": "http://snoooooomed/sctfffffg",
                "code": "734163000",
                "display": "Care plan",
            }
        ]
    }

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid category system: http://snoooooomed/sctfffffg Category system must be 'http://snomed.info/sct'",
        "expression": ["category[0].coding[0].system"],
    }


def test_validate_type_coding_invalid_code():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["type"] = {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "1234",
                "display": "Mental health crisis plan",
            }
        ]
    }

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid type code: 1234 Type must be a member of the England-NRLRecordType value set (https://fhir.nhs.uk/England/CodeSystem/England-NRLRecordType)",
        "expression": ["type.coding[0].code"],
    }


def test_validate_type_coding_invalid_system():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["type"] = {
        "coding": [
            {
                "system": "http://snoooooomed/sctfffffg",
                "code": "736253002",
                "display": "Mental health crisis plan",
            }
        ]
    }

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid type system: http://snoooooomed/sctfffffg Type system must be either 'http://snomed.info/sct' or 'https://nicip.nhs.uk'",
        "expression": ["type.coding[0].system"],
    }


@pytest.mark.parametrize(
    "type_str, display",
    [
        (type_str, display_dict["display"])
        for type_str, display_dict in TYPE_ATTRIBUTES.items()
    ],
)
def test_validate_type_coding_display_mismatch(type_str: str, display: str):
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")
    type_parts = type_str.split("|")
    type_system = type_parts[0]
    type_code = type_parts[1]

    document_ref_data["type"] = {
        "coding": [
            {
                "system": type_system,
                "code": type_code,
                "display": "some random display name",
            }
        ]
    }

    # Find the category string that matches the category code to avoid that error
    category_str = TYPE_CATEGORIES[type_str]
    category_parts = category_str.split("|")
    category_system = category_parts[0]
    category_code = category_parts[1]
    document_ref_data["category"][0] = {
        "coding": [
            {
                "system": category_system,
                "code": category_code,
                "display": CATEGORY_ATTRIBUTES[category_str]["display"],
            }
        ]
    }

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": f"type code '{type_code}' must have a display value of '{display}'",
        "expression": ["type.coding[0].display"],
    }


def test_validate_author_too_many_authors():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["author"].append(
        {
            "identifier": {
                "system": ODS_SYSTEM,
                "value": "someODSCode",
            }
        }
    )

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid author length: 2 Author must only contain a single value",
        "expression": ["author"],
    }


def test_validate_author_system_invalid():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["author"][0] = {
        "identifier": {
            "system": "some system",
            "value": "someODSCode",
        }
    }

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": f"Invalid author system: 'some system' Author system must be 'https://fhir.nhs.uk/Id/ods-organization-code'",
        "expression": ["author[0].identifier.system"],
    }


def test_validate_author_value_invalid():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["author"][0] = {
        "identifier": {
            "system": ODS_SYSTEM,
            "value": "!!!!!!12sd",
        }
    }

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": f"Invalid author value: '!!!!!!12sd' Author value must be alphanumeric",
        "expression": ["author[0].identifier.value"],
    }


def test_validate_author_value_too_long():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["author"][0] = {
        "identifier": {
            "system": ODS_SYSTEM,
            "value": "d1111111111111111111111111111111111111111111111",
        }
    }

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": f"Invalid author value: 'd1111111111111111111111111111111111111111111111' Author value must be less than 13 characters",
        "expression": ["author[0].identifier.value"],
    }


def test_validate_identifiers_invalid_systems():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["custodian"]["identifier"]["system"] = "invalid"
    document_ref_data["subject"]["identifier"]["system"] = "invalid"

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 2
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Provided custodian identifier system is not the ODS system (expected: 'https://fhir.nhs.uk/Id/ods-organization-code')",
        "expression": ["custodian.identifier.system"],
    }
    assert result.issues[1].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Provided subject identifier system is not the NHS number system (expected 'https://fhir.nhs.uk/Id/nhs-number')",
        "expression": ["subject.identifier.system"],
    }


def test_validate_relates_to_valid():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["relatesTo"] = [
        {
            "code": "replaces",
            "target": {
                "identifier": {
                    "system": "https://fhir.nhs.uk/Id/nhs-number",
                    "value": "9999999999",
                }
            },
        }
    ]

    result = validator.validate(document_ref_data)

    assert result.is_valid is True


def test_validate_relates_to_invalid_code():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["relatesTo"] = [
        {
            "code": "invalid",
            "target": {
                "identifier": {
                    "system": "https://fhir.nhs.uk/Id/nhs-number",
                    "value": "9999999999",
                }
            },
        }
    ]

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid relatesTo code: invalid",
        "expression": ["relatesTo[0].code"],
    }


def test_validate_ssp_content_with_asid():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json(
        "Y05868-736253002-Valid-with-ssp-content"
    )

    result = validator.validate(document_ref_data)

    assert result.is_valid is True


def test_validate_with_context_related_but_no_asid():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["context"]["related"] = [
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                "value": "Y05868",
            }
        }
    ]

    result = validator.validate(document_ref_data)

    assert result.is_valid is True


def test_validate_ssp_content_without_any_context_related():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json(
        "Y05868-736253002-Valid-with-ssp-content"
    )

    del document_ref_data["context"]["related"]

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Missing context.related. It must be provided and contain a single valid ASID identifier when content contains an SSP URL",
        "expression": ["context.related"],
    }


def test_validate_asid_with_no_ssp_content():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["context"]["related"] = [
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/nhsSpineASID",
                "value": "1234",
            }
        }
    ]

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid ASID value '1234'. A single ASID consisting of 12 digits can be provided in the context.related field.",
        "expression": ["context.related[0].identifier.value"],
    }


def test_validate_ssp_content_without_asid_in_context_related():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json(
        "Y05868-736253002-Valid-with-ssp-content"
    )

    document_ref_data["context"]["related"] = [
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                "value": "Y05868",
            }
        }
    ]

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Missing ASID identifier. context.related must contain a single valid ASID identifier when content contains an SSP URL",
        "expression": ["context.related"],
    }


def test_validate_ssp_content_with_invalid_asid_value():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json(
        "Y05868-736253002-Valid-with-ssp-content"
    )

    document_ref_data["context"]["related"][0]["identifier"][
        "value"
    ] = "TEST_INVALID_ASID"

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid ASID value 'TEST_INVALID_ASID'. A single ASID consisting of 12 digits can be provided in the context.related field.",
        "expression": ["context.related[0].identifier.value"],
    }


def test_validate_ssp_content_with_invalid_asid_value_and_multiple_related():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json(
        "Y05868-736253002-Valid-with-ssp-content"
    )

    document_ref_data["context"]["related"] = [
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                "value": "Y05868",
            }
        }
    ]
    document_ref_data["context"]["related"].append(
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                "value": "Y09999",
            }
        }
    )
    document_ref_data["context"]["related"].append(
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/nhsSpineASID",
                "value": "TEST_INVALID_ASID",
            }
        }
    )

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid ASID value 'TEST_INVALID_ASID'. A single ASID consisting of 12 digits can be provided in the context.related field.",
        "expression": ["context.related[2].identifier.value"],
    }


def test_validate_ssp_content_with_multiple_asids():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json(
        "Y05868-736253002-Valid-with-ssp-content"
    )

    document_ref_data["context"]["related"][0]["identifier"][
        "value"
    ] = "TEST_INVALID_ASID"
    document_ref_data["context"]["related"].append(
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/nhsSpineASID",
                "value": "09876543210",
            }
        }
    )

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Multiple ASID identifiers provided. Only a single valid ASID identifier can be provided in the context.related.",
        "expression": ["context.related"],
    }


def test_validate_content_format_invalid_code_for_unstructured_document():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["content"][0]["format"] = {
        "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLFormatCode",
        "code": "urn:nhs-ic:record-contact",
        "display": "Contact details (HTTP Unsecured)",
    }

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid content format code: urn:nhs-ic:record-contact format code must be 'urn:nhs-ic:unstructured' for Unstructured Document attachments.",
        "expression": ["content[0].format.code"],
    }


def test_validate_content_format_invalid_code_for_structured_document():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["content"][0]["attachment"]["contentType"] = "application/json"

    document_ref_data["content"][0]["format"] = {
        "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLFormatCode",
        "code": "urn:nhs-ic:record-contact",
        "display": "Contact details (HTTP Unsecured)",
    }

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid content format code: urn:nhs-ic:record-contact format code must be 'urn:nhs-ic:structured' for Structured Document attachments.",
        "expression": ["content[0].format.code"],
    }


def test_validate_content_format_invalid_code_for_contact_details():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["content"][0]["attachment"]["contentType"] = "text/html"

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid content format code: urn:nhs-ic:unstructured format code must be 'urn:nhs-ic:record-contact' for Contact details attachments.",
        "expression": ["content[0].format.code"],
    }


def test_validate_practiceSetting_coding_invalid_system():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["context"]["practiceSetting"] = {
        "coding": [
            {
                "system": "http://snoooooomed/sctfffffg",
                "code": "788002001",
                "display": "Adult mental health service",
            }
        ]
    }

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid practice setting system: http://snoooooomed/sctfffffg Practice Setting system must be 'http://snomed.info/sct'",
        "expression": ["context.practiceSetting.coding[0].system"],
    }


def test_validate_practiceSetting_coding_invalid_code():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["context"]["practiceSetting"] = {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "123",
                "display": "Adult mental health service",
            }
        ]
    }

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid practice setting code: 123 Practice Setting coding must be a member of value set https://fhir.nhs.uk/England/ValueSet/England-PracticeSetting",
        "expression": ["context.practiceSetting.coding[0].code"],
    }


def test_validate_practiceSetting_coding_mismatch_code_and_display():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["context"]["practiceSetting"] = {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "788002001",
                "display": "Nephrology service",
            }
        ]
    }

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid practice setting coding: display Nephrology service does not match the expected display for 788002001 Practice Setting coding is bound to value set https://fhir.nhs.uk/England/ValueSet/England-PracticeSetting",
        "expression": ["context.practiceSetting.coding[0]"],
    }


def test_validate_content_extension_invalid_code_and_display_mismatch():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["content"][0]["extension"][0] = {
        "url": "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-ContentStability",
        "valueCodeableConcept": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLContentStability",
                    "code": "static",
                    "display": "Dynamic",
                }
            ]
        },
    }

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid content extension display: Dynamic Extension display must be the same as code either 'Static' or 'Dynamic'",
        "expression": [
            "content[0].extension[0].valueCodeableConcept.coding[0].display"
        ],
    }


def test_validate_content_extension_missing_content_stability():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    # Remove all ContentStability extensions
    document_ref_data["content"][0]["extension"] = [
        {
            "url": "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-RetrievalMechanism",
            "valueCodeableConcept": {
                "coding": [
                    {
                        "system": "https://fhir.nhs.uk/England/CodeSystem/England-RetrievalMechanism",
                        "code": "Direct",
                        "display": "Direct",
                    }
                ]
            },
        }
    ]

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid content extension: Extension must have one content stability extension, see: ('https://fhir.nhs.uk/England/ValueSet/England-NRLContentStability')",
        "expression": ["content[0].extension"],
    }


def test_validate_content_extension_mismatch_between_retrieval_mechanism_display_and_code():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    # Add a retrieval mechanism extension with a valid code but wrong display
    document_ref_data["content"][0]["extension"].append(
        {
            "url": "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-RetrievalMechanism",
            "valueCodeableConcept": {
                "coding": [
                    {
                        "system": "https://fhir.nhs.uk/England/CodeSystem/England-RetrievalMechanism",
                        "code": "Direct",
                        "display": "Spine Secure Proxy",
                    }
                ]
            },
        }
    )

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid content extension display: Spine Secure Proxy Expected display is 'Direct'",
        "expression": [
            "content[0].extension[1].valueCodeableConcept.coding[0].display"
        ],
    }


def test_validate_content_invalid_content_type():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["content"][0]["attachment"]["contentType"] = "invalid/type"

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid contentType: invalid/type. Must be 'application/pdf', 'text/html' or 'application/fhir+json'",
        "expression": ["content[0].attachment.contentType"],
    }


@pytest.mark.parametrize(
    "content_type, format_code, format_display",
    [
        ("text/html", "urn:nhs-ic:record-contact", "Contact details (HTTP Unsecured)"),
        ("application/pdf", "urn:nhs-ic:unstructured", "Unstructured Document"),
        ("application/json+fhir", "urn:nhs-ic:structured", "Structured Document"),
    ],
)
def test_validate_nrl_format_code_valid_match(
    content_type, format_code, format_display
):
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")
    document_ref_data["content"][0]["attachment"]["contentType"] = content_type

    document_ref_data["content"][0]["format"] = {
        "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLFormatCode",
        "code": format_code,
        "display": format_display,
    }

    result = validator.validate(document_ref_data)

    assert result.is_valid is True


@pytest.mark.parametrize(
    "content_type, format_code, format_display, expected_display",
    [
        (
            "application/pdf",
            "urn:nhs-ic:unstructured",
            "Contact details (HTTP Unsecured)",
            "Unstructured Document",
        ),
        (
            "text/html",
            "urn:nhs-ic:record-contact",
            "Unstructured Document",
            "Contact details (HTTP Unsecured)",
        ),
        (
            "application/fhir+json",
            "urn:nhs-ic:structured",
            "Unstructured Document",
            "Structured Document",
        ),
    ],
)
def test_validate_nrl_format_code_display_mismatch(
    content_type, format_code, format_display, expected_display
):
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")
    document_ref_data["content"][0]["attachment"]["contentType"] = content_type

    document_ref_data["content"][0]["format"] = {
        "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLFormatCode",
        "code": format_code,
        "display": format_display,
    }

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": f"Invalid display for format code '{format_code}'. Expected '{expected_display}'",
        "expression": ["content[0].format.display"],
    }


def test_validate_content_multiple_content_stability_extensions():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    # Add a second duplicate contentStability extension
    document_ref_data["content"][0]["extension"].append(
        document_ref_data["content"][0]["extension"][0]
    )

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid content extension: Extension must have one content stability extension, see: ('https://fhir.nhs.uk/England/ValueSet/England-NRLContentStability')",
        "expression": ["content[0].extension"],
    }


def test_validate_content_multiple_content_retrieval_extensions():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    # Add 2 content retrieval extensions
    content_retrieval_extension = {
        "url": "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-RetrievalMechanism",
        "valueCodeableConcept": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/England/CodeSystem/England-RetrievalMechanism",
                    "code": "Direct",
                    "display": "Direct",
                }
            ]
        },
    }
    document_ref_data["content"][0]["extension"].append(content_retrieval_extension)
    document_ref_data["content"][0]["extension"].append(content_retrieval_extension)

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].model_dump(exclude_none=True) == {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                    "code": "UNPROCESSABLE_ENTITY",
                    "display": "Unprocessable Entity",
                }
            ]
        },
        "diagnostics": "Invalid content retrieval extension: Extension must have one content retrieval extension, see: ('https://fhir.nhs.uk/England/ValueSet/England-RetrievalMechanism')",
        "expression": ["content[0].extension"],
    }


def test_validate_two_content_with_different_retrieval_mechanisms():
    """Test that two content items with different retrieval mechanisms are valid."""
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    unstructured_format = {
        "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLFormatCode",
        "code": "urn:nhs-ic:unstructured",
        "display": "Unstructured Document",
    }

    static_content_stability = {
        "url": "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-ContentStability",
        "valueCodeableConcept": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLContentStability",
                    "code": "static",
                    "display": "Static",
                }
            ]
        },
    }

    # Add retrieval mechanism extension to the first content item, ssp
    first_content = {
        "attachment": {
            "contentType": "application/pdf",
            "url": "ssp://example.com/document1.pdf",
        },
        "format": unstructured_format,
        "extension": [
            {
                "url": "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-RetrievalMechanism",
                "valueCodeableConcept": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/England/CodeSystem/England-RetrievalMechanism",
                            "code": "SSP",
                            "display": "Spine Secure Proxy",
                        }
                    ]
                },
            },
            static_content_stability,
        ],
    }

    document_ref_data["content"] = [first_content]

    # Add valid ASID identifier in context.related
    document_ref_data["context"]["related"] = [
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/nhsSpineASID",
                "value": "123456789012",
            }
        }
    ]

    result = validator.validate(document_ref_data)

    assert result.is_valid is True
    assert len(result.issues) == 0

    # Add a second content item with a different retrieval mechanism
    second_content = {
        "attachment": {
            "contentType": "application/pdf",
            "url": "http://example.com/document2.pdf",
        },
        "format": unstructured_format,
        "extension": [
            {
                "url": "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-RetrievalMechanism",
                "valueCodeableConcept": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/England/CodeSystem/England-RetrievalMechanism",
                            "code": "Direct",
                            "display": "Direct",
                        }
                    ]
                },
            },
            static_content_stability,
        ],
    }

    document_ref_data["content"].append(second_content)

    result = validator.validate(document_ref_data)

    assert result.is_valid is True
    assert len(result.issues) == 0


def test_validate_content_retrieval_lowercase_urls():
    """Test that the extension is recognised when 'RetrievalMechanism' is in lowercase and throws an error for mismatching the URL case."""
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["content"][0]["extension"] = [
        {
            "url": "https://fhir.nhs.uk/england/structuredefinition/extension-england-retrievalmechanism",
            "valueCodeableConcept": {
                "coding": [
                    {
                        "system": "https://fhir.nhs.uk/England/CodeSystem/England-RetrievalMechanism",
                        "code": "Direct",
                        "display": "Direct",
                    }
                ]
            },
        },
        {
            "url": "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-ContentStability",
            "valueCodeableConcept": {
                "coding": [
                    {
                        "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLContentStability",
                        "code": "static",
                        "display": "Static",
                    }
                ]
            },
        },
    ]

    with pytest.raises(ParseError) as exc_info:
        validator.validate(document_ref_data)

    assert len(exc_info.value.issues) == 1
    assert exc_info.value.issues[0].model_dump(exclude_none=True) == {
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
        "diagnostics": "Invalid content retrieval extension (content[0].extension[0].url: Input should be 'https://fhir.nhs.uk/England/StructureDefinition/Extension-England-RetrievalMechanism', see: https://fhir.nhs.uk/England/ValueSet/England-RetrievalMechanism)",
        "expression": ["content[0].extension[0].url"],
    }
