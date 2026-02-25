import json
from typing import Dict, Type

from pydantic import BaseModel, ValidationError

from nrlf.core.codes import SpineErrorConcept
from nrlf.core.constants import CLIENT_RP_DETAILS, CONNECTION_METADATA
from nrlf.core.errors import OperationOutcomeError, ParseError
from nrlf.core.json_duplicate_checker import check_duplicate_keys
from nrlf.core.logger import LogReference, logger
from nrlf.core.model import ClientRpDetails, ConnectionMetadata


# from consumer proxy code - producer has extra bits
def _fetch_ods_app_id_headers(headers: dict[str, str]):
    ods_code = headers.get("nhsd-end-user-organisation-ods")

    if not ods_code or len(ods_code.strip()) == 0:
        logger.log(LogReference.HANDLER003a, headers_names=headers.keys())
        return

    # where should this come from now? soln: https://nhsd-confluence.digital.nhs.uk/spaces/clp/pages/1288189142/nrlf+access+permission+model#nrlf_access_permission_model-proposed_approach
    nrl_app_id = headers.get("nhsd-nrl-app-id")
    if not nrl_app_id or len(nrl_app_id.strip()) == 0:
        logger.log(LogReference.HANDLER003b, headers_names=headers.keys())
        return

    return ods_code, nrl_app_id


def parse_headers(
    headers: Dict[str, str], use_new_permissions=False
) -> ConnectionMetadata:
    """
    Parses the connection metadata and client rp details from the headers passed from Apigee
    """
    case_insensitive_headers = {key.lower(): value for key, value in headers.items()}

    try:
        raw_client_rp_details = json.loads(
            case_insensitive_headers.get(CLIENT_RP_DETAILS, "{}")
        )
        raw_connection_metadata = json.loads(
            case_insensitive_headers.get(CONNECTION_METADATA, "{}")
        )

        if use_new_permissions:
            # top up new perms to pass validation? feels bad? or no?
            ods_code, nrl_app_id = _fetch_ods_app_id_headers(headers)
            raw_connection_metadata["nrl.ods-code"] = ods_code
            raw_connection_metadata["nrl.app-id"] = nrl_app_id
            raw_client_rp_details["developer.app.id"] = nrl_app_id
            raw_client_rp_details["developer.app.name"] = nrl_app_id

        client_rp_details = ClientRpDetails.model_validate(raw_client_rp_details)
        return ConnectionMetadata.model_validate(
            {**raw_connection_metadata, "client_rp_details": client_rp_details}
        )

    except (ValidationError, json.JSONDecodeError):
        raise OperationOutcomeError(
            status_code="401",
            severity="error",
            code="invalid",
            details=SpineErrorConcept.from_code("MISSING_OR_INVALID_HEADER"),
            diagnostics=(
                "Unable to parse metadata about the requesting application. "
                "Contact the onboarding team."
            ),
        ) from None


def parse_params(
    model: Type[BaseModel] | None,
    query_string_params: Dict[str, str] | None,
) -> BaseModel | None:
    if not model:
        return None

    logger.log(
        LogReference.HANDLER006,
        params=query_string_params,
        model=model.__name__,
    )

    try:
        result = model.model_validate(query_string_params or {})
        logger.log(LogReference.HANDLER007, parsed_params=result.model_dump())
        return result

    except ValidationError as exc:
        raise ParseError.from_validation_error(
            exc,
            details=SpineErrorConcept.from_code("INVALID_PARAMETER"),
            msg="Invalid query parameter",
        ) from None


def parse_body(
    model: Type[BaseModel] | None,
    body: str | None,
) -> BaseModel | None:
    if not model:
        return None

    logger.log(LogReference.HANDLER008, body=body, model=model.__name__)

    if not body:
        raise OperationOutcomeError(
            status_code="400",
            severity="error",
            code="invalid",
            details=SpineErrorConcept.from_code("BAD_REQUEST"),
            diagnostics="Request body is required",
        )

    try:
        result = model.model_validate_json(body)
        raise_when_duplicate_keys(body)
        logger.log(LogReference.HANDLER009, parsed_body=result.model_dump())
        return result

    except ValidationError as exc:
        raise ParseError.from_validation_error(
            exc,
            details=SpineErrorConcept.from_code("MESSAGE_NOT_WELL_FORMED"),
            msg="Request body could not be parsed",
        ) from None


def raise_when_duplicate_keys(json_content: str) -> None:
    """
    Raises an error if duplicate keys are found in the JSON content.
    """
    logger.log(LogReference.HANDLER018)
    duplicates, paths = check_duplicate_keys(json_content)
    if duplicates:
        error = OperationOutcomeError(
            severity="error",
            code="invalid",
            details=SpineErrorConcept.from_code("MESSAGE_NOT_WELL_FORMED"),
            diagnostics=f"Duplicate keys found in FHIR document: {duplicates}",
            expression=paths,
        )
        logger.log(LogReference.HANDLER019, error=str(error))
        raise error


def parse_path(
    model: Type[BaseModel] | None,
    path_params: Dict[str, str] | None,
) -> BaseModel | None:
    if not model:
        return None

    logger.log(
        LogReference.HANDLER010,
        path=path_params,
        model=model.__name__,
    )

    try:
        result = model.model_validate(path_params or {})
        logger.log(LogReference.HANDLER011, parsed_path=result.model_dump())
        return result

    except ValidationError as exc:
        raise ParseError.from_validation_error(
            exc,
            details=SpineErrorConcept.from_code("INVALID_PARAMETER"),
            msg="Invalid path parameter",
        ) from None
