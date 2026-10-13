# Dates and Internationalization

## Purpose and scope

Date and time handling requires more than storing a day, month, year, and clock reading. International applications must distinguish calendar dates from global instants, convert instants into regional time zones, preserve timestamp precision, display dates according to locale conventions, and handle daylight-saving transitions.

This project examines these requirements through six executable artifacts. The implementations use Python's `datetime` and `zoneinfo`, JavaScript's `Date` and `Intl`, C++17 timestamp and calendar abstractions, Java's `java.time` API, and PostgreSQL's date-time types and queries.

The central design principle is to distinguish the event's actual instant from the regional time zone and locale used to display it.

## Core date-time concepts

### Calendar dates and local clock readings

A calendar date identifies a day independently of a time zone. Examples include a public holiday, a birthday, and a reporting date. A local clock reading identifies a wall-clock time but does not necessarily identify one unique point on the global timeline.

A date such as `2026-10-13` is not equivalent to a timestamp such as `2026-10-13T10:00:00Z`. The first represents a calendar day. The second represents a specific instant.

A local date-time such as `2026-10-13 15:30` becomes an instant only after a time-zone or UTC-offset interpretation is supplied. Without that information, different systems may interpret the same value differently.

### Instants and Unix timestamps

An instant represents a particular point on the global timeline. A Unix timestamp expresses elapsed time relative to the Unix epoch, `1970-01-01T00:00:00Z`.

The unit matters:

| Representation | Unit | Typical use |
|---|---|---|
| Unix seconds | Seconds | APIs and legacy systems |
| Unix milliseconds | Milliseconds | JavaScript `Date` and many application APIs |
| Unix nanoseconds | Nanoseconds | High-resolution measurements and specialized systems |
| ISO 8601 timestamp | Calendar fields plus offset or UTC marker | Human-readable interchange and APIs |

A timestamp's numeric value does not contain the user's locale or preferred display zone. These must be supplied separately.

JavaScript's `Date` uses milliseconds. Python's `datetime` supports microseconds. Java's `Instant` supports nanoseconds. Converting between these representations can lose precision, so the required precision should be decided at the system boundary.

### UTC offsets and regional time zones

A UTC offset expresses a difference from UTC, such as `+05:30`. A regional time zone, such as `Asia/Kolkata` or `Europe/London`, identifies a collection of civil-time rules maintained in a time-zone database.

An offset is not a substitute for a region. London has different offsets during parts of the year because of daylight-saving rules. A fixed offset remains unchanged even when the region's rules change.

Store the actual instant and retain the regional zone identifier when the original scheduling context matters. For historical events, the resolved instant is authoritative. For recurring events such as a meeting every weekday at 09:00 in London, the regional zone is essential because future offsets may change.

### Daylight-saving gaps and overlaps

When clocks advance, some local times do not exist. When clocks move backward, some local times occur twice.

For example, a regional clock can skip from 00:59 to 02:00. A requested time of 01:30 then has no valid interpretation on that date. During a rollback, 01:30 may refer to two different instants.

An application accepting local scheduling input must define how it handles these cases. It can reject nonexistent times, request a different time, or apply an explicitly documented adjustment. For ambiguous times, it can ask the user to select the intended offset.

Silently accepting a local time without an ambiguity policy can produce incorrect appointment times, duplicated executions, or missed deadlines.

### Internationalization and localization

Internationalization, often abbreviated as i18n, means designing software to support different languages, regions, calendars, numbering conventions, and formatting preferences.

Localization, often abbreviated as l10n, applies the appropriate conventions to a particular audience.

A single instant can be displayed with different date orders, month names, hour cycles, numeral systems, and regional time zones. These display choices do not change the underlying instant.

Machine-readable representations should remain stable. Localized strings belong at presentation boundaries rather than serving as the primary representation for database keys or API timestamp values.

## Python implementation

The Python script demonstrates the following mechanisms:

- `date`, `time`, `datetime`, and `timedelta` represent distinct calendar and clock concepts. Aware date-times carry offset information; naive date-times do not identify a reliable global instant.
- `datetime.fromtimestamp()` and `.timestamp()` convert between numeric Unix timestamps and date-time values. Fractional timestamps illustrate precision handling.
- `strptime()` parses a specified format, while `strftime()` produces formatted output. `fromisoformat()` handles supported ISO date-time representations.
- `zoneinfo.ZoneInfo` loads IANA time-zone rules. `astimezone()` converts an existing instant, whereas `replace(tzinfo=...)` attaches a zone interpretation without performing an instant conversion.
- `valid_local_candidates()` detects nonexistent and ambiguous London wall-clock values by checking UTC round trips for both `fold` values.
- `add_months()` demonstrates calendar-month arithmetic. A month is not a fixed number of seconds, and end-of-month behavior must be defined explicitly.
- `ScheduledEvent` validates event identity, title, instant awareness, and display-zone configuration. It stores normalized UTC instants and generates API records containing both UTC and localized representations.
- The test suite verifies timestamp round trips, equivalent instants, daylight-saving gaps and overlaps, calendar arithmetic, and invalid event input.

