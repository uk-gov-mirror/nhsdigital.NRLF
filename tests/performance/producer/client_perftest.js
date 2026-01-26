import http from "k6/http";
import { ODS_CODE } from "../constants.js";
import { check } from "k6";
import { randomItem } from "https://jslib.k6.io/k6-utils/1.2.0/index.js";
import { crypto } from "k6/experimental/webcrypto";
import { createRecord } from "../setup.js";
import { getHeaders, getFullUrl } from "../test-config.js";
import exec from "k6/execution";

const distPath = __ENV.DIST_PATH || "./dist";
const csvPath = `../../../${distPath}/nft/seed-pointers-extract.csv`;
const csv = open(csvPath);
const lines = csv.trim().split("\n");
// Skip header
const dataLines = lines.slice(1);

let pointerDist;
let pickPointerType, pickCustodian;

const referenceData = JSON.parse(open("./producer_reference_data.json"));
const NHSNumberStart = referenceData.NHSNumberStart;
const NHSNumberEnd = referenceData.NHSNumberEnd;
const ReuseNHSNumbersRatio = referenceData.ReuseNHSNumbersRatio || 0.8;
const MinimumFreeNHSNumbers = referenceData.MinimumFreeNHSNumbers || 100000;

const NHS_NUMBER_MIN = 0;
const NHS_NUMBER_MAX = 9999999999;

// Check if NHSNumberEnd is too close to max
if (NHS_NUMBER_MAX - NHSNumberEnd < MinimumFreeNHSNumbers) {
  throw new Error(
    `NHSNumberEnd (${NHSNumberEnd}) is too close to the maximum NHS number (${NHS_NUMBER_MAX}). Minimum free NHS numbers required: ${MinimumFreeNHSNumbers}`
  );
}

// Get next pointer data from CSV for current iteration
function getNextPointer() {
  // Use K6's iteration in scenario for deterministic selection
  const iter = exec.vu.iterationInScenario;
  const index = iter % dataLines.length;
  const line = dataLines[index];

  const [pointer_id, pointer_type, custodian, nhs_number] = line
    .split(",")
    .map((field) => field.trim());
  return { pointer_id, pointer_type, custodian, nhs_number };
}

function randomNHSNumberInRange(start, end) {
  // Inclusive range
  const range = end - start + 1;
  const rand = Math.floor(Math.random() * range);
  return start + rand;
}

function generateValidNHSNumber(start, end) {
  let nhsNumber = undefined;

  while (!nhsNumber) {
    const seedNumber = randomNHSNumberInRange(start, end);
    const first9Str = String(seedNumber).padStart(9, "0").substring(0, 9);

    if (!first9Str.match(/^\d{9}$/)) {
      throw new Error(
        `bad NHS number generated - expected 9 digits: ${first9Str}, ${seedNumber}`
      );
    }

    const parts = [];
    const digits = first9Str.split("");
    for (let i = 0; i < digits.length; i++) {
      parts.push(parseInt(digits[i], 10) * (10 - i));
    }
    const list_sum = parts.reduce((a, b) => a + b, 0);

    let checksum = 11 - (list_sum % 11);

    if (checksum === 10) {
      // Checksum of 10 means NHS number is invalid
      continue;
    }

    if (checksum === 11) {
      checksum = 0;
    }

    nhsNumber = `${first9Str}${checksum}`;
  }

  return nhsNumber;
}

function pickNHSNumber() {
  if (Math.random() < ReuseNHSNumbersRatio) {
    // Reuse: pick within [NHSNumberStart, NHSNumberEnd]
    return generateValidNHSNumber(NHSNumberStart, NHSNumberEnd);
  } else {
    // New: always pick from [NHSNumberEnd + 1, NHS_NUMBER_MAX]
    return generateValidNHSNumber(NHSNumberEnd + 1, NHS_NUMBER_MAX);
  }
}

// Load expanded pointer/custodian distributions
pointerDist = JSON.parse(open("./expanded_pointer_distributions.json"));
// Filter types to only those with a custodian array
pointerDist.types = pointerDist.types.filter(
  (type) => pointerDist.custodians[type]
);

pickPointerType = function () {
  return randomItem(pointerDist.types);
};
pickCustodian = function (typeCode) {
  const arr = pointerDist.custodians[typeCode];
  if (!arr) throw new Error(`No custodian array for type ${typeCode}`);
  return randomItem(arr);
};

function checkResponse(res) {
  const is_success = check(res, { "status is 200": (r) => r.status === 200 });
  if (!is_success) {
    console.warn(res.json());
  }
}

