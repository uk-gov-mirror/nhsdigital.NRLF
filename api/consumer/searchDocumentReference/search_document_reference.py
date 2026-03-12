from pydantic import ValidationError

from nrlf.consumer.fhir.r4.model import (
    Bundle,
    DocumentReference,
    OperationOutcome,
    OperationOutcomeIssue,
)
from nrlf.core.codes import SpineErrorConcept
from nrlf.core.config import Config
from nrlf.core.decorators import request_handler
from nrlf.core.dynamodb.repository import DocumentPointerRepository
from nrlf.core.logger import LogReference, logger
from nrlf.core.model import ConnectionMetadata, ConsumerRequestParams
from nrlf.core.response import Response, SpineErrorResponse
from nrlf.core.validators import validate_category, validate_type


@request_handler(params=ConsumerRequestParams)
def handler(
    metadata: ConnectionMetadata,
    params: ConsumerRequestParams,
    repository: DocumentPointerRepository,
) -> Response:
    """
    Searches for document references based on the provided parameters.

    Args:
        metadata (ConnectionMetadata): The connection metadata.
        params (ConsumerRequestParams): The consumer request parameters.
        repository (DocumentPointerRepository): The document pointer repository.

    Returns:
        Response: The response containing the search results.

    Raises:
        OperationOutcomeError: If an error occurs while parsing the document reference.
    """
    logger.log(LogReference.CONSEARCH000)

    if not params.nhs_number:
        logger.log(
            LogReference.CONSEARCH001, subject_identifier=params.subject_identifier
        )
        return SpineErrorResponse.INVALID_NHS_NUMBER(
            diagnostics="A valid NHS number is required to search for document references",
            expression="subject:identifier",
        )
    config = Config()
    base_url = f"https://{config.ENVIRONMENT}.api.service.nhs.uk/"
    self_link = f"{base_url}record-locator/consumer/FHIR/R4/DocumentReference?subject:identifier=https://fhir.nhs.uk/Id/nhs-number|{params.nhs_number}"

    allowed_types = (
        metadata.nrl_permissions_policy.types
        if metadata.nrl_permissions_policy
        else metadata.pointer_types
    )

    if not validate_type(params.type, allowed_types):
        logger.log(
            LogReference.CONSEARCH002,
            type=params.type,
            pointer_types=allowed_types,
        )
        return SpineErrorResponse.INVALID_CODE_SYSTEM(
            diagnostics="Invalid query parameter (The provided type does not match the allowed types for this organisation)",
            expression="type",
        )

    categories = params.category.root.split(",") if params.category else []
    if not validate_category(categories):
        logger.log(
            LogReference.CONSEARCH002b,
            category=params.category,
        )
        return SpineErrorResponse.INVALID_CODE_SYSTEM(
            diagnostics="Invalid query parameter (The provided category is not valid)",
            expression="category",
        )

    custodian_id = (
        params.custodian_identifier.root.split("|", maxsplit=1)[1]
        if params.custodian_identifier
        else None
    )
    if custodian_id:
        self_link += f"&custodian:identifier=https://fhir.nhs.uk/Id/ods-organization-code|{custodian_id}"

    pointer_types = [params.type.root] if params.type else allowed_types
    if params.type:
        self_link += f"&type={params.type.root}"

    if params.category:
        self_link += f"&category={params.category.root}"

    if params.field_summary:
        self_link += f"&_summary={params.field_summary.root}"

    bundle = {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [{"relation": "self", "url": self_link}],
        "total": 0,
        "entry": [],
    }

    logger.log(
        LogReference.CONSEARCH003,
        nhs_number=params.nhs_number,
        custodian=custodian_id,
        pointer_types=pointer_types,
    )

    if params.field_summary and params.field_summary.root == "count":
        bundle = {
            "resourceType": "Bundle",
            "type": "searchset",
            "link": [{"relation": "self", "url": self_link}],
            "total": 0,
        }
        logger.log(LogReference.CONSEARCH006)

        total = repository.count_by_nhs_number(
            nhs_number=params.nhs_number,
            pointer_types=pointer_types,
        )
        bundle["total"] = total
        logger.log(LogReference.CONSEARCH007, total=total)
        response = Response.from_resource(Bundle.model_validate(bundle))
        logger.log(LogReference.CONSEARCH999)
        return response

    for result in repository.search(
        nhs_number=params.nhs_number,
        custodian=custodian_id,
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
                LogReference.CONSEARCH004,
                id=document_reference.id,
                count=bundle["total"],
            )

        except ValidationError as exc:
            logger.log(
                LogReference.CONSEARCH005, error=str(exc), document=result.document
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
    logger.log(LogReference.CONSEARCH999)

    return response
