import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

/*
 * Enterprise scenario: an employee directory with role-specific behavior.
 *
 * The model uses:
 * - constructors to establish valid object state
 * - private fields to protect invariants
 * - inheritance for shared employee behavior
 * - static members for organization-wide state
 * - records for immutable value objects
 * - interfaces for explicit capability contracts
 * - exceptions for invalid domain operations
 */

public class ClassManagementDemo {

    public enum EmploymentStatus {
        ACTIVE,
        SUSPENDED,
        TERMINATED
    }

    public enum Department {
        ENGINEERING,
        SECURITY,
        FINANCE,
        OPERATIONS
    }

    public record EmployeeBadge(String badgeId, Department department) {
        public EmployeeBadge {
            if (badgeId == null || badgeId.isBlank()) {
                throw new IllegalArgumentException("Badge ID is required.");
            }
            Objects.requireNonNull(department, "Department is required.");
        }
    }

    public interface Reviewable {
        String reviewRole();
        boolean canApproveProductionChange();
    }

    public static abstract class Employee {
        private static int nextEmployeeId = 7000;
        private static int activeEmployeeCount = 0;
        private static final String ORGANIZATION = "Atlas Enterprise";

        private final int employeeId;
        private final String name;
        private double salary;
        private EmploymentStatus status;
        private final EmployeeBadge badge;

        protected Employee(
                String name,
                double salary,
                EmployeeBadge badge) {

            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Employee name is required.");
            }

            if (!Double.isFinite(salary) || salary < 0) {
                throw new IllegalArgumentException(
                        "Salary must be a finite non-negative number.");
            }

            this.employeeId = nextEmployeeId++;
            this.name = name.trim();
            this.salary = salary;
            this.status = EmploymentStatus.ACTIVE;
            this.badge = Objects.requireNonNull(badge, "Badge is required.");

            activeEmployeeCount++;
        }

        public final int employeeId() {
            return employeeId;
        }

        public final String name() {
            return name;
        }

        public final double salary() {
            return salary;
        }

        public final EmploymentStatus status() {
            return status;
        }

        public final EmployeeBadge badge() {
            return badge;
        }

        protected final void requireActive() {
            if (status != EmploymentStatus.ACTIVE) {
                throw new IllegalStateException(
                        "Operation requires an active employee.");
            }
        }

        public final void increaseSalary(double amount) {
            requireActive();

            if (!Double.isFinite(amount) || amount <= 0) {
                throw new IllegalArgumentException(
                        "Salary increase must be positive.");
            }

            salary = Math.round((salary + amount) * 100.0) / 100.0;
        }

        public final void suspend() {
            if (status != EmploymentStatus.ACTIVE) {
                throw new IllegalStateException(
                        "Only active employees can be suspended.");
            }

            status = EmploymentStatus.SUSPENDED;
            activeEmployeeCount--;
        }

        public final void terminate() {
            if (status == EmploymentStatus.TERMINATED) {
                throw new IllegalStateException("Employee is already terminated.");
            }

            if (status == EmploymentStatus.ACTIVE) {
                activeEmployeeCount--;
            }

            status = EmploymentStatus.TERMINATED;
        }

        public static int activeEmployeeCount() {
            return activeEmployeeCount;
        }

        public static String organization() {
            return ORGANIZATION;
        }

        public abstract String roleDescription();

