import json
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
import fire

from nrlf.core.logger import logger

dynamodb = boto3.client("dynamodb")
paginator = dynamodb.get_paginator("scan")

logger.setLevel("ERROR")

REQUIRED_ATTRIBUTES = [
    "nhs_number",
    "custodian",
    "id",
    "master_identifier",
    "type_id",
    "created_on",
]


def _get_duplicates(
    table_name: str, custodians: str | tuple[str], filename: str = "duplicates"
) -> Any:
    """
    Get masterids for duplicate pointers in the given table for a list of custodians.
    Parameters:
    - table_name: The name of the pointers table to use.
    - custodians: The ODS codes of the custodian(s) to check.
    - filename: A name for the output text file containing the list of affected pointers.
    """
    custodian_list = (
        custodians.split(",") if isinstance(custodians, str) else list(custodians)
    )

    print(  # noqa
        f"Finding duplicate pointers for custodians {custodian_list} in table {table_name}...."
    )

    required_attributes = REQUIRED_ATTRIBUTES

    expression_names_str = ",".join(
        [f":param{custodian}" for custodian in custodian_list]
    )
    expression_values_list = {
        f":param{custodian}": {"S": custodian} for custodian in custodian_list
    }

    params: dict[str, Any] = {
        "TableName": table_name,
        "PaginationConfig": {"PageSize": 50},
        "FilterExpression": f"custodian IN ({expression_names_str})",
        "ExpressionAttributeValues": expression_values_list,
        "ProjectionExpression": ",".join(required_attributes),
    }
    pointers_by_key = dict()
    total_scanned_count = 0
    duplicate_count = 0
    duplicates_set = set()

    start_time = datetime.now(tz=timezone.utc)

    for page in paginator.paginate(**params):
        for item in page["Items"]:
            pointer_id = item.get("id", {}).get("S", "no-id")
            pointer_type = item.get("type_id", {}).get("S", "no-type")
            master_id = item.get("master_identifier", {}).get("S", "no-master-id")
            custodian = item.get("custodian", {}).get("S", "no-custodian")
            patient_id = item.get("nhs_number", {}).get("S", "no-patient-id")
            created_on = item.get("created_on", {}).get("S", "no-creation-datetime")

            pointer_data = {
                "id": pointer_id,
                "master_id": master_id,
                "datetime": created_on,
            }

            px_type_ods_key = f"{custodian}-{patient_id}-{pointer_type}"

            if px_type_ods_key not in pointers_by_key:
                pointers_by_key[px_type_ods_key] = [pointer_data]
            else:
                pointers_by_key[px_type_ods_key].append(pointer_data)
                duplicate_count += 1
                duplicates_set.add(px_type_ods_key)

        total_scanned_count += page["ScannedCount"]

        if total_scanned_count % 1000 == 0:
            print(".", end="", flush=True)  # noqa

        if total_scanned_count % 100000 == 0:
            print(  # noqa
                f"scanned={total_scanned_count} found={duplicate_count} potential duplicates "
            )

    end_time = datetime.now(tz=timezone.utc)

    print(" Table scan completed")  # noqa

    output_pointers = dict()

    for key in sorted(duplicates_set):
        output_pointers[key] = pointers_by_key[key]

    print(f"Writing pointers to file ./{filename}.txt ...")  # noqa
    with open(f"{filename}.txt", "w") as f:
        f.write(json.dumps(output_pointers, indent=2))

    return {
        "output_file": f"{filename}.txt",
        "duplicates-found": duplicate_count,
        "scanned-count": total_scanned_count,
        "took-secs": timedelta.total_seconds(end_time - start_time),
    }


if __name__ == "__main__":
    fire.Fire(_get_duplicates)
