#!/usr/bin/env python
"""
Seeds a sandbox table with realistic pointer data using sample templates.
Creates 2 pointers of each type for 2 different custodians, one of which is the custodian that all sandbox users are represented by.
"""
import copy
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError

# Needed for when the script is run in Lambda where modules are in scripts subdirectory
try:
    from seed_utils import TestNhsNumbersIterator
except ImportError:
    # In Lambda, modules are in scripts subdirectory
    from scripts.seed_utils import TestNhsNumbersIterator

try:
    import fire
except ImportError:
    fire = None

try:
    from nrlf.core.dynamodb.model import DocumentPointer
    from nrlf.core.logger import logger
    from nrlf.producer.fhir.r4.model import DocumentReference

    logger.setLevel("ERROR")
except ImportError as e:
    print(f"Warning: Failed to import NRLF modules: {e}")
    raise

resource = boto3.resource("dynamodb")

SAMPLE_TEMPLATES = {
    "1382601000000107": "QUY_RESPECT_FORM_Feb25.json",
    "16521000000101": "G3H9E_LLOYD_GEORGE_RECORD_FOLDER_Aug25.json",
    "2181441000000107": "11X_PERSONALISED_CARE_AND_SUPPORT_PLAN_Feb25.json",
    "735324008": "11X_TREATMENT_ESCALATION_PLAN_Feb25.json",
    "736253002": "RAT_MENTAL_HEALTH_PLAN_Feb25.json",
    "736366004": "11X_ADVANCE_CARE_PLAN_Feb25.json",
    "861421000000109": "VM8W7_EOL_COORDINATION_SUMMARY_Feb25.json",
    "887701000000100": "B3H2B_EMERGENCY_HEALTHCARE_PLAN_Feb25.json",
}

# Y05868 is the test custodian required for int-sandbox, since it's the custodian that all sandbox users are represented by
CUSTODIANS = ["Y05868", "Y12345"]
AUTHOR = "X54321"


def _load_sample_template(filename: str) -> dict:
    samples_dir = Path(__file__).parent.parent / "tests" / "data" / "samples"
    filepath = samples_dir / filename

    with open(filepath, "r") as f:
        return json.load(f)


def _make_realistic_pointer(
    template: dict,
    custodian: str,
    nhs_number: str,
    counter: int,
) -> DocumentPointer:

    doc_ref_dict = copy.deepcopy(template)

    doc_ref_dict["id"] = f"{custodian}-SANDBOX-{str(counter).zfill(6)}"
    doc_ref_dict["subject"]["identifier"]["value"] = nhs_number
    doc_ref_dict["custodian"]["identifier"]["value"] = custodian
    doc_ref_dict["author"][0]["identifier"]["value"] = AUTHOR

    if "masterIdentifier" in doc_ref_dict:
        doc_ref_dict["masterIdentifier"]["value"] = f"sandbox-{custodian}-{counter}"

    retrieval_mechanism_ext = {
        "url": "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-NRLRetrievalMechanism",
        "valueCodeableConcept": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLRetrievalMechanism",
                    "code": "SSP",
                    "display": "Spine Secure Proxy",
                }
            ]
        },
    }

    if "content" not in doc_ref_dict or not doc_ref_dict["content"]:
        doc_ref_dict["content"] = [{"extension": [retrieval_mechanism_ext]}]
    else:
        extensions = doc_ref_dict["content"][0].get("extension", [])
        has_retrieval_mechanism = any(
            ext.get("url")
            == "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-NRLRetrievalMechanism"
            for ext in extensions
        )
        if not has_retrieval_mechanism:
            if "extension" not in doc_ref_dict["content"][0]:
                doc_ref_dict["content"][0]["extension"] = []
            doc_ref_dict["content"][0]["extension"].append(retrieval_mechanism_ext)

    doc_ref = DocumentReference(**doc_ref_dict)

    pointer = DocumentPointer.from_document_reference(doc_ref, source="SANDBOX-SEED")
    return pointer


