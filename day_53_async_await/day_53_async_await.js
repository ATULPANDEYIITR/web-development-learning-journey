"use strict";

/*
 * Async/await case study:
 * A deployment coordinator executes independent service checks,
 * handles failures without hiding successful work, applies timeouts,
 * retries transient failures, and limits concurrency.
 */

const sleep = (milliseconds) =>
  new Promise((resolve) => setTimeout(resolve, milliseconds));

class ServiceError extends Error {
  constructor(service, message) {
    super(message);
    this.name = "ServiceError";
    this.service = service;
  }
}

async function callService(service, delay, shouldFail = false) {
  await sleep(delay);

  if (shouldFail) {
    throw new ServiceError(service, `${service} failed`);
  }

  return `${service} response`;
}

async function sequentialChecks() {
  const results = [];

  results.push(await callService("database", 120));
  results.push(await callService("cache", 80));
  results.push(await callService("queue", 100));

  return results;
}

async function parallelChecks() {
  const operations = [
    callService("database", 120),
    callService("cache", 80),
    callService("queue", 100),
  ];

  return Promise.all(operations);
}

async function parallelWithFailureIsolation() {
  const jobs = [
    ["database", callService("database", 120)],
    ["payments", callService("payments", 80, true)],
    ["queue", callService("queue", 100)],
  ];

  const settled = await Promise.allSettled(jobs.map(([, operation]) => operation));

  return settled.map((result, index) => {
    const [name] = jobs[index];

    if (result.status === "fulfilled") {
      return {
        job: name,
        status: "completed",
        value: result.value,
      };
    }

    return {
      job: name,
      status: "failed",
      error: result.reason instanceof Error
        ? result.reason.message
        : String(result.reason),
    };
  });
}

function withTimeout(operation, milliseconds) {
  let timer;

  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => {
      reject(new Error(`operation exceeded ${milliseconds} ms`));
    }, milliseconds);
  });

  return Promise.race([operation, timeout]).finally(() => {
    clearTimeout(timer);
  });
}

async function retryAsync(operationFactory, attempts = 3, baseDelay = 40) {
  if (!Number.isInteger(attempts) || attempts < 1) {
    throw new RangeError("attempts must be a positive integer");
  }

  let lastError;

  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      return await operationFactory();
    } catch (error) {
      lastError = error;

      if (attempt === attempts - 1) {
        break;
      }

      await sleep(baseDelay * 2 ** attempt);
    }
  }

  throw lastError;
}

async function retryExample() {
  let attempts = 0;

  return retryAsync(async () => {
    attempts += 1;

    if (attempts < 3) {
      throw new Error("temporary dependency failure");
    }

    return `succeeded on attempt ${attempts}`;
  });
}

async function boundedParallelism(items, concurrency, worker) {
  if (!Number.isInteger(concurrency) || concurrency < 1) {
    throw new RangeError("concurrency must be a positive integer");
  }

  const results = new Array(items.length);
  let nextIndex = 0;

  async function consume() {
    while (true) {
      const index = nextIndex;
      nextIndex += 1;

      if (index >= items.length) {
        return;
      }

      try {
        results[index] = {
          status: "fulfilled",
          value: await worker(items[index]),
        };
      } catch (error) {
        results[index] = {
          status: "rejected",
          reason: error instanceof Error ? error.message : String(error),
        };
      }
    }
  }

  const workerCount = Math.min(concurrency, items.length);
  await Promise.all(
    Array.from({ length: workerCount }, () => consume())
  );

  return results;
}

async function cancellationAwareTask(signal) {
  if (!(signal instanceof AbortSignal)) {
    throw new TypeError("signal must be an AbortSignal");
  }

  if (signal.aborted) {
    throw new Error("operation cancelled before start");
  }

  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      signal.removeEventListener("abort", abort);
      resolve("completed");
    }, 500);

    function abort() {
      clearTimeout(timer);
      reject(new Error("operation cancelled"));
    }

    signal.addEventListener("abort", abort, { once: true });
  });
}

async function main() {
  console.log("Sequential:");
  console.log(await sequentialChecks());

  console.log("\nParallel:");
  console.log(await parallelChecks());

  console.log("\nFailure isolation:");
  console.log(await parallelWithFailureIsolation());

  console.log("\nTimeout:");
  try {
    console.log(
      await withTimeout(callService("slow-service", 200), 50)
    );
  } catch (error) {
    console.log(error.message);
  }

  console.log("\nRetry:");
  console.log(await retryExample());

  console.log("\nBounded concurrency:");
  console.log(
    await boundedParallelism(
      ["a", "b", "c", "d", "e"],
      2,
      async (item) => {
        await sleep(40);
        return `${item} processed`;
      }
    )
  );

  console.log("\nCancellation:");
  const controller = new AbortController();
  const pending = cancellationAwareTask(controller.signal);

  setTimeout(() => controller.abort(), 40);

  try {
    await pending;
  } catch (error) {
    console.log(error.message);
  }
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exitCode = 1;
});
