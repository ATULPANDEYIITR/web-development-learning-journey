import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * React Effects: Enterprise resource lifecycle management.
 *
 * Java 17 implementation modeling:
 * - Explicit effect definitions.
 * - Dependency comparison.
 * - Cleanup policies.
 * - Component lifecycle transitions.
 * - Strict Mode replay.
 * - Asynchronous cancellation.
 * - Resource ownership and leak detection.
 *
 * This is a standalone domain model, not a React implementation.
 */
public class ReactEffectsEnterprise {

    enum ComponentStatus {
        MOUNTED,
        UNMOUNTED
    }

    enum DependencyMode {
        EVERY_COMMIT,
        MOUNT_ONLY,
        TRACKED
    }

    @FunctionalInterface
    interface Cleanup {
        void execute() throws Exception;
    }

    @FunctionalInterface
    interface EffectSetup {
        Cleanup execute() throws Exception;
    }

    static class LifecycleException extends RuntimeException {
        LifecycleException(String message) {
            super(message);
        }

        LifecycleException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    record Dependency(String name, Object value) {
        Dependency {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Dependency name is required."
                );
            }
        }
    }

    record EffectPolicy(
        DependencyMode mode,
        boolean cleanupRequired
    ) {
        EffectPolicy {
            Objects.requireNonNull(mode);
        }
    }

    static final class EffectDefinition {
        private final String name;
        private final EffectSetup setup;
        private final EffectPolicy policy;

        private List<Dependency> dependencies;
        private Cleanup cleanup;
        private boolean initialized;
        private int executionCount;

        EffectDefinition(
            String name,
            EffectSetup setup,
            EffectPolicy policy,
            List<Dependency> dependencies
        ) {
            this.name = Objects.requireNonNull(name);
            this.setup = Objects.requireNonNull(setup);
            this.policy = Objects.requireNonNull(policy);
            this.dependencies = List.copyOf(dependencies);
        }
    }

    static final class ResourceManager {
        private final Map<String, AtomicBoolean> resources =
            new LinkedHashMap<>();

        synchronized Cleanup acquire(String name) {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Resource name cannot be empty."
                );
            }

            AtomicBoolean state = resources.get(name);

            if (state != null && state.get()) {
                throw new LifecycleException(
                    "Resource already active: " + name
                );
            }

            AtomicBoolean active = new AtomicBoolean(true);
            resources.put(name, active);

            System.out.println("Acquired resource: " + name);

            return () -> {
                if (active.compareAndSet(true, false)) {
                    System.out.println(
                        "Released resource: " + name
                    );
                }
            };
        }

        synchronized long activeCount() {
            return resources.values()
                .stream()
                .filter(AtomicBoolean::get)
                .count();
        }
    }

    static final class EffectManager {
        private final String componentName;

        private final Map<String, EffectDefinition> effects =
            new LinkedHashMap<>();

        private ComponentStatus status = ComponentStatus.MOUNTED;
        private long commitCount;

        EffectManager(String componentName) {
            if (componentName == null || componentName.isBlank()) {
                throw new IllegalArgumentException(
                    "Component name is required."
                );
            }

            this.componentName = componentName;
        }

        synchronized void register(
            String name,
            EffectSetup setup,
            EffectPolicy policy,
            List<Dependency> dependencies
        ) {
            ensureMounted();

            if (effects.containsKey(name)) {
                throw new LifecycleException(
                    "Duplicate effect: " + name
                );
            }

            validateDependencies(policy.mode(), dependencies);

            effects.put(
                name,
                new EffectDefinition(
                    name,
                    setup,
                    policy,
                    dependencies
                )
            );
        }

        synchronized void commit(
            Map<String, List<Dependency>> updates
        ) {
            ensureMounted();
            commitCount++;

            for (EffectDefinition effect : effects.values()) {
                List<Dependency> next =
                    updates.containsKey(effect.name)
                        ? List.copyOf(updates.get(effect.name))
                        : effect.dependencies;

                validateDependencies(
                    effect.policy.mode(),
                    next
                );

                boolean execute = !effect.initialized;

                if (effect.initialized) {
                    execute = switch (effect.policy.mode()) {
                        case EVERY_COMMIT -> true;
                        case MOUNT_ONLY -> false;
                        case TRACKED ->
                            dependenciesChanged(
                                effect.dependencies,
                                next
                            );
                    };
                }

                if (!execute) {
                    continue;
                }

                cleanup(effect);

                try {
                    Cleanup newCleanup = effect.setup.execute();

                    if (
                        effect.policy.cleanupRequired()
                        && newCleanup == null
                    ) {
                        throw new LifecycleException(
                            "Cleanup is required for "
                                + effect.name
                        );
                    }

                    effect.cleanup = newCleanup;
                    effect.dependencies = next;
                    effect.initialized = true;
                    effect.executionCount++;

                    System.out.println(
                        componentName
                            + " executed "
                            + effect.name
                    );

                } catch (Exception exception) {
                    effect.cleanup = null;
                    effect.dependencies = next;
                    effect.initialized = true;

                    throw new LifecycleException(
                        "Effect failed: " + effect.name,
                        exception
                    );
                }
            }
        }

        synchronized void replayStrictMode() {
            ensureMounted();

            for (EffectDefinition effect : effects.values()) {
                if (effect.initialized) {
                    cleanup(effect);
                    effect.initialized = false;
                }
            }

            commit(Collections.emptyMap());
        }

        synchronized void unmount() {
            if (status == ComponentStatus.UNMOUNTED) {
                return;
            }

            List<EffectDefinition> reversed =
                new ArrayList<>(effects.values());

            Collections.reverse(reversed);

            for (EffectDefinition effect : reversed) {
                cleanup(effect);
            }

            status = ComponentStatus.UNMOUNTED;

            System.out.println(
                componentName + " unmounted."
            );
        }

        private void cleanup(EffectDefinition effect) {
            Cleanup previous = effect.cleanup;
            effect.cleanup = null;

            if (previous == null) {
                return;
            }

            try {
                previous.execute();
            } catch (Exception exception) {
                throw new LifecycleException(
                    "Cleanup failed: " + effect.name,
                    exception
                );
            }
        }

        private void ensureMounted() {
            if (status != ComponentStatus.MOUNTED) {
                throw new LifecycleException(
                    "Component is not mounted."
                );
            }
        }

        private static boolean dependenciesChanged(
            List<Dependency> oldDependencies,
            List<Dependency> newDependencies
        ) {
            if (oldDependencies.size() != newDependencies.size()) {
                throw new LifecycleException(
                    "Dependency count cannot change."
                );
            }

            for (int i = 0; i < oldDependencies.size(); i++) {
                Dependency oldValue = oldDependencies.get(i);
                Dependency newValue = newDependencies.get(i);

                if (!oldValue.name().equals(newValue.name())) {
                    throw new LifecycleException(
                        "Dependency order cannot change."
                    );
                }

                if (!Object.is(
                    oldValue.value(),
                    newValue.value()
                )) {
                    return true;
                }
            }

            return false;
        }

        private static void validateDependencies(
            DependencyMode mode,
            List<Dependency> dependencies
        ) {
            Objects.requireNonNull(dependencies);

            if (
                mode == DependencyMode.MOUNT_ONLY
                && !dependencies.isEmpty()
            ) {
                throw new IllegalArgumentException(
                    "MOUNT_ONLY requires an empty dependency list."
                );
            }

            if (
                mode == DependencyMode.EVERY_COMMIT
                && !dependencies.isEmpty()
            ) {
                throw new IllegalArgumentException(
                    "EVERY_COMMIT does not accept tracked dependencies."
                );
            }
        }

        synchronized long getCommitCount() {
            return commitCount;
        }
    }

    static final class AsyncSearchService
        implements AutoCloseable {

        private final ExecutorService executor =
            Executors.newSingleThreadExecutor();

        private Future<List<String>> activeRequest;

        synchronized Future<List<String>> search(String query) {
            if (query == null || query.isBlank()) {
                throw new IllegalArgumentException(
                    "Search query is required."
                );
            }

            cancel();

            activeRequest = executor.submit(() -> {
                TimeUnit.MILLISECONDS.sleep(100);

                return List.of(
                    query + " result 1",
                    query + " result 2",
                    query + " result 3"
                );
            });

            return activeRequest;
        }

        synchronized void cancel() {
            if (activeRequest != null) {
                activeRequest.cancel(true);
                activeRequest = null;
            }
        }

        @Override
        public void close() {
            cancel();
            executor.shutdownNow();

            try {
                if (!executor.awaitTermination(
                    2,
                    TimeUnit.SECONDS
                )) {
                    throw new LifecycleException(
                        "Search executor failed to terminate."
                    );
                }
            } catch (InterruptedException exception) {
                Thread.currentThread().interrupt();
                throw new LifecycleException(
                    "Shutdown interrupted.",
                    exception
                );
            }
        }
    }

    private static Dependency dependency(
        String name,
        Object value
    ) {
        return new Dependency(name, value);
    }

    public static void main(String[] args) {
        ResourceManager resources = new ResourceManager();

        EffectManager component =
            new EffectManager("EnterpriseDashboard");

        String[] selectedChannel = {"system-events"};

        component.register(
            "channel-subscription",
            () -> {
                String channel = selectedChannel[0];

                return resources.acquire(channel);
            },
            new EffectPolicy(
                DependencyMode.TRACKED,
                true
            ),
            List.of(
                dependency("channel", selectedChannel[0])
            )
        );

        component.register(
            "mount-initialization",
            () -> {
                System.out.println("Component initialized.");
                return null;
            },
            new EffectPolicy(
                DependencyMode.MOUNT_ONLY,
                false
            ),
            List.of()
        );

        component.register(
            "commit-audit",
            () -> {
                System.out.println("Commit audit recorded.");
                return null;
            },
            new EffectPolicy(
                DependencyMode.EVERY_COMMIT,
                false
            ),
            List.of()
        );

        component.commit(Map.of());

        selectedChannel[0] = "security-events";

        component.commit(
            Map.of(
                "channel-subscription",
                List.of(
                    dependency(
                        "channel",
                        selectedChannel[0]
                    )
                )
            )
        );

        if (resources.activeCount() != 1) {
            throw new LifecycleException(
                "Unexpected resource count."
            );
        }

        component.replayStrictMode();
        component.unmount();

        if (resources.activeCount() != 0) {
            throw new LifecycleException(
                "Resource leak detected."
            );
        }

        try (AsyncSearchService search =
                 new AsyncSearchService()) {

            Future<List<String>> oldSearch =
                search.search("React");

            Future<List<String>> currentSearch =
                search.search("useEffect");

            try {
                currentSearch.get(
                    2,
                    TimeUnit.SECONDS
                );

                System.out.println(
                    "Current search completed."
                );

                if (!oldSearch.isCancelled()) {
                    throw new LifecycleException(
                        "Old search was not cancelled."
                    );
                }

            } catch (Exception exception) {
                throw new LifecycleException(
                    "Search workflow failed.",
                    exception
                );
            }
        }

        System.out.println(
            "All enterprise lifecycle checks passed."
        );
    }
}
