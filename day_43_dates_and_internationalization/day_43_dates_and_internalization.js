"use strict";

/*
 * Dates and Internationalization with JavaScript.
 *
 * Run with Node.js 18 or later:
 *     node dates-internationalization.js
 *
 * This implementation focuses on JavaScript Date semantics, milliseconds,
 * Intl formatters, locale negotiation, explicit time-zone rendering,
 * offset-aware parsing, and safe handling of calendar dates.
 */

const assert = require("node:assert/strict");

function heading(title) {
  console.log(`\n${"=".repeat(72)}\n${title}\n${"=".repeat(72)}`);
}

function requireValidDate(value, description = "date") {
  if (!(value instanceof Date) || Number.isNaN(value.getTime())) {
    throw new TypeError(`${description} must be a valid Date instance`);
  }
  return value;
}

function demonstrateDateBasics() {
  heading("JavaScript Date fundamentals");

  const instant = new Date("2026-10-13T10:00:00.000Z");

  console.log("UTC ISO representation:", instant.toISOString());
  console.log("Epoch milliseconds:", instant.getTime());
  console.log("Epoch seconds:", instant.getTime() / 1000);
  console.log("UTC year:", instant.getUTCFullYear());
  console.log("UTC month, one-based:", instant.getUTCMonth() + 1);
  console.log("UTC day:", instant.getUTCDate());

  // getMonth() is zero-based, while human-readable months are one-based.
  // Local getters depend on the machine's configured time zone.
  console.log("Machine-local representation:", instant.toString());

  const invalid = new Date("not-a-date");
  console.log("Invalid date detected:", Number.isNaN(invalid.getTime()));

  try {
    invalid.toISOString();
  } catch (error) {
    console.log("Invalid ISO conversion rejected:", error.name);
  }
}

function demonstrateTimestampPrecision() {
  heading("Timestamps and precision");

  const timestampMilliseconds = 1791878400625;
  const instant = new Date(timestampMilliseconds);

  console.log("Milliseconds:", instant.getTime());
  console.log("ISO:", instant.toISOString());
  console.log("Seconds:", Math.floor(instant.getTime() / 1000));

  // Date stores epoch milliseconds. It cannot preserve arbitrary sub-millisecond
  // fractions. For exact high-resolution duration measurement, use BigInt-based
  // process.hrtime.bigint() in Node.js rather than wall-clock Date values.
  const highResolutionStart = process.hrtime.bigint();
  let checksum = 0;
  for (let index = 0; index < 10000; index += 1) {
    checksum += index;
  }
  const elapsedNanoseconds = process.hrtime.bigint() - highResolutionStart;

  console.log("Benchmark checksum:", checksum);
  console.log("Elapsed nanoseconds:", elapsedNanoseconds.toString());

  const now = Date.now();
  console.log("Current epoch milliseconds:", now);
}

function demonstrateIntlFormatting() {
  heading("Intl.DateTimeFormat and locale-aware rendering");

  const instant = new Date("2026-10-13T10:00:00.000Z");

  const examples = [
    {
      locale: "en-US",
      timeZone: "America/New_York",
      options: {
        dateStyle: "full",
        timeStyle: "long",
      },
    },
    {
      locale: "en-GB",
      timeZone: "Europe/London",
      options: {
        dateStyle: "full",
        timeStyle: "short",
      },
    },
    {
      locale: "hi-IN",
      timeZone: "Asia/Kolkata",
      options: {
        dateStyle: "long",
        timeStyle: "medium",
      },
    },
    {
      locale: "ja-JP",
      timeZone: "Asia/Tokyo",
      options: {
        dateStyle: "long",
        timeStyle: "short",
      },
    },
  ];

  for (const example of examples) {
    const formatter = new Intl.DateTimeFormat(example.locale, {
      ...example.options,
      timeZone: example.timeZone,
    });

    console.log(
      `${example.locale}, ${example.timeZone}:`,
      formatter.format(instant)
    );
  }

  // Reuse formatter instances in high-volume applications. Constructing
  // formatters repeatedly can cost more than formatting each value.
  const reusableFormatter = new Intl.DateTimeFormat("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });

  console.log("Reusable formatter:", reusableFormatter.format(instant));
  console.log("Structured localized parts:", reusableFormatter
    .formatToParts(instant)
    .map(({ type, value }) => `${type}=${value}`)
    .join(" | "));
}

function demonstrateLocaleNegotiation() {
  heading("Locale negotiation and international numbers");

  const supported = ["en-GB", "en-IN", "hi-IN", "fr-FR"];
  const requested = ["hi-IN", "fr-FR", "de-DE"];

  const resolved = Intl.DateTimeFormat.supportedLocalesOf(requested, {
    localeMatcher: "lookup",
  });

  console.log("Requested locales:", requested);
  console.log("Supported requested locales:", resolved);

  const number = 1234567.89;
  const currency = 98765.43;

  for (const locale of supported) {
    const numberFormatter = new Intl.NumberFormat(locale, {
      maximumFractionDigits: 2,
    });
    const currencyFormatter = new Intl.NumberFormat(locale, {
      style: "currency",
      currency: locale === "en-GB"
        ? "GBP"
        : locale === "fr-FR"
          ? "EUR"
          : "INR",
    });

    console.log(
      locale,
      "number:",
      numberFormatter.format(number),
      "currency:",
      currencyFormatter.format(currency)
    );
  }
}

function parseStrictOffsetTimestamp(value) {
  // Require an explicit Z or numeric offset. Date.parse alone accepts some
  // implementation-dependent formats and can interpret date-only strings
  // differently from an application's intended local-calendar semantics.
  const pattern =
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2})$/;

  if (typeof value !== "string" || !pattern.test(value)) {
    throw new TypeError("Expected an ISO timestamp with an explicit UTC offset");
  }

  const epochMilliseconds = Date.parse(value);
  if (!Number.isFinite(epochMilliseconds)) {
    throw new RangeError("Timestamp is not a valid date-time");
  }

  const result = new Date(epochMilliseconds);
  requireValidDate(result, "parsed timestamp");
  return result;
}

