import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

/*
 * Enterprise React Component Architecture Model.
 *
 * Covers:
 * - Functional component contracts
 * - Immutable props
 * - Reusable component definitions
 * - Composition and nested component trees
 * - Default and required properties
 * - Type-safe validation
 * - Component lifecycle simulation
 * - Conditional rendering
 * - State management
 * - Component registry and policy enforcement
 * - Error handling and testing
 */

public class ReactComponentArchitecture {

    enum PropType {
        STRING,
        NUMBER,
        BOOLEAN,
        ARRAY,
        OBJECT,
        ANY
    }

    enum ComponentStatus {
        REGISTERED,
        ACTIVE,
        DEPRECATED
    }

    static class ComponentException extends RuntimeException {
        ComponentException(String message) {
            super(message);
        }
    }

    static class PropValidationException extends ComponentException {
        PropValidationException(String message) {
            super(message);
        }
    }

    record PropDefinition(
        PropType type,
        boolean required,
        Optional<Object> defaultValue
    ) {
        PropDefinition {
            Objects.requireNonNull(type);
            Objects.requireNonNull(defaultValue);

            if (required && defaultValue.isPresent()) {
                throw new IllegalArgumentException(
                    "Required properties cannot have defaults"
                );
            }

            defaultValue.ifPresent(value -> {
                if (!matches(value, type)) {
                    throw new IllegalArgumentException(
                        "Default value does not match " + type
                    );
                }
            });
        }

        static PropDefinition required(PropType type) {
            return new PropDefinition(type, true, Optional.empty());
        }

        static PropDefinition optional(
            PropType type,
            Object defaultValue
        ) {
            return new PropDefinition(
                type,
                false,
                Optional.ofNullable(defaultValue)
            );
        }

        private static boolean matches(Object value, PropType type) {
            return switch (type) {
                case STRING -> value instanceof String;
                case NUMBER -> value instanceof Number;
                case BOOLEAN -> value instanceof Boolean;
                case ARRAY -> value instanceof List<?>;
                case OBJECT -> value instanceof Map<?, ?>;
                case ANY -> true;
            };
        }
    }


    record ComponentNode(
        String componentName,
        String nodeId,
        Map<String, Object> props,
        List<ComponentNode> children
    ) {
        ComponentNode {
            if (componentName == null || componentName.isBlank()) {
                throw new IllegalArgumentException(
                    "Component name is required"
                );
            }

            if (nodeId == null || nodeId.isBlank()) {
                throw new IllegalArgumentException("Node ID is required");
            }

            props = Collections.unmodifiableMap(
                new LinkedHashMap<>(props)
            );

            children = List.copyOf(children);
        }
    }


    record RenderedComponent(
        String componentName,
        String nodeId,
        Map<String, Object> validatedProps,
        String output,
        List<RenderedComponent> children
    ) {
        RenderedComponent {
            validatedProps = Map.copyOf(validatedProps);
            children = List.copyOf(children);
        }
    }


    static class ComponentDefinition {
        private final String name;
        private final String description;
        private final Map<String, PropDefinition> schema;
        private final boolean acceptsChildren;
        private ComponentStatus status;

        ComponentDefinition(
            String name,
            String description,
            Map<String, PropDefinition> schema,
            boolean acceptsChildren
        ) {
            if (name == null || !name.matches("[A-Z][A-Za-z0-9]*")) {
                throw new IllegalArgumentException(
                    "Invalid component name"
                );
            }

            this.name = name;
            this.description = Objects.requireNonNull(description);
            this.schema = Map.copyOf(schema);
            this.acceptsChildren = acceptsChildren;
            this.status = ComponentStatus.REGISTERED;
        }

        String name() {
            return name;
        }

        String description() {
            return description;
        }

        Map<String, PropDefinition> schema() {
            return schema;
        }

        boolean acceptsChildren() {
            return acceptsChildren;
        }

        ComponentStatus status() {
            return status;
        }

        void activate() {
            if (status == ComponentStatus.DEPRECATED) {
                throw new ComponentException(
                    "Deprecated components cannot be activated"
                );
            }

            status = ComponentStatus.ACTIVE;
        }

        void deprecate() {
            status = ComponentStatus.DEPRECATED;
        }
    }


    interface ComponentRenderer {
        String render(
            Map<String, Object> props,
            List<RenderedComponent> children
        );
    }


    static class ComponentRegistry {
        private final Map<String, ComponentDefinition> definitions =
            new LinkedHashMap<>();

        private final Map<String, ComponentRenderer> renderers =
            new HashMap<>();

        void register(
            ComponentDefinition definition,
            ComponentRenderer renderer
        ) {
            Objects.requireNonNull(definition);
            Objects.requireNonNull(renderer);

            if (definitions.containsKey(definition.name())) {
                throw new ComponentException(
                    "Duplicate component: " + definition.name()
                );
            }

            definitions.put(definition.name(), definition);
            renderers.put(definition.name(), renderer);
        }