export function createDocumentReference() {
  const nhsNumber = pickNHSNumber();
  const pointerType = pickPointerType();
  const custodian = pickCustodian(pointerType);
  const record = createRecord(nhsNumber, pointerType, custodian);
  const path = "/DocumentReference";

  const res = http.post(getFullUrl(path, "producer"), JSON.stringify(record), {
    headers: getHeaders(custodian, "producer"),
  });

  check(res, { "create status is 201": (r) => r.status === 201 });
  if (res.status !== 201) {
    console.warn(
      `Failed to create record: ${res.status}: ${
        JSON.parse(res.body).issue[0].diagnostics
      }`
    );
  }
}

export function readDocumentReference() {
  const { pointer_id, custodian } = getNextPointer();
  const path = `/DocumentReference/${pointer_id}`;

  const res = http.get(getFullUrl(path, "producer"), {
    headers: getHeaders(custodian, "producer"),
  });

  checkResponse(res);
}

export function createThenReadDocumentReference() {
  const nhsNumber = pickNHSNumber();
  const pointerType = pickPointerType();
  const custodian = pickCustodian(pointerType);
  const record = createRecord(nhsNumber, pointerType, custodian);
  const createPath = "/DocumentReference";

  const createRes = http.post(
    getFullUrl(createPath, "producer"),
    JSON.stringify(record),
    { headers: getHeaders(custodian, "producer") }
  );

  check(createRes, { "create status is 201": (r) => r.status === 201 });
  if (createRes.status !== 201) {
    console.warn(
      `Failed to create record: ${createRes.status}: ${
        JSON.parse(createRes.body).issue[0].diagnostics
      }`
    );
    return;
  }

  // Get pointer ID from the location header
  const locationHeader = createRes.headers["Location"];
  const createdId = locationHeader
    ? locationHeader.split("/").pop()
    : record.id;
  const path = `/DocumentReference/${createdId}`;

  const readRes = http.get(getFullUrl(path, "producer"), {
    headers: getHeaders(custodian, "producer"),
  });

  check(readRes, { "create and read status is 200": (r) => r.status === 200 });
  if (readRes.status !== 200) {
    console.warn(
      `Failed to read record: ${readRes.status}: ${
        JSON.parse(readRes.body).issue[0].diagnostics
      }`
    );
  }
}

export function upsertThenReadDocumentReference() {
  const nhsNumber = pickNHSNumber();
  const pointerType = pickPointerType();
  const custodian = pickCustodian(pointerType);
  const record = createRecord(nhsNumber, pointerType, custodian);
  record.id = `${custodian}-${crypto.randomUUID()}`;
  const upsertPath = "/DocumentReference";

  const upsertRes = http.put(
    getFullUrl(upsertPath, "producer"),
    JSON.stringify(record),
    { headers: getHeaders(custodian, "producer") }
  );

  check(upsertRes, { "upsert status is 201": (r) => r.status === 201 });
  if (upsertRes.status !== 201) {
    console.warn(
      `Failed to upsert record: ${upsertRes.status}: ${
        JSON.parse(upsertRes.body).issue[0].diagnostics
      }`
    );
    return;
  }

  const upsertedId = record.id;
  const path = `/DocumentReference/${upsertedId}`;

  const readRes = http.get(getFullUrl(path, "producer"), {
    headers: getHeaders(custodian, "producer"),
  });

  check(readRes, { "upsert and read status is 200": (r) => r.status === 200 });
  if (readRes.status !== 200) {
    console.warn(
      `Failed to read record: ${upsertedId}, ${readRes.status}: ${
        JSON.parse(readRes.body).issue[0].diagnostics
      }`
    );
  }
}

export function createThenUpdateDocumentReference() {
  const nhsNumber = pickNHSNumber();
  const pointerType = pickPointerType();
  const custodian = pickCustodian(pointerType);
  const record = createRecord(nhsNumber, pointerType, custodian);
  const path = `/DocumentReference/${upsertedId}`;

  const createRes = http.post(
    getFullUrl(path, "producer"),
    JSON.stringify(record),
    { headers: getHeaders(custodian, "producer") }
  );

  check(createRes, {
    "createThenUpdateDocumentReference: create status is 201": (r) =>
      r.status === 201,
  });
  if (createRes.status !== 201) {
    console.warn(
      `Failed to create record: ${createRes.status}: ${
        JSON.parse(createRes.body).issue[0].diagnostics
      }`
    );
    return;
  }

  // Get pointer ID from the location header
  const locationHeader = createRes.headers["Location"];
  const createdId = locationHeader
    ? locationHeader.split("/").pop()
    : record.id;

  record.id = createdId;

  // Now update the record
  record.content[0].attachment.url = "https://example.com/k6-updated-url.pdf";
  const updatePath = `/DocumentReference/${createdId}`;

  const updateRes = http.put(
    getFullUrl(updatePath, "producer"),
    JSON.stringify(record),
    { headers: getHeaders(custodian, "producer") }
  );

  check(updateRes, {
    "createThenUpdateDocumentReference: update status is 200": (r) =>
      r.status === 200,
  });
  if (updateRes.status !== 200) {
    console.warn(
      `Failed to update record (createThenUpdateDocumentReference): ${
        updateRes.status
      }: ${JSON.parse(updateRes.body).issue[0].diagnostics}`
    );
  }
}

