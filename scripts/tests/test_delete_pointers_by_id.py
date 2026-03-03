import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

import pytest
from delete_pointers_by_id import (
    PointerDeletionContext,
    _batch_delete_pointers,
    _batch_get_existing_pointers,
    _build_and_write_result,
    _check_pointers_match_ods_code,
    _delete_pointers_by_id,
    _is_valid_pointer,
    _load_pointers_from_file,
    _parse_json_pointers,
    _parse_plain_text_pointers,
)

# ============================================================================
#  _load_pointers_from_file tests
# ============================================================================


@patch("builtins.open", create=True)
def test_load_json_array(mock_open):
    mock_open.return_value.__enter__.return_value.read.return_value = (
        '[{"id": "G3H9E-id1"}, {"id": "G3H9E-id2"}]'
    )
    result = _load_pointers_from_file("./pointers.json")
    assert result == ["G3H9E-id1", "G3H9E-id2"]


@patch("builtins.open", create=True)
def test_load_plain_text_file(mock_open):
    mock_open.return_value.__enter__.return_value.read.return_value = (
        "G3H9E-id1\nG3H9E-id2\nG3H9E-id3"
    )
    result = _load_pointers_from_file("./ids.txt")
    assert result == ["G3H9E-id1", "G3H9E-id2", "G3H9E-id3"]


@patch("builtins.open", create=True)
def test_load_empty_file(mock_open):
    mock_open.return_value.__enter__.return_value.read.return_value = ""
    result = _load_pointers_from_file("./empty.txt")
    assert result == []


# ============================================================================
#  _parse_json_pointers tests
# ============================================================================


def test_invalid_json():
    content = '[{"id": "G3H9E-id1"'
    with pytest.raises(ValueError, match="Failed to parse JSON file"):
        _parse_json_pointers(content, "./invalid.json")


def test_json_not_array():
    content = '{"id": "G3H9E-id1"}'
    with pytest.raises(ValueError, match="JSON file must contain an array of objects"):
        _parse_json_pointers(content, "./not_array.json")


def test_valid_json_array():
    content = '[{"id": "G3H9E-id1"}, {"id": "G3H9E-id2"}]'
    result = _parse_json_pointers(content, "./pointers.json")
    assert result == ["G3H9E-id1", "G3H9E-id2"]


def test_json_with_malformed_entries():
    content = '[{"id": "G3H9E-id1"}, {"patient_number": "123"}, {"id": ""}, {"id": "G3H9E-id2"}]'
    result = _parse_json_pointers(content, "./pointers.json")
    assert result == ["G3H9E-id1", "G3H9E-id2"]


# ============================================================================
#  _is_valid_pointer tests
# ============================================================================


def test_valid_pointer():
    item = {"id": "G3H9E-id1"}
    assert _is_valid_pointer(item)


def test_missing_id_field():
    item = {"patient_number": "123"}
    assert not _is_valid_pointer(item)


def test_empty_id_field():
    item = {"id": ""}
    assert not _is_valid_pointer(item)


def test_non_string_id_field():
    item = {"id": 123}
    assert not _is_valid_pointer(item)


def test_non_dict_item():
    item = ["id", "G3H9E-id1"]
    assert not _is_valid_pointer(item)


# ============================================================================
#  _parse_plain_text_pointers tests
# ============================================================================


def test_valid_plain_text():
    content = "G3H9E-id1\nG3H9E-id2\nG3H9E-id3"
    result = _parse_plain_text_pointers(content)
    assert result == ["G3H9E-id1", "G3H9E-id2", "G3H9E-id3"]


def test_plain_text_with_empty_lines():
    content = "G3H9E-id1\n\nG3H9E-id2\n  \nG3H9E-id3"
    result = _parse_plain_text_pointers(content)
    assert result == ["G3H9E-id1", "G3H9E-id2", "G3H9E-id3"]


def test_empty_plain_text():
    content = ""
    result = _parse_plain_text_pointers(content)
    assert result == []


# ============================================================================
#  _build_and_write_result tests
# ============================================================================


@patch("delete_pointers_by_id._write_result_file")
@patch("delete_pointers_by_id._print_summary")
def test_build_and_write_result_success(mock_print, mock_write):
    start_time = datetime.now(tz=timezone.utc)
    end_time = datetime.now(tz=timezone.utc)
    ctx = PointerDeletionContext(
        pointers_to_delete=["G3H9E-1", "G3H9E-2"],
        ods_code="G3H9E",
        matched_pointers=["G3H9E-1", "G3H9E-2"],
        mismatched_pointers=[],
        not_found_pointers=[],
        pointers_deleted=["G3H9E-1", "G3H9E-2"],
        failed_deletes=[],
        start_time=start_time,
        end_time=end_time,
        output_filename="delete_results_G3H9E_20231125T120000Z.json",
    )
    result = _build_and_write_result(ctx)
    assert result["pointers_to_delete"] == 2
    assert result["deleted_pointers"]["count"] == 2
    assert result["ods_code"] == "G3H9E"
    assert result["output_filename"] == "delete_results_G3H9E_20231125T120000Z.json"
    assert "_output_error" not in result
    mock_write.assert_called_once()
    mock_print.assert_called_once()


