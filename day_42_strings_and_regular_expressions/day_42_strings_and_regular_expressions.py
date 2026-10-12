#!/usr/bin/env python3
"""Practical string processing and regular-expression demonstrations.

Uses only the Python standard library. Run with Python 3.10 or later.
"""

from __future__ import annotations

import re
import string
import unittest
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


def demonstrate_string_methods() -> None:
    print("\n=== String methods and normalization ===")

    raw = "  Order-2026-0042:  Network Switches  "
    normalized = raw.strip()

    print("Original:", repr(raw))
    print("Trimmed:", normalized)
    print("Lowercase:", normalized.lower())
    print("Uppercase:", normalized.upper())
    print("Title:", normalized.title())
    print("Replace:", normalized.replace("Switches", "Routers"))
    print("Starts with Order:", normalized.startswith("Order"))
    print("Ends with Switches:", normalized.endswith("Switches"))
    print("Split:", normalized.split())
    print("Join:", " | ".join(["procurement", "inventory", "delivery"]))
    print("Contains digits:", any(character.isdigit() for character in normalized))
    print("Partition:", normalized.partition(":"))

    amount_text = "  125000.50  "
    amount = float(amount_text.strip())
    print(f"Formatted amount: ₹{amount:,.2f}")

    # Strings are immutable. replace() returns a new string.
    original = "pending"
    changed = original.replace("pending", "approved")
    print("Original remains:", original)
    print("New value:", changed)

    # splitlines() handles common newline conventions.
    report = "Received\nInspected\r\nStored"
    print("Report lines:", report.splitlines())

    # translate() efficiently removes a known set of characters.
    punctuation_table = str.maketrans("", "", string.punctuation)
    print("Punctuation removed:", "switch-A/B".translate(punctuation_table))


def demonstrate_template_literals_equivalent() -> None:
    print("\n=== Python formatted strings ===")

    order_id = "PO-2026-0184"
    supplier = "Northstar Components"
    quantity = 240
    unit_price = 875.50
    total = quantity * unit_price

    # f-strings evaluate expressions and support formatting specifications.
    print(f"Purchase order: {order_id}")
    print(f"Supplier: {supplier}")
    print(f"Quantity: {quantity:,}")
    print(f"Unit price: ₹{unit_price:,.2f}")
    print(f"Total: ₹{total:,.2f}")

    multiline = (
        f"Purchase order {order_id}\n"
        f"Supplier: {supplier}\n"
        f"Total payable: ₹{total:,.2f}"
    )
    print(multiline)


def demonstrate_regex_syntax() -> None:
    print("\n=== Regular-expression syntax ===")

    text = "Tickets INC-1042, INC-1043 and INC-2088 are open."

    # Raw strings prevent Python from interpreting regex backslashes first.
    ticket_pattern = re.compile(r"\bINC-\d{4}\b")
    print("Ticket IDs:", ticket_pattern.findall(text))

    examples = {
        "literal": re.compile(r"cat"),
        "digit": re.compile(r"\d"),
        "word character": re.compile(r"\w+"),
        "whitespace": re.compile(r"\s+"),
        "start and end": re.compile(r"^Approved$"),
        "one or more": re.compile(r"a+"),
        "optional character": re.compile(r"colou?r"),
        "alternation": re.compile(r"cat|dog"),
        "character class": re.compile(r"[A-F0-9]+"),
        "named group": re.compile(r"(?P<year>\d{4})-(?P<month>\d{2})"),
    }

    for name, pattern in examples.items():
        print(f"{name}: {pattern.pattern}")

    match = examples["named group"].search("Processed on 2026-10")
    if match:
        print("Named groups:", match.groupdict())

    # Greedy quantifiers consume as much as possible; lazy quantifiers
    # stop at the first match that satisfies the remaining pattern.
    sample = "<item>switch</item><item>router</item>"
    print("Greedy:", re.findall(r"<item>.*</item>", sample))
    print("Lazy:", re.findall(r"<item>.*?</item>", sample))


