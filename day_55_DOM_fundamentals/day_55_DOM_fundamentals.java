import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * Enterprise dashboard DOM model with explicit validation and state transitions.
 * Compile: javac Main.java
 * Run: java Main
 */
public class Main {
    private static final Pattern VALID_TAG = Pattern.compile("[a-z][a-z0-9-]*");

    static final class DOMException extends RuntimeException {
        DOMException(String message) {
            super(message);
        }
    }

    enum ReviewState {
        OPEN, IN_REVIEW, APPROVED, MERGED
    }

    record PullRequest(int number, String title) {
        PullRequest {
            if (number <= 0) throw new IllegalArgumentException("Number must be positive.");
            if (title == null || title.isBlank()) {
                throw new IllegalArgumentException("Title must not be blank.");
            }
        }
    }

    static final class Element {
        private final String tagName;
        private final Map<String, String> attributes = new LinkedHashMap<>();
        private final List<Element> children = new ArrayList<>();
        private String textContent;
        private Element parent;

        Element(String tagName, String textContent) {
            Objects.requireNonNull(tagName, "tagName");
            String normalized = tagName.toLowerCase();
            if (!VALID_TAG.matcher(normalized).matches()) {
                throw new DOMException("Invalid tag name: " + tagName);
            }
            this.tagName = normalized;
            this.textContent = Objects.requireNonNull(textContent, "textContent");
        }

        Element setAttribute(String name, String value) {
            if (name == null || name.isBlank() || name.chars().anyMatch(Character::isWhitespace)) {
                throw new DOMException("Invalid attribute name.");
            }
            attributes.put(name, Objects.requireNonNull(value, "value"));
            return this;
        }

        String getAttribute(String name) {
            return attributes.get(name);
        }

        String textContent() {
            return textContent;
        }

        void setTextContent(String text) {
            textContent = Objects.requireNonNull(text, "text");
        }

        Element appendChild(Element child) {
            Objects.requireNonNull(child, "child");
            if (child == this || child.contains(this)) {
                throw new DOMException("Mutation would create a cycle.");
            }
            if (child.parent != null) {
                throw new DOMException("Child already has a parent.");
            }
            child.parent = this;
            children.add(child);
            return child;
        }

        private boolean contains(Element candidate) {
            if (this == candidate) return true;
            return children.stream().anyMatch(child -> child.contains(candidate));
        }

        void remove() {
            if (parent == null) throw new DOMException("Root element has no parent.");
            if (!parent.children.remove(this)) {
                throw new DOMException("Parent-child relationship is inconsistent.");
            }
            parent = null;
        }

        private boolean matches(String selector) {
            if (selector.startsWith("#")) {
                return selector.length() > 1
                    && selector.substring(1).equals(attributes.get("id"));
            }
            if (selector.startsWith(".")) {
                String classes = attributes.getOrDefault("class", "");
                return selector.length() > 1
                    && List.of(classes.split("\\s+")).contains(selector.substring(1));
            }
            if (selector.startsWith("[") && selector.endsWith("]")) {
                String key = selector.substring(1, selector.length() - 1);
                return !key.isBlank() && attributes.containsKey(key);
            }
            if (!VALID_TAG.matcher(selector.toLowerCase()).matches()) {
                throw new DOMException("Unsupported selector: " + selector);
            }
            return tagName.equals(selector.toLowerCase());
        }

        List<Element> querySelectorAll(String selector) {
            Objects.requireNonNull(selector, "selector");
            if (selector.isBlank() || selector.chars().anyMatch(c -> " >+~,:".indexOf(c) >= 0)) {
                throw new DOMException("Only simple selectors are supported.");
            }
            List<Element> results = new ArrayList<>();
            collect(selector, results);
            return Collections.unmodifiableList(results);
        }

        private void collect(String selector, List<Element> results) {
            for (Element child : children) {
                if (child.matches(selector)) results.add(child);
                child.collect(selector, results);
            }
        }

        Optional<Element> querySelector(String selector) {
            return querySelectorAll(selector).stream().findFirst();
        }

        private static String escape(String value, boolean attribute) {
            String result = value.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;");
            return attribute
                ? result.replace("\"", "&quot;").replace("'", "&#39;")
                : result;
        }

        String toHTML() {
            String attrs = attributes.entrySet().stream()
                .map(e -> " " + escape(e.getKey(), true) + "=\""
                    + escape(e.getValue(), true) + "\"")
                .collect(Collectors.joining());
            String content = escape(textContent, false)
                + children.stream().map(Element::toHTML).collect(Collectors.joining());
            if (List.of("area", "base", "br", "col", "embed", "hr", "img",
                    "input", "link", "meta", "param", "source", "track", "wbr")
                    .contains(tagName)) {
                if (!content.isEmpty()) throw new DOMException("Void element has content.");
                return "<" + tagName + attrs + ">";
            }
            return "<" + tagName + attrs + ">" + content + "</" + tagName + ">";
        }
    }

