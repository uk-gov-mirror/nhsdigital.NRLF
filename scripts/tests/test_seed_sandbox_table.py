import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, mock_open, patch

import pytest
from botocore.exceptions import ClientError
from seed_sandbox_table import (
    _check_for_existing_sandbox_pointers,
    _create_pointer_item,
    _generate_and_write_pointers,
    _load_pointer_templates,
    _load_sample_template,
    _make_realistic_pointer,
    _validate_table_access,
    _write_batch_to_dynamodb,
    _write_pointer_extract,
    seed_sandbox_table,
)

# ============================================================================
# _load_sample_template tests
# ============================================================================


@patch("builtins.open", new_callable=mock_open, read_data='{"id": "test"}')
def test_load_valid_template(mock_file):
    result = _load_sample_template("test.json")

    assert result == {"id": "test"}
    mock_file.assert_called_once()


@patch("builtins.open", side_effect=FileNotFoundError)
def test_load_missing_template(mock_file):
    with pytest.raises(FileNotFoundError):
        _load_sample_template("missing.json")


@patch("builtins.open", new_callable=mock_open, read_data="invalid json")
def test_load_invalid_json(mock_file):
    with pytest.raises(json.JSONDecodeError):
        _load_sample_template("invalid.json")


# ============================================================================
# _validate_table_access tests
# ============================================================================


@patch("seed_sandbox_table.resource")
def test_successful_table_access(mock_resource):
    mock_table = MagicMock()
    mock_resource.Table.return_value = mock_table

    result = _validate_table_access("test-table")

    assert result == mock_table
    mock_resource.Table.assert_called_once_with("test-table")
    mock_table.load.assert_called_once()


@patch("seed_sandbox_table.resource")
@patch("builtins.print")
@patch("sys.exit")
def test_table_not_found(mock_exit, mock_print, mock_resource):
    mock_exit.side_effect = SystemExit(1)

    mock_table = MagicMock()
    mock_table.load.side_effect = ClientError(
        {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": "Table not found",
            }
        },
        "DescribeTable",
    )
    mock_resource.Table.return_value = mock_table

    with pytest.raises(SystemExit):
        _validate_table_access("nonexistent-table")

    mock_exit.assert_called_once_with(1)
    mock_print.assert_called_with("Error: Table 'nonexistent-table' does not exist")


@patch("seed_sandbox_table.resource")
@patch("builtins.print")
@patch("sys.exit")
def test_access_denied(mock_exit, mock_print, mock_resource):
    mock_exit.side_effect = SystemExit(1)

    mock_table = MagicMock()
    mock_table.load.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}},
        "DescribeTable",
    )
    mock_resource.Table.return_value = mock_table

    with pytest.raises(SystemExit):
        _validate_table_access("protected-table")

    mock_exit.assert_called_once_with(1)
    mock_print.assert_called_with(
        "Error: No permission to access table 'protected-table'"
    )


# ============================================================================
# _check_for_existing_sandbox_pointers tests
# ============================================================================


@patch("builtins.print")
def test_force_mode_enabled(mock_print):
    mock_table = MagicMock()

    _check_for_existing_sandbox_pointers(mock_table, force=True)

    mock_table.scan.assert_not_called()
    mock_print.assert_called_with(
        "⚠️  Force mode enabled - will overwrite existing sandbox pointers"
    )


def test_no_existing_pointers():
    mock_table = MagicMock()
    mock_table.scan.return_value = {"Items": []}

    _check_for_existing_sandbox_pointers(mock_table, force=False)

    mock_table.scan.assert_called_once()


@patch("builtins.print")
@patch("sys.exit")
def test_existing_pointers_found(mock_exit, mock_print):
    mock_exit.side_effect = SystemExit(1)

    mock_table = MagicMock()
    mock_table.scan.return_value = {"Items": [{"id": "existing"}]}

    with pytest.raises(SystemExit):
        _check_for_existing_sandbox_pointers(mock_table, force=False)

    mock_exit.assert_called_once_with(1)

    print_calls = [str(call) for call in mock_print.call_args_list]
    assert any(
        "Warning: Sandbox pointers already exist" in call for call in print_calls
    )


# ============================================================================
# _load_pointer_templates tests
# ============================================================================


