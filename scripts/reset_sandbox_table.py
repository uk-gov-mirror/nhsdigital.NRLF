#!/usr/bin/env python
"""
Resets a sandbox table by clearing all items and reseeding with fresh data

This script is for manual cli use to reset a sandbox table

There is a separate lambda function in place (../lambdas/seed_sandbox) which performs this same reset operation on a weekly schedule, but this script allows for on-demand resets without needing to wait for the scheduled job
"""
import sys

import fire
from delete_all_table_items import delete_all_table_items
from seed_sandbox_table import seed_sandbox_table


def reset_sandbox_table(table_name: str, pointers_per_type: int = 2):
    """
    Reset a sandbox table by clearing all items and reseeding with fresh data.

    Args:
        table_name: Name of the DynamoDB table to reset
        pointers_per_type: Number of pointers per type per custodian (default: 2)
    """
    print(f"=== Resetting Sandbox Table: {table_name} ===\n")

    print("Step 1: Deleting all existing items...")
    try:
        delete_all_table_items(table_name)
        print()
    except SystemExit as e:
        print("✗ Failed to delete items. Aborting reset.")
        sys.exit(e.code)
    except Exception as e:
        print(f"✗ Unexpected error during deletion: {e}")
        sys.exit(1)

    print("Step 2: Seeding with fresh pointer data...")
    try:
        result = seed_sandbox_table(table_name, pointers_per_type, force=True)
        print("\n=== ✓ Reset Complete ===")
        print(
            f"Table '{table_name}' has been reset with {result['successful']} fresh pointers"
        )
        if result["failed"] > 0:
            print(f"⚠️  {result['failed']} pointer(s) failed to create")
    except SystemExit as e:
        print("✗ Failed to seed table after deletion.")
        sys.exit(e.code)
    except Exception as e:
        print(f"✗ Unexpected error during seeding: {e}")
        sys.exit(1)


if __name__ == "__main__":
    fire.Fire(reset_sandbox_table)
