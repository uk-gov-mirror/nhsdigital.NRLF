REPO_ROOT=$(git rev-parse --show-toplevel)

syft -o spdx-json . > sbom.spdx.json

# for tool in "$@"; do
#   echo "Creating SBOM for $tool and merging"
#   # syft -q -o spdx-json "$(which "$tool")" | python "$REPO_ROOT/scripts/sbom-update.py"
#   syft -q -o spdx-json "$(which "$tool")"
# done