export function upsertThenUpdateDocumentReference() {
  const nhsNumber = pickNHSNumber();
  const pointerType = pickPointerType();
  const custodian = pickCustodian(pointerType);
  const record = createRecord(nhsNumber, pointerType, custodian);
  record.id = `${custodian}-${crypto.randomUUID()}`;
  const path = "/DocumentReference";

  const upsertRes = http.put(
    getFullUrl(path, "producer"),
    JSON.stringify(record),
    { headers: getHeaders(custodian, "producer") }
  );

  check(upsertRes, { "upsert status is 201": (r) => r.status === 201 });
  if (upsertRes.status !== 201) {
    console.warn(
      `Failed to upsert record: ${upsertRes.status}: ${
        JSON.parse(upsertRes.body).issue[0].diagnostics
      }`
    );
    return;
  }

  const upsertedId = record.id;

  // Now update the record
  record.content[0].attachment.url = "https://example.com/k6-updated-url.pdf";

  const updatePath = `/DocumentReference/${upsertedId}`;

  const updateRes = http.put(
    getFullUrl(updatePath, "producer"),
    JSON.stringify(record),
    { headers: getHeaders(custodian, "producer") }
  );

  check(updateRes, {
    "upsertThenUpdateDocumentReference: update status is 200": (r) =>
      r.status === 200,
  });
  if (updateRes.status !== 200) {
    console.warn(
      `Failed to update record (upsertThenUpdateDocumentReference): ${upsertedId}, ${
        updateRes.status
      }: ${JSON.parse(updateRes.body).issue[0].diagnostics}`
    );
  }
}

export function upsertDocumentReference() {
  const nhsNumber = pickNHSNumber();
  const pointerType = pickPointerType();
  const custodian = pickCustodian(pointerType);
  const record = createRecord(nhsNumber, pointerType, custodian);
  record.id = `${custodian}-k6perf-${crypto.randomUUID()}`;
  const path = "/DocumentReference";

  const res = http.put(getFullUrl(path, "producer"), JSON.stringify(record), {
    headers: getHeaders(custodian, "producer"),
  });

  check(res, { "create status is 201": (r) => r.status === 201 });
  if (res.status !== 201) {
    console.warn(
      `Failed to create record: ${res.status}: ${
        JSON.parse(res.body).issue[0].diagnostics
      }`
    );
  }
}

export function searchDocumentReference() {
  const { pointer_type, nhs_number, custodian } = getNextPointer();
  const identifier = encodeURIComponent(
    `https://fhir.nhs.uk/Id/nhs-number|${nhs_number}`
  );
  const type = encodeURIComponent(`http://snomed.info/sct|${pointer_type}`);
  const path = `/DocumentReference?subject:identifier=${identifier}&type=${type}`;

  const res = http.get(getFullUrl(path, "producer"), {
    headers: getHeaders(custodian, "producer"),
  });

  check(res, {
    "searchDocumentReference status is 200": (r) => r.status === 200,
  });
  if (res.status !== 200) {
    console.log(
      `Search failed with ${res.status}: ${JSON.stringify(res.body)}`
    );
  }
}

export function searchPostDocumentReference() {
  const { pointer_type, nhs_number, custodian } = getNextPointer();
  const body = JSON.stringify({
    "subject:identifier": `https://fhir.nhs.uk/Id/nhs-number|${nhs_number}`,
    type: `http://snomed.info/sct|${pointer_type}`,
  });
  const path = `/DocumentReference/_search`;

  const res = http.post(getFullUrl(path, "producer"), body, {
    headers: getHeaders(custodian, "producer"),
  });

  check(res, {
    "searchPostDocumentReference status is 200": (r) => r.status === 200,
  });
  if (res.status !== 200) {
    console.log(
      `Search failed with ${res.status}: ${JSON.stringify(res.body)}`
    );
  }
}
