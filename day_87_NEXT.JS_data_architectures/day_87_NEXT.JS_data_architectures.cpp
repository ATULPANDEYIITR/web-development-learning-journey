#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;

enum class FetchPolicy {
    Cached,
    Uncached
};

enum class RenderMode {
    Static,
    Dynamic,
    Partial
};

enum class CacheStatus {
    Hit,
    Miss,
    Stale
};

enum class RevalidationType {
    Tag,
    Path
};

struct Product {
    int id;
    string name;
    double price;
    int stock;
    string category;
    int version;
};

struct CacheEntry {
    string value;
    chrono::steady_clock::time_point expiresAt;
    set<string> tags;
    set<string> paths;
    uint64_t version;
};

struct CacheMetrics {
    uint64_t hits = 0;
    uint64_t misses = 0;
    uint64_t staleHits = 0;
    uint64_t writes = 0;
    uint64_t invalidations = 0;
};

class ValidationError : public runtime_error {
public:
    explicit ValidationError(const string& message)
        : runtime_error(message) {}
};

class ProductRepository {
private:
    unordered_map<int, Product> products;

public:
    ProductRepository() {
        products.emplace(101, Product{
            101, "Laptop", 75000.0, 12, "Electronics", 1
        });

        products.emplace(102, Product{
            102, "Keyboard", 2500.0, 45, "Accessories", 1
        });

        products.emplace(103, Product{
            103, "Monitor", 18000.0, 8, "Electronics", 1
        });
    }

    Product get(int id) const {
        auto it = products.find(id);

        if (it == products.end()) {
            throw out_of_range("Product not found.");
        }

        return it->second;
    }

    vector<Product> getAll() const {
        vector<Product> result;

        result.reserve(products.size());

        for (const auto& item : products) {
            result.push_back(item.second);
        }

        sort(
            result.begin(),
            result.end(),
            [](const Product& a, const Product& b) {
                return a.id < b.id;
            }
        );

        return result;
    }

    Product update(
        int id,
        optional<double> price,
        optional<int> stock
    ) {
        Product current = get(id);

        if (price && (!isfinite(*price) || *price < 0)) {
            throw ValidationError("Invalid price.");
        }

        if (stock && *stock < 0) {
            throw ValidationError("Invalid stock.");
        }

        if (price) current.price = *price;
        if (stock) current.stock = *stock;

        current.version++;

        products[id] = current;

        return current;
    }
};

class CacheEngine {
private:
    unordered_map<string, CacheEntry> entries;
    unordered_map<string, set<string>> tagIndex;
    unordered_map<string, set<string>> pathIndex;
    uint64_t nextVersion = 1;

    using Clock = chrono::steady_clock;

    void removeEntry(const string& key) {
        auto it = entries.find(key);

        if (it == entries.end()) return;

        for (const auto& tag : it->second.tags) {
            auto index = tagIndex.find(tag);

            if (index != tagIndex.end()) {
                index->second.erase(key);

                if (index->second.empty()) {
                    tagIndex.erase(index);
                }
            }
        }

        for (const auto& path : it->second.paths) {
            auto index = pathIndex.find(path);

            if (index != pathIndex.end()) {
                index->second.erase(key);

                if (index->second.empty()) {
                    pathIndex.erase(index);
                }
            }
        }

        entries.erase(it);
    }

public:
    CacheMetrics metrics;

    pair<CacheStatus, string> get(const string& key) {
        auto it = entries.find(key);

        if (it == entries.end()) {
            metrics.misses++;
            return {CacheStatus::Miss, ""};
        }

        if (Clock::now() >= it->second.expiresAt) {
            metrics.staleHits++;
            return {CacheStatus::Stale, it->second.value};
        }

        metrics.hits++;
        return {CacheStatus::Hit, it->second.value};
    }

    void set(
        const string& key,
        const string& value,
        int ttlSeconds,
        const set<string>& tags,
        const set<string>& paths
    ) {
        if (ttlSeconds <= 0) {
            throw ValidationError("TTL must be positive.");
        }

        for (const auto& path : paths) {
            if (path.empty() || path.front() != '/') {
                throw ValidationError("Invalid route path.");
            }
        }

        for (const auto& tag : tags) {
            if (tag.empty()) {
                throw ValidationError("Cache tag cannot be empty.");
            }
        }

        removeEntry(key);

        CacheEntry entry{
            value,
            Clock::now() + chrono::seconds(ttlSeconds),
            tags,
            paths,
            nextVersion++
        };

        entries.emplace(key, entry);

        for (const auto& tag : tags) {
            tagIndex[tag].insert(key);
        }

        for (const auto& path : paths) {
            pathIndex[path].insert(key);
        }

        metrics.writes++;
    }

