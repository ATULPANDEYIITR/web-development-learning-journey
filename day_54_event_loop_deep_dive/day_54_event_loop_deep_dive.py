from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Deque, Dict, List, Optional


class TaskType(Enum):
    TIMER = "timer"
    IO = "io"
    USER_EVENT = "user-event"
    RENDER = "render"


@dataclass
class Task:
    name: str
    callback: Callable[[], None]
    task_type: TaskType
    scheduled_at: int
    sequence: int


@dataclass
class EventLoop:
    """
    A deterministic event-loop simulator.

    Model:
        Call stack
            -> synchronous execution
            -> microtask checkpoint
            -> one task
            -> microtask checkpoint
            -> rendering opportunity
            -> repeat

    This is intentionally deterministic so ordering can be tested without
    depending on operating-system scheduling.
    """

    max_microtasks_per_checkpoint: int = 1000
    frame_interval: int = 16
    now: int = 0

    _stack: List[str] = field(default_factory=list)
    _tasks: Deque[Task] = field(default_factory=deque)
    _microtasks: Deque[Task] = field(default_factory=deque)
    _render_callbacks: Deque[Task] = field(default_factory=deque)
    _log: List[str] = field(default_factory=list)
    _sequence: int = 0
    _next_frame: int = 16

    def log(self, message: str) -> None:
        self._log.append(f"{self.now:04d}ms | {message}")

    def call_stack_depth(self) -> int:
        return len(self._stack)

    def run_sync(self, name: str, callback: Callable[[], None]) -> None:
        self._stack.append(name)
        self.log(f"stack-enter {name}")
        try:
            callback()
        finally:
            self.log(f"stack-exit {name}")
            self._stack.pop()

    def queue_microtask(self, name: str, callback: Callable[[], None]) -> None:
        self._sequence += 1
        self._microtasks.append(
            Task(name, callback, TaskType.IO, self.now, self._sequence)
        )
        self.log(f"microtask-queued {name}")

    def queue_task(
        self,
        name: str,
        callback: Callable[[], None],
        task_type: TaskType = TaskType.IO,
        delay: int = 0,
    ) -> None:
        if delay < 0:
            raise ValueError("delay cannot be negative")

        self._sequence += 1
        self._tasks.append(
            Task(
                name=name,
                callback=callback,
                task_type=task_type,
                scheduled_at=self.now + delay,
                sequence=self._sequence,
            )
        )
        self.log(f"task-queued {name} delay={delay}ms")

    def request_render(self, name: str, callback: Callable[[], None]) -> None:
        self._sequence += 1
        self._render_callbacks.append(
            Task(name, callback, TaskType.RENDER, self.now, self._sequence)
        )
        self.log(f"render-requested {name}")

    def _run_microtasks(self) -> None:
        processed = 0

        while self._microtasks:
            if processed >= self.max_microtasks_per_checkpoint:
                raise RuntimeError(
                    "microtask checkpoint exceeded safety limit; "
                    "possible starvation"
                )

            task = self._microtasks.popleft()
            processed += 1

            self.run_sync(task.name, task.callback)
            self.log(f"microtask-complete {task.name}")

    def _next_ready_task(self) -> Optional[Task]:
        ready = [
            task
            for task in self._tasks
            if task.scheduled_at <= self.now
        ]

        if not ready:
            return None

        selected = min(
            ready,
            key=lambda task: (task.scheduled_at, task.sequence),
        )
        self._tasks.remove(selected)
        return selected

    def _advance_time(self) -> None:
        future_times = [
            task.scheduled_at
            for task in self._tasks
            if task.scheduled_at > self.now
        ]

        if not future_times:
            self.now = self._next_frame
            return

        next_task_time = min(future_times)
        self.now = min(next_task_time, self._next_frame)

    def _render_if_due(self) -> None:
        if self.now < self._next_frame:
            return

        self.log("rendering-opportunity")

        while self._render_callbacks:
            task = self._render_callbacks.popleft()
            self.run_sync(task.name, task.callback)
            self.log(f"render-complete {task.name}")

        self._next_frame += self.frame_interval

    def run(self, max_turns: int = 100) -> List[str]:
        if max_turns <= 0:
            raise ValueError("max_turns must be positive")

        turns = 0

        while (
            self._tasks
            or self._microtasks
            or self._render_callbacks
        ):
            if turns >= max_turns:
                raise RuntimeError("event loop exceeded maximum turn count")

            turns += 1

            self._run_microtasks()

            task = self._next_ready_task()

            if task is None:
                self._advance_time()
                self._render_if_due()
                continue

            self.run_sync(task.name, task.callback)
            self.log(f"task-complete {task.name}")

            # Microtasks run at the checkpoint before another task is chosen.
            self._run_microtasks()

            self._render_if_due()

        return self._log


def build_demo() -> EventLoop:
    loop = EventLoop()

    def application_start() -> None:
        loop.log("synchronous-start")

        loop.queue_microtask(
            "promise-then",
            lambda: loop.log("Promise reaction executes"),
        )

        loop.queue_task(
            "timer-0",
            lambda: loop.log("timer callback executes"),
            TaskType.TIMER,
        )

        loop.request_render(
            "paint",
            lambda: loop.log("render callback executes"),
        )

        loop.run_sync(
            "nested-function",
            lambda: loop.log(
                f"nested stack depth={loop.call_stack_depth()}"
            ),
        )

        loop.log("synchronous-end")

    loop.run_sync("application-start", application_start)

    loop.queue_task(
        "network-response",
        lambda: (
            loop.log("network response callback executes"),
            loop.queue_microtask(
                "response-microtask",
                lambda: loop.log("microtask created by network callback"),
            ),
        ),
        TaskType.IO,
        delay=5,
    )

    return loop


def demonstrate_microtask_starvation() -> str:
    loop = EventLoop(max_microtasks_per_checkpoint=5)

    counter = {"value": 0}

    def recursive_microtask() -> None:
        counter["value"] += 1
        loop.queue_microtask(
            f"recursive-{counter['value']}",
            recursive_microtask,
        )

    loop.queue_microtask("recursive-0", recursive_microtask)

    try:
        loop.run()
    except RuntimeError as exc:
        return f"Starvation protection triggered after {counter['value']} callbacks: {exc}"

    return "No starvation detected"


def main() -> None:
    loop = build_demo()

    for entry in loop.run():
        print(entry)

    print()
    print(demonstrate_microtask_starvation())

    # Basic correctness checks for the model.
    loop = EventLoop()
    observed: List[str] = []

    loop.run_sync(
        "test-sync",
        lambda: (
            observed.append("sync"),
            loop.queue_microtask("test-microtask", lambda: observed.append("microtask")),
            loop.queue_task("test-task", lambda: observed.append("task")),
        ),
    )

    loop.run()
    assert observed == ["sync", "microtask", "task"]


if __name__ == "__main__":
    main()