    static final class DashboardService {
        private final Element root = new Element("main", "")
            .setAttribute("id", "repository")
            .setAttribute("class", "dashboard");
        private final Map<Integer, ReviewState> states = new LinkedHashMap<>();

        DashboardService() {
            root.appendChild(new Element("h1", "Repository Dashboard"));
            root.appendChild(new Element("p", "Review queue")
                .setAttribute("class", "status")
                .setAttribute("data-state", "ready"));

            Element list = root.appendChild(new Element("ul", "").setAttribute("id", "pull-requests"));
            addPullRequest(new PullRequest(101, "Validate API input"));
            addPullRequest(new PullRequest(102, "Improve database indexes"));
            addPullRequest(new PullRequest(103, "Fix navigation tests"));
        }

        Element document() {
            return root;
        }

        void addPullRequest(PullRequest request) {
            Objects.requireNonNull(request, "request");
            if (states.containsKey(request.number())) {
                throw new DOMException("Duplicate pull request number: " + request.number());
            }
            Element list = root.querySelector("#pull-requests")
                .orElseThrow(() -> new DOMException("List is missing."));
            Element item = list.appendChild(new Element("li", "")
                .setAttribute("class", "pull-request")
                .setAttribute("data-number", Integer.toString(request.number())));
            item.appendChild(new Element("span", request.title()).setAttribute("class", "title"));
            states.put(request.number(), ReviewState.OPEN);
        }

        void transition(int number, ReviewState next) {
            ReviewState current = states.get(number);
            if (current == null) throw new DOMException("Unknown pull request: " + number);

            boolean allowed = switch (current) {
                case OPEN -> next == ReviewState.IN_REVIEW;
                case IN_REVIEW -> next == ReviewState.APPROVED || next == ReviewState.OPEN;
                case APPROVED -> next == ReviewState.MERGED || next == ReviewState.IN_REVIEW;
                case MERGED -> false;
            };
            if (!allowed) {
                throw new DOMException("Invalid transition: " + current + " -> " + next);
            }
            states.put(number, next);
        }

        void removePullRequest(int number) {
            Element list = root.querySelector("#pull-requests")
                .orElseThrow(() -> new DOMException("List is missing."));
            Element item = list.querySelectorAll(".pull-request").stream()
                .filter(e -> Integer.toString(number).equals(e.getAttribute("data-number")))
                .findFirst()
                .orElseThrow(() -> new DOMException("Pull request not found."));
            if (states.get(number) == ReviewState.MERGED) {
                throw new DOMException("Merged pull requests cannot be removed from the dashboard.");
            }
            item.remove();
            states.remove(number);
        }

        ReviewState state(int number) {
            ReviewState state = states.get(number);
            if (state == null) throw new DOMException("Unknown pull request.");
            return state;
        }
    }

    public static void main(String[] args) {
        try {
            DashboardService service = new DashboardService();
            Element root = service.document();

            System.out.println("Initial tree:\n" + root.toHTML());
            System.out.println("Initial pull requests: " + root.querySelectorAll(".pull-request").size());

            Element first = root.querySelector("#pull-requests")
                .flatMap(list -> list.querySelector(".pull-request"))
                .orElseThrow(() -> new DOMException("First item missing."));

            first.querySelector(".title").orElseThrow().setTextContent(
                "Validate API input and reject unsafe payloads");
            first.setAttribute("data-review-state", "in-review");

            service.transition(101, ReviewState.IN_REVIEW);
            service.transition(101, ReviewState.APPROVED);

            service.addPullRequest(new PullRequest(104, "Add audit logging"));
            service.removePullRequest(103);

            System.out.println("\nUpdated tree:\n" + root.toHTML());
            System.out.println("Request 101 state: " + service.state(101));
            System.out.println("Final pull requests: " + root.querySelectorAll(".pull-request").size());

            if (root.querySelector("#missing").isPresent()) {
                throw new DOMException("Missing element unexpectedly found.");
            }

            try {
                service.transition(101, ReviewState.OPEN);
                throw new DOMException("Invalid state transition unexpectedly succeeded.");
            } catch (DOMException expected) {
                if (expected.getMessage().contains("unexpectedly succeeded")) throw expected;
                System.out.println("Expected transition failure: " + expected.getMessage());
            }

            System.out.println("All assertions passed.");
            System.out.println("Selector scans are O(n); repeated scans can dominate large trees.");
        } catch (RuntimeException error) {
            System.err.println("Dashboard failure: " + error.getMessage());
            System.exit(1);
        }
    }
}