    size_t invalidate(
        RevalidationType type,
        const string& identifier
    ) {
        unordered_map<string, set<string>>* index =
            type == RevalidationType::Tag
            ? &tagIndex
            : &pathIndex;

        auto it = index->find(identifier);

        if (it == index->end()) return 0;

        vector<string> keys(
            it->second.begin(),
            it->second.end()
        );

        for (const auto& key : keys) {
            removeEntry(key);
        }

        metrics.invalidations += keys.size();

        return keys.size();
    }

    size_t cleanupExpired() {
        vector<string> expired;
        const auto now = Clock::now();

        for (const auto& [key, entry] : entries) {
            if (now >= entry.expiresAt) {
                expired.push_back(key);
            }
        }

        for (const auto& key : expired) {
            removeEntry(key);
        }

        return expired.size();
    }

    size_t size() const {
        return entries.size();
    }

    void report() const {
        cout << "Cache entries: " << entries.size() << '\n';
        cout << "Hits: " << metrics.hits << '\n';
        cout << "Misses: " << metrics.misses << '\n';
        cout << "Stale hits: " << metrics.staleHits << '\n';
        cout << "Writes: " << metrics.writes << '\n';
        cout << "Invalidations: "
             << metrics.invalidations << '\n';

        const uint64_t total =
            metrics.hits + metrics.misses + metrics.staleHits;

        double ratio = total
            ? static_cast<double>(
                metrics.hits + metrics.staleHits
            ) / total
            : 0.0;

        cout << fixed << setprecision(2);
        cout << "Hit ratio: " << ratio * 100 << "%\n";
    }
};

class ProductDataService {
private:
    ProductRepository& repository;
    CacheEngine& cache;

    static string serialize(const Product& product) {
        ostringstream output;

        output << product.id << '|'
               << product.name << '|'
               << fixed << setprecision(2) << product.price << '|'
               << product.stock << '|'
               << product.category << '|'
               << product.version;

        return output.str();
    }

public:
    ProductDataService(
        ProductRepository& repository,
        CacheEngine& cache
    ) : repository(repository), cache(cache) {}

    Product fetch(int id, FetchPolicy policy) {
        if (id <= 0) {
            throw ValidationError("Product ID must be positive.");
        }

        if (policy == FetchPolicy::Uncached) {
            return repository.get(id);
        }

        const string key = "product:" + to_string(id);

        auto result = cache.get(key);

        if (result.first == CacheStatus::Hit) {
            Product product;
            istringstream input(result.second);
            char separator;

            input >> product.id >> separator;
            getline(input, product.name, '|');
            input >> product.price >> separator
                  >> product.stock >> separator;

            getline(input, product.category, '|');
            input >> product.version;

            return product;
        }

        // This simulation refreshes synchronously.
        // Production stale-while-revalidate systems refresh in
        // the background while serving the stale value.
        Product product = repository.get(id);

        cache.set(
            key,
            serialize(product),
            60,
            {"products", "product:" + to_string(id)},
            {"/products", "/products/" + to_string(id)}
        );

        return product;
    }

    Product update(
        int id,
        optional<double> price,
        optional<int> stock
    ) {
        Product updated = repository.update(id, price, stock);

        cache.invalidate(
            RevalidationType::Tag,
            "product:" + to_string(id)
        );

        cache.invalidate(
            RevalidationType::Tag,
            "products"
        );

        return updated;
    }
};

struct RequestContext {
    bool authenticated = false;
    bool readsCookies = false;
    bool readsHeaders = false;
    bool usesUncachedData = false;
};

class RenderingEngine {
public:
    static RenderMode determine(const RequestContext& context) {
        if (
            context.authenticated ||
            context.readsCookies ||
            context.readsHeaders ||
            context.usesUncachedData
        ) {
            return RenderMode::Dynamic;
        }

        return RenderMode::Partial;
    }

    static string name(RenderMode mode) {
        switch (mode) {
            case RenderMode::Static:
                return "STATIC";

            case RenderMode::Dynamic:
                return "DYNAMIC";

            case RenderMode::Partial:
                return "PARTIAL";
        }

        throw logic_error("Unknown render mode.");
    }
};

struct RoutePolicy {
    string route;
    bool protectedRoute;
    bool cachePublicData;
    int ttlSeconds;
    set<string> tags;
};

