"use strict";

/*
 * Backend Fundamentals
 * Node.js REST API architecture.
 *
 * Run:
 * node backend_fundamentals.js
 *
 * Endpoints:
 * GET    /health
 * GET    /api/v1/tasks
 * GET    /api/v1/tasks/:id
 * POST   /api/v1/tasks
 * PATCH  /api/v1/tasks/:id
 * DELETE /api/v1/tasks/:id
 */

const http = require("node:http");
const { randomUUID } = require("node:crypto");
const { performance } = require("node:perf_hooks");

const HOST = "127.0.0.1";
const PORT = 8001;
const MAX_BODY_SIZE = 16384;

// -----------------------------------------------------
// Domain errors
// -----------------------------------------------------

class HttpError extends Error {
    constructor(status, code, message) {
        super(message);
        this.status = status;
        this.code = code;
    }
}

class ValidationError extends HttpError {
    constructor(message) {
        super(400, "VALIDATION_ERROR", message);
    }
}

class NotFoundError extends HttpError {
    constructor(message) {
        super(404, "NOT_FOUND", message);
    }
}

// -----------------------------------------------------
// Task repository
// -----------------------------------------------------

class TaskRepository {
    #tasks = new Map();
    #nextId = 1;

    async create(data) {
        const now = new Date().toISOString();

        const task = Object.freeze({
            id: this.#nextId++,
            title: data.title,
            description: data.description,
            status: "pending",
            createdAt: now,
            updatedAt: now
        });

        this.#tasks.set(task.id, task);

        return task;
    }

    async findAll() {
        return Array.from(this.#tasks.values());
    }

    async findById(id) {
        const task = this.#tasks.get(id);

        if (!task) {
            throw new NotFoundError(
                `Task ${id} does not exist`
            );
        }

        return task;
    }

    async update(id, changes) {
        const current = await this.findById(id);

        const updated = Object.freeze({
            ...current,
            ...changes,
            updatedAt: new Date().toISOString()
        });

        this.#tasks.set(id, updated);

        return updated;
    }

    async delete(id) {
        if (!this.#tasks.delete(id)) {
            throw new NotFoundError(
                `Task ${id} does not exist`
            );
        }
    }
}

// -----------------------------------------------------
// Validation
// -----------------------------------------------------

class TaskValidator {
    static statuses = new Set([
        "pending",
        "in_progress",
        "completed"
    ]);

    static validateObject(data) {
        if (
            data === null ||
            typeof data !== "object" ||
            Array.isArray(data)
        ) {
            throw new ValidationError(
                "Request body must be a JSON object"
            );
        }
    }

    static validateTitle(value) {
        if (typeof value !== "string") {
            throw new ValidationError(
                "Title must be a string"
            );
        }

        const title = value.trim();

        if (!title || title.length > 150) {
            throw new ValidationError(
                "Title must contain 1 to 150 characters"
            );
        }

        return title;
    }

    static validateDescription(value) {
        if (typeof value !== "string") {
            throw new ValidationError(
                "Description must be a string"
            );
        }

        if (value.length > 2000) {
            throw new ValidationError(
                "Description exceeds 2000 characters"
            );
        }

        return value.trim();
    }

    static validateCreate(data) {
        this.validateObject(data);

        const allowed = new Set([
            "title",
            "description"
        ]);

        for (const key of Object.keys(data)) {
            if (!allowed.has(key)) {
                throw new ValidationError(
                    `Unknown field: ${key}`
                );
            }
        }

        if (!Object.hasOwn(data, "title")) {
            throw new ValidationError(
                "Title is required"
            );
        }

        return {
            title: this.validateTitle(data.title),
            description: this.validateDescription(
                data.description ?? ""
            )
        };
    }

    static validateUpdate(data) {
        this.validateObject(data);

        const allowed = new Set([
            "title",
            "description",
            "status"
        ]);

        const keys = Object.keys(data);

        if (keys.length === 0) {
            throw new ValidationError(
                "At least one update field is required"
            );
        }

        const result = {};

        for (const key of keys) {
            if (!allowed.has(key)) {
                throw new ValidationError(
                    `Unknown field: ${key}`
                );
            }

            switch (key) {
                case "title":
                    result.title = this.validateTitle(
                        data.title
                    );
                    break;

                case "description":
                    result.description =
                        this.validateDescription(
                            data.description
                        );
                    break;

                case "status":
                    if (!this.statuses.has(data.status)) {
                        throw new ValidationError(
                            "Invalid task status"
                        );
                    }

                    result.status = data.status;
                    break;
            }
        }

        return result;
    }
}

// -----------------------------------------------------
// Service layer
// -----------------------------------------------------

class TaskService {
    constructor(repository) {
        this.repository = repository;
    }

    async create(data) {
        const validated =
            TaskValidator.validateCreate(data);

        return this.repository.create(validated);
    }

    async list() {
        return this.repository.findAll();
    }

    async get(id) {
        return this.repository.findById(id);
    }

    async update(id, data) {
        const validated =
            TaskValidator.validateUpdate(data);

        return this.repository.update(id, validated);
    }

