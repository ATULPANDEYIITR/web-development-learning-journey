"use strict";

/*
 * API-powered operational dashboard.
 *
 * Node.js 18 or later.
 *
 * Features:
 * - HTTP API server with deterministic sample responses
 * - Fetch-based asynchronous API client
 * - Request timeouts and bounded retries
 * - In-flight request coalescing
 * - TTL cache and stale-data fallback
 * - Schema validation
 * - Event-driven state notifications
 * - Concurrent resource loading
 * - Cancellation of superseded refreshes
 * - Optional periodic refresh
 *
 * Run: node dashboard.js
 */

const http = require("node:http");
const { EventEmitter } = require("node:events");
const { randomUUID } = require("node:crypto");

const ENDPOINTS = Object.freeze({
    metrics: "/api/metrics",
    services: "/api/services",
    incidents: "/api/incidents"
});

const VALID_SERVICE_STATUSES = new Set([
    "OPERATIONAL",
    "DEGRADED",
    "DOWN"
]);

const VALID_SEVERITIES = new Set([
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL"
]);

const VALID_INCIDENT_STATUSES = new Set([
    "OPEN",
    "INVESTIGATING",
    "RESOLVED"
]);

class DashboardError extends Error {
    constructor(message, options = {}) {
        super(message, options);
        this.name = "DashboardError";
    }
}

class HttpError extends DashboardError {
    constructor(status, message) {
        super(message);
        this.name = "HttpError";
        this.status = status;
    }
}

function isoSecondsAgo(seconds) {
    return new Date(Date.now() - seconds * 1000).toISOString();
}

function createFixtures() {
    return {
        [ENDPOINTS.metrics]: [
            {
                serviceId: "payments",
                name: "latency",
                value: 145.2,
                unit: "ms",
                observedAt: isoSecondsAgo(12)
            },
            {
                serviceId: "payments",
                name: "errorRate",
                value: 0.8,
                unit: "%",
                observedAt: isoSecondsAgo(12)
            },
            {
                serviceId: "identity",
                name: "latency",
                value: 88.4,
                unit: "ms",
                observedAt: isoSecondsAgo(8)
            },
            {
                serviceId: "identity",
                name: "errorRate",
                value: 0.2,
                unit: "%",
                observedAt: isoSecondsAgo(8)
            },
            {
                serviceId: "notifications",
                name: "latency",
                value: 420,
                unit: "ms",
                observedAt: isoSecondsAgo(20)
            }
        ],
        [ENDPOINTS.services]: [
            {
                serviceId: "payments",
                name: "Payment Processing",
                status: "OPERATIONAL",
                region: "ap-south-1"
            },
            {
                serviceId: "identity",
                name: "Identity Service",
                status: "OPERATIONAL",
                region: "ap-south-1"
            },
            {
                serviceId: "notifications",
                name: "Notification Gateway",
                status: "DEGRADED",
                region: "ap-south-1"
            }
        ],
        [ENDPOINTS.incidents]: [
            {
                incidentId: "INC-2041",
                serviceId: "notifications",
                severity: "HIGH",
                title: "Elevated notification latency",
                status: "INVESTIGATING",
                openedAt: isoSecondsAgo(1800)
            },
            {
                incidentId: "INC-2038",
                serviceId: "payments",
                severity: "LOW",
                title: "Intermittent callback delay",
                status: "RESOLVED",
                openedAt: isoSecondsAgo(7200)
            }
        ]
    };
}

