#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <type_traits>
#include <variant>
#include <vector>

using namespace std;

// ============================================================
// TYPESCRIPT CORE: C++17 DOMAIN MODEL
// ============================================================

// ------------------------------------------------------------
// 1. Type aliases
// ------------------------------------------------------------

using UserId = int;
using Email = string;
using Score = double;
using Tags = vector<string>;
using Coordinate = pair<double, double>;


// ------------------------------------------------------------
// 2. Enums
// ------------------------------------------------------------

enum class UserRole {
    Admin,
    Developer,
    Analyst,
    Viewer
};

enum class AccountStatus {
    Active,
    Suspended,
    Pending
};

enum class ProjectStatus {
    Planned,
    InProgress,
    Completed
};

string toString(UserRole role) {
    switch (role) {
        case UserRole::Admin: return "ADMIN";
        case UserRole::Developer: return "DEVELOPER";
        case UserRole::Analyst: return "ANALYST";
        case UserRole::Viewer: return "VIEWER";
    }

    throw invalid_argument("Unknown role");
}

string toString(AccountStatus status) {
    switch (status) {
        case AccountStatus::Active: return "ACTIVE";
        case AccountStatus::Suspended: return "SUSPENDED";
        case AccountStatus::Pending: return "PENDING";
    }

    throw invalid_argument("Unknown status");
}


// ------------------------------------------------------------
// 3. Object structures
// ------------------------------------------------------------

struct Profile {
    string displayName;
    Email email;
    string location;

    void validate() const {
        if (displayName.empty()) {
            throw invalid_argument("Display name is required");
        }

        if (email.find('@') == string::npos) {
            throw invalid_argument("Invalid email");
        }

        if (location.empty()) {
            throw invalid_argument("Location is required");
        }
    }
};

struct User {
    UserId id;
    Profile profile;
    UserRole role;
    AccountStatus status;
    Tags tags;

    void validate() const {
        if (id <= 0) {
            throw invalid_argument("User ID must be positive");
        }

        profile.validate();

        set<string> uniqueTags(tags.begin(), tags.end());

        if (uniqueTags.size() != tags.size()) {
            throw invalid_argument("Duplicate tags");
        }
    }
};


// ------------------------------------------------------------
// 4. Tuple operations
// ------------------------------------------------------------

using UserSummary = tuple<UserId, string, UserRole>;

Coordinate createCoordinate(double latitude, double longitude) {
    if (!isfinite(latitude) || !isfinite(longitude)) {
        throw invalid_argument("Coordinates must be finite");
    }

    if (latitude < -90 || latitude > 90) {
        throw out_of_range("Invalid latitude");
    }

    if (longitude < -180 || longitude > 180) {
        throw out_of_range("Invalid longitude");
    }

    return {latitude, longitude};
}

string describeUser(const UserSummary& summary) {
    return to_string(get<0>(summary)) + ": " +
        get<1>(summary) + " (" +
        toString(get<2>(summary)) + ")";
}


// ------------------------------------------------------------
// 5. Union types using std::variant
// ------------------------------------------------------------

// TypeScript:
// type Identifier = number | string

using Identifier = variant<int, string>;

string normalizeIdentifier(const Identifier& identifier) {
    return visit([](const auto& value) -> string {
        using T = decay_t<decltype(value)>;

        if constexpr (is_same_v<T, int>) {
            if (value <= 0) {
                throw invalid_argument("ID must be positive");
            }

            return to_string(value);
        } else {
            if (value.empty()) {
                throw invalid_argument("ID cannot be empty");
            }

            return value;
        }
    }, identifier);
}


// ------------------------------------------------------------
// 6. Discriminated unions
// ------------------------------------------------------------

struct SuccessResult {
    map<string, string> data;
};

struct ErrorResult {
    string message;
    int code;
};

using ApiResult = variant<SuccessResult, ErrorResult>;

string handleResult(const ApiResult& result) {
    return visit([](const auto& value) -> string {
        using T = decay_t<decltype(value)>;

        if constexpr (is_same_v<T, SuccessResult>) {
            return "Success: " + to_string(value.data.size())
                + " fields";
        } else {
            return "Error " + to_string(value.code)
                + ": " + value.message;
        }
    }, result);
}


// ------------------------------------------------------------
// 7. Intersection types
// ------------------------------------------------------------

struct Auditable {
    UserId createdBy;
    string createdAt;
};

struct Permissions {
    bool canRead;
    bool canWrite;
    bool canDelete;
};

struct ManagedResource {
    int id;
    string name;
    Auditable audit;
    Permissions permissions;

    void validate() const {
        if (id <= 0 || name.empty()) {
            throw invalid_argument("Invalid resource");
        }

        if (audit.createdBy <= 0 || audit.createdAt.empty()) {
            throw invalid_argument("Invalid audit information");
        }
    }
};


// ------------------------------------------------------------
// 8. Array operations
// ------------------------------------------------------------

struct ScoreStatistics {
    double highest;
    double lowest;
    double average;
    vector<double> passed;
    vector<double> unique;
};

