from typing import List, Optional

from pydantic import ValidationError
from pydantic_core import ErrorDetails

from nrlf.core.response import Response
from nrlf.core.types import CodeableConcept
from nrlf.producer.fhir.r4 import model as producer_model
from nrlf.producer.fhir.r4.model import OperationOutcome, OperationOutcomeIssue


def format_error_location(loc: List) -> str:
    formatted_loc = ""
    for each in loc:
        if isinstance(each, int):
            formatted_loc = f"{formatted_loc}[{each}]"
        else:
            formatted_loc = f"{formatted_loc}.{each}" if formatted_loc else str(each)
    return formatted_loc


def diag_for_error(error: ErrorDetails, value_set: str, root_location: tuple) -> str:
    loc_string = format_error_location(error["loc"])
    if root_location:
        loc_string = format_error_location(root_location) + "." + loc_string

    msg = f"{loc_string or 'DocumentReference'}: {error['msg']}"
    msg += f", see: {value_set}" if value_set else ""
    return msg


def expression_for_error(error: ErrorDetails, root_location: tuple) -> Optional[str]:
    loc_string = format_error_location(error["loc"]) or "DocumentReference"
    if root_location and error["loc"]:
        loc_string = (
            format_error_location(root_location)
            + "."
            + format_error_location(error["loc"])
        )
    return loc_string


class OperationOutcomeError(Exception):
    """
    Will instantly trigger an OperationOutcome error response when raised
    """

    def __init__(  # noqa: PLR0913
        self,
        severity: str,
        code: str,
        details: CodeableConcept,
        diagnostics: Optional[str] = None,
        expression: Optional[list[str]] = None,
        status_code: str = "400",
    ):
        self.operation_outcome = OperationOutcome(
            resourceType="OperationOutcome",
            issue=[
                OperationOutcomeIssue(
                    severity=severity,
                    code=code,
                    details=details,  # type: ignore
                    diagnostics=diagnostics,
                    expression=expression,
                )
            ],
        )
        self.status_code = status_code

    @property
    def response(self) -> Response:
        return Response(
            statusCode=self.status_code,
            body=self.operation_outcome.model_dump_json(exclude_none=True, indent=2),
        )

    def __str__(self):
        return f"OperationOutcomeError: {self.operation_outcome}"


class ParseError(Exception):
    issues: List[OperationOutcomeIssue]

    def __init__(self, issues: List[OperationOutcomeIssue]):
        self.issues = issues

    @classmethod
    def from_validation_error(
        cls,
        exc: ValidationError,
        details: CodeableConcept,
        msg: str = "",
        value_set: str = "",
        root_location: tuple = None,
    ):
        issues = [
            producer_model.OperationOutcomeIssue(
                severity="error",
                code="invalid",
                details=details,  # type: ignore
                diagnostics=f"{msg} ({diag_for_error(error, value_set, root_location)})",
                expression=[expression_for_error(error, root_location)],  # type: ignore
            )
            for error in exc.errors()
        ]

        return cls(issues)

    @property
    def response(self):
        return Response(
            statusCode="400",
            body=producer_model.OperationOutcome(
                resourceType="OperationOutcome",
                issue=self.issues,
            ).model_dump_json(exclude_none=True, indent=2),
        )
