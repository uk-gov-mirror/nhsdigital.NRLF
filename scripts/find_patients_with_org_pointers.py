import json
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
import fire

from nrlf.consumer.fhir.r4.model import DocumentReference
from nrlf.core.constants import PointerTypes
from nrlf.core.logger import logger

type PatientCounter = dict[int, int]
type TypePatientCounter = dict[str, PatientCounter]
type OrgTypePatientCounter = dict[str, TypePatientCounter]

dynamodb = boto3.client("dynamodb")
paginator = dynamodb.get_paginator("scan")

logger.setLevel("ERROR")

type_to_name = {pointer_type.value: pointer_type.name for pointer_type in PointerTypes}


def _find_patients(
    table_name: str,
    number_of_patients: int = 1,
    number_of_pointers: int = 1,
    org_ods_code: str = "X26",
    pointer_type: str = PointerTypes.MENTAL_HEALTH_PLAN.value,
) -> dict[str, float | int]:

    print(f"Looking for {number_of_patients} patient(s)")  # noqa
    print(f"  with {number_of_pointers} or more pointers")  # noqa
    print(f"  of type {type_to_name[pointer_type]} ")  # noqa
    print(f"  produced by org {org_ods_code}")  # noqa
    print(f"  in table {table_name}")  # noqa

    params: dict[str, Any] = {
        "TableName": table_name,
        "PaginationConfig": {"PageSize": 50},
    }

    total_scanned_count = 0

    start_time = datetime.now(tz=timezone.utc)

    found_patients: set[str] = set()
    patient_counters: dict[str, Any] = {}

    for page in paginator.paginate(**params):
        for item in page["Items"]:
            document = item.get("document", {}).get("S", "")
            # TODO - Dont need to use doc for these attrs - switch to other attrs

            # Do validations
            try:
                docref = DocumentReference.model_validate_json(document)
            except Exception:
                continue

            patient_number = (
                docref.subject.identifier.value
                if docref.subject
                and docref.subject.identifier
                and docref.subject.identifier.value
                else "unknown"
            )
            producer = (
                docref.custodian.identifier.value
                if docref.custodian
                and docref.custodian.identifier
                and docref.custodian.identifier.value
                else "unknown"
            )
            type_coding = (
                docref.type.coding[0] if docref.type and docref.type.coding else None
            )
            type_str = (
                f"{type_coding.system}|{type_coding.code}" if type_coding else "unknown"
            )

            if producer != org_ods_code or type_str != pointer_type:
                continue

            patient_counters[patient_number] = (
                patient_counters.get(patient_number, 0) + 1
            )

            if patient_counters[patient_number] >= number_of_pointers:
                found_patients.add(patient_number)

        if len(found_patients) >= number_of_patients:
            print(f"Found {len(found_patients)} patients")
            break

        total_scanned_count += page["ScannedCount"]

        if total_scanned_count % 1000 == 0:
            print(".", end="", flush=True)  # noqa

        if total_scanned_count % 100000 == 0:
            print(f"scanned={total_scanned_count}")  # noqa

    end_time = datetime.now(tz=timezone.utc)

    print("Done")  # noqa

    return {
        "scanned_count": total_scanned_count,
        "took-secs": timedelta.total_seconds(end_time - start_time),
        "patients": str(found_patients),
    }


if __name__ == "__main__":
    fire.Fire(_find_patients)
