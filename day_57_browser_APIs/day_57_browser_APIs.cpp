#include <algorithm>
#include <cctype>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

enum class StorageScope {
    Local,
    Session
};

enum class SameSite {
    Strict,
    Lax,
    None
};

enum class HistoryOperation {
    PushState,
    ReplaceState
};

struct Cookie {
    std::string name;
    std::string value;
    std::string path{"/"};
    bool secure{true};
    bool httpOnly{true};
    SameSite sameSite{SameSite::Lax};
    std::optional<int> maxAge;

    std::string serialize() const {
        if (name.empty()) {
            throw std::invalid_argument("Cookie name cannot be empty");
        }

        if (path.empty() || path.front() != '/') {
            throw std::invalid_argument("Cookie path must start with '/'");
        }

        if (sameSite == SameSite::None && !secure) {
            throw std::invalid_argument(
                "SameSite=None requires Secure"
            );
        }

        std::string result = name + "=" + value;
        result += "; Path=" + path;

        if (secure) {
            result += "; Secure";
        }

        if (httpOnly) {
            result += "; HttpOnly";
        }

        switch (sameSite) {
            case SameSite::Strict:
                result += "; SameSite=Strict";
                break;
            case SameSite::Lax:
                result += "; SameSite=Lax";
                break;
            case SameSite::None:
                result += "; SameSite=None";
                break;
        }

        if (maxAge.has_value()) {
            if (*maxAge < 0) {
                throw std::invalid_argument("Max-Age cannot be negative");
            }
            result += "; Max-Age=" + std::to_string(*maxAge);
        }

        return result;
    }
};

class StorageArea {
private:
    std::string name_;
    std::size_t quota_;
    std::unordered_map<std::string, std::string> values_;

    static void validateKey(const std::string& key) {
        if (key.empty()) {
            throw std::invalid_argument("Storage key cannot be empty");
        }
    }

    std::size_t byteCount() const {
        std::size_t total = 0;

        for (const auto& [key, value] : values_) {
            total += key.size() + value.size();
        }

        return total;
    }

public:
    StorageArea(std::string name, std::size_t quota)
        : name_(std::move(name)), quota_(quota) {}

    void setItem(const std::string& key, const std::string& value) {
        validateKey(key);

        const auto existing = values_.find(key);
        std::size_t currentSize = byteCount();

        if (existing != values_.end()) {
            currentSize -= existing->first.size();
            currentSize -= existing->second.size();
        }

        const std::size_t newSize =
            currentSize + key.size() + value.size();

        if (newSize > quota_) {
            throw std::runtime_error(
                name_ + " quota exceeded: " +
                std::to_string(newSize) + "/" +
                std::to_string(quota_)
            );
        }

        values_[key] = value;
    }

    std::optional<std::string> getItem(const std::string& key) const {
        validateKey(key);

        auto it = values_.find(key);

        if (it == values_.end()) {
            return std::nullopt;
        }

        return it->second;
    }

    void removeItem(const std::string& key) {
        validateKey(key);
        values_.erase(key);
    }

    void clear() {
        values_.clear();
    }

    std::size_t size() const {
        return values_.size();
    }
};

class URL {
private:
    std::string scheme_;
    std::string host_;
    std::string path_;
    std::map<std::string, std::string> parameters_;

public:
    explicit URL(const std::string& raw) {
        const std::string delimiter = "://";
        const auto schemeEnd = raw.find(delimiter);

        if (schemeEnd == std::string::npos) {
            throw std::invalid_argument("URL must contain a scheme");
        }

        scheme_ = raw.substr(0, schemeEnd);

        if (scheme_ != "http" && scheme_ != "https") {
            throw std::invalid_argument("Only HTTP(S) URLs are supported");
        }

        const std::size_t hostStart = schemeEnd + delimiter.size();
        const auto pathStart = raw.find('/', hostStart);

        if (pathStart == std::string::npos) {
            host_ = raw.substr(hostStart);
            path_ = "/";
        } else {
            host_ = raw.substr(hostStart, pathStart - hostStart);
            path_ = raw.substr(pathStart);
        }

        if (host_.empty()) {
            throw std::invalid_argument("URL host cannot be empty");
        }

        const auto queryStart = path_.find('?');

        if (queryStart != std::string::npos) {
            const std::string query = path_.substr(queryStart + 1);
            path_ = path_.substr(0, queryStart);

            std::size_t start = 0;

            while (start <= query.size()) {
                const auto amp = query.find('&', start);
                const std::string pair =
                    query.substr(start, amp == std::string::npos
                        ? std::string::npos
                        : amp - start);

                if (!pair.empty()) {
                    const auto equal = pair.find('=');

                    if (equal == std::string::npos) {
                        parameters_[pair] = "";
                    } else {
                        parameters_[pair.substr(0, equal)] =
                            pair.substr(equal + 1);
                    }
                }

                if (amp == std::string::npos) {
                    break;
                }

                start = amp + 1;
            }
        }
    }

    void setParameter(
        const std::string& name,
        const std::string& value
    ) {
        if (name.empty()) {
            throw std::invalid_argument(
                "URL parameter name cannot be empty"
            );
        }

        parameters_[name] = value;
    }

    void removeParameter(const std::string& name) {
        parameters_.erase(name);
    }

