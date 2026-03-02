# flake8: noqa: T201

import json
import os

from scripts.delete_all_table_items import delete_all_table_items
from scripts.seed_sandbox_table import seed_sandbox_table


def handler(event, context):
    """
    Lambda handler that orchestrates the reset of specified pointer tables in the dev & test accounts, deleting all items and reseeding with fresh data .

    The tables to be reset and number of pointers per type can be specified in `terraform/account-wide-infrastructure/{env}/lambda__seed-sandbox.tf`

    """
    table_names_str = os.environ.get("TABLE_NAMES", "")
    pointers_per_type = int(os.environ.get("POINTERS_PER_TYPE", "2"))

    if not table_names_str:
        error_msg = "TABLE_NAMES environment variable is required"
        print(f"ERROR: {error_msg}")
        return {"statusCode": 500, "body": json.dumps({"error": error_msg})}

    table_names = [name.strip() for name in table_names_str.split(",") if name.strip()]

    if not table_names:
        error_msg = "No valid table names provided in TABLE_NAMES"
        print(f"ERROR: {error_msg}")
        return {"statusCode": 500, "body": json.dumps({"error": error_msg})}

    print(
        f"Starting table reset for {len(table_names)} table(s): {', '.join(table_names)}"
    )
    print(f"Pointers per type: {pointers_per_type}")

    results = []
    failed_tables = []

    for table_name in table_names:
        print(f"\n{'='*60}")
        print(f"Processing table: {table_name}")
        print(f"{'='*60}")

        try:
            print("Step 1: Deleting all items from table...")
            pointers_deleted_count = delete_all_table_items(table_name=table_name)
            print(f"✓ Deleted {pointers_deleted_count} items")

            print("Step 2: Seeding table with fresh data...")
            seed_result = seed_sandbox_table(
                table_name=table_name,
                pointers_per_type=pointers_per_type,
                force=True,
                write_csv=False,
            )
            print(f"✓ Created {seed_result['successful']} pointers")

            results.append(
                {
                    "table_name": table_name,
                    "status": "success",
                    "pointers_deleted": pointers_deleted_count,
                    "pointers_created": seed_result["successful"],
                    "pointers_attempted": seed_result["attempted"],
                    "pointers_failed": seed_result["failed"],
                }
            )

        except Exception as e:
            error_msg = f"Failed to reset table {table_name}: {str(e)}"
            print(f"ERROR: {error_msg}")
            failed_tables.append(table_name)
            results.append(
                {
                    "table_name": table_name,
                    "status": "failed",
                    "error": str(e),
                }
            )

    if failed_tables:
        status_code = 500 if len(failed_tables) == len(table_names) else 207
        message = (
            f"Failed to reset {len(failed_tables)} table(s): {', '.join(failed_tables)}"
        )
    else:
        status_code = 200
        message = f"Successfully reset {len(table_names)} table(s)"

    result = {
        "statusCode": status_code,
        "body": json.dumps(
            {
                "message": message,
                "tables_processed": len(table_names),
                "tables_succeeded": len(table_names) - len(failed_tables),
                "tables_failed": len(failed_tables),
                "results": results,
                "pointers_per_type": pointers_per_type,
            }
        ),
    }

    print(f"\n{'='*60}")
    print(f"RESULT: {message}")
    print(f"{'='*60}")
    return result
