import io
import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from migrate_v1_perms_by_app import (
    CONSUMER_OR_PRODUCER,
    _read_and_transform,
    migrate_v1_perms_by_app,
)

ENV = "dev"
FOLDER = "my-app-folder"
BUCKET = f"nhsd-nrlf--{ENV}-authorization-store"

SAMPLE_V1_PERMS = [
    "http://snomed.info/sct|736253002",
    "http://snomed.info/sct|1363501000000100",
    "http://snomed.info/sct|736366004",
]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _make_client_error(code: str, message: str) -> ClientError:
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        operation_name="S3Operation",
    )


def _mock_s3_client_with_response(data_to_return: bytes) -> MagicMock:
    s3 = MagicMock()
    s3.get_object.return_value = {"Body": io.BytesIO(data_to_return)}
    return s3


# ---------------------------------------------------------------------------
# Unit tests for _read_and_transform
# ---------------------------------------------------------------------------

FILE_PATH = f"{FOLDER}/perms.json"


def test_read_and_transform_returns_wrapped_json_and_count():
    s3 = _mock_s3_client_with_response(json.dumps(SAMPLE_V1_PERMS).encode())

    body, count = _read_and_transform(s3, BUCKET, FILE_PATH)

    assert count == len(SAMPLE_V1_PERMS)
    assert json.loads(body) == {"types": SAMPLE_V1_PERMS}
    s3.get_object.assert_called_once_with(Bucket=BUCKET, Key=FILE_PATH)


def test_read_and_transform_empty_list():
    s3 = _mock_s3_client_with_response(b"[]")

    body, count = _read_and_transform(s3, BUCKET, FILE_PATH)

    assert count == 0
    assert json.loads(body) == {"types": []}


def test_read_and_transform_raises_value_error_for_non_list():
    s3 = _mock_s3_client_with_response(b'{"key": "value"}')

    with pytest.raises(ValueError, match="Expected a JSON array, got dict"):
        _read_and_transform(s3, BUCKET, FILE_PATH)


def test_read_and_transform_raises_runtime_error_on_client_error():
    s3 = MagicMock()
    s3.get_object.side_effect = _make_client_error(
        "NoSuchKey", "The specified key does not exist"
    )

    with pytest.raises(
        RuntimeError,
        match=f"Failed to read s3://{BUCKET}/{FILE_PATH}.*The specified key does not exist",
    ):
        _read_and_transform(s3, BUCKET, FILE_PATH)


# ---------------------------------------------------------------------------
# Unit tests for migrate_v1_perms_by_app
# ---------------------------------------------------------------------------

MODULE = "migrate_v1_perms_by_app"

TRANSFORMED_BODY = '{"types": ["http://snomed.info/sct|736253002"]}'
ENTRY_COUNT = 1


@patch(f"{MODULE}._write_v2_consumer_and_producer_files")
@patch(f"{MODULE}._read_and_transform")
@patch(f"{MODULE}._list_json_files")
@patch(f"{MODULE}._get_s3_client")
@patch(f"{MODULE}._get_bucket_name")
def test_migrate_processes_each_file(
    mock_bucket, mock_s3, mock_list, mock_transform, mock_write
):
    mock_bucket.return_value = BUCKET
    s3 = MagicMock()
    mock_s3.return_value = s3
    mock_list.return_value = [f"{FOLDER}/a.json", f"{FOLDER}/b.json"]
    mock_transform.return_value = (TRANSFORMED_BODY, ENTRY_COUNT)

    migrate_v1_perms_by_app(ENV, FOLDER)

    mock_bucket.assert_called_once_with(ENV)
    mock_s3.assert_called_once_with(ENV)
    mock_list.assert_called_once_with(s3, BUCKET, FOLDER)
    assert mock_transform.call_count == 2
    assert mock_write.call_count == 2
    mock_write.assert_any_call(
        s3, BUCKET, f"{FOLDER}/a.json", TRANSFORMED_BODY, ENTRY_COUNT
    )
    mock_write.assert_any_call(
        s3, BUCKET, f"{FOLDER}/b.json", TRANSFORMED_BODY, ENTRY_COUNT
    )


@patch(f"{MODULE}._write_v2_consumer_and_producer_files")
@patch(f"{MODULE}._read_and_transform")
@patch(f"{MODULE}._list_json_files")
@patch(f"{MODULE}._get_s3_client")
@patch(f"{MODULE}._get_bucket_name")
def test_migrate_no_files_skips_transform_and_write(
    mock_bucket, mock_s3, mock_list, mock_transform, mock_write
):
    mock_bucket.return_value = BUCKET
    mock_s3.return_value = MagicMock()
    mock_list.return_value = []

    migrate_v1_perms_by_app(ENV, FOLDER)

    mock_transform.assert_not_called()
    mock_write.assert_not_called()
