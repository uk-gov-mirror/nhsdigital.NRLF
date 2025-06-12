from pydantic import ValidationError

from nrlf.core.codes import SpineErrorConcept
from nrlf.core.decorators import DocumentPointerRepository, request_handler
from nrlf.core.logger import LogReference, logger
from nrlf.core.model import ConnectionMetadata, ProducerRequestParams
from nrlf.core.response import Response, SpineErrorResponse
from nrlf.core.validators import validate_category, validate_type
from nrlf.producer.fhir.r4.model import (
    Bundle,
    DocumentReference,
    OperationOutcome,
    OperationOutcomeIssue,
)


@request_handler(params=ProducerRequestParams)
def handler(
    metadata: ConnectionMetadata,
    params: ProducerRequestParams,
    repository: DocumentPointerRepository,
) -> Response:
    """
    Search for document references based on the provided parameters.

    Args:
        metadata (ConnectionMetadata): The connection metadata.
        params (ProducerRequestParams): The request parameters.
        repository (DocumentPointerRepository): The document pointer repository.

    Returns:
        Response: The response containing the search results.
    """

    logger.log(LogReference.PROSEARCH000)

    if params.subject_identifier and not params.nhs_number:
        logger.log(
            LogReference.PROSEARCH001, subject_identifier=params.subject_identifier
        )
        return SpineErrorResponse.INVALID_NHS_NUMBER(
            diagnostics="Invalid NHS number provided in the search parameters",
            expression="subject:identifier",
        )

    if not params.nhs_number:
        logger.log(
            LogReference.PROSEARCH001, subject_identifier=params.subject_identifier
        )
        return SpineErrorResponse.INVALID_NHS_NUMBER(
            diagnostics="NHS number is missing from the search parameters",
            expression="subject:identifier",
        )

    if not validate_type(params.type, metadata.pointer_types):
        logger.log(
            LogReference.PROSEARCH002,
            type=params.type,
            pointer_types=metadata.pointer_types,
        )
        return SpineErrorResponse.INVALID_CODE_SYSTEM(
            diagnostics="Invalid query parameter (The provided type does not match the allowed types for this organisation)",
            expression="type",
        )

    categories = params.category.root.split(",") if params.category else []
    if not validate_category(categories):
        logger.log(
            LogReference.PROSEARCH002b,
            category=params.category,
        )  # TODO - Should update error message once permissioning by category is implemented
        return SpineErrorResponse.INVALID_CODE_SYSTEM(
            diagnostics="Invalid query parameter (The provided category is not valid)",
            expression="category",
        )

    pointer_types = [params.type.root] if params.type else metadata.pointer_types
    bundle = {"resourceType": "Bundle", "type": "searchset", "total": 0, "entry": []}

    logger.log(
        LogReference.PROSEARCH003,
        custodian=metadata.ods_code,
        custodian_suffix=metadata.ods_code_extension,
        nhs_number=params.nhs_number,
        pointer_types=pointer_types,
        categories=params.category.root.split(",") if params.category else [],
    )

    if params.field_summary and params.field_summary.root == "count":
        logger.log(LogReference.PROSEARCH006)
        bundle = {"resourceType": "Bundle", "type": "searchset", "total": 0}
        total = sum(
            1
            for _ in repository.search(
                custodian=metadata.ods_code,
                custodian_suffix=metadata.ods_code_extension,
                nhs_number=params.nhs_number,
                pointer_types=pointer_types,
                categories=categories,
            )
        )
        bundle["total"] = total
        response = Response.from_resource(Bundle.model_validate(bundle))
        logger.log(LogReference.PROSEARCH999)
        return response

    for result in repository.search(
        custodian=metadata.ods_code,
        custodian_suffix=metadata.ods_code_extension,
        nhs_number=params.nhs_number,
        pointer_types=pointer_types,
        categories=params.category.root.split(",") if params.category else [],
    ):
        try:
            document_reference = DocumentReference.model_validate_json(result.document)
            bundle["total"] += 1
            bundle["entry"].append(
                {"resource": document_reference.model_dump(exclude_none=True)}
            )
            logger.log(
                LogReference.PROSEARCH004,
                id=document_reference.id,
                count=bundle["total"],
            )

        except ValidationError as exc:
            logger.log(
                LogReference.PROSEARCH005, error=str(exc), document=result.document
            )
            operation_outcome = OperationOutcome(
                resourceType="OperationOutcome",
                issue=[
                    OperationOutcomeIssue(
                        severity="error",
                        code="exception",
                        details=SpineErrorConcept.from_code("INTERNAL_SERVER_ERROR"),
                        diagnostics="An error occurred whilst parsing the document reference search results",
                    )
                ],
            )
            bundle["total"] += 1
            bundle["entry"].append(
                {"resource": operation_outcome.model_dump(exclude_none=True)}
            )

    response = Response.from_resource(Bundle.model_validate(bundle))
    logger.log(LogReference.PROSEARCH999)
    return response
