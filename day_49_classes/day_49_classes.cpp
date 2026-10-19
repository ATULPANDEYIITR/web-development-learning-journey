#include <algorithm>
#include <iomanip>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * Case study: an enterprise equipment registry.
 *
 * The registry uses a base Asset class and specialized derived classes.
 * Private fields protect asset invariants, constructors establish valid state,
 * inheritance shares common identity behavior, and static members maintain
 * process-wide registry statistics.
 */

class ValidationError : public std::runtime_error {
public:
    explicit ValidationError(const std::string& message)
        : std::runtime_error(message) {}
};

class Asset {
private:
    inline static int next_id_ = 5000;
    inline static int active_assets_ = 0;

    const int id_;
    std::string owner_;
    bool active_;

protected:
    Asset(std::string owner)
        : id_(next_id_++), owner_(std::move(owner)), active_(true) {
        if (owner_.empty()) {
            throw ValidationError("Asset owner cannot be empty.");
        }

        ++active_assets_;
    }

    void ensureActive() const {
        if (!active_) {
            throw ValidationError("Operation requires an active asset.");
        }
    }

    void deactivateBase() {
        ensureActive();
        active_ = false;
        --active_assets_;
    }

public:
    virtual ~Asset() = default;

    Asset(const Asset&) = delete;
    Asset& operator=(const Asset&) = delete;

    int id() const {
        return id_;
    }

    const std::string& owner() const {
        return owner_;
    }

    bool active() const {
        return active_;
    }

    static int activeCount() {
        return active_assets_;
    }

    static int nextIdPreview() {
        return next_id_;
    }

    virtual std::string category() const = 0;
    virtual double annualCost() const = 0;
    virtual void printDetails() const = 0;

    void deactivate() {
        deactivateBase();
    }
};

class Laptop final : public Asset {
private:
    std::string operating_system_;
    int memory_gb_;

public:
    Laptop(
        const std::string& owner,
        std::string operating_system,
        int memory_gb)
        : Asset(owner),
          operating_system_(std::move(operating_system)),
          memory_gb_(memory_gb) {
        if (operating_system_.empty()) {
            throw ValidationError("Operating system is required.");
        }

        if (memory_gb_ <= 0) {
            throw ValidationError("Memory must be positive.");
        }
    }

    std::string category() const override {
        return "Laptop";
    }

    double annualCost() const override {
        return 180.0;
    }

    void printDetails() const override {
        std::cout
            << "Laptop #" << id()
            << " owner=" << owner()
            << " OS=" << operating_system_
            << " RAM=" << memory_gb_ << "GB\n";
    }
};

class Server final : public Asset {
private:
    int cpu_cores_;
    int storage_tb_;

public:
    Server(
        const std::string& owner,
        int cpu_cores,
        int storage_tb)
        : Asset(owner),
          cpu_cores_(cpu_cores),
          storage_tb_(storage_tb) {
        if (cpu_cores_ < 2) {
            throw ValidationError("Server requires at least two CPU cores.");
        }

        if (storage_tb_ <= 0) {
            throw ValidationError("Server storage must be positive.");
        }
    }

    std::string category() const override {
        return "Server";
    }

    double annualCost() const override {
        return 2400.0 + storage_tb_ * 120.0;
    }

    void printDetails() const override {
        std::cout
            << "Server #" << id()
            << " owner=" << owner()
            << " CPU=" << cpu_cores_
            << " cores storage=" << storage_tb_ << "TB\n";
    }
};

class AssetRegistry {
private:
    std::unordered_map<int, std::unique_ptr<Asset>> assets_;

public:
    void add(std::unique_ptr<Asset> asset) {
        if (!asset) {
            throw ValidationError("Cannot register a null asset.");
        }

        const int id = asset->id();

        if (assets_.contains(id)) {
            throw ValidationError("Asset ID already exists.");
        }

        assets_.emplace(id, std::move(asset));
    }

    Asset& get(int id) {
        auto iterator = assets_.find(id);

        if (iterator == assets_.end()) {
            throw ValidationError("Asset does not exist.");
        }

        return *iterator->second;
    }

    double annualOperatingCost() const {
        double total = 0.0;

        for (const auto& [id, asset] : assets_) {
            if (asset->active()) {
                total += asset->annualCost();
            }
        }

        return total;
    }