def demonstrate_matching_and_replacing() -> None:
    print("\n=== Matching, searching, splitting, and replacing ===")

    email_text = "Contact ops@example.com or support@example.org."
    email_pattern = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")

    print("First match:", email_pattern.search(email_text).group())
    print("All matches:", email_pattern.findall(email_text))
    print("Match at beginning:", bool(email_pattern.match(email_text)))
    print("Full string match:", bool(email_pattern.fullmatch(email_text)))

    # sub() can use capture groups to transform matching text.
    date_text = "Deployment date: 2026-10-12"
    converted = re.sub(
        r"(\d{4})-(\d{2})-(\d{2})",
        r"\3/\2/\1",
        date_text,
    )
    print("Reformatted date:", converted)

    # A callback performs conditional transformations.
    def redact_email(match: re.Match[str]) -> str:
        address = match.group()
        local, domain = address.split("@", 1)
        return f"{local[:1]}***@{domain}"

    print("Redacted:", email_pattern.sub(redact_email, email_text))

    fields = "PO-1001,PO-1002;PO-1003 | PO-1004"
    print("Split on multiple separators:", re.split(r"[,;|]\s*", fields))

    # Count replacements to verify the expected number of changes.
    result, count = re.subn(r"\bPENDING\b", "APPROVED", "PENDING / PENDING")
    print("Updated:", result, "Replacement count:", count)


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    normalized: str
    message: str


class InputValidator:
    """Validates common business inputs with explicit rules."""

    ORDER_ID = re.compile(r"PO-\d{4}-\d{4}")
    POSTAL_CODE = re.compile(r"\d{6}")
    USERNAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,19}")
    PHONE = re.compile(r"\+91[6-9]\d{9}")
    ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
    EMAIL = re.compile(
        r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
        r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+"
    )

    @staticmethod
    def _result(value: str, message: str) -> ValidationResult:
        return ValidationResult(message == "Valid", value, message)

    @classmethod
    def validate_order_id(cls, value: str) -> ValidationResult:
        normalized = value.strip().upper()
        if not cls.ORDER_ID.fullmatch(normalized):
            return cls._result(normalized, "Expected PO-YYYY-NNNN")
        return cls._result(normalized, "Valid")

    @classmethod
    def validate_username(cls, value: str) -> ValidationResult:
        normalized = value.strip()
        if not cls.USERNAME.fullmatch(normalized):
            return cls._result(
                normalized,
                "Use 3-20 ASCII letters, digits, or underscores; start with a letter",
            )
        return cls._result(normalized, "Valid")

    @classmethod
    def validate_phone(cls, value: str) -> ValidationResult:
        normalized = re.sub(r"[\s-]", "", value)
        if not cls.PHONE.fullmatch(normalized):
            return cls._result(normalized, "Expected an Indian mobile number in +91 format")
        return cls._result(normalized, "Valid")

    @classmethod
    def validate_postal_code(cls, value: str) -> ValidationResult:
        normalized = value.strip()
        if not cls.POSTAL_CODE.fullmatch(normalized):
            return cls._result(normalized, "Expected exactly six digits")
        return cls._result(normalized, "Valid")

    @classmethod
    def validate_email(cls, value: str) -> ValidationResult:
        normalized = value.strip()
        if len(normalized) > 254 or not cls.EMAIL.fullmatch(normalized):
            return cls._result(normalized, "Invalid email syntax")
        if len(normalized.rsplit("@", 1)[0]) > 64:
            return cls._result(normalized, "Email local part exceeds 64 characters")
        return cls._result(normalized, "Valid syntax; ownership is not verified")

    @classmethod
    def validate_iso_date(cls, value: str) -> ValidationResult:
        normalized = value.strip()
        if not cls.ISO_DATE.fullmatch(normalized):
            return cls._result(normalized, "Expected YYYY-MM-DD")
        try:
            datetime.strptime(normalized, "%Y-%m-%d")
        except ValueError:
            return cls._result(normalized, "Date does not exist")
        return cls._result(normalized, "Valid")


def demonstrate_validation() -> None:
    print("\n=== Input validation ===")

    cases: list[tuple[str, str, object]] = [
        ("Order ID", " po-2026-0184 ", InputValidator.validate_order_id),
        ("Order ID", "PO-26-184", InputValidator.validate_order_id),
        ("Username", "atul_pandey7", InputValidator.validate_username),
        ("Username", "7atul", InputValidator.validate_username),
        ("Phone", "+91 98765 43210", InputValidator.validate_phone),
        ("Postal code", "226001", InputValidator.validate_postal_code),
        ("Postal code", "2260A1", InputValidator.validate_postal_code),
        ("Email", "operations@example.com", InputValidator.validate_email),
        ("Date", "2024-02-29", InputValidator.validate_iso_date),
        ("Date", "2025-02-29", InputValidator.validate_iso_date),
    ]

    for label, value, validator in cases:
        result = validator(value)  # type: ignore[operator]
        print(f"{label:12} {value!r:30} {result.valid!s:5} {result.message}")


