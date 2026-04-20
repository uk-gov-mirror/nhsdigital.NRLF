from dataclasses import dataclass
from re import match
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from nrlf.consumer.fhir.r4.model import RequestQueryCategory
from nrlf.core.codes import SpineErrorConcept
from nrlf.core.constants import (
    ATTACHMENT_CONTENT_TYPES,
    CATEGORY_ATTRIBUTES,
    CONTENT_FORMAT_CODE_MAP,
    CONTENT_RETRIEVAL_CODE_MAP,
    ODS_SYSTEM,
    PRACTICE_SETTING_VALUE_SET_URL,
    REQUIRED_CREATE_FIELDS,
    SNOMED_PRACTICE_SETTINGS,
    SNOMED_SYSTEM_URL,
    TYPE_ATTRIBUTES,
    TYPE_CATEGORIES,
    Categories,
    PointerTypes,
)
from nrlf.core.errors import ParseError
from nrlf.core.logger import LogReference, logger
from nrlf.core.types import DocumentReference, OperationOutcomeIssue, RequestQueryType
from nrlf.producer.fhir.r4 import model as producer_model
from nrlf.producer.fhir.r4.model import (
    ContentStabilityExtension,
    NRLRetrievalMechanismExtension,
)


def validate_type(type_: Optional[RequestQueryType], pointer_types: List[str]) -> bool:
    """
    Validates if the given type is present in the list of pointer types.
    """
    if not type_:
        return True

    return type_.root in pointer_types


def validate_category(categories: Optional[RequestQueryCategory]) -> bool:
    """
    Validates if the given category is valid.
    """
    if not categories:
        return True

    return all(category in Categories.list() for category in categories)


@dataclass
class ValidationResult:
    resource: DocumentReference
    issues: List[OperationOutcomeIssue]

    def reset(self):
        self.__init__(
            resource=producer_model.DocumentReference.model_construct(), issues=[]
        )

    def add_error(
        self,
        issue_code: str,
        error_code: Optional[str] = None,
        diagnostics: Optional[str] = None,
        field: Optional[str] = None,
    ):
        details = None
        if error_code is not None:
            details = SpineErrorConcept.from_code(error_code)

        issue = producer_model.OperationOutcomeIssue(
            severity="error",
            code=issue_code,
            details=details,
            diagnostics=diagnostics,
            expression=[field] if field else None,  # type: ignore
        )

        logger.log(LogReference.VALIDATOR002, issue=issue.model_dump(exclude_none=True))
        self.issues.append(issue)

    @property
    def is_valid(self):
        return not any(issue.severity in {"error", "fatal"} for issue in self.issues)


class StopValidationError(Exception):
    pass


