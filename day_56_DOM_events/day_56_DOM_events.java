import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.Consumer;

/*
 * DOM Events enterprise model.
 *
 * The implementation represents an application event gateway whose
 * propagation rules mirror DOM event behavior:
 *
 * document
 *   -> application
 *      -> component
 *         -> target
 *
 * Capture moves toward the target, the target is processed, and bubbling
 * moves back toward the root. Delegated listeners can match descendants.
 */

public class DomEventsEnterprise {

    enum EventPhase {
        CAPTURING,
        AT_TARGET,
        BUBBLING
    }

    enum ReviewDecision {
        NONE,
        ACCEPT,
        REJECT
    }

    static final class EventDispatchException extends RuntimeException {
        EventDispatchException(String message) {
            super(message);
        }
    }

    static final class DomainEvent {
        private final String type;
        private final EventTarget target;
        private final boolean bubbles;
        private final boolean cancelable;

        private EventTarget currentTarget;
        private EventPhase phase;
        private boolean defaultPrevented;
        private boolean propagationStopped;
        private boolean immediatePropagationStopped;
        private Runnable defaultAction;

        DomainEvent(
            String type,
            EventTarget target,
            boolean bubbles,
            boolean cancelable
        ) {
            if (type == null || type.isBlank()) {
                throw new EventDispatchException(
                    "Event type is required."
                );
            }

            this.type = type;
            this.target = Objects.requireNonNull(target);
            this.bubbles = bubbles;
            this.cancelable = cancelable;
        }

        String type() {
            return type;
        }

        EventTarget target() {
            return target;
        }

        EventTarget currentTarget() {
            return currentTarget;
        }

        EventPhase phase() {
            return phase;
        }

        boolean bubbles() {
            return bubbles;
        }

        boolean defaultPrevented() {
            return defaultPrevented;
        }

        void stopPropagation() {
            propagationStopped = true;
        }

        void stopImmediatePropagation() {
            immediatePropagationStopped = true;
            propagationStopped = true;
        }

        void preventDefault() {
            if (cancelable) {
                defaultPrevented = true;
            }
        }

        void defaultAction(Runnable action) {
            defaultAction = action;
        }
    }

    @FunctionalInterface
    interface EventHandler {
        void handle(DomainEvent event);
    }

    record ListenerOptions(
        boolean capture,
        boolean once,
        boolean passive,
        String selector
    ) {
        ListenerOptions {
            selector = selector == null ? "" : selector;
        }

        static ListenerOptions bubble() {
            return new ListenerOptions(false, false, false, "");
        }

        static ListenerOptions capture() {
            return new ListenerOptions(true, false, false, "");
        }

        static ListenerOptions delegated(String selector) {
            return new ListenerOptions(false, false, false, selector);
        }

        static ListenerOptions once() {
            return new ListenerOptions(false, true, false, "");
        }

        static ListenerOptions passive() {
            return new ListenerOptions(false, false, true, "");
        }
    }

    record RegisteredListener(
        EventHandler handler,
        ListenerOptions options
    ) {}

    static final class EventTarget {
        private final String name;
        private final String id;
        private final Set<String> classes;
        private EventTarget parent;
        private final List<EventTarget> children = new ArrayList<>();
        private final Map<String, List<RegisteredListener>> listeners =
            new HashMap<>();

        EventTarget(
            String name,
            String id,
            Set<String> classes
        ) {
            if (name == null || name.isBlank()) {
                throw new EventDispatchException(
                    "Target name is required."
                );
            }

            this.name = name;
            this.id = id;
            this.classes = new HashSet<>(classes);
        }

        String name() {
            return name;
        }

        String id() {
            return id;
        }

        void appendChild(EventTarget child) {
            Objects.requireNonNull(child);

            if (child == this) {
                throw new EventDispatchException(
                    "A target cannot contain itself."
                );
            }

            EventTarget cursor = this;

            while (cursor != null) {
                if (cursor == child) {
                    throw new EventDispatchException(
                        "Cyclic event target hierarchy."
                    );
                }

                cursor = cursor.parent;
            }

            if (child.parent != null) {
                child.parent.children.remove(child);
            }

            child.parent = this;
            children.add(child);
        }

        boolean matches(String selector) {
            if (selector == null || selector.isBlank()) {
                return false;
            }

            if (selector.startsWith("#")) {
                return Objects.equals(
                    id,
                    selector.substring(1)
                );
            }

            if (selector.startsWith(".")) {
                return classes.contains(
                    selector.substring(1)
                );
            }

            return name.equals(selector);
        }

