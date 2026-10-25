"use strict";

/**
 * DOM fundamentals using a browser-native DOM when available.
 * Run in a browser, or with Node.js using the included lightweight model.
 * The model supports basic selectors, traversal, mutations, and safe HTML output.
 */

class DOMError extends Error {}

class MiniElement {
  constructor(tag, attributes = {}, text = "") {
    this.tagName = String(tag).toLowerCase();
    if (!/^[a-z][a-z0-9-]*$/.test(this.tagName)) {
      throw new DOMError(`Invalid element name: ${tag}`);
    }
    this.attributes = new Map(Object.entries(attributes).map(([k, v]) => [k, String(v)]));
    this.textContent = String(text);
    this.children = [];
    this.parentElement = null;
  }

  appendChild(child) {
    if (!(child instanceof MiniElement)) {
      throw new DOMError("Child must be a MiniElement.");
    }
    if (child === this || this.contains(child)) {
      throw new DOMError("Mutation would create a cycle.");
    }
    if (child.parentElement) {
      throw new DOMError("Remove the node from its current parent first.");
    }
    child.parentElement = this;
    this.children.push(child);
    return child;
  }

  contains(candidate) {
    for (let node = candidate; node; node = node.parentElement) {
      if (node === this) return true;
    }
    return false;
  }

  remove() {
    if (!this.parentElement) throw new DOMError("Node has no parent.");
    const parent = this.parentElement;
    parent.children.splice(parent.children.indexOf(this), 1);
    this.parentElement = null;
  }

  setAttribute(name, value) {
    if (!name || /\s/.test(name)) throw new DOMError("Invalid attribute name.");
    this.attributes.set(name, String(value));
  }

  getAttribute(name) {
    return this.attributes.has(name) ? this.attributes.get(name) : null;
  }

  matches(selector) {
    const s = selector.trim();
    if (!s || /[ >+~,:]/.test(s)) throw new DOMError(`Unsupported selector: ${s}`);
    if (s.startsWith("#")) return this.getAttribute("id") === s.slice(1);
    if (s.startsWith(".")) {
      return (this.getAttribute("class") || "").split(/\s+/).includes(s.slice(1));
    }
    const attr = s.match(/^\[([a-zA-Z_:][\w:.-]*)\]$/);
    if (attr) return this.attributes.has(attr[1]);
    if (!/^[a-zA-Z][\w-]*$/.test(s)) throw new DOMError(`Invalid selector: ${s}`);
    return this.tagName === s.toLowerCase();
  }

  *descendants() {
    for (const child of this.children) {
      yield child;
      yield* child.descendants();
    }
  }

  querySelectorAll(selector) {
    return [...this.descendants()].filter(node => node.matches(selector));
  }

  querySelector(selector) {
    for (const node of this.descendants()) {
      if (node.matches(selector)) return node;
    }
    return null;
  }

  toHTML() {
    const escapeHTML = value => String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
    const attrs = [...this.attributes.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => ` ${escapeHTML(k)}="${escapeHTML(v)}"`).join("");
    const voidTags = new Set([
      "area", "base", "br", "col", "embed", "hr", "img", "input",
      "link", "meta", "param", "source", "track", "wbr"
    ]);
    const content = escapeHTML(this.textContent) + this.children.map(c => c.toHTML()).join("");
    if (voidTags.has(this.tagName)) {
      if (content) throw new DOMError(`Void element ${this.tagName} cannot contain content.`);
      return `<${this.tagName}${attrs}>`;
    }
    return `<${this.tagName}${attrs}>${content}</${this.tagName}>`;
  }
}

function createElement(tag, attributes = {}, text = "") {
  return new MiniElement(tag, attributes, text);
}

function buildDashboard() {
  const main = createElement("main", { id: "repository", class: "dashboard" });
  main.appendChild(createElement("h1", {}, "Repository Dashboard"));
  main.appendChild(createElement("p", { class: "status", "data-state": "ready" },
    "Review queue"));

  const list = createElement("ul", { id: "pull-requests" });
  main.appendChild(list);

  const pullRequests = [
    [101, "Validate API input"],
    [102, "Improve database indexes"],
    [103, "Fix navigation tests"]
  ];

  for (const [number, title] of pullRequests) {
    const item = createElement("li", {
      class: "pull-request",
      "data-number": number
    });
    item.appendChild(createElement("span", { class: "title" }, title));
    item.appendChild(createElement("button", { type: "button", class: "review" }, "Review"));
    list.appendChild(item);
  }
  return main;
}

async function main() {
  const root = buildDashboard();
  console.log("1. Initial tree\n", root.toHTML());

  const requests = root.querySelectorAll(".pull-request");
  console.log("2. Pull request count:", requests.length);

  const first = root.querySelector("#pull-requests").querySelector(".pull-request");
  first.querySelector(".title").textContent =
    "Validate API input and reject unsafe payloads";
  first.setAttribute("data-review-state", "in-review");

  // Event-driven mutation: the callback is isolated from rendering logic.
  const addPullRequest = (list, number, title) => {
    if (!Number.isSafeInteger(number) || number <= 0) {
      throw new DOMError("Pull request number must be a positive safe integer.");
    }
    if (!title.trim()) throw new DOMError("Title cannot be empty.");
    if (list.querySelectorAll(".pull-request")
      .some(node => node.getAttribute("data-number") === String(number))) {
      throw new DOMError(`Duplicate pull request number: ${number}`);
    }
    const item = createElement("li", { class: "pull-request", "data-number": number });
    item.appendChild(createElement("span", { class: "title" }, title));
    list.appendChild(item);
    return item;
  };

  const list = root.querySelector("#pull-requests");
  addPullRequest(list, 104, "Add audit logging");

  const completed = list.querySelectorAll(".pull-request")
    .find(node => node.getAttribute("data-number") === "103");
  if (completed) completed.remove();

  // Simulate an asynchronous update, as a real interface might receive from an API.
  const refreshStatus = async () => {
    await Promise.resolve();
    const status = root.querySelector(".status");
    if (!status) throw new DOMError("Status element is missing.");
    status.textContent = "Queue refreshed";
    status.setAttribute("data-state", "updated");
    return status.textContent;
  };

  console.log("3. Status:", await refreshStatus());
  console.log("4. Modified tree\n", root.toHTML());

  if (root.querySelectorAll(".pull-request").length !== 3) {
    throw new DOMError("Unexpected pull request count.");
  }
  if (root.querySelector("#missing") !== null) {
    throw new DOMError("Missing selector should return null.");
  }

  try {
    addPullRequest(list, 104, "Duplicate");
    throw new DOMError("Duplicate validation failed.");
  } catch (error) {
    if (!(error instanceof DOMError) || !error.message.includes("Duplicate")) throw error;
    console.log("5. Expected validation failure:", error.message);
  }

  console.log("Assertions passed.");
  console.log("Selector scans are O(n); repeated scans can be expensive on large trees.");
  console.log("Use textContent for untrusted text, not innerHTML.");
}

main().catch(error => {
  console.error("DOM workflow failed:", error.message);
  process.exitCode = 1;
});