@patch("seed_sandbox_table._load_sample_template")
@patch(
    "seed_sandbox_table.SAMPLE_TEMPLATES",
    {"type1": "file1.json", "type2": "file2.json"},
)
def test_load_all_templates_success(mock_load):
    mock_load.side_effect = [{"template": "1"}, {"template": "2"}]

    result = _load_pointer_templates()

    assert len(result) == 2
    assert result["type1"] == {"template": "1"}
    assert result["type2"] == {"template": "2"}


@patch("seed_sandbox_table._load_sample_template")
@patch(
    "seed_sandbox_table.SAMPLE_TEMPLATES",
    {"type1": "file1.json", "type2": "file2.json"},
)
@patch("builtins.print")
def test_load_templates_with_failures(mock_print, mock_load):
    mock_load.side_effect = [{"template": "1"}, FileNotFoundError()]

    result = _load_pointer_templates()

    assert len(result) == 1
    assert result["type1"] == {"template": "1"}
    mock_print.assert_any_call("✗ Template file not found: file2.json")


@patch("seed_sandbox_table._load_sample_template")
@patch("seed_sandbox_table.SAMPLE_TEMPLATES", {"type1": "file1.json"})
@patch("builtins.print")
@patch("sys.exit")
def test_load_templates_all_fail(mock_exit, mock_print, mock_load):
    mock_exit.side_effect = SystemExit(1)
    mock_load.side_effect = FileNotFoundError()

    with pytest.raises(SystemExit):
        _load_pointer_templates()

    mock_exit.assert_called_once_with(1)
    mock_print.assert_any_call("Error: No templates could be loaded. Exiting.")


# ============================================================================
# _make_realistic_pointer tests
# ============================================================================


@patch("seed_sandbox_table.DocumentReference")
@patch("seed_sandbox_table.DocumentPointer")
def test_create_pointer_success(mock_pointer_class, mock_doc_ref_class):
    template = {
        "id": "original",
        "subject": {"identifier": {"value": "0000000000"}},
        "custodian": {"identifier": {"value": "OLD"}},
        "author": [{"identifier": {"value": "OLD_AUTHOR"}}],
        "masterIdentifier": {"value": "old-master"},
    }

    mock_doc_ref = MagicMock()
    mock_doc_ref_class.return_value = mock_doc_ref

    mock_pointer = MagicMock()
    mock_pointer_class.from_document_reference.return_value = mock_pointer

    result = _make_realistic_pointer(template, "Y12345", "9000000001", 1)

    assert result == mock_pointer
    mock_doc_ref_class.assert_called_once()
    mock_pointer_class.from_document_reference.assert_called_once_with(
        mock_doc_ref, source="SANDBOX-SEED"
    )


@patch("seed_sandbox_table.DocumentReference")
@patch("seed_sandbox_table.DocumentPointer")
def test_creates_content_structure_when_missing(mock_pointer_class, mock_doc_ref_class):
    template = {
        "id": "original",
        "subject": {"identifier": {"value": "0000000000"}},
        "custodian": {"identifier": {"value": "OLD"}},
        "author": [{"identifier": {"value": "OLD_AUTHOR"}}],
    }

    mock_doc_ref = MagicMock()
    mock_doc_ref_class.return_value = mock_doc_ref

    mock_pointer = MagicMock()
    mock_pointer_class.from_document_reference.return_value = mock_pointer

    _make_realistic_pointer(template, "Y12345", "9000000001", 1)

    call_args = mock_doc_ref_class.call_args[1]
    assert "content" in call_args
    assert len(call_args["content"]) > 0
    assert "extension" in call_args["content"][0]
    extensions = call_args["content"][0]["extension"]
    assert any(
        ext.get("url")
        == "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-NRLRetrievalMechanism"
        for ext in extensions
    )


@patch("seed_sandbox_table.DocumentReference")
@patch("seed_sandbox_table.DocumentPointer")
def test_adds_retrieval_mechanism_when_content_exists_without_it(
    mock_pointer_class, mock_doc_ref_class
):
    template = {
        "id": "original",
        "subject": {"identifier": {"value": "0000000000"}},
        "custodian": {"identifier": {"value": "OLD"}},
        "author": [{"identifier": {"value": "OLD_AUTHOR"}}],
        "content": [{"extension": [{"url": "some-other-extension", "value": "test"}]}],
    }

    mock_doc_ref = MagicMock()
    mock_doc_ref_class.return_value = mock_doc_ref

    mock_pointer = MagicMock()
    mock_pointer_class.from_document_reference.return_value = mock_pointer

    _make_realistic_pointer(template, "Y12345", "9000000001", 1)

    call_args = mock_doc_ref_class.call_args[1]
    extensions = call_args["content"][0]["extension"]
    assert len(extensions) == 2
    assert any(
        ext.get("url")
        == "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-NRLRetrievalMechanism"
        for ext in extensions
    )


