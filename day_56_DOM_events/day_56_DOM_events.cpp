#include <algorithm>
#include <functional>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

enum class EventPhase {
    Capturing,
    AtTarget,
    Bubbling
};

class Event;

class Node;

using ListenerCallback = std::function<void(Event&)>;

struct Listener {
    ListenerCallback callback;
    bool capture{false};
    bool once{false};
    bool passive{false};
    std::string selector;
};

class Event {
public:
    std::string type;
    Node* target;
    Node* currentTarget{nullptr};
    bool bubbles{true};
    bool cancelable{true};
    bool defaultPrevented{false};
    bool propagationStopped{false};
    bool immediatePropagationStopped{false};
    EventPhase phase{EventPhase::AtTarget};
    std::function<void()> defaultAction;

    Event(
        std::string type,
        Node* target,
        bool bubbles = true,
        bool cancelable = true
    )
        : type(std::move(type)),
          target(target),
          bubbles(bubbles),
          cancelable(cancelable) {}

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
};

class Node : public std::enable_shared_from_this<Node> {
private:
    std::string name_;
    std::string id_;
    std::unordered_set<std::string> classes_;
    std::weak_ptr<Node> parent_;
    std::vector<std::shared_ptr<Node>> children_;
    std::unordered_map<std::string, std::vector<Listener>> listeners_;

public:
    explicit Node(
        std::string name,
        std::string id = {},
        std::unordered_set<std::string> classes = {}
    )
        : name_(std::move(name)),
          id_(std::move(id)),
          classes_(std::move(classes)) {}

    const std::string& name() const {
        return name_;
    }

    const std::string& id() const {
        return id_;
    }

    void appendChild(const std::shared_ptr<Node>& child) {
        if (!child) {
            throw std::invalid_argument("Child cannot be null.");
        }

        if (child.get() == this) {
            throw std::invalid_argument("A node cannot contain itself.");
        }

        auto cursor = shared_from_this();

        while (cursor) {
            if (cursor.get() == child.get()) {
                throw std::invalid_argument("Cannot create a cyclic tree.");
            }

            cursor = cursor->parent_.lock();
        }

        if (auto oldParent = child->parent_.lock()) {
            auto& siblings = oldParent->children_;

            siblings.erase(
                std::remove(
                    siblings.begin(),
                    siblings.end(),
                    child
                ),
                siblings.end()
            );
        }

        child->parent_ = shared_from_this();
        children_.push_back(child);
    }

    bool matches(const std::string& selector) const {
        if (selector.empty()) {
            return false;
        }

        if (selector.front() == '#') {
            return id_ == selector.substr(1);
        }

        if (selector.front() == '.') {
            return classes_.contains(selector.substr(1));
        }

        return name_ == selector;
    }

    void addEventListener(
        const std::string& type,
        ListenerCallback callback,
        bool capture = false,
        bool once = false,
        bool passive = false,
        std::string selector = {}
    ) {
        if (type.empty() || !callback) {
            throw std::invalid_argument("Invalid event listener.");
        }

        listeners_[type].push_back(
            Listener{
                std::move(callback),
                capture,
                once,
                passive,
                std::move(selector)
            }
        );
    }

    bool removeEventListener(
        const std::string& type,
        const ListenerCallback& callback,
        bool capture = false
    ) {
        auto found = listeners_.find(type);

        if (found == listeners_.end()) {
            return false;
        }

        auto& listeners = found->second;

        auto iterator = std::find_if(
            listeners.begin(),
            listeners.end(),
            [&](const Listener& listener) {
                return listener.capture == capture;
            }
        );

        if (iterator == listeners.end()) {
            return false;
        }

        listeners.erase(iterator);
        return true;
    }

    std::vector<std::shared_ptr<Node>> pathFromRoot() {
        std::vector<std::shared_ptr<Node>> path;
        auto current = shared_from_this();

        while (current) {
            path.push_back(current);
            current = current->parent_.lock();
        }

        std::reverse(path.begin(), path.end());
        return path;
    }

