from nrlf.core.codes import SpineErrorConcept
from nrlf.core.constants import (
    PERMISSION_AUDIT_DATES_FROM_PAYLOAD,
    PERMISSION_SUPERSEDE_IGNORE_DELETE_FAIL,
    TYPES_WITH_MULTIPLES,
)
from nrlf.core.decorators import request_handler
from nrlf.core.dynamodb.repository import DocumentPointer, DocumentPointerRepository
from nrlf.core.errors import OperationOutcomeError
from nrlf.core.logger import LogReference, logger
from nrlf.core.model import ConnectionMetadata
from nrlf.core.response import NRLResponse, Response, SpineErrorResponse
from nrlf.core.utils import create_fhir_instant
from nrlf.core.validators import DocumentReferenceValidator
from nrlf.producer.fhir.r4.model import DocumentReference, Meta


def _set_upsert_time_fields(
    upsert_time: str, document_reference: DocumentReference, nrl_permissions: list[str]
) -> DocumentReference:
    """
    Set the date and lastUpdated timestamps on the provided DocumentReference
    """
    if not document_reference.meta:
        document_reference.meta = Meta()
    document_reference.meta.lastUpdated = upsert_time

    if (
        document_reference.date
        and PERMISSION_AUDIT_DATES_FROM_PAYLOAD in nrl_permissions
    ):
        # Perserving the original date if it exists and the permission is set
        logger.log(
            LogReference.PROUPSERT011,
            id=document_reference.id,
            date=document_reference.date,
        )
    else:
        document_reference.date = upsert_time

    return document_reference


def _create_core_model(resource: DocumentReference, metadata: ConnectionMetadata):
    """
    Create the DocumentPointer model from the provided DocumentReference
    """
    creation_time = create_fhir_instant()
    document_reference = _set_upsert_time_fields(
        creation_time,
        document_reference=resource,
        nrl_permissions=metadata.nrl_permissions,
    )

    return DocumentPointer.from_document_reference(
        document_reference, created_on=creation_time
    )


def _check_permissions(
    core_model: DocumentPointer, metadata: ConnectionMetadata
) -> Response | None:
    """
    Check the requester has permissions to create the DocumentReference
    """
    if metadata.ods_code != core_model.custodian:
        logger.log(
            LogReference.PROUPSERT004,
            ods_code=metadata.ods_code,
            custodian=core_model.custodian,
        )
        return SpineErrorResponse.UNPROCESSABLE_ENTITY(
            diagnostics="The custodian of the provided DocumentReference does not match the expected ODS code for this organisation",
            expression="custodian.identifier.value",
        )

    allowed_types = (
        metadata.nrl_permissions_policy.types
        if metadata.nrl_permissions_policy
        else metadata.pointer_types
    )

    if core_model.type not in allowed_types:
        logger.log(
            LogReference.PROUPSERT005,
            ods_code=metadata.ods_code,
            type=core_model.type,
            pointer_types=allowed_types,
        )
        return SpineErrorResponse.AUTHOR_CREDENTIALS_ERROR(
            diagnostics="The type of the provided DocumentReference is not in the list of allowed types for this organisation",
            expression="type.coding[0].code",
        )


def _get_document_ids_to_supersede(
    resource: DocumentReference,
    core_model: DocumentPointer,
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
    can_ignore_delete_fail: bool,
):
    """
    Get the list of document IDs to supersede based on the relatesTo field
    """
    if not resource.relatesTo:
        return []

    logger.log(LogReference.PROUPSERT006, relatesTo=resource.relatesTo)
    ids_to_delete = []

    for idx, relates_to in enumerate(resource.relatesTo):
        identifier = _validate_identifier(relates_to, idx)
        _validate_producer_id(identifier, metadata, idx)
        if can_ignore_delete_fail:
            logger.log(
                LogReference.PROUPSERT006a,
                pointer_id=resource.id,
                relatesTo=resource.relatesTo,
            )
        else:
            existing_pointer = _check_existing_pointer(identifier, repository, idx)
            _validate_pointer_details(existing_pointer, core_model, identifier, idx)

        _append_id_if_replaces(relates_to, ids_to_delete, identifier)

    return ids_to_delete


def _validate_identifier(relates_to, idx):
    """
    Validate that there is a identifier in relatesTo target
    """
    identifier = getattr(relates_to.target.identifier, "value", None)
    if not identifier:
        logger.log(LogReference.PROUPSERT007a)
        _raise_operation_outcome_error(
            "No identifier value provided for relatesTo target", idx
        )
    return identifier


