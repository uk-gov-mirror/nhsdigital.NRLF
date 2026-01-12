import json
from pathlib import Path

from seed_data_constants import (
    DEFAULT_CUSTODIAN_DISTRIBUTIONS,
    DEFAULT_TYPE_DISTRIBUTIONS,
)


def expand_distribution(dist):
    arr = []
    for key, count in dist.items():
        arr.extend([key] * count)
    return arr


# Expand type distribution
expanded_types = expand_distribution(DEFAULT_TYPE_DISTRIBUTIONS)

# Expand custodian distributions for each type
expanded_custodians = {}
for type_code, custodian_dist in DEFAULT_CUSTODIAN_DISTRIBUTIONS.items():
    expanded_custodians[type_code] = expand_distribution(custodian_dist)

output = {"types": expanded_types, "custodians": expanded_custodians}

out_path = Path("./tests/performance/producer/expanded_pointer_distributions.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
with out_path.open("w") as f:
    json.dump(output, f, indent=2)

print(f"Expanded pointer distributions written to {out_path}")  # noqa: T201
