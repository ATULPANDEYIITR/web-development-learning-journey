#!/usr/bin/env node

'use strict';

/*
 * Fetch and HTTP APIs:
 * - HTTP methods
 * - headers
 * - JSON request/response bodies
 * - status-code handling
 * - AbortController timeouts
 * - retry policy
 * - asynchronous request lifecycle
 * - event-driven request instrumentation
 *
 * Requires Node.js 18+ because fetch is provided by the runtime.
 */

const http = require('node:http');
const { URL } = require('node:url');
const { EventEmitter } = require('node:events');

class HttpApiError extends Error {
    constructor(message, response = null) {
        super(message);
        this.name = 'HttpApiError';
        this.response = response;
    }
}

class RequestMetrics extends EventEmitter {
    constructor() {
        super();
        this.completed = 0;
        this.failed = 0;
        this.totalDurationMs = 0;
    }

    record(response, durationMs) {
        this.completed += 1;
        this.totalDurationMs += durationMs;
        this.emit('response', {
            status: response.status,
            durationMs,
        });
    }

    recordFailure(error) {
        this.failed += 1;
        this.emit('error', error);
    }

    snapshot() {
        return {
            completed: this.completed,
            failed: this.failed,
            averageDurationMs:
                this.completed === 0
                    ? 0
                    : this.totalDurationMs / this.completed,
        };
    }
}

class FetchClient {
    constructor({
        timeoutMs = 3000,
        maxRetries = 2,
        metrics = new RequestMetrics(),
    } = {}) {
        if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) {
            throw new TypeError('timeoutMs must be positive');
        }
        if (!Number.isInteger(maxRetries) || maxRetries < 0) {
            throw new TypeError('maxRetries must be a non-negative integer');
        }

        this.timeoutMs = timeoutMs;
        this.maxRetries = maxRetries;
        this.metrics = metrics;
    }

    async request({
        url,
        method = 'GET',
        headers = {},
        query = {},
        body = undefined,
    }) {
        const parsed = new URL(url);

        if (!['http:', 'https:'].includes(parsed.protocol)) {
            throw new TypeError('Only HTTP and HTTPS URLs are supported');
        }

        for (const [name, value] of Object.entries(headers)) {
            if (!name.trim() || /[\r\n]/.test(name) || /[\r\n]/.test(String(value))) {
                throw new TypeError('Invalid HTTP header');
            }
        }

        const finalUrl = new URL(parsed);
        for (const [key, value] of Object.entries(query)) {
            finalUrl.searchParams.set(key, String(value));
        }

        const upperMethod = method.toUpperCase();
        if (!['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].includes(upperMethod)) {
            throw new TypeError(`Unsupported HTTP method: ${method}`);
        }

        const requestHeaders = {
            Accept: 'application/json',
            'User-Agent': 'FetchApiLearningClient/1.0',
            ...headers,
        };

        let requestBody;
        if (body !== undefined) {
            if (upperMethod === 'GET' || upperMethod === 'DELETE') {
                throw new TypeError(`${upperMethod} cannot use this JSON body`);
            }

            requestBody = JSON.stringify(body);
            requestHeaders['Content-Type'] ??= 'application/json';
        }

        for (let attempt = 0; attempt <= this.maxRetries; attempt += 1) {
            const controller = new AbortController();
            const timer = setTimeout(
                () => controller.abort(),
                this.timeoutMs,
            );

            const started = performance.now();

            this.metrics.emit('request:start', {
                method: upperMethod,
                url: finalUrl.toString(),
                attempt: attempt + 1,
            });

            try {
                const response = await fetch(finalUrl, {
                    method: upperMethod,
                    headers: requestHeaders,
                    body: requestBody,
                    signal: controller.signal,
                });

                const durationMs = performance.now() - started;
                this.metrics.record(response, durationMs);

                if (
                    [408, 429, 500, 502, 503, 504].includes(response.status) &&
                    attempt < this.maxRetries
                ) {
                    await this.#backoff(attempt);
                    continue;
                }

                return response;
            } catch (error) {
                this.metrics.recordFailure(error);

                if (attempt >= this.maxRetries) {
                    throw new HttpApiError(
                        `HTTP transport failed: ${error.message}`,
                    );
                }

                await this.#backoff(attempt);
            } finally {
                clearTimeout(timer);
            }
        }

        throw new Error('Request lifecycle ended unexpectedly');
    }

    async json(options) {
        const response = await this.request(options);
        const text = await response.text();

        let data;
        try {
            data = text ? JSON.parse(text) : null;
        } catch {
            throw new HttpApiError(
                'Server returned invalid JSON',
                response,
            );
        }

        if (!response.ok) {
            throw new HttpApiError(
                `HTTP ${response.status} ${response.statusText}`,
                response,
            );
        }

        return data;
    }

    async #backoff(attempt) {
        const delay = Math.min(100 * 2 ** attempt, 1000);
        await new Promise((resolve) => setTimeout(resolve, delay));
    }
}

