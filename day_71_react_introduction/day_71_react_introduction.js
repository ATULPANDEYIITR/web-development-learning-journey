import React, {
    useState,
    useMemo,
    useCallback,
    memo
} from "react";

import { createRoot } from "react-dom/client";


/*
 * React Introduction
 *
 * Demonstrates:
 * - Functional components
 * - JSX
 * - Component composition
 * - Props
 * - State
 * - Event handling
 * - Conditional rendering
 * - Lists and keys
 * - Derived data
 * - Memoization
 * - Error boundaries
 * - React rendering
 */


const styles = {
    app: {
        maxWidth: "1000px",
        margin: "40px auto",
        padding: "24px",
        fontFamily: "Arial, sans-serif",
        color: "#202938"
    },
    header: {
        borderBottom: "1px solid #ddd",
        marginBottom: "24px",
        paddingBottom: "16px"
    },
    grid: {
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: "16px"
    },
    card: {
        padding: "18px",
        border: "1px solid #ddd",
        borderRadius: "10px"
    },
    button: {
        padding: "10px 16px",
        margin: "5px",
        cursor: "pointer"
    }
};


const INITIAL_CONCEPTS = [
    {
        id: "components",
        title: "Component Architecture",
        description: "Create reusable interface units.",
        category: "Architecture"
    },
    {
        id: "jsx",
        title: "JSX",
        description: "Describe UI structures using JavaScript syntax.",
        category: "Syntax"
    },
    {
        id: "virtual-dom",
        title: "Virtual DOM",
        description: "Represent UI output as an in-memory tree.",
        category: "Rendering"
    },
    {
        id: "rendering",
        title: "Rendering",
        description: "Synchronize component output with the browser DOM.",
        category: "Rendering"
    }
];


class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}


function validateConcept(concept) {
    if (!concept || typeof concept !== "object") {
        throw new ValidationError("Concept must be an object.");
    }

    for (const field of ["id", "title", "description", "category"]) {
        if (
            typeof concept[field] !== "string" ||
            concept[field].trim() === ""
        ) {
            throw new ValidationError(
                `Invalid concept field: ${field}`
            );
        }
    }

    return Object.freeze({ ...concept });
}


function validateConceptCollection(concepts) {
    if (!Array.isArray(concepts)) {
        throw new ValidationError("Concept collection must be an array.");
    }

    const ids = new Set();

    return concepts.map((concept) => {
        const valid = validateConcept(concept);

        if (ids.has(valid.id)) {
            throw new ValidationError(
                `Duplicate concept ID: ${valid.id}`
            );
        }

        ids.add(valid.id);
        return valid;
    });
}


// Reusable component: Header
function Header({ title, subtitle }) {
    return (
        <header style={styles.header}>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </header>
    );
}


// Reusable component: ConceptCard
const ConceptCard = memo(function ConceptCard({ concept }) {
    return (
        <article
            style={styles.card}
            aria-labelledby={`heading-${concept.id}`}
        >
            <h2 id={`heading-${concept.id}`}>
                {concept.title}
            </h2>

            <p>{concept.description}</p>

            <small>Category: {concept.category}</small>
        </article>
    );
});


// Component composition through child components
function ConceptList({ concepts }) {
    if (concepts.length === 0) {
        return <p>No matching concepts found.</p>;
    }

    return (
        <section style={styles.grid} aria-label="React concepts">
            {concepts.map((concept) => (
                <ConceptCard
                    key={concept.id}
                    concept={concept}
                />
            ))}
        </section>
    );
}


