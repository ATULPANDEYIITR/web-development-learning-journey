"""
React Testing: Unit Tests, Component Tests, Mocking, and User Interaction Testing

A self-contained Python model demonstrating the testing principles used
in React applications:

1. Unit testing and isolated function validation
2. Component behavior testing
3. Mocking asynchronous API dependencies
4. User interaction testing
5. State and rendering validation
6. Error handling and boundary conditions
7. Test fixtures and reusable assertions
8. Test execution and coverage reporting

Run:
    python react_testing.py
"""

from __future__ import annotations

import asyncio
import unittest
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


# ============================================================
# 1. DOMAIN MODELS
# ============================================================

class RequestStatus(Enum):
    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class User:
    user_id: int
    name: str
    email: str
    active: bool = True


@dataclass
class ComponentState:
    status: RequestStatus = RequestStatus.IDLE
    users: list[User] = field(default_factory=list)
    error: Optional[str] = None
    search_query: str = ""


# ============================================================
# 2. UNIT TESTING: PURE FUNCTIONS
# ============================================================

def validate_email(email: str) -> bool:
    """Validate basic email structure without external dependencies."""
    if not isinstance(email, str):
        return False

    email = email.strip()

    if not email or len(email) > 254:
        return False

    if email.count("@") != 1:
        return False

    local, domain = email.split("@")

    if not local or len(local) > 64:
        return False

    if not domain or "." not in domain:
        return False

    if domain.startswith(".") or domain.endswith("."):
        return False

    if " " in email:
        return False

    return True


def normalize_search_query(query: str) -> str:
    """Normalize user-entered search text."""
    if not isinstance(query, str):
        raise TypeError("Search query must be a string")

    return " ".join(query.strip().lower().split())


def filter_users(users: list[User], query: str) -> list[User]:
    """Return users matching name or email."""
    normalized = normalize_search_query(query)

    if not normalized:
        return list(users)

    return [
        user for user in users
        if normalized in user.name.lower()
        or normalized in user.email.lower()
    ]


def format_user_name(user: User) -> str:
    """Return a display-ready user name."""
    return user.name.strip().title()


# ============================================================
# 3. MOCK API SERVICE
# ============================================================

class UserAPI:
    """Dependency interface used by the component model."""

    async def fetch_users(self) -> list[User]:
        raise NotImplementedError


class MockUserAPI(UserAPI):
    """
    Deterministic mock dependency.

    Allows tests to simulate successful requests, failures,
    and empty responses without accessing a real backend.
    """

    def __init__(
        self,
        users: Optional[list[User]] = None,
        should_fail: bool = False,
        delay: float = 0
    ):
        self.users = users or []
        self.should_fail = should_fail
        self.delay = delay
        self.call_count = 0

    async def fetch_users(self) -> list[User]:
        self.call_count += 1

        if self.delay:
            await asyncio.sleep(self.delay)

        if self.should_fail:
            raise ConnectionError("Unable to retrieve users")

        return list(self.users)


# ============================================================
# 4. COMPONENT BEHAVIOR MODEL
# ============================================================

class UserListComponent:
    """
    Framework-independent model of a React component.

    It represents component state, asynchronous effects,
    rendering decisions, and user-triggered interactions.
    """

    def __init__(self, api: UserAPI):
        self.api = api
        self.state = ComponentState()
        self.mounted = False
        self.request_version = 0

    async def mount(self) -> None:
        """Simulate component initialization and data loading."""
        self.mounted = True
        await self.load_users()

    async def load_users(self) -> None:
        self.request_version += 1
        current_version = self.request_version

        self.state.status = RequestStatus.LOADING
        self.state.error = None

        try:
            users = await self.api.fetch_users()

            # Ignore results belonging to an outdated request.
            if not self.mounted or current_version != self.request_version:
                return

            self.state.users = users
            self.state.status = RequestStatus.SUCCESS

        except Exception as exc:
            if not self.mounted or current_version != self.request_version:
                return

            self.state.status = RequestStatus.ERROR
            self.state.error = str(exc)

    def unmount(self) -> None:
        """Prevent pending asynchronous work from updating state."""
        self.mounted = False
        self.request_version += 1

    def search(self, query: str) -> None:
        """Simulate a controlled input event."""
        self.state.search_query = normalize_search_query(query)

    def get_visible_users(self) -> list[User]:
        return filter_users(
            self.state.users,
            self.state.search_query
        )

    def render(self) -> dict[str, Any]:
        """
        Represent the component's visible output.

        A real React component would produce a DOM tree.
        """
        if self.state.status == RequestStatus.LOADING:
            return {"type": "loading", "text": "Loading users..."}

        if self.state.status == RequestStatus.ERROR:
            return {
                "type": "error",
                "text": self.state.error or "Unknown error"
            }

        users = self.get_visible_users()

        if not users:
            return {
                "type": "empty",
                "text": "No users found"
            }

        return {
            "type": "list",
            "users": [
                {
                    "id": user.user_id,
                    "name": format_user_name(user),
                    "email": user.email
                }
                for user in users
            ]
        }


# ============================================================
# 5. TEST FIXTURES
# ============================================================

def create_test_users() -> list[User]:
    return [
        User(1, "alice johnson", "alice@example.com"),
        User(2, "bob smith", "bob@example.com"),
        User(3, "charlie brown", "charlie@example.com"),
    ]


# ============================================================
# 6. UNIT TESTS
# ============================================================

