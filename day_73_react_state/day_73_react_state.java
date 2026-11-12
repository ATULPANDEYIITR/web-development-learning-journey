import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Consumer;
import java.util.function.UnaryOperator;
import java.util.stream.Collectors;

/*
 * REACT STATE MANAGEMENT
 *
 * Enterprise-oriented state management model.
 *
 * Concepts:
 * - Initial state
 * - State updates
 * - Functional updates
 * - Immutable state
 * - Derived state
 * - Controlled components
 * - Validation
 * - State transitions
 * - Event listeners
 * - Error handling
 */

public class Main {

    /* =====================================================
       CUSTOM EXCEPTIONS
       ===================================================== */

    static class StateException extends RuntimeException {
        public StateException(String message) {
            super(message);
        }
    }

    static class ValidationException
            extends RuntimeException {

        public ValidationException(String message) {
            super(message);
        }
    }


    /* =====================================================
       STATE SNAPSHOT
       ===================================================== */

    record StateSnapshot<T>(
            long version,
            T value
    ) {}


    /* =====================================================
       GENERIC STATE CONTAINER
       ===================================================== */

    static final class StateContainer<T> {

        private T state;
        private long version;

        private final List<StateSnapshot<T>> history =
                new ArrayList<>();

        private final List<Consumer<T>> listeners =
                new ArrayList<>();

        public StateContainer(T initialState) {
            this.state = Objects.requireNonNull(
                    initialState,
                    "Initial state cannot be null."
            );

            this.version = 0;
        }

        public synchronized T getState() {
            return state;
        }

        public synchronized long getVersion() {
            return version;
        }

        public synchronized void subscribe(
                Consumer<T> listener
        ) {
            listeners.add(
                    Objects.requireNonNull(listener)
            );
        }

        public synchronized void unsubscribe(
                Consumer<T> listener
        ) {
            listeners.remove(listener);
        }

        public synchronized T setState(T nextState) {
            Objects.requireNonNull(
                    nextState,
                    "New state cannot be null."
            );

            if (Objects.equals(state, nextState)) {
                return state;
            }

            history.add(
                    new StateSnapshot<>(version, state)
            );

            state = nextState;
            version++;

            notifyListeners();

            return state;
        }

        public synchronized T update(
                UnaryOperator<T> updater
        ) {
            Objects.requireNonNull(
                    updater,
                    "Updater cannot be null."
            );

            T nextState = updater.apply(state);

            return setState(nextState);
        }

        public synchronized Optional<T> undo() {
            if (history.isEmpty()) {
                return Optional.empty();
            }

            StateSnapshot<T> previous =
                    history.remove(history.size() - 1);

            state = previous.value();
            version++;

            notifyListeners();

            return Optional.of(state);
        }

        private void notifyListeners() {
            // Copy listeners to avoid modification during iteration.
            List<Consumer<T>> currentListeners =
                    List.copyOf(listeners);

            for (Consumer<T> listener : currentListeners) {
                try {
                    listener.accept(state);
                } catch (RuntimeException error) {
                    System.err.println(
                            "State listener failed: "
                                    + error.getMessage()
                    );
                }
            }
        }
    }


    /* =====================================================
       COUNTER STATE
       ===================================================== */

    static void demonstrateCounter() {
        System.out.println("\n--- Counter State ---");

        StateContainer<Integer> counter =
                new StateContainer<>(0);

        counter.subscribe(
                value -> System.out.println(
                        "Counter changed: " + value
                )
        );

        counter.update(previous -> previous + 1);

        counter.update(previous -> previous + 1);

        counter.update(previous -> previous + 5);

        System.out.println(
                "Final count: " + counter.getState()
        );

        System.out.println(
                "Version: " + counter.getVersion()
        );

        counter.undo();

        System.out.println(
                "After undo: " + counter.getState()
        );
    }


    /* =====================================================
       USER DOMAIN MODEL
       ===================================================== */

