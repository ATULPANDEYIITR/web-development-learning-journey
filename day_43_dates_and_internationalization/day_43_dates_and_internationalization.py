#!/usr/bin/env python3
"""
Dates and Internationalization: practical Python implementation.

Demonstrates date and time values, Unix timestamps, parsing, formatting,
time-zone conversion, daylight-saving transitions, locale-aware output,
calendar arithmetic, interval calculations, validation, and serialization.

Requires Python 3.11 or later for the standard-library zoneinfo module
and reliable access to the IANA time-zone database. On systems without
an installed time-zone database, install the optional tzdata package.
"""

from __future__ import annotations

import calendar
import json
import math
import re
import time
import unittest

from dataclasses import asdict, dataclass
from datetime import date, datetime, time as ClockTime, timedelta, timezone
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


UTC = timezone.utc
ISO_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def heading(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def get_zone(name: str) -> ZoneInfo:
    """Load a named IANA time zone instead of relying on a fixed UTC offset."""
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"Unknown or unavailable time zone: {name}") from exc


def demonstrate_date_and_time_types() -> None:
    heading("Date and time types")

    today = date.today()
    current_local = datetime.now().astimezone()
    current_utc = datetime.now(UTC)
    meeting_time = ClockTime(hour=14, minute=30, second=0)

    print("Calendar date:", today.isoformat())
    print("Local aware datetime:", current_local.isoformat())
    print("UTC datetime:", current_utc.isoformat())
    print("Meeting clock time:", meeting_time.isoformat())
    print("Weekday, Monday=0:", today.weekday())
    print("Day of year:", today.timetuple().tm_yday)

    # A naive datetime has no offset or zone identity.
    naive = datetime(2026, 10, 13, 9, 0)
    print("Naive datetime:", naive.isoformat())
    print("Naive datetime has no reliable global instant:", naive.tzinfo is None)


def demonstrate_timestamps() -> None:
    heading("Unix timestamps")

    # A Unix timestamp counts seconds from 1970-01-01T00:00:00Z.
    timestamp = 1791878400
    instant = datetime.fromtimestamp(timestamp, UTC)

    print("Timestamp:", timestamp)
    print("Interpreted in UTC:", instant.isoformat())
    print("Converted back:", int(instant.timestamp()))

    fractional_timestamp = Decimal("1791878400.625")
    fractional_datetime = datetime.fromtimestamp(
        float(fractional_timestamp), UTC
    )
    print("Fractional timestamp:", fractional_datetime.isoformat())

    # Current timestamps should be obtained at runtime, not hard-coded.
    now_timestamp = time.time()
    print("Current Unix timestamp:", f"{now_timestamp:.3f}")

    # Python datetime has microsecond precision, not arbitrary nanosecond precision.
    nanoseconds = time.time_ns()
    print("Current Unix time in nanoseconds:", nanoseconds)

    try:
        datetime.fromtimestamp(float("inf"), UTC)
    except (OverflowError, OSError, ValueError) as exc:
        print("Invalid timestamp rejected:", type(exc).__name__)


def demonstrate_parsing_and_formatting() -> None:
    heading("Parsing and formatting")

    parsed = datetime.strptime("13/10/2026 15:45", "%d/%m/%Y %H:%M")
    print("Parsed naive value:", parsed.isoformat())
    print("Formatted date:", parsed.strftime("%A, %d %B %Y"))
    print("Formatted clock:", parsed.strftime("%I:%M %p"))

    iso_value = datetime.fromisoformat("2026-10-13T15:45:00+05:30")
    print("ISO 8601 value:", iso_value.isoformat())
    print("Equivalent UTC:", iso_value.astimezone(UTC).isoformat())

    try:
        datetime.strptime("31/02/2026", "%d/%m/%Y")
    except ValueError as exc:
        print("Invalid calendar date rejected:", exc)

    try:
        datetime.fromisoformat("2026-13-40T25:61:00")
    except ValueError as exc:
        print("Invalid ISO date-time rejected:", exc)

    # Strict application validation can reject formats that a permissive
    # parser might accept in a different representation.
    date_text = "2026-10-13"
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_text):
        raise ValueError("Expected YYYY-MM-DD")

    validated_date = date.fromisoformat(date_text)
    print("Validated date:", validated_date.isoformat())


