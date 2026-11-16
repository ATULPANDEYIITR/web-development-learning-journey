"""
React Context: Context API, Providers, Consumers, and Global State Patterns

Python reference implementation of context-based state management.
Models provider scopes, consumer subscriptions, immutable updates,
selectors, nested contexts, batching, and state isolation.

Run:
    python react_context.py
"""

from __future__ import annotations

import copy
import json
import logging
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Generic, TypeVar

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

T = TypeVar("T")
Selector = Callable[[dict[str, Any]], T]
Listener = Callable[[Any, Any], None]


class ContextError(Exception):
    """Base exception for context management."""


class ProviderNotFoundError(ContextError):
    """Raised when a consumer cannot locate its provider."""


class DuplicateProviderError(ContextError):
    """Raised when a scope contains a duplicate provider."""


class ValidationError(ContextError):
    """Raised when invalid state is supplied."""


class ActionType(Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    UPDATE_PROFILE = "UPDATE_PROFILE"
    SET_THEME = "SET_THEME"
    SET_LANGUAGE = "SET_LANGUAGE"
    RESET = "RESET"


@dataclass(frozen=True)
class Action:
    type: ActionType
    payload: dict[str, Any] = field(default_factory=dict)


def validate_state(state: dict[str, Any]) -> None:
    if not isinstance(state, dict):
        raise ValidationError("State must be a dictionary.")

    if not isinstance(state.get("authenticated"), bool):
        raise ValidationError("authenticated must be boolean.")

    if not isinstance(state.get("theme"), str):
        raise ValidationError("theme must be a string.")

    if state["theme"] not in {"light", "dark", "system"}:
        raise ValidationError("Unsupported theme.")

    if not isinstance(state.get("language"), str):
        raise ValidationError("language must be a string.")

    if not isinstance(state.get("profile"), dict):
        raise ValidationError("profile must be a dictionary.")

    if state["authenticated"] and not state["profile"].get("user_id"):
        raise ValidationError(
            "An authenticated state requires a user ID."
        )


def initial_state() -> dict[str, Any]:
    return {
        "authenticated": False,
        "profile": {},
        "theme": "light",
        "language": "en",
    }


def reducer(
    state: dict[str, Any],
    action: Action
) -> dict[str, Any]:

    new_state = copy.deepcopy(state)

    if action.type == ActionType.LOGIN:
        user_id = action.payload.get("user_id")
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValidationError("A valid user ID is required.")

        new_state["authenticated"] = True
        new_state["profile"] = {
            "user_id": user_id.strip(),
            "name": str(action.payload.get("name", "User")),
            "email": str(action.payload.get("email", "")),
        }

    elif action.type == ActionType.LOGOUT:
        new_state["authenticated"] = False
        new_state["profile"] = {}

    elif action.type == ActionType.UPDATE_PROFILE:
        if not state["authenticated"]:
            raise ValidationError(
                "Cannot update an unauthenticated profile."
            )

        allowed = {"name", "email"}
        updates = action.payload

        if not updates or not set(updates).issubset(allowed):
            raise ValidationError("Invalid profile fields.")

        new_state["profile"].update(updates)

    elif action.type == ActionType.SET_THEME:
        theme = action.payload.get("theme")
        if theme not in {"light", "dark", "system"}:
            raise ValidationError("Invalid theme.")
        new_state["theme"] = theme

    elif action.type == ActionType.SET_LANGUAGE:
        language = action.payload.get("language")
        if language not in {"en", "hi", "fr", "de"}:
            raise ValidationError("Unsupported language.")
        new_state["language"] = language

    elif action.type == ActionType.RESET:
        new_state = initial_state()

    else:
        raise ValidationError("Unsupported action.")

    validate_state(new_state)
    return new_state


@dataclass
class Consumer(Generic[T]):
    name: str
    selector: Selector[T]
    callback: Listener
    last_value: Any = None
    active: bool = True
    notification_count: int = 0


class ContextProvider:
    """
    Provider represents an independently scoped state container.

    Consumers subscribe to selected portions of the state.
    A consumer is notified only when its selected value changes.
    """

    def __init__(
        self,
        name: str,
        state: dict[str, Any] | None = None
    ):
        self.name = name
        self._state = copy.deepcopy(state or initial_state())
        validate_state(self._state)

        self._consumers: dict[str, Consumer] = {}
        self._batch_depth = 0
        self._pending_notification = False
        self._version = 0

    @property
    def version(self) -> int:
        return self._version

    def get_state(self) -> dict[str, Any]:
        return copy.deepcopy(self._state)

    def subscribe(
        self,
        name: str,
        selector: Selector,
        callback: Listener
    ) -> Callable[[], None]:

        if name in self._consumers:
            raise ContextError(
                f"Consumer '{name}' already exists."
            )

        consumer = Consumer(
            name=name,
            selector=selector,
            callback=callback,
        )

        consumer.last_value = copy.deepcopy(
            selector(self._state)
        )

        self._consumers[name] = consumer

        logging.info(
            "%s subscribed to provider %s",
            name,
            self.name
        )

        def unsubscribe() -> None:
            consumer.active = False
            self._consumers.pop(name, None)

        return unsubscribe

    def dispatch(self, action: Action) -> None:
        new_state = reducer(self._state, action)

        if new_state == self._state:
            return

        self._state = new_state
        self._version += 1

        if self._batch_depth:
            self._pending_notification = True
        else:
            self._notify()

    def _notify(self) -> None:
        for consumer in list(self._consumers.values()):
            if not consumer.active:
                continue

            try:
                current = consumer.selector(self._state)

                if current != consumer.last_value:
                    previous = consumer.last_value
                    consumer.last_value = copy.deepcopy(current)
                    consumer.notification_count += 1

                    consumer.callback(
                        copy.deepcopy(current),
                        copy.deepcopy(previous)
                    )

            except Exception:
                logging.exception(
                    "Consumer notification failed: %s",
                    consumer.name
                )

    @contextmanager
    def batch(self):
        """Combine several updates into one notification cycle."""
        self._batch_depth += 1

        try:
            yield self
        finally:
            self._batch_depth -= 1

            if (
                self._batch_depth == 0
                and self._pending_notification
            ):
                self._pending_notification = False
                self._notify()

    def consumer_count(self) -> int:
        return len(self._consumers)


class ContextRegistry:
    """
    Resolves providers through nested application scopes.
    A child scope can override a parent provider.
    """

    def __init__(
        self,
        parent: ContextRegistry | None = None
    ):
        self.parent = parent
        self.providers: dict[str, ContextProvider] = {}

    def provide(self, name: str, provider: ContextProvider):
        if name in self.providers:
            raise DuplicateProviderError(name)

        self.providers[name] = provider

    def consume(self, name: str) -> ContextProvider:
        if name in self.providers:
            return self.providers[name]

        if self.parent:
            return self.parent.consume(name)

        raise ProviderNotFoundError(
            f"No provider found for '{name}'."
        )


def save_state(
    provider: ContextProvider,
    filename: str
) -> None:
    """
    Persist non-sensitive preferences.

    Authentication credentials and tokens are deliberately
    excluded from persistence.
    """
    state = provider.get_state()

    safe_state = {
        "theme": state["theme"],
        "language": state["language"],
    }

    path = Path(filename)
    path.write_text(
        json.dumps(safe_state, indent=2),
        encoding="utf-8"
    )


def load_preferences(filename: str) -> dict[str, Any]:
    path = Path(filename)

    if not path.exists():
        return initial_state()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))

        state = initial_state()
        state["theme"] = data.get("theme", "light")
        state["language"] = data.get("language", "en")

        validate_state(state)
        return state

    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        logging.warning("Preferences could not be loaded: %s", exc)
        return initial_state()


