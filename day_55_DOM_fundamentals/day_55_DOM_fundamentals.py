#!/usr/bin/env python3
"""DOM fundamentals: tree traversal, selectors, mutation, and safe rendering.

Uses a small in-memory DOM model so the workflow runs with Python's
standard library. It models core DOM operations, not a browser HTML parser.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from typing import Iterable


class DOMError(Exception):
    """Raised when a DOM operation would violate tree invariants."""


@dataclass
class Element:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    text: str = ""
    children: list[Element] = field(default_factory=list)
    parent: Element | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.tag = self.tag.lower()
        if not self.tag or not self.tag.replace("-", "").isalnum():
            raise DOMError(f"Invalid element name: {self.tag!r}")

        self.attrs = {str(k): str(v) for k, v in self.attrs.items()}
        original_children = list(self.children)
        self.children = []
        for child in original_children:
            self.append(child)

    def append(self, child: Element) -> None:
        if not isinstance(child, Element):
            raise DOMError("Only Element objects can be appended.")
        if child is self or self._contains(child):
            raise DOMError("Appending this element would create a cycle.")
        if child.parent is not None:
            raise DOMError("Remove the child from its current parent first.")
        child.parent = self
        self.children.append(child)

    def remove(self) -> None:
        if self.parent is None:
            raise DOMError("The element has no parent.")
        self.parent.children.remove(self)
        self.parent = None

    def _contains(self, candidate: Element) -> bool:
        current: Element | None = self
        while current is not None:
            if current is candidate:
                return True
            current = current.parent
        return False

    def descendants(self, include_self: bool = False) -> Iterable[Element]:
        if include_self:
            yield self
        for child in self.children:
            yield child
            yield from child.descendants()

    def has_class(self, name: str) -> bool:
        return name in self.attrs.get("class", "").split()

    def matches(self, selector: str) -> bool:
        """Support simple tag, #id, .class, and [attribute] selectors."""
        selector = selector.strip()
        if not selector or any(c in selector for c in " >+~,:"):
            raise DOMError(f"Unsupported selector: {selector!r}")
        if selector.startswith("#"):
            return self.attrs.get("id") == selector[1:]
        if selector.startswith("."):
            return self.has_class(selector[1:])
        if selector.startswith("[") and selector.endswith("]"):
            key = selector[1:-1].strip()
            return bool(key) and key in self.attrs
        return self.tag == selector.lower()

    def query_selector_all(self, selector: str) -> list[Element]:
        return [node for node in self.descendants() if node.matches(selector)]

    def query_selector(self, selector: str) -> Element | None:
        return next(
            (node for node in self.descendants() if node.matches(selector)),
            None,
        )

    def set_attribute(self, name: str, value: str) -> None:
        if not name or any(c.isspace() for c in name):
            raise DOMError("Attribute names must be nonempty and contain no spaces.")
        self.attrs[name] = str(value)

    def get_attribute(self, name: str) -> str | None:
        return self.attrs.get(name)

    def set_text(self, value: str) -> None:
        # Text is stored separately from children to keep this model simple.
        self.text = str(value)

    def to_html(self) -> str:
        attrs = "".join(
            f' {escape(key, quote=True)}="{escape(value, quote=True)}"'
            for key, value in sorted(self.attrs.items())
        )
        content = escape(self.text) + "".join(c.to_html() for c in self.children)
        if self.tag in {"area", "base", "br", "col", "embed", "hr",
                        "img", "input", "link", "meta", "param", "source",
                        "track", "wbr"}:
            if content:
                raise DOMError(f"Void element {self.tag!r} cannot contain content.")
            return f"<{self.tag}{attrs}>"
        return f"<{self.tag}{attrs}>{content}</{self.tag}>"


def build_page() -> Element:
    """Build a small repository dashboard using DOM-like operations."""
    root = Element("main", {"id": "repository", "class": "dashboard"})
    heading = Element("h1", text="Repository Dashboard")
    root.append(heading)

    status = Element("p", {"class": "status", "data-state": "ready"},
                     text="Review queue")
    root.append(status)

    list_element = Element("ul", {"id": "pull-requests"})
    root.append(list_element)

    for number, title in [
        (101, "Validate API input"),
        (102, "Improve database indexes"),
        (103, "Fix navigation tests"),
    ]:
        item = Element("li", {"class": "pull-request", "data-number": str(number)})
        item.append(Element("span", {"class": "title"}, text=title))
        item.append(Element("button", {"type": "button", "class": "review"},
                            text="Review"))
        list_element.append(item)

    return root


def main() -> None:
    root = build_page()

    print("1. Initial tree")
    print(root.to_html())

    # Query selectors operate on descendants, excluding the receiver itself.
    requests = root.query_selector_all(".pull-request")
    print("\n2. Pull request count:", len(requests))

    first_title = root.query_selector("#pull-requests")
    if first_title is None:
        raise DOMError("Pull request list is missing.")

    first_item = first_title.query_selector(".pull-request")
    if first_item is None:
        raise DOMError("No pull request item was found.")

    title = first_item.query_selector(".title")
    if title is None:
        raise DOMError("Pull request title is missing.")

    title.set_text("Validate API input and reject unsafe payloads")
    first_item.set_attribute("data-review-state", "in-review")

    # Create a new node and append it to the existing list.
    list_element = root.query_selector("#pull-requests")
    assert list_element is not None
    new_item = Element(
        "li",
        {"class": "pull-request", "data-number": "104"},
        text="",
    )
    new_item.append(Element("span", {"class": "title"}, text="Add audit logging"))
    list_element.append(new_item)

    # Remove a completed item using its stable data attribute.
    completed = next(
        (node for node in list_element.query_selector_all(".pull-request")
         if node.get_attribute("data-number") == "103"),
        None,
    )
    if completed is not None:
        completed.remove()

    print("\n3. Modified tree")
    print(root.to_html())

    # Verify mutation and traversal behavior.
    assert len(root.query_selector_all(".pull-request")) == 3
    assert root.query_selector('[data-state]') is not None
    assert root.query_selector("#missing") is None
    assert new_item.parent is list_element
    assert completed is None or completed.parent is None

    # Attribute escaping and text escaping prevent markup injection in output.
    unsafe = Element("p", {"title": '"quoted"'}, text="<script>alert(1)</script>")
    rendered = unsafe.to_html()
    assert "&lt;script&gt;" in rendered
    assert "&quot;quoted&quot;" in rendered

    print("\n4. Assertions passed.")
    print("Traversal is O(n); selector evaluation scans descendants.")
    print("This educational model does not implement CSS selector grammar or events.")


if __name__ == "__main__":
    main()
