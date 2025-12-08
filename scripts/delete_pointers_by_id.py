#!/usr/bin/env python
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import boto3
import fire

dynamodb = boto3.client("dynamodb")


def _load_pointers_from_file(pointers_file: str) -> list[str]:
    """
    Read pointers from a file. Supports:
     - JSON array of objects with an "id" field
     - line-delimited plain text (one id per line)

    Returns a list of pointer id strings. Prints a warning for skipped malformed JSON entries.
    """
    with open(pointers_file, "r") as file:
        content = file.read().strip()

    if not content:
        return []

    if content.startswith("[") or content.startswith("{"):
        return _parse_json_pointers(content, pointers_file)

    return _parse_plain_text_pointers(content)


def _parse_json_pointers(content: str, pointers_file: str) -> list[str]:

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON file {pointers_file}: {e}") from e

    if not isinstance(data, list):
        raise ValueError("JSON file must contain an array of objects")

    parsed_ids: list[str] = []
    skipped_count = 0

    for item in data:
        if _is_valid_pointer(item):
            parsed_ids.append(item["id"].strip())
        else:
            skipped_count += 1

    if skipped_count:
        print(
            f"Warning: skipped {skipped_count} malformed entries in JSON file {pointers_file}"
        )

    return parsed_ids


def _is_valid_pointer(item: Any) -> bool:
    return (
        isinstance(item, dict)
        and "id" in item
        and isinstance(item["id"], str)
        and item["id"].strip()
    )


def _parse_plain_text_pointers(content: str) -> list[str]:
    return [line.strip() for line in content.splitlines() if line.strip()]


@dataclass
class PointerDeletionContext:
    pointers_to_delete: list[str]
    ods_code: str
    matched_pointers: list[str]
    mismatched_pointers: list[str]
    not_found_pointers: list[str]
    pointers_deleted: list[str]
    failed_deletes: list[str]
    start_time: datetime
    end_time: datetime
    output_filename: str


def _build_and_write_result(ctx: PointerDeletionContext) -> Dict[str, Any]:

    result = {
        "pointers_to_delete": len(ctx.pointers_to_delete),
        "ods_code": ctx.ods_code,
        "ods_code_matched": {
            "count": len(ctx.matched_pointers),
            "ids": ctx.matched_pointers,
        },
        "ods_code_mismatched": {
            "count": len(ctx.mismatched_pointers),
            "ids": ctx.mismatched_pointers,
        },
        "pointer_not_found": {
            "count": len(ctx.not_found_pointers),
            "ids": ctx.not_found_pointers,
        },
        "deleted_pointers": {
            "count": len(ctx.pointers_deleted),
            "ids": ctx.pointers_deleted,
        },
        "failed_deletes": {"count": len(ctx.failed_deletes), "ids": ctx.failed_deletes},
        "deletes-took-secs": timedelta.total_seconds(ctx.end_time - ctx.start_time),
        "output_filename": ctx.output_filename,
    }

    script_dir = os.path.dirname(os.path.abspath(__file__)) or "."
    output_file_path = os.path.join(script_dir, ctx.output_filename)

    try:
        _write_result_file(result, output_file_path)
    except Exception as exc:
        result["_output_error"] = (
            f"Failed to write result file {ctx.output_filename}: {exc}"
        )
    _print_summary(result)
    return result


def _write_result_file(result: Dict[str, Any], output_file: str) -> None:

    out_dir = os.path.dirname(os.path.abspath(output_file)) or "."
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=out_dir, prefix=".tmp_delete_results_", suffix=".json"
    ) as tf:
        json.dump(result, tf, indent=2)
        tf.flush()
        os.fsync(tf.fileno())
    os.replace(tf.name, output_file)


