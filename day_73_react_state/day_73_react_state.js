'use strict';

/*
 * REACT STATE MANAGEMENT
 *
 * React-specific implementation using:
 * useState
 * Functional state updates
 * Derived state
 * Controlled components
 * Immutable object and array updates
 * Event handlers
 * Form validation
 * Asynchronous event handling
 *
 * Run this file in a React application.
 */

import React, { useState } from 'react';


/* =========================================================
   1. COUNTER: BASIC useState AND STATE UPDATES
   ========================================================= */

export function Counter() {
    const [count, setCount] = useState(0);

    const increment = () => {
        setCount(previous => previous + 1);
    };

    const decrement = () => {
        setCount(previous => previous - 1);
    };

    const incrementMultipleTimes = () => {
        // Each functional update receives the latest queued state.
        setCount(previous => previous + 1);
        setCount(previous => previous + 1);
        setCount(previous => previous + 1);
    };

    const reset = () => {
        setCount(0);
    };

    return (
        <section>
            <h2>Counter</h2>

            <p>Current count: {count}</p>

            <button onClick={increment}>
                Increment
            </button>

            <button onClick={decrement}>
                Decrement
            </button>

            <button onClick={incrementMultipleTimes}>
                Increment by 3
            </button>

            <button onClick={reset}>
                Reset
            </button>
        </section>
    );
}


/* =========================================================
   2. CONTROLLED COMPONENTS
   ========================================================= */

export function ControlledForm() {
    const [form, setForm] = useState({
        username: '',
        email: '',
        age: '',
        acceptedTerms: false
    });

    const [errors, setErrors] = useState({});

    const [submitted, setSubmitted] = useState(false);

    function handleChange(event) {
        const { name, value, type, checked } = event.target;

        const nextValue = type === 'checkbox'
            ? checked
            : value;

        setForm(previous => ({
            ...previous,
            [name]: nextValue
        }));

        setErrors(previous => ({
            ...previous,
            [name]: ''
        }));

        setSubmitted(false);
    }

    function validate() {
        const nextErrors = {};

        if (!form.username.trim()) {
            nextErrors.username = 'Username is required.';
        } else if (form.username.trim().length > 50) {
            nextErrors.username = 'Username is too long.';
        }

        const emailPattern =
            /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!emailPattern.test(form.email)) {
            nextErrors.email = 'Enter a valid email address.';
        }

        const age = Number(form.age);

        if (
            !Number.isInteger(age) ||
            age < 18 ||
            age > 120
        ) {
            nextErrors.age = 'Age must be between 18 and 120.';
        }

        if (!form.acceptedTerms) {
            nextErrors.acceptedTerms =
                'Terms must be accepted.';
        }

        setErrors(nextErrors);

        return Object.keys(nextErrors).length === 0;
    }

    function handleSubmit(event) {
        event.preventDefault();

        if (!validate()) {
            setSubmitted(false);
            return;
        }

        setSubmitted(true);

        console.log('Validated form:', form);
    }

    return (
        <section>
            <h2>Controlled Registration Form</h2>

            <form onSubmit={handleSubmit} noValidate>
                <div>
                    <label htmlFor="username">
                        Username
                    </label>

                    <input
                        id="username"
                        name="username"
                        value={form.username}
                        onChange={handleChange}
                        maxLength={50}
                    />

                    {errors.username && (
                        <p role="alert">
                            {errors.username}
                        </p>
                    )}
                </div>

                <div>
                    <label htmlFor="email">
                        Email
                    </label>

                    <input
                        id="email"
                        name="email"
                        type="email"
                        value={form.email}
                        onChange={handleChange}
                    />

                    {errors.email && (
                        <p role="alert">
                            {errors.email}
                        </p>
                    )}
                </div>

                <div>
                    <label htmlFor="age">
                        Age
                    </label>

                    <input
                        id="age"
                        name="age"
                        type="number"
                        min="18"
                        max="120"
                        value={form.age}
                        onChange={handleChange}
                    />

                    {errors.age && (
                        <p role="alert">
                            {errors.age}
                        </p>
                    )}
                </div>

                <div>
                    <label htmlFor="acceptedTerms">
                        <input
                            id="acceptedTerms"
                            name="acceptedTerms"
                            type="checkbox"
                            checked={form.acceptedTerms}
                            onChange={handleChange}
                        />

                        Accept terms and conditions
                    </label>

                    {errors.acceptedTerms && (
                        <p role="alert">
                            {errors.acceptedTerms}
                        </p>
                    )}
                </div>

                <button type="submit">
                    Submit
                </button>
            </form>

            {submitted && (
                <p role="status">
                    Registration form validated successfully.
                </p>
            )}
        </section>
    );
}


/* =========================================================
   3. DERIVED STATE
   ========================================================= */