class DocumentReferenceValidator:
    """
    A class to validate document references
    """

    MODEL = producer_model.DocumentReference

    def __init__(self):
        self.result = ValidationResult(resource=self.MODEL.model_construct(), issues=[])

    @classmethod
    def parse(cls, data: Dict[str, Any]):
        try:
            logger.log(LogReference.PARSE000, data=data, model=cls.MODEL.__name__)
            result = cls.MODEL.model_validate(data)
            logger.log(LogReference.PARSE001, model=cls.MODEL.__name__)
            logger.log(LogReference.PARSE001a, result=result)
            return result

        except ValidationError as exc:
            logger.log(
                LogReference.PARSE002,
                model=cls.MODEL.__name__,
                data=data,
                validation_error=str(exc),
            )
            raise ParseError.from_validation_error(
                exc,
                details=SpineErrorConcept.from_code("BAD_REQUEST"),
                msg="Failed to parse DocumentReference resource",
            ) from None

    def validate(self, data: Dict[str, Any] | DocumentReference):
        """
        Validate the document reference
        """
        logger.log(LogReference.VALIDATOR000, resource_type="DocumentReference")
        resource = self.parse(data) if isinstance(data, dict) else data

        self.result = ValidationResult(resource=resource, issues=[])

        try:
            self._validate_required_fields(resource)
            self._validate_identifiers(resource)
            self._validate_relates_to(resource)
            self._validate_ssp_asid(resource)
            self._validate_type(resource)
            self._validate_category(resource)
            self._validate_author(resource)
            self._validate_type_category_mapping(resource)
            self._validate_content(resource)
            self._validate_content_format(resource)
            self._validate_content_extension(resource)
            self._validate_practice_setting(resource)

        except StopValidationError:
            logger.log(LogReference.VALIDATOR003)

        logger.log(
            LogReference.VALIDATOR999,
            is_valid=self.result.is_valid,
            issue_count=len(self.result.issues),
        )
        return self.result

    def _validate_required_fields(self, model: DocumentReference):
        """
        Validate the required fields
        """
        logger.log(
            LogReference.VALIDATOR001,
            step="required_fields",
            required_fields=REQUIRED_CREATE_FIELDS,
        )

        for field in REQUIRED_CREATE_FIELDS:
            if not getattr(model, field, None):
                self.result.add_error(
                    issue_code="business-rule",
                    error_code="UNPROCESSABLE_ENTITY",
                    diagnostics=f"The required field '{field}' is missing",
                    field=field,
                )

        if not self.result.is_valid:
            raise StopValidationError()

    def _validate_identifiers(self, model: DocumentReference):
        """ """
        logger.log(LogReference.VALIDATOR001, step="identifiers")

        if not (custodian_identifier := getattr(model.custodian, "identifier", None)):
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics="Custodian must have an identifier",
                field="custodian.identifier",
            )
            raise StopValidationError()

        if not (subject_identifier := getattr(model.subject, "identifier", None)):
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics="Subject must have an identifier",
                field="subject.identifier",
            )
            raise StopValidationError()

        if (
            custodian_identifier.system
            != "https://fhir.nhs.uk/Id/ods-organization-code"
        ):
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics="Provided custodian identifier system is not the ODS system (expected: 'https://fhir.nhs.uk/Id/ods-organization-code')",
                field="custodian.identifier.system",
            )

        if subject_identifier.system != "https://fhir.nhs.uk/Id/nhs-number":
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=(
                    "Provided subject identifier system is not the NHS number system "
                    "(expected 'https://fhir.nhs.uk/Id/nhs-number')"
                ),
                field="subject.identifier.system",
            )

    def _validate_relates_to(self, model: DocumentReference):
        """"""
        if not model.relatesTo:
            logger.log(
                LogReference.VALIDATOR001a, step="relates_to", reason="no_relates_to"
            )
            return

        logger.log(LogReference.VALIDATOR001, step="relates_to")

        logger.debug("Validating relatesTo")

        for index, relates_to in enumerate(model.relatesTo):
            if relates_to.code not in [
                "replaces",
                "transforms",
                "signs",
                "appends",
                "incorporates",
                "summarizes",
            ]:
                self.result.add_error(
                    issue_code="business-rule",
                    error_code="UNPROCESSABLE_ENTITY",
                    diagnostics=f"Invalid relatesTo code: {relates_to.code}",
                    field=f"relatesTo[{index}].code",
                )
                continue

            if relates_to.code == "replaces" and not (
                relates_to.target.identifier and relates_to.target.identifier.value
            ):
                self.result.add_error(
                    issue_code="business-rule",
                    error_code="UNPROCESSABLE_ENTITY",
                    diagnostics="relatesTo code 'replaces' must have a target identifier",
                    field=f"relatesTo[{index}].target.identifier.value",
                )

    def _validate_asid(self, asid_references: list):
        """
        Validate that the ASID provided in the document is valid
        """
        logger.log(LogReference.VALIDATOR001, step="ssp_asid")

        if len(asid_references) > 1:
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics="Multiple ASID identifiers provided. Only a single valid ASID identifier can be provided in the context.related.",
                field="context.related",
            )
            return

        idx, asid_reference = asid_references[0]
        asid_value = getattr(asid_reference.identifier, "value") or ""
        if not match(r"^\d{12}$", asid_value):
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid ASID value '{asid_value}'. A single ASID consisting of 12 digits can be provided in the context.related field.",
                field=f"context.related[{idx}].identifier.value",
            )

    def _validate_ssp_asid(self, model: DocumentReference):
        """
        Validate that the document contains a valid ASID in the context.related field when the content contains an SSP URL
        """

        ssp_content = any(
            content
            for content in model.content
            if content.attachment.url.startswith("ssp://")
        )

        logger.log(LogReference.VALIDATOR001, step="ssp_content_and_asid_exists")

        does_related_exist = getattr(model.context, "related", None)
        does_asid_exist = False
        if does_related_exist:
            asid_references = [
                (idx, related)
                for idx, related in enumerate(getattr(model.context, "related", []))
                if related.identifier.system == "https://fhir.nhs.uk/Id/nhsSpineASID"
            ]
            if len(asid_references) > 0:
                does_asid_exist = True
                self._validate_asid(asid_references)

        if not does_asid_exist and not ssp_content:
            logger.log(
                LogReference.VALIDATOR001a, step="ssp_asid", reason="no_ssp_content"
            )
            return

        if ssp_content and not does_related_exist:
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics="Missing context.related. It must be provided and contain a single valid ASID identifier when content contains an SSP URL",
                field="context.related",
            )
            return

        if ssp_content and does_related_exist and not does_asid_exist:
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics="Missing ASID identifier. context.related must contain a single valid ASID identifier when content contains an SSP URL",
                field="context.related",
            )

    def _validate_type(self, model: DocumentReference):
        """
        Validate the type field contains an appropriate coding system, code and display.
        """
        logger.log(LogReference.VALIDATOR001, step="type")

        if len(model.type.coding) > 1:
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid type coding length: {len(model.type.coding)} Type Coding must only contain a single value",
                field="type.coding",
            )
            return

        coding = model.type.coding[0]
        if coding.system not in ["http://snomed.info/sct", "https://nicip.nhs.uk"]:
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid type system: {coding.system} Type system must be either 'http://snomed.info/sct' or 'https://nicip.nhs.uk'",
                field="type.coding[0].system",
            )
            return

        type_id = f"{coding.system}|{coding.code}"
        if type_id not in TYPE_ATTRIBUTES.keys():
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid type code: {coding.code} Type must be a member of the England-NRLRecordType value set (https://fhir.nhs.uk/England/CodeSystem/England-NRLRecordType)",
                field="type.coding[0].code",
            )
            return

        type_attributes = TYPE_ATTRIBUTES.get(type_id, {})
        if coding.display != type_attributes.get("display"):
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"type code '{coding.code}' must have a display value of '{type_attributes.get('display')}'",
                field="type.coding[0].display",
            )

    def _validate_category(self, model: DocumentReference):
        """
        Validate the category field contains an appropriate coding system, code and display.
        """
        logger.log(LogReference.VALIDATOR001, step="category")

        if len(model.category) > 1:
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid category length: {len(model.category)} Category must only contain a single value",
                field="category",
            )
            return

        logger.debug("Validating category")

        if len(model.category[0].coding) > 1:
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid category coding length: {len(model.category[0].coding)} Category Coding must only contain a single value",
                field="category[0].coding",
            )
            return

        coding = model.category[0].coding[0]
        if coding.system != "http://snomed.info/sct":
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid category system: {coding.system} Category system must be 'http://snomed.info/sct'",
                field="category[0].coding[0].system",
            )
            return

        category_id = f"{coding.system}|{coding.code}"
        if category_id not in CATEGORY_ATTRIBUTES.keys():
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid category code: {coding.code} Category must be a member of the England-NRLRecordCategory value set (https://fhir.nhs.uk/England/CodeSystem/England-NRLRecordCategory)",
                field="category[0].coding[0].code",
            )
            return

        category_attributes = CATEGORY_ATTRIBUTES.get(category_id, {})
        if coding.display != category_attributes.get("display"):
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"category code '{coding.code}' must have a display value of '{category_attributes.get('display')}'",
                field="category[0].coding[0].display",
            )

    def _validate_type_category_mapping(self, model: DocumentReference):
        """
        Validate the type field matches the expected category
        """
        logger.log(LogReference.VALIDATOR001, step="type_category_mapping")

        type_coding = model.type.coding[0]
        type_id = f"{type_coding.system}|{type_coding.code}"
        category_coding = model.category[0].coding[0]
        category_id = f"{category_coding.system}|{category_coding.code}"

        if type_id not in PointerTypes.list() or category_id not in Categories.list():
            return  # No point mapping to an unexisting/unsupported type/category

        type_category = TYPE_CATEGORIES.get(type_id)
        if type_category != category_id:
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"The Category code of the provided document '{category_id}' must match the allowed category for pointer type '{type_id}' with a category value of '{type_category}'",
                field="category.coding[0].code",
            )

    def _validate_content_format(self, model: DocumentReference):
        """
        Validate the content.format field contains an appropriate coding.
        """
        logger.log(LogReference.VALIDATOR001, step="content_format")

        logger.debug("Validating format")
        for i, content in enumerate(model.content):
            if (
                content.attachment.contentType == "text/html"
                and content.format.code
                not in ["urn:nhs-ic:record-contact", "urn:nhs-ic:structured"]
            ):
                self.result.add_error(
                    issue_code="business-rule",
                    error_code="UNPROCESSABLE_ENTITY",
                    diagnostics=f"Invalid content format code: {content.format.code} format code must be 'urn:nhs-ic:record-contact' for Contact details attachments.",
                    field=f"content[{i}].format.code",
                )
            elif (
                content.attachment.contentType == "application/pdf"
                and content.format.code != "urn:nhs-ic:unstructured"
            ):
                self.result.add_error(
                    issue_code="business-rule",
                    error_code="UNPROCESSABLE_ENTITY",
                    diagnostics=f"Invalid content format code: {content.format.code} format code must be 'urn:nhs-ic:unstructured' for Unstructured Document attachments.",
                    field=f"content[{i}].format.code",
                )
            elif (
                content.attachment.contentType
                in {
                    "application/json",
                    "application/fhir+json",
                    "application/json+fhir",
                }
                and content.format.code != "urn:nhs-ic:structured"
            ):
                self.result.add_error(
                    issue_code="business-rule",
                    error_code="UNPROCESSABLE_ENTITY",
                    diagnostics=f"Invalid content format code: {content.format.code} format code must be 'urn:nhs-ic:structured' for Structured Document attachments.",
                    field=f"content[{i}].format.code",
                )

    def _validate_content_extension(self, model: DocumentReference):
        """
        Validate the content.extension field contains an appropriate coding.
        """
        logger.log(LogReference.VALIDATOR001, step="content_extension")
        logger.debug("Validating extension")

        for i, content in enumerate(model.content):
            if not self._has_valid_extensions(content.extension, i):
                return

    def _is_content_stability_extension(self, extension):
        return "contentstability" in str(extension).lower()

    def _is_retrieval_mechanism_extension(self, extension):
        return "retrievalmechanism" in str(extension).lower()

    def _has_valid_extensions(self, extensions, i):
        content_stability_count = 0
        content_retrieval_count = 0

        for extension in extensions:
            if self._is_content_stability_extension(extension):
                content_stability_count += 1
            elif self._is_retrieval_mechanism_extension(extension):
                content_retrieval_count += 1

        if content_stability_count != 1:
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics="Invalid content extension: Extension must have one content stability extension, see: ('https://fhir.nhs.uk/England/ValueSet/England-NRLContentStability')",
                field=f"content[{i}].extension",
            )
            return False

        if content_retrieval_count > 1:
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics="Invalid content retrieval extension: Extension must have one content retrieval extension, see: ('https://fhir.nhs.uk/England/ValueSet/England-NRLRetrievalMechanism')",
                field=f"content[{i}].extension",
            )
            return False

        return self._validate_content_extension_items(extensions, i)

    def _validate_content_extension_items(self, extensions, i):
        for j, extension in enumerate(extensions):
            if self._is_content_stability_extension(extension):
                if not self._validate_content_stability_extension(extension, i, j):
                    return False
            elif self._is_retrieval_mechanism_extension(extension):
                if not self._validate_retrieval_mechanism_extension(extension, i, j):
                    return False
        return True

    def _validate_content_stability_extension(self, extension, i, j):
        try:
            ContentStabilityExtension.model_validate(extension.model_dump())
        except ValidationError as exc:
            raise ParseError.from_validation_error(
                exc,
                details=SpineErrorConcept.from_code("BAD_REQUEST"),
                msg="Invalid content stability extension",
                value_set="https://fhir.nhs.uk/England/ValueSet/England-NRLContentStability",
                root_location=("content", i, "extension", j),
            ) from None
        coding = extension.valueCodeableConcept.coding[0]
        if coding.code != coding.display.lower():
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid content extension display: {coding.display} Extension display must be the same as code either 'Static' or 'Dynamic'",
                field=f"content[{i}].extension[{j}].valueCodeableConcept.coding[0].display",
            )
            return False
        return True

    def _validate_retrieval_mechanism_extension(self, extension, i, j):
        try:
            NRLRetrievalMechanismExtension.model_validate(extension.model_dump())
        except ValidationError as exc:
            raise ParseError.from_validation_error(
                exc,
                details=SpineErrorConcept.from_code("BAD_REQUEST"),
                msg="Invalid content retrieval extension",
                value_set="https://fhir.nhs.uk/England/ValueSet/England-NRLRetrievalMechanism",
                root_location=("content", i, "extension", j),
            ) from None
        coding = extension.valueCodeableConcept.coding[0]
        expected_retrieval_display = CONTENT_RETRIEVAL_CODE_MAP.get(coding.code)
        if coding.display != expected_retrieval_display:
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid content extension display: {coding.display} Expected display is '{expected_retrieval_display}'",
                field=f"content[{i}].extension[{j}].valueCodeableConcept.coding[0].display",
            )
            return False
        return True

    def _validate_author(self, model: DocumentReference):
        """
        Validate the author field contains an appropriate coding system and code.
        """
        logger.log(LogReference.VALIDATOR001, step="author")

        if len(model.author) > 1:
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid author length: {len(model.author)} Author must only contain a single value",
                field="author",
            )
            return

        logger.debug("Validating author")
        identifier = model.author[0].identifier

        if identifier.system != ODS_SYSTEM:
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid author system: '{identifier.system}' Author system must be '{ODS_SYSTEM}'",
                field="author[0].identifier.system",
            )
            return

        if not identifier.value.isalnum():
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid author value: '{identifier.value}' Author value must be alphanumeric",
                field="author[0].identifier.value",
            )
            return

        if len(identifier.value) > 12:
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid author value: '{identifier.value}' Author value must be less than 13 characters",
                field="author[0].identifier.value",
            )

    def _validate_practice_setting(self, model: DocumentReference):
        """
        Validate the practice setting field contains an appropriate coding system and code.
        """

        if not (
            practice_setting_coding := getattr(
                model.context.practiceSetting, "coding", []
            )
        ):
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics="Invalid practice setting: must contain a Coding",
                field="context.practiceSetting.coding",
            )
            return

        if len(practice_setting_coding) != 1:
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid practice setting coding length: {len(model.context.practiceSetting.coding)} Practice Setting Coding must only contain a single value",
                field="context.practiceSetting.coding",
            )
            return

        if (
            practice_setting_system := getattr(
                practice_setting_coding[0], "system", None
            )
        ) != SNOMED_SYSTEM_URL:
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid practice setting system: {practice_setting_system} Practice Setting system must be '{SNOMED_SYSTEM_URL}'",
                field="context.practiceSetting.coding[0].system",
            )
            return

        if (
            practice_setting_value := getattr(practice_setting_coding[0], "code", None)
        ) not in SNOMED_PRACTICE_SETTINGS:
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid practice setting code: {practice_setting_value} Practice Setting coding must be a member of value set {PRACTICE_SETTING_VALUE_SET_URL}",
                field="context.practiceSetting.coding[0].code",
            )
            return

        if (
            practice_setting_display := getattr(
                practice_setting_coding[0], "display", None
            )
        ) != SNOMED_PRACTICE_SETTINGS.get(practice_setting_value):
            self.result.add_error(
                issue_code="business-rule",
                error_code="UNPROCESSABLE_ENTITY",
                diagnostics=f"Invalid practice setting coding: display {practice_setting_display} does not match the expected display for {practice_setting_value} Practice Setting coding is bound to value set {PRACTICE_SETTING_VALUE_SET_URL}",
                field="context.practiceSetting.coding[0]",
            )

    def _validate_content(self, model: DocumentReference):
        """
        Validate that the contentType is present and supported.
        """
        logger.log(LogReference.VALIDATOR001, step="content")

        for i, content in enumerate(model.content):
            if content.attachment.contentType not in ATTACHMENT_CONTENT_TYPES:
                self.result.add_error(
                    issue_code="business-rule",
                    error_code="UNPROCESSABLE_ENTITY",
                    diagnostics=f"Invalid contentType: {content.attachment.contentType}. Must be 'application/pdf', 'text/html' or 'application/fhir+json'",
                    field=f"content[{i}].attachment.contentType",
                )

            # Validate NRLFormatCode
            format_code = content.format.code
            format_display = content.format.display
            expected_display = CONTENT_FORMAT_CODE_MAP.get(format_code)
            if expected_display and format_display != expected_display:
                self.result.add_error(
                    issue_code="business-rule",
                    error_code="UNPROCESSABLE_ENTITY",
                    diagnostics=f"Invalid display for format code '{format_code}'. Expected '{expected_display}'",
                    field=f"content[{i}].format.display",
                )