@patch("seed_sandbox_table.DocumentReference")
@patch("seed_sandbox_table.DocumentPointer")
def test_does_not_duplicate_retrieval_mechanism_when_already_present(
    mock_pointer_class, mock_doc_ref_class
):
    template = {
        "id": "original",
        "subject": {"identifier": {"value": "0000000000"}},
        "custodian": {"identifier": {"value": "OLD"}},
        "author": [{"identifier": {"value": "OLD_AUTHOR"}}],
        "content": [
            {
                "extension": [
                    {
                        "url": "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-NRLRetrievalMechanism",
                        "valueCodeableConcept": {
                            "coding": [
                                {
                                    "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLRetrievalMechanism",
                                    "code": "SSP",
                                    "display": "Spine Secure Proxy",
                                }
                            ]
                        },
                    }
                ]
            }
        ],
    }

    mock_doc_ref = MagicMock()
    mock_doc_ref_class.return_value = mock_doc_ref

    mock_pointer = MagicMock()
    mock_pointer_class.from_document_reference.return_value = mock_pointer

    _make_realistic_pointer(template, "Y12345", "9000000001", 1)

    call_args = mock_doc_ref_class.call_args[1]
    extensions = call_args["content"][0]["extension"]
    retrieval_mechanism_count = sum(
        1
        for ext in extensions
        if ext.get("url")
        == "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-NRLRetrievalMechanism"
    )
    assert retrieval_mechanism_count == 1


# ============================================================================
# _write_batch_to_dynamodb tests
# ============================================================================


@patch("seed_sandbox_table.resource")
def test_empty_batch_returns_true(mock_resource):
    result = _write_batch_to_dynamodb("test-table", [])

    assert result is True
    mock_resource.batch_write_item.assert_not_called()


@patch("seed_sandbox_table.resource")
@patch("builtins.print")
def test_successful_batch_write(mock_print, mock_resource):
    mock_resource.batch_write_item.return_value = {}

    batch_items = [{"PutRequest": {"Item": {"id": "test"}}}]
    result = _write_batch_to_dynamodb("test-table", batch_items)

    assert result is True
    mock_resource.batch_write_item.assert_called_once_with(
        RequestItems={"test-table": batch_items}
    )
    mock_print.assert_called_once_with(".", end="", flush=True)


@patch("seed_sandbox_table.resource")
@patch("builtins.print")
def test_batch_write_with_unprocessed_items(mock_print, mock_resource):
    mock_resource.batch_write_item.return_value = {
        "UnprocessedItems": {"test-table": [{"PutRequest": {"Item": {"id": "1"}}}]}
    }

    batch_items = [{"PutRequest": {"Item": {"id": "test"}}}]
    result = _write_batch_to_dynamodb("test-table", batch_items)

    assert result is True
    mock_print.assert_any_call("\nWarning: 1 unprocessed items")


@patch("seed_sandbox_table.resource")
@patch("builtins.print")
def test_batch_write_throttling_error(mock_print, mock_resource):
    mock_resource.batch_write_item.side_effect = ClientError(
        {
            "Error": {
                "Code": "ProvisionedThroughputExceededException",
                "Message": "Throttled",
            }
        },
        "BatchWriteItem",
    )

    batch_items = [{"PutRequest": {"Item": {"id": "test"}}}]
    result = _write_batch_to_dynamodb("test-table", batch_items)

    assert result is False
    mock_print.assert_called_with("\n✗ Throttled. Retrying batch...")


@patch("seed_sandbox_table.resource")
@patch("builtins.print")
def test_batch_write_other_error(mock_print, mock_resource):
    error = ClientError(
        {"Error": {"Code": "ValidationException", "Message": "Invalid"}},
        "BatchWriteItem",
    )
    mock_resource.batch_write_item.side_effect = error

    batch_items = [{"PutRequest": {"Item": {"id": "test"}}}]
    result = _write_batch_to_dynamodb("test-table", batch_items)

    assert result is False
    print_calls = [str(call) for call in mock_print.call_args_list]
    assert any("Error writing batch" in call for call in print_calls)


# ============================================================================
# _create_pointer_item tests
# ============================================================================