    record User(
            String username,
            String email,
            int age,
            boolean acceptedTerms
    ) {
        public User {
            Objects.requireNonNull(username);
            Objects.requireNonNull(email);

            if (username.isBlank() || username.length() > 50) {
                throw new ValidationException(
                        "Invalid username."
                );
            }

            if (
                    !email.matches(
                            "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$"
                    ) ||
                    email.length() > 254
            ) {
                throw new ValidationException(
                        "Invalid email address."
                );
            }

            if (age < 18 || age > 120) {
                throw new ValidationException(
                        "Age must be between 18 and 120."
                );
            }
        }
    }


    /* =====================================================
       CONTROLLED FORM SERVICE
       ===================================================== */

    static final class RegistrationService {

        private final StateContainer<User> formState;

        public RegistrationService() {
            User initial = new User(
                    "InitialUser",
                    "initial@example.com",
                    18,
                    false
            );

            formState = new StateContainer<>(initial);
        }

        public void updateUsername(String username) {
            User previous = formState.getState();

            formState.setState(
                    new User(
                            username,
                            previous.email(),
                            previous.age(),
                            previous.acceptedTerms()
                    )
            );
        }

        public void updateEmail(String email) {
            User previous = formState.getState();

            formState.setState(
                    new User(
                            previous.username(),
                            email,
                            previous.age(),
                            previous.acceptedTerms()
                    )
            );
        }

        public void updateAge(int age) {
            User previous = formState.getState();

            formState.setState(
                    new User(
                            previous.username(),
                            previous.email(),
                            age,
                            previous.acceptedTerms()
                    )
            );
        }

        public void acceptTerms(boolean accepted) {
            User previous = formState.getState();

            formState.setState(
                    new User(
                            previous.username(),
                            previous.email(),
                            previous.age(),
                            accepted
                    )
            );
        }

        public boolean canSubmit() {
            return formState.getState().acceptedTerms();
        }

        public User submit() {
            if (!canSubmit()) {
                throw new ValidationException(
                        "Terms acceptance is required."
                );
            }

            return formState.getState();
        }

        public User getForm() {
            return formState.getState();
        }
    }


    /* =====================================================
       SHOPPING CART DOMAIN
       ===================================================== */

    record Product(
            String id,
            String name,
            long priceInPaise,
            int quantity
    ) {
        public Product {
            Objects.requireNonNull(id);
            Objects.requireNonNull(name);

            if (
                    id.isBlank() ||
                    name.isBlank() ||
                    priceInPaise < 0 ||
                    quantity <= 0
            ) {
                throw new ValidationException(
                        "Invalid product."
                );
            }
        }
    }

    record CartState(
            List<Product> products
    ) {
        public CartState {
            products = List.copyOf(products);
        }
    }

    record CartSummary(
            int totalItems,
            long subtotalInPaise,
            boolean empty
    ) {}


    /* =====================================================
       CART SERVICE
       ===================================================== */

    static final class CartService {

        private final StateContainer<CartState> state =
                new StateContainer<>(
                        new CartState(List.of())
                );

        public CartState getState() {
            return state.getState();
        }

        public void addProduct(Product product) {
            Objects.requireNonNull(product);

            state.update(previous -> {
                List<Product> next =
                        new ArrayList<>(previous.products());

                for (int i = 0; i < next.size(); i++) {
                    Product existing = next.get(i);

                    if (existing.id().equals(product.id())) {
                        int quantity = Math.addExact(
                                existing.quantity(),
                                product.quantity()
                        );

                        next.set(
                                i,
                                new Product(
                                        existing.id(),
                                        existing.name(),
                                        existing.priceInPaise(),
                                        quantity
                                )
                        );

                        return new CartState(next);
                    }
                }

                next.add(product);

                return new CartState(next);
            });
        }

        public void removeProduct(String productId) {
            Objects.requireNonNull(productId);

            state.update(previous -> {
                List<Product> next =
                        previous.products()
                                .stream()
                                .filter(product ->
                                        !product.id().equals(productId)
                                )
                                .collect(Collectors.toList());

                if (
                        next.size() ==
                        previous.products().size()
                ) {
                    throw new StateException(
                            "Product not found."
                    );
                }

                return new CartState(next);
            });
        }

