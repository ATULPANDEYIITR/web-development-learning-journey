#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;

struct ServiceSample {
    string name;
    double latencyMs;
    int failedRequests;
    bool healthy;
};

class DeploymentMonitor {
private:
    vector<ServiceSample> samples;

    static void validate(const ServiceSample& sample) {
        if (sample.name.empty()) {
            throw invalid_argument("Service name cannot be empty");
        }
        if (!isfinite(sample.latencyMs) || sample.latencyMs < 0.0) {
            throw invalid_argument("Latency must be finite and non-negative");
        }
        if (sample.failedRequests < 0) {
            throw invalid_argument("Failure count cannot be negative");
        }
    }

public:
    explicit DeploymentMonitor(vector<ServiceSample> input)
        : samples(move(input)) {
        for (const auto& sample : samples) {
            validate(sample);
        }
    }

    vector<ServiceSample> slowServices(double thresholdMs) const {
        if (!isfinite(thresholdMs) || thresholdMs < 0.0) {
            throw invalid_argument("Threshold must be finite and non-negative");
        }

        vector<ServiceSample> result;
        copy_if(samples.begin(), samples.end(), back_inserter(result),
                [thresholdMs](const ServiceSample& sample) {
                    return sample.latencyMs > thresholdMs;
                });
        return result;
    }

    optional<ServiceSample> firstUnhealthy() const {
        auto found = find_if(samples.begin(), samples.end(),
                             [](const ServiceSample& sample) {
                                 return !sample.healthy;
                             });

        if (found == samples.end()) {
            return nullopt;
        }
        return *found;
    }

    bool anyCriticalLatency(double thresholdMs) const {
        return any_of(samples.begin(), samples.end(),
                      [thresholdMs](const ServiceSample& sample) {
                          return sample.latencyMs >= thresholdMs;
                      });
    }

    bool allHealthy() const {
        // An empty range satisfies all_of mathematically. This monitoring
        // policy treats an empty deployment as unverified, not healthy.
        return !samples.empty() &&
               all_of(samples.begin(), samples.end(),
                      [](const ServiceSample& sample) {
                          return sample.healthy;
                      });
    }

    double averageLatency() const {
        if (samples.empty()) {
            return 0.0;
        }

        const double total = accumulate(
            samples.begin(), samples.end(), 0.0,
            [](double sum, const ServiceSample& sample) {
                return sum + sample.latencyMs;
            });

        return total / static_cast<double>(samples.size());
    }

    int totalFailures() const {
        return accumulate(
            samples.begin(), samples.end(), 0,
            [](int total, const ServiceSample& sample) {
                return total + sample.failedRequests;
            });
    }

    vector<string> uniqueServiceNames() const {
        vector<string> result;
        unordered_set<string> seen;

        for (const auto& sample : samples) {
            // The vector preserves first-seen order; the hash set avoids
            // repeatedly scanning all previously encountered names.
            if (seen.insert(sample.name).second) {
                result.push_back(sample.name);
            }
        }
        return result;
    }

    void printReport() const {
        cout << fixed << setprecision(2);
        cout << "Service count: " << samples.size() << '\n';
        cout << "Average latency: " << averageLatency() << " ms\n";
        cout << "Total failed requests: " << totalFailures() << '\n';
        cout << "All healthy: " << boolalpha << allHealthy() << '\n';

        const auto slow = slowServices(100.0);
        cout << "Slow services:";
        for (const auto& sample : slow) {
            cout << ' ' << sample.name << '(' << sample.latencyMs << " ms)";
        }
        cout << '\n';

        const auto unhealthy = firstUnhealthy();
        cout << "First unhealthy service: ";
        if (unhealthy.has_value()) {
            cout << unhealthy->name;
        } else {
            cout << "none";
        }
        cout << '\n';

        cout << "Critical latency present: "
             << anyCriticalLatency(150.0) << '\n';

        cout << "Unique service names:";
        for (const auto& name : uniqueServiceNames()) {
            cout << ' ' << name;
        }
        cout << '\n';
    }
};

int main() {
    try {
        cout << "Deployment latency analysis\n";

        vector<ServiceSample> productionSamples{
            {"gateway", 45.5, 2, true},
            {"billing", 135.0, 8, true},
            {"inventory", 88.0, 0, false},
            {"search", 172.5, 15, true},
            {"gateway", 52.0, 1, true}
        };

        DeploymentMonitor production(move(productionSamples));
        production.printReport();

        cout << "\nEmpty deployment policy\n";
        DeploymentMonitor empty({});
        empty.printReport();

        cout << "\nInvalid sample handling\n";
        try {
            DeploymentMonitor invalid({
                {"payments", -5.0, 0, true}
            });
            invalid.printReport();
        } catch (const invalid_argument& error) {
            cerr << "Rejected invalid data: " << error.what() << '\n';
        }

        cout << "\nThreshold validation\n";
        try {
            production.slowServices(-1.0);
        } catch (const invalid_argument& error) {
            cerr << "Rejected threshold: " << error.what() << '\n';
        }
    } catch (const exception& error) {
        cerr << "Monitoring error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