@patch("seed_sandbox_table._make_realistic_pointer")
def test_successful_pointer_creation(mock_make_pointer):
    template = {"id": "test"}
    mock_pointer = MagicMock()
    mock_pointer.id = "PTR-001"
    mock_pointer.custodian = "CUST1"
    mock_pointer.nhs_number = "9000000001"
    mock_pointer.model_dump.return_value = {
        "id": "PTR-001",
        "custodian": "CUST1",
        "nhs_number": "9000000001",
    }
    mock_make_pointer.return_value = mock_pointer

    put_req, csv_data = _create_pointer_item(
        template, "CUST1", "9000000001", 1, "type1"
    )

    assert put_req == {
        "PutRequest": {
            "Item": {
                "id": "PTR-001",
                "custodian": "CUST1",
                "nhs_number": "9000000001",
            }
        }
    }
    assert csv_data == ["PTR-001", "type1", "CUST1", "9000000001"]
    mock_make_pointer.assert_called_once_with(template, "CUST1", "9000000001", 1)


@patch("seed_sandbox_table._make_realistic_pointer")
@patch("builtins.print")
def test_pointer_creation_value_error(mock_print, mock_make_pointer):
    template = {"id": "test"}
    mock_make_pointer.side_effect = ValueError("Invalid NHS number")

    put_req, csv_data = _create_pointer_item(template, "CUST1", "invalid", 1, "type1")

    assert put_req is None
    assert csv_data is None
    mock_print.assert_called_once_with(
        "\n✗ Validation error for pointer 1: Invalid NHS number"
    )


@patch("seed_sandbox_table._make_realistic_pointer")
@patch("builtins.print")
def test_pointer_creation_general_error(mock_print, mock_make_pointer):
    template = {"id": "test"}
    mock_make_pointer.side_effect = Exception("Unexpected error")

    put_req, csv_data = _create_pointer_item(
        template, "CUST1", "9000000001", 1, "type1"
    )

    assert put_req is None
    assert csv_data is None
    mock_print.assert_called_once_with("\n✗ Error creating pointer 1: Unexpected error")


# ============================================================================
# _generate_and_write_pointers tests
# ============================================================================


@patch("seed_sandbox_table.resource")
@patch("seed_sandbox_table._make_realistic_pointer")
@patch("seed_sandbox_table.CUSTODIANS", ["CUST1"])
def test_generate_pointers_success(mock_make_pointer, mock_resource):
    templates = {"type1": {"template": "data"}}

    mock_pointer = MagicMock()
    mock_pointer.id = "TEST-001"
    mock_pointer.custodian = "CUST1"
    mock_pointer.nhs_number = "9000000001"
    mock_pointer.model_dump.return_value = {"id": "TEST-001"}
    mock_make_pointer.return_value = mock_pointer

    mock_resource.batch_write_item.return_value = {}

    nhs_iter = iter(["9000000001", "9000000002"])

    pointer_data, total_attempts = _generate_and_write_pointers(
        "test-table", templates, 2, nhs_iter
    )

    assert total_attempts == 2
    assert len(pointer_data) == 2
    assert pointer_data[0][0] == "TEST-001"


@patch("seed_sandbox_table.resource")
@patch("seed_sandbox_table._make_realistic_pointer")
@patch("seed_sandbox_table.CUSTODIANS", ["CUST1"])
def test_generate_pointers_with_validation_error(mock_make_pointer, mock_resource):
    templates = {"type1": {"template": "data"}}

    mock_make_pointer.side_effect = [ValueError("Invalid data"), MagicMock()]

    nhs_iter = iter(["9000000001", "9000000002"])

    pointer_data, total_attempts = _generate_and_write_pointers(
        "test-table", templates, 2, nhs_iter
    )

    # First attempt failed, second succeeded
    assert total_attempts == 2
    assert len(pointer_data) == 1