def _print_summary(result: Dict[str, Any]) -> None:

    def count_from(field):
        val = result.get(field)
        if isinstance(val, dict):
            return val.get("count", 0)
        if isinstance(val, list):
            return len(val)
        return 0

    print("*******************************************************")
    print("Summary:")
    print(f"  pointers_to_delete: {result.get('pointers_to_delete')}")
    print(f"  ods_code_matched:   {count_from('ods_code_matched')}")
    print(f"  ods_code_mismatched:{count_from('ods_code_mismatched')}")
    print(f"  pointer_not_found:  {count_from('pointer_not_found')}")
    print(f"  deleted_pointers:   {count_from('deleted_pointers')}")
    print(f"  failed_deletes:     {count_from('failed_deletes')}")
    if "deletes-took-secs" in result:
        print(f"  deletes-took-secs:  {result.get('deletes-took-secs')}")

    if "_output_error" in result:
        print(f"  output_error:       {result['_output_error']}")
    elif "output_filename" in result:
        print(f"  See output file for full results:  {result.get('output_filename')}")
    print("*******************************************************")


def _check_pointers_match_ods_code(
    ods_code: str, pointer_ids: List[str]
) -> tuple[List[str], List[str]]:

    matched = []
    mismatched = []

    for pointer_id in pointer_ids:
        if pointer_id.startswith(f"{ods_code}-"):
            matched.append(pointer_id)
        else:
            mismatched.append(pointer_id)

    return matched, mismatched


def _batch_get_existing_pointers(
    table_name: str, pointer_ids: List[str]
) -> tuple[List[str], List[str]]:
    """
    Check which pointers exist using BatchGetItem (max 100 items per request).
    Returns (existing_ids, not_found_ids)
    """
    existing = []
    not_found = []

    for batch_idx in range(0, len(pointer_ids), 100):
        batch_ids = pointer_ids[batch_idx : batch_idx + 100]

        keys = [
            {
                "pk": {"S": f"D#{pointer_id}"},
                "sk": {"S": f"D#{pointer_id}"},
            }
            for pointer_id in batch_ids
        ]

        response = dynamodb.batch_get_item(RequestItems={table_name: {"Keys": keys}})

        found_ids = {
            item["pk"]["S"][2:]
            for item in response.get("Responses", {}).get(table_name, [])
        }

        for pointer_id in batch_ids:
            if pointer_id in found_ids:
                existing.append(pointer_id)
            else:
                not_found.append(pointer_id)

    return existing, not_found


def _batch_delete_pointers(
    table_name: str, pointer_ids: List[str]
) -> tuple[List[str], List[str]]:
    """
    Delete pointers using BatchWriteItem (max 25 items per request).
    """
    pointers_deleted = []
    failed_deletes_set: set[str] = set()

    for _batch_id in range(0, len(pointer_ids), 25):
        batch_ptrs = pointer_ids[_batch_id : _batch_id + 25]

        batch = [
            {
                "DeleteRequest": {
                    "Key": {
                        "pk": {"S": f"D#{pointer_id}"},
                        "sk": {"S": f"D#{pointer_id}"},
                    }
                }
            }
            for pointer_id in batch_ptrs
        ]

        result = dynamodb.batch_write_item(RequestItems={table_name: batch})
        unprocessed = result.get("UnprocessedItems", {}).get(table_name, [])

        # Collect unprocessed IDs
        for item in unprocessed:
            pk_val = item["DeleteRequest"]["Key"]["pk"]["S"]
            failed_deletes_set.add(pk_val[2:])  # Remove "D#"

        # Only count successfully deleted items (batch size minus unprocessed)
        successfully_deleted = [p for p in batch_ptrs if p not in failed_deletes_set]
        pointers_deleted.extend(successfully_deleted)

        if len(pointers_deleted) % 1000 == 0 and len(pointers_deleted) > 0:
            print(".", end="", flush=True)

    return pointers_deleted, sorted(failed_deletes_set)


