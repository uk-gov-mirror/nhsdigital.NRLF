#!/usr/bin/env python3
"""Generate an SBOM-looking document for our asdf dependencies"""

import json
from pathlib import Path


def parse_tool_versions(file_path=".tool-versions"):
    tools = []

    if not Path(file_path).exists():
        return tools

    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) >= 2:
                tool_name = parts[0]
                version = parts[1]
                tools.append({"name": tool_name, "version": version})

    return tools


def generate_asdf_sbom(output_file="sbom-asdf.spdx.json"):
    tools = parse_tool_versions()

    print(f"Found {len(tools)} ASDF-managed tools")

    sbom = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "asdf-tools",
        "packages": [
            {
                "name": tool["name"],
                "SPDXID": f"SPDXRef-Package-asdf-{tool['name']}-{index}",
                "versionInfo": tool["version"],
                "supplier": "NOASSERTION",
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "sourceInfo": "ASDF-managed tool: acquired package info from /.tool-versions",
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "copyrightText": "NOASSERTION",
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": f"pkg:asdf/{tool['name']}@{tool['version']}",
                    }
                ],
            }
            for index, tool in enumerate(tools)
        ],
        "relationships": [
            {
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": f"SPDXRef-Package-asdf-{tool['name']}-{index}",
            }
            for index, tool in enumerate(tools)
        ],
    }

    with open(output_file, "w") as f:
        json.dump(sbom, f, indent=2)

    print(f"Generated SBOM with {len(tools)} ASDF-managed tools")
    return output_file


if __name__ == "__main__":
    generate_asdf_sbom()
