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
export const POINTER_TYPES = [
  "736253002",
  "887701000000100",
  "861421000000109",
  "1382601000000107",
  "1363501000000100",
  "325691000000100",
  "736373009",
  "16521000000101",
  "736366004",
  "735324008",
  "824321000000109",
  "2181441000000107",
  "749001000000101",
  "887181000000106",
];

export const POINTER_TYPE_DISPLAY = {
  736253002: "Mental health crisis plan",
  887701000000100: "Emergency health care plan",
  861421000000109: "End of life care coordination summary",
  1382601000000107: "ReSPECT (Recommended Summary Plan for Emergency Care and Treatment) form",
  1363501000000100: "Royal College of Physicians NEWS2 (National Early Warning Score 2) chart",
  325691000000100: "Contingency plan",
  736373009: "End of life care plan",
  16521000000101: "Lloyd George record folder",
  736366004: "Advance care plan",
  735324008: "Treatment escalation plan",
  824321000000109: "Summary record",
  2181441000000107: "Personalised Care and Support Plan",
  749001000000101: "Appointment",
  887181000000106: "Clinical summary",
};

export const CATEGORIES = [
  "734163000",
  "1102421000000108",
  "823651000000106",
  "419891008",
  "716931000000107",
];

export const CATEGORY_DISPLAY = {
  734163000: "Care plan",
  1102421000000108: "Observations",
  823651000000106: "Clinical note",
  419891008: "Record artifact",
  716931000000107: "Record headings",
};

export const TYPE_CATEGORY_MAP = {
  // Care plans
  736253002: "734163000",
  887701000000100: "734163000",
  861421000000109: "734163000",
  1382601000000107: "734163000",
  325691000000100: "734163000",
  736373009: "734163000",
  16521000000101: "734163000",
  736366004: "734163000",
  735324008: "734163000",
  2181441000000107: "734163000",

  // Observations
  1363501000000100: "1102421000000108",

  // Clinical notes
  824321000000109: "823651000000106",

  // Bookings and Referrals
  749001000000101: "419891008",

  // Shared Care Records
  887181000000106: "716931000000107",
};
