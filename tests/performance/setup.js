import {
  DEFAULT_TEST_RECORD,
  ODS_CODE,
  POINTER_TYPE_DISPLAY,
  TYPE_CATEGORY_MAP,
  CATEGORY_DISPLAY,
} from "./constants.js";
import { crypto } from "k6/experimental/webcrypto";

export function createRecord(nhsNumber, pointerType) {
  const record = JSON.parse(DEFAULT_TEST_RECORD);
  record.id = `${ODS_CODE}-${crypto.randomUUID()}`;

  record.type.coding[0].code = pointerType;
  if (!POINTER_TYPE_DISPLAY[pointerType]) {
    throw new Error(`Display not found for pointerType: ${pointerType}`);
  }
  record.type.coding[0].display = POINTER_TYPE_DISPLAY[pointerType];

  const categoryCode = TYPE_CATEGORY_MAP[pointerType];
  record.category[0].coding[0].code = categoryCode;
  record.category[0].coding[0].display = CATEGORY_DISPLAY[categoryCode];

  record.subject.identifier.value = nhsNumber;
  record.context.sourcePatientInfo.identifier.value = nhsNumber;

  return record;
}