def demonstrate_time_zones() -> None:
    heading("Time zones and daylight saving time")

    utc_instant = datetime(2026, 10, 13, 10, 0, tzinfo=UTC)
    zones = (
        "UTC",
        "Asia/Kolkata",
        "Europe/London",
        "America/New_York",
        "Australia/Sydney",
    )

    for zone_name in zones:
        local_value = utc_instant.astimezone(get_zone(zone_name))
        print(
            f"{zone_name:22} "
            f"{local_value.isoformat():35} "
            f"UTC offset={local_value.strftime('%z')}"
        )

    # Replace attaches a time zone to a wall-clock reading. It does not
    # convert an existing instant. Use astimezone for conversion.
    kolkata_wall_time = datetime(2026, 10, 13, 15, 30)
    kolkata_aware = kolkata_wall_time.replace(tzinfo=get_zone("Asia/Kolkata"))
    print("Localized wall time:", kolkata_aware.isoformat())
    print("Same instant in London:", kolkata_aware.astimezone(
        get_zone("Europe/London")
    ).isoformat())

    # This London wall time occurs twice when clocks move backward.
    repeated_first = datetime(
        2026, 10, 25, 1, 30,
        tzinfo=get_zone("Europe/London"),
        fold=0,
    )
    repeated_second = datetime(
        2026, 10, 25, 1, 30,
        tzinfo=get_zone("Europe/London"),
        fold=1,
    )

    print("First occurrence:", repeated_first.isoformat())
    print("Second occurrence:", repeated_second.isoformat())
    print("First occurrence in UTC:", repeated_first.astimezone(UTC).isoformat())
    print("Second occurrence in UTC:", repeated_second.astimezone(UTC).isoformat())

    # A nonexistent wall time can be constructed by datetime, so input
    # validation must detect round-trip mismatches when user input matters.
    nonexistent = datetime(
        2026, 3, 29, 1, 30,
        tzinfo=get_zone("Europe/London"),
    )
    round_trip = nonexistent.astimezone(UTC).astimezone(
        get_zone("Europe/London")
    )
    print("Spring transition input:", nonexistent.isoformat())
    print("Round-trip result:", round_trip.isoformat())
    print("Wall time exists:", round_trip.replace(tzinfo=None)
          == nonexistent.replace(tzinfo=None))


def valid_local_candidates(
    wall_time: datetime,
    zone_name: str,
) -> list[datetime]:
    """
    Return valid aware interpretations of a naive wall-clock datetime.

    Zero candidates means a nonexistent local time.
    One candidate means an unambiguous local time.
    Two candidates means an ambiguous local time during a clock rollback.
    """
    if wall_time.tzinfo is not None:
        raise ValueError("Expected a naive local wall-clock datetime")

    zone = get_zone(zone_name)
    candidates: dict[datetime, datetime] = {}

    for fold in (0, 1):
        candidate = wall_time.replace(tzinfo=zone, fold=fold)
        round_trip = candidate.astimezone(UTC).astimezone(zone)

        if round_trip.replace(tzinfo=None) == wall_time:
            # Deduplicate ordinary times whose fold values map to one instant.
            candidates[candidate.astimezone(UTC)] = candidate

    return list(candidates.values())


def demonstrate_local_time_validation() -> None:
    heading("Validating local wall-clock input")

    test_values = (
        datetime(2026, 3, 29, 1, 30),
        datetime(2026, 10, 25, 1, 30),
        datetime(2026, 10, 13, 12, 0),
    )

    for value in test_values:
        candidates = valid_local_candidates(value, "Europe/London")
        if not candidates:
            classification = "nonexistent"
        elif len(candidates) == 2:
            classification = "ambiguous"
        else:
            classification = "unambiguous"

        print(value.isoformat(), "->", classification)
        for candidate in candidates:
            print("  Valid instant:", candidate.astimezone(UTC).isoformat())


