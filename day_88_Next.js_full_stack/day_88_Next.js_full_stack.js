'use strict';

/**
 * Next.js Full-Stack Architecture
 *
 * Demonstrates:
 * - Request routing
 * - Route handler behavior
 * - Server action behavior
 * - Middleware execution
 * - Environment configuration
 * - Authentication and authorization
 * - Async request processing
 * - Event-driven cache invalidation
 *
 * Runtime: Node.js 18+
 *
 * Run: node nextjs-fullstack.js
 *
 * No external dependencies.
 */

const crypto = require('node:crypto');
const { EventEmitter } = require('node:events');

// -------------------------------------------------------
// Application Errors
// -------------------------------------------------------

class ApplicationError extends Error {
    constructor(message, status = 500, code = 'INTERNAL_ERROR') {
        super(message);
        this.name = 'ApplicationError';
        this.status = status;
        this.code = code;
    }
}

class ConfigurationError extends ApplicationError {
    constructor(message) {
        super(message, 500, 'CONFIGURATION_ERROR');
    }
}

// -------------------------------------------------------
// Environment Configuration
// -------------------------------------------------------

class EnvironmentManager {
    constructor(source = process.env) {
        this.source = { ...source };
        this.config = null;
    }

    load() {
        const required = [
            'DATABASE_URL',
            'SESSION_SECRET',
            'APP_ENV'
        ];

        const missing = required.filter(
            key => !this.source[key]
        );

        if (missing.length > 0) {
            throw new ConfigurationError(
                `Missing environment variables: ${missing.join(', ')}`
            );
        }

        if (this.source.SESSION_SECRET.length < 32) {
            throw new ConfigurationError(
                'SESSION_SECRET must have at least 32 characters'
            );
        }

        if (!['development', 'production', 'test'].includes(
            this.source.APP_ENV
        )) {
            throw new ConfigurationError('Invalid APP_ENV');
        }

        let database;

        try {
            database = new URL(this.source.DATABASE_URL);
        } catch {
            throw new ConfigurationError('Invalid DATABASE_URL');
        }

        if (!['postgres:', 'postgresql:'].includes(database.protocol)) {
            throw new ConfigurationError(
                'DATABASE_URL must reference PostgreSQL'
            );
        }

        this.config = Object.freeze({
            appEnvironment: this.source.APP_ENV,
            databaseUrl: this.source.DATABASE_URL,
            sessionSecret: this.source.SESSION_SECRET,
            publicAppName: this.source.NEXT_PUBLIC_APP_NAME || 'Application'
        });

        return this.config;
    }

    publicConfiguration() {
        if (!this.config) {
            throw new ConfigurationError('Configuration not loaded');
        }

        return {
            appName: this.config.publicAppName
        };
    }
}

// -------------------------------------------------------
// Domain Types
// -------------------------------------------------------

class User {
    constructor(id, username, role = 'user') {
        if (!Number.isInteger(id) || id <= 0) {
            throw new ApplicationError('Invalid user ID', 400);
        }

        if (!['user', 'admin'].includes(role)) {
            throw new ApplicationError('Invalid user role', 400);
        }

        this.id = id;
        this.username = username;
        this.role = role;
        this.active = true;
        Object.seal(this);
    }
}

class Task {
    constructor(id, userId, title) {
        this.id = id;
        this.userId = userId;
        this.title = title;
        this.completed = false;
        this.createdAt = new Date();
    }

    serialize() {
        return {
            id: this.id,
            userId: this.userId,
            title: this.title,
            completed: this.completed,
            createdAt: this.createdAt.toISOString()
        };
    }
}

// -------------------------------------------------------
// Validation
// -------------------------------------------------------

const Validation = Object.freeze({
    taskTitle(value) {
        if (typeof value !== 'string') {
            throw new ApplicationError(
                'Title must be a string',
                400,
                'INVALID_TITLE'
            );
        }

        const title = value.trim();

        if (title.length === 0 || title.length > 120) {
            throw new ApplicationError(
                'Title must contain between 1 and 120 characters',
                400,
                'INVALID_TITLE'
            );
        }

        if (/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/.test(title)) {
            throw new ApplicationError(
                'Title contains invalid characters',
                400
            );
        }

        return title;
    },

    taskId(value) {
        const id = Number(value);

        if (!Number.isSafeInteger(id) || id <= 0) {
            throw new ApplicationError('Invalid task ID', 400);
        }

        return id;
    }
});

// -------------------------------------------------------
// Repository
// -------------------------------------------------------

class TaskRepository {
    #tasks = new Map();
    #nextId = 1;

