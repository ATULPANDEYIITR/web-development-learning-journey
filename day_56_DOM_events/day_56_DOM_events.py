"""
DOM Events: event propagation, delegation, default behavior, and workflow simulation.

This is a self-contained Python model of browser-style event dispatch.
It models:
- event targets
- capturing
- target handling
- bubbling
- listener registration
- stopPropagation
- stopImmediatePropagation
- preventDefault
- delegated handling
- once listeners
- passive listeners
- event paths
- validation and failure conditions

Python does not provide a browser DOM, so the implementation models the
event-dispatch semantics explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional


class EventPhase(Enum):
    CAPTURING = 1
    AT_TARGET = 2
    BUBBLING = 3


class EventDispatchError(Exception):
    """Raised when an invalid event operation is requested."""


@dataclass
class Event:
    type: str
    target: "Node"
    bubbles: bool = True
    cancelable: bool = True
    default_prevented: bool = False
    propagation_stopped: bool = False
    immediate_propagation_stopped: bool = False
    phase: Optional[EventPhase] = None
    current_target: Optional["Node"] = None
    default_action: Optional[Callable[[], None]] = None

    def stop_propagation(self) -> None:
        self.propagation_stopped = True

    def stop_immediate_propagation(self) -> None:
        self.immediate_propagation_stopped = True
        self.propagation_stopped = True

    def prevent_default(self) -> None:
        if self.cancelable:
            self.default_prevented = True


@dataclass
class Listener:
    callback: Callable[[Event], None]
    capture: bool = False
    once: bool = False
    passive: bool = False
    selector: Optional[str] = None


@dataclass
class Node:
    name: str
    element_id: Optional[str] = None
    classes: set[str] = field(default_factory=set)
    parent: Optional["Node"] = field(default=None, repr=False)
    children: List["Node"] = field(default_factory=list, repr=False)
    listeners: Dict[str, List[Listener]] = field(
        default_factory=dict, repr=False
    )

    def append_child(self, child: "Node") -> None:
        if child is self:
            raise EventDispatchError("A node cannot be its own child.")

        cursor = self
        while cursor is not None:
            if cursor is child:
                raise EventDispatchError("A node cannot become its own ancestor.")
            cursor = cursor.parent

        if child.parent is not None:
            child.parent.children.remove(child)

        child.parent = self
        self.children.append(child)

    def add_event_listener(
        self,
        event_type: str,
        callback: Callable[[Event], None],
        *,
        capture: bool = False,
        once: bool = False,
        passive: bool = False,
        selector: Optional[str] = None,
    ) -> None:
        if not event_type:
            raise EventDispatchError("Event type cannot be empty.")

        self.listeners.setdefault(event_type, []).append(
            Listener(
                callback=callback,
                capture=capture,
                once=once,
                passive=passive,
                selector=selector,
            )
        )

    def remove_event_listener(
        self,
        event_type: str,
        callback: Callable[[Event], None],
        *,
        capture: bool = False,
    ) -> bool:
        listeners = self.listeners.get(event_type, [])
        for index, listener in enumerate(listeners):
            if listener.callback is callback and listener.capture == capture:
                listeners.pop(index)
                return True
        return False

    def matches(self, selector: str) -> bool:
        if selector.startswith("#"):
            return self.element_id == selector[1:]

        if selector.startswith("."):
            return selector[1:] in self.classes

        return self.name == selector

    def path_from_root(self) -> List["Node"]:
        path: List[Node] = []
        current: Optional[Node] = self

        while current is not None:
            path.append(current)
            current = current.parent

        return list(reversed(path))

    def dispatch_event(self, event: Event) -> bool:
        if event.target is not self:
            raise EventDispatchError(
                "The event target must be the node dispatching the event."
            )

        path = self.path_from_root()
        event.default_prevented = False
        event.propagation_stopped = False
        event.immediate_propagation_stopped = False

        # Capture travels root -> parent of target.
        for node in path[:-1]:
            if event.propagation_stopped:
                break

            event.phase = EventPhase.CAPTURING
            event.current_target = node
            self._invoke_listeners(node, event, capture=True)

        # Target phase invokes capture listeners first, then bubble listeners.
        if not event.propagation_stopped:
            event.phase = EventPhase.AT_TARGET
            event.current_target = self
            self._invoke_listeners(self, event, capture=True)

        if not event.immediate_propagation_stopped:
            self._invoke_listeners(self, event, capture=False)

        # Bubble travels parent of target -> root.
        if event.bubbles and not event.propagation_stopped:
            for node in reversed(path[:-1]):
                if event.propagation_stopped:
                    break

                event.phase = EventPhase.BUBBLING
                event.current_target = node
                self._invoke_listeners(node, event, capture=False)

        event.phase = None
        event.current_target = None

        if not event.default_prevented and event.default_action is not None:
            event.default_action()

        return not event.default_prevented

    def _invoke_listeners(
        self,
        node: "Node",
        event: Event,
        *,
        capture: bool,
    ) -> None:
        listeners = node.listeners.get(event.type, [])
        to_remove: List[Listener] = []

        for listener in list(listeners):
            if listener.capture != capture:
                continue

            if listener.selector is not None:
                matched = self._find_matching_target(
                    event.target, node, listener.selector
                )
                if matched is None:
                    continue

            previous_prevented = event.default_prevented

            listener.callback(event)

            # A passive listener cannot cancel the default action.
            if listener.passive and event.default_prevented:
                event.default_prevented = previous_prevented

            if listener.once:
                to_remove.append(listener)

            if event.immediate_propagation_stopped:
                break

        for listener in to_remove:
            if listener in listeners:
                listeners.remove(listener)

    @staticmethod
    def _find_matching_target(
        target: "Node",
        delegation_root: "Node",
        selector: str,
    ) -> Optional["Node"]:
        current: Optional[Node] = target

        while current is not None:
            if current.matches(selector):
                return current

            if current is delegation_root:
                break

            current = current.parent

        return None


def describe(event: Event, label: str) -> None:
    current = event.current_target.name if event.current_target else "-"
    print(
        f"{label}: target={event.target.name}, "
        f"current={current}, phase={event.phase.name if event.phase else '-'}"
    )


def main() -> None:
    document = Node("document")
    page = Node("section", element_id="page")
    menu = Node("ul", element_id="menu")
    item_a = Node("li", element_id="item-a", classes={"menu-item"})
    item_b = Node("li", element_id="item-b", classes={"menu-item"})
    button = Node("button", element_id="save")

    document.append_child(page)
    page.append_child(menu)
    menu.append_child(item_a)
    menu.append_child(item_b)
    item_a.append_child(button)

    print("=== Capturing and bubbling ===")

    document.add_event_listener(
        "click",
        lambda event: describe(event, "document capture"),
        capture=True,
    )

    page.add_event_listener(
        "click",
        lambda event: describe(event, "page capture"),
        capture=True,
    )

    button.add_event_listener(
        "click",
        lambda event: describe(event, "button target")
    )

    page.add_event_listener(
        "click",
        lambda event: describe(event, "page bubble")
    )

    document.add_event_listener(
        "click",
        lambda event: describe(event, "document bubble")
    )

    click = Event(type="click", target=button)
    button.dispatch_event(click)

    print("\n=== Event delegation ===")

    def delegated_menu_handler(event: Event) -> None:
        describe(event, "delegated .menu-item handler")

    menu.add_event_listener(
        "click",
        delegated_menu_handler,
        selector=".menu-item",
    )

    item_a.dispatch_event(Event(type="click", target=item_a))

    print("\n=== preventDefault ===")

    def prevent_navigation(event: Event) -> None:
        print("navigation handler: default action cancelled")
        event.prevent_default()

    button.add_event_listener("navigate", prevent_navigation)

    navigation = Event(
        type="navigate",
        target=button,
        default_action=lambda: print("DEFAULT: navigation executed"),
    )
    allowed = button.dispatch_event(navigation)
    print(f"default action allowed: {allowed}")

    print("\n=== stopPropagation ===")

    parent = Node("div", element_id="parent")
    child = Node("button", element_id="child")
    document.append_child(parent)
    parent.append_child(child)

    parent.add_event_listener(
        "custom",
        lambda event: (
            print("parent listener"),
            event.stop_propagation(),
        ),
        capture=True,
    )

    document.add_event_listener(
        "custom",
        lambda event: print("document should not receive this event"),
        capture=False,
    )

    child.dispatch_event(Event(type="custom", target=child))

    print("\n=== once listener ===")

    calls = {"count": 0}

    def run_once(event: Event) -> None:
        calls["count"] += 1
        print(f"once listener invoked: {calls['count']}")

    child.add_event_listener("once-event", run_once, once=True)
    child.dispatch_event(Event(type="once-event", target=child))
    child.dispatch_event(Event(type="once-event", target=child))

    assert calls["count"] == 1

    print("\n=== passive listener ===")

    passive = Node("div")

    def passive_handler(event: Event) -> None:
        event.prevent_default()

    passive.add_event_listener(
        "wheel",
        passive_handler,
        passive=True,
    )

    wheel = Event(
        type="wheel",
        target=passive,
        default_action=lambda: print("DEFAULT: scrolling remains enabled"),
    )
    assert passive.dispatch_event(wheel) is True

    print("\n=== Non-bubbling event ===")

    leaf = Node("input")
    parent = Node("form")
    parent.append_child(leaf)

    parent.add_event_listener(
        "focus",
        lambda event: print("parent bubble listener should not run"),
    )

    leaf.dispatch_event(Event(type="focus", target=leaf, bubbles=False))

    print("\nAll assertions passed.")


if __name__ == "__main__":
    main()