        void addEventListener(
            String type,
            EventHandler handler,
            ListenerOptions options
        ) {
            if (type == null || type.isBlank()) {
                throw new EventDispatchException(
                    "Event type is required."
                );
            }

            Objects.requireNonNull(handler);
            Objects.requireNonNull(options);

            listeners
                .computeIfAbsent(type, ignored -> new ArrayList<>())
                .add(new RegisteredListener(handler, options));
        }

        List<EventTarget> pathFromRoot() {
            List<EventTarget> path = new ArrayList<>();
            EventTarget cursor = this;

            while (cursor != null) {
                path.add(cursor);
                cursor = cursor.parent;
            }

            java.util.Collections.reverse(path);
            return path;
        }

        boolean dispatchEvent(DomainEvent event) {
            if (event.target() != this) {
                throw new EventDispatchException(
                    "Event target does not match dispatcher."
                );
            }

            List<EventTarget> path = pathFromRoot();

            for (int i = 0; i < path.size() - 1; i++) {
                if (event.propagationStopped) {
                    break;
                }

                event.phase = EventPhase.CAPTURING;
                event.currentTarget = path.get(i);

                invoke(
                    path.get(i),
                    event,
                    true
                );
            }

            if (!event.propagationStopped) {
                event.phase = EventPhase.AT_TARGET;
                event.currentTarget = this;

                invoke(this, event, true);

                if (!event.immediatePropagationStopped) {
                    invoke(this, event, false);
                }
            }

            if (event.bubbles && !event.propagationStopped) {
                for (int i = path.size() - 2; i >= 0; i--) {
                    if (event.propagationStopped) {
                        break;
                    }

                    event.phase = EventPhase.BUBBLING;
                    event.currentTarget = path.get(i);

                    invoke(
                        path.get(i),
                        event,
                        false
                    );
                }
            }

            event.currentTarget = null;
            event.phase = null;

            if (!event.defaultPrevented &&
                event.defaultAction != null) {
                event.defaultAction.run();
            }

            return !event.defaultPrevented;
        }

        private void invoke(
            EventTarget node,
            DomainEvent event,
            boolean capture
        ) {
            List<RegisteredListener> registered =
                listeners.getOrDefault(
                    event.type(),
                    List.of()
                );

            List<RegisteredListener> snapshot =
                new ArrayList<>(registered);

            List<RegisteredListener> remove =
                new ArrayList<>();

            for (RegisteredListener listener : snapshot) {
                ListenerOptions options = listener.options();

                if (options.capture() != capture) {
                    continue;
                }

                if (!options.selector().isBlank() &&
                    !delegatedMatch(
                        event.target(),
                        node,
                        options.selector()
                    )) {
                    continue;
                }

                boolean previousPrevented =
                    event.defaultPrevented;

                listener.handler().handle(event);

                if (options.passive() &&
                    event.defaultPrevented) {
                    event.defaultPrevented = previousPrevented;
                }

                if (options.once()) {
                    remove.add(listener);
                }

                if (event.immediatePropagationStopped) {
                    break;
                }
            }

            registered.removeAll(remove);
        }

        private static boolean delegatedMatch(
            EventTarget target,
            EventTarget root,
            String selector
        ) {
            EventTarget cursor = target;

            while (cursor != null) {
                if (cursor.matches(selector)) {
                    return true;
                }

                if (cursor == root) {
                    break;
                }

                cursor = cursor.parent;
            }

            return false;
        }
    }

    static final class InteractionPolicy {
        private final Set<String> allowedEventTypes;

        InteractionPolicy(Set<String> allowedEventTypes) {
            this.allowedEventTypes =
                Set.copyOf(allowedEventTypes);
        }

        void validate(DomainEvent event) {
            if (!allowedEventTypes.contains(event.type())) {
                throw new EventDispatchException(
                    "Event type is not permitted: " +
                    event.type()
                );
            }
        }
    }

    static void log(String label, DomainEvent event) {
        System.out.printf(
            "%s: target=%s, current=%s, phase=%s%n",
            label,
            event.target().name(),
            event.currentTarget().name(),
            event.phase()
        );
    }

