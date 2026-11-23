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
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/*
 * UI Engineering: Enterprise Design System Governance.
 *
 * Java 17 implementation featuring:
 * - Immutable design tokens
 * - Theme configuration
 * - Component catalog
 * - Accessibility policies
 * - Component dependency management
 * - Controlled lifecycle transitions
 * - Release approval service
 * - Audit reporting
 */

public class Main {

    enum TokenCategory {
        COLOR,
        SPACING,
        TYPOGRAPHY,
        RADIUS,
        ELEVATION,
        MOTION
    }

    enum ComponentStatus {
        DRAFT,
        REVIEW,
        APPROVED,
        DEPRECATED
    }

    enum AccessibilityLevel {
        A,
        AA,
        AAA
    }

    enum Severity {
        ERROR,
        WARNING,
        INFO
    }

    record DesignToken(
        String name,
        TokenCategory category,
        String value,
        Optional<String> alias
    ) {
        DesignToken {
            Objects.requireNonNull(name);
            Objects.requireNonNull(category);
            Objects.requireNonNull(value);
            Objects.requireNonNull(alias);

            if (!Pattern.matches(
                "[a-z][a-z0-9-]*(\\.[a-z][a-z0-9-]*)*",
                name
            )) {
                throw new IllegalArgumentException(
                    "Invalid token name: " + name
                );
            }

            if (value.isBlank()) {
                throw new IllegalArgumentException(
                    "Token value cannot be empty"
                );
            }

            if (alias.isPresent() && alias.get().equals(name)) {
                throw new IllegalArgumentException(
                    "Token cannot reference itself"
                );
            }

            if (category == TokenCategory.COLOR &&
                alias.isEmpty() &&
                !Pattern.matches("#[0-9a-fA-F]{6}", value)) {
                throw new IllegalArgumentException(
                    "Invalid color token: " + value
                );
            }

            if (category == TokenCategory.SPACING &&
                !Pattern.matches("\\d+(\\.\\d+)?(px|rem)", value)) {
                throw new IllegalArgumentException(
                    "Invalid spacing token: " + value
                );
            }
        }
    }

    record AccessibilityPolicy(
        String role,
        boolean accessibleName,
        boolean keyboardOperable,
        boolean visibleFocus,
        double contrastRatio,
        AccessibilityLevel level
    ) {
        AccessibilityPolicy {
            Objects.requireNonNull(role);
            Objects.requireNonNull(level);

            if (role.isBlank()) {
                throw new IllegalArgumentException(
                    "Semantic role is required"
                );
            }
        }

        List<String> validate() {
            List<String> errors = new ArrayList<>();

            if (!accessibleName) {
                errors.add("Accessible name is missing");
            }

            if (!keyboardOperable) {
                errors.add("Keyboard operation is unavailable");
            }

            if (!visibleFocus) {
                errors.add("Visible focus indicator is missing");
            }

            if (!Double.isFinite(contrastRatio) ||
                contrastRatio < 0 ||
                contrastRatio > 21) {
                errors.add("Invalid contrast ratio");
            } else {
                double minimum = switch (level) {
                    case A -> 3.0;
                    case AA -> 4.5;
                    case AAA -> 7.0;
                };

                if (contrastRatio < minimum) {
                    errors.add(
                        "Contrast " + contrastRatio +
                        " is below " + level + " threshold " + minimum
                    );
                }
            }

            return errors;
        }
    }

    record PropertyRule(
        Class<?> type,
        boolean required,
        Set<String> allowedValues
    ) {
        PropertyRule {
            Objects.requireNonNull(type);
            allowedValues = Set.copyOf(allowedValues);
        }

        void validate(String name, Object value) {
            if (!type.isInstance(value)) {
                throw new IllegalArgumentException(
                    name + " must be " + type.getSimpleName()
                );
            }

            if (!allowedValues.isEmpty() &&
                !allowedValues.contains(value.toString())) {
                throw new IllegalArgumentException(
                    "Unsupported value for " + name
                );
            }
        }
    }

    static final class ComponentDefinition {
        private final String name;
        private final String version;
        private final String category;
        private final Map<String, PropertyRule> properties;
        private final List<String> tokenDependencies;
        private final List<String> componentDependencies;
        private final AccessibilityPolicy accessibility;

        private ComponentStatus status = ComponentStatus.DRAFT;

