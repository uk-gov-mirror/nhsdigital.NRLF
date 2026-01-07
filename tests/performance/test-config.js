import { POINTER_TYPES } from "./constants.js";
import exec from "k6/execution";

let config = null;

const connectMode = __ENV.TEST_CONNECT_MODE || "internal";
let configData = null;

if (connectMode === "public") {
  const configFile = __ENV.TEST_CONFIG_FILE;
  if (!configFile) {
    throw new Error("Public mode requires TEST_CONFIG_FILE");
  }
  configData = JSON.parse(open(configFile));
}

function initConfig() {
  if (config !== null) {
    return config;
  }

  if (connectMode === "public") {
    config = {
      connectMode: "public",
      baseUrl: __ENV.TEST_PUBLIC_BASE_URL.replace(/\/$/, ""),
      consumerPath: "/consumer/FHIR/R4",
      producerPath: "/producer/FHIR/R4",
      // odsCode: ODS_CODE,
      bearerToken: configData.bearer_token,
    };

    if (!config.baseUrl) {
      throw new Error("Public mode requires TEST_PUBLIC_BASE_URL");
    }
    if (!config.bearerToken) {
      throw new Error("Bearer token not found in config file");
    }
  } else {
    config = {
      connectMode: "internal",
      baseUrl: `https://${__ENV.HOST}`,
      consumerPath: "/consumer",
      producerPath: "/producer",
      // odsCode: ODS_CODE,
      bearerToken: null,
    };
  }

  return config;
}

export function getHeaders(odsCode, actorType) {
  const cfg = initConfig();

  const baseHeaders = {
    "Content-Type": "application/fhir+json",
    "X-Request-Id": `K6perftest-${actorType}-${exec.scenario.name}-${exec.vu.idInTest}-${exec.vu.iterationInScenario}`,
    "NHSD-Correlation-Id": `K6perftest-${actorType}-${exec.scenario.name}-${exec.vu.idInTest}-${exec.vu.iterationInScenario}`,
  };

  if (cfg.connectMode === "internal") {
    return {
      ...baseHeaders,
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
  } else {
    return {
      ...baseHeaders,
      Authorization: `Bearer ${cfg.bearerToken}`,
      "NHSD-End-User-Organisation-ODS": odsCode,
    };
  }
}

export function getFullUrl(path, actorType) {
  if (!actorType || (actorType !== "consumer" && actorType !== "producer")) {
    throw new Error("actorType must be either 'consumer' or 'producer'");
  }
  const cfg = initConfig();
  const apiPath =
    actorType === "producer" ? cfg.producerPath : cfg.consumerPath;
  const fullUrl = `${cfg.baseUrl}${apiPath}${path}`;

  return fullUrl;
}