        ComponentDefinition get(String name) {
            ComponentDefinition definition = definitions.get(name);

            if (definition == null) {
                throw new ComponentException(
                    "Unknown component: " + name
                );
            }

            return definition;
        }

        ComponentRenderer renderer(String name) {
            ComponentRenderer renderer = renderers.get(name);

            if (renderer == null) {
                throw new ComponentException(
                    "Renderer unavailable: " + name
                );
            }

            return renderer;
        }

        List<String> names() {
            return definitions.keySet()
                .stream()
                .sorted()
                .toList();
        }
    }


    static class PropValidator {

        Map<String, Object> validate(
            ComponentDefinition definition,
            Map<String, Object> supplied
        ) {
            Map<String, Object> validated = new LinkedHashMap<>();

            for (String property : supplied.keySet()) {
                if (!definition.schema().containsKey(property)) {
                    throw new PropValidationException(
                        definition.name() +
                        ": unknown property " + property
                    );
                }
            }

            for (var entry : definition.schema().entrySet()) {
                String name = entry.getKey();
                PropDefinition schema = entry.getValue();

                Object value = supplied.get(name);

                if (value == null) {
                    if (supplied.containsKey(name)) {
                        throw new PropValidationException(
                            name + " cannot be null"
                        );
                    }

                    if (schema.defaultValue().isPresent()) {
                        value = schema.defaultValue().get();
                    } else if (schema.required()) {
                        throw new PropValidationException(
                            definition.name() +
                            ": missing required property " + name
                        );
                    } else {
                        continue;
                    }
                }

                if (!matches(value, schema.type())) {
                    throw new PropValidationException(
                        definition.name() + "." + name +
                        " expects " + schema.type()
                    );
                }

                validated.put(name, value);
            }

            return Map.copyOf(validated);
        }

        private boolean matches(Object value, PropType type) {
            return switch (type) {
                case STRING -> value instanceof String;
                case NUMBER -> value instanceof Number;
                case BOOLEAN -> value instanceof Boolean;
                case ARRAY -> value instanceof List<?>;
                case OBJECT -> value instanceof Map<?, ?>;
                case ANY -> true;
            };
        }
    }


    static class ComponentService {
        private final ComponentRegistry registry;
        private final PropValidator validator;

        ComponentService(ComponentRegistry registry) {
            this.registry = registry;
            this.validator = new PropValidator();
        }

        RenderedComponent render(ComponentNode node) {
            return renderInternal(node, new HashSet<>());
        }

        private RenderedComponent renderInternal(
            ComponentNode node,
            Set<String> ancestors
        ) {
            String identity = node.nodeId();

            if (!ancestors.add(identity)) {
                throw new ComponentException(
                    "Circular component composition: " + identity
                );
            }

            try {
                ComponentDefinition definition =
                    registry.get(node.componentName());

                if (definition.status() != ComponentStatus.ACTIVE) {
                    throw new ComponentException(
                        definition.name() + " is not active"
                    );
                }

                if (!definition.acceptsChildren()
                    && !node.children().isEmpty()) {
                    throw new ComponentException(
                        definition.name() + " does not accept children"
                    );
                }

                Map<String, Object> props =
                    validator.validate(definition, node.props());

                List<RenderedComponent> children =
                    new ArrayList<>();

                for (ComponentNode child : node.children()) {
                    children.add(
                        renderInternal(child, ancestors)
                    );
                }

                String output = registry.renderer(
                    definition.name()
                ).render(props, children);

                return new RenderedComponent(
                    definition.name(),
                    node.nodeId(),
                    props,
                    output,
                    children
                );

            } finally {
                ancestors.remove(identity);
            }
        }
    }