@patch("delete_pointers_by_id._write_result_file")
@patch("delete_pointers_by_id._print_summary")
def test_build_and_write_result_with_error(mock_print, mock_write):
    mock_write.side_effect = Exception("Write failed")
    start_time = datetime.now(tz=timezone.utc)
    end_time = datetime.now(tz=timezone.utc)
    ctx = PointerDeletionContext(
        pointers_to_delete=["G3H9E-1"],
        ods_code="G3H9E",
        matched_pointers=["G3H9E-1"],
        mismatched_pointers=[],
        not_found_pointers=[],
        pointers_deleted=["G3H9E-1"],
        failed_deletes=[],
        start_time=start_time,
        end_time=end_time,
        output_filename="delete_results_G3H9E_20231125T120000Z.json",
    )
    result = _build_and_write_result(ctx)
    assert "_output_error" in result
    assert "Write failed" in result["_output_error"]
    mock_write.assert_called_once()
    mock_print.assert_called_once()


# ============================================================================
#  _check_pointers_match_ods_code tests
# ============================================================================


def test_all_match():
    ods = "G3H9E"
    ids = ["G3H9E-a", "G3H9E-b"]
    matched, mismatched = _check_pointers_match_ods_code(ods, ids)
    assert matched == ids and mismatched == []


def test_none_match():
    ods = "G3H9E"
    ids = ["X-a", "Y-b"]
    matched, mismatched = _check_pointers_match_ods_code(ods, ids)
    assert matched == [] and mismatched == ids


def test_mixed():
    ods = "G3H9E"
    ids = ["G3H9E-a", "X-b", "G3H9E-c"]
    matched, mismatched = _check_pointers_match_ods_code(ods, ids)
    assert matched == ["G3H9E-a", "G3H9E-c"]
    assert mismatched == ["X-b"]


# ============================================================================
#  _batch_get_existing_pointers tests
# ============================================================================


@patch("delete_pointers_by_id.dynamodb")
def test_all_exist(mock_dynamodb):
    table = "t"
    ids = ["G3H9E-1", "G3H9E-2"]
    mock_dynamodb.batch_get_item.return_value = {
        "Responses": {table: [{"pk": {"S": "D#G3H9E-1"}}, {"pk": {"S": "D#G3H9E-2"}}]}
    }
    existing, not_found = _batch_get_existing_pointers(table, ids)
    assert existing == ids and not_found == []


@patch("delete_pointers_by_id.dynamodb")
def test_none_exist(mock_dynamodb):
    table = "t"
    ids = ["G3H9E-1", "G3H9E-2"]
    mock_dynamodb.batch_get_item.return_value = {"Responses": {table: []}}
    existing, not_found = _batch_get_existing_pointers(table, ids)
    assert existing == [] and not_found == ids


# ============================================================================
#  _batch_delete_pointers tests
# ============================================================================


@patch("delete_pointers_by_id.dynamodb")
def test_all_deleted(mock_dynamodb):
    table = "t"
    ids = ["G3H9E-1", "G3H9E-2"]
    mock_dynamodb.batch_write_item.return_value = {"UnprocessedItems": {}}
    deleted, failed = _batch_delete_pointers(table, ids)
    assert deleted == ids and failed == []


@patch("delete_pointers_by_id.dynamodb")
def test_some_unprocessed(mock_dynamodb):
    table = "t"
    ids = ["G3H9E-1", "G3H9E-2", "G3H9E-3"]
    mock_dynamodb.batch_write_item.return_value = {
        "UnprocessedItems": {
            table: [
                {
                    "DeleteRequest": {
                        "Key": {"pk": {"S": "D#G3H9E-3"}, "sk": {"S": "D#G3H9E-3"}}
                    }
                }
            ]
        }
    }
    deleted, failed = _batch_delete_pointers(table, ids)
    assert deleted == ["G3H9E-1", "G3H9E-2"]
    assert failed == ["G3H9E-3"]


# ============================================================================
#  _delete_pointers_by_id tests
# ============================================================================


def test_missing_params():
    with pytest.raises(
        ValueError,
        match="Must provide either --pointers_to_delete or --pointers_file",
    ):
        _delete_pointers_by_id("t", "G3H9E")


def test_both_params_provided():
    with pytest.raises(
        ValueError,
        match="Cannot provide both --pointers_to_delete and --pointers_file",
    ):
        _delete_pointers_by_id(
            "t", "G3H9E", pointers_to_delete=["a"], pointers_file="./f"
        )