def _validate_table_access(table_name: str):
    """Validate that the table exists and can be accessed"""
    try:
        table = resource.Table(table_name)
        table.load()
        return table
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ResourceNotFoundException":
            print(f"Error: Table '{table_name}' does not exist")
            sys.exit(1)
        elif error_code == "AccessDeniedException":
            print(f"Error: No permission to access table '{table_name}'")
            sys.exit(1)
        else:
            print(f"Error accessing table: {e}")
            sys.exit(1)


def _check_for_existing_sandbox_pointers(table, force: bool):
    if force:
        print("⚠️  Force mode enabled - will overwrite existing sandbox pointers")
        return

    try:
        response = table.scan(
            FilterExpression="begins_with(#src, :sandbox)",
            ExpressionAttributeNames={"#src": "source"},
            ExpressionAttributeValues={":sandbox": "SANDBOX"},
            Limit=1,
            ProjectionExpression="id",
        )

        if response.get("Items"):
            print("\n⚠️  Warning: Sandbox pointers already exist in this table.")
            print(
                "Running this script will OVERWRITE any existing sandbox pointers that have the same IDs."
            )
            print("\nOptions:")
            print("  1. Use --force flag to overwrite existing pointers")
            print("  2. Use reset_sandbox_table.py to clear all items first")
            print("  3. Use delete_all_table_items.py to manually clear the table\n")
            sys.exit(1)
    except ClientError as e:
        print(f"Warning: Could not check for existing pointers: {e}")


def _load_pointer_templates() -> dict[str, dict]:
    templates = {}
    for pointer_type, filename in SAMPLE_TEMPLATES.items():
        try:
            templates[pointer_type] = _load_sample_template(filename)
            print(f"✓ Loaded template for type {pointer_type}")
        except FileNotFoundError:
            print(f"✗ Template file not found: {filename}")
            continue
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON in template {filename}: {e}")
            continue
        except Exception as e:
            print(f"✗ Failed to load template {filename}: {e}")
            continue

    if not templates:
        print("Error: No templates could be loaded. Exiting.")
        sys.exit(1)

    return templates


def _write_batch_to_dynamodb(table_name: str, batch_items: list[dict]) -> bool:
    if not batch_items:
        return True

    try:
        response = resource.batch_write_item(RequestItems={table_name: batch_items})

        if response.get("UnprocessedItems"):
            unprocessed = len(response["UnprocessedItems"].get(table_name, []))
            print(f"\nWarning: {unprocessed} unprocessed items")

        print(".", end="", flush=True)
        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ProvisionedThroughputExceededException":
            print("\n✗ Throttled. Retrying batch...")
        else:
            print(f"\n✗ Error writing batch, batch cancelled: {e}")
        return False


def _create_pointer_item(
    template: dict,
    custodian: str,
    nhs_number: str,
    counter: int,
    pointer_type: str,
) -> tuple[dict | None, list[str] | None]:
    """Create a single pointer and return the put request and CSV data."""
    try:
        pointer = _make_realistic_pointer(template, custodian, nhs_number, counter)

        put_req = {"PutRequest": {"Item": pointer.model_dump()}}
        csv_data = [pointer.id, pointer_type, pointer.custodian, pointer.nhs_number]

        return put_req, csv_data

    except ValueError as e:
        print(f"\n✗ Validation error for pointer {counter}: {e}")
        return None, None
    except Exception as e:
        print(f"\n✗ Error creating pointer {counter}: {e}")
        return None, None


def _generate_pointers_for_custodian(
    template: dict,
    pointer_type: str,
    custodian: str,
    pointers_per_type: int,
    counter_start: int,
    testnum_iter,
) -> tuple[list[dict], list[list[str]], int]:
    batch_items = []
    csv_rows = []
    counter = counter_start

    for _ in range(pointers_per_type):
        counter += 1

        try:
            nhs_number = next(testnum_iter)
        except StopIteration:
            print(f"\n✗ Error: Ran out of NHS numbers at pointer {counter}")
            break

        put_req, csv_data = _create_pointer_item(
            template, custodian, nhs_number, counter, pointer_type
        )

        if put_req and csv_data:
            batch_items.append(put_req)
            csv_rows.append(csv_data)

    return batch_items, csv_rows, counter