        ComponentDefinition(
            String name,
            String version,
            String category,
            Map<String, PropertyRule> properties,
            List<String> tokenDependencies,
            List<String> componentDependencies,
            AccessibilityPolicy accessibility
        ) {
            if (!Pattern.matches("[A-Z][A-Za-z0-9]*", name)) {
                throw new IllegalArgumentException(
                    "Invalid component name"
                );
            }

            if (!Pattern.matches("\\d+\\.\\d+\\.\\d+", version)) {
                throw new IllegalArgumentException(
                    "Invalid semantic version"
                );
            }

            if (category == null || category.isBlank()) {
                throw new IllegalArgumentException(
                    "Component category is required"
                );
            }

            this.name = name;
            this.version = version;
            this.category = category;
            this.properties = Map.copyOf(properties);
            this.tokenDependencies = List.copyOf(tokenDependencies);
            this.componentDependencies =
                List.copyOf(componentDependencies);
            this.accessibility = Objects.requireNonNull(accessibility);
        }

        String name() {
            return name;
        }

        String version() {
            return version;
        }

        String category() {
            return category;
        }

        ComponentStatus status() {
            return status;
        }

        AccessibilityPolicy accessibility() {
            return accessibility;
        }

        List<String> tokenDependencies() {
            return tokenDependencies;
        }

        List<String> componentDependencies() {
            return componentDependencies;
        }

        void transition(ComponentStatus next) {
            Map<ComponentStatus, Set<ComponentStatus>> transitions =
                Map.of(
                    ComponentStatus.DRAFT,
                    Set.of(ComponentStatus.REVIEW),
                    ComponentStatus.REVIEW,
                    Set.of(
                        ComponentStatus.DRAFT,
                        ComponentStatus.APPROVED
                    ),
                    ComponentStatus.APPROVED,
                    Set.of(ComponentStatus.DEPRECATED),
                    ComponentStatus.DEPRECATED,
                    Set.of()
                );

            if (!transitions.get(status).contains(next)) {
                throw new IllegalStateException(
                    "Invalid lifecycle transition: " +
                    status + " -> " + next
                );
            }

            status = next;
        }

        void validateProperties(Map<String, Object> input) {
            for (String key : input.keySet()) {
                if (!properties.containsKey(key)) {
                    throw new IllegalArgumentException(
                        "Unknown component property: " + key
                    );
                }
            }

            for (Map.Entry<String, PropertyRule> entry :
                 properties.entrySet()) {
                String key = entry.getKey();
                PropertyRule rule = entry.getValue();

                if (!input.containsKey(key)) {
                    if (rule.required()) {
                        throw new IllegalArgumentException(
                            "Missing required property: " + key
                        );
                    }
                    continue;
                }

                rule.validate(key, input.get(key));
            }
        }
    }

    record AuditFinding(
        Severity severity,
        String subject,
        String message
    ) {}

    static final class TokenService {
        private final Map<String, DesignToken> tokens =
            new LinkedHashMap<>();

        private final Map<String, Map<String, String>> themes =
            new HashMap<>();

        private String activeTheme;

        void register(DesignToken token) {
            if (tokens.putIfAbsent(token.name(), token) != null) {
                throw new IllegalArgumentException(
                    "Duplicate token: " + token.name()
                );
            }
        }

        void registerTheme(
            String name,
            Map<String, String> overrides
        ) {
            if (themes.containsKey(name)) {
                throw new IllegalArgumentException(
                    "Theme already exists: " + name
                );
            }

            for (Map.Entry<String, String> entry :
                 overrides.entrySet()) {
                DesignToken token = tokens.get(entry.getKey());

                if (token == null) {
                    throw new IllegalArgumentException(
                        "Unknown theme token: " + entry.getKey()
                    );
                }

                if (entry.getValue() == null ||
                    entry.getValue().isBlank()) {
                    throw new IllegalArgumentException(
                        "Invalid theme override"
                    );
                }

                if (token.category() == TokenCategory.COLOR &&
                    !Pattern.matches(
                        "#[0-9a-fA-F]{6}",
                        entry.getValue()
                    )) {
                    throw new IllegalArgumentException(
                        "Invalid theme color"
                    );
                }
            }

            themes.put(name, Map.copyOf(overrides));
        }

        String resolve(String name) {
            return resolve(name, new HashSet<>());
        }

        private String resolve(String name, Set<String> visited) {
            if (!visited.add(name)) {
                throw new IllegalStateException(
                    "Circular token alias: " + name
                );
            }

            if (activeTheme != null) {
                String override = themes.get(activeTheme).get(name);

                if (override != null) {
                    return override;
                }
            }

            DesignToken token = tokens.get(name);

            if (token == null) {
                throw new IllegalArgumentException(
                    "Unknown token: " + name
                );
            }

            if (token.alias().isPresent()) {
                return resolve(token.alias().get(), visited);
            }

            return token.value();
        }

        void activateTheme(String name) {
            if (!themes.containsKey(name)) {
                throw new IllegalArgumentException(
                    "Unknown theme: " + name
                );
            }

            activeTheme = name;
        }