def _delete_pointers_by_id(
    table_name: str,
    ods_code: str,
    pointers_to_delete: list[str] | None = None,
    pointers_file: str | None = None,
) -> None:
    """
    Delete DynamoDB pointers by ID with ODS code validation.

    REQUIRED: Provide either --pointers_to_delete OR --pointers_file (but not both)

    Can accept pointers as:
    - list of strings: --pointers_to_delete '["ABC123-12345678910", "ABC123-109876543210"]'
    - JSON file: --pointers_file /path/to/pointers.json (array of objects with "id" field)
    - text file: --pointers_file /path/to/ids.txt (one id per line)

    Args:
        table_name: DynamoDB table name
        ods_code: ODS code to validate pointer IDs against
        pointers_to_delete: List of pointer IDs as JSON string
        pointers_file: Path to file containing pointer IDs
    """
    if pointers_to_delete is None and pointers_file is None:
        raise ValueError("Must provide either --pointers_to_delete or --pointers_file")

    if pointers_to_delete is not None and pointers_file is not None:
        raise ValueError("Cannot provide both --pointers_to_delete and --pointers_file")

    if pointers_file:
        pointers_to_delete = _load_pointers_from_file(pointers_file)

    start_time = datetime.now(tz=timezone.utc)
    timestamp = start_time.strftime("%Y%m%dT%H%M%SZ")
    output_filename = f"delete_results_{ods_code}_{timestamp}.json"

    if not pointers_to_delete:
        end_time = datetime.now(tz=timezone.utc)
        _build_and_write_result(
            PointerDeletionContext(
                pointers_to_delete=pointers_to_delete,
                ods_code=ods_code,
                matched_pointers=[],
                mismatched_pointers=[],
                not_found_pointers=[],
                pointers_deleted=[],
                failed_deletes=[],
                start_time=start_time,
                end_time=end_time,
                output_filename=output_filename,
            )
        )
        return

    print(
        f"Validating {len(pointers_to_delete)} pointers against ODS code {ods_code}..."
    )
    matched_pointers, mismatched_pointers = _check_pointers_match_ods_code(
        ods_code, pointers_to_delete
    )

    print(
        f"Validate pointer's ODS code: {len(matched_pointers)} matched, {len(mismatched_pointers)} mismatched"
    )

    if not matched_pointers:
        print(f"None of the pointer IDs are a match for ODS code {ods_code}. Exiting.")
        end_time = datetime.now(tz=timezone.utc)
        _build_and_write_result(
            PointerDeletionContext(
                pointers_to_delete=pointers_to_delete,
                ods_code=ods_code,
                matched_pointers=matched_pointers,
                mismatched_pointers=mismatched_pointers,
                not_found_pointers=[],
                pointers_deleted=[],
                failed_deletes=[],
                start_time=start_time,
                end_time=end_time,
                output_filename=output_filename,
            )
        )
        return

    print(f"Checking existence of {len(matched_pointers)} pointers in {table_name}...")
    existing_pointers, not_found_pointers = _batch_get_existing_pointers(
        table_name, matched_pointers
    )

    print(
        f"Found {len(existing_pointers)} existing pointers to delete, {len(not_found_pointers)} not found."
    )

    if not existing_pointers:
        print("No pointers found to delete. Exiting.")
        end_time = datetime.now(tz=timezone.utc)
        _build_and_write_result(
            PointerDeletionContext(
                pointers_to_delete=pointers_to_delete,
                ods_code=ods_code,
                matched_pointers=matched_pointers,
                mismatched_pointers=mismatched_pointers,
                not_found_pointers=not_found_pointers,
                pointers_deleted=[],
                failed_deletes=[],
                start_time=start_time,
                end_time=end_time,
                output_filename=output_filename,
            )
        )
        return

    # Proceed with deletion using BatchWriteItem
    pointers_deleted, failed_deletes = _batch_delete_pointers(
        table_name, existing_pointers
    )

    end_time = datetime.now(tz=timezone.utc)
    _build_and_write_result(
        PointerDeletionContext(
            pointers_to_delete=pointers_to_delete,
            ods_code=ods_code,
            matched_pointers=matched_pointers,
            mismatched_pointers=mismatched_pointers,
            not_found_pointers=not_found_pointers,
            pointers_deleted=pointers_deleted,
            failed_deletes=failed_deletes,
            start_time=start_time,
            end_time=end_time,
            output_filename=output_filename,
        )
    )
    print(" Done")


if __name__ == "__main__":
    fire.Fire(_delete_pointers_by_id)
