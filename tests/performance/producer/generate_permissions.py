import json
from pathlib import Path

import fire
from seed_nft_tables import DEFAULT_CUSTODIAN_DISTRIBUTIONS


def main(output_dir="../../dist/nrlf_permissions/K6PerformanceTest"):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Invert the mapping: custodian -> list of pointer types
    custodian_permissions = {}
    for pointer_type, custodians in DEFAULT_CUSTODIAN_DISTRIBUTIONS.items():
        for custodian, _ in custodians.items():
            custodian_permissions.setdefault(custodian, []).append(pointer_type)

    for custodian, pointer_types in custodian_permissions.items():
        permissions = [f"http://snomed.info/sct|{pt}" for pt in pointer_types]
        out_path = output_dir / f"{custodian}.json"
        with out_path.open("w") as f:
            json.dump(permissions, f, indent=2)
        print(f"Wrote permissions for {custodian} to {out_path}")  # noqa: T201


if __name__ == "__main__":
    fire.Fire(main)
