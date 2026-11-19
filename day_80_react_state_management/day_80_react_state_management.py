#!/usr/bin/env python3
"""
React State Management: Redux Concepts and Redux Toolkit Simulation

Demonstrates:
- Centralized application state
- Actions and action creators
- Pure reducers
- Redux-style store
- Middleware and logging
- Thunk-style asynchronous operations
- Immutable state updates
- Selectors and derived state
- State subscriptions
- Error handling and validation
- Undo history and state snapshots

Run:
    python react_state_management.py
"""

from __future__ import annotations

import asyncio
import copy
import logging
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger("redux-simulation")


# ============================================================
# 1. Domain Types
# ============================================================

class ActionType(str, Enum):
    TASK_ADDED = "tasks/added"
    TASK_TOGGLED = "tasks/toggled"
    TASK_DELETED = "tasks/deleted"
    FILTER_CHANGED = "tasks/filterChanged"
    COUNTER_INCREMENTED = "counter/incremented"
    COUNTER_DECREMENTED = "counter/decremented"
    DATA_REQUESTED = "data/requested"
    DATA_SUCCEEDED = "data/succeeded"
    DATA_FAILED = "data/failed"
    STATE_RESET = "app/reset"


class AsyncStatus(str, Enum):
    IDLE = "idle"
    LOADING = "loading"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class Action:
    type: str
    payload: Any = None
    meta: dict = field(default_factory=dict)
    error: bool = False


@dataclass
class MiddlewareContext:
    store: "Store"
    get_state: Callable[[], dict]


Reducer = Callable[[dict, Action], dict]
Middleware = Callable[
    ["Store", Action, Callable[[Action], dict]],
    Any
]


# ============================================================
# 2. Initial Application State
# ============================================================

def create_initial_state() -> dict:
    return {
        "tasks": [],
        "filter": "all",
        "counter": 0,
        "request": {
            "status": AsyncStatus.IDLE.value,
            "data": [],
            "error": None
        }
    }


# ============================================================
# 3. Action Creators
# ============================================================

def add_task(task_id: int, title: str) -> Action:
    return Action(
        type=ActionType.TASK_ADDED.value,
        payload={"id": task_id, "title": title}
    )


def toggle_task(task_id: int) -> Action:
    return Action(
        type=ActionType.TASK_TOGGLED.value,
        payload={"id": task_id}
    )


def delete_task(task_id: int) -> Action:
    return Action(
        type=ActionType.TASK_DELETED.value,
        payload={"id": task_id}
    )


def change_filter(filter_name: str) -> Action:
    return Action(
        type=ActionType.FILTER_CHANGED.value,
        payload=filter_name
    )


# ============================================================
# 4. Pure Reducer Functions
# ============================================================

def tasks_reducer(state: list, action: Action) -> list:
    if action.type == ActionType.TASK_ADDED.value:
        payload = action.payload

        if not isinstance(payload, dict):
            raise ValueError("Task payload must be an object")

        task_id = payload.get("id")
        title = payload.get("title")

        if not isinstance(task_id, int) or isinstance(task_id, bool):
            raise ValueError("Task ID must be an integer")

        if not isinstance(title, str) or not title.strip():
            raise ValueError("Task title cannot be empty")

        if any(task["id"] == task_id for task in state):
            raise ValueError(f"Task ID {task_id} already exists")

        return state + [{
            "id": task_id,
            "title": title.strip(),
            "completed": False
        }]

    if action.type == ActionType.TASK_TOGGLED.value:
        task_id = action.payload["id"]

        if not any(task["id"] == task_id for task in state):
            raise KeyError(f"Task {task_id} does not exist")

        return [
            {
                **task,
                "completed": not task["completed"]
            }
            if task["id"] == task_id else task
            for task in state
        ]

    if action.type == ActionType.TASK_DELETED.value:
        task_id = action.payload["id"]

        if not any(task["id"] == task_id for task in state):
            raise KeyError(f"Task {task_id} does not exist")

        return [
            task for task in state
            if task["id"] != task_id
        ]

    return state


