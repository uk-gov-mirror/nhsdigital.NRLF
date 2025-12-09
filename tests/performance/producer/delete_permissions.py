from pathlib import Path

import fire
from seed_nft_tables import DEFAULT_CUSTODIAN_DISTRIBUTIONS


def main(permissions_dir="../../dist/nrlf_permissions/K6PerformanceTest"):
    permissions_dir = Path(permissions_dir)
    # Collect all custodian codes from DEFAULT_CUSTODIAN_DISTRIBUTIONS
    custodian_codes = set()
    for custodians in DEFAULT_CUSTODIAN_DISTRIBUTIONS.values():
        custodian_codes.update(custodians.keys())

    # Delete only the files for these custodians
    for custodian in custodian_codes:
        file = permissions_dir / f"{custodian}.json"
        if file.exists():
            print(f"Deleting {file}")  # noqa: T201
            file.unlink()


if __name__ == "__main__":
    fire.Fire(main)
