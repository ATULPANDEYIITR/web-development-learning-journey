#include <algorithm>
#include <chrono>
#include <cmath>
#include <future>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * API-powered operational dashboard.
 *
 * C++17 implementation focused on:
 * - Concurrent data acquisition with std::async
 * - Typed resource models
 * - Resource-specific validation
 * - Bounded retry policies
 * - Last-known-good cache values
 * - Explicit dashboard lifecycle states
 * - Aggregation and health evaluation
 *
 * Compile:
 * g++ -std=c++17 -O2 -Wall -Wextra -pedantic dashboard.cpp -o dashboard
 */

using Clock = std::chrono::system_clock;
using TimePoint = Clock::time_point;

enum class DashboardPhase {
    Idle,
    Loading,
    Ready,
    Degraded,
    Failed
};

enum class ServiceStatus {
    Operational,
    Degraded,
    Down
};

enum class IncidentSeverity {
    Low,
    Medium,
    High,
    Critical
};

enum class IncidentStatus {
    Open,
    Investigating,
    Resolved
};

std::string toString(DashboardPhase phase) {
    switch (phase) {
        case DashboardPhase::Idle: return "IDLE";
        case DashboardPhase::Loading: return "LOADING";
        case DashboardPhase::Ready: return "READY";
        case DashboardPhase::Degraded: return "DEGRADED";
        case DashboardPhase::Failed: return "FAILED";
    }
    throw std::logic_error("Unknown dashboard phase.");
}

std::string toString(ServiceStatus status) {
    switch (status) {
        case ServiceStatus::Operational: return "OPERATIONAL";
        case ServiceStatus::Degraded: return "DEGRADED";
        case ServiceStatus::Down: return "DOWN";
    }
    throw std::logic_error("Unknown service status.");
}

std::string toString(IncidentSeverity severity) {
    switch (severity) {
        case IncidentSeverity::Low: return "LOW";
        case IncidentSeverity::Medium: return "MEDIUM";
        case IncidentSeverity::High: return "HIGH";
        case IncidentSeverity::Critical: return "CRITICAL";
    }
    throw std::logic_error("Unknown incident severity.");
}

TimePoint secondsAgo(int seconds) {
    return Clock::now() - std::chrono::seconds(seconds);
}

struct Metric {
    std::string serviceId;
    std::string name;
    double value{};
    std::string unit;
    TimePoint observedAt;
};

struct Service {
    std::string id;
    std::string name;
    ServiceStatus status;
    std::string region;
};

struct Incident {
    std::string id;
    std::string serviceId;
    IncidentSeverity severity;
    IncidentStatus status;
    std::string title;
    TimePoint openedAt;
};

template <typename T>
struct ResourceResult {
    std::vector<T> records;
    bool stale{false};
    std::string error;

    bool available() const {
        return !records.empty();
    }
};

struct DashboardSnapshot {
    DashboardPhase phase{DashboardPhase::Idle};
    std::vector<Metric> metrics;
    std::vector<Service> services;
    std::vector<Incident> incidents;
    std::vector<std::string> errors;
    std::vector<std::string> staleResources;
    TimePoint updatedAt{};
};

struct DashboardPolicy {
    int maxAttempts{3};
    int retryDelayMilliseconds{10};
    int maxFutureTimestampSeconds{300};

    void validate() const {
        if (maxAttempts < 1 || retryDelayMilliseconds < 0) {
            throw std::invalid_argument("Invalid retry policy.");
        }
        if (maxFutureTimestampSeconds < 0) {
            throw std::invalid_argument("Invalid timestamp policy.");
        }
    }
};

class MockApiClient {
public:
    MockApiClient()
        : incidentFailuresRemaining_(0) {}

    std::vector<Metric> fetchMetrics() const {
        const auto now = Clock::now();

        return {
            {"payments", "latency", 145.2, "ms", now - std::chrono::seconds(12)},
            {"payments", "error_rate", 0.8, "%", now - std::chrono::seconds(12)},
            {"identity", "latency", 88.4, "ms", now - std::chrono::seconds(8)},
            {"identity", "error_rate", 0.2, "%", now - std::chrono::seconds(8)},
            {"notifications", "latency", 420.0, "ms", now - std::chrono::seconds(20)}
        };
    }

