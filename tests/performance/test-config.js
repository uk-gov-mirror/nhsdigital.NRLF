import { POINTER_TYPES, ODS_CODE } from "./constants.js";

let config = null;

function initConfig() {
  if (config !== null) {
    return config;
  }

  const connectMode = __ENV.TEST_CONNECT_MODE || "internal";

  if (connectMode === "public") {
    config = {
      connectMode: "public",
      baseUrl: __ENV.TEST_PUBLIC_BASE_URL.replace(/\/$/, ""),
      consumerPath: "/consumer/FHIR/R4",
      producerPath: "/producer/FHIR/R4",
      odsCode: ODS_CODE,
      bearerToken: __ENV.TEST_BEARER_TOKEN,
    };

    if (!config.baseUrl) {
      throw new Error("Public mode requires TEST_PUBLIC_BASE_URL");
    }
    if (!config.bearerToken) {
      throw new Error("Public mode requires TEST_BEARER_TOKEN");
    }
  } else {
    config = {
      connectMode: "internal",
      baseUrl: `https://${__ENV.HOST}`,
      consumerPath: "/consumer",
      producerPath: "/producer",
      odsCode: ODS_CODE,
      bearerToken: null,
    };
  }

  return config;
}

export function getHeaders(appId = "K6PerformanceTest") {
  const cfg = initConfig();

  const baseHeaders = {
    "Content-Type": "application/fhir+json",
    "X-Request-Id": appId,
    "NHSD-Correlation-Id": appId,
  };

  if (cfg.connectMode === "internal") {
    return {
      ...baseHeaders,
      "NHSD-Connection-Metadata": JSON.stringify({
        "nrl.ods-code": cfg.odsCode,
        "nrl.pointer-types": POINTER_TYPES.map(
          (type) => `http://snomed.info/sct|${type}`
        ),
        "nrl.app-id": appId,
      }),
      "NHSD-Client-RP-Details": JSON.stringify({
        "developer.app.name": appId,
        "developer.app.id": appId,
      }),
    };
  } else {
    return {
      ...baseHeaders,
      Authorization: `Bearer ${cfg.bearerToken}`,
      "NHSD-End-User-Organisation-ODS": cfg.odsCode,
    };
  }
}

export function getFullUrl(path, apiType = "consumer") {
  const cfg = initConfig();
  const apiPath = apiType === "producer" ? cfg.producerPath : cfg.consumerPath;
  return `${cfg.baseUrl}${apiPath}${path}`;
}