    async create(userId, title) {
        const task = new Task(
            this.#nextId++,
            userId,
            title
        );

        this.#tasks.set(task.id, task);

        return task.serialize();
    }

    async findByUser(userId) {
        return Array.from(this.#tasks.values())
            .filter(task => task.userId === userId)
            .map(task => task.serialize());
    }

    async update(taskId, userId, changes) {
        const task = this.#tasks.get(taskId);

        if (!task) {
            throw new ApplicationError('Task not found', 404);
        }

        if (task.userId !== userId) {
            throw new ApplicationError('Forbidden', 403);
        }

        if (typeof changes.completed !== 'boolean') {
            throw new ApplicationError(
                'completed must be a boolean',
                400
            );
        }

        task.completed = changes.completed;

        return task.serialize();
    }

    async delete(taskId, userId) {
        const task = this.#tasks.get(taskId);

        if (!task) {
            throw new ApplicationError('Task not found', 404);
        }

        if (task.userId !== userId) {
            throw new ApplicationError('Forbidden', 403);
        }

        this.#tasks.delete(taskId);

        return true;
    }
}

// -------------------------------------------------------
// Event-Driven Cache
// -------------------------------------------------------

class CacheManager extends EventEmitter {
    #cache = new Map();

    set(key, value) {
        this.#cache.set(key, {
            value: structuredClone(value),
            createdAt: Date.now()
        });
    }

    get(key, maxAgeMs = 30000) {
        const entry = this.#cache.get(key);

        if (!entry) {
            return null;
        }

        if (Date.now() - entry.createdAt > maxAgeMs) {
            this.#cache.delete(key);
            return null;
        }

        return structuredClone(entry.value);
    }

    invalidate(key) {
        const existed = this.#cache.delete(key);

        this.emit('invalidated', {
            key,
            existed,
            timestamp: new Date().toISOString()
        });
    }

    clear() {
        this.#cache.clear();
    }
}

// -------------------------------------------------------
// Middleware
// -------------------------------------------------------

class ApplicationMiddleware {
    constructor() {
        this.protectedPrefixes = [
            '/dashboard',
            '/api/tasks'
        ];
    }

    async execute(request) {
        const requestId = crypto.randomUUID();

        request.requestId = requestId;

        if (
            request.pathname.includes('\0') ||
            request.pathname.split('/').includes('..')
        ) {
            throw new ApplicationError('Invalid path', 400);
        }

        const protectedRoute = this.protectedPrefixes.some(
            prefix =>
                request.pathname === prefix ||
                request.pathname.startsWith(prefix + '/')
        );

        if (protectedRoute && !request.user) {
            throw new ApplicationError(
                'Authentication required',
                401
            );
        }

        if (request.user && !request.user.active) {
            throw new ApplicationError(
                'Inactive account',
                403
            );
        }

        return {
            requestId,
            allowed: true
        };
    }
}

// -------------------------------------------------------
// Route Handler Layer
// -------------------------------------------------------

class RouteHandlerService {
    constructor(repository, cache) {
        this.repository = repository;
        this.cache = cache;
    }

    async dispatch(request) {
        const { method, pathname, user, body } = request;

        if (!user) {
            throw new ApplicationError(
                'Authentication required',
                401
            );
        }

        if (pathname === '/api/tasks' && method === 'GET') {
            const key = `tasks:${user.id}`;

            const cached = this.cache.get(key);

            if (cached !== null) {
                return {
                    status: 200,
                    body: { tasks: cached, cached: true }
                };
            }

            const tasks = await this.repository.findByUser(user.id);

            this.cache.set(key, tasks);

            return {
                status: 200,
                body: { tasks, cached: false }
            };
        }

        if (pathname === '/api/tasks' && method === 'POST') {
            const title = Validation.taskTitle(body?.title);

            const task = await this.repository.create(
                user.id,
                title
            );

            this.cache.invalidate(`tasks:${user.id}`);

            return {
                status: 201,
                body: { task }
            };
        }

        const match = pathname.match(
            /^\/api\/tasks\/([1-9]\d*)$/
        );

        if (match && method === 'PATCH') {
            const taskId = Validation.taskId(match[1]);

            const task = await this.repository.update(
                taskId,
                user.id,
                body ?? {}
            );

            this.cache.invalidate(`tasks:${user.id}`);

            return {
                status: 200,
                body: { task }
            };
        }

        if (match && method === 'DELETE') {
            const taskId = Validation.taskId(match[1]);

            await this.repository.delete(taskId, user.id);

            this.cache.invalidate(`tasks:${user.id}`);

            return {
                status: 200,
                body: { deleted: true }
            };
        }

        throw new ApplicationError('Route not found', 404);
    }
}