    std::string href() const {
        std::string result = scheme_ + "://" + host_ + path_;

        if (!parameters_.empty()) {
            result += "?";

            bool first = true;

            for (const auto& [key, value] : parameters_) {
                if (!first) {
                    result += "&";
                }

                result += key + "=" + value;
                first = false;
            }
        }

        return result;
    }

    std::string origin() const {
        return scheme_ + "://" + host_;
    }
};

struct HistoryEntry {
    std::string url;
    std::string state;
};

class HistoryManager {
private:
    std::vector<HistoryEntry> entries_;
    std::size_t index_{0};

    static void validateURL(const std::string& url) {
        if (url.rfind("http://", 0) != 0 &&
            url.rfind("https://", 0) != 0) {
            throw std::invalid_argument(
                "History accepts only HTTP(S) URLs"
            );
        }
    }

public:
    explicit HistoryManager(std::string initialURL) {
        validateURL(initialURL);
        entries_.push_back({std::move(initialURL), "{}"});
    }

    void pushState(
        const std::string& url,
        const std::string& state
    ) {
        validateURL(url);

        entries_.resize(index_ + 1);
        entries_.push_back({url, state});
        ++index_;
    }

    void replaceState(
        const std::string& url,
        const std::string& state
    ) {
        validateURL(url);
        entries_[index_] = {url, state};
    }

    const HistoryEntry& back() {
        if (index_ > 0) {
            --index_;
        }

        return entries_[index_];
    }

    const HistoryEntry& forward() {
        if (index_ + 1 < entries_.size()) {
            ++index_;
        }

        return entries_[index_];
    }

    const HistoryEntry& current() const {
        return entries_[index_];
    }

    std::size_t length() const {
        return entries_.size();
    }
};

class BrowserPolicy {
public:
    static bool isSafeNavigation(
        const std::string& url,
        const std::string& expectedOrigin
    ) {
        if (url.rfind(expectedOrigin, 0) != 0) {
            return false;
        }

        if (url.find("javascript:") != std::string::npos) {
            return false;
        }

        return true;
    }

    static void validateCookieForSession(const Cookie& cookie) {
        if (!cookie.secure) {
            throw std::invalid_argument(
                "Session cookies must use Secure"
            );
        }

        if (!cookie.httpOnly) {
            throw std::invalid_argument(
                "Session cookies should use HttpOnly"
            );
        }
    }
};

int main() {
    try {
        std::cout << "=== Storage ===\n";

        StorageArea localStorage("localStorage", 256);
        StorageArea sessionStorage("sessionStorage", 256);

        localStorage.setItem("theme", "dark");
        localStorage.setItem("language", "en");
        sessionStorage.setItem("checkoutStep", "payment");

        std::cout
            << "Theme: "
            << localStorage.getItem("theme").value()
            << "\n";

        std::cout
            << "Session step: "
            << sessionStorage.getItem("checkoutStep").value()
            << "\n";

        try {
            localStorage.setItem("oversized", std::string(500, 'x'));
        } catch (const std::exception& ex) {
            std::cout << "Expected storage failure: "
                      << ex.what() << "\n";
        }

        std::cout << "\n=== URL ===\n";

        URL url(
            "https://example.test/products"
            "?page=2&sort=price"
        );

        url.setParameter("filter", "available");
        url.removeParameter("sort");

        std::cout << "Origin: " << url.origin() << "\n";
        std::cout << "Updated URL: " << url.href() << "\n";

        std::cout << "\n=== Cookies ===\n";

        Cookie sessionCookie{
            "session_id",
            "opaque-server-token",
            "/",
            true,
            true,
            SameSite::Lax,
            std::nullopt
        };

        BrowserPolicy::validateCookieForSession(sessionCookie);

        std::cout << sessionCookie.serialize() << "\n";

        std::cout << "\n=== History ===\n";

        HistoryManager history(
            "https://example.test/dashboard"
        );

        history.pushState(
            "https://example.test/dashboard?tab=activity",
            R"({"tab":"activity"})"
        );

        history.pushState(
            "https://example.test/dashboard?tab=settings",
            R"({"tab":"settings"})"
        );

        std::cout
            << "Length: "
            << history.length()
            << "\n";

        std::cout
            << "Current: "
            << history.current().url
            << "\n";

        std::cout
            << "Back: "
            << history.back().url
            << "\n";

        history.replaceState(
            "https://example.test/dashboard?tab=security",
            R"({"tab":"security"})"
        );

        std::cout
            << "After replaceState: "
            << history.current().url
            << "\n";

        std::cout << "\n=== Navigation Policy ===\n";

        const bool safe =
            BrowserPolicy::isSafeNavigation(
                "https://example.test/account",
                "https://example.test"
            );

        const bool unsafe =
            BrowserPolicy::isSafeNavigation(
                "https://attacker.example/account",
                "https://example.test"
            );

        std::cout << "Same-origin navigation: "
                  << std::boolalpha << safe << "\n";

        std::cout << "Cross-origin navigation allowed by policy: "
                  << unsafe << "\n";

        if (!safe || unsafe) {
            throw std::runtime_error(
                "Navigation policy assertion failed"
            );
        }

        std::cout << "\nAll browser API model checks passed.\n";
    } catch (const std::exception& ex) {
        std::cerr << "Fatal error: " << ex.what() << "\n";
        return 1;
    }

    return 0;
}
