#include <algorithm>
#include <cmath>
#include <functional>
#include <iomanip>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using NumberFunction = std::function<double(double)>;

double greetLength(const std::string& name) {
    if (name.empty()) {
        throw std::invalid_argument("name cannot be empty");
    }

    return static_cast<double>(name.size());
}

double calculateTotal(double price, int quantity = 1) {
    if (!std::isfinite(price) || price < 0) {
        throw std::invalid_argument("price must be non-negative and finite");
    }

    if (quantity < 0) {
        throw std::invalid_argument("quantity cannot be negative");
    }

    return price * quantity;
}

double square(double value) {
    return value * value;
}

double applyOperation(double value, const NumberFunction& operation) {
    if (!operation) {
        throw std::invalid_argument("operation cannot be empty");
    }

    return operation(value);
}

NumberFunction makeMultiplier(double factor) {
    if (!std::isfinite(factor)) {
        throw std::invalid_argument("factor must be finite");
    }

    // The lambda captures factor by value, so the returned function owns its
    // required state independently of the stack frame that created it.
    return [factor](double value) {
        return value * factor;
    };
}

class Counter {
private:
    int count{0};

public:
    int next() {
        return ++count;
    }
};

struct Statistics {
    std::size_t count;
    double minimum;
    double maximum;
    double average;
};

Statistics summarize(const std::vector<double>& values) {
    if (values.empty()) {
        throw std::invalid_argument("values cannot be empty");
    }

    if (!std::all_of(values.begin(), values.end(),
                     [](double value) { return std::isfinite(value); })) {
        throw std::invalid_argument("all values must be finite");
    }

    const auto [minimumIterator, maximumIterator] =
        std::minmax_element(values.begin(), values.end());

    double total = 0.0;
    for (double value : values) {
        total += value;
    }

    return {
        values.size(),
        *minimumIterator,
        *maximumIterator,
        total / static_cast<double>(values.size())
    };
}

double divide(double dividend, double divisor) {
    if (divisor == 0.0) {
        throw std::domain_error("division by zero");
    }

    return dividend / divisor;
}

NumberFunction compose(NumberFunction first, NumberFunction second) {
    if (!first || !second) {
        throw std::invalid_argument("composition requires two valid functions");
    }

    return [first = std::move(first), second = std::move(second)](double value) {
        return second(first(value));
    };
}

double executePipeline(
    double value,
    const std::vector<NumberFunction>& operations
) {
    for (const auto& operation : operations) {
        if (!operation) {
            throw std::invalid_argument("pipeline contains an empty function");
        }

        value = operation(value);
    }

    return value;
}

class PayrollService {
private:
    double taxRate;

public:
    explicit PayrollService(double taxRate) : taxRate(taxRate) {
        if (!std::isfinite(taxRate) || taxRate < 0.0 || taxRate > 1.0) {
            throw std::invalid_argument("tax rate must be between 0 and 1");
        }
    }

    double grossPay(double salary, double bonus = 0.0) const {
        if (!std::isfinite(salary) || salary < 0.0) {
            throw std::invalid_argument("salary must be non-negative");
        }

        if (!std::isfinite(bonus) || bonus < 0.0) {
            throw std::invalid_argument("bonus must be non-negative");
        }

        return salary + bonus;
    }

    double netPay(double salary, double bonus = 0.0) const {
        return grossPay(salary, bonus) * (1.0 - taxRate);
    }
};

std::function<bool(double)> createRangeValidator(
    double minimum,
    double maximum
) {
    if (minimum > maximum) {
        throw std::invalid_argument("minimum cannot exceed maximum");
    }

    return [minimum, maximum](double value) {
        return std::isfinite(value) &&
               value >= minimum &&
               value <= maximum;
    };
}

void demonstrateExceptionHandling() {
    try {
        std::cout << "10 / 2 = " << divide(10, 2) << '\n';
        std::cout << "10 / 0 = " << divide(10, 0) << '\n';
    } catch (const std::exception& error) {
        std::cout << "Handled failure: " << error.what() << '\n';
    }
}

int main() {
    std::cout << std::fixed << std::setprecision(2);

    std::cout << "=== Function return values ===\n";
    std::cout << "Name length: " << greetLength("Atul") << '\n';
    std::cout << "Total: " << calculateTotal(250.0, 3) << '\n';
    std::cout << "Default quantity: " << calculateTotal(100.0) << '\n';

    std::cout << "\n=== Functions as values ===\n";
    NumberFunction operation = square;
    std::cout << "Square: " << applyOperation(8.0, operation) << '\n';

    NumberFunction doubleValue = [](double value) {
        return value * 2.0;
    };
    std::cout << "Double: " << applyOperation(8.0, doubleValue) << '\n';

    std::cout << "\n=== Closure implemented with a lambda ===\n";
    NumberFunction triple = makeMultiplier(3.0);
    std::cout << "Triple: " << triple(10.0) << '\n';

    std::cout << "\n=== Stateful object method ===\n";
    Counter counter;
    std::cout << counter.next() << '\n';
    std::cout << counter.next() << '\n';
    std::cout << counter.next() << '\n';

    std::cout << "\n=== Data-processing function ===\n";
    std::vector<double> values{10.0, 20.0, 30.0, 40.0};
    const Statistics statistics = summarize(values);

    std::cout << "Count: " << statistics.count << '\n';
    std::cout << "Minimum: " << statistics.minimum << '\n';
    std::cout << "Maximum: " << statistics.maximum << '\n';
    std::cout << "Average: " << statistics.average << '\n';

    std::cout << "\n=== Composition ===\n";
    NumberFunction addTen = [](double value) {
        return value + 10.0;
    };

    NumberFunction multiplyTwo = [](double value) {
        return value * 2.0;
    };

    NumberFunction composed = compose(addTen, multiplyTwo);
    std::cout << "compose(addTen, multiplyTwo)(5) = "
              << composed(5.0) << '\n';

    std::cout << "\n=== Pipeline ===\n";
    std::vector<NumberFunction> pipeline{
        addTen,
        multiplyTwo,
        square
    };

    std::cout << "Pipeline result: "
              << executePipeline(5.0, pipeline) << '\n';

    std::cout << "\n=== Function returning a function ===\n";
    const auto percentageValidator = createRangeValidator(0.0, 100.0);

    for (double value : {-5.0, 25.0, 100.0, 110.0}) {
        std::cout << value << " -> "
                  << std::boolalpha
                  << percentageValidator(value)
                  << '\n';
    }

    std::cout << "\n=== Enterprise-style service methods ===\n";
    PayrollService payroll(0.20);
    std::cout << "Gross pay: "
              << payroll.grossPay(60000.0, 5000.0)
              << '\n';

    std::cout << "Net pay: "
              << payroll.netPay(60000.0, 5000.0)
              << '\n';

    std::cout << "\n=== Failure handling ===\n";
    demonstrateExceptionHandling();

    try {
        calculateTotal(-10.0, 2);
    } catch (const std::exception& error) {
        std::cout << "Validation failure: " << error.what() << '\n';
    }

    return 0;
}