@patch("delete_pointers_by_id._build_and_write_result")
@patch("delete_pointers_by_id._check_pointers_match_ods_code")
@patch("delete_pointers_by_id._batch_get_existing_pointers")
@patch("delete_pointers_by_id._batch_delete_pointers")
def test_empty_pointers_list(mock_delete, mock_get, mock_check, mock_build):

    _delete_pointers_by_id("t", "G3H9E", pointers_to_delete=[])

    mock_build.assert_called_once()
    mock_check.assert_not_called()
    mock_get.assert_not_called()
    mock_delete.assert_not_called()
    call_args = mock_build.call_args[0][0]

    assert call_args.pointers_to_delete == []
    assert call_args.matched_pointers == []


@patch("delete_pointers_by_id._check_pointers_match_ods_code")
@patch("delete_pointers_by_id._build_and_write_result")
@patch("delete_pointers_by_id._batch_get_existing_pointers")
@patch("delete_pointers_by_id._batch_delete_pointers")
def test_no_matched_ods_codes(mock_delete, mock_get, mock_build, mock_check):
    mock_check.return_value = ([], ["RAT-1", "RAT-2"])

    _delete_pointers_by_id("t", "G3H9E", pointers_to_delete=["RAT-1", "RAT-2"])

    mock_build.assert_called_once()
    mock_check.assert_called_once()
    mock_get.assert_not_called()
    mock_delete.assert_not_called()

    call_args = mock_build.call_args[0][0]
    assert call_args.matched_pointers == []
    assert call_args.mismatched_pointers == ["RAT-1", "RAT-2"]


@patch("delete_pointers_by_id._build_and_write_result")
@patch("delete_pointers_by_id._check_pointers_match_ods_code")
@patch("delete_pointers_by_id._batch_get_existing_pointers")
@patch("delete_pointers_by_id._batch_delete_pointers")
def test_successful_flow(mock_delete, mock_get, mock_check, mock_build):

    ids = ["G3H9E-1", "G3H9E-2"]
    mock_check.return_value = (ids, [])
    mock_get.return_value = (ids, [])
    mock_delete.return_value = (ids, [])

    _delete_pointers_by_id("t", "G3H9E", pointers_to_delete=ids)

    mock_build.assert_called_once()
    mock_check.assert_called_once()
    mock_get.assert_called_once()
    mock_delete.assert_called_once()

    call_args = mock_build.call_args[0][0]
    assert call_args.pointers_deleted == ids
    assert call_args.failed_deletes == []


@patch("delete_pointers_by_id._check_pointers_match_ods_code")
@patch("delete_pointers_by_id._batch_get_existing_pointers")
@patch("delete_pointers_by_id._build_and_write_result")
@patch("delete_pointers_by_id._batch_delete_pointers")
def test_partial_with_failures(mock_delete, mock_build, mock_get, mock_check):
    matched = ["G3H9E-1", "G3H9E-2", "G3H9E-3"]
    mock_check.return_value = (matched, ["RAT-1"])
    mock_get.return_value = (matched, [])
    mock_delete.return_value = (["G3H9E-1", "G3H9E-2"], ["G3H9E-3"])

    _delete_pointers_by_id("t", "G3H9E", pointers_to_delete=matched + ["RAT-1"])

    mock_build.assert_called_once()

    call_args = mock_build.call_args[0][0]
    assert call_args.mismatched_pointers == ["RAT-1"]
    assert call_args.pointers_deleted == ["G3H9E-1", "G3H9E-2"]
    assert call_args.failed_deletes == ["G3H9E-3"]


@patch("delete_pointers_by_id._build_and_write_result")
@patch("delete_pointers_by_id._check_pointers_match_ods_code")
@patch("delete_pointers_by_id._batch_get_existing_pointers")
@patch("delete_pointers_by_id._batch_delete_pointers")
def test_some_pointers_not_found(mock_delete, mock_get, mock_check, mock_build):
    matched = ["G3H9E-1", "G3H9E-2", "G3H9E-3"]
    mock_check.return_value = (matched, [])
    mock_get.return_value = (["G3H9E-1", "G3H9E-2"], ["G3H9E-3"])
    mock_delete.return_value = (["G3H9E-1", "G3H9E-2"], [])

    _delete_pointers_by_id("t", "G3H9E", pointers_to_delete=matched)

    mock_build.assert_called_once()

    call_args = mock_build.call_args[0][0]
    assert call_args.not_found_pointers == ["G3H9E-3"]
    assert call_args.pointers_deleted == ["G3H9E-1", "G3H9E-2"]


@patch("delete_pointers_by_id._build_and_write_result")
@patch("delete_pointers_by_id._check_pointers_match_ods_code")
@patch("delete_pointers_by_id._batch_get_existing_pointers")
@patch("delete_pointers_by_id._batch_delete_pointers")
def test_no_existing_pointers(mock_delete, mock_get, mock_check, mock_build):
    matched = ["G3H9E-1", "G3H9E-2"]
    mock_check.return_value = (matched, [])
    mock_get.return_value = ([], matched)

    _delete_pointers_by_id("t", "G3H9E", pointers_to_delete=matched)

    mock_build.assert_called_once()
    mock_delete.assert_not_called()

    call_args = mock_build.call_args[0][0]
    assert call_args.not_found_pointers == matched
    assert call_args.pointers_deleted == []