async function startMockApiServer() {
    const fixtures = createFixtures();
    let incidentFailuresRemaining = 0;

    const server = http.createServer((request, response) => {
        const requestId = randomUUID();

        response.setHeader("Content-Type", "application/json");
        response.setHeader("Cache-Control", "no-store");
        response.setHeader("X-Request-Id", requestId);

        const path = new URL(
            request.url,
            "http://127.0.0.1"
        ).pathname;

        if (request.method !== "GET") {
            response.writeHead(405);
            response.end(JSON.stringify({
                error: "Method not allowed",
                requestId
            }));
            return;
        }

        if (!Object.hasOwn(fixtures, path)) {
            response.writeHead(404);
            response.end(JSON.stringify({
                error: "Resource not found",
                requestId
            }));
            return;
        }

        if (path === ENDPOINTS.incidents && incidentFailuresRemaining > 0) {
            incidentFailuresRemaining -= 1;
            response.writeHead(503);
            response.end(JSON.stringify({
                error: "Temporary upstream failure",
                requestId
            }));
            return;
        }

        response.writeHead(200);
        response.end(JSON.stringify({
            data: fixtures[path],
            requestId,
            generatedAt: new Date().toISOString()
        }));
    });

    await new Promise((resolve, reject) => {
        server.once("error", reject);
        server.listen(0, "127.0.0.1", resolve);
    });

    const address = server.address();

    return {
        server,
        baseUrl: `http://127.0.0.1:${address.port}`,
        failNextIncidents(count) {
            if (!Number.isInteger(count) || count < 0) {
                throw new TypeError("Failure count must be a non-negative integer.");
            }
            incidentFailuresRemaining = count;
        }
    };
}

function isPlainObject(value) {
    return value !== null &&
        typeof value === "object" &&
        !Array.isArray(value);
}

function validateTimestamp(value, fieldName) {
    if (
        typeof value !== "string" ||
        !Number.isFinite(Date.parse(value))
    ) {
        throw new DashboardError(`${fieldName} must be a valid timestamp.`);
    }

    if (Date.parse(value) > Date.now() + 5 * 60 * 1000) {
        throw new DashboardError(`${fieldName} is unexpectedly in the future.`);
    }
}

function validateMetrics(rows) {
    if (!Array.isArray(rows)) {
        throw new DashboardError("Metrics payload must be an array.");
    }

    const seen = new Set();

    for (const metric of rows) {
        if (!isPlainObject(metric)) {
            throw new DashboardError("Each metric must be an object.");
        }

        for (const field of ["serviceId", "name", "unit"]) {
            if (
                typeof metric[field] !== "string" ||
                metric[field].trim() === ""
            ) {
                throw new DashboardError(`Metric ${field} is required.`);
            }
        }

        if (
            typeof metric.value !== "number" ||
            !Number.isFinite(metric.value) ||
            metric.value < 0
        ) {
            throw new DashboardError("Metric value must be finite and non-negative.");
        }

        validateTimestamp(metric.observedAt, "Metric observedAt");

        const key = `${metric.serviceId}:${metric.name}`;
        if (seen.has(key)) {
            throw new DashboardError(`Duplicate metric: ${key}`);
        }
        seen.add(key);
    }

    return rows;
}

function validateServices(rows) {
    if (!Array.isArray(rows)) {
        throw new DashboardError("Services payload must be an array.");
    }

    const seen = new Set();

    for (const service of rows) {
        if (!isPlainObject(service)) {
            throw new DashboardError("Each service must be an object.");
        }

        for (const field of ["serviceId", "name", "region"]) {
            if (
                typeof service[field] !== "string" ||
                service[field].trim() === ""
            ) {
                throw new DashboardError(`Service ${field} is required.`);
            }
        }

        if (!VALID_SERVICE_STATUSES.has(service.status)) {
            throw new DashboardError(`Invalid service status: ${service.status}`);
        }

        if (seen.has(service.serviceId)) {
            throw new DashboardError(`Duplicate service: ${service.serviceId}`);
        }
        seen.add(service.serviceId);
    }

    return rows;
}

