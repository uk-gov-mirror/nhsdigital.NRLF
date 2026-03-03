import sys
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from botocore.exceptions import ClientError
from delete_all_table_items import delete_all_table_items


@patch("delete_all_table_items.boto3")
def test_successful_deletion_single_page(mock_boto3):

    mock_table = MagicMock()
    mock_table.key_schema = [
        {"AttributeName": "id", "KeyType": "HASH"},
    ]
    mock_table.scan.return_value = {
        "Items": [{"id": "item1"}, {"id": "item2"}, {"id": "item3"}],
    }

    mock_resource = MagicMock()
    mock_resource.Table.return_value = mock_table
    mock_boto3.resource.return_value = mock_resource

    result = delete_all_table_items("test-table")

    assert result == 3
    mock_resource.Table.assert_called_once_with("test-table")
    mock_table.scan.assert_called_once()


@patch("delete_all_table_items.boto3")
def test_successful_deletion_multiple_pages(mock_boto3):

    mock_table = MagicMock()
    mock_table.key_schema = [
        {"AttributeName": "id", "KeyType": "HASH"},
    ]

    mock_table.scan.side_effect = [
        {
            "Items": [{"id": f"item{i}"} for i in range(100)],
            "LastEvaluatedKey": {"id": "item99"},
        },
        {
            "Items": [{"id": f"item{i}"} for i in range(100, 150)],
        },
    ]

    mock_resource = MagicMock()
    mock_resource.Table.return_value = mock_table
    mock_boto3.resource.return_value = mock_resource

    result = delete_all_table_items("test-table")

    assert result == 150
    assert mock_table.scan.call_count == 2


@patch("delete_all_table_items.boto3")
def test_successful_deletion_composite_key(mock_boto3):
    """Test deletion with composite key (hash + range)."""

    mock_table = MagicMock()
    mock_table.key_schema = [
        {"AttributeName": "pk", "KeyType": "HASH"},
        {"AttributeName": "sk", "KeyType": "RANGE"},
    ]
    mock_table.scan.return_value = {
        "Items": [
            {"pk": "cust1", "sk": "ptr1"},
            {"pk": "cust1", "sk": "ptr2"},
        ],
    }

    mock_resource = MagicMock()
    mock_resource.Table.return_value = mock_table
    mock_boto3.resource.return_value = mock_resource

    result = delete_all_table_items("test-table")

    assert result == 2
    call_kwargs = mock_table.scan.call_args[1]
    assert "pk,sk" in call_kwargs["ProjectionExpression"]


@patch("delete_all_table_items.boto3")
def test_empty_table(mock_boto3):

    mock_table = MagicMock()
    mock_table.key_schema = [{"AttributeName": "id", "KeyType": "HASH"}]
    mock_table.scan.return_value = {"Items": []}

    mock_resource = MagicMock()
    mock_resource.Table.return_value = mock_table
    mock_boto3.resource.return_value = mock_resource

    result = delete_all_table_items("test-table")

    assert result == 0


@patch("delete_all_table_items.boto3")
@patch("builtins.print")
@patch("sys.exit")
def test_table_not_found(mock_exit, mock_print, mock_boto3):

    mock_exit.side_effect = SystemExit(1)

    mock_table = MagicMock()
    type(mock_table).key_schema = PropertyMock(
        side_effect=ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "Table not found",
                }
            },
            "DescribeTable",
        )
    )

    mock_resource = MagicMock()
    mock_resource.Table.return_value = mock_table
    mock_boto3.resource.return_value = mock_resource

    with pytest.raises(SystemExit):
        delete_all_table_items("nonexistent-table")

    mock_exit.assert_called_once_with(1)
    mock_print.assert_called_with("Error: Table 'nonexistent-table' does not exist")


