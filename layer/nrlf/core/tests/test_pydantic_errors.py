import pytest

from nrlf.core.constants import SNOMED_SYSTEM_URL
from nrlf.core.errors import ParseError
from nrlf.core.validators import DocumentReferenceValidator
from nrlf.tests.data import load_document_reference_json


def test_validate_content_missing_attachment():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["content"][0].pop("attachment")

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
        "diagnostics": "Failed to parse DocumentReference resource (content[0].attachment: Field required)",
        "expression": ["content[0].attachment"],
    }


def test_validate_content_missing_content_type():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["content"][0]["attachment"].pop("contentType")

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
        "diagnostics": "Failed to parse DocumentReference resource (content[0].attachment.contentType: Field required)",
        "expression": ["content[0].attachment.contentType"],
    }


def test_validate_content_missing_format():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["content"][0].pop("format")

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
        "diagnostics": "Failed to parse DocumentReference resource (content[0].format: Field required. See ValueSet: https://fhir.nhs.uk/England/CodeSystem/England-NRLFormatCode)",
        "expression": ["content[0].format"],
    }


def test_validate_content_multiple_content_stability_extensions():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    # Add a second duplicate contentStability extension
    document_ref_data["content"][0]["extension"].append(
        document_ref_data["content"][0]["extension"][0]
    )

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
        "diagnostics": "Failed to parse DocumentReference resource (content[0].extension: List should have at most 1 item after validation, not 2. See ValueSet: https://fhir.nhs.uk/England/CodeSystem/England-NRLContentStability)",
        "expression": ["content[0].extension"],
    }


def test_validate_content_invalid_content_stability_code():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    # Set an invalid code for contentStability extension
    content_extension = document_ref_data["content"][0]["extension"][0]
    content_extension["valueCodeableConcept"]["coding"][0]["code"] = "invalid"

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
        "diagnostics": "Failed to parse DocumentReference resource (content[0].extension[0].valueCodeableConcept.coding[0].code: Input should be 'static' or 'dynamic'. See ValueSet: https://fhir.nhs.uk/England/CodeSystem/England-NRLContentStability)",
        "expression": ["content[0].extension[0].valueCodeableConcept.coding[0].code"],
    }


def test_validate_content_invalid_content_stability_display():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    # Set an invalid display for contentStability extension
    content_extension = document_ref_data["content"][0]["extension"][0]
    content_extension["valueCodeableConcept"]["coding"][0]["display"] = "invalid"

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
        "diagnostics": "Failed to parse DocumentReference resource (content[0].extension[0].valueCodeableConcept.coding[0].display: Input should be 'Static' or 'Dynamic'. See ValueSet: https://fhir.nhs.uk/England/CodeSystem/England-NRLContentStability)",
        "expression": [
            "content[0].extension[0].valueCodeableConcept.coding[0].display"
        ],
    }


def test_validate_content_invalid_content_stability_system():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    # Set an invalid system for contentStability extension
    content_extension = document_ref_data["content"][0]["extension"][0]
    content_extension["valueCodeableConcept"]["coding"][0]["system"] = "invalid"

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
        "diagnostics": "Failed to parse DocumentReference resource (content[0].extension[0].valueCodeableConcept.coding[0].system: Input should be 'https://fhir.nhs.uk/England/CodeSystem/England-NRLContentStability')",
        "expression": ["content[0].extension[0].valueCodeableConcept.coding[0].system"],
    }


def test_validate_content_invalid_content_stability_url():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    # Set an invalid URL for contentStability extension
    document_ref_data["content"][0]["extension"][0]["url"] = "invalid"

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
        "diagnostics": "Failed to parse DocumentReference resource (content[0].extension[0].url: Input should be 'https://fhir.nhs.uk/England/StructureDefinition/Extension-England-ContentStability')",
        "expression": ["content[0].extension[0].url"],
    }


def test_validate_multiple_codings():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["category"][0] = {
        "coding": [
            {
                "system": SNOMED_SYSTEM_URL,
                "code": "734163000",
                "display": "Care plan",
            },
            {
                "system": SNOMED_SYSTEM_URL,
                "code": "734163000",
                "display": "Care plan",
            },
            {
                "system": SNOMED_SYSTEM_URL,
                "code": "734163000",
                "display": "Care plan",
            },
        ]
    }

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
        "diagnostics": "Failed to parse DocumentReference resource (category[0].coding: List should have at most 1 item after validation, not 3)",
        "expression": ["category[0].coding"],
    }


def test_validate_whitespace_strings():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["category"][0] = {
        "coding": [
            {
                "system": SNOMED_SYSTEM_URL,
                "code": "734163000",
                "display": "  ",
            }
        ]
    }

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
        "diagnostics": "Failed to parse DocumentReference resource (category[0].coding[0].display: String should match pattern '[\\S]+[ \\r\\n\\t\\S]*')",
        "expression": ["category[0].coding[0].display"],
    }


def test_validate_no_coding_where_mandatory():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["context"]["practiceSetting"] = {
        "text": "Description of the clinic in text"
    }

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
        "diagnostics": "Failed to parse DocumentReference resource (context.practiceSetting.coding: Field required)",
        "expression": ["context.practiceSetting.coding"],
    }


def test_validate_no_coding_where_optional():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["context"]["facilityType"] = {
        "text": "Description of the facility type in text"
    }

    result = validator.validate(document_ref_data)

    assert result.is_valid


def test_validate_missing_system_from_coding_where_mandatory():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["context"]["practiceSetting"] = {
        "coding": [
            {
                "code": "734163000",
                "display": "Valid display string",
            }
        ]
    }

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
        "diagnostics": "Failed to parse DocumentReference resource (context.practiceSetting.coding[0].system: Field required)",
        "expression": ["context.practiceSetting.coding[0].system"],
    }


def test_validate_missing_code_from_coding_where_mandatory():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["context"]["practiceSetting"] = {
        "coding": [
            {
                "system": SNOMED_SYSTEM_URL,
                "display": "Valid display string",
            }
        ]
    }

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
        "diagnostics": "Failed to parse DocumentReference resource (context.practiceSetting.coding[0].code: Field required)",
        "expression": ["context.practiceSetting.coding[0].code"],
    }


def test_validate_missing_display_from_coding_where_mandatory():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["context"]["practiceSetting"] = {
        "coding": [
            {
                "system": SNOMED_SYSTEM_URL,
                "code": "788002001",
            }
        ]
    }

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
        "diagnostics": "Failed to parse DocumentReference resource (context.practiceSetting.coding[0].display: Field required)",
        "expression": ["context.practiceSetting.coding[0].display"],
    }