function validateIncidents(rows) {
    if (!Array.isArray(rows)) {
        throw new DashboardError("Incidents payload must be an array.");
    }

    const seen = new Set();

    for (const incident of rows) {
        if (!isPlainObject(incident)) {
            throw new DashboardError("Each incident must be an object.");
        }

        for (const field of [
            "incidentId",
            "serviceId",
            "title"
        ]) {
            if (
                typeof incident[field] !== "string" ||
                incident[field].trim() === ""
            ) {
                throw new DashboardError(`Incident ${field} is required.`);
            }
        }

        if (!VALID_SEVERITIES.has(incident.severity)) {
            throw new DashboardError(`Invalid severity: ${incident.severity}`);
        }

        if (!VALID_INCIDENT_STATUSES.has(incident.status)) {
            throw new DashboardError(`Invalid incident status: ${incident.status}`);
        }

        validateTimestamp(incident.openedAt, "Incident openedAt");

        if (seen.has(incident.incidentId)) {
            throw new DashboardError(
                `Duplicate incident: ${incident.incidentId}`
            );
        }
        seen.add(incident.incidentId);
    }

    return rows;
}

class DashboardApiClient {
    constructor(baseUrl, options = {}) {
        this.baseUrl = baseUrl.replace(/\/+$/, "");
        this.timeoutMs = options.timeoutMs ?? 2500;
        this.maxAttempts = options.maxAttempts ?? 3;
        this.cacheTtlMs = options.cacheTtlMs ?? 5000;

        if (!Number.isInteger(this.maxAttempts) || this.maxAttempts < 1) {
            throw new TypeError("maxAttempts must be a positive integer.");
        }

        this.cache = new Map();
        this.inFlight = new Map();

        this.validators = new Map([
            [ENDPOINTS.metrics, validateMetrics],
            [ENDPOINTS.services, validateServices],
            [ENDPOINTS.incidents, validateIncidents]
        ]);
    }

    async request(path, parentSignal) {
        const controller = new AbortController();

        const timeout = setTimeout(() => {
            controller.abort(new Error("Request timed out."));
        }, this.timeoutMs);

        const forwardAbort = () => controller.abort(parentSignal.reason);

        if (parentSignal) {
            if (parentSignal.aborted) {
                forwardAbort();
            } else {
                parentSignal.addEventListener("abort", forwardAbort, {
                    once: true
                });
            }
        }

        try {
            const response = await fetch(`${this.baseUrl}${path}`, {
                method: "GET",
                headers: {
                    Accept: "application/json",
                    "X-Request-Id": randomUUID()
                },
                signal: controller.signal
            });

            if (!response.ok) {
                throw new HttpError(
                    response.status,
                    `API returned HTTP ${response.status} for ${path}`
                );
            }

            const body = await response.json();

            if (!isPlainObject(body) || !Array.isArray(body.data)) {
                throw new DashboardError(`Invalid API envelope for ${path}.`);
            }

            return body.data;

        } finally {
            clearTimeout(timeout);

            if (parentSignal) {
                parentSignal.removeEventListener("abort", forwardAbort);
            }
        }
    }

    async requestWithRetry(path, signal) {
        let lastError;

        for (let attempt = 0; attempt < this.maxAttempts; attempt += 1) {
            if (signal?.aborted) {
                throw new DashboardError("Dashboard request was cancelled.");
            }

            try {
                const rows = await this.request(path, signal);
                return this.validators.get(path)(rows);

            } catch (error) {
                lastError = error;

                if (signal?.aborted) {
                    throw new DashboardError("Dashboard request was cancelled.");
                }

                const retryable = !(error instanceof HttpError) ||
                    error.status === 429 ||
                    error.status >= 500;

                if (!retryable || attempt + 1 >= this.maxAttempts) {
                    break;
                }

                await new Promise((resolve, reject) => {
                    const timer = setTimeout(
                        resolve,
                        30 * (2 ** attempt)
                    );

                    if (signal) {
                        const cancel = () => {
                            clearTimeout(timer);
                            reject(new DashboardError("Retry cancelled."));
                        };

                        signal.addEventListener("abort", cancel, {
                            once: true
                        });
                    }
                });
            }
        }

        throw new DashboardError(
            `${path} failed after ${this.maxAttempts} attempts: ` +
            `${lastError?.message ?? "unknown error"}`,
            { cause: lastError }
        );
    }