// State and event-driven rendering
function Counter() {
    const [count, setCount] = useState(0);

    const increment = useCallback(() => {
        setCount((previous) => previous + 1);
    }, []);

    const decrement = useCallback(() => {
        setCount((previous) => Math.max(0, previous - 1));
    }, []);

    const reset = useCallback(() => {
        setCount(0);
    }, []);

    return (
        <section style={{ marginTop: "30px" }}>
            <h2>State and Events</h2>

            <p aria-live="polite">
                Current count: <strong>{count}</strong>
            </p>

            <button
                type="button"
                style={styles.button}
                onClick={increment}
            >
                Increment
            </button>

            <button
                type="button"
                style={styles.button}
                onClick={decrement}
                disabled={count === 0}
            >
                Decrement
            </button>

            <button
                type="button"
                style={styles.button}
                onClick={reset}
            >
                Reset
            </button>

            {count >= 5 && (
                <p role="status">
                    The counter reached five or more.
                </p>
            )}
        </section>
    );
}


// Derived rendering with useMemo
function SearchableConcepts({ concepts }) {
    const [search, setSearch] = useState("");
    const [category, setCategory] = useState("All");

    const categories = useMemo(() => {
        return [
            "All",
            ...new Set(concepts.map((item) => item.category))
        ];
    }, [concepts]);

    const filteredConcepts = useMemo(() => {
        const query = search.trim().toLowerCase();

        return concepts.filter((concept) => {
            const matchesSearch = [
                concept.title,
                concept.description,
                concept.category
            ].some((value) =>
                value.toLowerCase().includes(query)
            );

            const matchesCategory =
                category === "All" ||
                concept.category === category;

            return matchesSearch && matchesCategory;
        });
    }, [concepts, search, category]);

    return (
        <section style={{ marginTop: "30px" }}>
            <h2>Component Filtering</h2>

            <label htmlFor="concept-search">
                Search concepts
            </label>

            <div>
                <input
                    id="concept-search"
                    type="search"
                    value={search}
                    maxLength={100}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search concepts..."
                />

                <select
                    aria-label="Filter by category"
                    value={category}
                    onChange={(event) => setCategory(event.target.value)}
                >
                    {categories.map((item) => (
                        <option key={item} value={item}>
                            {item}
                        </option>
                    ))}
                </select>
            </div>

            <p>
                Displaying {filteredConcepts.length} of {concepts.length} concepts.
            </p>

            <ConceptList concepts={filteredConcepts} />
        </section>
    );
}


// Error Boundary: handles rendering errors in descendants
class ApplicationErrorBoundary extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            hasError: false
        };
    }

    static getDerivedStateFromError() {
        return { hasError: true };
    }

    componentDidCatch(error, info) {
        // Production applications should send sanitized diagnostics
        // to an authorized monitoring service.
        console.error("Component rendering failed:", error.message);
        console.error("Component stack:", info.componentStack);
    }

    render() {
        if (this.state.hasError) {
            return (
                <main role="alert">
                    <h2>Interface rendering failed.</h2>
                    <p>Reload the application to try again.</p>
                </main>
            );
        }

        return this.props.children;
    }
}


// Main application component
function App() {
    const concepts = useMemo(
        () => validateConceptCollection(INITIAL_CONCEPTS),
        []
    );

    return (
        <main style={styles.app}>
            <Header
                title="React Introduction"
                subtitle="Component architecture, JSX, virtual DOM and rendering"
            />

            <section>
                <h2>Component Architecture</h2>
                <p>
                    React applications are composed of reusable
                    components arranged in a component tree.
                </p>
            </section>

            <ConceptList concepts={concepts} />

            <Counter />

            <SearchableConcepts concepts={concepts} />
        </main>
    );
}


// Application initialization
function mountApplication(container) {
    if (!(container instanceof HTMLElement)) {
        throw new Error("A valid HTML mounting element is required.");
    }

    const root = createRoot(container);

    root.render(
        <React.StrictMode>
            <ApplicationErrorBoundary>
                <App />
            </ApplicationErrorBoundary>
        </React.StrictMode>
    );

    return root;
}


// Browser entry point
const container = document.getElementById("root");

if (!container) {
    throw new Error(
        'Missing root element. Add <div id="root"></div> to the HTML document.'
    );
}

mountApplication(container);
