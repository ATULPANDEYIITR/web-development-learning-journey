/**
 * React Hooks: useRef, useMemo, useCallback, and Custom Hooks.
 *
 * Runtime: React 18+ or React 19, JavaScript ES modules.
 *
 * This module provides:
 * - Persistent mutable references.
 * - Memoized derived data.
 * - Stable event callbacks.
 * - Custom hooks for previous values and debounced values.
 * - DOM interaction.
 * - Effect cleanup.
 * - Input validation and failure handling.
 */

import {
    createElement,
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState
} from "react";


function validateItems(items) {
    if (!Array.isArray(items)) {
        throw new TypeError("items must be an array.");
    }

    const ids = new Set();

    for (const item of items) {
        if (
            item === null ||
            typeof item !== "object" ||
            !Number.isSafeInteger(item.id) ||
            typeof item.name !== "string" ||
            typeof item.score !== "number" ||
            !Number.isFinite(item.score)
        ) {
            throw new TypeError(
                "Each item requires an integer id, string name, and finite score."
            );
        }

        if (ids.has(item.id)) {
            throw new TypeError(`Duplicate item id: ${item.id}`);
        }

        ids.add(item.id);
    }
}


/**
 * Custom Hook: useLatest
 *
 * Maintains access to the latest committed value without
 * changing the identity of the returned ref.
 */
export function useLatest(value) {
    const reference = useRef(value);

    useEffect(() => {
        reference.current = value;
    }, [value]);

    return reference;
}


/**
 * Custom Hook: usePrevious
 *
 * Returns the value from the preceding committed render.
 * The initial value is undefined unless an initial value is supplied.
 */
export function usePrevious(value, initialValue = undefined) {
    const reference = useRef(initialValue);

    useEffect(() => {
        reference.current = value;
    }, [value]);

    return reference.current;
}


/**
 * Custom Hook: useDebouncedValue
 *
 * Delays publishing changes until the specified period
 * has elapsed without another update.
 *
 * The effect cleanup prevents outdated timers from publishing.
 */
export function useDebouncedValue(value, delay = 300) {
    if (!Number.isFinite(delay) || delay < 0) {
        throw new RangeError("delay must be a non-negative finite number.");
    }

    const [debouncedValue, setDebouncedValue] = useState(value);

    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);

        return () => clearTimeout(timer);
    }, [value, delay]);

    return debouncedValue;
}


/**
 * Custom Hook: useStableEvent
 *
 * Provides a stable callback identity while invoking
 * the latest committed callback implementation.
 *
 * Useful for event handlers registered with external systems.
 */
export function useStableEvent(handler) {
    if (typeof handler !== "function") {
        throw new TypeError("handler must be a function.");
    }

    const latestHandler = useLatest(handler);

    return useCallback((...args) => {
        return latestHandler.current(...args);
    }, []);
}


/**
 * Custom Hook: useFilteredRecords
 *
 * Separates expensive derived data from rendering.
 * The input array should be updated immutably.
 */
export function useFilteredRecords(items, minimumScore, query) {
    return useMemo(() => {
        const normalizedQuery = query.trim().toLowerCase();

        return items.filter((item) => {
            const matchesScore = item.score >= minimumScore;

            const matchesQuery =
                normalizedQuery.length === 0 ||
                item.name.toLowerCase().includes(normalizedQuery);

            return matchesScore && matchesQuery;
        });
    }, [items, minimumScore, query]);
}


/**
 * Custom Hook: useRenderMetrics
 *
 * A mutable ref counts render executions without scheduling
 * additional renders.
 *
 * This is diagnostic information, not a production profiler.
 */
export function useRenderMetrics() {
    const renderCount = useRef(0);
    renderCount.current += 1;

    return renderCount.current;
}


/**
 * Repository dashboard component.
 *
 * Props:
 * - items: array of repository records.
 * - minimumScore: numeric filtering threshold.
 * - onSelect: optional selection callback.
 * - debounceDelay: search delay.
 */