The script uses only the Python standard library, except that an external time-zone database may be required on systems that do not provide one. Locale-specific month names and other localized formatting can also depend on installed operating-system locales.

## JavaScript implementation

JavaScript represents an instant with a `Date` object whose internal value is epoch milliseconds. The constructor accepts several input forms, but application code should validate incoming strings rather than relying on permissive parsing behavior.

The implementation uses `getTime()` for numeric comparison and `toISOString()` for a stable UTC representation. Local getters and `toString()` depend on the machine's configured time zone, so they should not be used when a service requires a particular region.

`Intl.DateTimeFormat` separates locale and time-zone configuration from the instant being displayed. The program compares US, British, Indian, and Japanese presentation conventions and demonstrates `formatToParts()` for interfaces that need individual localized fields.

The script also demonstrates:

- Locale negotiation with `supportedLocalesOf()`.
- Currency and number formatting with `Intl.NumberFormat`.
- Strict validation of ISO date-time input that includes an explicit UTC marker or numeric offset.
- Calendar-date validation that preserves the original `YYYY-MM-DD` components.
- Elapsed-time calculations using numeric epoch milliseconds.
- High-resolution performance measurements with Node.js `process.hrtime.bigint()`.
- An event scheduler that validates identifiers, rejects duplicate events, validates time-zone identifiers, and sorts records chronologically.

The high-resolution timer and `Date` serve different purposes. `Date` represents wall-clock instants. A monotonic or high-resolution performance clock is more suitable for measuring how long an operation takes because system wall clocks can be adjusted.

JavaScript's standard `Date` API does not provide general-purpose IANA-zone wall-time resolution with explicit control over every daylight-saving ambiguity. Applications requiring strict recurring-event scheduling should use a suitable time-zone-aware implementation rather than assume that every local date-time has one unique interpretation.

## C++ case study: international operations scheduling

The C++ program models an operations scheduler that records deployment reviews, security exercises, and infrastructure maintenance events.

### Architecture and data structures

`Instant` wraps a `system_clock::time_point`. Conversion functions expose epoch seconds and milliseconds. The UTC formatter generates a stable timestamp representation.

`CalendarDate` validates a year, month, and day. Its month-length calculation applies the Gregorian leap-year rules: a year is a leap year when divisible by four, except century years that are not divisible by 400.

`ZonedDisplay` represents a display label and an explicitly supplied UTC offset. It demonstrates how an instant can be rendered at a different offset, but it deliberately does not claim to resolve regional time-zone rules. Its offset must be correct for the instant being displayed.

`OperationsEvent` groups an identifier, title, instant, and display configuration. `OperationsScheduler` stores events in an `unordered_map`, rejects duplicate identifiers, looks up individual records, and creates a chronologically sorted report.

### Algorithmic behavior

Event insertion and identifier lookup are expected O(1) operations with a hash table, subject to normal hash-table behavior. Sorting a report containing n events takes O(n log n) time and O(n) additional storage for the result.

The program validates event fields before insertion and catches failures at the application boundary. Invalid dates, duplicate identifiers, and missing event lookups do not silently produce successful records.

The main limitation is time-zone support. C++17's standard library does not expose a portable IANA time-zone database interface. The program therefore uses UTC for actual instant calculations and explicit offsets for display examples. A production application that needs daylight-saving-aware regional scheduling must use a maintained time-zone database implementation.

## Java implementation: enterprise scheduling

Java's `java.time` package offers separate types for calendar dates, local clock readings, offset date-times, regional date-times, and instants.

The implementation demonstrates these distinctions directly:

| Java type | Meaning |
|---|---|
| `LocalDate` | Calendar date without time or zone |
| `LocalTime` | Clock time without date or zone |
| `LocalDateTime` | Local calendar and clock fields without zone |
| `OffsetDateTime` | Date-time fields with a fixed UTC offset |
| `Instant` | Global point on the timeline |
| `ZonedDateTime` | Date-time representation interpreted with regional zone rules |
| `ZoneId` | Regional zone identifier or a fixed-offset zone |

### Domain model and policy enforcement

`EventId` validates event identifiers. `EventRecord` requires an identifier, nonempty title, instant, and display zone. It offers localized display through `instant.atZone(displayZone)` and a stable API representation through `DateTimeFormatter.ISO_INSTANT`.

`EventScheduler` stores records by identifier, rejects duplicate scheduling attempts, returns explicit errors for missing events, and sorts events by their instants. Its synchronized methods illustrate a basic approach to protecting shared in-memory state from concurrent access.

The daylight-saving demonstration uses `ZoneRules.getValidOffsets()` to determine how many offsets are valid for a local date-time. Zero valid offsets means a gap; two valid offsets indicate an overlap.

`resolveUserWallTime()` makes that policy explicit. It rejects nonexistent times, requires an offset when the wall time is ambiguous, and rejects offsets that do not apply to the selected local time.

Java's `LocalDate.plusMonths()` and `ZonedDateTime.plusDays()` provide calendar-aware operations. These operations differ from adding a fixed number of elapsed hours. Applications must decide whether a requirement means the next calendar day at the same local time or exactly 24 hours later.

