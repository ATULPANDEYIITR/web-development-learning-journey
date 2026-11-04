#include <algorithm>
#include <cctype>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

class PackageError : public runtime_error {
public:
    explicit PackageError(const string& message)
        : runtime_error(message) {}
};

struct Version {
    int major;
    int minor;
    int patch;

    static Version parse(const string& text) {
        stringstream stream(text);
        Version version{};

        char first, second, extra;

        if (!(stream >> version.major >> first
                     >> version.minor >> second
                     >> version.patch)) {
            throw PackageError("Invalid semantic version: " + text);
        }

        if (first != '.' || second != '.' ||
            version.major < 0 ||
            version.minor < 0 ||
            version.patch < 0 ||
            (stream >> extra)) {
            throw PackageError("Invalid semantic version: " + text);
        }

        return version;
    }

    bool operator==(const Version& other) const {
        return major == other.major &&
               minor == other.minor &&
               patch == other.patch;
    }

    bool operator<(const Version& other) const {
        if (major != other.major) return major < other.major;
        if (minor != other.minor) return minor < other.minor;
        return patch < other.patch;
    }

    bool operator<=(const Version& other) const {
        return *this < other || *this == other;
    }

    string str() const {
        return to_string(major) + "." +
               to_string(minor) + "." +
               to_string(patch);
    }
};

class VersionConstraint {
private:
    string expression;

public:
    explicit VersionConstraint(string value)
        : expression(move(value)) {
        if (expression.empty()) {
            throw PackageError("Empty version constraint.");
        }

        string base = expression;

        if (base[0] == '^' || base[0] == '~') {
            base.erase(base.begin());
        } else if (base.rfind(">=", 0) == 0 ||
                   base.rfind("<=", 0) == 0) {
            base = base.substr(2);
        } else if (base[0] == '>' || base[0] == '<') {
            base.erase(base.begin());
        }

        if (base != "*" && base != "latest") {
            Version::parse(base);
        }
    }

    bool accepts(const Version& candidate) const {
        if (expression == "*" || expression == "latest") {
            return true;
        }

        string op;
        string base = expression;

        if (base[0] == '^' || base[0] == '~') {
            op = base.substr(0, 1);
            base.erase(base.begin());
        } else if (base.rfind(">=", 0) == 0 ||
                   base.rfind("<=", 0) == 0) {
            op = base.substr(0, 2);
            base = base.substr(2);
        } else if (base[0] == '>' || base[0] == '<') {
            op = base.substr(0, 1);
            base.erase(base.begin());
        } else {
            op = "=";
        }

        Version expected = Version::parse(base);

        if (op == "^") {
            if (candidate < expected) return false;

            if (expected.major > 0) {
                return candidate.major == expected.major;
            }

            if (expected.minor > 0) {
                return candidate.major == 0 &&
                       candidate.minor == expected.minor;
            }

            return candidate.major == 0 &&
                   candidate.minor == 0 &&
                   candidate.patch == expected.patch;
        }

        if (op == "~") {
            return candidate >= expected &&
                   candidate.major == expected.major &&
                   candidate.minor == expected.minor;
        }

        if (op == ">=") return candidate >= expected;
        if (op == "<=") return candidate <= expected;
        if (op == ">") return expected < candidate;
        if (op == "<") return candidate < expected;
        if (op == "=") return candidate == expected;

        return false;
    }

    string str() const {
        return expression;
    }
};

enum class DependencyKind {
    Production,
    Development,
    Optional,
    Peer
};

string kindName(DependencyKind kind) {
    switch (kind) {
        case DependencyKind::Production: return "dependencies";
        case DependencyKind::Development: return "devDependencies";
        case DependencyKind::Optional: return "optionalDependencies";
        case DependencyKind::Peer: return "peerDependencies";
    }
    return "unknown";
}

struct Package {
    string name;
    Version version;
    map<string, VersionConstraint> dependencies;
};

struct DependencyDeclaration {
    string package;
    VersionConstraint constraint;
    DependencyKind kind;
};

struct InstalledPackage {
    string name;
    Version version;
    DependencyKind kind;
};

class Registry {
private:
    map<string, vector<Package>> packages;

public:
    void publish(const Package& package) {
        auto& versions = packages[package.name];

        for (const auto& existing : versions) {
            if (existing.version == package.version) {
                throw PackageError("Duplicate package version: " +
                                   package.name);
            }
        }

        versions.push_back(package);

        sort(
            versions.begin(),
            versions.end(),
            [](const Package& a, const Package& b) {
                return a.version < b.version;
            }
        );
    }

