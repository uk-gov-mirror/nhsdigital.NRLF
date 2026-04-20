import os

from behave.runner import Context

from tests.features.utils.certificates import get_cert_path_for_environment

os.environ.setdefault("POWERTOOLS_LOG_LEVEL", "ERROR")
os.environ.setdefault("AWS_DEFAULT_REGION", "eu-west-2")

from nrlf.core.dynamodb.repository import DocumentPointerRepository


def before_scenario(context: Context, scenario):
    """
    Called before each scenario unless the the resources (i.e. the DynamoDB tables) are shared for the stack.
    Deletes every item in the table so that leftover data created by previous runs doesn't affect the current
    scenario.  Documents set up in 'Given' steps are re-created fresh after this cleanup.
    """
    if context.is_shared_resources:
        return

    try:
        scan_kwargs = {"ProjectionExpression": "pk, sk"}
        keys_to_delete = []
        while True:
            response = context.repository.table.scan(**scan_kwargs)
            keys_to_delete.extend(
                {"pk": item["pk"], "sk": item["sk"]}
                for item in response.get("Items", [])
            )
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_key

        for i in range(0, len(keys_to_delete), 25):
            context.repository.table.meta.client.batch_write_item(
                RequestItems={
                    context.repository.table_name: [
                        {"DeleteRequest": {"Key": key}}
                        for key in keys_to_delete[i : i + 25]
                    ]
                }
            )
    except Exception:
        pass


def before_all(context: Context):
    """
    This function is called before all the tests are executed
    """

    context.env = context.config.userdata.get("env")
    context.account_name = context.config.userdata.get("account_name")
    context.is_shared_resources = context.config.userdata.get("is_shared_resources")

    context.stack_name = (
        context.account_name if context.is_shared_resources else context.env
    )

    context.base_url = f"https://{context.env}.api.record-locator.dev.national.nhs.uk/"
    context.request_id = "feature-test-request-id"
    context.correlation_id = "feature-test-correlation-id"

    print(f"Running tests in {context.env} environment: {context.base_url}")  # noqa

    default_table_name = f"nhsd-nrlf--{context.stack_name}-pointers-table"

    context.client_cert = get_cert_path_for_environment(context.env)
    context.repository = DocumentPointerRepository(table_name=default_table_name)