    static bool delegatedMatch(
        const std::shared_ptr<Node>& target,
        const std::shared_ptr<Node>& root,
        const std::string& selector
    ) {
        auto current = target;

        while (current) {
            if (current->matches(selector)) {
                return true;
            }

            if (current.get() == root.get()) {
                break;
            }

            current = current->parent_.lock();
        }

        return false;
    }

    void invokeListeners(
        const std::shared_ptr<Node>& node,
        Event& event,
        bool capture
    ) {
        auto found = listeners_.find(event.type);

        if (found == listeners_.end()) {
            return;
        }

        auto& listeners = found->second;
        std::vector<std::size_t> removeIndices;

        const auto target =
            event.target->shared_from_this();

        const auto root =
            node;

        const std::size_t listenerCount = listeners.size();

        for (std::size_t i = 0; i < listenerCount && i < listeners.size(); ++i) {
            auto& listener = listeners[i];

            if (listener.capture != capture) {
                continue;
            }

            if (
                !listener.selector.empty() &&
                !delegatedMatch(
                    target,
                    root,
                    listener.selector
                )
            ) {
                continue;
            }

            const bool wasPrevented = event.defaultPrevented;

            listener.callback(event);

            // Passive listeners cannot cancel the default action.
            if (listener.passive && event.defaultPrevented) {
                event.defaultPrevented = wasPrevented;
            }

            if (listener.once) {
                removeIndices.push_back(i);
            }

            if (event.immediatePropagationStopped) {
                break;
            }
        }

        std::sort(
            removeIndices.rbegin(),
            removeIndices.rend()
        );

        for (std::size_t index : removeIndices) {
            if (index < listeners.size()) {
                listeners.erase(listeners.begin() + index);
            }
        }
    }

    bool dispatchEvent(Event& event) {
        if (event.target != this) {
            throw std::invalid_argument(
                "Event target must be the dispatching node."
            );
        }

        const auto path = pathFromRoot();

        // Capture phase: root toward the event target.
        for (std::size_t i = 0; i + 1 < path.size(); ++i) {
            if (event.propagationStopped) {
                break;
            }

            event.phase = EventPhase::Capturing;
            event.currentTarget = path[i].get();

            invokeListeners(
                path[i],
                event,
                true
            );
        }

        // Target phase.
        if (!event.propagationStopped) {
            event.phase = EventPhase::AtTarget;
            event.currentTarget = this;

            invokeListeners(
                shared_from_this(),
                event,
                true
            );

            if (!event.immediatePropagationStopped) {
                invokeListeners(
                    shared_from_this(),
                    event,
                    false
                );
            }
        }

        // Bubble phase: target parent toward root.
        if (event.bubbles && !event.propagationStopped) {
            for (std::size_t i = path.size() - 1; i-- > 0;) {
                if (event.propagationStopped) {
                    break;
                }

                event.phase = EventPhase::Bubbling;
                event.currentTarget = path[i].get();

                invokeListeners(
                    path[i],
                    event,
                    false
                );
            }
        }

        event.currentTarget = nullptr;

        if (!event.defaultPrevented && event.defaultAction) {
            event.defaultAction();
        }

        return !event.defaultPrevented;
    }
};

void logEvent(const std::string& label, Event& event) {
    std::string phase;

    switch (event.phase) {
        case EventPhase::Capturing:
            phase = "capturing";
            break;
        case EventPhase::AtTarget:
            phase = "target";
            break;
        case EventPhase::Bubbling:
            phase = "bubbling";
            break;
    }

    std::cout
        << label
        << ": target=" << event.target->name()
        << ", current="
        << (event.currentTarget
                ? event.currentTarget->name()
                : "none")
        << ", phase=" << phase
        << '\n';
}