    std::vector<Service> fetchServices() const {
        return {
            {"payments", "Payment Processing", ServiceStatus::Operational, "ap-south-1"},
            {"identity", "Identity Service", ServiceStatus::Operational, "ap-south-1"},
            {"notifications", "Notification Gateway", ServiceStatus::Degraded, "ap-south-1"}
        };
    }

    std::vector<Incident> fetchIncidents() {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            if (incidentFailuresRemaining_ > 0) {
                --incidentFailuresRemaining_;
                throw std::runtime_error("Temporary incident API failure.");
            }
        }

        return {
            {
                "INC-2041",
                "notifications",
                IncidentSeverity::High,
                IncidentStatus::Investigating,
                "Elevated notification latency",
                secondsAgo(1800)
            },
            {
                "INC-2038",
                "payments",
                IncidentSeverity::Low,
                IncidentStatus::Resolved,
                "Intermittent callback delay",
                secondsAgo(7200)
            }
        };
    }

    void failNextIncidents(int count) {
        if (count < 0) {
            throw std::invalid_argument("Failure count cannot be negative.");
        }

        std::lock_guard<std::mutex> lock(mutex_);
        incidentFailuresRemaining_ = count;
    }

private:
    std::mutex mutex_;
    int incidentFailuresRemaining_;
};

void validateMetrics(const std::vector<Metric>& records) {
    std::set<std::pair<std::string, std::string>> seen;

    for (const auto& metric : records) {
        if (metric.serviceId.empty() || metric.name.empty() || metric.unit.empty()) {
            throw std::invalid_argument("Metric identifiers and units are required.");
        }

        if (!std::isfinite(metric.value) || metric.value < 0) {
            throw std::invalid_argument("Metric value must be finite and non-negative.");
        }

        if (!seen.emplace(metric.serviceId, metric.name).second) {
            throw std::invalid_argument("Duplicate service metric.");
        }

        if (metric.observedAt > Clock::now() + std::chrono::minutes(5)) {
            throw std::invalid_argument("Metric timestamp is in the future.");
        }
    }
}

void validateServices(const std::vector<Service>& records) {
    std::set<std::string> seen;

    for (const auto& service : records) {
        if (service.id.empty() || service.name.empty() || service.region.empty()) {
            throw std::invalid_argument("Service fields cannot be empty.");
        }

        if (!seen.insert(service.id).second) {
            throw std::invalid_argument("Duplicate service identifier.");
        }
    }
}

void validateIncidents(const std::vector<Incident>& records) {
    std::set<std::string> seen;

    for (const auto& incident : records) {
        if (
            incident.id.empty() ||
            incident.serviceId.empty() ||
            incident.title.empty()
        ) {
            throw std::invalid_argument("Incident fields cannot be empty.");
        }

        if (!seen.insert(incident.id).second) {
            throw std::invalid_argument("Duplicate incident identifier.");
        }

        if (incident.openedAt > Clock::now() + std::chrono::minutes(5)) {
            throw std::invalid_argument("Incident timestamp is in the future.");
        }
    }
}

template <typename T, typename FetchFunction, typename ValidateFunction>
ResourceResult<T> loadWithRetry(
    FetchFunction fetch,
    ValidateFunction validate,
    std::vector<T>& lastKnownGood,
    const DashboardPolicy& policy
) {
    std::string lastError;

    for (int attempt = 0; attempt < policy.maxAttempts; ++attempt) {
        try {
            auto records = fetch();
            validate(records);

            // Replace the cache only after the complete payload passes validation.
            lastKnownGood = records;

            return {std::move(records), false, ""};

        } catch (const std::exception& error) {
            lastError = error.what();

            if (attempt + 1 < policy.maxAttempts) {
                const int delay =
                    policy.retryDelayMilliseconds * (1 << std::min(attempt, 10));

                std::this_thread::sleep_for(
                    std::chrono::milliseconds(delay)
                );
            }
        }
    }

    if (!lastKnownGood.empty()) {
        return {
            lastKnownGood,
            true,
            "Using last-known-good data: " + lastError
        };
    }

    return {{}, false, lastError};
}