    async remove(id) {
        return this.repository.delete(id);
    }
}

// -----------------------------------------------------
// HTTP response utilities
// -----------------------------------------------------

function sendJSON(response, status, data) {
    const body = JSON.stringify(data);

    response.writeHead(status, {
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": Buffer.byteLength(body),
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff"
    });

    response.end(body);
}

// -----------------------------------------------------
// Request body parser
// -----------------------------------------------------

function readJSON(request) {
    return new Promise((resolve, reject) => {
        const contentType = (
            request.headers["content-type"] || ""
        ).split(";")[0].trim().toLowerCase();

        if (contentType !== "application/json") {
            reject(
                new HttpError(
                    415,
                    "UNSUPPORTED_MEDIA_TYPE",
                    "Expected application/json"
                )
            );
            request.resume();
            return;
        }

        let size = 0;
        const chunks = [];

        request.on("data", chunk => {
            size += chunk.length;

            if (size > MAX_BODY_SIZE) {
                reject(
                    new HttpError(
                        413,
                        "PAYLOAD_TOO_LARGE",
                        "Request body exceeds size limit"
                    )
                );

                request.destroy();
                return;
            }

            chunks.push(chunk);
        });

        request.on("end", () => {
            if (size === 0) {
                reject(
                    new ValidationError(
                        "Request body cannot be empty"
                    )
                );
                return;
            }

            try {
                const parsed = JSON.parse(
                    Buffer.concat(chunks).toString("utf8")
                );

                TaskValidator.validateObject(parsed);
                resolve(parsed);

            } catch (error) {
                reject(
                    error instanceof HttpError
                        ? error
                        : new HttpError(
                            400,
                            "INVALID_JSON",
                            "Malformed JSON request"
                        )
                );
            }
        });

        request.on("error", reject);
    });
}

// -----------------------------------------------------
// Router
// -----------------------------------------------------

class Router {
    #routes = [];

    register(method, pattern, handler) {
        const parameterNames = [];

        const regex = new RegExp(
            "^" + pattern.replace(
                /:([A-Za-z0-9_]+)/g,
                (_, name) => {
                    parameterNames.push(name);
                    return "([^/]+)";
                }
            ) + "$"
        );

        this.#routes.push({
            method,
            regex,
            parameterNames,
            handler
        });
    }

    async dispatch(context) {
        let methodMismatch = false;

        for (const route of this.#routes) {
            const match = context.pathname.match(
                route.regex
            );

            if (!match) {
                continue;
            }

            if (route.method !== context.method) {
                methodMismatch = true;
                continue;
            }

            const params = {};

            route.parameterNames.forEach(
                (name, index) => {
                    try {
                        params[name] = decodeURIComponent(
                            match[index + 1]
                        );
                    } catch {
                        throw new ValidationError(
                            "Invalid URL parameter encoding"
                        );
                    }
                }
            );

            context.params = params;

            return route.handler(context);
        }

        if (methodMismatch) {
            throw new HttpError(
                405,
                "METHOD_NOT_ALLOWED",
                "HTTP method is not supported for this route"
            );
        }

        throw new NotFoundError(
            "Route does not exist"
        );
    }
}

// -----------------------------------------------------
// Controllers
// -----------------------------------------------------

class TaskController {
    constructor(service) {
        this.service = service;
    }

    list = async () => {
        const tasks = await this.service.list();

        return {
            status: 200,
            body: {
                count: tasks.length,
                data: tasks
            }
        };
    };

    get = async context => {
        const task = await this.service.get(
            parseTaskId(context.params.id)
        );

        return {
            status: 200,
            body: { data: task }
        };
    };

    create = async context => {
        const task = await this.service.create(
            context.body
        );

        return {
            status: 201,
            body: { data: task }
        };
    };

    update = async context => {
        const task = await this.service.update(
            parseTaskId(context.params.id),
            context.body
        );

        return {
            status: 200,
            body: { data: task }
        };
    };

    remove = async context => {
        await this.service.remove(
            parseTaskId(context.params.id)
        );

        return {
            status: 200,
            body: {
                message: "Task deleted successfully"
            }
        };
    };
}

function parseTaskId(value) {
    if (!/^[1-9]\d*$/.test(value)) {
        throw new ValidationError(
            "Task ID must be a positive integer"
        );
    }

    const id = Number(value);

    if (!Number.isSafeInteger(id)) {
        throw new ValidationError(
            "Task ID exceeds supported range"
        );
    }

    return id;
}

// -----------------------------------------------------
// Middleware pipeline
// -----------------------------------------------------

function compose(middlewares, endpoint) {
    return middlewares.reduceRight(
        (next, middleware) =>
            context => middleware(context, next),
        endpoint
    );
}

async function requestIdMiddleware(context, next) {
    context.requestId = randomUUID();

    const result = await next(context);

    result.body.requestId = context.requestId;

    return result;
}