def _validate_producer_id(identifier, metadata, idx):
    """
    Validate that there is an ODS code in the relatesTo target identifier
    """
    producer_id = identifier.split("-", 1)[0]
    if metadata.ods_code != producer_id:
        logger.log(
            LogReference.PROUPSERT007b,
            related_identifier=identifier,
            ods_code=metadata.ods_code,
        )
        _raise_operation_outcome_error(
            "The relatesTo target identifier value does not include the expected ODS code for this organisation",
            idx,
        )


def _check_existing_pointer(identifier, repository, idx):
    """
    Check that there is an existing pointer that will be deleted when superseding
    """
    existing_pointer = repository.get_by_id(identifier)
    if not existing_pointer:
        logger.log(LogReference.PROUPSERT007c, related_identifier=identifier)
        _raise_operation_outcome_error(
            "The relatesTo target document does not exist", idx
        )
    return existing_pointer


def _validate_pointer_details(existing_pointer, core_model, identifier, idx):
    """
    Validate that the nhs numbers and type matches between the existing pointer and the requested one.
    """
    if existing_pointer.nhs_number != core_model.nhs_number:
        logger.log(LogReference.PROUPSERT007d, related_identifier=identifier)
        _raise_operation_outcome_error(
            "The relatesTo target document NHS number does not match the NHS number in the request",
            idx,
        )

    if existing_pointer.type != core_model.type:
        logger.log(LogReference.PROUPSERT007e, related_identifier=identifier)
        _raise_operation_outcome_error(
            "The relatesTo target document type does not match the type in the request",
            idx,
        )


def _append_id_if_replaces(relates_to, ids_to_delete, identifier):
    """
    Append pointer ID if the if the relatesTo code is 'replaces'
    """
    if relates_to.code == "replaces":
        logger.log(
            LogReference.PROUPSERT008,
            relates_to_code=relates_to.code,
            identifier=identifier,
        )
        ids_to_delete.append(identifier)


def _raise_operation_outcome_error(diagnostics, idx):
    """
    General function to raise an operation outcome error
    """
    raise OperationOutcomeError(
        severity="error",
        code="business-rule",
        details=SpineErrorConcept.from_code("UNPROCESSABLE_ENTITY"),
        diagnostics=diagnostics,
        expression=[f"relatesTo[{idx}].target.identifier.value"],
        status_code="422",
    )


@request_handler(body=DocumentReference)
def handler(
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
    body: DocumentReference,
) -> Response:
    """
    Entrypoint for the upsertDocumentReference function
    """
    logger.log(LogReference.PROUPSERT000)

    logger.log(LogReference.PROUPSERT001, resource=body)
    validator = DocumentReferenceValidator()
    result = validator.validate(body)

    if not result.is_valid:
        logger.log(LogReference.PROUPSERT002)
        return Response.from_issues(issues=result.issues, statusCode="422")

    core_model = _create_core_model(result.resource, metadata)

    if metadata.ods_code != core_model.producer_id:
        logger.log(
            LogReference.PROUPSERT003,
            ods_code=metadata.ods_code,
            producer_id=core_model.producer_id,
        )
        return SpineErrorResponse.UNPROCESSABLE_ENTITY(
            diagnostics="The id of the provided DocumentReference does not include the expected ODS code for this organisation"
        )

    if error_response := _check_permissions(core_model, metadata):
        return error_response

    can_ignore_delete_fail = (
        PERMISSION_SUPERSEDE_IGNORE_DELETE_FAIL in metadata.nrl_permissions
    )

    if ids_to_delete := _get_document_ids_to_supersede(
        result.resource, core_model, metadata, repository, can_ignore_delete_fail
    ):
        logger.log(
            LogReference.PROUPSERT010,
            pointer_id=result.resource.id,
            ids_to_delete=ids_to_delete,
            can_ignore_delete_fail=can_ignore_delete_fail,
        )
        saved_model = repository.supersede(
            core_model, ids_to_delete, can_ignore_delete_fail
        )
        logger.log(LogReference.PROUPSERT999)
        return NRLResponse.RESOURCE_SUPERSEDED(resource_id=saved_model.id)

    pointer_type = core_model.type
    if pointer_type not in TYPES_WITH_MULTIPLES:
        nhs_number = core_model.nhs_number
        existing_pointers_count = repository.count_by_nhs_number(
            nhs_number, [pointer_type]
        )

        if existing_pointers_count > 0 and not nhs_number.startswith("9"):
            logger.log(
                LogReference.PROUPSERT012,
                new_pointer_id=core_model.id,
                new_pointer_master_id=core_model.master_identifier,
                pointer_type=pointer_type,
                nhs_number=nhs_number,
                custodian=core_model.custodian,
                existing_pointers_count=existing_pointers_count,
            )

    logger.log(LogReference.PROUPSERT009, pointer_id=result.resource.id)
    saved_model = repository.create(core_model)
    logger.log(LogReference.PROUPSERT999)
    return NRLResponse.RESOURCE_CREATED(resource_id=saved_model.id)