        public abstract double annualBonus();
    }

    public static final class Engineer extends Employee implements Reviewable {
        private final String specialty;

        public Engineer(
                String name,
                double salary,
                EmployeeBadge badge,
                String specialty) {

            super(name, salary, badge);

            if (specialty == null || specialty.isBlank()) {
                activeEmployeeCount--;
                throw new IllegalArgumentException(
                        "Engineering specialty is required.");
            }

            this.specialty = specialty.trim();
        }

        public String specialty() {
            return specialty;
        }

        @Override
        public String roleDescription() {
            return specialty + " engineer";
        }

        @Override
        public double annualBonus() {
            return salary() * 0.12;
        }

        @Override
        public String reviewRole() {
            return "Technical reviewer";
        }

        @Override
        public boolean canApproveProductionChange() {
            return badge().department() == Department.ENGINEERING
                    || badge().department() == Department.SECURITY;
        }
    }

    public static final class Manager extends Employee implements Reviewable {
        private final List<Employee> directReports = new ArrayList<>();

        public Manager(
                String name,
                double salary,
                EmployeeBadge badge) {

            super(name, salary, badge);
        }

        public void assign(Employee employee) {
            requireActive();

            Objects.requireNonNull(employee, "Employee is required.");

            if (employee == this) {
                throw new IllegalArgumentException(
                        "An employee cannot report to themselves.");
            }

            if (employee.status() == EmploymentStatus.TERMINATED) {
                throw new IllegalStateException(
                        "Terminated employees cannot be assigned.");
            }

            if (!directReports.contains(employee)) {
                directReports.add(employee);
            }
        }

        public List<Employee> directReports() {
            return Collections.unmodifiableList(directReports);
        }

        @Override
        public String roleDescription() {
            return "People manager";
        }

        @Override
        public double annualBonus() {
            return salary() * 0.20;
        }

        @Override
        public String reviewRole() {
            return "Management reviewer";
        }

        @Override
        public boolean canApproveProductionChange() {
            return badge().department() == Department.OPERATIONS;
        }
    }

    public static final class PayrollService {
        public double totalAnnualBonus(List<? extends Employee> employees) {
            return employees.stream()
                    .filter(employee -> employee.status()
                            != EmploymentStatus.TERMINATED)
                    .mapToDouble(Employee::annualBonus)
                    .sum();
        }

        public boolean hasEligibleProductionApprover(
                List<? extends Employee> employees) {

            return employees.stream()
                    .filter(employee -> employee.status()
                            == EmploymentStatus.ACTIVE)
                    .filter(employee -> employee instanceof Reviewable)
                    .map(employee -> (Reviewable) employee)
                    .anyMatch(Reviewable::canApproveProductionChange);
        }
    }

    private static void demonstrateDomainModel() {
        System.out.println("=== Enterprise class model ===");

        EmployeeBadge engineeringBadge =
                new EmployeeBadge("ENG-401", Department.ENGINEERING);

        EmployeeBadge operationsBadge =
                new EmployeeBadge("OPS-205", Department.OPERATIONS);

        Engineer engineer = new Engineer(
                "Ananya Singh",
                110000,
                engineeringBadge,
                "Platform Security");

        Manager manager = new Manager(
                "Rahul Mehta",
                140000,
                operationsBadge);

        manager.assign(engineer);

        System.out.println(
                engineer.name() + " -> " + engineer.roleDescription());

        System.out.println(
                manager.name() + " manages "
                        + manager.directReports().size()
                        + " employee(s).");

        engineer.increaseSalary(5000);

        System.out.printf(
                "Engineer salary: %.2f%n",
                engineer.salary());

        System.out.printf(
                "Engineer annual bonus: %.2f%n",
                engineer.annualBonus());
    }

    private static void demonstrateStaticMembers() {
        System.out.println("\n=== Static class state ===");

        System.out.println("Organization: " + Employee.organization());
        System.out.println(
                "Active employees: " + Employee.activeEmployeeCount());

        EmployeeBadge badge =
                new EmployeeBadge("FIN-900", Department.FINANCE);

        Engineer temporary = new Engineer(
                "Temporary Engineer",
                70000,
                badge,
                "Data Engineering");

        System.out.println(
                "After construction: "
                        + Employee.activeEmployeeCount());

        temporary.terminate();

        System.out.println(
                "After termination: "
                        + Employee.activeEmployeeCount());
    }

    private static void demonstratePolymorphism() {
        System.out.println("\n=== Polymorphic behavior ===");

        EmployeeBadge securityBadge =
                new EmployeeBadge("SEC-777", Department.SECURITY);

        EmployeeBadge operationsBadge =
                new EmployeeBadge("OPS-888", Department.OPERATIONS);

        List<Employee> employees = List.of(
                new Engineer(
                        "Vikram Rao",
                        120000,
                        securityBadge,
                        "Application Security"),
                new Manager(
                        "Sonia Kapoor",
                        135000,
                        operationsBadge));

        for (Employee employee : employees) {
            System.out.printf(
                    "%s | %s | bonus=%.2f%n",
                    employee.name(),
                    employee.roleDescription(),
                    employee.annualBonus());
        }

        PayrollService payroll = new PayrollService();

        System.out.printf(
                "Combined annual bonus: %.2f%n",
                payroll.totalAnnualBonus(employees));

        System.out.println(
                "Production approver available: "
                        + payroll.hasEligibleProductionApprover(employees));
    }

    private static void demonstrateInvalidStates() {
        System.out.println("\n=== Invalid state handling ===");

        try {
            new Engineer(
                    "",
                    100000,
                    new EmployeeBadge("BAD-1", Department.ENGINEERING),
                    "Cloud");
        } catch (IllegalArgumentException exception) {
            System.out.println("Invalid construction: "
                    + exception.getMessage());
        }

        try {
            EmployeeBadge badge =
                    new EmployeeBadge("OPS-001", Department.OPERATIONS);

            Engineer engineer = new Engineer(
                    "Valid Employee",
                    80000,
                    badge,
                    "Infrastructure");

            engineer.terminate();
            engineer.increaseSalary(1000);
        } catch (IllegalStateException exception) {
            System.out.println("Invalid lifecycle operation: "
                    + exception.getMessage());
        }

        try {
            new EmployeeBadge("", Department.FINANCE);
        } catch (IllegalArgumentException exception) {
            System.out.println("Invalid value object: "
                    + exception.getMessage());
        }
    }

    public static void main(String[] args) {
        demonstrateDomainModel();
        demonstrateStaticMembers();
        demonstratePolymorphism();
        demonstrateInvalidStates();

        System.out.println(
                "\nRemaining active employees: "
                        + Employee.activeEmployeeCount());
    }
}
