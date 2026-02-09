import json
import sys
from pathlib import Path

import fire


def update_sbom(existing_sbom="sbom.spdx.json") -> None:
    with Path(existing_sbom).open("r") as f:
        sbom = json.load(f)

    tool = json.loads(sys.stdin.read())

    sbom.setdefault("packages", []).extend(tool.setdefault("packages", []))
    sbom.setdefault("files", []).extend(tool.setdefault("files", []))
    sbom.setdefault("relationships", []).extend(tool.setdefault("relationships", []))

    with Path(existing_sbom).open("w") as f:
        json.dump(sbom, f)


if __name__ == "__main__":
    fire.Fire(update_sbom)