## PostgreSQL implementation: relational scheduling and auditing

The SQL script represents event scheduling with relational constraints and explicit audit records.

### Data model

| Table | Responsibility |
|---|---|
| `supported_zones` | Approved regional time-zone identifiers |
| `display_preferences` | User locale, preferred zone, and display styles |
| `scheduled_events` | Event identity, instant, zone, type, status, and optional original wall-time fields |
| `event_audit` | Event creation, status changes, and rescheduling history |

Primary keys identify records, unique constraints prevent duplicate event codes and preference owners, foreign keys enforce zone and event references, and `CHECK` constraints reject invalid statuses, event categories, empty identifiers, and unsupported style values.

The indexes support chronological scheduling queries, status-filtered event lists, and zone-based time ranges.

### Timestamp and regional conversion

PostgreSQL's `TIMESTAMPTZ` stores an instant normalized internally by PostgreSQL. It does not preserve the original IANA zone identifier supplied by the user. The separate `display_zone` field retains that context.

The `AT TIME ZONE` expression converts between an instant and a regional wall-clock value. In the view, the same event is shown in UTC and in the event's selected regional zone.

`TIMESTAMP WITHOUT TIME ZONE` represents local date-time fields without a global interpretation. The schema uses `DATE` and `TIME WITHOUT TIME ZONE` to retain optional original calendar and clock input. The application must verify that these values agree with the intended zone and instant.

### Queries and integrity enforcement

The script demonstrates chronological retrieval, regional date grouping, fixed-reference deadline evaluation, interval arithmetic, and audit-history queries.

The fixed reference instant in the deadline query makes the example reproducible. A live application can substitute `CURRENT_TIMESTAMP` when it needs to evaluate the actual current instant.

The audit trigger writes records when an event is inserted, its status changes, or its instant changes. The status constraint prevents an unsupported value such as `waiting` from being stored.

The schema intentionally does not claim that a `CHECK` constraint alone resolves daylight-saving ambiguity. Correct validation of user-entered regional wall times requires checking the zone rules and applying an explicit gap or overlap policy.

## Technical distinctions and operational risks

| Requirement | Appropriate representation | Important consideration |
|---|---|---|
| Store a completed event | UTC instant or `TIMESTAMPTZ` | Preserve the original zone separately if needed |
| Store a birthday | Calendar date | Do not shift it through UTC conversion |
| Schedule a recurring regional meeting | Local time plus IANA zone and recurrence rule | Recompute each occurrence using regional rules |
| Measure processing duration | Monotonic or elapsed-time clock | Wall clocks can be adjusted |
| Exchange a timestamp through an API | ISO 8601 with UTC marker or offset | Validate input and define precision |
| Display an event for a user | Instant, locale, and time zone | Formatting must not change the instant |
| Handle a daylight-saving overlap | Local date-time plus a selected offset or policy | The same wall time may map to two instants |
| Handle a daylight-saving gap | Local date-time plus an explicit resolution policy | The requested wall time may not exist |
| Calculate a month-end deadline | Calendar arithmetic | A month is not a fixed duration |
| Record audit history | Instant plus event and state-change metadata | Store event identity and changes consistently |

## Practical implementation considerations

### API contracts

Choose one canonical timestamp representation for external interfaces. UTC ISO 8601 strings are useful because they are explicit and readable. Numeric timestamps are also suitable when their unit is documented.

Do not infer timestamp units from the magnitude of a number. Do not accept an offset-free date-time as a global instant unless the API contract explicitly supplies the zone context.

### Recurring schedules

A recurring schedule is not simply an instant plus a fixed number of seconds. A request such as every weekday at 09:00 in London must preserve the recurrence rule and the `Europe/London` zone. Each future occurrence must be interpreted under the rules applicable to that date.

If the regional rules change, future occurrences may change their UTC instants while remaining at the intended local time.

### Data integrity and auditing

The database should enforce constraints that can be evaluated reliably from stored values. Application services should validate regional wall-time input against the relevant time-zone database and apply the system's scheduling policy.

For auditability, record the actual resolved instant, the relevant regional zone, and any user-selected offset or ambiguity decision. This helps explain why an event occurred at a particular instant.

### Internationalized presentation

Keep locale selection separate from time-zone selection. A user may prefer Indian English formatting while viewing an event scheduled in London. Locale determines formatting conventions; the regional zone determines the event's local clock representation.

Avoid parsing localized display strings as machine-readable timestamps. Month names, date order, numeral systems, and hour cycles vary between locales. Preserve canonical date-time data internally and localize it at the interface boundary.

### Testing and debugging

Test ordinary dates, month ends, leap days, negative or fractional timestamps where applicable, invalid input, and daylight-saving transitions. Include tests for both nonexistent and ambiguous local times.

For distributed applications, compare stored instants rather than formatted strings. Two timestamps with different offsets may identify the same instant. A display difference does not necessarily indicate a scheduling error.

The Python, JavaScript, C++, Java, and SQL artifacts illustrate complementary approaches to these requirements. Their representations differ, but they share one essential rule: calendar semantics, time-zone interpretation, global instants, and localized display must remain distinct.