    static ComponentRegistry buildRegistry() {
        ComponentRegistry registry = new ComponentRegistry();

        registry.register(
            new ComponentDefinition(
                "Text",
                "Reusable text element",
                Map.of(
                    "content",
                    PropDefinition.required(PropType.STRING),
                    "tone",
                    PropDefinition.optional(PropType.STRING, "normal")
                ),
                false
            ),
            (props, children) ->
                "Text(" + props.get("content") + ")"
        );

        registry.register(
            new ComponentDefinition(
                "Button",
                "Reusable action button",
                Map.of(
                    "label",
                    PropDefinition.required(PropType.STRING),
                    "variant",
                    PropDefinition.optional(PropType.STRING, "primary"),
                    "disabled",
                    PropDefinition.optional(PropType.BOOLEAN, false)
                ),
                false
            ),
            (props, children) ->
                "Button[label=" + props.get("label") +
                ", variant=" + props.get("variant") +
                ", disabled=" + props.get("disabled") + "]"
        );

        registry.register(
            new ComponentDefinition(
                "Badge",
                "Status indicator",
                Map.of(
                    "label",
                    PropDefinition.required(PropType.STRING),
                    "status",
                    PropDefinition.optional(PropType.STRING, "neutral")
                ),
                false
            ),
            (props, children) ->
                "Badge[" + props.get("label") +
                ", " + props.get("status") + "]"
        );

        registry.register(
            new ComponentDefinition(
                "Card",
                "Composable content container",
                Map.of(
                    "title",
                    PropDefinition.required(PropType.STRING),
                    "description",
                    PropDefinition.optional(PropType.STRING, "")
                ),
                true
            ),
            (props, children) ->
                "Card[" + props.get("title") +
                ", children=" + children.size() + "]"
        );

        registry.register(
            new ComponentDefinition(
                "Conditional",
                "Conditional content wrapper",
                Map.of(
                    "visible",
                    PropDefinition.required(PropType.BOOLEAN)
                ),
                true
            ),
            (props, children) ->
                Boolean.TRUE.equals(props.get("visible"))
                    ? "Visible(" + children.size() + " children)"
                    : "Hidden"
        );

        for (String name : registry.names()) {
            registry.get(name).activate();
        }

        return registry;
    }


    static ComponentNode buildDashboard() {
        ComponentNode text = new ComponentNode(
            "Text",
            "description",
            Map.of(
                "content", "Operational project dashboard",
                "tone", "muted"
            ),
            List.of()
        );

        ComponentNode badge = new ComponentNode(
            "Badge",
            "project-status",
            Map.of(
                "label", "Active",
                "status", "success"
            ),
            List.of()
        );

        ComponentNode button = new ComponentNode(
            "Button",
            "project-action",
            Map.of("label", "Open Projects"),
            List.of()
        );

        ComponentNode conditional = new ComponentNode(
            "Conditional",
            "additional-information",
            Map.of("visible", true),
            List.of(
                new ComponentNode(
                    "Text",
                    "additional-text",
                    Map.of("content", "Additional project details"),
                    List.of()
                )
            )
        );

        return new ComponentNode(
            "Card",
            "dashboard",
            Map.of(
                "title", "Project Dashboard",
                "description", "Enterprise component composition"
            ),
            List.of(text, badge, button, conditional)
        );
    }


    static void printTree(
        RenderedComponent component,
        int depth
    ) {
        System.out.println(
            "  ".repeat(depth) +
            component.componentName() +
            " [" + component.nodeId() + "] " +
            component.output()
        );

        component.children().forEach(
            child -> printTree(child, depth + 1)
        );
    }


    static void runTests(ComponentService service) {
        ComponentNode validButton = new ComponentNode(
            "Button",
            "test-button",
            Map.of("label", "Save"),
            List.of()
        );

        RenderedComponent result = service.render(validButton);

        if (!result.validatedProps().get("disabled").equals(false)) {
            throw new AssertionError("Default property test failed");
        }

        // Missing required property.
        expectFailure(
            () -> service.render(new ComponentNode(
                "Button", "missing", Map.of(), List.of()
            ))
        );

        // Incorrect property type.
        expectFailure(
            () -> service.render(new ComponentNode(
                "Button",
                "wrong-type",
                Map.of("label", 42),
                List.of()
            ))
        );

        // Unknown property.
        expectFailure(
            () -> service.render(new ComponentNode(
                "Text",
                "unknown",
                Map.of(
                    "content", "Hello",
                    "unexpected", true
                ),
                List.of()
            ))
        );

        // Non-composable component.
        expectFailure(
            () -> service.render(new ComponentNode(
                "Badge",
                "invalid-child",
                Map.of("label", "Ready"),
                List.of(validButton)
            ))
        );

        // Duplicate node identity on the active composition path.
        ComponentNode circular = new ComponentNode(
            "Card",
            "same-id",
            Map.of("title", "Parent"),
            List.of(
                new ComponentNode(
                    "Card",
                    "same-id",
                    Map.of("title", "Child"),
                    List.of()
                )
            )
        );

        expectFailure(() -> service.render(circular));

        System.out.println("All Java component tests passed.");
    }


    static void expectFailure(Runnable action) {
        try {
            action.run();
        } catch (ComponentException expected) {
            return;
        }

        throw new AssertionError("Expected component failure");
    }


    public static void main(String[] args) {
        try {
            ComponentRegistry registry = buildRegistry();
            ComponentService service = new ComponentService(registry);

            System.out.println("Registered components:");

            registry.names().forEach(
                name -> System.out.println(
                    "- " + name + ": " +
                    registry.get(name).status()
                )
            );

            runTests(service);

            System.out.println("\nEnterprise component hierarchy:");

            RenderedComponent dashboard =
                service.render(buildDashboard());

            printTree(dashboard, 0);

        } catch (Exception exception) {
            System.err.println(
                "Component architecture error: " +
                exception.getMessage()
            );

            System.exit(1);
        }
    }
}
