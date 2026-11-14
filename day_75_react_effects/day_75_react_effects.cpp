#include <algorithm>
#include <cmath>
#include <functional>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

/*
 * React Effects: Repository-style lifecycle and resource engine.
 *
 * This standalone C++17 program models effect execution,
 * dependency changes, cleanup, subscriptions, and merge-like
 * lifecycle conditions without depending on React.
 *
 * Complexity:
 * - Effect lookup: O(log n) using std::map.
 * - Dependency comparison: O(d) per effect.
 * - Commit: O(n * d), excluding callback execution.
 * - Cleanup: O(n) for registered effects.
 */

enum class ComponentStatus {
    Mounted,
    Unmounted
};

enum class DependencyMode {
    EveryCommit,
    MountOnly,
    Tracked
};

struct Dependency {
    std::string key;
    std::string value;

    bool operator==(const Dependency& other) const {
        return key == other.key && value == other.value;
    }
};

using Dependencies = std::vector<Dependency>;
using Cleanup = std::function<void()>;
using Setup = std::function<Cleanup()>;

struct Effect {
    std::string name;
    Setup setup;
    Dependencies dependencies;
    DependencyMode mode;
    Cleanup cleanup;
    bool initialized = false;
    std::size_t executions = 0;
};

class LifecycleError : public std::runtime_error {
public:
    explicit LifecycleError(const std::string& message)
        : std::runtime_error(message) {}
};

class ResourceRegistry {
private:
    std::map<std::string, bool> resources;

public:
    void acquire(const std::string& name) {
        if (name.empty()) {
            throw std::invalid_argument("Resource name is empty.");
        }

        if (resources[name]) {
            throw LifecycleError(
                "Resource already active: " + name
            );
        }

        resources[name] = true;
        std::cout << "Acquired: " << name << '\n';
    }

    void release(const std::string& name) {
        auto iterator = resources.find(name);

        if (iterator == resources.end() || !iterator->second) {
            return;
        }

        iterator->second = false;
        std::cout << "Released: " << name << '\n';
    }

    std::size_t activeCount() const {
        return std::count_if(
            resources.begin(),
            resources.end(),
            [](const auto& entry) {
                return entry.second;
            }
        );
    }
};

class EffectEngine {
private:
    std::string componentName;
    ComponentStatus status = ComponentStatus::Mounted;
    std::map<std::string, Effect> effects;
    std::size_t commits = 0;

    static bool changed(
        const Dependencies& previous,
        const Dependencies& current
    ) {
        if (previous.size() != current.size()) {
            throw LifecycleError(
                "Dependency count must remain constant."
            );
        }

        return previous != current;
    }

    void cleanup(Effect& effect) {
        if (effect.cleanup) {
            Cleanup previous = std::move(effect.cleanup);
            effect.cleanup = nullptr;
            previous();
        }
    }

public:
    explicit EffectEngine(std::string name)
        : componentName(std::move(name)) {
        if (componentName.empty()) {
            throw std::invalid_argument(
                "Component name cannot be empty."
            );
        }
    }

    void registerEffect(
        const std::string& name,
        Setup setup,
        DependencyMode mode,
        Dependencies dependencies = {}
    ) {
        if (status != ComponentStatus::Mounted) {
            throw LifecycleError("Component is unmounted.");
        }

        if (name.empty() || !setup) {
            throw std::invalid_argument(
                "Effect name and setup are required."
            );
        }

        if (effects.count(name)) {
            throw LifecycleError("Duplicate effect: " + name);
        }

        effects.emplace(
            name,
            Effect{
                name,
                std::move(setup),
                std::move(dependencies),
                mode,
                nullptr,
                false,
                0
            }
        );
    }

