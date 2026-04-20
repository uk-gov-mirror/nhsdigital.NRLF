import json

from behave import *  # noqa
from behave.runner import Context

from tests.features.utils.api_client import (
    consumer_client_from_context,
    producer_client_from_context,
)
from tests.features.utils.data import (
    create_test_document_reference,
    create_test_document_reference_with_defaults,
)


@when("consumer '{ods_code}' counts DocumentReferences with parameters")
def consumer_count_document_references_step(context: Context, ods_code: str):
    client = consumer_client_from_context(context, ods_code)

    if not context.table:
        raise ValueError("No count query table provided")

    items = {row["parameter"]: row["value"] for row in context.table}
    context.response = client.count(items)


@when("consumer '{ods_code}' searches for DocumentReferences with parameters")
def consumer_search_document_reference_step(context: Context, ods_code: str):
    client = consumer_client_from_context(context, ods_code)

    if not context.table:
        raise ValueError("No search query table provided")

    items = {row["parameter"]: row["value"] for row in context.table}

    subject = items.pop("subject", None)
    custodian = items.pop("custodian", None)
    pointer_type = items.pop("pointer_type", None)

    context.response = client.search(
        nhs_number=subject,
        custodian=custodian,
        pointer_type=pointer_type,
        extra_params=items,
    )


@when(
    "consumer '{ods_code}' searches for DocumentReferences using POST with request body"
)
def consumer_search_post_document_reference_step(context: Context, ods_code: str):
    client = consumer_client_from_context(context, ods_code)

    if not context.table:
        raise ValueError("No search query table provided")

    items = {row["key"]: row["value"] for row in context.table}

    subject = items.pop("subject", None)
    custodian = items.pop("custodian", None)
    pointer_type = items.pop("pointer_type", None)

    context.response = client.search_post(
        nhs_number=subject,
        custodian=custodian,
        pointer_type=pointer_type,
        extra_fields=items,
    )


@when("consumer '{ods_code}' reads a DocumentReference with ID '{doc_ref_id}'")
def consumer_read_document_reference_step(
    context: Context, ods_code: str, doc_ref_id: str
):
    client = consumer_client_from_context(context, ods_code)
    context.response = client.read(doc_ref_id)


@when("producer '{ods_code}' creates a DocumentReference with values")
def create_post_document_reference_step(context: Context, ods_code: str):
    client = producer_client_from_context(context, ods_code)

    if not context.table:
        raise ValueError("No document reference data table provided")

    items = {row["property"]: row["value"] for row in context.table}

    doc_ref = create_test_document_reference(items)
    context.response = client.create(doc_ref.model_dump(exclude_none=True))

    if context.response.status_code == 201:
        doc_ref_id = context.response.headers["Location"].split("/")[-1]
        doc_ref_id = doc_ref_id.replace(
            "|", "."
        )  # NRL-766 define and resolve custodian suffix behaviour
        context.add_cleanup(lambda id=doc_ref_id: context.repository.delete_by_id(id))


def _create_or_upsert_body_step(
    context: Context,
    method: str,
    section: str,
    pointer_id: str = "TSTCUS-sample-id-00000",
):
    client = producer_client_from_context(context, "TSTCUS")

    if not context.text:
        raise ValueError("No document reference text snippet provided")

    doc_ref = create_test_document_reference_with_defaults(
        section, context.text, pointer_id
    )
    context.response = getattr(client, method)(doc_ref)

    if context.response.status_code == 201:
        doc_ref_id = context.response.headers["Location"].split("/")[-1]
        doc_ref_id = doc_ref_id.replace(
            "|", "."
        )  # NRL-766 define and resolve custodian suffix behaviour
        context.add_cleanup(lambda id=doc_ref_id: context.repository.delete_by_id(id))


@when(
    "producer 'TSTCUS' requests creation of a DocumentReference with default test values except '{section}' is"
)
def create_post_body_step(context: Context, section: str):
    _create_or_upsert_body_step(context, "create_text", section)


@when(
    "producer 'TSTCUS' requests upsert of a DocumentReference with pointerId '{pointer_id}' and default test values except '{section}' is"
)
def upsert_post_body_step(context: Context, section: str, pointer_id: str):
    _create_or_upsert_body_step(context, "upsert_text", section, pointer_id)


