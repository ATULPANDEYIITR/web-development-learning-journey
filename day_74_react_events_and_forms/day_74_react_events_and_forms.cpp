#include <algorithm>
#include <cassert>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <regex>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <variant>
#include <vector>

using namespace std;

using Value = variant<string, bool, double>;

enum class EventType {
    Click,
    Input,
    Change,
    Blur,
    Focus,
    Submit,
    Reset
};

enum class FormStatus {
    Idle,
    Dirty,
    Validating,
    Invalid,
    Submitting,
    Submitted
};

string statusName(FormStatus status) {
    switch (status) {
        case FormStatus::Idle: return "IDLE";
        case FormStatus::Dirty: return "DIRTY";
        case FormStatus::Validating: return "VALIDATING";
        case FormStatus::Invalid: return "INVALID";
        case FormStatus::Submitting: return "SUBMITTING";
        case FormStatus::Submitted: return "SUBMITTED";
    }

    throw logic_error("Unknown form status");
}

struct UIEvent {
    EventType type;
    string target;
    Value value = string("");
    bool bubbles = true;
    bool defaultPrevented = false;
    bool propagationStopped = false;

    void preventDefault() {
        defaultPrevented = true;
    }

    void stopPropagation() {
        propagationStopped = true;
    }
};

class EventTarget {
private:
    map<EventType, vector<function<void(UIEvent&)>>> handlers;
    shared_ptr<EventTarget> parent;

public:
    explicit EventTarget(shared_ptr<EventTarget> parent = nullptr)
        : parent(move(parent)) {}

    void addEventListener(
        EventType type,
        function<void(UIEvent&)> handler
    ) {
        handlers[type].push_back(move(handler));
    }

    bool dispatchEvent(UIEvent event) {
        auto current = this;

        while (current != nullptr) {
            auto found = current->handlers.find(event.type);

            if (found != current->handlers.end()) {
                for (auto& handler : found->second) {
                    handler(event);

                    if (event.propagationStopped) {
                        return !event.defaultPrevented;
                    }
                }
            }

            if (!event.bubbles) {
                break;
            }

            current = current->parent.get();
        }

        return !event.defaultPrevented;
    }
};

struct Field {
    string name;
    Value value;
    Value initialValue;
    bool required = false;
    bool controlled = true;
    size_t maxLength = 255;
    bool touched = false;
};

struct FieldRules {
    size_t minLength = 0;
    bool email = false;
    bool numeric = false;
    double minimum = -1e18;
    double maximum = 1e18;
};

class ValidationEngine {
public:
    static vector<string> validate(
        const Field& field,
        const FieldRules& rules
    ) {
        vector<string> errors;

        if (holds_alternative<bool>(field.value)) {
            return errors;
        }

        if (holds_alternative<double>(field.value)) {
            double number = get<double>(field.value);

            if (rules.numeric &&
                (number < rules.minimum || number > rules.maximum)) {
                errors.push_back("Numeric value outside allowed range.");
            }

            return errors;
        }

        const string& value = get<string>(field.value);

        if (field.required && value.empty()) {
            errors.push_back("This field is required.");
            return errors;
        }

        if (value.empty()) {
            return errors;
        }

        if (value.size() > field.maxLength) {
            errors.push_back("Maximum length exceeded.");
        }

        if (rules.minLength > 0 &&
            value.size() < rules.minLength) {
            errors.push_back("Minimum length not satisfied.");
        }

        if (rules.email) {
            static const regex pattern(
                R"(^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$)"
            );

            if (!regex_match(value, pattern)) {
                errors.push_back("Invalid email address.");
            }
        }

        return errors;
    }
};

class Form {
private:
    map<string, Field> fields;
    map<string, FieldRules> rules;
    map<string, vector<string>> errors;
    FormStatus status = FormStatus::Idle;
    size_t revision = 0;
    size_t submissionCount = 0;
    EventTarget eventTarget;