class TestEmailValidation(unittest.TestCase):

    def test_valid_email(self):
        self.assertTrue(validate_email("alice@example.com"))

    def test_email_with_whitespace(self):
        self.assertTrue(validate_email(" alice@example.com "))

    def test_missing_at_symbol(self):
        self.assertFalse(validate_email("alice.example.com"))

    def test_multiple_at_symbols(self):
        self.assertFalse(validate_email("alice@@example.com"))

    def test_missing_domain(self):
        self.assertFalse(validate_email("alice@"))

    def test_invalid_input_type(self):
        self.assertFalse(validate_email(None))

    def test_missing_domain_extension(self):
        self.assertFalse(validate_email("alice@example"))


class TestSearchFunctions(unittest.TestCase):

    def setUp(self):
        self.users = create_test_users()

    def test_search_by_name(self):
        result = filter_users(self.users, "alice")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].user_id, 1)

    def test_search_by_email(self):
        result = filter_users(self.users, "bob@example")
        self.assertEqual(len(result), 1)

    def test_case_insensitive_search(self):
        result = filter_users(self.users, "ALICE")
        self.assertEqual(len(result), 1)

    def test_empty_search(self):
        self.assertEqual(
            len(filter_users(self.users, "")),
            3
        )

    def test_no_matching_user(self):
        self.assertEqual(
            filter_users(self.users, "unknown"),
            []
        )

    def test_normalization(self):
        self.assertEqual(
            normalize_search_query("  ALICE   JOHNSON "),
            "alice johnson"
        )

    def test_invalid_query_type(self):
        with self.assertRaises(TypeError):
            normalize_search_query(None)


# ============================================================
# 7. COMPONENT TESTS
# ============================================================

class TestUserListComponent(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.users = create_test_users()
        self.api = MockUserAPI(self.users)
        self.component = UserListComponent(self.api)

    async def test_initial_state(self):
        self.assertEqual(
            self.component.state.status,
            RequestStatus.IDLE
        )

    async def test_successful_mount(self):
        await self.component.mount()

        self.assertEqual(
            self.component.state.status,
            RequestStatus.SUCCESS
        )

        self.assertEqual(len(self.component.state.users), 3)

    async def test_loading_state(self):
        api = MockUserAPI(self.users, delay=0.05)
        component = UserListComponent(api)

        task = asyncio.create_task(component.mount())

        # Allow the asynchronous operation to start.
        await asyncio.sleep(0)

        self.assertEqual(
            component.render()["type"],
            "loading"
        )

        await task

    async def test_api_failure(self):
        api = MockUserAPI(should_fail=True)
        component = UserListComponent(api)

        await component.mount()

        self.assertEqual(
            component.state.status,
            RequestStatus.ERROR
        )

        self.assertIn("Unable to retrieve", component.state.error)

    async def test_empty_response(self):
        api = MockUserAPI([])
        component = UserListComponent(api)

        await component.mount()

        self.assertEqual(
            component.render()["type"],
            "empty"
        )

    async def test_user_interaction_search(self):
        await self.component.mount()

        self.component.search("alice")

        result = self.component.render()

        self.assertEqual(result["type"], "list")
        self.assertEqual(len(result["users"]), 1)
        self.assertEqual(result["users"][0]["name"], "Alice Johnson")

    async def test_search_with_no_results(self):
        await self.component.mount()

        self.component.search("unknown")

        self.assertEqual(
            self.component.render()["type"],
            "empty"
        )

    async def test_search_resets_to_all_users(self):
        await self.component.mount()

        self.component.search("alice")
        self.component.search("")

        self.assertEqual(
            len(self.component.get_visible_users()),
            3
        )

    async def test_api_call_count(self):
        await self.component.mount()

        self.assertEqual(self.api.call_count, 1)

    async def test_unmount_prevents_stale_update(self):
        api = MockUserAPI(self.users, delay=0.05)
        component = UserListComponent(api)

        task = asyncio.create_task(component.mount())

        await asyncio.sleep(0)
        component.unmount()

        await task

        self.assertFalse(component.mounted)
        self.assertEqual(
            component.state.status,
            RequestStatus.LOADING
        )


# ============================================================
# 8. ADDITIONAL TESTING UTILITIES
# ============================================================

@dataclass
class TestResult:
    name: str
    passed: bool
    message: str = ""


def run_contract_check(
    name: str,
    operation: Callable[[], Any],
    expected: Any
) -> TestResult:
    """Reusable assertion helper for simple behavioral contracts."""
    try:
        actual = operation()

        if actual != expected:
            return TestResult(
                name,
                False,
                f"Expected {expected!r}, received {actual!r}"
            )

        return TestResult(name, True)

    except Exception as exc:
        return TestResult(name, False, str(exc))


def demonstrate_contract_checks() -> None:
    checks = [
        run_contract_check(
            "Email validation",
            lambda: validate_email("test@example.com"),
            True
        ),
        run_contract_check(
            "Invalid email",
            lambda: validate_email("invalid"),
            False
        ),
        run_contract_check(
            "Search normalization",
            lambda: normalize_search_query("  REACT TESTING "),
            "react testing"
        )
    ]

    for result in checks:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status}: {result.name}")

        if result.message:
            print(f"  {result.message}")


# ============================================================
# 9. TEST EXECUTION
# ============================================================

def main() -> None:
    print("=" * 65)
    print("REACT TESTING: BEHAVIORAL TESTING MODEL")
    print("=" * 65)

    demonstrate_contract_checks()

    print("\nRunning automated tests...\n")

    suite = unittest.defaultTestLoader.loadTestsFromModule(
        __import__(__name__)
    )

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 65)
    print("TEST EXECUTION REPORT")
    print("=" * 65)

    print(f"Tests executed: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        "Result:",
        "PASSED" if result.wasSuccessful() else "FAILED"
    )

    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
