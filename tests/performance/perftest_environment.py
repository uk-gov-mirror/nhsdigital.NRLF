import csv
import json
import os
import re

import boto3

from tests.performance.seed_data_constants import CHECKSUM_WEIGHTS

DYNAMODB = boto3.resource("dynamodb", region_name="eu-west-2")

default_table_name = "default-table-name"


def _get_pointers_table_name():
    perftest_table_name = os.environ.get("PERFTEST_TABLE_NAME", default_table_name)

    if re.search("^nhsd-nrlf--.+-pointers-table$", perftest_table_name):
        return perftest_table_name

    return f"nhsd-nrlf--{perftest_table_name}-pointers-table"


def create_extract_metadata_file(
    table_name: str,
    output_dir=".",
):
    meta_out = output_dir + f"/info.json"

    os.system(f"./scripts/get-current-info.sh > {meta_out}.temp")

    with open(f"{meta_out}.temp", "r") as temp_f:
        metadata = json.load(temp_f)
        # Set any additional metadata fields (e.g. table name) as needed
        metadata["table_name"] = table_name
        with open(f"{meta_out}", "w+") as f:
            json.dump(metadata, f, indent=2)

    os.system(f"rm {meta_out}.temp")

    print(f"Pointer extract metadata saved to {meta_out}")  # noqa: T201


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


def generate_pointer_table_extract(
    extract_size=2000000,  # must be a multiple of buffer_size (1 million)
    output_dir=".",
):
    """
    Generate a CSV file containing all pointer IDs, pointer type, custodian, and nhs_number (patient).
    """
    table_name = _get_pointers_table_name()
    out = output_dir + f"/seed-pointers-extract.csv"
    table = DYNAMODB.Table(table_name)
    scan_kwargs = {}
    done = False
    start_key = None
    buffer = []
    buffer_size = 1_000_000  # 10k rows needs ~3MB of RAM, so 1M rows needs ~300MB
    buffers_written = 0

    with open(out, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["pointer_id", "pointer_type", "custodian", "nhs_number"])
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
                            pointer_id,
                            pointer_type,
                            custodian,
                            nhs_number,
                        ]
                    ]
                )
                if len(buffer) >= buffer_size:
                    print("Writing buffer to CSV...")  # noqa: T201
                    writer.writerows(buffer)
                    buffers_written += 1
                    buffer.clear()
            start_key = response.get("LastEvaluatedKey", None)

            no_more_to_read = start_key is None
            reached_desired_extract_size = (
                buffers_written * buffer_size
            ) >= extract_size

            done = no_more_to_read or reached_desired_extract_size
        # Write any remaining rows in buffer
        if buffer:
            writer.writerows(buffer)
            buffers_written += 1
    print(f"Pointer extract CSV data written to {out}")  # noqa: T201

    create_extract_metadata_file(table_name, output_dir)


if __name__ == "__main__":
    import fire

    fire.Fire(
        {
            "generate_pointer_table_extract": generate_pointer_table_extract,
        }
    )