function createDemoServer() {
    return http.createServer(async (req, res) => {
        const url = new URL(req.url, `http://${req.headers.host}`);

        const sendJson = (status, payload) => {
            const text = JSON.stringify(payload);
            res.writeHead(status, {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(text),
            });
            res.end(text);
        };

        if (req.method === 'GET' && url.pathname === '/users') {
            sendJson(200, {
                users: [
                    { id: 1, name: 'Anita' },
                    { id: 2, name: 'Rahul' },
                ],
                active: url.searchParams.get('active'),
            });
            return;
        }

        if (req.method === 'GET' && url.pathname === '/health') {
            sendJson(200, { status: 'ok' });
            return;
        }

        if (req.method === 'POST' && url.pathname === '/users') {
            let raw = '';

            req.on('data', (chunk) => {
                raw += chunk;
                if (Buffer.byteLength(raw) > 1_000_000) {
                    req.destroy();
                }
            });

            req.on('end', () => {
                try {
                    const payload = JSON.parse(raw);

                    if (
                        !payload ||
                        typeof payload !== 'object' ||
                        typeof payload.name !== 'string' ||
                        payload.name.trim() === ''
                    ) {
                        sendJson(422, { error: 'name_is_required' });
                        return;
                    }

                    sendJson(201, {
                        id: 3,
                        name: payload.name.trim(),
                        created: true,
                    });
                } catch {
                    sendJson(400, { error: 'invalid_json' });
                }
            });

            return;
        }

        sendJson(404, { error: 'resource_not_found' });
    });
}

async function main() {
    const metrics = new RequestMetrics();

    metrics.on('request:start', (event) => {
        console.log(
            `request ${event.attempt}: ${event.method} ${event.url}`,
        );
    });

    metrics.on('response', (event) => {
        console.log(
            `response: HTTP ${event.status}, ${event.durationMs.toFixed(1)} ms`,
        );
    });

    metrics.on('error', (error) => {
        console.log(`transport error: ${error.message}`);
    });

    const server = createDemoServer();

    await new Promise((resolve) => {
        server.listen(0, '127.0.0.1', resolve);
    });

    const address = server.address();
    const baseUrl = `http://127.0.0.1:${address.port}`;

    const client = new FetchClient({
        timeoutMs: 3000,
        maxRetries: 1,
        metrics,
    });

    try {
        const users = await client.json({
            url: `${baseUrl}/users`,
            method: 'GET',
            query: { active: true },
            headers: { 'X-Request-ID': 'js-001' },
        });

        console.log('\nGET result:', users);

        const created = await client.json({
            url: `${baseUrl}/users`,
            method: 'POST',
            headers: { 'X-Request-ID': 'js-002' },
            body: { name: 'Priya' },
        });

        console.log('\nPOST result:', created);

        try {
            await client.json({
                url: `${baseUrl}/missing`,
                method: 'GET',
            });
        } catch (error) {
            console.log('\nExpected HTTP failure:', error.message);
        }

        console.log('\nMetrics:', metrics.snapshot());
    } finally {
        await new Promise((resolve) => server.close(resolve));
    }
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