def extract_log_events(lines: Iterable[str]) -> list[dict[str, str]]:
    """Parse structured log lines without assuming every line is valid."""
    pattern = re.compile(
        r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T"
        r"\d{2}:\d{2}:\d{2}Z)\s+"
        r"(?P<level>INFO|WARNING|ERROR)\s+"
        r"request_id=(?P<request_id>[A-Za-z0-9-]+)\s+"
        r"message=(?P<message>.*)$"
    )

    events: list[dict[str, str]] = []
    for line in lines:
        match = pattern.fullmatch(line.strip())
        if match:
            events.append(match.groupdict())
        else:
            print("Rejected malformed log line:", repr(line))
    return events


def demonstrate_log_processing() -> None:
    print("\n=== Log processing ===")

    lines = [
        "2026-10-12T08:30:00Z INFO request_id=req-101 message=Order accepted",
        "2026-10-12T08:30:03Z WARNING request_id=req-102 message=Retry scheduled",
        "2026-10-12T08:30:05Z ERROR request_id=req-103 message=Payment failed",
        "broken record without expected fields",
    ]

    events = extract_log_events(lines)
    error_events = [event for event in events if event["level"] == "ERROR"]

    print("Valid events:", len(events))
    print("Errors:", error_events)

    counts: dict[str, int] = {}
    for event in events:
        counts[event["level"]] = counts.get(event["level"], 0) + 1
    print("Counts by level:", counts)


def demonstrate_regex_performance_and_safety() -> None:
    print("\n=== Regex safety and design ===")

    # Compiling a frequently reused pattern avoids repeatedly parsing it.
    pattern = re.compile(r"\b[A-Z]{3}-\d{6}\b")
    identifiers = ["INV-123456", "PO-123456", "INV-12345X", "INV-654321"]

    valid = [identifier for identifier in identifiers if pattern.fullmatch(identifier)]
    print("Valid invoice identifiers:", valid)

    # Nested ambiguous repetition such as (a+)+ can exhibit catastrophic
    # backtracking on hostile input. Prefer bounded, unambiguous patterns.
    safe_pattern = re.compile(r"a{1,100}b")
    print("Safe bounded pattern:", bool(safe_pattern.fullmatch("a" * 50 + "b")))

    # A regex validates syntax, not business existence, authorization, or ownership.
    print("Syntax validation does not prove that a mailbox exists.")

    # For arbitrary literal text, escape it before embedding it in a regex.
    literal = "PO.2026"
    safe_literal_pattern = re.compile(re.escape(literal))
    print("Escaped literal match:", bool(safe_literal_pattern.search("Reference PO.2026")))


class StringRegexTests(unittest.TestCase):
    def test_order_id(self) -> None:
        self.assertTrue(InputValidator.validate_order_id("po-2026-0001").valid)
        self.assertFalse(InputValidator.validate_order_id("PO-2026-1").valid)

    def test_date_calendar_validation(self) -> None:
        self.assertTrue(InputValidator.validate_iso_date("2024-02-29").valid)
        self.assertFalse(InputValidator.validate_iso_date("2025-02-29").valid)

    def test_email_syntax(self) -> None:
        self.assertTrue(InputValidator.validate_email("ops@example.com").valid)
        self.assertFalse(InputValidator.validate_email("ops@localhost").valid)

    def test_phone_normalization(self) -> None:
        result = InputValidator.validate_phone("+91 98765 43210")
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized, "+919876543210")

    def test_replacement(self) -> None:
        result, count = re.subn("pending", "approved", "pending pending")
        self.assertEqual(result, "approved approved")
        self.assertEqual(count, 2)

    def test_malformed_logs_are_rejected(self) -> None:
        self.assertEqual(extract_log_events(["invalid"]), [])

    def test_username_rejects_unicode_digits(self) -> None:
        self.assertFalse(InputValidator.validate_username("atul١٢٣").valid)


def main() -> None:
    demonstrate_string_methods()
    demonstrate_template_literals_equivalent()
    demonstrate_regex_syntax()
    demonstrate_matching_and_replacing()
    demonstrate_validation()
    demonstrate_log_processing()
    demonstrate_regex_performance_and_safety()

    print("\n=== Automated checks ===")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(StringRegexTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