    const Package& resolve(
        const string& name,
        const vector<VersionConstraint>& constraints
    ) const {
        auto found = packages.find(name);

        if (found == packages.end()) {
            throw PackageError("Unknown package: " + name);
        }

        for (auto it = found->second.rbegin();
             it != found->second.rend(); ++it) {

            bool accepted = all_of(
                constraints.begin(),
                constraints.end(),
                [&](const VersionConstraint& constraint) {
                    return constraint.accepts(it->version);
                }
            );

            if (accepted) return *it;
        }

        throw PackageError(
            "No compatible version for package: " + name
        );
    }
};

class PackageProject {
private:
    string name;
    Version version;
    vector<DependencyDeclaration> declarations;

public:
    PackageProject(
        string projectName,
        Version projectVersion
    ) : name(move(projectName)), version(projectVersion) {
        if (name.empty()) {
            throw PackageError("Project name cannot be empty.");
        }
    }

    void addDependency(
        const string& package,
        const string& range,
        DependencyKind kind
    ) {
        if (package.empty()) {
            throw PackageError("Dependency name cannot be empty.");
        }

        declarations.push_back({
            package,
            VersionConstraint(range),
            kind
        });
    }

    const vector<DependencyDeclaration>& getDependencies() const {
        return declarations;
    }

    string getName() const {
        return name;
    }
};

class DependencyResolver {
private:
    const Registry& registry;

public:
    explicit DependencyResolver(const Registry& source)
        : registry(source) {}

    vector<InstalledPackage> resolve(
        const PackageProject& project,
        bool includeDevelopment = true
    ) const {
        map<string, vector<VersionConstraint>> requirements;
        map<string, DependencyKind> kinds;
        set<string> processed;
        vector<InstalledPackage> result;

        for (const auto& dependency : project.getDependencies()) {
            if (
                dependency.kind == DependencyKind::Development &&
                !includeDevelopment
            ) {
                continue;
            }

            requirements[dependency.package].push_back(
                dependency.constraint
            );

            if (!kinds.count(dependency.package)) {
                kinds[dependency.package] = dependency.kind;
            }
        }

        while (processed.size() < requirements.size()) {
            auto pending = find_if(
                requirements.begin(),
                requirements.end(),
                [&](const auto& entry) {
                    return !processed.count(entry.first);
                }
            );

            if (pending == requirements.end()) break;

            const string name = pending->first;

            const Package& selected = registry.resolve(
                name,
                pending->second
            );

            processed.insert(name);

            result.push_back({
                selected.name,
                selected.version,
                kinds.count(name)
                    ? kinds[name]
                    : DependencyKind::Production
            });

            for (const auto& child : selected.dependencies) {
                requirements[child.first].push_back(child.second);

                if (processed.count(child.first)) {
                    const auto& installed = *find_if(
                        result.begin(),
                        result.end(),
                        [&](const InstalledPackage& item) {
                            return item.name == child.first;
                        }
                    );

                    if (!child.second.accepts(installed.version)) {
                        throw PackageError(
                            "Transitive version conflict: " + child.first
                        );
                    }
                }
            }
        }

        sort(
            result.begin(),
            result.end(),
            [](const InstalledPackage& a, const InstalledPackage& b) {
                return a.name < b.name;
            }
        );

        return result;
    }
};

enum class Severity {
    Low,
    Moderate,
    High,
    Critical
};

string severityName(Severity severity) {
    switch (severity) {
        case Severity::Low: return "LOW";
        case Severity::Moderate: return "MODERATE";
        case Severity::High: return "HIGH";
        case Severity::Critical: return "CRITICAL";
    }
    return "UNKNOWN";
}

struct Advisory {
    string package;
    VersionConstraint affected;
    Severity severity;
    string identifier;
};

class SecurityPolicy {
private:
    vector<Advisory> advisories;
    Severity maximumAllowed;

    int severityValue(Severity severity) const {
        return static_cast<int>(severity);
    }

public:
    explicit SecurityPolicy(Severity maximum)
        : maximumAllowed(maximum) {}

    void addAdvisory(const Advisory& advisory) {
        advisories.push_back(advisory);
    }

