"""
Prototype chains, inheritance, constructor functions, and Object.create.

Python models the underlying ideas using classes, inheritance, and explicit
prototype-like lookup. Python does not implement JavaScript's prototype chain.
"""

from dataclasses import dataclass
from typing import Any, Optional


class PrototypeObject:
    """A small JavaScript-inspired object with explicit prototype lookup."""

    def __init__(
        self,
        properties: Optional[dict[str, Any]] = None,
        prototype: Optional["PrototypeObject"] = None,
    ) -> None:
        self.properties = dict(properties or {})
        self.prototype = prototype

    def get(self, name: str) -> Any:
        """Look locally first, then search each prototype in order."""
        current: Optional[PrototypeObject] = self
        visited: set[int] = set()

        while current is not None:
            if id(current) in visited:
                raise RuntimeError("Prototype cycle detected")
            visited.add(id(current))

            if name in current.properties:
                return current.properties[name]

            current = current.prototype

        raise AttributeError(f"Property {name!r} was not found")

    def has_own(self, name: str) -> bool:
        return name in self.properties

    def has_property(self, name: str) -> bool:
        try:
            self.get(name)
            return True
        except AttributeError:
            return False

    def set(self, name: str, value: Any) -> None:
        """Assign locally without modifying inherited properties."""
        self.properties[name] = value

    def describe_chain(self) -> list[dict[str, Any]]:
        """Return each object's own properties along the prototype chain."""
        chain = []
        current: Optional[PrototypeObject] = self
        visited: set[int] = set()

        while current is not None:
            if id(current) in visited:
                raise RuntimeError("Prototype cycle detected")
            visited.add(id(current))
            chain.append(current.properties.copy())
            current = current.prototype

        return chain


def demonstrate_lookup_and_shadowing() -> None:
    print("\nPrototype lookup and property shadowing")

    vehicle = PrototypeObject({
        "category": "vehicle",
        "wheels": 4,
    })

    car = PrototypeObject({
        "brand": "Toyota",
    }, prototype=vehicle)

    print("Inherited category:", car.get("category"))
    print("Inherited wheels:", car.get("wheels"))
    print("Own brand:", car.get("brand"))
    print("Own category before assignment:", car.has_own("category"))

    car.set("category", "car")

    print("Shadowed category:", car.get("category"))
    print("Prototype category remains:", vehicle.get("category"))
    print("Own category after assignment:", car.has_own("category"))
    print("Complete chain:", car.describe_chain())


def demonstrate_constructor_functions() -> None:
    print("\nConstructor-function concepts")

    # A Python function can initialize an existing instance. This illustrates
    # initialization, not JavaScript's new operator or prototype assignment.
    class Employee:
        def __init__(self, employee_id: str, role: str) -> None:
            self.employee_id = employee_id
            self.role = role

        def describe(self) -> str:
            return f"{self.employee_id}: {self.role}"

    engineer = Employee("EMP-104", "Software Engineer")
    analyst = Employee("EMP-205", "Security Analyst")

    print(engineer.describe())
    print(analyst.describe())
    print("Shared Python class:", type(engineer) is type(analyst))


def demonstrate_class_inheritance() -> None:
    print("\nPython class inheritance")

    @dataclass
    class Device:
        asset_tag: str
        manufacturer: str

        def inventory_label(self) -> str:
            return f"{self.asset_tag} | {self.manufacturer}"

    @dataclass
    class Server(Device):
        cpu_cores: int = 8
        environment: str = "production"

        def inventory_label(self) -> str:
            parent_label = super().inventory_label()
            return (
                f"{parent_label} | {self.cpu_cores} cores"
                f" | {self.environment}"
            )

    server = Server("SRV-001", "Example Systems", 32, "staging")

    print(server.inventory_label())
    print("Is a Device:", isinstance(server, Device))
    print("Method resolution order:", Server.__mro__)


def demonstrate_shared_behavior() -> None:
    print("\nShared methods and per-instance state")

    class Account:
        def __init__(self, owner: str, balance: float = 0.0) -> None:
            if balance < 0:
                raise ValueError("Initial balance cannot be negative")
            self.owner = owner
            self.balance = balance

        def deposit(self, amount: float) -> float:
            if amount <= 0:
                raise ValueError("Deposit must be positive")
            self.balance += amount
            return self.balance

    first = Account("Asha", 500.0)
    second = Account("Ravi", 200.0)

    first.deposit(75.0)

    print("First account:", first.balance)
    print("Second account:", second.balance)
    print(
        "Deposit method shared by class:",
        first.deposit.__func__ is second.deposit.__func__,
    )


def demonstrate_edge_cases() -> None:
    print("\nValidation and edge cases")

    root = PrototypeObject({"status": "active"})
    child = PrototypeObject({"name": "node"}, root)

    print("Inherited property exists:", child.has_property("status"))
    print("Inherited property is own:", child.has_own("status"))

    try:
        child.get("missing")
    except AttributeError as error:
        print("Missing property:", error)

    # Normal construction prevents cycles in this simple API, but direct
    # mutation can introduce one. Lookup detects it instead of looping forever.
    root.prototype = child

    try:
        child.get("absent")
    except RuntimeError as error:
        print("Cycle protection:", error)

    root.prototype = None


def main() -> None:
    demonstrate_lookup_and_shadowing()
    demonstrate_constructor_functions()
    demonstrate_class_inheritance()
    demonstrate_shared_behavior()
    demonstrate_edge_cases()


if __name__ == "__main__":
    main()
