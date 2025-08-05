import json
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
import fire

from nrlf.consumer.fhir.r4.model import DocumentReference
from nrlf.core.constants import PointerTypes
from nrlf.core.logger import logger
from nrlf.core.validators import DocumentReferenceValidator

type PatientCounter = dict[int, int]
type TypePatientCounter = dict[str, PatientCounter]
type OrgTypePatientCounter = dict[str, TypePatientCounter]

dynamodb = boto3.client("dynamodb")
paginator = dynamodb.get_paginator("scan")

logger.setLevel("ERROR")

type_to_name = {pointer_type.value: pointer_type.name for pointer_type in PointerTypes}


def _calc_type_stats(producer: str, type_str: str, stats: dict[str, Any]) -> None:
    stats["type_counts"] = stats.get("type_counts", {})
    stats["type_counts"][type_str] = stats["type_counts"].get(type_str, 0) + 1

    stats["producer_by_type_counts"][producer] = stats["producer_by_type_counts"].get(
        producer, {}
    )
    stats["producer_by_type_counts"][producer][type_str] = (
        stats["producer_by_type_counts"][producer].get(type_str, 0) + 1
    )


def _calc_date_stats(created_on: str, stats: dict[str, Any]) -> None:
    month_created = created_on[:7] if created_on else "not-set"
    if month_created not in stats["created_by_month"]:
        stats["created_by_month"][month_created] = 1
    else:
        stats["created_by_month"][month_created] += 1


def _calc_patient_counters(
    patient_number: str, producer: str, type_str: str, patient_counters: dict[str, Any]
) -> None:
    if patient_number not in patient_counters:
        patient_counters[patient_number] = {
            "count": 1,
            "types": {type_str: 1},
            "orgs": {producer: {type_str: 1}},
        }
    else:
        patient_counters[patient_number]["count"] += 1
        patient_counters[patient_number]["types"][type_str] = (
            patient_counters[patient_number]["types"].get(type_str, 0) + 1
        )
        patient_counters[patient_number]["orgs"][producer] = patient_counters[
            patient_number
        ]["orgs"].get(producer, {})
        patient_counters[patient_number]["orgs"][producer][type_str] = (
            patient_counters[patient_number]["orgs"][producer].get(type_str, 0) + 1
        )


def _get_patient_stats(patient_counters: dict[str, Any]) -> dict[str, Any]:
    total_pointers = 0
    max_pointers = 0
    min_pointers = 0
    counts_with_pointers: PatientCounter = {}
    counts_with_types: TypePatientCounter = {}
    counts_with_orgs_types: OrgTypePatientCounter = {}

    for counters in patient_counters.values():
        count = counters["count"]

        total_pointers += count
        max_pointers = max(max_pointers, count)
        min_pointers = min(min_pointers, count) if min_pointers else count

        counts_with_pointers[count] = counts_with_pointers.get(count, 0) + 1

        for type, type_count in counters["types"].items():
            counts_with_types[type] = counts_with_types.get(type, {})
            counts_with_types[type][type_count] = (
                counts_with_types[type].get(type_count, 0) + 1
            )

        for org, types in counters["orgs"].items():
            counts_with_orgs_types[org] = counts_with_orgs_types.get(org, {})
            for type, type_count in types.items():
                counts_with_orgs_types[org][type] = counts_with_orgs_types[org].get(
                    type, {}
                )
                counts_with_orgs_types[org][type][type_count] = (
                    counts_with_orgs_types[org][type].get(type_count, 0) + 1
                )

    return {
        "avg_pointers_per_patient": (
            total_pointers / len(patient_counters) if patient_counters else 0
        ),
        "max_pointers_per_patient": max_pointers,
        "min_pointers_per_patient": min_pointers,
        "patient_counts_with_pointers": counts_with_pointers,
        "patient_counts_with_types": counts_with_types,
        "patient_counts_with_org_types": counts_with_orgs_types,
    }


def _scan_and_get_stats(
    table_name: str, report_output_file: str = ""
) -> dict[str, float | int]:
    """
    Calculate stats from the pointers table.
    Parameters:
    - table_name: The name of the pointers table to use.
    """
    params: dict[str, Any] = {
        "TableName": table_name,
        "PaginationConfig": {"PageSize": 50},
    }

    total_scanned_count = 0

    start_time = datetime.now(tz=timezone.utc)

    stats: dict[str, Any] = {
        "fails_model": 0,
        "fails_validation": 0,
        "total_pointers": 0,
        "type_counts": {},
        "producer_by_type_counts": {},
        "created_by_month": {},
        "patients_with_pointers": 0,
        "avg_pointers_per_patient": 0,
        "max_pointers_per_patient": 0,
        "min_pointers_per_patient": 0,
        "patient_counts_with_pointers": {},
        "patient_counts_with_types": {},
        "patient_counts_with_org_types": {},
    }

    patient_counters: dict[str, Any] = {}

    for page in paginator.paginate(**params):
        for item in page["Items"]:
            document = item.get("document", {}).get("S", "")
            created_on = item.get("created_on", {}).get("S", "")

            # Do validations
            try:
                docref = DocumentReference.model_validate_json(document)
            except Exception:
                stats["fails_model"] += 1
                continue

            result = DocumentReferenceValidator().validate(data=docref)
            if not result.is_valid:
                stats["fails_validation"] += 1

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

            _calc_type_stats(producer, type_str, stats)
            _calc_date_stats(created_on, stats)
            _calc_patient_counters(patient_number, producer, type_str, patient_counters)

        total_scanned_count += page["ScannedCount"]

        if total_scanned_count % 1000 == 0:
            print(".", end="", flush=True)  # noqa

        if total_scanned_count % 100000 == 0:
            print(f"scanned={total_scanned_count}")  # noqa

    end_time = datetime.now(tz=timezone.utc)

    stats["total_pointers"] = total_scanned_count
    stats["patients_with_pointers"] = len(patient_counters)
    stats["avg_pointers_per_patient"] = (
        total_scanned_count / stats["patients_with_pointers"]
        if stats["patients_with_pointers"] > 0
        else 0
    )

    patient_stats = _get_patient_stats(patient_counters)
    stats.update(patient_stats)

    print("Done")  # noqa

    if report_output_file:
        with open(report_output_file, "w") as f:
            json.dump(stats, f, indent=2)
        print(f"Stats saved to {report_output_file}")  # noqa

    return {
        "scanned_count": total_scanned_count,
        "took-secs": timedelta.total_seconds(end_time - start_time),
        "stats": json.dumps(stats, indent=2),
    }


if __name__ == "__main__":
    fire.Fire(_scan_and_get_stats)
