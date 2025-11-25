import {
  POINTER_IDS,
  POINTER_TYPES,
  ODS_CODE,
  CATEGORIES,
} from "../constants.js";
import http from "k6/http";
import { check } from "k6";

let NHS_NUMBERS, POINTER_IDS, ODS_CODE;
if (__ENV.ISPERFTEST === "true") {
  const referenceData = JSON.parse(open("./consumer_reference_data.json"));
  NHS_NUMBERS = referenceData.nhs_numbers;
  POINTER_IDS = referenceData.pointer_ids;
  ODS_CODE = referenceData.ods_codes[0];
} else {
  NHS_NUMBERS = require("../constants.js").NHS_NUMBERS;
  POINTER_IDS = require("../constants.js").POINTER_IDS;
  ODS_CODE = require("../constants.js").ODS_CODE;
}

function getHeaders(odsCode = ODS_CODE) {
  return {
    "Content-Type": "application/fhir+json",
    "X-Request-Id": "K6PerformanceTest",
    "NHSD-Correlation-Id": "K6PerformanceTest",
    "NHSD-Connection-Metadata": JSON.stringify({
      "nrl.ods-code": odsCode,
      "nrl.pointer-types": POINTER_TYPES.map(
        (type) => `http://snomed.info/sct|${type}`
      ),
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

export function countDocumentReference() {
  const choice = Math.floor(Math.random() * NHS_NUMBERS.length);
  const nhsNumber = NHS_NUMBERS[choice];

  const identifier = encodeURIComponent(
    `https://fhir.nhs.uk/Id/nhs-number|${nhsNumber}`
  );
  const res = http.get(
    `https://${__ENV.HOST}/consumer/DocumentReference?_summary=count&subject:identifier=${identifier}`,
    {
      headers: getHeaders(),
    }
  );
  checkResponse(res);
}

export function readDocumentReference() {
  const choice = Math.floor(Math.random() * POINTER_IDS.length);
  const id = POINTER_IDS[choice];

  const res = http.get(
    `https://${__ENV.HOST}/consumer/DocumentReference/${id}`,
    {
      headers: getHeaders(),
    }
  );

  checkResponse(res);
}

export function searchDocumentReference() {
  const nhsNumber = NHS_NUMBERS[Math.floor(Math.random() * NHS_NUMBERS.length)];
  const pointer_type =
    POINTER_TYPES[Math.floor(Math.random() * POINTER_TYPES.length)];

  const identifier = encodeURIComponent(
    `https://fhir.nhs.uk/Id/nhs-number|${nhsNumber}`
  );
  const type = encodeURIComponent(`http://snomed.info/sct|${pointer_type}`);

  const res = http.get(
    `https://${__ENV.HOST}/consumer/DocumentReference?subject:identifier=${identifier}&type=${type}`,
    {
      headers: getHeaders(),
    }
  );
  checkResponse(res);
}

export function searchDocumentReferenceByCategory() {
  const nhsNumber = NHS_NUMBERS[Math.floor(Math.random() * NHS_NUMBERS.length)];
  const randomCategory =
    CATEGORIES[Math.floor(Math.random() * CATEGORIES.length)];

  const identifier = encodeURIComponent(
    `https://fhir.nhs.uk/Id/nhs-number|${nhsNumber}`
  );
  const category = encodeURIComponent(
    `http://snomed.info/sct|${randomCategory}`
  );

  const res = http.get(
    `https://${__ENV.HOST}/consumer/DocumentReference?subject:identifier=${identifier}&category=${category}`,
    {
      headers: getHeaders(),
    }
  );
  checkResponse(res);
}

export function searchPostDocumentReference() {
  const nhsNumber = NHS_NUMBERS[Math.floor(Math.random() * NHS_NUMBERS.length)];
  const pointer_type =
    POINTER_TYPES[Math.floor(Math.random() * POINTER_TYPES.length)];

  const body = JSON.stringify({
    "subject:identifier": `https://fhir.nhs.uk/Id/nhs-number|${nhsNumber}`,
    type: `http://snomed.info/sct|${pointer_type}`,
  });

  const res = http.post(
    `https://${__ENV.HOST}/consumer/DocumentReference/_search`,
    body,
    {
      headers: getHeaders(),
    }
  );
  checkResponse(res);
}

export function searchPostDocumentReferenceByCategory() {
  const nhsNumber = NHS_NUMBERS[Math.floor(Math.random() * NHS_NUMBERS.length)];
  const category = CATEGORIES[Math.floor(Math.random() * CATEGORIES.length)];

  const body = JSON.stringify({
    "subject:identifier": `https://fhir.nhs.uk/Id/nhs-number|${nhsNumber}`,
    category: `http://snomed.info/sct|${category}`,
  });

  const res = http.post(
    `https://${__ENV.HOST}/consumer/DocumentReference/_search`,
    body,
    {
      headers: getHeaders(),
    }
  );
  checkResponse(res);
}

export function countPostDocumentReference() {
  const choice = Math.floor(Math.random() * NHS_NUMBERS.length);
  const nhsNumber = NHS_NUMBERS[choice];

  const body = JSON.stringify({
    "subject:identifier": `https://fhir.nhs.uk/Id/nhs-number|${nhsNumber}`,
  });
  const res = http.post(
    `https://${__ENV.HOST}/consumer/DocumentReference/_search?_summary=count`,
    body,
    {
      headers: getHeaders(),
    }
  );
  checkResponse(res);
}
