import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;


/*
 * React Introduction
 *
 * Enterprise-oriented component architecture and rendering model.
 *
 * Covers:
 * - Component contracts
 * - Immutable virtual nodes
 * - Component registration
 * - Props
 * - Component composition
 * - State transitions
 * - Rendering
 * - Virtual DOM reconciliation
 * - Validation
 * - Exception handling
 * - Unit-style verification
 */

public class ReactIntroduction {

    // -----------------------------------------------------
    // Exceptions
    // -----------------------------------------------------

    static class ComponentException extends RuntimeException {
        ComponentException(String message) {
            super(message);
        }
    }

    static class RenderingException extends RuntimeException {
        RenderingException(String message) {
            super(message);
        }
    }

    static class StateException extends RuntimeException {
        StateException(String message) {
            super(message);
        }
    }


    // -----------------------------------------------------
    // Virtual DOM types
    // -----------------------------------------------------

    enum NodeType {
        ELEMENT,
        TEXT,
        FRAGMENT
    }

    enum PatchType {
        REPLACE,
        UPDATE_TEXT,
        UPDATE_PROPS,
        INSERT,
        REMOVE
    }

    record Patch(
        PatchType type,
        String path,
        String description
    ) {}


    // -----------------------------------------------------
    // Immutable virtual DOM node
    // -----------------------------------------------------

    static final class VNode {

        private final NodeType type;
        private final String tag;
        private final String text;
        private final Map<String, String> props;
        private final List<VNode> children;

        private VNode(
            NodeType type,
            String tag,
            String text,
            Map<String, String> props,
            List<VNode> children
        ) {
            this.type = Objects.requireNonNull(type);
            this.tag = tag;
            this.text = text;

            this.props = Collections.unmodifiableMap(
                new LinkedHashMap<>(props)
            );

            this.children = List.copyOf(children);
        }

        static VNode text(String value) {
            return new VNode(
                NodeType.TEXT,
                null,
                Objects.requireNonNull(value),
                Map.of(),
                List.of()
            );
        }

        static VNode element(
            String tag,
            Map<String, String> props,
            List<VNode> children
        ) {
            validateTag(tag);

            return new VNode(
                NodeType.ELEMENT,
                tag,
                null,
                props,
                children
            );
        }

        static VNode fragment(List<VNode> children) {
            return new VNode(
                NodeType.FRAGMENT,
                null,
                null,
                Map.of(),
                children
            );
        }

        NodeType type() {
            return type;
        }

        String tag() {
            return tag;
        }

        String text() {
            return text;
        }

        Map<String, String> props() {
            return props;
        }

        List<VNode> children() {
            return children;
        }

        private static void validateTag(String tag) {
            if (tag == null ||
                !tag.matches("[A-Za-z][A-Za-z0-9-]*")) {
                throw new ComponentException(
                    "Invalid element tag: " + tag
                );
            }
        }
    }


    // -----------------------------------------------------
    // Component interface and registry
    // -----------------------------------------------------

    @FunctionalInterface
    interface Component {
        VNode render(Map<String, String> props);
    }

    static final class ComponentRegistry {

        private final Map<String, Component> components =
            new HashMap<>();

        void register(String name, Component component) {
            if (name == null || name.isBlank()) {
                throw new ComponentException(
                    "Component name cannot be empty."
                );
            }

            Objects.requireNonNull(component);

            if (components.putIfAbsent(name, component) != null) {
                throw new ComponentException(
                    "Duplicate component: " + name
                );
            }
        }

        VNode render(
            String name,
            Map<String, String> props
        ) {
            Component component = components.get(name);

            if (component == null) {
                throw new ComponentException(
                    "Unknown component: " + name
                );
            }

            VNode result = component.render(
                Collections.unmodifiableMap(
                    new HashMap<>(props)
                )
            );

            if (result == null) {
                throw new ComponentException(
                    "Component returned null."
                );
            }

            return result;
        }
    }


    // -----------------------------------------------------
    // HTML renderer
    // -----------------------------------------------------

    static final Set<String> VOID_ELEMENTS = Set.of(
        "area", "base", "br", "col", "embed",
        "hr", "img", "input", "link", "meta",
        "param", "source", "track", "wbr"
    );

