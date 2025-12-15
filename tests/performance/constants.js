import { CATEGORY_TYPE_GROUPS } from "./type-category-mappings.js";

export const DEFAULT_TEST_RECORD = open(
  "../data/DocumentReference/Y05868-736253002-Valid.json"
);
export const ODS_CODE = "Y05868";
export const REFERENCE_DATA = JSON.parse(open("./reference-data.json"));
export const POINTER_DOCUMENTS =
  "documents" in REFERENCE_DATA ? REFERENCE_DATA["documents"] : {};
export const ALL_POINTER_IDS =
  "pointer_ids" in REFERENCE_DATA
    ? REFERENCE_DATA["pointer_ids"]
    : Object.keys(POINTER_DOCUMENTS);
export const POINTERS_TO_DELETE = ALL_POINTER_IDS.slice(0, 3500);
export const POINTER_IDS = ALL_POINTER_IDS.slice(3500);
export const NHS_NUMBERS = REFERENCE_DATA["nhs_numbers"];

// filter only 736253001, 736253002, 1363501000000100, 861421000000109, 749001000000101 for now
export const FILTERED_POINTER_TYPES = [
  "736253001",
  "736253002",
  "1363501000000100",
  "861421000000109",
  "749001000000101",
];

export const POINTER_TYPES = FILTERED_POINTER_TYPES;

export const CATEGORIES = CATEGORY_TYPE_GROUPS.map(
  (group) => group.category.code
);
export const POINTER_TYPE_DISPLAY = Object.fromEntries(
  CATEGORY_TYPE_GROUPS.flatMap((group) =>
    group.types.map((t) => [t.code, t.display])
  )
);
export const TYPE_CATEGORY_MAP = Object.fromEntries(
  CATEGORY_TYPE_GROUPS.flatMap((group) =>
    group.types.map((t) => [t.code, group.category.code])
  )
);
export const CATEGORY_DISPLAY = Object.fromEntries(
  CATEGORY_TYPE_GROUPS.map((group) => [
    group.category.code,
    group.category.display,
  ])
);