// -------------------------------------------------------
// Server Action Layer
// -------------------------------------------------------

class ServerActionService {
    constructor(repository, cache) {
        this.repository = repository;
        this.cache = cache;
    }

    async createTask(context, formData) {
        const user = context.user;

        if (!user || !user.active) {
            throw new ApplicationError(
                'Authentication required',
                401
            );
        }

        const title = Validation.taskTitle(
            formData.get('title')
        );

        const task = await this.repository.create(
            user.id,
            title
        );

        this.cache.invalidate(`tasks:${user.id}`);

        return {
            success: true,
            task,
            revalidatedPath: '/dashboard'
        };
    }

    async completeTask(context, taskId) {
        const user = context.user;

        if (!user || !user.active) {
            throw new ApplicationError(
                'Authentication required',
                401
            );
        }

        const id = Validation.taskId(taskId);

        const task = await this.repository.update(
            id,
            user.id,
            { completed: true }
        );

        this.cache.invalidate(`tasks:${user.id}`);

        return {
            success: true,
            task,
            revalidatedPath: '/dashboard'
        };
    }
}

// -------------------------------------------------------
// Application Runtime
// -------------------------------------------------------

class Application {
    constructor(environment) {
        this.config = environment.load();

        this.repository = new TaskRepository();
        this.cache = new CacheManager();
        this.middleware = new ApplicationMiddleware();

        this.routes = new RouteHandlerService(
            this.repository,
            this.cache
        );

        this.actions = new ServerActionService(
            this.repository,
            this.cache
        );

        this.cache.on('invalidated', event => {
            console.log('Cache invalidated:', event.key);
        });
    }

    async handle(request) {
        try {
            const parsed = new URL(
                request.url,
                'http://localhost'
            );

            const normalized = {
                method: request.method,
                pathname: parsed.pathname,
                user: request.user ?? null,
                body: request.body ?? {}
            };

            const middlewareResult =
                await this.middleware.execute(normalized);

            const result = await this.routes.dispatch(normalized);

            return {
                ...result,
                headers: {
                    'X-Request-ID': middlewareResult.requestId,
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-store'
                }
            };
        } catch (error) {
            const status = error instanceof ApplicationError
                ? error.status
                : 500;

            return {
                status,
                body: {
                    error: status === 500
                        ? 'Internal server error'
                        : error.message,
                    code: error.code || 'INTERNAL_ERROR'
                }
            };
        }
    }
}

// -------------------------------------------------------
// Demonstration
// -------------------------------------------------------

async function main() {
    const environment = new EnvironmentManager({
        DATABASE_URL:
            'postgresql://app:secret@localhost:5432/tasks',
        SESSION_SECRET: crypto.randomBytes(48).toString('hex'),
        APP_ENV: 'development',
        NEXT_PUBLIC_APP_NAME: 'Full Stack Task Manager'
    });

    const application = new Application(environment);

    const alice = new User(1, 'alice');

    console.log('\nAPPLICATION CONFIGURATION');
    console.log(environment.publicConfiguration());

    console.log('\nUNAUTHENTICATED REQUEST');

    console.log(await application.handle({
        method: 'GET',
        url: '/api/tasks'
    }));

    console.log('\nCREATE TASK');

    console.log(await application.handle({
        method: 'POST',
        url: '/api/tasks',
        user: alice,
        body: {
            title: 'Build Next.js route handlers'
        }
    }));

    console.log('\nGET TASKS');

    console.log(await application.handle({
        method: 'GET',
        url: '/api/tasks',
        user: alice
    }));

    console.log('\nGET TASKS FROM CACHE');

    console.log(await application.handle({
        method: 'GET',
        url: '/api/tasks',
        user: alice
    }));

    console.log('\nSERVER ACTION');

    const formData = new FormData();
    formData.set('title', 'Build server actions');

    console.log(
        await application.actions.createTask(
            { user: alice },
            formData
        )
    );

    console.log('\nCOMPLETE TASK');

    console.log(
        await application.actions.completeTask(
            { user: alice },
            1
        )
    );

    console.log('\nINVALID INPUT');

    console.log(await application.handle({
        method: 'POST',
        url: '/api/tasks',
        user: alice,
        body: { title: '' }
    }));

    console.log('\nALL DEMONSTRATIONS COMPLETED');
}

main().catch(error => {
    console.error('Application startup failed:', error.message);
    process.exitCode = 1;
});