    void transition(FormStatus next) {
        static const map<FormStatus, set<FormStatus>> allowed = {
            {FormStatus::Idle, {
                FormStatus::Dirty,
                FormStatus::Validating
            }},
            {FormStatus::Dirty, {
                FormStatus::Dirty,
                FormStatus::Idle,
                FormStatus::Validating
            }},
            {FormStatus::Validating, {
                FormStatus::Dirty,
                FormStatus::Invalid,
                FormStatus::Idle
            }},
            {FormStatus::Invalid, {
                FormStatus::Dirty,
                FormStatus::Idle,
                FormStatus::Validating
            }},
            {FormStatus::Submitting, {
                FormStatus::Dirty,
                FormStatus::Invalid,
                FormStatus::Submitted
            }},
            {FormStatus::Submitted, {
                FormStatus::Dirty,
                FormStatus::Idle,
                FormStatus::Validating
            }}
        };

        if (!allowed.at(status).count(next)) {
            throw logic_error("Invalid form state transition");
        }

        status = next;
    }

public:
    explicit Form(vector<Field> definitions) {
        for (auto& field : definitions) {
            if (field.name.empty()) {
                throw invalid_argument("Empty field name");
            }

            if (field.maxLength == 0) {
                throw invalid_argument("Invalid maximum length");
            }

            field.initialValue = field.value;

            if (!fields.emplace(field.name, field).second) {
                throw invalid_argument("Duplicate field");
            }
        }
    }

    void setRules(const string& name, FieldRules fieldRules) {
        if (!fields.count(name)) {
            throw invalid_argument("Unknown field rules");
        }

        rules[name] = fieldRules;
    }

    void setValue(const string& name, Value value) {
        auto found = fields.find(name);

        if (found == fields.end()) {
            throw invalid_argument("Unknown field");
        }

        if (!found->second.controlled) {
            throw logic_error("Field is uncontrolled");
        }

        updateField(found->second, move(value));
    }

    void setUncontrolledValue(const string& name, Value value) {
        auto found = fields.find(name);

        if (found == fields.end()) {
            throw invalid_argument("Unknown field");
        }

        if (found->second.controlled) {
            throw logic_error("Field is controlled");
        }

        updateField(found->second, move(value));
    }

private:
    void updateField(Field& field, Value value) {
        if (status == FormStatus::Submitting) {
            throw logic_error("Form submission is in progress");
        }

        if (holds_alternative<string>(value)) {
            const auto& text = get<string>(value);

            if (text.size() > field.maxLength) {
                throw length_error("Field maximum length exceeded");
            }
        }

        field.value = move(value);
        field.touched = true;

        ++revision;

        errors.erase(field.name);
        transition(FormStatus::Dirty);

        UIEvent event{
            EventType::Change,
            field.name,
            field.value
        };

        eventTarget.dispatchEvent(event);
    }

public:
    bool validate() {
        transition(FormStatus::Validating);
        errors.clear();

        for (const auto& [name, field] : fields) {
            FieldRules fieldRules;

            auto rule = rules.find(name);

            if (rule != rules.end()) {
                fieldRules = rule->second;
            }

            auto fieldErrors = ValidationEngine::validate(
                field,
                fieldRules
            );

            if (!fieldErrors.empty()) {
                errors[name] = move(fieldErrors);
            }
        }

        auto password = fields.find("password");
        auto confirmation = fields.find("confirmPassword");

        if (
            password != fields.end() &&
            confirmation != fields.end() &&
            password->second.value != confirmation->second.value
        ) {
            errors["confirmPassword"].push_back(
                "Passwords do not match."
            );
        }

        transition(
            errors.empty()
                ? FormStatus::Idle
                : FormStatus::Invalid
        );

        return errors.empty();
    }

    bool submit(
        const function<bool(const map<string, Field>&)>& handler
    ) {
        if (status == FormStatus::Submitting) {
            throw logic_error("Submission already active");
        }

        const size_t submittedRevision = revision;

        if (!validate()) {
            UIEvent event{
                EventType::Submit,
                "form"
            };

            eventTarget.dispatchEvent(event);
            return false;
        }

        if (revision != submittedRevision) {
            throw logic_error("Form changed during validation");
        }

        transition(FormStatus::Submitting);

        try {
            bool successful = handler(fields);

            if (revision != submittedRevision) {
                throw logic_error("Form changed during submission");
            }

            if (!successful) {
                transition(FormStatus::Dirty);
                return false;
            }

            ++submissionCount;
            transition(FormStatus::Submitted);

            UIEvent event{
                EventType::Submit,
                "form"
            };

            eventTarget.dispatchEvent(event);

            return true;

        } catch (...) {
            transition(FormStatus::Dirty);
            throw;
        }
    }