ScoreStatistics analyzeScores(const vector<double>& scores) {
    if (scores.empty()) {
        throw invalid_argument("Scores cannot be empty");
    }

    for (double score : scores) {
        if (!isfinite(score) || score < 0 || score > 100) {
            throw out_of_range("Invalid score");
        }
    }

    vector<double> sorted = scores;

    sort(sorted.begin(), sorted.end());

    vector<double> uniqueScores;

    for (double score : sorted) {
        if (uniqueScores.empty() || uniqueScores.back() != score) {
            uniqueScores.push_back(score);
        }
    }

    vector<double> passed;

    copy_if(
        scores.begin(),
        scores.end(),
        back_inserter(passed),
        [](double score) {
            return score >= 50;
        }
    );

    double average = accumulate(
        scores.begin(),
        scores.end(),
        0.0
    ) / scores.size();

    return {
        sorted.back(),
        sorted.front(),
        average,
        passed,
        uniqueScores
    };
}


// ------------------------------------------------------------
// 9. Generic repository
// ------------------------------------------------------------

template<typename T>
class Repository {
private:
    map<int, T> records;

public:
    void add(int id, const T& value) {
        if (id <= 0) {
            throw invalid_argument("Invalid record ID");
        }

        auto [iterator, inserted] = records.emplace(id, value);

        if (!inserted) {
            throw runtime_error("Duplicate record ID");
        }
    }

    optional<T> get(int id) const {
        auto iterator = records.find(id);

        if (iterator == records.end()) {
            return nullopt;
        }

        return iterator->second;
    }

    bool remove(int id) {
        return records.erase(id) > 0;
    }

    size_t size() const {
        return records.size();
    }
};


// ------------------------------------------------------------
// 10. Generic utility
// ------------------------------------------------------------

template<typename T>
optional<T> firstItem(const vector<T>& values) {
    if (values.empty()) {
        return nullopt;
    }

    return values.front();
}


// ------------------------------------------------------------
// 11. Main application
// ------------------------------------------------------------

int main() {
    try {
        cout << "\n=== TYPESCRIPT CORE ===\n";

        // Arrays
        cout << "\nARRAYS\n";

        vector<double> scores = {85, 92, 67, 48, 92};

        ScoreStatistics statistics = analyzeScores(scores);

        cout << "Highest: " << statistics.highest << '\n';
        cout << "Lowest: " << statistics.lowest << '\n';
        cout << "Average: " << statistics.average << '\n';

        cout << "Passed: ";

        for (double score : statistics.passed) {
            cout << score << " ";
        }

        cout << '\n';

        // Objects
        cout << "\nOBJECTS\n";

        Profile profile{
            "Atul Pandey",
            "atul@example.com",
            "Lucknow"
        };

        User user{
            101,
            profile,
            UserRole::Admin,
            AccountStatus::Active,
            {"typescript", "cpp", "backend"}
        };

        user.validate();

        cout << "User: " << user.profile.displayName << '\n';
        cout << "Email: " << user.profile.email << '\n';

        // Tuples
        cout << "\nTUPLES\n";

        Coordinate location = createCoordinate(
            26.8467,
            80.9462
        );

        cout << "Latitude: " << location.first << '\n';
        cout << "Longitude: " << location.second << '\n';

        UserSummary summary{
            user.id,
            user.profile.displayName,
            user.role
        };

        cout << describeUser(summary) << '\n';

        // Enums
        cout << "\nENUMS\n";

        cout << toString(user.role) << '\n';
        cout << toString(user.status) << '\n';

        // Union types
        cout << "\nUNION TYPES\n";

        Identifier numericId = 101;
        Identifier stringId = string("USER-101");

        cout << normalizeIdentifier(numericId) << '\n';
        cout << normalizeIdentifier(stringId) << '\n';

        // Discriminated unions
        cout << "\nDISCRIMINATED UNIONS\n";

        ApiResult success = SuccessResult{
            {{"userId", "101"}}
        };

        ApiResult failure = ErrorResult{
            "Permission denied",
            403
        };

        cout << handleResult(success) << '\n';
        cout << handleResult(failure) << '\n';

        // Intersection
        cout << "\nINTERSECTION TYPES\n";

        ManagedResource resource{
            501,
            "Project Repository",
            {101, "2026-11-07T08:00:00"},
            {true, true, false}
        };

        resource.validate();

        cout << resource.name << '\n';
        cout << "Can delete: "
             << boolalpha
             << resource.permissions.canDelete
             << '\n';

        // Generic repository
        cout << "\nGENERIC REPOSITORY\n";

        Repository<User> repository;

        repository.add(user.id, user);

        auto retrieved = repository.get(101);

        if (retrieved) {
            cout << retrieved->profile.displayName << '\n';
        }

        cout << "Count: " << repository.size() << '\n';

        // Generic utility
        cout << "\nGENERICS\n";

        auto first = firstItem(scores);

        if (first) {
            cout << "First score: " << *first << '\n';
        }

        // Validation and failure handling
        cout << "\nVALIDATION\n";

        vector<function<void()>> invalidOperations = {
            [] {
                normalizeIdentifier(Identifier{0});
            },
            [] {
                createCoordinate(100, 80);
            },
            [] {
                analyzeScores({});
            },
            [&repository, &user] {
                repository.add(user.id, user);
            }
        };

        for (const auto& operation : invalidOperations) {
            try {
                operation();
            } catch (const exception& error) {
                cout << "Expected error: "
                     << error.what() << '\n';
            }
        }

        cout << "\nExecution completed.\n";

    } catch (const exception& error) {
        cerr << "Application failure: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
