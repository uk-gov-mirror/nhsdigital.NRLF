import json

from behave import *  # noqa
from behave.runner import Context
from pydantic import BaseModel

from nrlf.core.boto import get_s3_client
from nrlf.core.dynamodb.model import DocumentPointer
from tests.features.utils.data import create_test_document_reference


class Application(BaseModel):
    app_id: str = "UNSET"
    app_name: str = "UNSET"

    def add_pointer_types(self, ods_code: str, context: Context):
        if not context.table:
            raise ValueError("No permissions table provided")

        pointer_types = [f"{system}|{value}" for system, value in context.table]
        bucket = f"nhsd-nrlf--{context.stack_name}-authorization-store"
        key = f"{self.app_id}/{ods_code}.json"

        s3_client = get_s3_client()
        s3_client.put_object(Bucket=bucket, Key=key, Body=json.dumps(pointer_types))
        context.add_cleanup(lambda: s3_client.delete_object(Bucket=bucket, Key=key))

    def add_v2_permissions(
        self, api_side: str, context: Context, ods_code: Optional[str] = None
    ):
        if not context.table:
            raise ValueError("No permissions table provided")

        pointer_types = [f"{system}|{value}" for system, value in context.table]
        perms_body = {"types": pointer_types}
        bucket = f"nhsd-nrlf--{context.stack_name}-authorization-store"
        if ods_code:  # org-level permissions
            key = f"{api_side}/{self.app_id}/{ods_code}.json"
        else:  # app-level permissions
            key = f"{api_side}/{self.app_id}.json"

        s3_client = get_s3_client()
        s3_client.put_object(Bucket=bucket, Key=key, Body=json.dumps(pointer_types))
        context.add_cleanup(lambda: s3_client.delete_object(Bucket=bucket, Key=key))


@given("the application '{app_name}' (ID '{app_id}') is registered to access the API")
def register_application_step(context: Context, app_name: str, app_id: str):
    context.application = Application(app_id=app_id, app_name=app_name)


@given("the organisation '{ods_code}' is authorised to access pointer types")
def register_org_permissions_step(context: Context, ods_code: str):
    if not context.table:
        raise ValueError("No permissions table provided")

    context.application.add_pointer_types(ods_code, context)


@given("the organisation '{ods_code}' is authorised as a Producer for pointer types")
def register_v2_producer_org_permissions_step(context: Context, ods_code: str):
    if not context.table:
        raise ValueError("No permissions table provided")

    context.application.add_v2_permissions("producer", context, ods_code)


@given("the organisation '{ods_code}' is authorised as a Consumer for pointer types")
def register_v2_consumer_org_permissions_step(context: Context, ods_code: str):
    if not context.table:
        raise ValueError("No permissions table provided")

    context.application.add_v2_permissions("consumer", context, ods_code)


@given("the application has '{use_type}' permissions for pointer types")
def register_app_level_permissions_step(context: Context, use_type: str):
    if not context.table:
        raise ValueError("No permissions table provided")
    if use_type not in {"producer", "consumer"}:
        raise ValueError("Producer or Consumer side must be specified")
    context.application.add_v2_permissions(use_type, context)


@given("a DocumentReference resource exists with values")
def create_document_reference_step(context: Context):
    if not context.table:
        raise ValueError("No DocumentReference table provided")

    items = {row["property"]: row["value"] for row in context.table}
    base_doc_ref = create_test_document_reference(items)
    doc_pointer = DocumentPointer.from_document_reference(base_doc_ref)

    context.repository.create(doc_pointer)
    context.add_cleanup(clean_up_test_pointer, context, doc_pointer)


def clean_up_test_pointer(context: Context, doc_pointer: DocumentPointer):
    """Remove a pointer during cleanup without failing if it has already been deleted"""
    if context.repository.get_by_id(doc_pointer.id):
        context.repository.delete(doc_pointer)
