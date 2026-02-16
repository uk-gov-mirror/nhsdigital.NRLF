REPO_ROOT=$(git rev-parse --show-toplevel)

syft -o spdx-json . > sbom.spdx.json

ASDF_SBOM="sbom-asdf.spdx.json"

poetry run python "$REPO_ROOT/scripts/sbom_from_asdf.py" $ASDF_SBOM

poetry run python "$REPO_ROOT/scripts/sbom_update.py" $ASDF_SBOM "sbom.spdx.json"
