export * from "./client.js";

const config = JSON.parse(open("./perftest.config.json"));
const PROFILE = config.profile.toUpperCase();
const tlsAuth = config.tlsAuth;
const scenarioConfigs = config.scenarios;

function makeSoakScenario(execName, conf) {
  return {
    exec: execName,
    executor: "ramping-arrival-rate",
    startRate: 0,
    timeUnit: "1s",
    preAllocatedVUs: 5,
    stages: [
      { target: conf.tps, duration: conf.duration },
      { target: conf.tps, duration: conf.hold },
      { target: 0, duration: conf.rampDown },
    ],
  };
}

function makeStressScenario(execName, conf) {
  return {
    exec: execName,
    executor: "ramping-arrival-rate",
    startRate: conf.startTps || 1,
    timeUnit: "1s",
    preAllocatedVUs: 5,
    stages: [
      { target: conf.tps, duration: conf.duration },
      { target: conf.tps, duration: conf.hold },
    ],
  };
}

const scenarios = {};
for (const [name, conf] of Object.entries(scenarioConfigs)) {
  scenarios[name] =
    PROFILE === "SOAK"
      ? makeSoakScenario(name, conf)
      : makeStressScenario(name, conf);
}

export const options = {
  tlsAuth: [
    {
      cert: open(tlsAuth.cert.replace("${ENV_TYPE}", __ENV.ENV_TYPE)),
      key: open(tlsAuth.key.replace("${ENV_TYPE}", __ENV.ENV_TYPE)),
    },
  ],
  scenarios,
};
