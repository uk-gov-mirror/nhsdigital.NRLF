import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
import fire

INCLUDE_PATIENT_IDS = os.environ.get("INCLUDE_PATIENT_IDS", "false").lower() == "true"

dynamodb = boto3.client("dynamodb")
paginator = dynamodb.get_paginator("scan")


def _get_masterids_for_custodians(table_name: str, custodians: str | tuple[str]) -> Any:
    """
    Get masterids for pointers in the given table for a list of custodians.
    Parameters:
    - table_name: The name of the pointers table to use.
    """
    custodian_list = (
        custodians.split(",") if isinstance(custodians, str) else list(custodians)
    )

    print(  # noqa
        f"Getting masterids for custodians {custodian_list} in table {table_name}...."
    )

    required_attributes = (
        ["id", "type_id", "master_identifier", "custodian"]
        if not INCLUDE_PATIENT_IDS
        else ["id", "type_id", "master_identifier", "custodian", "nhs_number"]
    )

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

    pointers_info: list[dict[str, str]] = []
    total_scanned_count = 0

    start_time = datetime.now(tz=timezone.utc)

    for page in paginator.paginate(**params):
        for item in page["Items"]:
            pointer_id = item.get("id", {}).get("S", "no-id")
            pointer_type = item.get("type_id", {}).get("S", "no-type")
            master_id = item.get("master_identifier", {}).get("S", "no-master-id")
            custodian = item.get("custodian", {}).get("S", "no-custodian")

            pointers_info.append(
                {
                    "nrl-id": pointer_id,
                    "pointer-type": pointer_type,
                    "master_identifier": master_id,
                    "custodian": custodian,
                    "patient_id": item.get("nhs_number", {}).get("S", "no-patient-id"),
                }
            )

        total_scanned_count += page["ScannedCount"]

        if total_scanned_count % 1000 == 0:
            print(".", end="", flush=True)  # noqa

        if total_scanned_count % 100000 == 0:
            print(f"scanned={total_scanned_count} found={len(pointers_info)} ")  # noqa

    end_time = datetime.now(tz=timezone.utc)

    print(" Done")  # noqa

    print(f"Writing pointers to file ./pointer-masterids.txt ...")  # noqa
    with open("pointer-masterids.txt", "w") as f:
        f.write(json.dumps(pointers_info, indent=2))

    return {
        "output-file": "pointer-masterids.txt",
        "pointers-found": len(pointers_info),
        "scanned-count": total_scanned_count,
        "took-secs": timedelta.total_seconds(end_time - start_time),
    }


if __name__ == "__main__":
    fire.Fire(_get_masterids_for_custodians)
