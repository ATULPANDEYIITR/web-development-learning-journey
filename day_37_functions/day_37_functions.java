import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.function.DoubleFunction;
import java.util.function.DoublePredicate;
import java.util.function.Function;

public class FunctionsDemo {

    static String greet(String name) {
        Objects.requireNonNull(name, "name cannot be null");

        if (name.isBlank()) {
            throw new IllegalArgumentException("name cannot be blank");
        }

        return "Hello, " + name + "!";
    }

    static double calculateTotal(double price, int quantity) {
        if (!Double.isFinite(price) || price < 0) {
            throw new IllegalArgumentException("price must be non-negative and finite");
        }

        if (quantity < 0) {
            throw new IllegalArgumentException("quantity cannot be negative");
        }

        return price * quantity;
    }

    static double calculateTotal(double price) {
        return calculateTotal(price, 1);
    }

    static double square(double value) {
        return value * value;
    }

    static double applyOperation(
            double value,
            DoubleFunction<Double> operation
    ) {
        Objects.requireNonNull(operation, "operation cannot be null");
        return operation.apply(value);
    }

    static Function<Double, Double> makeMultiplier(double factor) {
        if (!Double.isFinite(factor)) {
            throw new IllegalArgumentException("factor must be finite");
        }

        return value -> value * factor;
    }

    static String demonstrateScope() {
        String outerValue = "service scope";

        class ScopeReader {
            String read() {
                String innerValue = "method scope";
                return outerValue + " | " + innerValue;
            }
        }

        return new ScopeReader().read();
    }

    static Statistics summarize(List<Double> values) {
        if (values == null || values.isEmpty()) {
            throw new IllegalArgumentException("values cannot be empty");
        }

        double minimum = Double.POSITIVE_INFINITY;
        double maximum = Double.NEGATIVE_INFINITY;
        double total = 0.0;

        for (Double value : values) {
            if (value == null || !Double.isFinite(value)) {
                throw new IllegalArgumentException("values must be finite");
            }

            minimum = Math.min(minimum, value);
            maximum = Math.max(maximum, value);
            total += value;
        }

        return new Statistics(
                values.size(),
                minimum,
                maximum,
                total / values.size()
        );
    }

    record Statistics(
            int count,
            double minimum,
            double maximum,
            double average
    ) {}

    static Function<Double, Double> compose(
            Function<Double, Double> first,
            Function<Double, Double> second
    ) {
        Objects.requireNonNull(first);
        Objects.requireNonNull(second);

        return value -> second.apply(first.apply(value));
    }

    static double executePipeline(
            double value,
            List<DoubleFunction<Double>> operations
    ) {
        double result = value;

        for (DoubleFunction<Double> operation : operations) {
            Objects.requireNonNull(operation);
            result = operation.apply(result);
        }

        return result;
    }

    static DoublePredicate createRangeValidator(
            double minimum,
            double maximum
    ) {
        if (!Double.isFinite(minimum) || !Double.isFinite(maximum)) {
            throw new IllegalArgumentException("bounds must be finite");
        }

        if (minimum > maximum) {
            throw new IllegalArgumentException(
                    "minimum cannot exceed maximum"
            );
        }

        return value ->
                Double.isFinite(value) &&
                value >= minimum &&
                value <= maximum;
    }

    static final class PayrollService {
        private final double taxRate;

        PayrollService(double taxRate) {
            if (!Double.isFinite(taxRate) ||
                    taxRate < 0 ||
                    taxRate > 1) {
                throw new IllegalArgumentException(
                        "tax rate must be between 0 and 1"
                );
            }

            this.taxRate = taxRate;
        }

        double grossPay(Employee employee, double bonus) {
            Objects.requireNonNull(employee);

            if (employee.salary() < 0 || bonus < 0) {
                throw new IllegalArgumentException(
                        "salary and bonus cannot be negative"
                );
            }

            return employee.salary() + bonus;
        }

        double netPay(Employee employee, double bonus) {
            return grossPay(employee, bonus) * (1 - taxRate);
        }
    }

    record Employee(String name, double salary) {
        Employee {
            Objects.requireNonNull(name, "name cannot be null");

            if (name.isBlank()) {
                throw new IllegalArgumentException(
                        "name cannot be blank"
                );
            }

            if (!Double.isFinite(salary) || salary < 0) {
                throw new IllegalArgumentException(
                        "salary must be non-negative and finite"
                );
            }
        }
    }

    static double divide(double dividend, double divisor) {
        if (divisor == 0) {
            throw new ArithmeticException("division by zero");
        }

        return dividend / divisor;
    }

    public static void main(String[] args) {
        System.out.println("=== Function declaration ===");
        System.out.println(greet("Atul"));

        System.out.println("\n=== Parameters and return values ===");
        System.out.println(calculateTotal(250, 3));
        System.out.println(calculateTotal(100));

        System.out.println("\n=== Lambda function ===");
        DoubleFunction<Double> squareFunction =
                FunctionsDemo::square;

        System.out.println(
                applyOperation(8, squareFunction)
        );

        DoubleFunction<Double> tripleFunction =
                value -> value * 3;

        System.out.println(
                applyOperation(8, tripleFunction)
        );

        System.out.println("\n=== Function returned from a method ===");
        Function<Double, Double> triple =
                makeMultiplier(3);

        System.out.println(triple.apply(10.0));

        System.out.println("\n=== Scope ===");
        System.out.println(demonstrateScope());

        System.out.println("\n=== Collection processing ===");
        List<Double> values =
                new ArrayList<>(List.of(10.0, 20.0, 30.0, 40.0));

        Statistics statistics = summarize(values);

        System.out.println("Count: " + statistics.count());
        System.out.println("Minimum: " + statistics.minimum());
        System.out.println("Maximum: " + statistics.maximum());
        System.out.println("Average: " + statistics.average());

        System.out.println("\n=== Composition ===");
        Function<Double, Double> addTen =
                value -> value + 10;

        Function<Double, Double> multiplyTwo =
                value -> value * 2;

        Function<Double, Double> composed =
                compose(addTen, multiplyTwo);

        System.out.println(composed.apply(5.0));

        System.out.println("\n=== Pipeline ===");
        List<DoubleFunction<Double>> pipeline = List.of(
                addTen::apply,
                multiplyTwo::apply,
                FunctionsDemo::square
        );

        System.out.println(
                executePipeline(5.0, pipeline)
        );

        System.out.println("\n=== Explicit validation function ===");
        DoublePredicate percentageValidator =
                createRangeValidator(0, 100);

        for (double value : new double[]{-5, 25, 100, 110}) {
            System.out.println(
                    value + " -> " + percentageValidator.test(value)
            );
        }

        System.out.println("\n=== Enterprise service methods ===");
        Employee employee = new Employee("Ravi", 60000);
        PayrollService payroll = new PayrollService(0.20);

        System.out.println(
                "Gross: " + payroll.grossPay(employee, 5000)
        );

        System.out.println(
                "Net: " + payroll.netPay(employee, 5000)
        );

        System.out.println("\n=== Failure handling ===");
        try {
            divide(10, 0);
        } catch (ArithmeticException error) {
            System.out.println(
                    "Handled error: " + error.getMessage()
            );
        }

        try {
            calculateTotal(-10, 2);
        } catch (IllegalArgumentException error) {
            System.out.println(
                    "Validation error: " + error.getMessage()
            );
        }
    }
}
