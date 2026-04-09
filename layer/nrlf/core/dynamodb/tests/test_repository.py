from unittest.mock import patch

import pytest
from moto import mock_aws

from nrlf.core.constants import PointerTypes
from nrlf.core.dynamodb.model import DocumentPointer
from nrlf.core.dynamodb.repository import (
    DocumentPointerRepository,
    _get_sk_ids_for_type,
)
from nrlf.core.log_references import LogReference
from nrlf.tests.data import load_document_reference
from nrlf.tests.dynamodb import mock_repository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_document_pointer(id: str = "Y05868-99999-99999-999999") -> DocumentPointer:
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.id = id
    return DocumentPointer.from_document_reference(doc_ref)


# ---------------------------------------------------------------------------
# _get_sk_ids_for_type
# ---------------------------------------------------------------------------


def test_get_sk_ids_for_type_exception_thrown_for_invalid_type():
    with pytest.raises(ValueError) as error:
        _get_sk_ids_for_type("invalid_type")

    assert str(error.value) == "Cannot find category for pointer type: invalid_type"


def test_get_sk_ids_for_type_returns_type_and_category_for_every_type():
    for each in PointerTypes.list():
        category, pointer_type = _get_sk_ids_for_type(each)
        assert category and pointer_type


def test_get_sk_ids_for_type_exception_thrown_if_new_type_has_no_category():
    pointer_types = PointerTypes.list()
    pointer_types.append("some_pointer_type")
    with pytest.raises(ValueError) as error:
        for each in pointer_types:
            category, pointer_type = _get_sk_ids_for_type(each)
            assert category and pointer_type

    assert (
        str(error.value) == "Cannot find category for pointer type: some_pointer_type"
    )


# ---------------------------------------------------------------------------
# DocumentPointerRepository.supersede
# ---------------------------------------------------------------------------


@mock_aws
@mock_repository
def test_supersede_creates_new_and_deletes_old(repository: DocumentPointerRepository):
    old_doc = make_document_pointer(id="Y05868-OLD0001")
    repository.create(old_doc)
    assert repository.get_by_id("Y05868-OLD0001") is not None

    new_doc = make_document_pointer(id="Y05868-NEW0001")
    result = repository.supersede(new_doc, ids_to_delete=["Y05868-OLD0001"])

    assert result.id == "Y05868-NEW0001"
    assert repository.get_by_id("Y05868-NEW0001") is not None
    assert repository.get_by_id("Y05868-OLD0001") is None


@mock_aws
@mock_repository
@patch("nrlf.core.dynamodb.repository.logger")
def test_supersede_with_can_ignore_delete_fail(
    mock_logger,
    repository: DocumentPointerRepository,
):
    new_doc = make_document_pointer(id="Y05868-NEW0003")

    with patch.object(
        repository.table,
        "delete_item",
        side_effect=Exception("simulated delete failure"),
    ):
        result = repository.supersede(
            new_doc,
            ids_to_delete=["Y05868-NONEXISTENT"],
            can_ignore_delete_fail=True,
        )

    assert result.id == "Y05868-NEW0003"
    log_codes = [c.args[0] for c in mock_logger.log.call_args_list]
    assert LogReference.REPOSITORY026a in log_codes


# ---------------------------------------------------------------------------
# DocumentPointerRepository.delete_by_id
# ---------------------------------------------------------------------------


@mock_aws
@mock_repository
def test_delete_by_id_removes_document_pointer(repository: DocumentPointerRepository):
    doc = make_document_pointer()
    repository.create(doc)
    assert repository.get_by_id(doc.id) is not None

    repository.delete_by_id(doc.id)

    assert repository.get_by_id(doc.id) is None


@pytest.mark.parametrize(
    "ignore_delete_fail, log_reference",
    [(True, LogReference.REPOSITORY026a), (False, LogReference.REPOSITORY026b)],
)
@mock_aws
@mock_repository
@patch("nrlf.core.dynamodb.repository.logger")
def test_delete_by_id_logs_correct_reference_based_on_can_ignore_delete_fail(
    mock_logger,
    repository: DocumentPointerRepository,
    ignore_delete_fail,
    log_reference,
):
    with patch.object(
        repository.table,
        "delete_item",
        side_effect=Exception("simulated delete failure"),
    ):
        repository.delete_by_id(
            "Y05868-NONEXISTENT", can_ignore_delete_fail=ignore_delete_fail
        )

    log_codes = [c.args[0] for c in mock_logger.log.call_args_list]
    assert log_reference in log_codes
