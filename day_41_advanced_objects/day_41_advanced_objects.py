#!/usr/bin/env python3
"""Advanced JavaScript object concepts modeled with executable Python examples.

The demonstrations focus on property descriptors, getters, setters, frozen and
sealed objects, prototype inheritance, descriptor inspection, and validation.

Python does not implement JavaScript property descriptors directly. The
DescriptorProperty class models their behavior explicitly, while Python's
property, __slots__, and read-only mapping interfaces demonstrate related
language-specific mechanisms.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable


class ObjectStateError(RuntimeError):
    """Raised when an operation violates an object's integrity state."""


@dataclass
class PropertyDescriptor:
    """A compact model of a JavaScript-style property descriptor."""

    enumerable: bool = True
    configurable: bool = True
    writable: bool = True
    value: Any = None
    getter: Callable[[Any], Any] | None = None
    setter: Callable[[Any, Any], None] | None = None

    def is_accessor(self) -> bool:
        return self.getter is not None or self.setter is not None


class DescriptorObject:
    """A small object model with descriptor-controlled properties."""

    def __init__(self) -> None:
        self._descriptors: dict[str, PropertyDescriptor] = {}
        self._extensible = True
        self._sealed = False
        self._frozen = False

    def define_property(
        self,
        name: str,
        descriptor: PropertyDescriptor,
    ) -> None:
        if not name:
            raise ValueError("Property names must not be empty.")

        existing = self._descriptors.get(name)

        if existing is None and not self._extensible:
            raise ObjectStateError("Cannot add a property to a non-extensible object.")

        if existing is not None and not existing.configurable:
            if descriptor.configurable:
                raise ObjectStateError("Cannot make a non-configurable property configurable.")

            if descriptor.enumerable != existing.enumerable:
                raise ObjectStateError("Cannot change enumerability of a non-configurable property.")

            if existing.is_accessor() != descriptor.is_accessor():
                raise ObjectStateError("Cannot change descriptor kind of a non-configurable property.")

            if not existing.is_accessor() and not existing.writable:
                if descriptor.writable:
                    raise ObjectStateError("Cannot make a non-writable property writable.")
                if descriptor.value != existing.value:
                    raise ObjectStateError("Cannot change a non-writable property's value.")

        self._descriptors[name] = descriptor

        if self._frozen:
            descriptor.configurable = False
            if not descriptor.is_accessor():
                descriptor.writable = False

        elif self._sealed:
            descriptor.configurable = False

    def get(self, name: str) -> Any:
        descriptor = self._descriptors.get(name)

        if descriptor is None:
            raise AttributeError(f"Property {name!r} does not exist.")

        if descriptor.getter is not None:
            return descriptor.getter(self)

        return descriptor.value

    def set(self, name: str, value: Any) -> None:
        descriptor = self._descriptors.get(name)

        if descriptor is None:
            if not self._extensible:
                raise ObjectStateError("Cannot add a property to a non-extensible object.")

            self.define_property(name, PropertyDescriptor(value=value))
            return

        if descriptor.setter is not None:
            descriptor.setter(self, value)
            return

        if descriptor.getter is not None:
            raise ObjectStateError("Cannot assign to a getter-only property.")

        if not descriptor.writable:
            raise ObjectStateError(f"Property {name!r} is not writable.")

        descriptor.value = value

    def delete(self, name: str) -> bool:
        descriptor = self._descriptors.get(name)

        if descriptor is None:
            return True

        if not descriptor.configurable:
            raise ObjectStateError(f"Property {name!r} is not configurable.")

        del self._descriptors[name]
        return True

    def own_property_names(self) -> list[str]:
        return list(self._descriptors)

    def enumerable_properties(self) -> dict[str, Any]:
        return {
            name: self.get(name)
            for name, descriptor in self._descriptors.items()
            if descriptor.enumerable
        }

    def descriptor(self, name: str) -> PropertyDescriptor | None:
        return self._descriptors.get(name)

    def prevent_extensions(self) -> None:
        self._extensible = False

    def seal(self) -> None:
        self._extensible = False
        self._sealed = True

        for descriptor in self._descriptors.values():
            descriptor.configurable = False

    def freeze(self) -> None:
        self._extensible = False
        self._sealed = True
        self._frozen = True

        for descriptor in self._descriptors.values():
            descriptor.configurable = False

            if not descriptor.is_accessor():
                descriptor.writable = False

    @property
    def is_extensible(self) -> bool:
        return self._extensible

    @property
    def is_sealed(self) -> bool:
        return self._sealed and all(
            not descriptor.configurable
            for descriptor in self._descriptors.values()
        )

    @property
    def is_frozen(self) -> bool:
        return self.is_sealed and all(
            descriptor.is_accessor() or not descriptor.writable
            for descriptor in self._descriptors.values()
        )


class Account:
    """Demonstrates computed properties, getters, and validated setters."""

    def __init__(self, owner: str, balance: float) -> None:
        if not owner.strip():
            raise ValueError("Account owner must not be empty.")

        self.owner = owner
        self._balance = 0.0
        self.balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("Balance must be numeric.")

        if value < 0:
            raise ValueError("Balance cannot be negative.")

        self._balance = float(value)

    @property
    def account_summary(self) -> str:
        return f"{self.owner}: balance={self.balance:.2f}"

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit must be positive.")

        self.balance = self.balance + amount

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Withdrawal must be positive.")

        if amount > self.balance:
            raise ValueError("Insufficient funds.")

        self.balance = self.balance - amount