class GovernanceEngine {
private:
    map<string, RoutePolicy> policies;

public:
    void registerPolicy(const RoutePolicy& policy) {
        if (
            policy.route.empty() ||
            policy.route.front() != '/'
        ) {
            throw ValidationError("Invalid route.");
        }

        if (policy.ttlSeconds < 0) {
            throw ValidationError("Invalid route TTL.");
        }

        if (
            policy.protectedRoute &&
            policy.cachePublicData
        ) {
            throw ValidationError(
                "Protected routes cannot use shared public caching."
            );
        }

        policies[policy.route] = policy;
    }

    bool canUseSharedCache(const string& route) const {
        auto it = policies.find(route);

        if (it == policies.end()) {
            throw out_of_range("Route policy not found.");
        }

        return !it->second.protectedRoute &&
               it->second.cachePublicData;
    }

    void report() const {
        for (const auto& [path, policy] : policies) {
            cout << path
                 << " | TTL: " << policy.ttlSeconds
                 << " | Public cache: "
                 << boolalpha << policy.cachePublicData
                 << " | Protected: "
                 << policy.protectedRoute
                 << '\n';
        }
    }
};

void runTests() {
    ProductRepository repository;
    CacheEngine cache;
    ProductDataService service(repository, cache);

    Product first = service.fetch(101, FetchPolicy::Cached);
    Product second = service.fetch(101, FetchPolicy::Cached);

    if (first.price != second.price) {
        throw runtime_error("Cache consistency test failed.");
    }

    Product updated = service.update(
        101,
        72000.0,
        15
    );

    if (updated.version != 2) {
        throw runtime_error("Version increment failed.");
    }

    Product refreshed = service.fetch(
        101,
        FetchPolicy::Cached
    );

    if (refreshed.price != 72000.0) {
        throw runtime_error("Revalidation test failed.");
    }

    if (cache.invalidate(
        RevalidationType::Path,
        "/products/101"
    ) != 1) {
        throw runtime_error("Path invalidation test failed.");
    }

    try {
        service.fetch(-1, FetchPolicy::Cached);
        throw runtime_error("Invalid ID was accepted.");
    } catch (const ValidationError&) {
        // Expected.
    }

    cout << "All C++17 tests passed.\n";
}

int main() {
    try {
        runTests();

        cout << "\nNEXT.JS DATA ARCHITECTURE ENGINE\n";
        cout << "========================================\n";

        ProductRepository repository;
        CacheEngine cache;
        ProductDataService service(repository, cache);

        cout << "\n1. Initial server-side fetch\n";

        Product laptop = service.fetch(
            101,
            FetchPolicy::Cached
        );

        cout << laptop.name
             << " | Price: " << laptop.price
             << " | Version: " << laptop.version
             << '\n';

        cout << "\n2. Repeated cached fetch\n";

        Product cached = service.fetch(
            101,
            FetchPolicy::Cached
        );

        cout << cached.name << " retrieved.\n";

        cout << "\n3. Uncached fetch\n";

        Product fresh = service.fetch(
            102,
            FetchPolicy::Uncached
        );

        cout << fresh.name << " fetched directly.\n";

        cout << "\n4. Dynamic rendering evaluation\n";

        RequestContext publicRequest;
        RequestContext authenticatedRequest;

        authenticatedRequest.authenticated = true;
        authenticatedRequest.readsCookies = true;

        cout << "Public page: "
             << RenderingEngine::name(
                RenderingEngine::determine(publicRequest)
             )
             << '\n';

        cout << "Authenticated page: "
             << RenderingEngine::name(
                RenderingEngine::determine(authenticatedRequest)
             )
             << '\n';

        cout << "\n5. Mutation and tag invalidation\n";

        Product updated = service.update(
            101,
            70000.0,
            20
        );

        cout << "Updated price: " << updated.price
             << " | Version: " << updated.version
             << '\n';

        cout << "\n6. Refreshed data\n";

        Product refreshed = service.fetch(
            101,
            FetchPolicy::Cached
        );

        cout << "Current price: " << refreshed.price << '\n';

        cout << "\n7. Route governance\n";

        GovernanceEngine governance;

        governance.registerPolicy({
            "/products",
            false,
            true,
            300,
            {"products"}
        });

        governance.registerPolicy({
            "/account",
            true,
            false,
            0,
            {}
        });

        governance.report();

        cout << "\nShared caching /products: "
             << boolalpha
             << governance.canUseSharedCache("/products")
             << '\n';

        cout << "Shared caching /account: "
             << governance.canUseSharedCache("/account")
             << '\n';

        cout << "\n8. Cache metrics\n";
        cache.report();

        cout << "\n9. Expiration cleanup\n";
        cout << "Removed: "
             << cache.cleanupExpired()
             << '\n';

        cout << "\nExecution completed.\n";

    } catch (const exception& error) {
        cerr << "Application error: "
             << error.what()
             << '\n';

        return 1;
    }

    return 0;
}
