"use strict";

/*
 * Deterministic event-loop model.
 *
 * The model separates:
 *   1. synchronous call-stack execution,
 *   2. task/macrotask processing,
 *   3. microtask checkpoints,
 *   4. rendering opportunities.
 *
 * It is deliberately independent of the host's actual event loop so that
 * ordering and starvation behavior can be tested reproducibly.
 */

class EventLoopError extends Error {}

class EventLoop {
  constructor({ frameInterval = 16, maxMicrotasks = 1000 } = {}) {
    if (frameInterval <= 0 || maxMicrotasks <= 0) {
      throw new RangeError("Event-loop limits must be positive.");
    }

    this.now = 0;
    this.frameInterval = frameInterval;
    this.nextFrame = frameInterval;
    this.maxMicrotasks = maxMicrotasks;

    this.stack = [];
    this.tasks = [];
    this.microtasks = [];
    this.renderCallbacks = [];
    this.sequence = 0;
    this.logEntries = [];
  }

  log(message) {
    this.logEntries.push(
      `${String(this.now).padStart(4, "0")}ms | ${message}`
    );
  }

  runSync(name, callback) {
    if (typeof callback !== "function") {
      throw new TypeError(`Callback for ${name} must be a function.`);
    }

    this.stack.push(name);
    this.log(`stack-enter ${name}`);

    try {
      callback();
    } finally {
      this.log(`stack-exit ${name}`);
      this.stack.pop();
    }
  }

  queueMicrotask(name, callback) {
    if (typeof callback !== "function") {
      throw new TypeError("Microtask callback must be a function.");
    }

    this.microtasks.push({
      name,
      callback,
      sequence: ++this.sequence,
    });

    this.log(`microtask-queued ${name}`);
  }

  queueTask(name, callback, { type = "io", delay = 0 } = {}) {
    if (typeof callback !== "function") {
      throw new TypeError("Task callback must be a function.");
    }

    if (!Number.isInteger(delay) || delay < 0) {
      throw new RangeError("Task delay must be a non-negative integer.");
    }

    this.tasks.push({
      name,
      callback,
      type,
      scheduledAt: this.now + delay,
      sequence: ++this.sequence,
    });

    this.log(`task-queued ${name} delay=${delay}ms`);
  }

  requestRender(name, callback) {
    if (typeof callback !== "function") {
      throw new TypeError("Render callback must be a function.");
    }

    this.renderCallbacks.push({
      name,
      callback,
      sequence: ++this.sequence,
    });

    this.log(`render-requested ${name}`);
  }

  runMicrotasks() {
    let processed = 0;

    while (this.microtasks.length > 0) {
      if (processed >= this.maxMicrotasks) {
        throw new EventLoopError(
          "Microtask checkpoint exceeded its safety limit."
        );
      }

      const task = this.microtasks.shift();
      processed += 1;

      this.runSync(task.name, task.callback);
      this.log(`microtask-complete ${task.name}`);
    }
  }

  nextReadyTask() {
    const ready = this.tasks
      .filter((task) => task.scheduledAt <= this.now)
      .sort(
        (a, b) =>
          a.scheduledAt - b.scheduledAt ||
          a.sequence - b.sequence
      );

    if (ready.length === 0) {
      return null;
    }

    const selected = ready[0];
    const index = this.tasks.indexOf(selected);
    this.tasks.splice(index, 1);

    return selected;
  }

  advanceTime() {
    const futureTimes = this.tasks
      .filter((task) => task.scheduledAt > this.now)
      .map((task) => task.scheduledAt);

    if (futureTimes.length === 0) {
      this.now = this.nextFrame;
      return;
    }

    const nextTask = Math.min(...futureTimes);
    this.now = Math.min(nextTask, this.nextFrame);
  }

  renderIfDue() {
    if (this.now < this.nextFrame) {
      return;
    }

    this.log("rendering-opportunity");

    while (this.renderCallbacks.length > 0) {
      const callback = this.renderCallbacks.shift();

      this.runSync(callback.name, callback.callback);
      this.log(`render-complete ${callback.name}`);
    }

    this.nextFrame += this.frameInterval;
  }

  run(maxTurns = 100) {
    if (!Number.isInteger(maxTurns) || maxTurns <= 0) {
      throw new RangeError("maxTurns must be positive.");
    }

    let turns = 0;

    while (
      this.tasks.length > 0 ||
      this.microtasks.length > 0 ||
      this.renderCallbacks.length > 0
    ) {
      if (++turns > maxTurns) {
        throw new EventLoopError("Maximum event-loop turns exceeded.");
      }

      this.runMicrotasks();

      const task = this.nextReadyTask();

      if (task === null) {
        this.advanceTime();
        this.renderIfDue();
        continue;
      }

      this.runSync(task.name, task.callback);
      this.log(`task-complete ${task.name}`);

      this.runMicrotasks();
      this.renderIfDue();
    }

    return [...this.logEntries];
  }
}

function buildScenario() {
  const loop = new EventLoop();

  loop.runSync("application-start", () => {
    loop.log("synchronous-start");

    loop.queueMicrotask("promise-reaction", () => {
      loop.log("Promise reaction executes");
    });

    loop.queueTask(
      "zero-delay-timer",
      () => loop.log("timer callback executes"),
      { type: "timer" }
    );

    loop.requestRender("paint", () => {
      loop.log("render callback executes");
    });

    loop.runSync("nested-function", () => {
      loop.log(`stack depth=${loop.stack.length}`);
    });

    loop.log("synchronous-end");
  });

  loop.queueTask(
    "network-response",
    () => {
      loop.log("network response callback executes");

      loop.queueMicrotask("response-microtask", () => {
        loop.log("microtask created by network callback");
      });
    },
    { type: "io", delay: 5 }
  );

  return loop;
}

function demonstrateStarvationProtection() {
  const loop = new EventLoop({ maxMicrotasks: 5 });
  let count = 0;

  const recursive = () => {
    count += 1;

    loop.queueMicrotask(`recursive-${count}`, recursive);
  };

  loop.queueMicrotask("recursive-0", recursive);

  try {
    loop.run();
  } catch (error) {
    if (!(error instanceof EventLoopError)) {
      throw error;
    }

    return `Starvation protection triggered after ${count} callbacks: ${error.message}`;
  }

  return "No starvation detected";
}

function testOrdering() {
  const loop = new EventLoop();
  const observed = [];

  loop.runSync("test", () => {
    observed.push("sync");
    loop.queueMicrotask("microtask", () => observed.push("microtask"));
    loop.queueTask("task", () => observed.push("task"));
  });

  loop.run();

  const expected = ["sync", "microtask", "task"];

  if (JSON.stringify(observed) !== JSON.stringify(expected)) {
    throw new Error(
      `Ordering failure. Expected ${expected}, received ${observed}.`
    );
  }
}

function main() {
  const loop = buildScenario();

  for (const entry of loop.run()) {
    console.log(entry);
  }

  console.log();
  console.log(demonstrateStarvationProtection());

  testOrdering();
  console.log("Ordering assertion passed.");
}

main();