def request_reducer(state: dict, action: Action) -> dict:
    if action.type == ActionType.DATA_REQUESTED.value:
        return {
            **state,
            "status": AsyncStatus.LOADING.value,
            "error": None
        }

    if action.type == ActionType.DATA_SUCCEEDED.value:
        return {
            "status": AsyncStatus.SUCCEEDED.value,
            "data": copy.deepcopy(action.payload),
            "error": None
        }

    if action.type == ActionType.DATA_FAILED.value:
        return {
            **state,
            "status": AsyncStatus.FAILED.value,
            "error": str(action.payload)
        }

    return state


def root_reducer(state: dict, action: Action) -> dict:
    if action.type == ActionType.STATE_RESET.value:
        return create_initial_state()

    counter = state["counter"]

    if action.type == ActionType.COUNTER_INCREMENTED.value:
        counter += 1

    elif action.type == ActionType.COUNTER_DECREMENTED.value:
        counter -= 1

    if not isinstance(counter, int):
        raise ValueError("Counter must remain an integer")

    new_filter = state["filter"]

    if action.type == ActionType.FILTER_CHANGED.value:
        new_filter = action.payload

        if new_filter not in {"all", "active", "completed"}:
            raise ValueError("Invalid task filter")

    return {
        "tasks": tasks_reducer(state["tasks"], action),
        "filter": new_filter,
        "counter": counter,
        "request": request_reducer(state["request"], action)
    }


# ============================================================
# 5. Redux-Style Store
# ============================================================

class Store:
    def __init__(self, reducer: Reducer, initial_state: dict):
        self.reducer = reducer
        self._state = copy.deepcopy(initial_state)
        self._listeners: list[Callable] = []
        self._dispatching = False

    def get_state(self) -> dict:
        return copy.deepcopy(self._state)

    def subscribe(self, listener: Callable) -> Callable:
        if not callable(listener):
            raise TypeError("Listener must be callable")

        self._listeners.append(listener)

        def unsubscribe():
            if listener in self._listeners:
                self._listeners.remove(listener)

        return unsubscribe

    def dispatch(self, action: Action) -> dict:
        if not isinstance(action, Action):
            raise TypeError("Dispatch expects an Action")

        if self._dispatching:
            raise RuntimeError("Reducers cannot dispatch actions")

        self._dispatching = True

        try:
            # A failed reducer must not partially modify store state.
            new_state = self.reducer(self._state, action)

            if not isinstance(new_state, dict):
                raise TypeError("Root reducer must return a dictionary")

            self._state = new_state

        finally:
            self._dispatching = False

        for listener in tuple(self._listeners):
            listener(self.get_state(), action)

        return self.get_state()


# ============================================================
# 6. Middleware
# ============================================================

def logger_middleware(
    store: Store,
    action: Action,
    next_dispatch: Callable
):
    logger.info("Dispatching: %s", action.type)

    result = next_dispatch(action)

    logger.info(
        "Current counter: %s",
        store.get_state()["counter"]
    )

    return result


def validation_middleware(
    store: Store,
    action: Action,
    next_dispatch: Callable
):
    if not isinstance(action.type, str) or not action.type:
        raise ValueError("Action type is required")

    return next_dispatch(action)


def apply_middleware(store: Store, *middlewares):
    original_dispatch = store.dispatch

    def build_chain(index: int, action: Action):
        if index == len(middlewares):
            return original_dispatch(action)

        middleware = middlewares[index]

        return middleware(
            store,
            action,
            lambda next_action: build_chain(index + 1, next_action)
        )

    store.dispatch = lambda action: build_chain(0, action)


# ============================================================
# 7. Selectors
# ============================================================

def select_tasks(state: dict) -> list:
    filter_name = state["filter"]

    if filter_name == "active":
        return [
            task for task in state["tasks"]
            if not task["completed"]
        ]

    if filter_name == "completed":
        return [
            task for task in state["tasks"]
            if task["completed"]
        ]

    return state["tasks"]