    static String escapeHtml(String input) {
        return input
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\"", "&quot;")
            .replace("'", "&#39;");
    }

    static String renderHtml(VNode node) {
        if (node == null) {
            throw new RenderingException(
                "Cannot render a null node."
            );
        }

        if (node.type() == NodeType.TEXT) {
            return escapeHtml(node.text());
        }

        if (node.type() == NodeType.FRAGMENT) {
            return node.children()
                .stream()
                .map(ReactIntroduction::renderHtml)
                .collect(Collectors.joining());
        }

        StringBuilder output = new StringBuilder();

        output.append("<").append(node.tag());

        node.props().entrySet().stream()
            .sorted(Map.Entry.comparingByKey())
            .forEach(entry -> {
                String name = entry.getKey();

                if (name.matches("[Oo][Nn].*")) {
                    return;
                }

                if (!name.matches("[A-Za-z_:][A-Za-z0-9_:.-]*")) {
                    throw new RenderingException(
                        "Invalid attribute: " + name
                    );
                }

                output.append(" ")
                    .append(name)
                    .append("=\"")
                    .append(escapeHtml(entry.getValue()))
                    .append("\"");
            });

        if (VOID_ELEMENTS.contains(node.tag())) {
            if (!node.children().isEmpty()) {
                throw new RenderingException(
                    "Void elements cannot contain children."
                );
            }

            return output.append("/>").toString();
        }

        output.append(">");

        for (VNode child : node.children()) {
            output.append(renderHtml(child));
        }

        output.append("</")
            .append(node.tag())
            .append(">");

        return output.toString();
    }


    // -----------------------------------------------------
    // Component state management
    // -----------------------------------------------------

    static final class CounterState {

        private int count;
        private long version;

        CounterState(int initialValue) {
            if (initialValue < 0) {
                throw new StateException(
                    "Initial count cannot be negative."
                );
            }

            count = initialValue;
        }

        synchronized int getCount() {
            return count;
        }

        synchronized long getVersion() {
            return version;
        }

        synchronized void increment() {
            if (count == Integer.MAX_VALUE) {
                throw new StateException(
                    "Counter limit reached."
                );
            }

            count++;
            version++;
        }

        synchronized void decrement() {
            if (count == 0) {
                throw new StateException(
                    "Counter cannot become negative."
                );
            }

            count--;
            version++;
        }

        synchronized void reset() {
            if (count != 0) {
                count = 0;
                version++;
            }
        }
    }


    // -----------------------------------------------------
    // Component definitions
    // -----------------------------------------------------

    static void registerComponents(
        ComponentRegistry registry
    ) {

        registry.register(
            "Header",
            props -> {
                String title = props.getOrDefault(
                    "title",
                    "React Introduction"
                );

                return VNode.element(
                    "header",
                    Map.of("class", "application-header"),
                    List.of(
                        VNode.element(
                            "h1",
                            Map.of(),
                            List.of(VNode.text(title))
                        )
                    )
                );
            }
        );

        registry.register(
            "Card",
            props -> {
                String title = props.get("title");
                String description = props.get("description");

                if (title == null || description == null) {
                    throw new ComponentException(
                        "Card requires title and description."
                    );
                }

                return VNode.element(
                    "article",
                    Map.of("class", "concept-card"),
                    List.of(
                        VNode.element(
                            "h2",
                            Map.of(),
                            List.of(VNode.text(title))
                        ),
                        VNode.element(
                            "p",
                            Map.of(),
                            List.of(VNode.text(description))
                        )
                    )
                );
            }
        );

        registry.register(
            "Counter",
            props -> {
                String value = props.get("value");

                if (value == null) {
                    throw new ComponentException(
                        "Counter requires a value."
                    );
                }

                return VNode.element(
                    "section",
                    Map.of("class", "counter"),
                    List.of(
                        VNode.element(
                            "p",
                            Map.of("aria-live", "polite"),
                            List.of(
                                VNode.text("Current count: " + value)
                            )
                        )
                    )
                );
            }
        );
    }


    // -----------------------------------------------------
    // Application composition
    // -----------------------------------------------------

    static VNode buildApplication(
        ComponentRegistry registry,
        int count
    ) {
        VNode header = registry.render(
            "Header",
            Map.of("title", "React Introduction")
        );

        List<Map<String, String>> concepts = List.of(
            Map.of(
                "title", "Component Architecture",
                "description",
                "Reusable interface units arranged in a component tree."
            ),
            Map.of(
                "title", "JSX",
                "description",
                "JavaScript syntax for describing UI structures."
            ),
            Map.of(
                "title", "Virtual DOM",
                "description",
                "An in-memory representation of the rendered interface."
            ),
            Map.of(
                "title", "Rendering",
                "description",
                "Updating browser-visible elements from component output."
            )
        );

        List<VNode> cards = concepts.stream()
            .map(props -> registry.render("Card", props))
            .toList();

        VNode cardContainer = VNode.element(
            "section",
            Map.of("class", "card-grid"),
            cards
        );

        VNode counter = registry.render(
            "Counter",
            Map.of("value", Integer.toString(count))
        );

        return VNode.element(
            "main",
            Map.of("class", "application"),
            List.of(header, cardContainer, counter)
        );
    }


    // -----------------------------------------------------
    // Virtual DOM reconciliation
    // -----------------------------------------------------

    static void reconcile(
        VNode oldNode,
        VNode newNode,
        String path,
        List<Patch> patches
    ) {
        if (oldNode == null || newNode == null) {
            patches.add(
                new Patch(
                    PatchType.REPLACE,
                    path,
                    "Replace missing node"
                )
            );
            return;
        }

        if (oldNode.type() != newNode.type()) {
            patches.add(
                new Patch(
                    PatchType.REPLACE,
                    path,
                    "Node type changed"
                )
            );
            return;
        }

        if (oldNode.type() == NodeType.TEXT) {
            if (!Objects.equals(
                oldNode.text(),
                newNode.text()
            )) {
                patches.add(
                    new Patch(
                        PatchType.UPDATE_TEXT,
                        path,
                        "Text content changed"
                    )
                );
            }

            return;
        }

        if (!Objects.equals(oldNode.tag(), newNode.tag())) {
            patches.add(
                new Patch(
                    PatchType.REPLACE,
                    path,
                    "Element tag changed"
                )
            );

            return;
        }

        if (!oldNode.props().equals(newNode.props())) {
            patches.add(
                new Patch(
                    PatchType.UPDATE_PROPS,
                    path,
                    "Properties changed"
                )
            );
        }

        int maximum = Math.max(
            oldNode.children().size(),
            newNode.children().size()
        );

        for (int i = 0; i < maximum; i++) {
            String childPath = path + "." + i;

            if (i >= oldNode.children().size()) {
                patches.add(
                    new Patch(
                        PatchType.INSERT,
                        childPath,
                        "Insert child"
                    )
                );
            } else if (i >= newNode.children().size()) {
                patches.add(
                    new Patch(
                        PatchType.REMOVE,
                        childPath,
                        "Remove child"
                    )
                );
            } else {
                reconcile(
                    oldNode.children().get(i),
                    newNode.children().get(i),
                    childPath,
                    patches
                );
            }
        }
    }


    // -----------------------------------------------------
    // Tree inspection
    // -----------------------------------------------------

    static int countNodes(VNode node) {
        return 1 + node.children()
            .stream()
            .mapToInt(ReactIntroduction::countNodes)
            .sum();
    }


    // -----------------------------------------------------
    // Tests
    // -----------------------------------------------------

    static void runTests() {

        String escaped = renderHtml(
            VNode.text("<script>alert(1)</script>")
        );

        if (escaped.contains("<script>")) {
            throw new AssertionError(
                "HTML escaping failed."
            );
        }

        CounterState state = new CounterState(0);

        state.increment();

        if (state.getCount() != 1) {
            throw new AssertionError(
                "Increment failed."
            );
        }

        state.decrement();

        if (state.getCount() != 0) {
            throw new AssertionError(
                "Decrement failed."
            );
        }

        boolean underflowDetected = false;

        try {
            state.decrement();
        } catch (StateException exception) {
            underflowDetected = true;
        }

        if (!underflowDetected) {
            throw new AssertionError(
                "Underflow validation failed."
            );
        }

        VNode oldNode = VNode.element(
            "p",
            Map.of(),
            List.of(VNode.text("Old"))
        );

        VNode newNode = VNode.element(
            "p",
            Map.of(),
            List.of(VNode.text("New"))
        );

        List<Patch> patches = new ArrayList<>();

        reconcile(oldNode, newNode, "root", patches);

        if (patches.size() != 1 ||
            patches.get(0).type() != PatchType.UPDATE_TEXT) {
            throw new AssertionError(
                "Virtual DOM reconciliation failed."
            );
        }

        System.out.println("All Java tests passed.");
    }


    // -----------------------------------------------------
    // Main
    // -----------------------------------------------------

    public static void main(String[] args) {

        try {
            ComponentRegistry registry =
                new ComponentRegistry();

            registerComponents(registry);

            CounterState state = new CounterState(0);

            VNode initialTree = buildApplication(
                registry,
                state.getCount()
            );

            state.increment();

            VNode updatedTree = buildApplication(
                registry,
                state.getCount()
            );

            System.out.println("REACT INTRODUCTION");
            System.out.println("==================");

            System.out.println("\nRendered HTML:\n");
            System.out.println(renderHtml(initialTree));

            System.out.println(
                "\nVirtual DOM node count: " +
                countNodes(initialTree)
            );

            List<Patch> patches = new ArrayList<>();

            reconcile(
                initialTree,
                updatedTree,
                "root",
                patches
            );

            System.out.println("\nReconciliation:");

            patches.forEach(patch ->
                System.out.println(
                    patch.description() +
                    " at " +
                    patch.path()
                )
            );

            runTests();

        } catch (Exception exception) {
            System.err.println(
                "Application failure: " +
                exception.getMessage()
            );

            System.exit(1);
        }
    }
}