@patch("delete_all_table_items.boto3")
@patch("builtins.print")
@patch("sys.exit")
def test_access_denied(mock_exit, mock_print, mock_boto3):

    mock_exit.side_effect = SystemExit(1)

    mock_table = MagicMock()
    type(mock_table).key_schema = PropertyMock(
        side_effect=ClientError(
            {
                "Error": {
                    "Code": "AccessDeniedException",
                    "Message": "Access denied",
                }
            },
            "DescribeTable",
        )
    )

    mock_resource = MagicMock()
    mock_resource.Table.return_value = mock_table
    mock_boto3.resource.return_value = mock_resource

    with pytest.raises(SystemExit):
        delete_all_table_items("protected-table")

    mock_exit.assert_called_once_with(1)
    mock_print.assert_called_with(
        "Error: No permission to access table 'protected-table'"
    )


@patch("delete_all_table_items.boto3")
@patch("builtins.print")
def test_throttling_warning(mock_print, mock_boto3):

    mock_table = MagicMock()
    mock_table.key_schema = [{"AttributeName": "id", "KeyType": "HASH"}]

    throttle_count = [0]

    def scan_side_effect(**kwargs):
        if throttle_count[0] == 0:
            throttle_count[0] += 1
            raise ClientError(
                {"Error": {"Code": "ProvisionedThroughputExceededException"}},
                "Scan",
            )
        return {"Items": [{"id": "item1"}]}

    mock_table.scan.side_effect = scan_side_effect

    mock_resource = MagicMock()
    mock_resource.Table.return_value = mock_table
    mock_boto3.resource.return_value = mock_resource

    result = delete_all_table_items("test-table")

    assert result == 1
    warning_calls = [
        call for call in mock_print.call_args_list if "Throttled" in str(call)
    ]
    assert len(warning_calls) > 0


@patch("delete_all_table_items.boto3")
@patch("sys.exit")
def test_unexpected_error(mock_exit, mock_boto3):

    mock_exit.side_effect = SystemExit(1)

    mock_table = MagicMock()
    mock_table.key_schema = [{"AttributeName": "id", "KeyType": "HASH"}]
    mock_table.scan.side_effect = RuntimeError("Unexpected error")

    mock_resource = MagicMock()
    mock_resource.Table.return_value = mock_table
    mock_boto3.resource.return_value = mock_resource

    with pytest.raises(SystemExit):
        delete_all_table_items("test-table")

    mock_exit.assert_called_once_with(1)


@patch("delete_all_table_items.boto3")
@patch("builtins.print")
def test_progress_indicator(mock_print, mock_boto3):

    mock_table = MagicMock()
    mock_table.key_schema = [{"AttributeName": "id", "KeyType": "HASH"}]

    mock_table.scan.side_effect = [
        {
            "Items": [{"id": f"item{i}"} for i in range(100)],
            "LastEvaluatedKey": {"id": "item99"},
        },
        {
            "Items": [{"id": f"item{i}"} for i in range(100, 200)],
            "LastEvaluatedKey": {"id": "item199"},
        },
        {
            "Items": [{"id": f"item{i}"} for i in range(200, 250)],
        },
    ]

    mock_resource = MagicMock()
    mock_resource.Table.return_value = mock_table
    mock_boto3.resource.return_value = mock_resource

    result = delete_all_table_items("test-table")

    assert result == 250

    progress_calls = [
        call
        for call in mock_print.call_args_list
        if "Deleted" in str(call) and "items..." in str(call)
    ]
    assert len(progress_calls) == 2


@patch("delete_all_table_items.boto3")
def test_batch_writer_context_manager(mock_boto3):

    mock_batch_writer = MagicMock()
    mock_table = MagicMock()
    mock_table.key_schema = [{"AttributeName": "id", "KeyType": "HASH"}]
    mock_table.scan.return_value = {
        "Items": [{"id": "item1"}],
    }
    mock_table.batch_writer.return_value.__enter__.return_value = mock_batch_writer

    mock_resource = MagicMock()
    mock_resource.Table.return_value = mock_table
    mock_boto3.resource.return_value = mock_resource

    delete_all_table_items("test-table")

    mock_table.batch_writer.assert_called_once()
    mock_batch_writer.delete_item.assert_called_once_with(Key={"id": "item1"})
