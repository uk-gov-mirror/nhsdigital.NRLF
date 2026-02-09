REPO_ROOT=$(git rev-parse --show-toplevel)

syft -o spdx-json . > sbom.spdx.json

poetry run python "$REPO_ROOT/scripts/sbom_from_asdf.py" | poetry run python "$REPO_ROOT/scripts/sbom_update.py"