def _generate_and_write_pointers(
    table_name: str, templates: dict[str, dict], pointers_per_type: int, testnum_iter
) -> tuple[list[list[str]], int]:
    """Generate pointers and write them to DynamoDB in batches."""
    counter = 0
    pointer_data: list[list[str]] = []
    batch_upsert_items: list[dict[str, Any]] = []

    for (pointer_type, template), custodian in (
        (item, cust) for item in templates.items() for cust in CUSTODIANS
    ):
        batch_items, csv_rows, counter = _generate_pointers_for_custodian(
            template,
            pointer_type,
            custodian,
            pointers_per_type,
            counter,
            testnum_iter,
        )

        pointer_data.extend(csv_rows)

        for item in batch_items:
            batch_upsert_items.append(item)
            if len(batch_upsert_items) >= 25:
                _write_batch_to_dynamodb(table_name, batch_upsert_items)
                batch_upsert_items = []

    _write_batch_to_dynamodb(table_name, batch_upsert_items)

    return pointer_data, counter


def seed_sandbox_table(
    table_name: str,
    pointers_per_type: int = 2,
    force: bool = False,
    write_csv: bool = True,
):
    """
    Seed a sandbox table with realistic pointer data.

    Args:
        table_name: Name of the DynamoDB table to seed
        pointers_per_type: Number of pointers per type per custodian (default: 2)
        force: If True, overwrite existing sandbox pointers without prompting (default: False)
        write_csv: If True, write pointer data to CSV file (default: True)
    """
    print(
        f"Seeding table {table_name} with {pointers_per_type} pointers per type per custodian"
    )
    print(f"Total pointer types: {len(SAMPLE_TEMPLATES)}")
    print(f"Total custodians: {len(CUSTODIANS)}")
    print(
        f"Total pointers to create: {len(SAMPLE_TEMPLATES) * len(CUSTODIANS) * pointers_per_type}"
    )

    table = _validate_table_access(table_name)
    _check_for_existing_sandbox_pointers(table, force)

    testnum_cls = TestNhsNumbersIterator()
    testnum_iter = iter(testnum_cls)

    start_time = datetime.now(tz=timezone.utc)

    templates = _load_pointer_templates()
    pointer_data, total_attempts = _generate_and_write_pointers(
        table_name, templates, pointers_per_type, testnum_iter
    )

    print("\n✓ Done!")

    end_time = datetime.now(tz=timezone.utc)
    duration = (end_time - start_time).total_seconds()

    total_pointers_created = len(pointer_data)
    print(
        f"\nAttempted {total_attempts} pointers, successfully created {total_pointers_created}"
    )

    if total_attempts > total_pointers_created:
        failed = total_attempts - total_pointers_created
        print(f"⚠️  {failed} pointer(s) failed to create")

    print(f"Completed in {duration:.2f} seconds")
    if duration > 0:
        print(f"Average: {total_pointers_created/duration:.2f} pointers/second")

    if write_csv:
        try:
            _write_pointer_extract(pointer_data)
        except Exception as e:
            print(f"Warning: Failed to write CSV extract: {e}")

    return {
        "successful": total_pointers_created,
        "attempted": total_attempts,
        "failed": total_attempts - total_pointers_created,
    }


def _write_pointer_extract(pointer_data: list[list[str]]):
    try:
        output_dir = Path(__file__).parent.parent / "dist" / "sandbox"
        output_dir.mkdir(parents=True, exist_ok=True)

        csv_file = (
            output_dir
            / f"sandbox-pointers-{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        with open(csv_file, "w") as f:
            writer = csv.writer(f)
            writer.writerow(["pointer_id", "pointer_type", "custodian", "nhs_number"])
            writer.writerows(pointer_data)

        print(f"Pointer data saved to {csv_file}")
    except PermissionError:
        print(f"Error: Permission denied writing to {output_dir}")
        raise
    except Exception as e:
        print(f"Error writing CSV file: {e}")
        raise


if __name__ == "__main__":
    if fire is None:
        print("Error: fire module not available")
        sys.exit(1)
    fire.Fire(seed_sandbox_table)