struct DashboardSummary {
    std::size_t totalServices{};
    std::size_t operationalServices{};
    std::size_t degradedServices{};
    std::size_t unavailableServices{};
    std::size_t openIncidents{};
    double operationalPercentage{};
    std::optional<double> averageErrorRate;
};

class DashboardService {
public:
    DashboardService(MockApiClient& api, DashboardPolicy policy)
        : api_(api), policy_(policy) {
        policy_.validate();
    }

    DashboardSnapshot refresh() {
        snapshot_.phase = DashboardPhase::Loading;

        /*
         * Each resource has an independent task and cache.
         * The futures execute API calls concurrently. Snapshot mutation
         * remains on the calling thread after all futures have completed.
         */
        auto metricsFuture = std::async(
            std::launch::async,
            [this]() {
                return loadWithRetry<Metric>(
                    [this]() { return api_.fetchMetrics(); },
                    validateMetrics,
                    metricsCache_,
                    policy_
                );
            }
        );

        auto servicesFuture = std::async(
            std::launch::async,
            [this]() {
                return loadWithRetry<Service>(
                    [this]() { return api_.fetchServices(); },
                    validateServices,
                    servicesCache_,
                    policy_
                );
            }
        );

        auto incidentsFuture = std::async(
            std::launch::async,
            [this]() {
                return loadWithRetry<Incident>(
                    [this]() { return api_.fetchIncidents(); },
                    validateIncidents,
                    incidentsCache_,
                    policy_
                );
            }
        );

        auto metricsResult = metricsFuture.get();
        auto servicesResult = servicesFuture.get();
        auto incidentsResult = incidentsFuture.get();

        snapshot_.metrics = std::move(metricsResult.records);
        snapshot_.services = std::move(servicesResult.records);
        snapshot_.incidents = std::move(incidentsResult.records);

        snapshot_.errors.clear();
        snapshot_.staleResources.clear();

        recordResourceState("metrics", metricsResult);
        recordResourceState("services", servicesResult);
        recordResourceState("incidents", incidentsResult);

        const bool noData =
            snapshot_.metrics.empty() &&
            snapshot_.services.empty() &&
            snapshot_.incidents.empty();

        if (noData) {
            snapshot_.phase = DashboardPhase::Failed;
        } else if (
            !snapshot_.errors.empty() ||
            !snapshot_.staleResources.empty()
        ) {
            snapshot_.phase = DashboardPhase::Degraded;
        } else {
            snapshot_.phase = DashboardPhase::Ready;
        }

        snapshot_.updatedAt = Clock::now();
        return snapshot_;
    }

    DashboardSummary summarize() const {
        DashboardSummary summary;
        summary.totalServices = snapshot_.services.size();

        for (const auto& service : snapshot_.services) {
            switch (service.status) {
                case ServiceStatus::Operational:
                    ++summary.operationalServices;
                    break;
                case ServiceStatus::Degraded:
                    ++summary.degradedServices;
                    break;
                case ServiceStatus::Down:
                    ++summary.unavailableServices;
                    break;
            }
        }

        summary.openIncidents = std::count_if(
            snapshot_.incidents.begin(),
            snapshot_.incidents.end(),
            [](const Incident& incident) {
                return incident.status != IncidentStatus::Resolved;
            }
        );

        if (summary.totalServices > 0) {
            summary.operationalPercentage =
                100.0 * static_cast<double>(summary.operationalServices) /
                static_cast<double>(summary.totalServices);
        }

        double totalErrorRate = 0.0;
        std::size_t errorRateCount = 0;

        for (const auto& metric : snapshot_.metrics) {
            if (metric.name == "error_rate") {
                totalErrorRate += metric.value;
                ++errorRateCount;
            }
        }

        if (errorRateCount > 0) {
            summary.averageErrorRate =
                totalErrorRate / static_cast<double>(errorRateCount);
        }

        return summary;
    }

