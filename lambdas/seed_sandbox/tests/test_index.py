import json
from unittest.mock import MagicMock, patch

import pytest

from lambdas.seed_sandbox.index import handler


@pytest.fixture
def mock_lambda_context():
    mock_context = MagicMock()
    mock_context.function_name = "test-function"
    mock_context.invoked_function_arn = (
        "arn:aws:lambda:eu-west-2:123456789012:function:test-function"
    )
    return mock_context


@pytest.fixture
def mock_env_vars():
    with patch.dict(
        "os.environ", {"TABLE_NAMES": "test-table", "POINTERS_PER_TYPE": "2"}
    ):
        yield


@patch("lambdas.seed_sandbox.index.seed_sandbox_table")
@patch("lambdas.seed_sandbox.index.delete_all_table_items")
def test_single_table_reset_success(
    mock_delete, mock_seed, mock_lambda_context, mock_env_vars
):
    mock_delete.return_value = 10
    mock_seed.return_value = {"successful": 8, "attempted": 8, "failed": 0}

    result = handler({}, mock_lambda_context)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["message"] == "Successfully reset 1 table(s)"
    assert body["tables_processed"] == 1
    assert body["tables_succeeded"] == 1
    assert body["tables_failed"] == 0
    assert len(body["results"]) == 1
    assert body["results"][0]["table_name"] == "test-table"
    assert body["results"][0]["status"] == "success"
    assert body["results"][0]["pointers_deleted"] == 10
    assert body["results"][0]["pointers_created"] == 8

    mock_delete.assert_called_once_with(table_name="test-table")
    mock_seed.assert_called_once_with(
        table_name="test-table", pointers_per_type=2, force=True, write_csv=False
    )


@patch("lambdas.seed_sandbox.index.seed_sandbox_table")
@patch("lambdas.seed_sandbox.index.delete_all_table_items")
def test_multiple_table_reset_success(
    mock_delete, mock_seed, mock_lambda_context, mock_env_vars
):
    with patch.dict(
        "os.environ",
        {"TABLE_NAMES": "table1,table2,table3", "POINTERS_PER_TYPE": "5"},
    ):
        mock_delete.return_value = 15
        mock_seed.return_value = {"successful": 20, "attempted": 20, "failed": 0}

        result = handler({}, mock_lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["message"] == "Successfully reset 3 table(s)"
        assert body["tables_processed"] == 3
        assert body["tables_succeeded"] == 3
        assert body["tables_failed"] == 0
        assert len(body["results"]) == 3
        assert all(r["status"] == "success" for r in body["results"])

        assert mock_delete.call_count == 3
        assert mock_seed.call_count == 3


@patch("lambdas.seed_sandbox.index.seed_sandbox_table")
@patch("lambdas.seed_sandbox.index.delete_all_table_items")
def test_partial_failure(mock_delete, mock_seed, mock_lambda_context):
    with patch.dict(
        "os.environ",
        {"TABLE_NAMES": "table1,table2,table3", "POINTERS_PER_TYPE": "2"},
    ):
        # First and third tables succeed, second fails during delete
        mock_delete.side_effect = [10, Exception("Access denied"), 5]
        mock_seed.side_effect = [
            {"successful": 8, "attempted": 8, "failed": 0},
            {"successful": 8, "attempted": 8, "failed": 0},
        ]

        result = handler({}, mock_lambda_context)

        assert result["statusCode"] == 207
        body = json.loads(result["body"])
        assert "Failed to reset 1 table(s): table2" in body["message"]
        assert body["tables_processed"] == 3
        assert body["tables_succeeded"] == 2
        assert body["tables_failed"] == 1
        assert len(body["results"]) == 3
        assert body["results"][0]["status"] == "success"
        assert body["results"][1]["status"] == "failed"
        assert body["results"][1]["error"] == "Access denied"
        assert body["results"][2]["status"] == "success"


@patch("lambdas.seed_sandbox.index.seed_sandbox_table")
@patch("lambdas.seed_sandbox.index.delete_all_table_items")
def test_complete_failure(mock_delete, mock_seed, mock_lambda_context):
    with patch.dict(
        "os.environ", {"TABLE_NAMES": "table1,table2", "POINTERS_PER_TYPE": "2"}
    ):
        mock_delete.side_effect = Exception("Database error")

        result = handler({}, mock_lambda_context)

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "Failed to reset 2 table(s)" in body["message"]
        assert body["tables_processed"] == 2
        assert body["tables_succeeded"] == 0
        assert body["tables_failed"] == 2


def test_missing_table_names_env_var(mock_lambda_context):
    with patch.dict("os.environ", {}, clear=True):
        result = handler({}, mock_lambda_context)

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert body["error"] == "TABLE_NAMES environment variable is required"


def test_empty_table_names(mock_lambda_context):
    with patch.dict("os.environ", {"TABLE_NAMES": "   ", "POINTERS_PER_TYPE": "2"}):
        result = handler({}, mock_lambda_context)

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert body["error"] == "No valid table names provided in TABLE_NAMES"


@patch("lambdas.seed_sandbox.index.seed_sandbox_table")
@patch("lambdas.seed_sandbox.index.delete_all_table_items")
def test_table_names_with_whitespace(mock_delete, mock_seed, mock_lambda_context):
    with patch.dict(
        "os.environ",
        {"TABLE_NAMES": " table1 , table2 , ", "POINTERS_PER_TYPE": "2"},
    ):
        mock_delete.return_value = 5
        mock_seed.return_value = {"successful": 4, "attempted": 4, "failed": 0}

        result = handler({}, mock_lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["tables_processed"] == 2
        assert body["results"][0]["table_name"] == "table1"
        assert body["results"][1]["table_name"] == "table2"


@patch("lambdas.seed_sandbox.index.seed_sandbox_table")
@patch("lambdas.seed_sandbox.index.delete_all_table_items")
def test_seed_with_failures(mock_delete, mock_seed, mock_lambda_context, mock_env_vars):
    mock_delete.return_value = 5
    mock_seed.return_value = {"successful": 6, "attempted": 8, "failed": 2}

    result = handler({}, mock_lambda_context)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["results"][0]["pointers_created"] == 6
    assert body["results"][0]["pointers_attempted"] == 8
    assert body["results"][0]["pointers_failed"] == 2