@patch("seed_sandbox_table.resource")
@patch("seed_sandbox_table._make_realistic_pointer")
@patch("seed_sandbox_table.CUSTODIANS", ["CUST1"])
def test_generate_pointers_respects_batch_limit(mock_make_pointer, mock_resource):
    templates = {"type1": {"template": "data"}}

    mock_pointer = MagicMock()
    mock_pointer.id = "TEST-001"
    mock_pointer.custodian = "CUST1"
    mock_pointer.nhs_number = "9000000001"
    mock_pointer.model_dump.return_value = {"id": "TEST-001"}
    mock_make_pointer.return_value = mock_pointer

    mock_resource.batch_write_item.return_value = {}

    nhs_numbers = [f"900000{i:04d}" for i in range(30)]
    nhs_iter = iter(nhs_numbers)

    pointer_data, _ = _generate_and_write_pointers(
        "test-table", templates, 30, nhs_iter
    )

    for call in mock_resource.batch_write_item.call_args_list:
        request_items = call[1]["RequestItems"]["test-table"]
        assert (
            len(request_items) <= 25
        ), f"Batch exceeded 25 items: {len(request_items)}"

    assert mock_resource.batch_write_item.call_count >= 2
    assert len(pointer_data) == 30


# ============================================================================
# seed_sandbox_table tests
# ============================================================================


@patch("seed_sandbox_table._validate_table_access")
@patch("seed_sandbox_table._check_for_existing_sandbox_pointers")
@patch("seed_sandbox_table._load_pointer_templates")
@patch("seed_sandbox_table._generate_and_write_pointers")
@patch("seed_sandbox_table._write_pointer_extract")
@patch("seed_sandbox_table.TestNhsNumbersIterator")
def test_seed_table_success(
    mock_nhs_iter_class,
    mock_write_extract,
    mock_generate,
    mock_load_templates,
    mock_check_pointers,
    mock_validate,
):
    mock_table = MagicMock()
    mock_validate.return_value = mock_table

    mock_templates = {"type1": {"template": "data"}}
    mock_load_templates.return_value = mock_templates

    pointer_data = [["PTR-001", "type1", "CUST1", "9000000001"]]
    mock_generate.return_value = (pointer_data, 1)

    result = seed_sandbox_table("test-table", pointers_per_type=1, force=False)

    assert result == {"successful": 1, "attempted": 1, "failed": 0}
    mock_validate.assert_called_once_with("test-table")
    mock_check_pointers.assert_called_once_with(mock_table, False)
    mock_generate.assert_called_once()
    mock_write_extract.assert_called_once()


@patch("seed_sandbox_table._validate_table_access")
@patch("seed_sandbox_table._check_for_existing_sandbox_pointers")
@patch("seed_sandbox_table._load_pointer_templates")
@patch("seed_sandbox_table._generate_and_write_pointers")
@patch("seed_sandbox_table._write_pointer_extract")
@patch("seed_sandbox_table.TestNhsNumbersIterator")
@patch("builtins.print")
def test_seed_table_with_failures(
    mock_print,
    mock_nhs_iter_class,
    mock_write_extract,
    mock_generate,
    mock_load_templates,
    mock_check_pointers,
    mock_validate,
):
    mock_table = MagicMock()
    mock_validate.return_value = mock_table

    mock_templates = {"type1": {"template": "data"}}
    mock_load_templates.return_value = mock_templates

    pointer_data = [
        ["PTR-001", "type1", "CUST1", "9000000001"],
        ["PTR-002", "type1", "CUST1", "9000000002"],
        ["PTR-003", "type1", "CUST1", "9000000003"],
    ]
    mock_generate.return_value = (pointer_data, 5)

    result = seed_sandbox_table("test-table", pointers_per_type=1, force=False)

    assert result == {"successful": 3, "attempted": 5, "failed": 2}

    mock_print.assert_any_call("⚠️  2 pointer(s) failed to create")


@patch("seed_sandbox_table._validate_table_access")
@patch("seed_sandbox_table._check_for_existing_sandbox_pointers")
@patch("seed_sandbox_table._load_pointer_templates")
@patch("seed_sandbox_table._generate_and_write_pointers")
@patch("seed_sandbox_table._write_pointer_extract")
@patch("seed_sandbox_table.TestNhsNumbersIterator")
def test_seed_table_skip_csv_writing(
    mock_nhs_iter_class,
    mock_write_extract,
    mock_generate,
    mock_load_templates,
    mock_check_pointers,
    mock_validate,
):
    mock_table = MagicMock()
    mock_validate.return_value = mock_table

    mock_templates = {"type1": {"template": "data"}}
    mock_load_templates.return_value = mock_templates

    pointer_data = [["PTR-001", "type1", "CUST1", "9000000001"]]
    mock_generate.return_value = (pointer_data, 1)

    result = seed_sandbox_table(
        "test-table", pointers_per_type=1, force=False, write_csv=False
    )

    assert result == {"successful": 1, "attempted": 1, "failed": 0}
    mock_write_extract.assert_not_called()