    vector<string> audit(
        const vector<InstalledPackage>& installed
    ) const {
        vector<string> findings;

        for (const auto& package : installed) {
            for (const auto& advisory : advisories) {
                if (
                    package.name == advisory.package &&
                    advisory.affected.accepts(package.version)
                ) {
                    findings.push_back(
                        severityName(advisory.severity) + " " +
                        advisory.identifier + ": " +
                        package.name + "@" + package.version.str()
                    );
                }
            }
        }

        return findings;
    }

    bool deploymentAllowed(
        const vector<InstalledPackage>& installed
    ) const {
        for (const auto& package : installed) {
            for (const auto& advisory : advisories) {
                if (
                    package.name == advisory.package &&
                    advisory.affected.accepts(package.version) &&
                    severityValue(advisory.severity) >
                        severityValue(maximumAllowed)
                ) {
                    return false;
                }
            }
        }

        return true;
    }
};

int main() {
    try {
        cout << "PACKAGE MANAGEMENT AND DEPENDENCY GOVERNANCE\n";

        Registry registry;

        registry.publish({
            "express",
            Version::parse("4.21.0"),
            {}
        });

        registry.publish({
            "express",
            Version::parse("4.21.1"),
            {}
        });

        registry.publish({
            "express",
            Version::parse("5.0.0"),
            {}
        });

        registry.publish({
            "database-driver",
            Version::parse("3.2.0"),
            {}
        });

        registry.publish({
            "database-driver",
            Version::parse("3.3.0"),
            {}
        });

        registry.publish({
            "api-client",
            Version::parse("2.1.0"),
            {
                {
                    "express",
                    VersionConstraint("^4.0.0")
                }
            }
        });

        PackageProject project(
            "enterprise-dashboard",
            Version::parse("1.5.0")
        );

        project.addDependency(
            "express",
            "^4.0.0",
            DependencyKind::Production
        );

        project.addDependency(
            "database-driver",
            "~3.2.0",
            DependencyKind::Production
        );

        project.addDependency(
            "api-client",
            "^2.0.0",
            DependencyKind::Production
        );

        project.addDependency(
            "typescript",
            "^5.0.0",
            DependencyKind::Development
        );

        // Publish the development dependency.
        registry.publish({
            "typescript",
            Version::parse("5.7.0"),
            {}
        });

        DependencyResolver resolver(registry);

        cout << "\nPRODUCTION INSTALLATION\n";

        auto production = resolver.resolve(project, false);

        for (const auto& item : production) {
            cout << item.name << "@"
                 << item.version.str() << "\n";
        }

        cout << "\nDEVELOPMENT INSTALLATION\n";

        auto development = resolver.resolve(project, true);

        for (const auto& item : development) {
            cout << item.name << "@"
                 << item.version.str()
                 << " [" << kindName(item.kind) << "]\n";
        }

        SecurityPolicy security(Severity::Moderate);

        security.addAdvisory({
            "express",
            VersionConstraint("<4.21.1"),
            Severity::High,
            "SEC-2026-001"
        });

        security.addAdvisory({
            "database-driver",
            VersionConstraint("<3.3.0"),
            Severity::Moderate,
            "SEC-2026-002"
        });

        cout << "\nSECURITY AUDIT\n";

        auto findings = security.audit(development);

        if (findings.empty()) {
            cout << "No matching vulnerabilities.\n";
        } else {
            for (const auto& finding : findings) {
                cout << finding << "\n";
            }
        }

        cout << "\nDEPLOYMENT POLICY\n";

        cout << (
            security.deploymentAllowed(development)
                ? "Deployment permitted.\n"
                : "Deployment blocked by security policy.\n"
        );

        cout << "\nSEMANTIC VERSIONING\n";

        Version current = Version::parse("2.4.1");

        for (const string& range : {
            "^2.0.0",
            "~2.4.0",
            ">=2.0.0",
            "<2.0.0"
        }) {
            VersionConstraint constraint(range);

            cout << current.str() << " satisfies "
                 << range << ": "
                 << boolalpha
                 << constraint.accepts(current)
                 << "\n";
        }

        cout << "\nEDGE CASE VALIDATION\n";

        try {
            Version::parse("2.4");
        } catch (const PackageError& error) {
            cout << "Rejected malformed version: "
                 << error.what() << "\n";
        }

        try {
            project.addDependency(
                "missing-package",
                "^1.0.0",
                DependencyKind::Production
            );

            resolver.resolve(project, true);
        } catch (const PackageError& error) {
            cout << "Dependency resolution failed: "
                 << error.what() << "\n";
        }

        cout << "\nPackage governance simulation completed.\n";

    } catch (const exception& error) {
        cerr << "FATAL ERROR: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