async function loggingMiddleware(context, next) {
    const started = performance.now();

    try {
        const result = await next(context);

        console.log({
            requestId: context.requestId,
            method: context.method,
            path: context.pathname,
            status: result.status,
            durationMs: Number(
                (performance.now() - started).toFixed(2)
            )
        });

        return result;

    } catch (error) {
        console.error({
            requestId: context.requestId,
            error: error.message
        });

        throw error;
    }
}

// -----------------------------------------------------
// Application composition
// -----------------------------------------------------

class Application {
    constructor() {
        this.repository = new TaskRepository();
        this.service = new TaskService(this.repository);
        this.controller = new TaskController(this.service);

        this.router = new Router();

        this.router.register(
            "GET",
            "/health",
            async () => ({
                status: 200,
                body: {
                    status: "healthy",
                    service: "task-api"
                }
            })
        );

        this.router.register(
            "GET",
            "/api/v1/tasks",
            this.controller.list
        );

        this.router.register(
            "POST",
            "/api/v1/tasks",
            this.controller.create
        );

        this.router.register(
            "GET",
            "/api/v1/tasks/:id",
            this.controller.get
        );

        this.router.register(
            "PATCH",
            "/api/v1/tasks/:id",
            this.controller.update
        );

        this.router.register(
            "DELETE",
            "/api/v1/tasks/:id",
            this.controller.remove
        );

        this.pipeline = compose(
            [
                requestIdMiddleware,
                loggingMiddleware
            ],
            context => this.router.dispatch(context)
        );
    }

    async handle(context) {
        try {
            const result = await this.pipeline(context);

            return result;

        } catch (error) {
            if (error instanceof HttpError) {
                return {
                    status: error.status,
                    body: {
                        error: error.code,
                        message: error.message,
                        requestId: context.requestId
                    }
                };
            }

            console.error(error);

            return {
                status: 500,
                body: {
                    error: "INTERNAL_ERROR",
                    message: "Unexpected server error",
                    requestId: context.requestId
                }
            };
        }
    }
}

// -----------------------------------------------------
// Server adapter
// -----------------------------------------------------

const application = new Application();

const server = http.createServer(async (request, response) => {
    const started = performance.now();

    try {
        const url = new URL(
            request.url,
            `http://${request.headers.host || HOST}`
        );

        const context = {
            method: request.method,
            pathname: url.pathname,
            query: url.searchParams,
            headers: request.headers,
            body: {},
            params: {}
        };

        if (["POST", "PATCH", "PUT"].includes(request.method)) {
            context.body = await readJSON(request);
        }

        const result = await application.handle(context);

        sendJSON(
            response,
            result.status,
            result.body
        );

    } catch (error) {
        const status = error instanceof HttpError
            ? error.status
            : 400;

        sendJSON(response, status, {
            error: error.code || "REQUEST_ERROR",
            message: error.message
        });

    } finally {
        const duration = (
            performance.now() - started
        ).toFixed(2);

        if (!response.destroyed) {
            response.setHeader(
                "Server-Timing",
                `total;dur=${duration}`
            );
        }
    }
});

server.listen(PORT, HOST, () => {
    console.log(
        `Task API running at http://${HOST}:${PORT}`
    );
});

// -----------------------------------------------------
// Graceful shutdown
// -----------------------------------------------------

function shutdown() {
    console.log("Shutting down HTTP server");

    server.close(error => {
        if (error) {
            console.error(error);
            process.exitCode = 1;
        }
    });

    setTimeout(() => {
        server.closeAllConnections();
    }, 5000).unref();
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

// -----------------------------------------------------
// Built-in integration test runner
// -----------------------------------------------------

async function runTests() {
    const app = new Application();

    const makeRequest = async (
        method,
        pathname,
        body = {}
    ) => app.handle({
        method,
        pathname,
        query: new URLSearchParams(),
        headers: {},
        body,
        params: {}
    });

    const health = await makeRequest(
        "GET",
        "/health"
    );

    console.assert(health.status === 200);

    const created = await makeRequest(
        "POST",
        "/api/v1/tasks",
        {
            title: "Configure middleware",
            description: "Build request pipeline"
        }
    );

    console.assert(created.status === 201);

    const id = created.body.data.id;

    const fetched = await makeRequest(
        "GET",
        `/api/v1/tasks/${id}`
    );

    console.assert(fetched.status === 200);

    const updated = await makeRequest(
        "PATCH",
        `/api/v1/tasks/${id}`,
        { status: "completed" }
    );

    console.assert(
        updated.body.data.status === "completed"
    );

    const invalid = await makeRequest(
        "POST",
        "/api/v1/tasks",
        { title: "" }
    );

    console.assert(invalid.status === 400);

    const missing = await makeRequest(
        "GET",
        "/api/v1/tasks/99999"
    );

    console.assert(missing.status === 404);

    const deleted = await makeRequest(
        "DELETE",
        `/api/v1/tasks/${id}`
    );

    console.assert(deleted.status === 200);

    console.log("All JavaScript integration tests passed.");
}

if (process.argv.includes("--test")) {
    server.close();
    runTests().catch(error => {
        console.error(error);
        process.exitCode = 1;
    });
}