def demonstrate_arithmetic() -> None:
    heading("Date arithmetic and elapsed time")

    start = datetime(2026, 10, 13, 9, 0, tzinfo=UTC)
    duration = timedelta(hours=8, minutes=45)
    finish = start + duration

    print("Start:", start.isoformat())
    print("Finish:", finish.isoformat())
    print("Elapsed:", finish - start)

    today = date(2026, 10, 13)
    print("Seven calendar days later:", today + timedelta(days=7))
    print("Days in October 2026:", calendar.monthrange(2026, 10)[1])

    # Calendar months are not fixed durations. Clamp the day to the
    # destination month's last valid day.
    def add_months(value: date, months: int) -> date:
        month_index = value.year * 12 + value.month - 1 + months
        year, zero_based_month = divmod(month_index, 12)
        month = zero_based_month + 1
        day = min(value.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)

    print("One month after January 31:", add_months(date(2026, 1, 31), 1))
    print("One month before March 31:", add_months(date(2026, 3, 31), -1))

    # Compare instants in UTC when measuring actual elapsed time across
    # daylight-saving transitions.
    before_transition = datetime(
        2026, 3, 29, 0, 30, tzinfo=get_zone("Europe/London")
    )
    after_transition = datetime(
        2026, 3, 29, 2, 30, tzinfo=get_zone("Europe/London")
    )

    elapsed = after_transition.astimezone(UTC) - before_transition.astimezone(UTC)
    print("Wall-clock difference:", after_transition.replace(tzinfo=None)
          - before_transition.replace(tzinfo=None))
    print("Actual elapsed difference:", elapsed)


def demonstrate_internationalization() -> None:
    heading("Internationalization and localization")

    # Locale configuration depends on the operating system and installed
    # locales. Avoid changing the process-wide locale in concurrent services.
    instant = datetime(2026, 10, 13, 15, 30, tzinfo=UTC)

    examples = {
        "ISO": instant.strftime("%Y-%m-%d %H:%M UTC"),
        "US-style": instant.strftime("%m/%d/%Y %I:%M %p UTC"),
        "India-style": instant.strftime("%d/%m/%Y %H:%M UTC"),
        "European-style": instant.strftime("%d.%m.%Y %H:%M UTC"),
    }

    for label, value in examples.items():
        print(f"{label:18} {value}")

    localized = instant.astimezone(get_zone("Asia/Kolkata"))
    print("India local ISO:", localized.isoformat())

    # Locale-specific month names require the corresponding locale to be
    # installed and configured. Explicit numeric formats are more portable.
    print("Portable numeric date:", localized.strftime("%d-%m-%Y"))


def demonstrate_serialization() -> None:
    heading("Serialization and API boundaries")

    event_time = datetime(
        2026, 10, 13, 15, 30, 45, 123456,
        tzinfo=get_zone("Asia/Kolkata"),
    )

    payload = {
        "event": "deployment_review",
        "occurred_at": event_time.isoformat(),
        "occurred_at_utc": event_time.astimezone(UTC).isoformat(),
        "unix_timestamp": event_time.timestamp(),
        "timezone": "Asia/Kolkata",
    }

    encoded = json.dumps(payload, indent=2)
    print(encoded)

    decoded: dict[str, Any] = json.loads(encoded)
    restored = datetime.fromisoformat(decoded["occurred_at"])

    if restored.astimezone(UTC) != event_time.astimezone(UTC):
        raise AssertionError("Serialization changed the instant")

    print("Restored instant:", restored.astimezone(UTC).isoformat())

    # JSON does not natively serialize datetime values. Convert them to
    # ISO 8601 strings or explicit numeric timestamps before encoding.
    try:
        json.dumps({"time": event_time})
    except TypeError as exc:
        print("Raw datetime serialization rejected:", type(exc).__name__)