    async getResource(path, options = {}) {
        if (!this.validators.has(path)) {
            throw new DashboardError(`Unsupported endpoint: ${path}`);
        }

        const force = options.force ?? false;
        const signal = options.signal;
        const cached = this.cache.get(path);

        if (
            !force &&
            cached &&
            Date.now() - cached.fetchedAt <= this.cacheTtlMs
        ) {
            return {
                data: cached.data,
                stale: false,
                fromCache: true
            };
        }

        // Identical concurrent requests share a single network operation.
        if (this.inFlight.has(path)) {
            return this.inFlight.get(path);
        }

        const operation = (async () => {
            try {
                const data = await this.requestWithRetry(path, signal);

                this.cache.set(path, {
                    data,
                    fetchedAt: Date.now()
                });

                return {
                    data,
                    stale: false,
                    fromCache: false
                };

            } catch (error) {
                if (cached) {
                    return {
                        data: cached.data,
                        stale: true,
                        fromCache: true,
                        error: error.message
                    };
                }

                throw error;
            }
        })();

        this.inFlight.set(path, operation);

        try {
            return await operation;
        } finally {
            this.inFlight.delete(path);
        }
    }
}

function initialState() {
    return {
        phase: "IDLE",
        resources: {
            metrics: [],
            services: [],
            incidents: []
        },
        staleResources: [],
        errors: {},
        updatedAt: null,
        generation: 0
    };
}

/*
 * The store replaces state instead of mutating existing objects.
 * Subscribers receive a complete state snapshot after each transition.
 */
class DashboardStore extends EventEmitter {
    constructor() {
        super();
        this.state = initialState();
    }

    replace(nextState) {
        this.state = nextState;
        this.emit("change", this.state);
    }

    getState() {
        return this.state;
    }
}

class DashboardController {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.store = new DashboardStore();
        this.refreshController = null;
        this.generation = 0;
        this.pollingTimer = null;
    }

    async refresh(options = {}) {
        // A newer refresh supersedes the previous one.
        if (this.refreshController) {
            this.refreshController.abort();
        }

        const controller = new AbortController();
        this.refreshController = controller;

        const generation = ++this.generation;

        this.store.replace({
            ...this.store.getState(),
            phase: "LOADING",
            generation,
            errors: {}
        });

        const definitions = [
            ["metrics", ENDPOINTS.metrics],
            ["services", ENDPOINTS.services],
            ["incidents", ENDPOINTS.incidents]
        ];

        const outcomes = await Promise.allSettled(
            definitions.map(([, path]) =>
                this.apiClient.getResource(path, {
                    force: options.force ?? false,
                    signal: controller.signal
                })
            )
        );

        // An old request must not overwrite the state from a newer refresh.
        if (generation !== this.generation || controller.signal.aborted) {
            return this.store.getState();
        }

        const resources = {
            ...this.store.getState().resources
        };
        const errors = {};
        const staleResources = [];

        outcomes.forEach((outcome, index) => {
            const [name] = definitions[index];

            if (outcome.status === "rejected") {
                errors[name] = outcome.reason?.message ?? "Unknown failure";
                return;
            }

            const result = outcome.value;
            resources[name] = result.data;

            if (result.stale) {
                staleResources.push(name);
                errors[name] = result.error;
            }
        });

        const successCount = definitions.filter(
            ([name]) => resources[name].length >= 0 &&
                !errors[name]
        ).length;

        let phase;

        if (successCount === 0) {
            phase = "ERROR";
        } else if (
            Object.keys(errors).length > 0 ||
            staleResources.length > 0 ||
            successCount < definitions.length
        ) {
            phase = "DEGRADED";
        } else {
            phase = "READY";
        }

        this.store.replace({
            ...this.store.getState(),
            phase,
            resources,
            staleResources,
            errors,
            updatedAt: new Date().toISOString()
        });

        return this.store.getState();
    }

    startPolling(intervalMs = 10000) {
        if (!Number.isInteger(intervalMs) || intervalMs < 1000) {
            throw new RangeError("Polling interval must be at least 1000 ms.");
        }

        this.stopPolling();

        this.pollingTimer = setInterval(() => {
            this.refresh().catch(error => {
                this.store.emit("error", error);
            });
        }, intervalMs);

        this.pollingTimer.unref?.();
    }

    stopPolling() {
        if (this.pollingTimer) {
            clearInterval(this.pollingTimer);
            this.pollingTimer = null;
        }
    }

    cancel() {
        this.generation += 1;
        this.refreshController?.abort();
        this.refreshController = null;
        this.stopPolling();
    }
}

