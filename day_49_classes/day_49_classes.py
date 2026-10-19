from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Iterable


class ValidationError(ValueError):
    """Raised when an object violates its class invariants."""


class Account(ABC):
    """
    Base class demonstrating:
    - a constructor
    - private instance state using name mangling
    - a class-level/static member
    - inheritance
    - an abstract method
    """

    _next_id: ClassVar[int] = 1000
    _active_accounts: ClassVar[int] = 0
    account_type: ClassVar[str] = "generic"

    def __init__(self, owner: str, balance: float = 0.0) -> None:
        owner = owner.strip()
        if not owner:
            raise ValidationError("Owner name cannot be empty.")
        if balance < 0:
            raise ValidationError("Initial balance cannot be negative.")

        self.__account_id = Account._next_id
        Account._next_id += 1

        self.__owner = owner
        self.__balance = float(balance)
        self.__closed = False

        Account._active_accounts += 1

    @property
    def account_id(self) -> int:
        return self.__account_id

    @property
    def owner(self) -> str:
        return self.__owner

    @property
    def balance(self) -> float:
        return self.__balance

    @property
    def closed(self) -> bool:
        return self.__closed

    def _change_balance(self, amount: float) -> None:
        """Protected helper used by subclasses while preserving invariants."""
        new_balance = self.__balance + amount
        if new_balance < 0:
            raise ValidationError("Transaction would create a negative balance.")
        self.__balance = round(new_balance, 2)

    def deposit(self, amount: float) -> None:
        if self.__closed:
            raise ValidationError("Cannot deposit into a closed account.")
        if amount <= 0:
            raise ValidationError("Deposit must be positive.")
        self._change_balance(amount)

    def close(self) -> None:
        if self.__closed:
            raise ValidationError("Account is already closed.")
        if self.__balance != 0:
            raise ValidationError("Account must have zero balance before closing.")

        self.__closed = True
        Account._active_accounts -= 1

    @classmethod
    def active_accounts(cls) -> int:
        """Class method accesses class-wide state rather than one object."""
        return Account._active_accounts

    @staticmethod
    def normalize_currency(amount: float) -> float:
        """Static method does not depend on object or class state."""
        return round(float(amount), 2)

    @abstractmethod
    def monthly_charge(self) -> float:
        """Each subclass supplies its own account-specific rule."""
        raise NotImplementedError


class SavingsAccount(Account):
    account_type: ClassVar[str] = "savings"
    INTEREST_RATE: ClassVar[float] = 0.04
    MINIMUM_BALANCE: ClassVar[float] = 500.0

    def __init__(self, owner: str, balance: float = 0.0) -> None:
        super().__init__(owner, balance)
        if balance < self.MINIMUM_BALANCE:
            # Constructor validation demonstrates that subclasses can strengthen
            # the invariant established by the parent constructor.
            Account._active_accounts -= 1
            raise ValidationError(
                f"Savings account requires at least {self.MINIMUM_BALANCE:.2f}."
            )

    def monthly_charge(self) -> float:
        return 0.0

    def apply_interest(self) -> None:
        if self.closed:
            raise ValidationError("Cannot apply interest to a closed account.")
        self._change_balance(self.balance * self.INTEREST_RATE / 12)


class BusinessAccount(Account):
    account_type: ClassVar[str] = "business"
    TRANSACTION_FEE: ClassVar[float] = 2.50

    def __init__(self, owner: str, balance: float = 0.0) -> None:
        super().__init__(owner, balance)

    def monthly_charge(self) -> float:
        return 25.0

    def transfer_to(self, target: Account, amount: float) -> None:
        if self.closed or target.closed:
            raise ValidationError("Both accounts must be active.")
        if amount <= 0:
            raise ValidationError("Transfer amount must be positive.")

        total = amount + self.TRANSACTION_FEE
        self._change_balance(-total)
        target.deposit(amount)


class AuditedAccount(BusinessAccount):
    """
    A second inheritance level demonstrates that subclass behavior can extend
    inherited behavior without exposing the parent's private fields.
    """

    AUDIT_FEE: ClassVar[float] = 0.50

    def __init__(self, owner: str, balance: float = 0.0) -> None:
        super().__init__(owner, balance)
        self.__audit_events: list[str] = []

    def transfer_to(self, target: Account, amount: float) -> None:
        super().transfer_to(target, amount)
        self.__audit_events.append(
            f"Transferred {amount:.2f} to account {target.account_id}"
        )

    def audit_events(self) -> tuple[str, ...]:
        return tuple(self.__audit_events)


