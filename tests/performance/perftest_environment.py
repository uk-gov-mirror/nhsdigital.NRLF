import csv
import json
import os
import pathlib
import re

import boto3

# from nhs_number import generate


DYNAMODB = boto3.resource("dynamodb", region_name="eu-west-2")

default_table_name = "default-table-name"
# default_table_name = "nhsd-nrlf--xaxel-deleteme-pointers-table"


def _get_pointers_table_name():
    perftest_table_name = os.environ.get("PERFTEST_TABLE_NAME", default_table_name)

    if re.search("^nhsd-nrlf--.+-pointers-table$", perftest_table_name):
        return perftest_table_name

    return f"nhsd-nrlf--{perftest_table_name}-pointers-table"


def extract_consumer_data(output_dir="."):
    out = output_dir + "/consumer_reference_data.json"
    table_name = _get_pointers_table_name()
    table = DYNAMODB.Table(table_name)
    scan_kwargs = {}
    done = False
    start_key = None
    nhs_numbers = set()
    pointer_ids = []
    custodians = set()
    while not done:
        if start_key:
            scan_kwargs["ExclusiveStartKey"] = start_key
        response = table.scan(**scan_kwargs)
        for item in response.get("Items", []):
            nhs_number = item.get("nhs_number")
            pointer_id = item.get("id")
            custodian = item.get("custodian")
            if nhs_number:
                nhs_numbers.add(nhs_number)
            if pointer_id:
                pointer_ids.append(pointer_id)
            if custodian:
                custodians.add(custodian)
        start_key = response.get("LastEvaluatedKey", None)
        done = start_key is None
    data = {
        "nhs_numbers": list(nhs_numbers),
        "pointer_ids": pointer_ids,
        "custodians": list(custodians),
    }
    pathlib.Path(out).write_text(json.dumps(data))
    print(f"Consumer data written to {out}")  # noqa: T201


# Semi-deterministic NHS number generator (duplicated from seed_nft_tables.py)
CHECKSUM_WEIGHTS = [i for i in range(10, 1, -1)]


class TestNhsNumbersIterator:
    def __iter__(self):
        self.first9 = 900000000
        return self

    def __next__(self):
        if self.first9 > 999999999:
            raise StopIteration
        checksum = 10
        while checksum == 10:
            self.first9 += 1
            nhs_no_digits = list(map(int, str(self.first9)))
            checksum = (
                sum(
                    weight * digit
                    for weight, digit in zip(CHECKSUM_WEIGHTS, nhs_no_digits)
                )
                * -1
                % 11
            )
        nhs_no = str(self.first9) + str(checksum)
        return nhs_no


def generate_producer_data(
    output_dir=".",
    proportion_existing=0.8,  # Proportion of output that should be existing NHS numbers
    total_count=1000,  # Total number of NHS numbers to output
    last_existing_nhs_number=None,  # Optionally specify the last NHS number in the table
):
    """
    Generate a reference dataset for producer tests, containing a mix of existing and new NHS numbers.
    - proportion_existing: fraction of output that should be existing NHS numbers (0.0-1.0)
    - total_count: total number of NHS numbers in output
    NHS numbers are generated in a semi-deterministic way, similar to the NFT seeding script.
    """
    out = output_dir + "/producer_reference_data.json"
    table_name = _get_pointers_table_name()
    table = DYNAMODB.Table(table_name)
    scan_kwargs = {}
    done = False
    start_key = None
    existing_nhs_numbers = set()

    # Scan DynamoDB table for all existing NHS numbers
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

    # Calculate how many existing and new NHS numbers to use
    num_existing = min(
        int(total_count * proportion_existing), len(existing_nhs_numbers)
    )
    num_new = total_count - num_existing

    # Select existing NHS numbers
    selected_existing_nhs_numbers = list(existing_nhs_numbers)[:num_existing]

    # Generate new NHS numbers that do not overlap with existing
    new_nhs_numbers = set()
    # If last_existing_nhs_number is provided, start from the next value
    if last_existing_nhs_number is not None:
        try:
            # Use only the first 9 digits for incrementing
            start_first9 = int(str(last_existing_nhs_number)[:9])
        except Exception:
            start_first9 = 900000000

        class CustomTestNhsNumbersIterator:
            def __iter__(self):
                self.first9 = start_first9
                return self

            def __next__(self):
                if self.first9 > 999999999:
                    raise StopIteration
                checksum = 10
                while checksum == 10:
                    self.first9 += 1
                    nhs_no_digits = list(map(int, str(self.first9)))
                    checksum = (
                        sum(
                            weight * digit
                            for weight, digit in zip(CHECKSUM_WEIGHTS, nhs_no_digits)
                        )
                        * -1
                        % 11
                    )
                nhs_no = str(self.first9) + str(checksum)
                return nhs_no

        nhs_iter = iter(CustomTestNhsNumbersIterator())
    else:
        nhs_iter = iter(TestNhsNumbersIterator())
    while len(new_nhs_numbers) < num_new:
        nhs = next(nhs_iter)
        if nhs not in existing_nhs_numbers and nhs not in new_nhs_numbers:
            new_nhs_numbers.add(nhs)

    # Prepare output data
    data = {
        "new_nhs_numbers": list(new_nhs_numbers),
        "existing_nhs_numbers": selected_existing_nhs_numbers,
        "proportion_existing": proportion_existing,
        "total_count": total_count,
    }
    pathlib.Path(out).write_text(json.dumps(data))
    print(f"Producer data written to {out}")  # noqa: T201


def generate_pointer_table_extract(
    output_dir=".",
):
    """
    Generate a CSV file containing all pointer IDs, pointer type, custodian, and nhs_number (patient).
    """
    out = output_dir + "/producer_reference_data.csv"
    table_name = _get_pointers_table_name()
    table = DYNAMODB.Table(table_name)
    scan_kwargs = {}
    done = False
    start_key = None
    buffer = []
    buffer_size = 1_000_000  # 10k rows needs ~3MB of RAM, so 1M rows needs ~300MB
    count = 1

    with open(out, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            ["count", "pointer_id", "pointer_type", "custodian", "nhs_number"]
        )
        while not done:

            if start_key:
                scan_kwargs["ExclusiveStartKey"] = start_key
            response = table.scan(**scan_kwargs)
            for item in response.get("Items", []):
                pointer_id = item.get("id", "")
                pointer_type = item.get("type", "").split("|", 1)[
                    1
                ]  # only keep code part
                custodian = item.get("custodian", "")
                nhs_number = item.get("nhs_number", "")
                buffer.append(
                    [
                        str(field).strip()
                        for field in [
                            count,
                            pointer_id,
                            pointer_type,
                            custodian,
                            nhs_number,
                        ]
                    ]
                )
                count += 1
                if len(buffer) >= buffer_size:
                    print("Writing buffer to CSV...")  # noqa: T201
                    writer.writerows(buffer)
                    buffer.clear()
            start_key = response.get("LastEvaluatedKey", None)
            done = start_key is None
        # Write any remaining rows in buffer
        if buffer:
            writer.writerows(buffer)
    print(f"Producer CSV data written to {out}")  # noqa: T201


if __name__ == "__main__":
    import fire

    fire.Fire(
        {
            "extract_consumer_data": extract_consumer_data,
            "generate_producer_data": generate_producer_data,
            "generate_pointer_table_extract": generate_pointer_table_extract,
        }
    )
