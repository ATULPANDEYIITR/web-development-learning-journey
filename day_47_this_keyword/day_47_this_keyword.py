"""
JavaScript this Keyword: Behavior, Methods, Constructors, call, apply, bind,
and Arrow Functions

Run with:
    python this_keyword_lab.py

This Python script models JavaScript's `this` behavior explicitly so that
the distinctions between Python's `self` and JavaScript's dynamic `this`
remain clear.
"""

from dataclasses import dataclass
from functools import partial
from typing import Any, Callable


@dataclass
class JavaScriptObject:
    """A small object model used to simulate JavaScript method receivers."""
    name: str
    department: str

    def describe(self) -> str:
        return f"{self.name} works in {self.department}."


def heading(title: str) -> None:
    print(f"\n{'=' * 12} {title} {'=' * 12}")


def js_method(receiver: JavaScriptObject, method: Callable[..., Any],
              *args: Any) -> Any:
    """Explicitly supply the receiver, analogous to method invocation."""
    return method(receiver, *args)


def js_call(receiver: JavaScriptObject, function: Callable[..., Any],
            *args: Any) -> Any:
    """Model Function.prototype.call by supplying arguments individually."""
    return function(receiver, *args)


def js_apply(receiver: JavaScriptObject, function: Callable[..., Any],
             arguments: list[Any]) -> Any:
    """Model Function.prototype.apply by supplying an argument list."""
    return function(receiver, *arguments)


def js_bind(receiver: JavaScriptObject, function: Callable[..., Any],
            *preset_args: Any) -> Callable[..., Any]:
    """Create a callable with a permanently supplied receiver and arguments."""
    return partial(function, receiver, *preset_args)


def employee_summary(this: JavaScriptObject, task: str = "review") -> str:
    """A receiver-dependent function used by call, apply, and bind examples."""
    return f"{this.name} in {this.department} will {task}."


def demonstrate_python_receiver_model() -> None:
    heading("Python self versus JavaScript this")

    employee = JavaScriptObject("Maya", "Engineering")
    print(employee.describe())

    # Python binds employee as self when employee.describe() is evaluated.
    # JavaScript normally derives this from the invocation expression.
    print(js_method(employee, JavaScriptObject.describe))


def demonstrate_call_apply_bind() -> None:
    heading("call, apply, and bind")

    engineering = JavaScriptObject("Arun", "Engineering")
    security = JavaScriptObject("Leena", "Cybersecurity")

    print("call:", js_call(engineering, employee_summary, "approve a change"))
    print("apply:", js_apply(
        security,
        employee_summary,
        ["inspect a security review"]
    ))

    # A bound function retains its receiver even when called elsewhere.
    bound_summary = js_bind(
        engineering,
        employee_summary,
        "merge a reviewed pull request"
    )
    print("bind:", bound_summary())

    # Bind can preset fewer arguments and accept the rest later.
    bound_partial = js_bind(security, employee_summary)
    print("bind with later argument:", bound_partial("audit branch rules"))


def demonstrate_constructor_behavior() -> None:
    heading("Constructor-style initialization")

    class RepositoryMember:
        """A Python analogue of a constructor assigning instance properties."""

        def __init__(self, username: str, role: str) -> None:
            self.username = username
            self.role = role

        def display(self) -> str:
            return f"{self.username}: {self.role}"

    reviewer = RepositoryMember("reviewer_01", "CODE_REVIEWER")
    print(reviewer.display())

    # In JavaScript, new RepositoryMember(...) creates a new instance and
    # binds this to that instance during constructor execution.
    # Python's __init__ receives the instance through self instead.
    print(f"Stored fields: {reviewer.__dict__}")


def demonstrate_arrow_function_distinction() -> None:
    heading("Arrow functions and lexical this")

    class Dashboard:
        def __init__(self, owner: str) -> None:
            self.owner = owner

        def make_callback(self) -> Callable[[], str]:
            # This closure captures self lexically. It illustrates the
            # result of JavaScript's arrow-function lexical-this behavior.
            captured_owner = self.owner
            return lambda: f"Dashboard owner: {captured_owner}"

    dashboard = Dashboard("Atul")
    callback = dashboard.make_callback()
    print(callback())

    # A JavaScript arrow function has no independently bound this.
    # call, apply, and bind cannot replace its lexical this.
    # A normal JavaScript function, by contrast, may receive a different
    # this depending on how it is invoked.


def demonstrate_callback_context_loss() -> None:
    heading("Callback context")

    class NotificationService:
        def __init__(self, service_name: str) -> None:
            self.service_name = service_name

        def send(self, message: str) -> str:
            return f"[{self.service_name}] {message}"

    service = NotificationService("ReviewNotifier")

    # Saving a Python bound method retains the instance automatically.
    saved_method = service.send
    print(saved_method("Approval required"))

    # JavaScript commonly loses a normal method's receiver when the method
    # is extracted and called as a standalone function. bind fixes this.
    # Python's equivalent is to preserve the bound method or use a closure.
    def send_with_captured_service(message: str) -> str:
        return service.send(message)

    callback = send_with_captured_service
    print(callback("Required checks are pending"))


def demonstrate_edge_cases() -> None:
    heading("Receiver validation and edge cases")

    def safe_summary(receiver: Any) -> str:
        if not isinstance(receiver, JavaScriptObject):
            raise TypeError("Receiver must be a JavaScriptObject")
        return employee_summary(receiver)

    employee = JavaScriptObject("Nina", "Platform")

    print(safe_summary(employee))

    try:
        safe_summary({"name": "Nina"})
    except TypeError as error:
        print("Rejected invalid receiver:", error)

    # Python does not implement JavaScript's strict-mode or sloppy-mode
    # this conversion rules. In JavaScript, an ordinary function called
    # without a receiver may see undefined in strict mode or the global
    # object in non-strict mode. Class methods are strict-mode functions.


def main() -> None:
    demonstrate_python_receiver_model()
    demonstrate_call_apply_bind()
    demonstrate_constructor_behavior()
    demonstrate_arrow_function_distinction()
    demonstrate_callback_context_loss()
    demonstrate_edge_cases()


if __name__ == "__main__":
    main()