@dataclass(frozen=True)
class Customer:
    """A separate class shows composition: a customer owns account objects."""

    customer_id: int
    name: str
    accounts: tuple[Account, ...]

    @property
    def total_balance(self) -> float:
        return round(sum(account.balance for account in self.accounts), 2)


def demonstrate_constructors_and_private_fields() -> None:
    print("=== Constructors and private instance state ===")

    savings = SavingsAccount("Asha Sharma", 5000)
    print(
        f"{savings.owner}: account={savings.account_id}, "
        f"type={savings.account_type}, balance={savings.balance:.2f}"
    )

    # __balance is intentionally private. Access should happen through the
    # public property rather than direct mutation.
    try:
        savings.__balance = 999999
        print("Name-mangled private state was not replaced:", savings.balance)
    except AttributeError as exc:
        print("Private-state access rejected:", exc)

    print("Normalized amount:", Account.normalize_currency(123.456))


def demonstrate_inheritance_and_polymorphism() -> None:
    print("\n=== Inheritance and polymorphism ===")

    savings = SavingsAccount("Ravi Kumar", 3000)
    business = BusinessAccount("Northwind Traders", 10000)
    audited = AuditedAccount("Acme Analytics", 15000)

    accounts: list[Account] = [savings, business, audited]

    for account in accounts:
        # The same method call dispatches to the appropriate subclass.
        print(
            f"{account.account_type:8} "
            f"monthly charge={account.monthly_charge():.2f}"
        )

    audited.transfer_to(savings, 1000)
    print(f"Audited account balance: {audited.balance:.2f}")
    print(f"Savings account balance: {savings.balance:.2f}")
    print("Audit trail:", audited.audit_events())


def demonstrate_static_and_class_members() -> None:
    print("\n=== Static and class members ===")

    before = Account.active_accounts()
    print("Active accounts:", before)

    print("Savings interest rate:", SavingsAccount.INTEREST_RATE)
    print("Business transfer fee:", BusinessAccount.TRANSACTION_FEE)

    amount = Account.normalize_currency(9876.54321)
    print("Static normalization:", amount)

    account = SavingsAccount("Meera Singh", 2500)
    print("Active accounts after construction:", Account.active_accounts())

    account.apply_interest()
    print("Balance after monthly interest:", account.balance)

    # The same class variable is visible through instances, but changing an
    # instance attribute would create a separate instance attribute instead.
    print("Class-level account type:", account.account_type)

    account._change_balance(-account.balance)
    account.close()
    print("Active accounts after closing:", Account.active_accounts())


def demonstrate_composition() -> None:
    print("\n=== Composition ===")

    personal = SavingsAccount("Neha Verma", 7000)
    business = BusinessAccount("Verma Design Studio", 5000)

    customer = Customer(
        customer_id=501,
        name="Neha Verma",
        accounts=(personal, business),
    )

    print(customer.name)
    print("Customer accounts:", len(customer.accounts))
    print("Combined balance:", customer.total_balance)


def demonstrate_validation_and_failure_conditions() -> None:
    print("\n=== Validation and failure conditions ===")

    invalid_constructors = [
        ("empty owner", lambda: BusinessAccount("", 1000)),
        ("negative balance", lambda: BusinessAccount("Valid Owner", -1)),
        (
            "insufficient savings balance",
            lambda: SavingsAccount("Valid Owner", 100),
        ),
    ]

    for description, factory in invalid_constructors:
        try:
            factory()
        except ValidationError as exc:
            print(f"{description}: {exc}")

    account = BusinessAccount("Secure Operations", 1000)

    try:
        account.deposit(-50)
    except ValidationError as exc:
        print("Invalid deposit:", exc)

    try:
        account.transfer_to(account, 2000)
    except ValidationError as exc:
        print("Insufficient funds:", exc)

    account._change_balance(-1000)
    account.close()
    print("Closed account:", account.closed)

    try:
        account.deposit(10)
    except ValidationError as exc:
        print("Operation on closed account:", exc)


def main() -> None:
    demonstrate_constructors_and_private_fields()
    demonstrate_inheritance_and_polymorphism()
    demonstrate_static_and_class_members()
    demonstrate_composition()
    demonstrate_validation_and_failure_conditions()

    print("\n=== Final class-level state ===")
    print("Active accounts:", Account.active_accounts())


if __name__ == "__main__":
    main()