    void reset() {
        if (status == FormStatus::Submitting) {
            throw logic_error("Cannot reset during submission");
        }

        for (auto& [name, field] : fields) {
            field.value = field.initialValue;
            field.touched = false;
        }

        errors.clear();
        ++revision;

        transition(FormStatus::Idle);

        UIEvent event{
            EventType::Reset,
            "form"
        };

        eventTarget.dispatchEvent(event);
    }

    const map<string, vector<string>>& getErrors() const {
        return errors;
    }

    const map<string, Field>& getFields() const {
        return fields;
    }

    FormStatus getStatus() const {
        return status;
    }

    size_t getRevision() const {
        return revision;
    }

    void addEventListener(
        EventType type,
        function<void(UIEvent&)> handler
    ) {
        eventTarget.addEventListener(type, move(handler));
    }

    void printErrors() const {
        for (const auto& [name, messages] : errors) {
            cout << name << ":\n";

            for (const auto& message : messages) {
                cout << "  - " << message << '\n';
            }
        }
    }
};

string getString(
    const map<string, Field>& fields,
    const string& name
) {
    auto found = fields.find(name);

    if (
        found == fields.end() ||
        !holds_alternative<string>(found->second.value)
    ) {
        throw runtime_error("Missing string field: " + name);
    }

    return get<string>(found->second.value);
}

int main() {
    try {
        cout << "REACT EVENTS AND FORMS\n";

        cout << "\n1. Event propagation\n";

        auto parent = make_shared<EventTarget>();
        EventTarget child(parent);

        parent->addEventListener(
            EventType::Click,
            [](UIEvent&) {
                cout << "Parent received click\n";
            }
        );

        child.addEventListener(
            EventType::Click,
            [](UIEvent& event) {
                cout << "Button received click\n";
                event.preventDefault();
            }
        );

        UIEvent click{
            EventType::Click,
            "submit-button"
        };

        cout << "Default action allowed: "
             << boolalpha
             << child.dispatchEvent(click)
             << '\n';

        cout << "\n2. Form construction\n";

        Form form({
            {
                "username",
                string(""),
                string(""),
                true,
                true,
                30
            },
            {
                "email",
                string(""),
                string(""),
                true,
                true,
                100
            },
            {
                "password",
                string(""),
                string(""),
                true,
                true,
                128
            },
            {
                "confirmPassword",
                string(""),
                string(""),
                true,
                true,
                128
            },
            {
                "newsletter",
                false,
                false,
                false,
                false,
                1
            }
        });

        form.setRules(
            "username",
            FieldRules{3, false, false}
        );

        form.setRules(
            "email",
            FieldRules{0, true, false}
        );

        form.setRules(
            "password",
            FieldRules{8, false, false}
        );

        form.addEventListener(
            EventType::Change,
            [](UIEvent& event) {
                cout << "Field changed: " << event.target << '\n';
            }
        );

        form.setValue("username", string("atul"));
        form.setValue("email", string("atul@example.com"));
        form.setValue("password", string("SecurePass123"));
        form.setValue(
            "confirmPassword",
            string("SecurePass123")
        );

        form.setUncontrolledValue("newsletter", true);

        cout << "\n3. Valid submission\n";

        bool result = form.submit(
            [](const map<string, Field>& fields) {
                cout << "Registration accepted for "
                     << getString(fields, "email")
                     << '\n';

                // The password is deliberately not printed.
                return true;
            }
        );

        cout << "Submission successful: "
             << result << '\n';

        cout << "Status: "
             << statusName(form.getStatus())
             << '\n';

        cout << "\n4. Invalid submission\n";

        form.setValue("email", string("invalid"));
        form.setValue(
            "confirmPassword",
            string("DifferentPassword")
        );

        result = form.submit(
            [](const map<string, Field>&) {
                return true;
            }
        );

        cout << "Submission successful: "
             << result << '\n';

        form.printErrors();

        cout << "\n5. Reset\n";

        form.reset();

        cout << "Status: "
             << statusName(form.getStatus())
             << '\n';

        cout << "\n6. Assertion tests\n";

        assert(
            form.getStatus() == FormStatus::Idle
        );

        assert(
            form.getErrors().empty()
        );

        try {
            form.setValue("unknown", string("value"));
            assert(false);
        } catch (const invalid_argument&) {
            cout << "Unknown field rejected\n";
        }

        cout << "All tests passed.\n";

    } catch (const exception& error) {
        cerr << "Application error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