        String activeTheme() {
            return activeTheme;
        }

        int size() {
            return tokens.size();
        }
    }

    static final class ComponentCatalog {
        private final Map<String, ComponentDefinition> components =
            new LinkedHashMap<>();

        void register(ComponentDefinition component) {
            if (components.putIfAbsent(
                component.name(),
                component
            ) != null) {
                throw new IllegalArgumentException(
                    "Duplicate component: " + component.name()
                );
            }
        }

        ComponentDefinition get(String name) {
            ComponentDefinition component = components.get(name);

            if (component == null) {
                throw new IllegalArgumentException(
                    "Unknown component: " + name
                );
            }

            return component;
        }

        List<String> dependencyOrder() {
            Set<String> temporary = new HashSet<>();
            Set<String> permanent = new HashSet<>();
            List<String> ordered = new ArrayList<>();

            for (String name : components.keySet()) {
                visit(name, temporary, permanent, ordered);
            }

            return List.copyOf(ordered);
        }

        private void visit(
            String name,
            Set<String> temporary,
            Set<String> permanent,
            List<String> ordered
        ) {
            if (permanent.contains(name)) {
                return;
            }

            if (!temporary.add(name)) {
                throw new IllegalStateException(
                    "Component dependency cycle: " + name
                );
            }

            ComponentDefinition component = get(name);

            for (String dependency :
                 component.componentDependencies()) {
                visit(dependency, temporary, permanent, ordered);
            }

            temporary.remove(name);
            permanent.add(name);
            ordered.add(name);
        }

        List<ComponentDefinition> byCategory(String category) {
            return components.values().stream()
                .filter(c -> c.category().equals(category))
                .collect(Collectors.toUnmodifiableList());
        }

        int size() {
            return components.size();
        }
    }

    static final class GovernanceService {
        private final TokenService tokens;
        private final ComponentCatalog catalog;

        GovernanceService(
            TokenService tokens,
            ComponentCatalog catalog
        ) {
            this.tokens = tokens;
            this.catalog = catalog;
        }

        List<String> validate(ComponentDefinition component) {
            List<String> errors = new ArrayList<>();

            for (String tokenName : component.tokenDependencies()) {
                try {
                    tokens.resolve(tokenName);
                } catch (RuntimeException error) {
                    errors.add(error.getMessage());
                }
            }

            for (String dependency :
                 component.componentDependencies()) {
                try {
                    catalog.get(dependency);
                } catch (RuntimeException error) {
                    errors.add(error.getMessage());
                }
            }

            errors.addAll(component.accessibility().validate());

            return errors;
        }

        void submitForReview(String name) {
            catalog.get(name).transition(ComponentStatus.REVIEW);
        }

        void approve(String name) {
            ComponentDefinition component = catalog.get(name);

            if (component.status() != ComponentStatus.REVIEW) {
                throw new IllegalStateException(
                    "Component must be under review"
                );
            }

            List<String> errors = validate(component);

            if (!errors.isEmpty()) {
                throw new IllegalStateException(
                    "Approval rejected: " + String.join("; ", errors)
                );
            }

            // Dependency ordering also detects cycles in the catalog.
            catalog.dependencyOrder();

            component.transition(ComponentStatus.APPROVED);
        }

        boolean eligibleForRelease(String name) {
            ComponentDefinition component = catalog.get(name);

            return component.status() == ComponentStatus.APPROVED
                && validate(component).isEmpty();
        }

        List<AuditFinding> audit() {
            List<AuditFinding> findings = new ArrayList<>();

            for (String name : catalog.dependencyOrder()) {
                ComponentDefinition component = catalog.get(name);

                for (String error : validate(component)) {
                    findings.add(new AuditFinding(
                        Severity.ERROR,
                        name,
                        error
                    ));
                }

                if (component.status() ==
                    ComponentStatus.DEPRECATED) {
                    findings.add(new AuditFinding(
                        Severity.WARNING,
                        name,
                        "Component is deprecated"
                    ));
                }
            }

            return Collections.unmodifiableList(findings);
        }
    }

    static double contrast(String foreground, String background) {
        double first = luminance(foreground);
        double second = luminance(background);

        return (Math.max(first, second) + 0.05)
            / (Math.min(first, second) + 0.05);
    }

    static double luminance(String color) {
        if (!Pattern.matches("#[0-9a-fA-F]{6}", color)) {
            throw new IllegalArgumentException("Invalid color");
        }

        double[] channels = new double[3];

        for (int i = 0; i < 3; i++) {
            int value = Integer.parseInt(
                color.substring(1 + i * 2, 3 + i * 2),
                16
            );

            double normalized = value / 255.0;

            channels[i] = normalized <= 0.04045
                ? normalized / 12.92
                : Math.pow((normalized + 0.055) / 1.055, 2.4);
        }

        return 0.2126 * channels[0]
            + 0.7152 * channels[1]
            + 0.0722 * channels[2];
    }