int main() {
    try {
        auto document = std::make_shared<Node>("document");
        auto app = std::make_shared<Node>("section", "app");
        auto list = std::make_shared<Node>("ul", "users");
        auto row = std::make_shared<Node>(
            "li",
            "user-17",
            std::unordered_set<std::string>{"user-row"}
        );
        auto button = std::make_shared<Node>(
            "button",
            "delete"
        );

        document->appendChild(app);
        app->appendChild(list);
        list->appendChild(row);
        row->appendChild(button);

        std::cout << "=== Capture and bubbling ===\n";

        document->addEventListener(
            "click",
            [](Event& event) {
                logEvent("document capture", event);
            },
            true
        );

        app->addEventListener(
            "click",
            [](Event& event) {
                logEvent("app capture", event);
            },
            true
        );

        button->addEventListener(
            "click",
            [](Event& event) {
                logEvent("button target", event);
            }
        );

        app->addEventListener(
            "click",
            [](Event& event) {
                logEvent("app bubble", event);
            }
        );

        document->addEventListener(
            "click",
            [](Event& event) {
                logEvent("document bubble", event);
            }
        );

        Event click("click", button.get());
        button->dispatchEvent(click);

        std::cout << "\n=== Event delegation ===\n";

        list->addEventListener(
            "click",
            [](Event& event) {
                std::cout
                    << "delegated handler accepted "
                    << event.target->id()
                    << '\n';
            },
            false,
            false,
            false,
            ".user-row"
        );

        Event delegatedClick("click", row.get());
        row->dispatchEvent(delegatedClick);

        std::cout << "\n=== preventDefault ===\n";

        button->addEventListener(
            "navigate",
            [](Event& event) {
                std::cout
                    << "navigation handler cancelled default behavior\n";
                event.preventDefault();
            }
        );

        Event navigation("navigate", button.get());
        navigation.defaultAction = [] {
            std::cout << "DEFAULT: navigation executed\n";
        };

        const bool navigationAllowed =
            button->dispatchEvent(navigation);

        std::cout
            << "default action allowed: "
            << std::boolalpha
            << navigationAllowed
            << '\n';

        std::cout << "\n=== stopImmediatePropagation ===\n";

        auto secure = std::make_shared<Node>("button");

        secure->addEventListener(
            "secure",
            [](Event& event) {
                std::cout << "security listener\n";
                event.stopImmediatePropagation();
            }
        );

        secure->addEventListener(
            "secure",
            [](Event&) {
                std::cout
                    << "ERROR: blocked listener executed\n";
            }
        );

        Event secureEvent("secure", secure.get());
        secure->dispatchEvent(secureEvent);

        std::cout << "\n=== once listener ===\n";

        int count = 0;

        secure->addEventListener(
            "audit",
            [&](Event&) {
                ++count;
                std::cout
                    << "audit invocation "
                    << count
                    << '\n';
            },
            false,
            true
        );

        Event auditOne("audit", secure.get());
        Event auditTwo("audit", secure.get());

        secure->dispatchEvent(auditOne);
        secure->dispatchEvent(auditTwo);

        if (count != 1) {
            throw std::runtime_error(
                "once listener invariant failed."
            );
        }

        std::cout << "\n=== Passive listener ===\n";

        auto scrollingArea =
            std::make_shared<Node>("div");

        scrollingArea->addEventListener(
            "wheel",
            [](Event& event) {
                event.preventDefault();
            },
            false,
            false,
            true
        );

        Event wheel("wheel", scrollingArea.get());

        wheel.defaultAction = [] {
            std::cout
                << "DEFAULT: scrolling remains enabled\n";
        };

        if (!scrollingArea->dispatchEvent(wheel)) {
            throw std::runtime_error(
                "Passive listener cancelled default behavior."
            );
        }

        std::cout << "\nAll assertions passed.\n";
        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "Event system failure: "
            << error.what()
            << '\n';
        return 1;
    }
}