function demonstrateStrictParsing() {
  heading("Input validation and parsing");

  const timestamp = parseStrictOffsetTimestamp(
    "2026-10-13T15:30:00+05:30"
  );

  console.log("Parsed UTC instant:", timestamp.toISOString());
  console.log(
    "Rendered in London:",
    new Intl.DateTimeFormat("en-GB", {
      dateStyle: "medium",
      timeStyle: "long",
      timeZone: "Europe/London",
    }).format(timestamp)
  );

  const invalidInputs = [
    "2026-10-13",
    "2026-13-40T25:61:00Z",
    "2026-10-13T10:00:00",
  ];

  for (const input of invalidInputs) {
    try {
      parseStrictOffsetTimestamp(input);
      console.log("Accepted:", input);
    } catch (error) {
      console.log("Rejected:", input, error.name);
    }
  }
}

function demonstrateCalendarDates() {
  heading("Calendar dates versus instants");

  // A birthday or a holiday is often a calendar date, not a point on the
  // global timeline. Preserve its components instead of converting it into
  // a Date at midnight and accidentally shifting the displayed day.
  function parseCalendarDate(value) {
    if (typeof value !== "string" ||
        !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
      throw new TypeError("Expected YYYY-MM-DD");
    }

    const [year, month, day] = value.split("-").map(Number);
    const probe = new Date(Date.UTC(year, month - 1, day));

    if (
      probe.getUTCFullYear() !== year ||
      probe.getUTCMonth() !== month - 1 ||
      probe.getUTCDate() !== day
    ) {
      throw new RangeError("Invalid calendar date");
    }

    return Object.freeze({ year, month, day, iso: value });
  }

  const independenceDay = parseCalendarDate("2026-08-15");
  console.log("Calendar date:", independenceDay.iso);
  console.log("Calendar components:", independenceDay);

  try {
    parseCalendarDate("2026-02-30");
  } catch (error) {
    console.log("Invalid calendar date rejected:", error.name);
  }

  const instant = new Date("2026-08-15T00:00:00.000Z");
  console.log("Same instant rendered in Los Angeles:", new Intl.DateTimeFormat(
    "en-US",
    { dateStyle: "long", timeZone: "America/Los_Angeles" }
  ).format(instant));
}

function demonstrateElapsedTime() {
  heading("Elapsed time and deadlines");

  const start = new Date("2026-10-13T09:00:00.000Z");
  const finish = new Date("2026-10-13T17:45:00.000Z");

  const elapsedMilliseconds = finish.getTime() - start.getTime();
  const elapsedMinutes = elapsedMilliseconds / 60000;

  console.log("Elapsed milliseconds:", elapsedMilliseconds);
  console.log("Elapsed hours:", elapsedMilliseconds / 3600000);
  console.log("Elapsed minutes:", elapsedMinutes);

  function isExpired(deadline, now = new Date()) {
    requireValidDate(deadline, "deadline");
    requireValidDate(now, "current time");
    return now.getTime() >= deadline.getTime();
  }

  console.log(
    "Deadline expired:",
    isExpired(new Date("2026-10-13T12:00:00.000Z"), start)
  );

  // Fixed-duration arithmetic is suitable for elapsed hours. Calendar-day
  // arithmetic requires a calendar-aware representation and explicit zone.
  const oneDayLater = new Date(start.getTime() + 24 * 60 * 60 * 1000);
  console.log("Exactly 24 hours later:", oneDayLater.toISOString());
}

function demonstrateApiSerialization() {
  heading("API serialization");

  const eventInstant = parseStrictOffsetTimestamp(
    "2026-10-13T15:30:45.123+05:30"
  );

  const record = {
    eventId: "OPS-104",
    title: "Infrastructure maintenance",
    occurredAt: eventInstant.toISOString(),
    epochMilliseconds: eventInstant.getTime(),
    displayTimeZone: "Asia/Kolkata",
  };

  const json = JSON.stringify(record, null, 2);
  console.log(json);

  const restored = JSON.parse(json);
  const restoredInstant = new Date(restored.occurredAt);

  assert.equal(restoredInstant.getTime(), eventInstant.getTime());
  console.log("Serialization preserved the instant.");

  // JSON.stringify(Date) invokes Date.toJSON(), which emits UTC ISO text.
  console.log("Date JSON representation:", JSON.stringify(eventInstant));
}

class EventScheduler {
  #events = new Map();

  schedule({ id, title, timestamp, displayTimeZone }) {
    if (typeof id !== "string" || id.trim() === "") {
      throw new TypeError("Event ID is required");
    }
    if (typeof title !== "string" || title.trim() === "") {
      throw new TypeError("Event title is required");
    }
    if (this.#events.has(id)) {
      throw new Error(`Duplicate event ID: ${id}`);
    }

    const instant = parseStrictOffsetTimestamp(timestamp);

    try {
      new Intl.DateTimeFormat("en", {
        timeZone: displayTimeZone,
      }).format(instant);
    } catch {
      throw new RangeError(`Invalid time zone: ${displayTimeZone}`);
    }

    const event = Object.freeze({
      id,
      title,
      epochMilliseconds: instant.getTime(),
      displayTimeZone,
    });

    this.#events.set(id, event);
    return this.getDisplayRecord(id);
  }

  getDisplayRecord(id) {
    const event = this.#events.get(id);
    if (!event) {
      throw new Error(`Unknown event: ${id}`);
