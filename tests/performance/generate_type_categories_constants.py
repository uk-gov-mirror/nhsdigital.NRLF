import json
import re

from nrlf.core.constants import CATEGORY_ATTRIBUTES, TYPE_ATTRIBUTES, TYPE_CATEGORIES


def extract_code(enum_val):
    return enum_val.split("|")[1]


def extract_category_code(enum_val):
    return enum_val.split("|")[1]


# Build mapping from category code to pointer types
category_type_groups = {}
for pt, cat in TYPE_CATEGORIES.items():
    category_code = extract_category_code(cat)
    pointer_code = extract_code(pt)
    pointer_display = TYPE_ATTRIBUTES[pt]["display"]
    category_display = CATEGORY_ATTRIBUTES[cat]["display"]

    if category_code not in category_type_groups:
        category_type_groups[category_code] = {
            "category": {"code": category_code, "display": category_display},
            "types": [],
        }
    category_type_groups[category_code]["types"].append(
        {"code": pointer_code, "display": pointer_display}
    )

# Convert to list for JS export
category_type_groups_list = list(category_type_groups.values())

js_content = f"export const CATEGORY_TYPE_GROUPS = {json.dumps(category_type_groups_list, indent=2)};\n"

# Remove quotes from keys
js_content = re.sub(r'"(\w+)":', r"\1:", js_content)

with open("./tests/performance/type-category-mappings.js", "w") as f:
    # Please note, that the linter/formatter likes to add commas at the end of the last items in objects/arrays.
    # I'm not adding the code to add those here as I don't think we need the extra complexity.
    f.write(js_content)