    void commit(
        const std::map<std::string, Dependencies>& updates = {}
    ) {
        if (status != ComponentStatus::Mounted) {
            throw LifecycleError("Cannot commit after unmount.");
        }

        ++commits;

        for (auto& [name, effect] : effects) {
            Dependencies next = effect.dependencies;

            auto update = updates.find(name);

            if (update != updates.end()) {
                next = update->second;
            }

            bool shouldRun = !effect.initialized;

            if (effect.initialized) {
                switch (effect.mode) {
                    case DependencyMode::EveryCommit:
                        shouldRun = true;
                        break;

                    case DependencyMode::MountOnly:
                        shouldRun = false;
                        break;

                    case DependencyMode::Tracked:
                        shouldRun = changed(
                            effect.dependencies,
                            next
                        );
                        break;
                }
            }

            if (!shouldRun) {
                continue;
            }

            cleanup(effect);

            try {
                Cleanup newCleanup = effect.setup();

                effect.cleanup = std::move(newCleanup);
                effect.dependencies = std::move(next);
                effect.initialized = true;
                ++effect.executions;

                std::cout
                    << componentName
                    << " executed "
                    << name << '\n';

            } catch (...) {
                effect.cleanup = nullptr;
                effect.initialized = true;
                effect.dependencies = std::move(next);
                throw;
            }
        }
    }

    void strictModeReplay() {
        if (status != ComponentStatus::Mounted) {
            throw LifecycleError("Component is unmounted.");
        }

        for (auto& [name, effect] : effects) {
            if (effect.initialized) {
                cleanup(effect);
                effect.initialized = false;
            }
        }

        commit();
    }

    void unmount() {
        if (status == ComponentStatus::Unmounted) {
            return;
        }

        // Reverse registration order for deterministic disposal.
        for (auto iterator = effects.rbegin();
             iterator != effects.rend();
             ++iterator) {
            cleanup(iterator->second);
        }

        status = ComponentStatus::Unmounted;
        std::cout << componentName << " unmounted\n";
    }

    std::size_t commitCount() const {
        return commits;
    }
};

struct SearchRequest {
    std::string query;
    unsigned long generation = 0;
    bool cancelled = false;
};

class SearchCoordinator {
private:
    unsigned long generation = 0;
    std::optional<SearchRequest> active;

public:
    SearchRequest start(const std::string& query) {
        if (query.empty()) {
            throw std::invalid_argument(
                "Search query cannot be empty."
            );
        }

        if (active) {
            active->cancelled = true;
        }

        active = SearchRequest{
            query,
            ++generation,
            false
        };

        return *active;
    }

    bool canPublish(const SearchRequest& request) const {
        return active.has_value()
            && !active->cancelled
            && request.generation == active->generation;
    }

    void cancel() {
        if (active) {
            active->cancelled = true;
            active.reset();
        }
    }
};

int main() {
    try {
        ResourceRegistry registry;
        EffectEngine component("AnalyticsDashboard");

        std::string channel = "system-events";

        component.registerEffect(
            "event-subscription",
            [&registry, &channel]() -> Cleanup {
                const std::string resource = channel;

                registry.acquire(resource);

                return [&registry, resource]() {
                    registry.release(resource);
                };
            },
            DependencyMode::Tracked,
            {{"channel", channel}}
        );

        component.registerEffect(
            "render-audit",
            []() -> Cleanup {
                std::cout << "Commit audit executed\n";
                return nullptr;
            },
            DependencyMode::EveryCommit
        );

        component.registerEffect(
            "initialization",
            []() -> Cleanup {
                std::cout << "Initialization executed\n";
                return nullptr;
            },
            DependencyMode::MountOnly
        );

        component.commit();

        if (registry.activeCount() != 1) {
            throw LifecycleError("Initial subscription failed.");
        }

        channel = "security-events";

        component.commit({
            {
                "event-subscription",
                {{"channel", channel}}
            }
        });

        if (registry.activeCount() != 1) {
            throw LifecycleError(
                "Previous subscription was not cleaned up."
            );
        }

        component.strictModeReplay();

        component.unmount();

        if (registry.activeCount() != 0) {
            throw LifecycleError(
                "Resource leak detected after unmount."
            );
        }

        SearchCoordinator search;

        SearchRequest oldRequest = search.start("React");

        SearchRequest newRequest = search.start("useEffect");

        if (search.canPublish(oldRequest)) {
            throw LifecycleError(
                "Obsolete request incorrectly remains active."
            );
        }

        if (!search.canPublish(newRequest)) {
            throw LifecycleError(
                "Current request cannot publish."
            );
        }

        search.cancel();

        std::cout << "\nAll lifecycle checks passed.\n";

    } catch (const std::exception& error) {
        std::cerr << "Failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
