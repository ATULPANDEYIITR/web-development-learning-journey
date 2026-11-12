from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
from copy import deepcopy
import json


# ============================================================
# REACT STATE: STATE MANAGEMENT CONCEPT SIMULATOR
# ============================================================

@dataclass
class StateSnapshot:
    version: int
    values: dict[str, Any]


class StateError(Exception):
    """Raised when an invalid state operation is attempted."""


class StateManager:
    """
    Simulates React's fundamental state-management concepts:
    - Initial state
    - State updates
    - Functional updates
    - Immutable updates
    - Derived state
    - Controlled components
    - State snapshots
    - Update validation
    """

    def __init__(self, initial_state: dict[str, Any]):
        if not isinstance(initial_state, dict):
            raise TypeError("Initial state must be a dictionary.")

        self._state = deepcopy(initial_state)
        self._version = 0
        self._history: list[StateSnapshot] = []
        self._listeners: list[Callable[[dict[str, Any]], None]] = []

    @property
    def state(self) -> dict[str, Any]:
        return deepcopy(self._state)

    @property
    def version(self) -> int:
        return self._version

    def subscribe(
        self,
        callback: Callable[[dict[str, Any]], None]
    ) -> None:
        if not callable(callback):
            raise TypeError("Listener must be callable.")
        self._listeners.append(callback)

    def unsubscribe(
        self,
        callback: Callable[[dict[str, Any]], None]
    ) -> None:
        self._listeners = [
            listener
            for listener in self._listeners
            if listener is not callback
        ]

    def _notify(self) -> None:
        snapshot = self.state

        for listener in tuple(self._listeners):
            listener(deepcopy(snapshot))

    def set_state(
        self,
        updates: dict[str, Any] | Callable[[dict[str, Any]], dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Object updates replace specified fields.
        Functional updates calculate new values from current state.

        This simulator applies updates synchronously. React schedules
        and batches updates according to its rendering lifecycle.
        """
        previous = self.state

        if callable(updates):
            result = updates(deepcopy(previous))
        else:
            result = updates

        if not isinstance(result, dict):
            raise StateError("State update must return a dictionary.")

        if not result.keys() <= self._state.keys():
            raise StateError("State update contains unknown properties.")

        next_state = deepcopy(self._state)
        next_state.update(deepcopy(result))

        if next_state != self._state:
            self._history.append(
                StateSnapshot(self._version, previous)
            )
            self._state = next_state
            self._version += 1
            self._notify()

        return self.state

    def update_nested(
        self,
        property_name: str,
        nested_updates: dict[str, Any]
    ) -> dict[str, Any]:
        """Perform an immutable nested-object update."""
        current = self._state.get(property_name)

        if not isinstance(current, dict):
            raise StateError(
                f"{property_name} must contain a dictionary."
            )

        updated = {
            **current,
            **deepcopy(nested_updates)
        }

        return self.set_state({property_name: updated})

    def derived_state(self) -> dict[str, Any]:
        """Calculate values without storing redundant state."""
        cart = self._state.get("cart", [])

        subtotal = sum(
            item["price"] * item["quantity"]
            for item in cart
        )

        return {
            "cart_items": sum(
                item["quantity"] for item in cart
            ),
            "subtotal": round(subtotal, 2),
            "has_items": len(cart) > 0,
            "is_authenticated": bool(
                self._state.get("user")
            ),
        }

    def controlled_input(
        self,
        field_name: str,
        value: Any,
        validator: Callable[[Any], bool] | None = None
    ) -> dict[str, Any]:
        """Validate and update a controlled input value."""
        if field_name not in self._state:
            raise StateError("Unknown controlled field.")

        if validator and not validator(value):
            raise StateError("Controlled input validation failed.")

        return self.set_state({field_name: value})

    def add_to_cart(
        self,
        product_id: str,
        name: str,
        price: float,
        quantity: int = 1
    ) -> dict[str, Any]:
        if not product_id or not name:
            raise ValueError("Product ID and name are required.")

        if price < 0 or quantity <= 0:
            raise ValueError("Invalid price or quantity.")

        def updater(previous: dict[str, Any]) -> dict[str, Any]:
            cart = deepcopy(previous["cart"])

            for item in cart:
                if item["product_id"] == product_id:
                    item["quantity"] += quantity
                    return {"cart": cart}

            cart.append({
                "product_id": product_id,
                "name": name,
                "price": price,
                "quantity": quantity
            })

            return {"cart": cart}

        return self.set_state(updater)

    def remove_from_cart(
        self,
        product_id: str
    ) -> dict[str, Any]:
        return self.set_state(
            lambda previous: {
                "cart": [
                    item
                    for item in previous["cart"]
                    if item["product_id"] != product_id
                ]
            }
        )

    def undo(self) -> dict[str, Any]:
        if not self._history:
            raise StateError("No previous state is available.")

        snapshot = self._history.pop()
        self._state = deepcopy(snapshot.values)
        self._version += 1
        self._notify()

        return self.state

    def export_state(self) -> str:
        return json.dumps(
            {
                "version": self._version,
                "state": self._state,
                "derived": self.derived_state()
            },
            indent=4
        )


# ============================================================
# COUNTER STATE
# ============================================================

def counter_example() -> None:
    counter = StateManager({"count": 0})

    counter.set_state(
        lambda previous: {
            "count": previous["count"] + 1
        }
    )

    counter.set_state(
        lambda previous: {
            "count": previous["count"] + 1
        }
    )

    print("Counter:", counter.state["count"])

    # Functional updates preserve sequential intent.
    counter.set_state(
        lambda previous: {
            "count": previous["count"] + 5
        }
    )

    print("After increment:", counter.state["count"])


# ============================================================
# CONTROLLED FORM
# ============================================================

def form_example() -> None:
    form = StateManager({
        "username": "",
        "email": "",
        "age": 0,
        "accepted_terms": False
    })

    form.controlled_input(
        "username",
        "Atul",
        lambda value: (
            isinstance(value, str)
            and 1 <= len(value.strip()) <= 50
        )
    )

    form.controlled_input(
        "email",
        "atul@example.com",
        lambda value: (
            isinstance(value, str)
            and "@" in value
            and len(value) <= 254
        )
    )

    form.controlled_input(
        "age",
        28,
        lambda value: (
            isinstance(value, int)
            and not isinstance(value, bool)
            and 18 <= value <= 120
        )
    )

    form.controlled_input("accepted_terms", True)

    valid = (
        bool(form.state["username"].strip())
        and "@" in form.state["email"]
        and form.state["age"] >= 18
        and form.state["accepted_terms"]
    )

    print("Form state:", form.state)
    print("Form valid:", valid)


# ============================================================
# SHOPPING CART AND DERIVED STATE
# ============================================================

def shopping_cart_example() -> None:
    store = StateManager({
        "user": {
            "id": 101,
            "name": "Atul"
        },
        "cart": []
    })

    store.subscribe(
        lambda state: print(
            "State changed:",
            state
        )
    )

    store.add_to_cart(
        "P001",
        "Mechanical Keyboard",
        2499.00,
        1
    )

    store.add_to_cart(
        "P002",
        "Wireless Mouse",
        999.00,
        2
    )

    store.add_to_cart(
        "P001",
        "Mechanical Keyboard",
        2499.00,
        1
    )

    print("Derived values:", store.derived_state())

    store.remove_from_cart("P002")

    print("Updated cart:", store.state["cart"])
    print("Final derived values:", store.derived_state())


# ============================================================
# NESTED STATE
# ============================================================

def nested_state_example() -> None:
    profile = StateManager({
        "user": {
            "name": "Atul",
            "address": {
                "city": "Lucknow",
                "country": "India"
            }
        }
    })

    profile.update_nested(
        "user",
        {
            "address": {
                **profile.state["user"]["address"],
                "city": "Patna"
            }
        }
    )

    print("Updated profile:", profile.state)


# ============================================================
# EDGE CASES AND VALIDATION
# ============================================================

def error_handling_example() -> None:
    manager = StateManager({"count": 0})

    tests = [
        lambda: manager.set_state({"unknown": 10}),
        lambda: manager.controlled_input(
            "count",
            -1,
            lambda value: value >= 0
        ),
        lambda: manager.add_to_cart(
            "P003",
            "Invalid Product",
            -100
        )
    ]

    for test in tests:
        try:
            test()
        except (StateError, ValueError, TypeError) as error:
            print("Handled error:", error)


# ============================================================
# MAIN EXECUTION
# ============================================================

def main() -> None:
    print("\n--- Counter State ---")
    counter_example()

    print("\n--- Controlled Form ---")
    form_example()

    print("\n--- Shopping Cart ---")
    shopping_cart_example()

    print("\n--- Nested State ---")
    nested_state_example()

    print("\n--- Error Handling ---")
    error_handling_example()

    print("\nReact State simulation completed.")


if __name__ == "__main__":
    main()