function renderDashboard(state) {
    const services = state.resources.services;
    const incidents = state.resources.incidents;
    const metrics = state.resources.metrics;

    const openIncidents = incidents.filter(
        incident => incident.status !== "RESOLVED"
    );

    const unavailableServices = services.filter(
        service => service.status === "DOWN"
    );

    console.log("\nAPI OPERATIONS DASHBOARD");
    console.log("=".repeat(60));
    console.log(`State: ${state.phase}`);
    console.log(`Updated: ${state.updatedAt ?? "Never"}`);
    console.log(`Services: ${services.length}`);
    console.log(`Unavailable services: ${unavailableServices.length}`);
    console.log(`Open incidents: ${openIncidents.length}`);

    console.log("\nServices");
    for (const service of services) {
        console.log(
            `  ${service.name.padEnd(26)} ` +
            `${service.status.padEnd(12)} ${service.region}`
        );
    }

    console.log("\nMetrics");
    for (const metric of metrics) {
        console.log(
            `  ${metric.serviceId.padEnd(16)} ` +
            `${metric.name.padEnd(12)} ${metric.value} ${metric.unit}`
        );
    }

    console.log("\nOpen incidents");
    for (const incident of openIncidents) {
        console.log(
            `  ${incident.incidentId} | ${incident.severity} | ` +
            `${incident.title}`
        );
    }

    if (state.staleResources.length > 0) {
        console.log(
            "\nStale resources:",
            state.staleResources.join(", ")
        );
    }

    if (Object.keys(state.errors).length > 0) {
        console.log("\nErrors");
        for (const [resource, message] of Object.entries(state.errors)) {
            console.log(`  ${resource}: ${message}`);
        }
    }
}

async function main() {
    const mock = await startMockApiServer();

    const client = new DashboardApiClient(mock.baseUrl, {
        timeoutMs: 2500,
        maxAttempts: 3,
        cacheTtlMs: 5000
    });

    const dashboard = new DashboardController(client);

    dashboard.store.on("change", state => {
        console.log(`[state] ${state.phase}`);
    });

    try {
        // One transient 503 is retried successfully.
        mock.failNextIncidents(1);
        let state = await dashboard.refresh({ force: true });
        renderDashboard(state);

        // All retry attempts fail. The previously validated incidents remain
        // available and are explicitly marked as stale.
        mock.failNextIncidents(3);
        state = await dashboard.refresh({ force: true });
        renderDashboard(state);

        if (state.phase !== "DEGRADED") {
            throw new DashboardError("Expected a degraded dashboard state.");
        }

        if (!state.staleResources.includes("incidents")) {
            throw new DashboardError("Expected stale incident data.");
        }

    } finally {
        dashboard.cancel();

        await new Promise((resolve, reject) => {
            mock.server.close(error => {
                if (error) reject(error);
                else resolve();
            });
        });
    }
}

main().catch(error => {
    console.error("Dashboard execution failed:", error);
    process.exitCode = 1;
});
