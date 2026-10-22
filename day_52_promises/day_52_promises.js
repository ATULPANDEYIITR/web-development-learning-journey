"use strict";

/*
 * Promise behavior model for Node.js.
 * The examples use real JavaScript Promises rather than a synchronous
 * imitation, because Promise settlement and microtask scheduling are
 * observable parts of the language runtime.
 */

class ConfigurationError extends Error {
  constructor(message) {
    super(message);
    this.name = "ConfigurationError";
  }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function resolveConfiguration() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ timeout: 30, retries: 3 });
    }, 20);
  });
}

async function demonstrateStateAndChaining() {
  const result = await resolveConfiguration()
    .then((config) => ({
      ...config,
      endpoint: "https://service.internal",
    }))
    .then((config) => {
      if (config.timeout <= 0) {
        throw new ConfigurationError("timeout must be positive");
      }
      return config;
    });

  console.log("chained value:", result);
}

async function demonstrateErrorPropagation() {
  return Promise.resolve("request")
    .then(() => {
      throw new Error("request validation failed");
    })
    .then(
      () => "unreachable",
      (error) => {
        console.log("rejection handled:", error.message);
        return "recovered";
      }
    );
}

function service(name, ms, shouldReject = false) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (shouldReject) {
        reject(new Error(`${name} failed`));
      } else {
        resolve(`${name} completed`);
      }
    }, ms);
  });
}

async function demonstrateAll() {
  try {
    const values = await Promise.all([
      service("database", 50),
      service("cache", 20),
      service("queue", 35),
    ]);

    console.log("Promise.all:", values);
  } catch (error) {
    console.error("Promise.all rejected:", error.message);
  }

  try {
    await Promise.all([
      service("database", 50),
      service("cache", 15, true),
      service("queue", 35),
    ]);
  } catch (error) {
    // Promise.all rejects when the first input rejection is observed.
    console.log("Promise.all fail-fast:", error.message);
  }
}

async function demonstrateRace() {
  const winner = await Promise.race([
    service("primary", 90),
    service("replica", 25),
    service("fallback", 60),
  ]);

  console.log("Promise.race winner:", winner);

  try {
    await Promise.race([
      service("unhealthy-primary", 15, true),
      service("slow-backup", 70),
    ]);
  } catch (error) {
    // race() settles from the first settlement, including rejection.
    console.log("Promise.race rejection:", error.message);
  }
}

async function demonstrateAllSettled() {
  const results = await Promise.allSettled([
    service("metrics", 20),
    service("audit", 35, true),
    service("cache", 10),
  ]);

  console.log("Promise.allSettled:", results);

  const successful = results
    .filter((result) => result.status === "fulfilled")
    .map((result) => result.value);

  const failures = results
    .filter((result) => result.status === "rejected")
    .map((result) => result.reason.message);

  console.log("successful operations:", successful);
  console.log("failed operations:", failures);
}

async function demonstrateAny() {
  try {
    const winner = await Promise.any([
      service("region-a", 50, true),
      service("region-b", 30, true),
      service("region-c", 45, false),
    ]);

    console.log("Promise.any winner:", winner);
  } catch (error) {
    // Promise.any rejects only after every input rejects.
    console.log("Promise.any AggregateError:", error.errors);
  }

  try {
    await Promise.any([
      service("backup-a", 10, true),
      service("backup-b", 20, true),
    ]);
  } catch (error) {
    if (error instanceof AggregateError) {
      console.log("all candidates failed:", error.errors.map((e) => e.message));
    }
  }
}

async function demonstrateMicrotaskOrdering() {
  const events = [];

  events.push("synchronous-start");

  Promise.resolve().then(() => {
    events.push("promise-microtask");
  });

  setTimeout(() => {
    events.push("timer-task");
    console.log("event ordering:", events);
  }, 0);

  events.push("synchronous-end");
}

async function timeoutWrapper(promise, timeoutMs) {
  let timer;

  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => {
      reject(new Error(`operation exceeded ${timeoutMs} ms`));
    }, timeoutMs);
  });

  try {
    return await Promise.race([promise, timeout]);
  } finally {
    clearTimeout(timer);
  }
}

async function demonstrateTimeoutPolicy() {
  try {
    const result = await timeoutWrapper(service("remote-api", 25), 100);
    console.log("timeout policy result:", result);
  } catch (error) {
    console.log("timeout policy failure:", error.message);
  }

  try {
    await timeoutWrapper(service("slow-api", 100), 20);
  } catch (error) {
    console.log("timeout policy rejection:", error.message);
  }
}

async function main() {
  await demonstrateStateAndChaining();
  await demonstrateErrorPropagation();
  await demonstrateAll();
  await demonstrateRace();
  await demonstrateAllSettled();
  await demonstrateAny();
  await demonstrateMicrotaskOrdering();
  await delay(10);
  await demonstrateTimeoutPolicy();
}

main().catch((error) => {
  console.error("Unhandled application failure:", error);
  process.exitCode = 1;
});
