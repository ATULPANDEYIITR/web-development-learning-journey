"""
React Events and Forms: Event Handling, Form State, and Validation

A self-contained simulation of React-inspired event and form behavior.
Demonstrates:
- Event handling and propagation
- Event objects and event delegation
- Controlled and uncontrolled inputs
- Form state management
- Synchronous and asynchronous validation
- Field-level and cross-field validation
- Submission lifecycle
- Error handling and security
- Unit-style assertions

Run: python react_events_forms.py
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class EventType(Enum):
    CLICK = "click"
    CHANGE = "change"
    INPUT = "input"
    SUBMIT = "submit"
    BLUR = "blur"
    FOCUS = "focus"


class FormStatus(Enum):
    IDLE = "idle"
    DIRTY = "dirty"
    VALIDATING = "validating"
    INVALID = "invalid"
    SUBMITTING = "submitting"
    SUBMITTED = "submitted"


class FormError(Exception):
    pass


class ValidationError(FormError):
    pass


class SubmissionError(FormError):
    pass


@dataclass
class Event:
    event_type: EventType
    target: str
    value: Any = None
    bubbles: bool = True
    default_prevented: bool = False
    propagation_stopped: bool = False
    timestamp: float = field(default_factory=time.time)

    def prevent_default(self) -> None:
        self.default_prevented = True

    def stop_propagation(self) -> None:
        self.propagation_stopped = True


class EventEmitter:
    """Supports ordered handlers and controlled event propagation."""

    def __init__(self):
        self._handlers: dict[EventType, list[Callable]] = {}

    def on(self, event_type: EventType, handler: Callable) -> None:
        if not callable(handler):
            raise TypeError("Handler must be callable")
        self._handlers.setdefault(event_type, []).append(handler)

    def off(self, event_type: EventType, handler: Callable) -> None:
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def emit(self, event: Event) -> None:
        for handler in tuple(self._handlers.get(event.event_type, [])):
            handler(event)
            if event.propagation_stopped:
                break


class EventNode:
    """Models a simple parent-child event tree."""

    def __init__(self, name: str, parent: EventNode | None = None):
        self.name = name
        self.parent = parent
        self.emitter = EventEmitter()

    def dispatch(self, event: Event) -> None:
        node: EventNode | None = self

        while node is not None:
            node.emitter.emit(event)

            if event.propagation_stopped or not event.bubbles:
                break

            node = node.parent


@dataclass
class Field:
    name: str
    value: Any = ""
    required: bool = False
    input_type: str = "text"
    max_length: int = 255
    touched: bool = False
    controlled: bool = True
    initial_value: Any = ""

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Field name cannot be empty")

        if self.max_length < 1:
            raise ValueError("Maximum length must be positive")

        self.initial_value = self.value


class Validator:
    """Centralizes field-level and cross-field validation."""

    EMAIL_PATTERN = re.compile(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    @staticmethod
    def validate_field(name: str, value: Any, rules: dict) -> list[str]:
        errors = []

        if value is None:
            value = ""

        text = str(value)

        if rules.get("required") and not text.strip():
            errors.append("This field is required.")
            return errors

        if not text.strip():
            return errors

        if len(text) > rules.get("max_length", 255):
            errors.append("Maximum length exceeded.")

        if rules.get("email") and not Validator.EMAIL_PATTERN.fullmatch(text):
            errors.append("Enter a valid email address.")

        if rules.get("min_length") and len(text) < rules["min_length"]:
            errors.append(
                f"Minimum length is {rules['min_length']} characters."
            )

        if rules.get("pattern") and not re.fullmatch(rules["pattern"], text):
            errors.append("Value does not match the required format.")

        if rules.get("numeric"):
            try:
                number = float(text)
                if not number == number or abs(number) == float("inf"):
                    raise ValueError
            except ValueError:
                errors.append("Enter a finite numeric value.")

        if rules.get("minimum") is not None:
            try:
                if float(text) < rules["minimum"]:
                    errors.append("Value is below the minimum.")
            except ValueError:
                pass

        if rules.get("maximum") is not None:
            try:
                if float(text) > rules["maximum"]:
                    errors.append("Value exceeds the maximum.")
            except ValueError:
                pass

        return errors


class Form:
    def __init__(self, fields: list[Field], rules: dict[str, dict]):
        names = [field.name for field in fields]

        if len(names) != len(set(names)):
            raise ValueError("Duplicate field names are not allowed")

        if set(rules) - set(names):
            raise ValueError("Validation rules reference unknown fields")

        self.fields = {item.name: item for item in fields}
        self.rules = rules
        self.errors: dict[str, list[str]] = {}
        self.status = FormStatus.IDLE
        self.submission_count = 0
        self.events = EventEmitter()

    @property
    def values(self) -> dict[str, Any]:
        return {
            name: item.value
            for name, item in self.fields.items()
        }

    def set_value(self, name: str, value: Any) -> None:
        if name not in self.fields:
            raise FormError(f"Unknown field: {name}")

        item = self.fields[name]

        if not item.controlled:
            raise FormError(
                f"{name} is uncontrolled. Use set_uncontrolled_value()."
            )

        item.value = value
        item.touched = True
        self.status = FormStatus.DIRTY

        self.events.emit(
            Event(EventType.CHANGE, target=name, value=value)
        )

    def set_uncontrolled_value(self, name: str, value: Any) -> None:
        if name not in self.fields:
            raise FormError(f"Unknown field: {name}")

        item = self.fields[name]

        if item.controlled:
            raise FormError(f"{name} is controlled.")

        item.value = value
        item.touched = True
        self.status = FormStatus.DIRTY

    def reset(self) -> None:
        for item in self.fields.values():
            item.value = item.initial_value
            item.touched = False

        self.errors.clear()
        self.status = FormStatus.IDLE

        self.events.emit(
            Event(EventType.CHANGE, target="form", value=self.values)
        )

    def validate(self) -> bool:
        self.status = FormStatus.VALIDATING
        self.errors.clear()

        for name, item in self.fields.items():
            field_rules = {
                "required": item.required,
                "max_length": item.max_length,
                **self.rules.get(name, {})
            }

            errors = Validator.validate_field(
                name, item.value, field_rules
            )

            if errors:
                self.errors[name] = errors

        # Cross-field validation.
        password = self.values.get("password")
        confirmation = self.values.get("confirm_password")

        if (
            password is not None
            and confirmation is not None
            and password != confirmation
        ):
            self.errors.setdefault(
                "confirm_password", []
            ).append("Passwords do not match.")

        self.status = (
            FormStatus.INVALID if self.errors
            else FormStatus.IDLE
        )

        return not self.errors

    async def validate_async(self) -> bool:
        self.status = FormStatus.VALIDATING

        # Represents a remote validation operation.
        await asyncio.sleep(0.01)

        valid = self.validate()

        email = self.values.get("email", "")

        if email.lower() == "taken@example.com":
            self.errors.setdefault("email", []).append(
                "This email address is already registered."
            )
            valid = False
            self.status = FormStatus.INVALID

        return valid

    async def submit(
        self,
        handler: Callable[[dict], Any]
    ) -> dict:
        if self.status == FormStatus.SUBMITTING:
            raise SubmissionError("Submission already in progress.")

        if not await self.validate_async():
            self.events.emit(
                Event(EventType.SUBMIT, "form", self.values)
            )
            raise ValidationError(str(self.errors))

        self.status = FormStatus.SUBMITTING

        try:
            result = handler(self.values.copy())

            if asyncio.iscoroutine(result):
                result = await result

            self.submission_count += 1
            self.status = FormStatus.SUBMITTED

            self.events.emit(
                Event(EventType.SUBMIT, "form", self.values)
            )

            return result

        except Exception as exc:
            self.status = FormStatus.DIRTY
            raise SubmissionError(
                f"Submission failed: {exc}"
            ) from exc


async def register_user(data: dict) -> dict:
    """Simulates a backend registration service."""

    await asyncio.sleep(0.01)

    if data["email"].lower() == "failure@example.com":
        raise RuntimeError("Registration service unavailable")

    # Never return or log passwords.
    return {
        "user": data["username"],
        "email": data["email"],
        "created": True
    }


async def demonstrate_event_propagation():
    print("\n--- EVENT PROPAGATION ---")

    parent = EventNode("form")
    child = EventNode("submit-button", parent)

    parent.emitter.on(
        EventType.CLICK,
        lambda event: print("Parent received click")
    )

    child.emitter.on(
        EventType.CLICK,
        lambda event: print("Button received click")
    )

    child.dispatch(Event(EventType.CLICK, "submit-button"))

    print("\n--- STOP PROPAGATION ---")

    child.emitter.on(
        EventType.CLICK,
        lambda event: event.stop_propagation()
    )

    child.dispatch(Event(EventType.CLICK, "submit-button"))


async def demonstrate_form():
    print("\n--- FORM MANAGEMENT ---")

    fields = [
        Field("username", required=True, max_length=30),
        Field("email", required=True, max_length=100),
        Field("password", required=True, max_length=128),
        Field("confirm_password", required=True, max_length=128),
        Field(
            "newsletter",
            value=False,
            controlled=False,
            input_type="checkbox"
        )
    ]

    rules = {
        "username": {"min_length": 3},
        "email": {"email": True},
        "password": {"min_length": 8}
    }

    form = Form(fields, rules)

    form.set_value("username", "atul")
    form.set_value("email", "atul@example.com")
    form.set_value("password", "SecurePass123")
    form.set_value("confirm_password", "SecurePass123")

    # Uncontrolled inputs are read from their current field value.
    form.set_uncontrolled_value("newsletter", True)

    print("Current values:", form.values)

    form.events.on(
        EventType.SUBMIT,
        lambda event: print("Submit event dispatched")
    )

    try:
        result = await form.submit(register_user)
        print("Submission result:", result)
        print("Status:", form.status.value)

    except FormError as exc:
        print("Form error:", exc)

    print("\n--- VALIDATION FAILURE ---")

    form.set_value("email", "invalid-email")
    form.set_value("confirm_password", "DifferentPassword")

    try:
        await form.submit(register_user)
    except FormError as exc:
        print("Rejected:", exc)
        print("Field errors:", form.errors)

    print("\n--- RESET ---")

    form.reset()
    print("Values after reset:", form.values)
    print("Status:", form.status.value)

    print("\n--- SERVER FAILURE ---")

    form.set_value("username", "atul")
    form.set_value("email", "failure@example.com")
    form.set_value("password", "SecurePass123")
    form.set_value("confirm_password", "SecurePass123")

    try:
        await form.submit(register_user)
    except SubmissionError as exc:
        print("Handled:", exc)
        print("Recovery status:", form.status.value)


def run_tests():
    print("\n--- ASSERTION TESTS ---")

    assert Validator.validate_field(
        "email", "person@example.com", {"email": True}
    ) == []

    assert Validator.validate_field(
        "email", "invalid", {"email": True}
    )

    form = Form(
        [Field("name", required=True)],
        {}
    )

    assert form.validate() is False

    form.set_value("name", "Example")
    assert form.validate() is True

    form.reset()
    assert form.values["name"] == ""

    try:
        form.set_value("missing", "value")
        raise AssertionError("Unknown field should fail")
    except FormError:
        pass

    try:
        form.set_value("name", None)
        assert form.validate() is False
    except Exception as exc:
        raise AssertionError("Unexpected failure") from exc

    print("All tests passed.")


async def main():
    print("REACT EVENTS AND FORMS SIMULATION")

    await demonstrate_event_propagation()
    await demonstrate_form()
    run_tests()


if __name__ == "__main__":
    asyncio.run(main())