def demonstrate_context_api() -> None:
    print("\n=== 1. Provider Creation ===")

    preferences = load_preferences("context_preferences.json")
    app_provider = ContextProvider(
        "ApplicationContext",
        preferences
    )

    registry = ContextRegistry()
    registry.provide("application", app_provider)

    print("Initial state:", app_provider.get_state())

    print("\n=== 2. Consumer Subscriptions ===")

    def theme_consumer(new, old):
        print(f"Theme changed: {old} -> {new}")

    def auth_consumer(new, old):
        print(f"Authentication changed: {old} -> {new}")

    unsubscribe_theme = app_provider.subscribe(
        "ThemeConsumer",
        lambda state: state["theme"],
        theme_consumer
    )

    unsubscribe_auth = app_provider.subscribe(
        "AuthConsumer",
        lambda state: state["authenticated"],
        auth_consumer
    )

    print("\n=== 3. State Updates ===")

    app_provider.dispatch(
        Action(
            ActionType.SET_THEME,
            {"theme": "dark"}
        )
    )

    app_provider.dispatch(
        Action(
            ActionType.LOGIN,
            {
                "user_id": "USR-1001",
                "name": "Aarav Sharma",
                "email": "aarav@example.com",
            }
        )
    )

    app_provider.dispatch(
        Action(
            ActionType.UPDATE_PROFILE,
            {"name": "Aarav Kumar"}
        )
    )

    print("\nCurrent state:", app_provider.get_state())

    print("\n=== 4. Batched Updates ===")

    with app_provider.batch():
        app_provider.dispatch(
            Action(
                ActionType.SET_THEME,
                {"theme": "light"}
            )
        )

        app_provider.dispatch(
            Action(
                ActionType.SET_LANGUAGE,
                {"language": "hi"}
            )
        )

    print("Version:", app_provider.version)

    print("\n=== 5. Nested Provider Scope ===")

    child_provider = ContextProvider(
        "ChildThemeContext",
        {
            **app_provider.get_state(),
            "theme": "system",
        }
    )

    child_registry = ContextRegistry(registry)
    child_registry.provide("application", child_provider)

    resolved = child_registry.consume("application")

    print("Parent theme:", app_provider.get_state()["theme"])
    print("Child theme:", resolved.get_state()["theme"])

    print("\n=== 6. Error Handling ===")

    try:
        registry.consume("missing")
    except ProviderNotFoundError as exc:
        print("Expected error:", exc)

    try:
        app_provider.dispatch(
            Action(
                ActionType.SET_THEME,
                {"theme": "invalid"}
            )
        )
    except ValidationError as exc:
        print("Validation error:", exc)

    print("\n=== 7. Consumer Cleanup ===")

    unsubscribe_theme()
    unsubscribe_auth()

    print(
        "Remaining consumers:",
        app_provider.consumer_count()
    )

    print("\n=== 8. Persistence ===")

    save_state(app_provider, "context_preferences.json")
    print("Non-sensitive preferences saved.")

    print("\n=== 9. Assertions ===")

    assert app_provider.get_state()["authenticated"]
    assert app_provider.get_state()["profile"]["user_id"] == "USR-1001"
    assert app_provider.get_state()["language"] == "hi"
    assert app_provider.consumer_count() == 0

    print("All assertions passed.")


if __name__ == "__main__":
    demonstrate_context_api()
