#!/usr/bin/env python3
"""
Merge two SBOMs together

packages, files, and relationships from new_sbom will be merged into existing_sbom
"""

import json
from pathlib import Path

import fire


def update_sbom(new_sbom, existing_sbom="sbom.spdx.json") -> None:
    with Path(new_sbom).open("r") as f:
        updates = json.load(f)

    with Path(existing_sbom).open("r") as f:
        sbom = json.load(f)

    sbom.setdefault("packages", []).extend(updates.setdefault("packages", []))
    sbom.setdefault("files", []).extend(updates.setdefault("files", []))
    sbom.setdefault("relationships", []).extend(updates.setdefault("relationships", []))

    with Path(existing_sbom).open("w") as f:
        json.dump(sbom, f)


if __name__ == "__main__":
    fire.Fire(update_sbom)