    static void addDefaultTokens(TokenService tokens) {
        tokens.register(new DesignToken(
            "color.brand.primary",
            TokenCategory.COLOR,
            "#2457C5",
            Optional.empty()
        ));

        tokens.register(new DesignToken(
            "color.text.primary",
            TokenCategory.COLOR,
            "#172033",
            Optional.empty()
        ));

        tokens.register(new DesignToken(
            "color.action.primary",
            TokenCategory.COLOR,
            "color.brand.primary",
            Optional.of("color.brand.primary")
        ));

        tokens.register(new DesignToken(
            "spacing.medium",
            TokenCategory.SPACING,
            "16px",
            Optional.empty()
        ));
    }

    static void run() {
        TokenService tokens = new TokenService();
        addDefaultTokens(tokens);

        tokens.registerTheme("dark", Map.of(
            "color.brand.primary", "#8CAFFF",
            "color.text.primary", "#FFFFFF"
        ));

        ComponentCatalog catalog = new ComponentCatalog();

        double buttonContrast = contrast("#FFFFFF", "#2457C5");

        AccessibilityPolicy buttonAccessibility =
            new AccessibilityPolicy(
                "button",
                true,
                true,
                true,
                buttonContrast,
                AccessibilityLevel.AA
            );

        ComponentDefinition button = new ComponentDefinition(
            "Button",
            "1.0.0",
            "Actions",
            Map.of(
                "label", new PropertyRule(
                    String.class, true, Set.of()
                ),
                "variant", new PropertyRule(
                    String.class,
                    false,
                    Set.of("primary", "secondary", "danger")
                ),
                "disabled", new PropertyRule(
                    Boolean.class, false, Set.of()
                )
            ),
            List.of(
                "color.action.primary",
                "spacing.medium"
            ),
            List.of(),
            buttonAccessibility
        );

        ComponentDefinition iconButton = new ComponentDefinition(
            "IconButton",
            "1.0.0",
            "Actions",
            Map.of(
                "icon", new PropertyRule(
                    String.class, true, Set.of()
                ),
                "label", new PropertyRule(
                    String.class, true, Set.of()
                )
            ),
            List.of("color.text.primary"),
            List.of("Button"),
            buttonAccessibility
        );

        catalog.register(button);
        catalog.register(iconButton);

        GovernanceService governance =
            new GovernanceService(tokens, catalog);

        System.out.println("Design system: Enterprise UI");

        System.out.println("\nToken resolution:");
        System.out.println(
            "Primary action: " +
            tokens.resolve("color.action.primary")
        );

        System.out.println("\nComponent dependency order:");
        catalog.dependencyOrder().forEach(
            System.out::println
        );

        System.out.println("\nProperty validation:");

        button.validateProperties(Map.of(
            "label", "Save",
            "variant", "primary",
            "disabled", false
        ));

        System.out.println("Button instance properties are valid.");

        System.out.println("\nApproval workflow:");

        governance.submitForReview("Button");
        governance.approve("Button");

        governance.submitForReview("IconButton");
        governance.approve("IconButton");

        System.out.println(
            "Button release eligible: " +
            governance.eligibleForRelease("Button")
        );

        System.out.println(
            "IconButton release eligible: " +
            governance.eligibleForRelease("IconButton")
        );

        System.out.println("\nTheme activation:");

        tokens.activateTheme("dark");

        System.out.println(
            "Active theme: " + tokens.activeTheme()
        );

        System.out.println(
            "Primary color: " +
            tokens.resolve("color.brand.primary")
        );

        System.out.println("\nAccessibility audit:");

        AccessibilityPolicy invalidPolicy =
            new AccessibilityPolicy(
                "button",
                false,
                false,
                false,
                2.0,
                AccessibilityLevel.AA
            );

        invalidPolicy.validate().forEach(
            error -> System.out.println("- " + error)
        );

        System.out.println("\nGovernance audit:");

        governance.audit().forEach(finding ->
            System.out.println(
                finding.severity() + " " +
                finding.subject() + ": " +
                finding.message()
            )
        );

        System.out.println(
            "\nRegistered tokens: " + tokens.size()
        );

        System.out.println(
            "Registered components: " + catalog.size()
        );
    }

    public static void main(String[] args) {
        try {
            run();
        } catch (RuntimeException error) {
            System.err.println(
                "Design system failure: " + error.getMessage()
            );
            System.exit(1);
        }
    }
}
