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


@request_handler(body=ProducerRequestParams)
def handler(
    body: ProducerRequestParams,
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
) -> Response:
    """
    Search for document references based on the provided parameters.

    Args:
        body (ProducerRequestParams): The request parameters for the search.
        metadata (ConnectionMetadata): The connection metadata.
        repository (DocumentPointerRepository): The repository for document pointers.

    Returns:
        Response: The response containing the search results.

    Raises:
        OperationOutcomeError: If an error occurs while parsing the document reference.
    """

    logger.log(LogReference.PROPOSTSEARCH000)

    if not body.nhs_number:
        logger.log(
            LogReference.PROPOSTSEARCH001, subject_identifier=body.subject_identifier
        )
        return SpineErrorResponse.INVALID_NHS_NUMBER(
            diagnostics="A valid NHS number is required to search for document references",
            expression="subject:identifier",
        )

    allowed_types = (
        metadata.nrl_permissions_policy.types
        if metadata.nrl_permissions_policy
        else metadata.pointer_types
    )

    if not validate_type(body.type, allowed_types):
        logger.log(
            LogReference.PROPOSTSEARCH002,
            type=body.type,
            pointer_types=allowed_types,
        )
        return SpineErrorResponse.INVALID_CODE_SYSTEM(
            diagnostics="The provided type does not match the allowed types for this organisation",
            expression="type",
        )

    categories = body.category.root.split(",") if body.category else []
    if not validate_category(categories):
        logger.log(
            LogReference.PROPOSTSEARCH002b,
            category=body.category,
        )
        return SpineErrorResponse.INVALID_CODE_SYSTEM(
            diagnostics="The provided category is not valid",
            expression="category",
        )

    pointer_types = [body.type.root] if body.type else allowed_types
    bundle = {"resourceType": "Bundle", "type": "searchset", "total": 0, "entry": []}

    logger.log(
        LogReference.PROPOSTSEARCH003,
        custodian=metadata.ods_code,
        nhs_number=body.nhs_number,
        pointer_types=pointer_types,
        categories=categories,
    )

    for result in repository.search(
        custodian=metadata.ods_code,
        nhs_number=body.nhs_number,
        pointer_types=pointer_types,
        categories=categories,
    ):
        try:
            document_reference = DocumentReference.model_validate_json(result.document)
            bundle["total"] += 1
            bundle["entry"].append(
                {"resource": document_reference.model_dump(exclude_none=True)}
            )
            logger.log(
                LogReference.PROPOSTSEARCH004,
                id=document_reference.id,
                count=bundle["total"],
            )

        except ValidationError as exc:
            logger.log(
                LogReference.PROPOSTSEARCH005, error=str(exc), document=result.document
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

    logger.log(LogReference.PROPOSTSEARCH999)
    return Response.from_resource(Bundle.model_validate(bundle))