    const DashboardSnapshot& snapshot() const {
        return snapshot_;
    }

private:
    template <typename T>
    void recordResourceState(
        const std::string& name,
        const ResourceResult<T>& result
    ) {
        if (!result.error.empty()) {
            snapshot_.errors.push_back(name + ": " + result.error);
        }

        if (result.stale) {
            snapshot_.staleResources.push_back(name);
        }
    }

    MockApiClient& api_;
    DashboardPolicy policy_;

    // Each cache belongs to one resource, avoiding cross-resource data mixing.
    std::vector<Metric> metricsCache_;
    std::vector<Service> servicesCache_;
    std::vector<Incident> incidentsCache_;

    DashboardSnapshot snapshot_;
};

void printDashboard(const DashboardService& dashboard) {
    const auto& snapshot = dashboard.snapshot();
    const auto summary = dashboard.summarize();

    std::cout << "\nAPI OPERATIONS DASHBOARD\n";
    std::cout << std::string(60, '=') << '\n';

    std::cout << "State: " << toString(snapshot.phase) << '\n';
    std::cout << "Services: " << summary.totalServices << '\n';
    std::cout << "Operational: " << summary.operationalServices << '\n';
    std::cout << "Degraded: " << summary.degradedServices << '\n';
    std::cout << "Unavailable: " << summary.unavailableServices << '\n';
    std::cout << "Operational percentage: "
              << std::fixed << std::setprecision(1)
              << summary.operationalPercentage << "%\n";

    std::cout << "Open incidents: " << summary.openIncidents << '\n';

    if (summary.averageErrorRate.has_value()) {
        std::cout << "Average error rate: "
                  << *summary.averageErrorRate << "%\n";
    }

    std::cout << "\nService inventory\n";
    for (const auto& service : snapshot.services) {
        std::cout << "  " << std::left << std::setw(26) << service.name
                  << std::setw(12) << toString(service.status)
                  << service.region << '\n';
    }

    std::cout << "\nMetrics\n";
    for (const auto& metric : snapshot.metrics) {
        std::cout << "  " << std::left << std::setw(16) << metric.serviceId
                  << std::setw(14) << metric.name
                  << std::right << metric.value << ' '
                  << metric.unit << '\n';
    }

    if (!snapshot.staleResources.empty()) {
        std::cout << "\nStale resources\n";
        for (const auto& resource : snapshot.staleResources) {
            std::cout << "  " << resource << '\n';
        }
    }

    if (!snapshot.errors.empty()) {
        std::cout << "\nResource errors\n";
        for (const auto& error : snapshot.errors) {
            std::cout << "  " << error << '\n';
        }
    }
}

int main() {
    try {
        MockApiClient api;

        DashboardPolicy policy;
        policy.maxAttempts = 3;
        policy.retryDelayMilliseconds = 10;

        DashboardService dashboard(api, policy);

        // The first incident request fails, and a retry succeeds.
        api.failNextIncidents(1);
        auto firstSnapshot = dashboard.refresh();
        printDashboard(dashboard);

        if (firstSnapshot.phase != DashboardPhase::Ready) {
            throw std::runtime_error("Expected a READY dashboard.");
        }

        // The next three incident requests fail. The prior valid response
        // remains available, but the dashboard reports degraded freshness.
        api.failNextIncidents(3);
        auto secondSnapshot = dashboard.refresh();
        printDashboard(dashboard);

        if (secondSnapshot.phase != DashboardPhase::Degraded) {
            throw std::runtime_error("Expected a DEGRADED dashboard.");
        }

        if (secondSnapshot.staleResources.empty()) {
            throw std::runtime_error("Expected a stale resource indicator.");
        }

        return 0;

    } catch (const std::exception& error) {
        std::cerr << "Dashboard failure: " << error.what() << '\n';
        return 1;
    }
}