        public CartSummary deriveSummary() {
            CartState current = getState();

            int totalItems = current.products()
                    .stream()
                    .mapToInt(Product::quantity)
                    .sum();

            long subtotal = current.products()
                    .stream()
                    .mapToLong(product ->
                            Math.multiplyExact(
                                    product.priceInPaise(),
                                    product.quantity()
                            )
                    )
                    .reduce(0L, Math::addExact);

            return new CartSummary(
                    totalItems,
                    subtotal,
                    current.products().isEmpty()
            );
        }

        public void printCart() {
            for (Product product : getState().products()) {
                System.out.println(
                        product.name()
                                + " | Quantity: "
                                + product.quantity()
                                + " | Price in paise: "
                                + product.priceInPaise()
                );
            }

            CartSummary summary = deriveSummary();

            System.out.println(
                    "Total items: " + summary.totalItems()
            );

            System.out.println(
                    "Subtotal: ₹"
                            + String.format(
                                    "%.2f",
                                    summary.subtotalInPaise() / 100.0
                            )
            );

            System.out.println(
                    "Cart empty: " + summary.empty()
            );
        }
    }


    /* =====================================================
       NESTED STATE WITH IMMUTABLE RECORDS
       ===================================================== */

    record Address(
            String city,
            String country
    ) {}

    record Profile(
            String name,
            Address address
    ) {}

    static void demonstrateNestedState() {
        System.out.println("\n--- Nested State ---");

        Profile original = new Profile(
                "Atul",
                new Address("Lucknow", "India")
        );

        Profile updated = new Profile(
                original.name(),
                new Address("Patna", original.address().country())
        );

        System.out.println(
                "Original city: " + original.address().city()
        );

        System.out.println(
                "Updated city: " + updated.address().city()
        );
    }


    /* =====================================================
       CONTROLLED FORM EXECUTION
       ===================================================== */

    static void demonstrateControlledForm() {
        System.out.println("\n--- Controlled Form ---");

        RegistrationService registration =
                new RegistrationService();

        registration.updateUsername("Atul");
        registration.updateEmail("atul@example.com");
        registration.updateAge(28);
        registration.acceptTerms(true);

        System.out.println(
                "Registration: " + registration.submit()
        );

        System.out.println(
                "Can submit: " + registration.canSubmit()
        );
    }


    /* =====================================================
       SHOPPING CART EXECUTION
       ===================================================== */

    static void demonstrateShoppingCart() {
        System.out.println("\n--- Shopping Cart ---");

        CartService cart = new CartService();

        cart.addProduct(
                new Product(
                        "P001",
                        "Mechanical Keyboard",
                        249900,
                        1
                )
        );

        cart.addProduct(
                new Product(
                        "P002",
                        "Wireless Mouse",
                        99900,
                        2
                )
        );

        cart.addProduct(
                new Product(
                        "P001",
                        "Mechanical Keyboard",
                        249900,
                        1
                )
        );

        cart.printCart();

        cart.removeProduct("P002");

        System.out.println("\nAfter removing mouse:");

        cart.printCart();
    }


    /* =====================================================
       ERROR HANDLING
       ===================================================== */

    static void demonstrateErrors() {
        System.out.println("\n--- Error Handling ---");

        try {
            new Product(
                    "P003",
                    "Invalid Product",
                    -500,
                    1
            );
        } catch (ValidationException error) {
            System.out.println(
                    "Validation failure: "
                            + error.getMessage()
            );
        }

        try {
            RegistrationService registration =
                    new RegistrationService();

            registration.submit();
        } catch (ValidationException error) {
            System.out.println(
                    "Submission rejected: "
                            + error.getMessage()
            );
        }
    }


    /* =====================================================
       MAIN
       ===================================================== */

    public static void main(String[] args) {
        try {
            demonstrateCounter();

            demonstrateControlledForm();

            demonstrateShoppingCart();

            demonstrateNestedState();

            demonstrateErrors();

            System.out.println(
                    "\nReact State management concepts demonstrated."
            );
        } catch (RuntimeException error) {
            System.err.println(
                    "Application error: " + error.getMessage()
            );

            System.exit(1);
        }
    }
}