def select_task_statistics(state: dict) -> dict:
    tasks = state["tasks"]

    completed = sum(
        task["completed"] for task in tasks
    )

    total = len(tasks)

    return {
        "total": total,
        "completed": completed,
        "active": total - completed,
        "completion_rate": (
            round(completed / total * 100, 2)
            if total else 0.0
        )
    }


# ============================================================
# 8. Asynchronous Thunk Operations
# ============================================================

async def fetch_remote_tasks(store: Store):
    store.dispatch(Action(ActionType.DATA_REQUESTED.value))

    try:
        # Simulates an asynchronous service request.
        await asyncio.sleep(0.1)

        remote_data = [
            {"id": 101, "title": "Review pull requests"},
            {"id": 102, "title": "Run automated tests"}
        ]

        store.dispatch(
            Action(
                ActionType.DATA_SUCCEEDED.value,
                payload=remote_data
            )
        )

    except Exception as exc:
        store.dispatch(
            Action(
                ActionType.DATA_FAILED.value,
                payload=str(exc),
                error=True
            )
        )


# ============================================================
# 9. Undo History
# ============================================================

class History:
    def __init__(self, maximum_size: int = 20):
        if maximum_size < 1:
            raise ValueError("History size must be positive")

        self.snapshots = deque(maxlen=maximum_size)

    def record(self, state: dict):
        self.snapshots.append(copy.deepcopy(state))

    def previous(self) -> Optional[dict]:
        if len(self.snapshots) < 2:
            return None

        self.snapshots.pop()
        return copy.deepcopy(self.snapshots[-1])


# ============================================================
# 10. Application Demonstration
# ============================================================

async def main():
    store = Store(
        reducer=root_reducer,
        initial_state=create_initial_state()
    )

    apply_middleware(
        store,
        validation_middleware,
        logger_middleware
    )

    history = History()

    store.subscribe(
        lambda state, action: print(
            f"STATE UPDATED | {action.type}"
        )
    )

    def dispatch(action):
        history.record(store.get_state())
        return store.dispatch(action)

    print("\n--- TASK OPERATIONS ---")

    dispatch(add_task(1, "Understand Redux reducers"))
    dispatch(add_task(2, "Implement middleware"))
    dispatch(add_task(3, "Test asynchronous actions"))

    dispatch(toggle_task(1))

    print("\nAll tasks:")
    print(select_tasks(store.get_state()))

    print("\nStatistics:")
    print(select_task_statistics(store.get_state()))

    dispatch(change_filter("active"))

    print("\nActive tasks:")
    print(select_tasks(store.get_state()))

    print("\n--- COUNTER OPERATIONS ---")

    dispatch(Action(ActionType.COUNTER_INCREMENTED.value))
    dispatch(Action(ActionType.COUNTER_INCREMENTED.value))
    dispatch(Action(ActionType.COUNTER_DECREMENTED.value))

    print("Counter:", store.get_state()["counter"])

    print("\n--- ASYNC OPERATION ---")

    await fetch_remote_tasks(store)

    print("Request state:")
    print(store.get_state()["request"])

    print("\n--- EDGE CASE TESTS ---")

    try:
        dispatch(add_task(1, "Duplicate task"))
    except (ValueError, KeyError) as exc:
        print("Expected validation failure:", exc)

    try:
        dispatch(change_filter("invalid"))
    except ValueError as exc:
        print("Expected filter failure:", exc)

    print("\n--- IMMUTABILITY TEST ---")

    external_state = store.get_state()
    external_state["counter"] = 999

    assert store.get_state()["counter"] != 999

    print("External state modification did not affect the store.")

    print("\n--- RESET ---")

    dispatch(Action(ActionType.STATE_RESET.value))

    print(store.get_state())


if __name__ == "__main__":
    asyncio.run(main())