    public static void main(String[] args) {
        EventTarget document =
            new EventTarget("document", null, Set.of());

        EventTarget application =
            new EventTarget("section", "app", Set.of());

        EventTarget table =
            new EventTarget("table", "users", Set.of());

        EventTarget row =
            new EventTarget(
                "tr",
                "user-17",
                Set.of("user-row")
            );

        EventTarget button =
            new EventTarget(
                "button",
                "delete",
                Set.of()
            );

        document.appendChild(application);
        application.appendChild(table);
        table.appendChild(row);
        row.appendChild(button);

        InteractionPolicy policy =
            new InteractionPolicy(
                Set.of("click", "navigate", "audit", "wheel")
            );

        System.out.println(
            "=== Capture, target, and bubbling ==="
        );

        document.addEventListener(
            "click",
            event -> log("document capture", event),
            ListenerOptions.capture()
        );

        application.addEventListener(
            "click",
            event -> log("application capture", event),
            ListenerOptions.capture()
        );

        button.addEventListener(
            "click",
            event -> log("button target", event),
            ListenerOptions.bubble()
        );

        application.addEventListener(
            "click",
            event -> log("application bubble", event),
            ListenerOptions.bubble()
        );

        document.addEventListener(
            "click",
            event -> log("document bubble", event),
            ListenerOptions.bubble()
        );

        DomainEvent click =
            new DomainEvent(
                "click",
                button,
                true,
                true
            );

        policy.validate(click);
        button.dispatchEvent(click);

        System.out.println("\n=== Delegation ===");

        table.addEventListener(
            "click",
            event -> System.out.println(
                "delegated table handler accepted " +
                event.target().id()
            ),
            ListenerOptions.delegated(".user-row")
        );

        DomainEvent delegated =
            new DomainEvent(
                "click",
                row,
                true,
                true
            );

        policy.validate(delegated);
        row.dispatchEvent(delegated);

        System.out.println("\n=== preventDefault ===");

        button.addEventListener(
            "navigate",
            event -> {
                System.out.println(
                    "navigation policy cancelled default behavior"
                );
                event.preventDefault();
            },
            ListenerOptions.bubble()
        );

        DomainEvent navigation =
            new DomainEvent(
                "navigate",
                button,
                true,
                true
            );

        navigation.defaultAction(
            () -> System.out.println(
                "DEFAULT: navigation executed"
            )
        );

        policy.validate(navigation);

        boolean navigationAllowed =
            button.dispatchEvent(navigation);

        System.out.println(
            "default action allowed: " +
            navigationAllowed
        );

        System.out.println("\n=== Once listener ===");

        EventTarget auditTarget =
            new EventTarget(
                "button",
                "audit",
                Set.of()
            );

        final int[] invocationCount = {0};

        auditTarget.addEventListener(
            "audit",
            event -> {
                invocationCount[0]++;
                System.out.println(
                    "audit invocation " +
                    invocationCount[0]
                );
            },
            ListenerOptions.once()
        );

        DomainEvent auditOne =
            new DomainEvent(
                "audit",
                auditTarget,
                true,
                true
            );

        DomainEvent auditTwo =
            new DomainEvent(
                "audit",
                auditTarget,
                true,
                true
            );

        auditTarget.dispatchEvent(auditOne);
        auditTarget.dispatchEvent(auditTwo);

        if (invocationCount[0] != 1) {
            throw new AssertionError(
                "once listener invariant failed"
            );
        }

        System.out.println("\n=== Passive listener ===");

        EventTarget scrolling =
            new EventTarget(
                "div",
                "scroll-area",
                Set.of()
            );

        scrolling.addEventListener(
            "wheel",
            DomainEventsEnterprise::passiveWheelHandler,
            ListenerOptions.passive()
        );

        DomainEvent wheel =
            new DomainEvent(
                "wheel",
                scrolling,
                true,
                true
            );

        wheel.defaultAction(
            () -> System.out.println(
                "DEFAULT: scrolling remains enabled"
            )
        );

        policy.validate(wheel);

        if (!scrolling.dispatchEvent(wheel)) {
            throw new AssertionError(
                "Passive event was incorrectly cancelled."
            );
        }

        System.out.println("\n=== Non-bubbling event ===");

        EventTarget form =
            new EventTarget(
                "form",
                "profile",
                Set.of()
            );

        EventTarget input =
            new EventTarget(
                "input",
                "email",
                Set.of()
            );

        form.appendChild(input);

        form.addEventListener(
            "focus",
            event -> {
                throw new AssertionError(
                    "Non-bubbling event reached parent."
                );
            },
            ListenerOptions.bubble()
        );

        DomainEvent focus =
            new DomainEvent(
                "focus",
                input,
                false,
                false
            );

        input.dispatchEvent(focus);

        System.out.println("\nAll assertions passed.");
    }

    private static void passiveWheelHandler(
        DomainEvent event
    ) {
        event.preventDefault();
    }
}
