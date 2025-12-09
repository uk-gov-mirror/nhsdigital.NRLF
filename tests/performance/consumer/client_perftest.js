import http from "k6/http";
import { check } from "k6";
import exec from "k6/execution";
import { CATEGORY_TYPE_GROUPS } from "../type-category-mappings.js";

const csv = open("../producer_reference_data.csv");
const lines = csv.trim().split("\n");
// Skip header
const dataLines = lines.slice(1);

function getNextPointer() {
  // pick the next line accoording to iteration in scenario
  const iter = exec.vu.iterationInScenario;
  const index = iter % dataLines.length;
  const line = dataLines[index];
  const [count, pointer_id, pointer_type, custodian, nhs_number] = line
    .split(",")
    .map((field) => field.trim());
  return { pointer_id, pointer_type, nhs_number };
}

function getHeaders(odsCode) {
  return {
    "Content-Type": "application/fhir+json",
    "X-Request-Id": `K6perftest-consumer-${exec.scenario.name}-${exec.vu.idInTest}-${exec.vu.iterationInScenario}`,
    "NHSD-Correlation-Id": `K6perftest-consumer-${exec.scenario.name}-${exec.vu.idInTest}-${exec.vu.iterationInScenario}`,
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

function getCustodianFromPointerId(pointer_id) {
  // pointer_id format is "CUSTODIAN-XXXX"
  return pointer_id.split("-")[0];
}

function checkResponse(res) {
  const is_success = check(res, { "status is 200": (r) => r.status === 200 });
  if (!is_success) {
    console.warn(res.json());
  }
}

const pointerTypeToCategoryMap = new Map();
for (const group of CATEGORY_TYPE_GROUPS) {
  for (const type of group.types) {
    pointerTypeToCategoryMap.set(type.code, group.category.code);
  }
}

export function countDocumentReference() {
  const { pointer_id, nhs_number } = getNextPointer();
  const custodian = getCustodianFromPointerId(pointer_id);
  const identifier = encodeURIComponent(
    `https://fhir.nhs.uk/Id/nhs-number|${nhs_number}`
  );
  const res = http.get(
    `https://${__ENV.HOST}/consumer/DocumentReference?_summary=count&subject:identifier=${identifier}`,
    {
      headers: getHeaders(custodian),
    }
  );
  checkResponse(res);
}

export function readDocumentReference() {
  const { pointer_id } = getNextPointer();
  const custodian = getCustodianFromPointerId(pointer_id);

  const res = http.get(
    `https://${__ENV.HOST}/consumer/DocumentReference/${pointer_id}`,
    {
      headers: getHeaders(custodian),
    }
  );

  checkResponse(res);
}

export function searchDocumentReference() {
  const { pointer_id, pointer_type, nhs_number } = getNextPointer();
  const custodian = getCustodianFromPointerId(pointer_id);

  const identifier = encodeURIComponent(
    `https://fhir.nhs.uk/Id/nhs-number|${nhs_number}`
  );
  const type = encodeURIComponent(`http://snomed.info/sct|${pointer_type}`);

  const res = http.get(
    `https://${__ENV.HOST}/consumer/DocumentReference?subject:identifier=${identifier}&type=${type}`,
    {
      headers: getHeaders(custodian),
    }
  );
  checkResponse(res);
}

export function searchDocumentReferenceByCategory() {
  const { pointer_id, pointer_type, nhs_number } = getNextPointer();
  const custodian = getCustodianFromPointerId(pointer_id);
  const category_code = pointerTypeToCategoryMap.get(pointer_type);

  const identifier = encodeURIComponent(
    `https://fhir.nhs.uk/Id/nhs-number|${nhs_number}`
  );
  const category = encodeURIComponent(
    `http://snomed.info/sct|${category_code}`
  );

  const res = http.get(
    `https://${__ENV.HOST}/consumer/DocumentReference?subject:identifier=${identifier}&category=${category}`,
    {
      headers: getHeaders(custodian),
    }
  );
  checkResponse(res);
}

export function searchPostDocumentReference() {
  const { pointer_id, pointer_type, nhs_number } = getNextPointer();
  const custodian = getCustodianFromPointerId(pointer_id);

  const body = JSON.stringify({
    "subject:identifier": `https://fhir.nhs.uk/Id/nhs-number|${nhs_number}`,
    type: `http://snomed.info/sct|${pointer_type}`,
  });

  const res = http.post(
    `https://${__ENV.HOST}/consumer/DocumentReference/_search`,
    body,
    {
      headers: getHeaders(custodian),
    }
  );
  checkResponse(res);
}

export function searchPostDocumentReferenceByCategory() {
  const { pointer_id, pointer_type, nhs_number } = getNextPointer();
  const custodian = getCustodianFromPointerId(pointer_id);
  const category_code = pointerTypeToCategoryMap.get(pointer_type);

  const body = JSON.stringify({
    "subject:identifier": `https://fhir.nhs.uk/Id/nhs-number|${nhs_number}`,
    category: `http://snomed.info/sct|${category_code}`,
  });

  const res = http.post(
    `https://${__ENV.HOST}/consumer/DocumentReference/_search`,
    body,
    {
      headers: getHeaders(custodian),
    }
  );
  checkResponse(res);
}

export function countPostDocumentReference() {
  const { pointer_id, nhs_number } = getNextPointer();
  const custodian = getCustodianFromPointerId(pointer_id);

  const body = JSON.stringify({
    "subject:identifier": `https://fhir.nhs.uk/Id/nhs-number|${nhs_number}`,
  });
  const res = http.post(
    `https://${__ENV.HOST}/consumer/DocumentReference/_search?_summary=count`,
    body,
    {
      headers: getHeaders(custodian),
    }
  );
  checkResponse(res);
}

export function searchPostDocumentReferenceAccessDenied() {
  const { nhs_number, pointer_type } = getNextPointer();

  const body = JSON.stringify({
    "subject:identifier": `https://fhir.nhs.uk/Id/nhs-number|${nhs_number}`,
    type: `http://snomed.info/sct|${pointer_type}`,
  });

  // Use a custodian that should not have access (simulate denied)
  const deniedCustodian = "DENIED_ODS_CODE";
  let headers = getHeaders(deniedCustodian);
  headers["NHSD-Connection-Metadata"] = JSON.stringify({
    "nrl.ods-code": deniedCustodian,
    "nrl.app-id": "K6PerformanceTest",
  });
  const res = http.post(
    `https://${__ENV.HOST}/consumer/DocumentReference/_search`,
    body,
    {
      headers: headers,
    }
  );

  const is_denied = check(res, { "status is 403": (r) => r.status === 403 });
  if (!is_denied) {
    console.warn(`Expected access denied but got: ${res.status}`);
  }
}

export function readDocumentReferenceNotFound() {
  const { custodian } = getNextPointer();

  const res = http.get(
    `https://${__ENV.HOST}/consumer/DocumentReference/NonExistentID`,
    {
      headers: getHeaders(custodian),
    }
  );

  // we expect a 404 here
  check(res, { "status is 404": (r) => r.status === 404 });
}