export function ShoppingCart() {
    const [cart, setCart] = useState([
        {
            id: 1,
            name: 'Keyboard',
            price: 2499,
            quantity: 1
        },
        {
            id: 2,
            name: 'Mouse',
            price: 999,
            quantity: 2
        }
    ]);

    // These values are calculated from existing state.
    // They do not require separate useState declarations.
    const totalItems = cart.reduce(
        (total, item) => total + item.quantity,
        0
    );

    const subtotal = cart.reduce(
        (total, item) =>
            total + item.price * item.quantity,
        0
    );

    const hasItems = cart.length > 0;

    function incrementQuantity(id) {
        setCart(previous =>
            previous.map(item =>
                item.id === id
                    ? {
                        ...item,
                        quantity: item.quantity + 1
                    }
                    : item
            )
        );
    }

    function decrementQuantity(id) {
        setCart(previous =>
            previous
                .map(item =>
                    item.id === id
                        ? {
                            ...item,
                            quantity: item.quantity - 1
                        }
                        : item
                )
                .filter(item => item.quantity > 0)
        );
    }

    function removeItem(id) {
        setCart(previous =>
            previous.filter(item => item.id !== id)
        );
    }

    return (
        <section>
            <h2>Shopping Cart</h2>

            {!hasItems ? (
                <p>Your cart is empty.</p>
            ) : (
                <>
                    {cart.map(item => (
                        <article key={item.id}>
                            <h3>{item.name}</h3>

                            <p>Price: ₹{item.price}</p>

                            <p>
                                Quantity: {item.quantity}
                            </p>

                            <button
                                onClick={() =>
                                    incrementQuantity(item.id)
                                }
                            >
                                +
                            </button>

                            <button
                                onClick={() =>
                                    decrementQuantity(item.id)
                                }
                            >
                                -
                            </button>

                            <button
                                onClick={() =>
                                    removeItem(item.id)
                                }
                            >
                                Remove
                            </button>
                        </article>
                    ))}
                </>
            )}

            <p>Total items: {totalItems}</p>

            <p>Subtotal: ₹{subtotal.toFixed(2)}</p>
        </section>
    );
}


/* =========================================================
   4. NESTED OBJECT STATE
   ========================================================= */

export function UserProfile() {
    const [user, setUser] = useState({
        name: 'Atul',
        address: {
            city: 'Lucknow',
            country: 'India'
        },
        preferences: {
            theme: 'light',
            notifications: true
        }
    });

    function updateCity(city) {
        setUser(previous => ({
            ...previous,
            address: {
                ...previous.address,
                city
            }
        }));
    }

    function toggleNotifications() {
        setUser(previous => ({
            ...previous,
            preferences: {
                ...previous.preferences,
                notifications:
                    !previous.preferences.notifications
            }
        }));
    }

    return (
        <section>
            <h2>User Profile</h2>

            <p>Name: {user.name}</p>

            <p>City: {user.address.city}</p>

            <p>Country: {user.address.country}</p>

            <p>
                Notifications:
                {user.preferences.notifications
                    ? ' Enabled'
                    : ' Disabled'}
            </p>

            <button onClick={() => updateCity('Patna')}>
                Change City
            </button>

            <button onClick={toggleNotifications}>
                Toggle Notifications
            </button>
        </section>
    );
}


/* =========================================================
   5. ASYNCHRONOUS STATE AND LOADING STATES
   ========================================================= */

export function UserDirectory() {
    const [users, setUsers] = useState([]);
    const [status, setStatus] = useState('idle');
    const [error, setError] = useState(null);

    async function loadUsers() {
        setStatus('loading');
        setError(null);

        try {
            const response = await fetch(
                'https://jsonplaceholder.typicode.com/users'
            );

            if (!response.ok) {
                throw new Error(
                    `HTTP error: ${response.status}`
                );
            }

            const data = await response.json();

            if (!Array.isArray(data)) {
                throw new Error('Invalid server response.');
            }

            setUsers(data);
            setStatus('success');
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : 'Unknown request error.'
            );

            setStatus('error');
        }
    }

    return (
        <section>
            <h2>User Directory</h2>

            <button
                onClick={loadUsers}
                disabled={status === 'loading'}
            >
                {status === 'loading'
                    ? 'Loading...'
                    : 'Load Users'}
            </button>

            {status === 'error' && (
                <p role="alert">{error}</p>
            )}

            {status === 'success' && (
                <ul>
                    {users.map(user => (
                        <li key={user.id}>
                            {user.name} - {user.email}
                        </li>
                    ))}
                </ul>
            )}
        </section>
    );
}


/* =========================================================
   6. STATE INITIALIZATION AND LAZY INITIALIZATION
   ========================================================= */

export function SearchHistory() {
    const [history, setHistory] = useState(() => {
        try {
            const stored = localStorage.getItem(
                'search-history'
            );

            if (!stored) {
                return [];
            }

            const parsed = JSON.parse(stored);

            return Array.isArray(parsed)
                ? parsed.filter(
                    value =>
                        typeof value === 'string' &&
                        value.length <= 100
                )
                : [];
        } catch {
            return [];
        }
    });

    const [query, setQuery] = useState('');

    function addSearch(event) {
        event.preventDefault();

        const normalized = query.trim();

        if (!normalized || normalized.length > 100) {
            return;
        }

        setHistory(previous => {
            const next = [
                normalized,
                ...previous.filter(
                    item => item !== normalized
                )
            ].slice(0, 10);

            try {
                localStorage.setItem(
                    'search-history',
                    JSON.stringify(next)
                );
            } catch (error) {
                console.error(
                    'Unable to persist search history:',
                    error
                );
            }

            return next;
        });

        setQuery('');
    }

    return (
        <section>
            <h2>Search History</h2>

            <form onSubmit={addSearch}>
                <input
                    value={query}
                    onChange={event =>
                        setQuery(event.target.value)
                    }
                    maxLength={100}
                    placeholder="Enter search term"
                />

                <button type="submit">
                    Add Search
                </button>
            </form>

            <ul>
                {history.map((item, index) => (
                    <li key={`${item}-${index}`}>
                        {item}
                    </li>
                ))}
            </ul>
        </section>
    );
}


/* =========================================================
   7. APPLICATION
   ========================================================= */

export default function App() {
    return (
        <main>
            <h1>React State Management</h1>

            <Counter />

            <hr />

            <ControlledForm />

            <hr />

            <ShoppingCart />

            <hr />

            <UserProfile />

            <hr />

            <UserDirectory />

            <hr />

            <SearchHistory />
        </main>
    );
}
