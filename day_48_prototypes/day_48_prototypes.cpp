#include <iostream>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

/*
 * Repository asset catalog modeled with explicit prototype delegation.
 *
 * JavaScript uses prototype objects directly. C++ does not have a native
 * JavaScript-style prototype chain, so this case study models delegation
 * explicitly with shared ownership and property lookup.
 */

using PropertyMap = std::unordered_map<std::string, std::string>;

class CatalogPrototype {
public:
    explicit CatalogPrototype(
        PropertyMap properties = {},
        std::shared_ptr<CatalogPrototype> prototype = nullptr
    )
        : properties_(std::move(properties)),
          prototype_(std::move(prototype)) {}

    void setOwn(const std::string& key, const std::string& value) {
        properties_[key] = value;
    }

    bool hasOwn(const std::string& key) const {
        return properties_.find(key) != properties_.end();
    }

    std::optional<std::string> get(
        const std::string& key
    ) const {
        std::unordered_set<const CatalogPrototype*> visited;
        const CatalogPrototype* current = this;

        while (current != nullptr) {
            if (!visited.insert(current).second) {
                throw std::runtime_error("Prototype cycle detected");
            }

            const auto found = current->properties_.find(key);
            if (found != current->properties_.end()) {
                return found->second;
            }

            current = current->prototype_.get();
        }

        return std::nullopt;
    }

    void setPrototype(std::shared_ptr<CatalogPrototype> prototype) {
        prototype_ = std::move(prototype);
    }

    std::shared_ptr<CatalogPrototype> prototype() const {
        return prototype_;
    }

    std::vector<PropertyMap> describeChain() const {
        std::vector<PropertyMap> result;
        std::unordered_set<const CatalogPrototype*> visited;
        const CatalogPrototype* current = this;

        while (current != nullptr) {
            if (!visited.insert(current).second) {
                throw std::runtime_error("Prototype cycle detected");
            }

            result.push_back(current->properties_);
            current = current->prototype_.get();
        }

        return result;
    }

private:
    PropertyMap properties_;
    std::shared_ptr<CatalogPrototype> prototype_;
};

class AssetRecord {
public:
    AssetRecord(
        std::string assetTag,
        std::string hostname,
        std::shared_ptr<CatalogPrototype> prototype
    )
        : assetTag_(std::move(assetTag)),
          hostname_(std::move(hostname)),
          prototype_(std::move(prototype)) {
        if (assetTag_.empty() || hostname_.empty()) {
            throw std::invalid_argument(
                "Asset tag and hostname must not be empty"
            );
        }

        if (!prototype_) {
            throw std::invalid_argument(
                "Asset must reference a valid prototype"
            );
        }
    }

    void setOwn(const std::string& key, const std::string& value) {
        ownProperties_[key] = value;
    }

    std::optional<std::string> get(
        const std::string& key
    ) const {
        const auto own = ownProperties_.find(key);

        if (own != ownProperties_.end()) {
            return own->second;
        }

        return prototype_->get(key);
    }

    bool hasOwn(const std::string& key) const {
        return ownProperties_.find(key) != ownProperties_.end();
    }

    std::string assetTag() const {
        return assetTag_;
    }

    std::string hostname() const {
        return hostname_;
    }

private:
    std::string assetTag_;
    std::string hostname_;
    PropertyMap ownProperties_;
    std::shared_ptr<CatalogPrototype> prototype_;
};

void printProperty(
    const AssetRecord& asset,
    const std::string& property
) {
    const auto value = asset.get(property);

    std::cout << property << ": "
              << (value ? *value : "<not found>")
              << '\n';
}

int main() {
    try {
        auto organization = std::make_shared<CatalogPrototype>(
            PropertyMap{
                {"owner", "Platform Operations"},
                {"region", "ap-south-1"},
                {"classification", "internal"}
            }
        );

        auto serverDefaults = std::make_shared<CatalogPrototype>(
            PropertyMap{
                {"assetType", "server"},
                {"monitoring", "enabled"},
                {"backupPolicy", "daily"}
            },
            organization
        );

        auto productionServer = std::make_shared<CatalogPrototype>(
            PropertyMap{
                {"environment", "production"},
                {"backupPolicy", "hourly"}
            },
            serverDefaults
        );

        AssetRecord apiServer(
            "SRV-104",
            "api-01.internal",
            productionServer
        );

        apiServer.setOwn("owner", "Payments Team");
        apiServer.setOwn("cpuCores", "16");

        std::cout << "Repository asset inventory\n";
        std::cout << "Asset: " << apiServer.assetTag() << '\n';
        std::cout << "Hostname: " << apiServer.hostname() << '\n';

        printProperty(apiServer, "assetType");
        printProperty(apiServer, "environment");
        printProperty(apiServer, "owner");
        printProperty(apiServer, "region");
        printProperty(apiServer, "backupPolicy");
        printProperty(apiServer, "cpuCores");
        printProperty(apiServer, "unsupportedProperty");

        std::cout << "\nOwnership checks\n";
        std::cout << "Own owner: "
                  << (apiServer.hasOwn("owner") ? "yes" : "no")
                  << '\n';
        std::cout << "Own region: "
                  << (apiServer.hasOwn("region") ? "yes" : "no")
                  << '\n';

        std::cout << "\nPrototype chain depth: "
                  << productionServer->describeChain().size()
                  << '\n';

        // shared_ptr ownership can form reference cycles. The lookup algorithm
        // detects cycles, but shared_ptr cannot automatically reclaim a cycle.
        auto cyclicA = std::make_shared<CatalogPrototype>(
            PropertyMap{{"name", "A"}}
        );

        auto cyclicB = std::make_shared<CatalogPrototype>(
            PropertyMap{{"name", "B"}},
            cyclicA
        );

        cyclicA->setPrototype(cyclicB);

        try {
            const auto missing = cyclicA->get("notPresent");
            std::cout << "Unexpected lookup result: "
                      << (missing ? *missing : "<not found>")
                      << '\n';
        } catch (const std::runtime_error& error) {
            std::cout << "Cycle validation: " << error.what() << '\n';
        }

        // Break the ownership cycle to avoid a memory leak.
        cyclicA->setPrototype(nullptr);
        cyclicB->setPrototype(nullptr);

        try {
            AssetRecord invalid("", "api-02.internal", productionServer);
            std::cout << invalid.hostname() << '\n';
        } catch (const std::invalid_argument& error) {
            std::cout << "Invalid asset rejected: "
                      << error.what() << '\n';
        }
    } catch (const std::exception& error) {
        std::cerr << "Catalog failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
