#!/usr/bin/env python
import sys

import boto3
from botocore.exceptions import ClientError

# Needed for when the script is run in Lambda where modules are in scripts subdirectory
try:
    import fire
except ImportError:
    fire = None


def _handle_table_access_error(e, table_name):
    error_code = e.response["Error"]["Code"]
    if error_code == "ResourceNotFoundException":
        print(f"Error: Table '{table_name}' does not exist")
    elif error_code == "AccessDeniedException":
        print(f"Error: No permission to access table '{table_name}'")
    else:
        print(f"Error accessing table: {e}")
    sys.exit(1)


def _scan_and_delete_batch(table, scan_kwargs, deleted_count):
    try:
        response = table.scan(**scan_kwargs)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ProvisionedThroughputExceededException":
            print(f"\nWarning: Throttled at {deleted_count} items. Retrying...")
            return scan_kwargs.get("ExclusiveStartKey"), deleted_count, True
        raise

    with table.batch_writer() as batch:
        for item in response["Items"]:
            batch.delete_item(Key=item)
            deleted_count += 1

    if deleted_count % 100 == 0:
        print(f"Deleted {deleted_count} items...", end="\r")

    return response.get("LastEvaluatedKey"), deleted_count, False


def delete_all_table_items(table_name):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    try:
        key_names = [key["AttributeName"] for key in table.key_schema]
    except ClientError as e:
        _handle_table_access_error(e, table_name)

    scan_kwargs = {"ProjectionExpression": ",".join(key_names)}
    deleted_count = 0

    try:
        while True:
            last_key, deleted_count, was_throttled = _scan_and_delete_batch(
                table, scan_kwargs, deleted_count
            )

            if was_throttled:
                scan_kwargs.pop("ExclusiveStartKey", None)
                if last_key:
                    scan_kwargs["ExclusiveStartKey"] = last_key
                continue

            if not last_key:
                break

            scan_kwargs["ExclusiveStartKey"] = last_key

    except Exception as e:
        print(f"\nError during deletion: {e}")
        print(f"Successfully deleted {deleted_count} items before error")
        sys.exit(1)

    print(f"\n✓ Cleared {deleted_count} items from {table_name}")
    return deleted_count


if __name__ == "__main__":
    if fire is None:
        print("Error: fire module not available")
        sys.exit(1)
    fire.Fire(delete_all_table_items)
