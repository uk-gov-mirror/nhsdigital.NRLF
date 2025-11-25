import json
import pathlib

import boto3
from nhs_number import generate

from scripts.are_resources_shared_for_stack import uses_shared_resources

DYNAMODB = boto3.resource("dynamodb", region_name="eu-west-2")


def get_pointers_table_name(stack_name):
    if uses_shared_resources(stack_name):
        env = stack_name.split("-")[0]
        return f"nhsd-nrlf--{env}-pointers-table"
    else:
        return f"nhsd-nrlf--{stack_name}-pointers-table"


def extract_consumer_data(stack_name, out="consumer_reference_data.json"):
    table_name = get_pointers_table_name(stack_name)
    table = DYNAMODB.Table(table_name)
    scan_kwargs = {}
    done = False
    start_key = None
    nhs_numbers = set()
    pointer_ids = []
    ods_codes = set()
    while not done:
        if start_key:
            scan_kwargs["ExclusiveStartKey"] = start_key
        response = table.scan(**scan_kwargs)
        for item in response.get("Items", []):
            nhs_number = item.get("nhs_number")
            pointer_id = item.get("id")
            ods_code = item.get("ods_code")
            if nhs_number:
                nhs_numbers.add(nhs_number)
            if pointer_id:
                pointer_ids.append(pointer_id)
            if ods_code:
                ods_codes.add(ods_code)
        start_key = response.get("LastEvaluatedKey", None)
        done = start_key is None
    data = {
        "nhs_numbers": list(nhs_numbers),
        "pointer_ids": pointer_ids,
        "ods_codes": list(ods_codes),
    }
    pathlib.Path(out).write_text(json.dumps(data))
    print(f"Consumer data written to {out}")  # noqa: T201


def generate_producer_data(
    stack_name, count=1000, ratio=0.8, out="producer_reference_data.json"
):
    table_name = get_pointers_table_name(stack_name)
    table = DYNAMODB.Table(table_name)
    scan_kwargs = {}
    done = False
    start_key = None
    existing_nhs_numbers = set()
    while not done:
        if start_key:
            scan_kwargs["ExclusiveStartKey"] = start_key
        response = table.scan(**scan_kwargs)
        for item in response.get("Items", []):
            nhs_number = item.get("nhs_number")
            if nhs_number:
                existing_nhs_numbers.add(nhs_number)
        start_key = response.get("LastEvaluatedKey", None)
        done = start_key is None
    new_nhs_numbers = set()
    while len(new_nhs_numbers) < int(count * ratio):
        (nhs,) = generate()
        if nhs not in existing_nhs_numbers:
            new_nhs_numbers.add(nhs)
    use_existing = list(existing_nhs_numbers)[: int(count * (1 - ratio))]
    data = {
        "new_nhs_numbers": list(new_nhs_numbers),
        "existing_nhs_numbers": use_existing,
        "ratio": ratio,
    }
    pathlib.Path(out).write_text(json.dumps(data))
    print(f"Producer data written to {out}")  # noqa: T201


if __name__ == "__main__":
    import fire

    fire.Fire(
        {
            "extract_consumer_data": extract_consumer_data,
            "generate_producer_data": generate_producer_data,
        }
    )