@dataclass(frozen=True)
class ScheduledEvent:
    event_id: str
    title: str
    instant_utc: datetime
    display_zone: str

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("Event ID must not be empty")
        if not self.title.strip():
            raise ValueError("Event title must not be empty")
        if self.instant_utc.tzinfo is None:
            raise ValueError("Event instant must be timezone-aware")
        if self.instant_utc.utcoffset() is None:
            raise ValueError("Event instant must have a valid UTC offset")

        # Normalize stored instants so equivalent offsets use one representation.
        object.__setattr__(self, "instant_utc", self.instant_utc.astimezone(UTC))
        get_zone(self.display_zone)

    def as_api_record(self) -> dict[str, Any]:
        local_time = self.instant_utc.astimezone(get_zone(self.display_zone))
        return {
            "event_id": self.event_id,
            "title": self.title,
            "instant_utc": self.instant_utc.isoformat(),
            "display_time": local_time.isoformat(),
            "display_zone": self.display_zone,
            "unix_timestamp": self.instant_utc.timestamp(),
        }


def demonstrate_event_scheduler() -> None:
    heading("Event scheduling across time zones")

    events = [
        ScheduledEvent(
            "DEP-104",
            "Production deployment review",
            datetime(2026, 10, 13, 9, 0, tzinfo=UTC),
            "Asia/Kolkata",
        ),
        ScheduledEvent(
            "SEC-207",
            "Security incident exercise",
            datetime(2026, 10, 13, 15, 0, tzinfo=UTC),
            "Europe/London",
        ),
        ScheduledEvent(
            "OPS-315",
            "Infrastructure maintenance",
            datetime(2026, 10, 14, 1, 0, tzinfo=UTC),
            "America/New_York",
        ),
    ]

    events.sort(key=lambda event: event.instant_utc)

    for event in events:
        print(json.dumps(event.as_api_record(), indent=2))

    try:
        ScheduledEvent(
            "INVALID",
            "Naive event",
            datetime(2026, 10, 13, 9, 0),
            "UTC",
        )
    except ValueError as exc:
        print("Invalid scheduled event rejected:", exc)


class DateTimeTests(unittest.TestCase):
    def test_timestamp_round_trip(self) -> None:
        original = datetime(2026, 10, 13, 10, 0, tzinfo=UTC)
        restored = datetime.fromtimestamp(original.timestamp(), UTC)
        self.assertEqual(original, restored)

    def test_equivalent_instants(self) -> None:
        utc_value = datetime(2026, 10, 13, 10, 0, tzinfo=UTC)
        india_value = utc_value.astimezone(get_zone("Asia/Kolkata"))
        self.assertEqual(utc_value, india_value)

    def test_wall_time_gap(self) -> None:
        gap = datetime(2026, 3, 29, 1, 30)
        self.assertEqual(valid_local_candidates(gap, "Europe/London"), [])

    def test_wall_time_overlap(self) -> None:
        overlap = datetime(2026, 10, 25, 1, 30)
        self.assertEqual(len(valid_local_candidates(overlap, "Europe/London")), 2)

    def test_month_arithmetic(self) -> None:
        value = date(2026, 1, 31)
        result = date(2026, 2, calendar.monthrange(2026, 2)[1])
        self.assertEqual(result, date(2026, 2, 28))
        self.assertEqual(value.month, 1)

    def test_event_normalizes_utc(self) -> None:
        event = ScheduledEvent(
            "EVT-1",
            "Review",
            datetime(2026, 10, 13, 15, 30, tzinfo=get_zone("Asia/Kolkata")),
            "UTC",
        )
        self.assertEqual(event.instant_utc.tzinfo, UTC)
        self.assertEqual(event.instant_utc.hour, 10)

    def test_empty_identifier_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ScheduledEvent(
                "",
                "Review",
                datetime(2026, 10, 13, 10, 0, tzinfo=UTC),
                "UTC",
            )

    def test_nonexistent_local_time(self) -> None:
        candidates = valid_local_candidates(
            datetime(2026, 3, 29, 1, 30), "Europe/London"
        )
        self.assertFalse(candidates)


def run_tests() -> None:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DateTimeTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


def main() -> None:
    demonstrate_date_and_time_types()
    demonstrate_timestamps()
    demonstrate_parsing_and_formatting()
    demonstrate_time_zones()
    demonstrate_local_time_validation()
    demonstrate_arithmetic()
    demonstrate_internationalization()
    demonstrate_serialization()
    demonstrate_event_scheduler()
    heading("Automated validation")
    run_tests()


if __name__ == "__main__":
    main()