@when(
    "producer 'TSTCUS' requests update of a DocumentReference with pointerId '{pointer_id}' but replacing '{section}'"
)
def update_post_body_step(context: Context, section: str, pointer_id: str):
    """This can only update top level fields"""
    consumer_client = consumer_client_from_context(context, "TSTCUS")
    context.response = consumer_client.read(pointer_id)

    if context.response.status_code != 200:
        raise ValueError(f"Failed to read existing pointer: {context.response.text}")

    doc_ref = context.response.json()
    doc_ref[section] = "placeholder"
    doc_ref_text = json.dumps(doc_ref)
    doc_ref_text = doc_ref_text.replace('"placeholder"', context.text)

    producer_client = producer_client_from_context(context, "TSTCUS")
    context.response = producer_client.update_text(doc_ref_text, pointer_id)


@when(
    "producer 'TSTCUS' requests update of a DocumentReference with pointerId '{pointer_id}' and only changing"
)
def update_post_body_step(context: Context, pointer_id: str):
    """
    Updates an existing DocumentReference with new values for a specific section
    """
    consumer_client = consumer_client_from_context(context, "TSTCUS")
    context.response = consumer_client.read(pointer_id)

    if context.response.status_code != 200:
        raise ValueError(f"Failed to read existing pointer: {context.response.text}")

    doc_ref = context.response.json()
    custom_data = json.loads(context.text)
    for key in custom_data:
        doc_ref[key] = custom_data[key]

    producer_client = producer_client_from_context(context, "TSTCUS")
    context.response = producer_client.update(doc_ref, pointer_id)


@when("producer '{ods_code}' upserts a DocumentReference with values")
def create_put_document_reference_step(context: Context, ods_code: str):
    client = producer_client_from_context(context, ods_code)

    if not context.table:
        raise ValueError("No document reference data table provided")

    items = {row["property"]: row["value"] for row in context.table}

    doc_ref = create_test_document_reference(items)
    doc_ref_id = items.get("id")
    context.response = client.upsert(doc_ref.model_dump(exclude_none=True))

    if context.response.status_code == 201:
        context.add_cleanup(lambda id=doc_ref_id: context.repository.delete_by_id(id))


@when("producer '{ods_code}' updates a DocumentReference '{doc_ref_id}' with values")
def update_put_document_reference_step(
    context: Context, ods_code: str, doc_ref_id: str
):
    client = producer_client_from_context(context, ods_code)

    if not context.table:
        raise ValueError("No document reference data table provided")

    items = {row["property"]: row["value"] for row in context.table}

    doc_ref = client.read(doc_ref_id).json()
    for key, value in items.items():
        doc_ref.update({key: value})

    context.response = client.update(doc_ref, doc_ref_id)

    if context.response.status_code == 200:
        context.add_cleanup(lambda id=doc_ref_id: context.repository.delete_by_id(id))


@when(
    "producer '{ods_code}' requests to delete DocumentReference with id '{doc_ref_id}'"
)
def delete_document_reference_step(context: Context, ods_code: str, doc_ref_id: str):
    client = producer_client_from_context(context, ods_code)
    context.response = client.delete(doc_ref_id)


@when("producer '{ods_code}' reads a DocumentReference with ID '{doc_ref_id}'")
def producer_read_document_reference_step(
    context: Context, ods_code: str, doc_ref_id: str
):
    client = producer_client_from_context(context, ods_code)
    context.response = client.read(doc_ref_id)


@when("producer '{ods_code}' searches for DocumentReferences with parameters")
def producer_search_document_reference_step(context: Context, ods_code: str):
    client = producer_client_from_context(context, ods_code)

    if not context.table:
        raise ValueError("No search query table provided")

    items = {row["parameter"]: row["value"] for row in context.table}

    subject = items.pop("subject", None)
    pointer_type = items.pop("pointer_type", None)

    context.response = client.search(
        nhs_number=subject,
        pointer_type=pointer_type,
        extra_params=items,
    )


@when(
    "{consumer_or_producer} '{ods_code}' sends HEAD request to '{endpoint}' endpoint with headers"
)
def consumer_head_request_step(
    context: Context, consumer_or_producer: str, ods_code: str, endpoint: str
):
    if not context.table:
        raise ValueError("No headers table provided")

    headers = {row["header"]: row["value"] for row in context.table}

    if consumer_or_producer == "producer":
        client = producer_client_from_context(context, ods_code)
    elif consumer_or_producer == "consumer":
        client = consumer_client_from_context(context, ods_code)
    context.response = client.head(endpoint, headers=headers)