class FrozenConfiguration:
    """Demonstrates immutable attribute binding with __slots__."""

    __slots__ = ("_values", "_locked")

    def __init__(self, values: Mapping[str, Any]) -> None:
        object.__setattr__(self, "_values", MappingProxyType(dict(values)))
        object.__setattr__(self, "_locked", True)

    def __getattr__(self, name: str) -> Any:
        try:
            return self._values[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: Any) -> None:
        if self._locked:
            raise ObjectStateError("Configuration attributes are read-only.")

        object.__setattr__(self, name, value)


class Prototype:
    """Represents a prototype with lookup through a parent chain."""

    def __init__(
        self,
        properties: Mapping[str, Any] | None = None,
        parent: Prototype | None = None,
    ) -> None:
        self.properties = dict(properties or {})
        self.parent = parent

    def lookup(self, name: str) -> Any:
        current: Prototype | None = self

        while current is not None:
            if name in current.properties:
                return current.properties[name]
            current = current.parent

        raise AttributeError(f"Prototype property {name!r} not found.")

    def has_own(self, name: str) -> bool:
        return name in self.properties

    def set_own(self, name: str, value: Any) -> None:
        self.properties[name] = value


def expect_error(label: str, operation: Callable[[], Any]) -> None:
    try:
        operation()
    except (ValueError, TypeError, AttributeError, ObjectStateError) as exc:
        print(f"{label}: {type(exc).__name__}: {exc}")
    else:
        raise AssertionError(f"{label}: expected an exception.")


def demonstrate_data_descriptors() -> None:
    print("\nProperty descriptors")

    product = DescriptorObject()
    product.define_property(
        "sku",
        PropertyDescriptor(
            value="NET-204",
            enumerable=True,
            configurable=False,
            writable=False,
        ),
    )
    product.define_property(
        "internal_cost",
        PropertyDescriptor(
            value=1250.0,
            enumerable=False,
            configurable=True,
            writable=True,
        ),
    )

    print("SKU:", product.get("sku"))
    print("All own properties:", product.own_property_names())
    print("Enumerable properties:", product.enumerable_properties())
    expect_error("Change immutable SKU", lambda: product.set("sku", "NET-205"))
    expect_error("Delete non-configurable SKU", lambda: product.delete("sku"))


def demonstrate_accessors() -> None:
    print("\nGetters and setters")

    account = Account("Operations", 5000)
    account.deposit(750)
    account.withdraw(400)

    print(account.account_summary)
    expect_error("Negative balance", lambda: setattr(account, "balance", -1))
    expect_error("Invalid deposit", lambda: account.deposit(0))
    expect_error("Excessive withdrawal", lambda: account.withdraw(100000))


def demonstrate_integrity_levels() -> None:
    print("\nPrevent extensions, seal, and freeze")

    non_extensible = DescriptorObject()
    non_extensible.define_property("region", PropertyDescriptor(value="APAC"))
    non_extensible.prevent_extensions()
    expect_error(
        "Add property after preventExtensions",
        lambda: non_extensible.set("country", "India"),
    )

    sealed = DescriptorObject()
    sealed.define_property("status", PropertyDescriptor(value="active"))
    sealed.seal()
    sealed.set("status", "maintenance")
    print("Sealed object can update writable values:", sealed.get("status"))
    expect_error("Add property to sealed object", lambda: sealed.set("owner", "team-a"))
    expect_error("Delete sealed property", lambda: sealed.delete("status"))

    frozen = DescriptorObject()
    frozen.define_property("release", PropertyDescriptor(value="2.4.0"))
    frozen.freeze()
    print("Frozen:", frozen.is_frozen)
    expect_error("Update frozen property", lambda: frozen.set("release", "2.5.0"))

    # Freezing a containing object does not recursively freeze referenced values.
    nested = {"enabled": True}
    shallow = DescriptorObject()
    shallow.define_property("settings", PropertyDescriptor(value=nested))
    shallow.freeze()
    shallow.get("settings")["enabled"] = False
    print("Nested mutable value after shallow freeze:", shallow.get("settings"))


def demonstrate_prototypes() -> None:
    print("\nPrototype lookup")

    entity = Prototype({"kind": "service", "enabled": True})
    database_service = Prototype({"name": "inventory-db"}, parent=entity)

    print("Inherited kind:", database_service.lookup("kind"))
    print("Own name:", database_service.has_own("name"))
    print("Inherited kind is own:", database_service.has_own("kind"))

    database_service.set_own("enabled", False)
    print("Shadowed enabled value:", database_service.lookup("enabled"))
    print("Parent enabled value:", entity.lookup("enabled"))
    expect_error("Missing prototype property", lambda: database_service.lookup("region"))


def demonstrate_read_only_configuration() -> None:
    print("\nRead-only configuration")

    configuration = FrozenConfiguration(
        {"environment": "production", "retry_limit": 3}
    )
    print(configuration.environment, configuration.retry_limit)

    expect_error(
        "Assign configuration attribute",
        lambda: setattr(configuration, "retry_limit", 5),
    )

    try:
        configuration._values["retry_limit"] = 5
    except TypeError as exc:
        print("Mutate read-only mapping:", type(exc).__name__, exc)


def main() -> None:
    demonstrate_data_descriptors()
    demonstrate_accessors()
    demonstrate_integrity_levels()
    demonstrate_prototypes()
    demonstrate_read_only_configuration()
    print("\nAll advanced object demonstrations completed.")


if __name__ == "__main__":
    main()