export function HookWorkbench({
    items,
    minimumScore = 70,
    onSelect = () => {},
    debounceDelay = 300
}) {
    validateItems(items);

    if (!Number.isFinite(minimumScore)) {
        throw new TypeError("minimumScore must be finite.");
    }

    if (typeof onSelect !== "function") {
        throw new TypeError("onSelect must be a function.");
    }

    const [search, setSearch] = useState("");
    const [selectedId, setSelectedId] = useState(null);

    // Persistent references do not independently trigger rendering.
    const searchInputRef = useRef(null);
    const renderCount = useRenderMetrics();

    // Previous search value is available for diagnostics.
    const previousSearch = usePrevious(search, "");

    // Avoid recalculating the debounced search value on every keystroke.
    const debouncedSearch = useDebouncedValue(
        search,
        debounceDelay
    );

    // Memoize derived repository records.
    const filteredItems = useFilteredRecords(
        items,
        minimumScore,
        debouncedSearch
    );

    // Stable event identity, with the latest committed callback.
    const notifySelection = useStableEvent(onSelect);

    // Stable handler for selecting a repository.
    const selectRepository = useCallback((repository) => {
        setSelectedId(repository.id);
        notifySelection(repository);
    }, [notifySelection]);

    // Focus the search input without querying the DOM manually.
    const focusSearch = useCallback(() => {
        searchInputRef.current?.focus();
    }, []);

    // Memoize a lookup structure for repeated selection checks.
    const repositoryIds = useMemo(() => {
        return new Set(filteredItems.map((item) => item.id));
    }, [filteredItems]);

    // Avoid stale selections when a selected record disappears.
    useEffect(() => {
        if (
            selectedId !== null &&
            !items.some((item) => item.id === selectedId)
        ) {
            setSelectedId(null);
        }
    }, [items, selectedId]);

    const rows = filteredItems.map((repository) => {
        const selected = repositoryIds.has(repository.id) &&
            selectedId === repository.id;

        return createElement(
            "li",
            {
                key: repository.id,
                "data-selected": selected,
                style: {
                    padding: "8px",
                    borderBottom: "1px solid #ddd"
                }
            },
            createElement(
                "span",
                null,
                `${repository.name} (${repository.score})`
            ),
            createElement(
                "button",
                {
                    type: "button",
                    onClick: () => selectRepository(repository),
                    "aria-pressed": selected,
                    style: { marginLeft: "12px" }
                },
                selected ? "Selected" : "Select"
            )
        );
    });

    return createElement(
        "section",
        { "aria-label": "Repository dashboard" },

        createElement("h2", null, "Repository Dashboard"),

        createElement("label", null, "Search repositories"),

        createElement("input", {
            ref: searchInputRef,
            type: "search",
            value: search,
            onChange: (event) => setSearch(event.target.value),
            placeholder: "Search by repository name",
            "aria-label": "Search repositories"
        }),

        createElement(
            "button",
            {
                type: "button",
                onClick: focusSearch
            },
            "Focus Search"
        ),

        createElement(
            "p",
            null,
            `Minimum score: ${minimumScore}`
        ),

        createElement(
            "p",
            { "aria-live": "polite" },
            `Matching repositories: ${filteredItems.length}`
        ),

        createElement(
            "ul",
            null,
            rows.length > 0
                ? rows
                : createElement("li", null, "No matching repositories.")
        ),

        createElement(
            "p",
            { "data-testid": "render-metrics" },
            `Render count: ${renderCount}`
        ),

        createElement(
            "p",
            null,
            `Previous search: ${previousSearch || "(empty)"}`
        ),

        createElement(
            "p",
            null,
            `Debounced search: ${debouncedSearch || "(empty)"}`
        ),

        createElement(
            "p",
            null,
            selectedId === null
                ? "No repository selected."
                : `Selected repository ID: ${selectedId}`
        )
    );
}


/**
 * Standalone custom hook for maintaining a mutable
 * request identifier.
 *
 * It can be used to prevent stale asynchronous results
 * from replacing newer request results.
 */
export function useRequestSequence() {
    const sequence = useRef(0);

    const next = useCallback(() => {
        sequence.current += 1;
        return sequence.current;
    }, []);

    const isCurrent = useCallback((requestId) => {
        return requestId === sequence.current;
    }, []);

    return { next, isCurrent };
}


/**
 * Example asynchronous data hook.
 *
 * A newer request invalidates the result of an older request.
 * The effect cleanup prevents state updates after unmount.
 */
export function useRepositoryData(fetchRepositories) {
    if (typeof fetchRepositories !== "function") {
        throw new TypeError("fetchRepositories must be a function.");
    }

    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const requestSequence = useRequestSequence();

    useEffect(() => {
        const controller = new AbortController();
        const requestId = requestSequence.next();

        async function load() {
            setLoading(true);
            setError(null);

            try {
                const result = await fetchRepositories({
                    signal: controller.signal
                });

                if (!Array.isArray(result)) {
                    throw new TypeError(
                        "The repository service must return an array."
                    );
                }

                if (requestSequence.isCurrent(requestId)) {
                    validateItems(result);
                    setData(result);
                }
            } catch (caughtError) {
                if (
                    !controller.signal.aborted &&
                    requestSequence.isCurrent(requestId)
                ) {
                    setError(caughtError);
                }
            } finally {
                if (
                    !controller.signal.aborted &&
                    requestSequence.isCurrent(requestId)
                ) {
                    setLoading(false);
                }
            }
        }

        load();

        return () => {
            controller.abort();
        };
    }, [fetchRepositories, requestSequence]);

    return { data, loading, error };
}