    void printInventory() const {
        std::vector<const Asset*> ordered;

        for (const auto& [id, asset] : assets_) {
            ordered.push_back(asset.get());
        }

        std::sort(
            ordered.begin(),
            ordered.end(),
            [](const Asset* left, const Asset* right) {
                return left->id() < right->id();
            });

        for (const Asset* asset : ordered) {
            asset->printDetails();
        }
    }
};

void demonstrateConstructorsAndPrivateState() {
    std::cout << "=== Constructors and private state ===\n";

    Laptop laptop("Operations", "Linux", 32);

    std::cout << "Created asset #" << laptop.id()
              << " for " << laptop.owner() << '\n';

    /*
     * id_, owner_, and active_ are private. Client code cannot directly mutate
     * them, so state changes must pass through class-controlled operations.
     */
    laptop.deactivate();

    std::cout << "Laptop active after deactivation: "
              << std::boolalpha << laptop.active() << "\n\n";
}

void demonstrateInheritanceAndPolymorphism() {
    std::cout << "=== Inheritance and polymorphism ===\n";

    std::vector<std::unique_ptr<Asset>> assets;

    assets.push_back(
        std::make_unique<Laptop>("Finance", "Windows", 16));

    assets.push_back(
        std::make_unique<Server>("Data Platform", 16, 12));

    for (const auto& asset : assets) {
        /*
         * Virtual dispatch chooses the derived implementation of category(),
         * annualCost(), and printDetails() through the Asset interface.
         */
        std::cout << asset->category()
                  << " annual cost=" << asset->annualCost() << '\n';
        asset->printDetails();
    }

    std::cout << '\n';
}

void demonstrateStaticMembers() {
    std::cout << "=== Static members ===\n";

    std::cout << "Next asset ID: "
              << Asset::nextIdPreview() << '\n';

    std::cout << "Active assets: "
              << Asset::activeCount() << '\n';

    auto temporary = std::make_unique<Laptop>("Temporary User", "Linux", 8);

    std::cout << "After construction: "
              << Asset::activeCount() << " active\n";

    temporary->deactivate();

    std::cout << "After deactivation: "
              << Asset::activeCount() << " active\n\n";
}

void demonstrateRegistry() {
    std::cout << "=== Enterprise asset registry ===\n";

    AssetRegistry registry;

    registry.add(
        std::make_unique<Laptop>("Engineering", "Linux", 64));

    registry.add(
        std::make_unique<Laptop>("Sales", "Windows", 16));

    registry.add(
        std::make_unique<Server>("Production", 32, 24));

    registry.printInventory();

    std::cout << std::fixed << std::setprecision(2)
              << "Annual active-asset cost: "
              << registry.annualOperatingCost() << "\n\n";

    const int serverId = Asset::nextIdPreview() - 1;
    Asset& server = registry.get(serverId);
    server.deactivate();

    std::cout << "After retiring asset #" << serverId << ":\n";
    std::cout << "Annual active-asset cost: "
              << registry.annualOperatingCost() << "\n\n";
}

void demonstrateFailures() {
    std::cout << "=== Failure conditions ===\n";

    try {
        Laptop invalid("", "Linux", 16);
    } catch (const ValidationError& error) {
        std::cout << "Invalid owner: " << error.what() << '\n';
    }

    try {
        Server invalid("Platform", 1, 10);
    } catch (const ValidationError& error) {
        std::cout << "Invalid server: " << error.what() << '\n';
    }

    try {
        AssetRegistry registry;
        registry.get(999999);
    } catch (const ValidationError& error) {
        std::cout << "Unknown asset: " << error.what() << '\n';
    }

    Laptop asset("Controlled Lifecycle", "Linux", 16);
    asset.deactivate();

    try {
        asset.deactivate();
    } catch (const ValidationError& error) {
        std::cout << "Repeated deactivation: " << error.what() << '\n';
    }

    std::cout << '\n';
}

int main() {
    try {
        demonstrateConstructorsAndPrivateState();
        demonstrateInheritanceAndPolymorphism();
        demonstrateStaticMembers();
        demonstrateRegistry();
        demonstrateFailures();

        std::cout << "Final active asset count: "
                  << Asset::activeCount() << '\n';

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }
}
