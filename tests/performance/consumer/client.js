import { getHeaders, getFullUrl } from "../test-config.js";
import {
  POINTER_TYPES,
  CATEGORIES,
  NHS_NUMBERS,
  POINTER_IDS,
} from "../constants.js";
import http from "k6/http";
import { check } from "k6";

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

  const path = `/DocumentReference?_summary=count&subject:identifier=${identifier}`;
  const res = http.get(getFullUrl(path), {
    headers: getHeaders(),
  });
  checkResponse(res);
}

export function readDocumentReference() {
  const choice = Math.floor(Math.random() * POINTER_IDS.length);
  const id = POINTER_IDS[choice];

  const path = `/DocumentReference/${id}`;
  const res = http.get(getFullUrl(path), {
    headers: getHeaders(),
  });

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

  const path = `/DocumentReference?subject:identifier=${identifier}&type=${type}`;
  const res = http.get(getFullUrl(path), {
    headers: getHeaders(),
  });
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

  const path = `/DocumentReference?subject:identifier=${identifier}&category=${category}`;
  const res = http.get(getFullUrl(path), {
    headers: getHeaders(),
  });
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

  const path = `/DocumentReference/_search`;
  const res = http.post(getFullUrl(path), body, {
    headers: getHeaders(),
  });
  checkResponse(res);
}

export function searchPostDocumentReferenceByCategory() {
  const nhsNumber = NHS_NUMBERS[Math.floor(Math.random() * NHS_NUMBERS.length)];
  const category = CATEGORIES[Math.floor(Math.random() * CATEGORIES.length)];

  const body = JSON.stringify({
    "subject:identifier": `https://fhir.nhs.uk/Id/nhs-number|${nhsNumber}`,
    category: `http://snomed.info/sct|${category}`,
  });

  const path = `/DocumentReference/_search`;
  const res = http.post(getFullUrl(path), body, {
    headers: getHeaders(),
  });
  checkResponse(res);
}

export function countPostDocumentReference() {
  const choice = Math.floor(Math.random() * NHS_NUMBERS.length);
  const nhsNumber = NHS_NUMBERS[choice];

  const body = JSON.stringify({
    "subject:identifier": `https://fhir.nhs.uk/Id/nhs-number|${nhsNumber}`,
  });

  const path = `/DocumentReference/_search?_summary=count`;
  const res = http.post(getFullUrl(path), body, {
    headers: getHeaders(),
  });
  checkResponse(res);
}
