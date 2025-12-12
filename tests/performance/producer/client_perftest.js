import http from "k6/http";
import { ODS_CODE } from "../constants.js";
import { check } from "k6";
import { randomItem } from "https://jslib.k6.io/k6-utils/1.2.0/index.js";
import { crypto } from "k6/experimental/webcrypto";
import { createRecord } from "../setup.js";
import exec from "k6/execution";

// Parse CSV for deterministic pointer iteration
const csv = open("../producer_reference_data.csv");
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
  // Adjust field names as per CSV columns: count,pointer_id,pointer_type,custodian,nhs_number
  const [count, pointer_id, pointer_type, custodian, nhs_number] = line
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

function generateValidNHSNumber(first9) {
  const first9Str = String(first9).padStart(9, "0");

  if (first9Str.match(/^\d{9}$/)) {
    throw new Error(
      "bad NHS number generated - expected 9 digits",
      first9Str,
      first9
    );
  }

  // NHS numbers not validated, checksum doesn't need to be legit
  return `${first9Str}${"1"}`;
}

function pickNHSNumber() {
  if (Math.random() < ReuseNHSNumbersRatio) {
    // Reuse: pick within [NHSNumberStart, NHSNumberEnd]
    const first9 = randomNHSNumberInRange(NHSNumberStart, NHSNumberEnd);
    return generateValidNHSNumber(first9);
  } else {
    // New: always pick from [NHSNumberEnd + 1, NHS_NUMBER_MAX]
    const first9 = randomNHSNumberInRange(NHSNumberEnd + 1, NHS_NUMBER_MAX);
    return generateValidNHSNumber(first9);
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

function getBaseURL() {
  return `https://${__ENV.HOST}/producer/DocumentReference`;
}

function getHeaders(odsCode = ODS_CODE) {
  return {
    "Content-Type": "application/fhir+json",
    "X-Request-Id": `K6perftest-producer-${exec.scenario.name}-${exec.vu.idInTest}-${exec.vu.iterationInScenario}`,
    "NHSD-Correlation-Id": `K6perftest-producer-${exec.scenario.name}-${exec.vu.idInTest}-${exec.vu.iterationInScenario}`,
    "NHSD-Connection-Metadata": JSON.stringify({
      "nrl.ods-code": odsCode,
      "nrl.app-id": "K6PerformanceTest",
    }),
    "NHSD-Client-RP-Details": JSON.stringify({
      "developer.app.name": "K6PerformanceTest",
      "developer.app.id": "K6PerformanceTest",
    }),
  };
}
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
  const res = http.post(getBaseURL(), JSON.stringify(record), {
    headers: getHeaders(custodian),
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
  const res = http.get(`${getBaseURL()}/${pointer_id}`, {
    headers: getHeaders(custodian),
  });
  checkResponse(res);
}

export function createThenReadDocumentReference() {
  const nhsNumber = pickNHSNumber();
  const pointerType = pickPointerType();
  const custodian = pickCustodian(pointerType);
  const record = createRecord(nhsNumber, pointerType, custodian);
  const createRes = http.post(getBaseURL(), JSON.stringify(record), {
    headers: getHeaders(custodian),
  });
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

  const readRes = http.get(`${getBaseURL()}/${createdId}`, {
    headers: getHeaders(custodian),
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
  const upsertRes = http.put(getBaseURL(), JSON.stringify(record), {
    headers: getHeaders(custodian),
  });
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

  const readRes = http.get(`${getBaseURL()}/${upsertedId}`, {
    headers: getHeaders(custodian),
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
  const createRes = http.post(getBaseURL(), JSON.stringify(record), {
    headers: getHeaders(custodian),
  });
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

  const updateRes = http.put(
    `${getBaseURL()}/${createdId}`,
    JSON.stringify(record),
    {
      headers: getHeaders(custodian),
    }
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
  const upsertRes = http.put(getBaseURL(), JSON.stringify(record), {
    headers: getHeaders(custodian),
  });
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

  const updateRes = http.put(
    `${getBaseURL()}/${upsertedId}`,
    JSON.stringify(record),
    {
      headers: getHeaders(custodian),
    }
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
  const res = http.put(getBaseURL(), JSON.stringify(record), {
    headers: getHeaders(custodian),
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
  const url = `${getBaseURL()}?subject:identifier=${identifier}&type=${type}`;
  const res = http.get(url, {
    headers: getHeaders(custodian),
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
  const res = http.post(`${getBaseURL()}/_search`, body, {
    headers: getHeaders(custodian),
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
