'use strict';

/**
 * Next.js Fundamentals: Event-driven routing and rendering model.
 *
 * Runtime: Node.js 18+
 *
 * Models:
 * - File-system route definitions
 * - Dynamic and catch-all segments
 * - Nested layout composition
 * - Client-side navigation
 * - Server/client module boundaries
 * - Prefetching and navigation events
 * - Request validation and error handling
 */

const { EventEmitter } = require('node:events');

class FrameworkError extends Error {
    constructor(message, code = 'FRAMEWORK_ERROR') {
        super(message);
        this.name = 'FrameworkError';
        this.code = code;
    }
}

const ComponentKind = Object.freeze({
    SERVER: 'server',
    CLIENT: 'client'
});

class RouteDefinition {
    constructor({ pattern, page, layouts = [], metadata = {} }) {
        if (typeof pattern !== 'string' || !pattern.startsWith('/')) {
            throw new FrameworkError('Invalid route pattern');
        }

        this.pattern = pattern;
        this.page = page;
        this.layouts = Object.freeze([...layouts]);
        this.metadata = Object.freeze({ ...metadata });
        this.segments = this.parse(pattern);

        Object.freeze(this.segments);
    }

    parse(pattern) {
        if (pattern === '/') return [];

        return pattern.slice(1).split('/').map(segment => {
            if (/^\[\.\.\.[A-Za-z_]\w*\]$/.test(segment)) {
                return {
                    name: segment.slice(4, -1),
                    type: 'catch-all'
                };
            }

            if (/^\[[A-Za-z_]\w*\]$/.test(segment)) {
                return {
                    name: segment.slice(1, -1),
                    type: 'dynamic'
                };
            }

            if (segment.includes('[') || segment.includes(']')) {
                throw new FrameworkError(
                    `Malformed route segment: ${segment}`
                );
            }

            return { name: segment, type: 'static' };
        });
    }
}

class FileSystemRouter {
    #routes = [];

    register(definition) {
        if (!(definition instanceof RouteDefinition)) {
            throw new TypeError('Expected RouteDefinition');
        }

        if (this.#routes.some(r => r.pattern === definition.pattern)) {
            throw new FrameworkError(
                `Duplicate route: ${definition.pattern}`,
                'DUPLICATE_ROUTE'
            );
        }

        this.#routes.push(definition);

        // Prioritize static segments over dynamic segments.
        this.#routes.sort((a, b) => {
            const staticA = a.segments.filter(
                s => s.type === 'static'
            ).length;

            const staticB = b.segments.filter(
                s => s.type === 'static'
            ).length;

            return staticB - staticA ||
                b.segments.length - a.segments.length;
        });
    }

    static normalize(path) {
        if (typeof path !== 'string' || path.length > 2048) {
            throw new FrameworkError('Invalid request path');
        }

        if (/^[a-z][a-z0-9+.-]*:/i.test(path) || path.startsWith('//')) {
            throw new FrameworkError(
                'Absolute URLs are not valid route paths'
            );
        }

        let url;

        try {
            url = new URL(path, 'http://internal.local');
        } catch {
            throw new FrameworkError('Malformed URL');
        }

        const decoded = url.pathname.split('/').map(segment => {
            try {
                return decodeURIComponent(segment);
            } catch {
                throw new FrameworkError('Invalid URL encoding');
            }
        });

        if (
            decoded.some(part =>
                part === '.' ||
                part === '..' ||
                part.includes('\\') ||
                part.includes('\0')
            )
        ) {
            throw new FrameworkError('Unsafe route path');
        }

        return {
            parts: decoded.filter(Boolean),
            query: url.searchParams
        };
    }

    resolve(path) {
        const { parts, query } = FileSystemRouter.normalize(path);

        for (const route of this.#routes) {
            const segments = route.segments;
            const hasCatchAll =
                segments.at(-1)?.type === 'catch-all';

            if (hasCatchAll) {
                if (parts.length < segments.length) continue;
            } else if (parts.length !== segments.length) {
                continue;
            }

            const params = {};
            let valid = true;

            for (let i = 0; i < segments.length; i++) {
                const segment = segments[i];
                const value = parts[i];

                if (segment.type === 'static' && segment.name !== value) {
                    valid = false;
                    break;
                }

                if (segment.type === 'dynamic') {
                    if (!value) {
                        valid = false;
                        break;
                    }
                    params[segment.name] = value;
                }

                if (segment.type === 'catch-all') {
                    const remaining = parts.slice(i);

                    if (!remaining.length) {
                        valid = false;
                        break;
                    }

                    params[segment.name] = remaining;
                }
            }

            if (valid) {
                return {
                    route,
                    params: Object.freeze(params),
                    query
                };
            }
        }

        throw new FrameworkError(
            `No matching route: ${path}`,
            'NOT_FOUND'
        );
    }

    listRoutes() {
        return this.#routes.map(route => route.pattern);
    }
}

class ComponentModule {
    constructor({
        name,
        kind = ComponentKind.SERVER,
        imports = [],
        features = []
    }) {
        this.name = name;
        this.kind = kind;
        this.imports = [...imports];
        this.features = new Set(features);
    }

    validate() {
        const clientFeatures = [
            'state',
            'effect',
            'browser-api',
            'event-handler'
        ];

        if (
            this.kind === ComponentKind.SERVER &&
            clientFeatures.some(feature =>
                this.features.has(feature)
            )
        ) {
            throw new FrameworkError(
                `${this.name} uses browser functionality but is a Server Component`
            );
        }
    }
}

class ModuleAnalyzer {
    constructor() {
        this.modules = new Map();
    }

    add(module) {
        module.validate();

        if (this.modules.has(module.name)) {
            throw new FrameworkError(
                `Duplicate module: ${module.name}`
            );
        }

        this.modules.set(module.name, module);
    }

    analyzeClientGraph(entry) {
        const result = new Set();
        const active = new Set();

        const visit = name => {
            if (active.has(name)) {
                throw new FrameworkError(
                    `Circular dependency detected: ${name}`
                );
            }

            if (result.has(name)) return;

            const module = this.modules.get(name);

            if (!module) {
                throw new FrameworkError(
                    `Missing dependency: ${name}`
                );
            }

            active.add(name);
            result.add(name);

            // Imports of a client entry join its client module graph.
            for (const dependency of module.imports) {
                visit(dependency);
            }

            active.delete(name);
        };

        visit(entry);
        return [...result];
    }
}

class NavigationController extends EventEmitter {
    #router;
    #currentPath = '/';
    #prefetched = new Map();
    #layoutState = new Map();

    constructor(router) {
        super();
        this.#router = router;
    }

    setLayoutState(layoutName, key, value) {
        if (!this.#layoutState.has(layoutName)) {
            this.#layoutState.set(layoutName, new Map());
        }

        this.#layoutState.get(layoutName).set(key, value);
    }

    getLayoutState(layoutName, key) {
        return this.#layoutState.get(layoutName)?.get(key);
    }

    async prefetch(path, loader) {
        if (typeof loader !== 'function') {
            throw new TypeError('Prefetch loader must be a function');
        }

        if (this.#prefetched.has(path)) return;

        this.emit('prefetch:start', { path });

        try {
            const result = await loader(path);
            this.#prefetched.set(path, result);

            this.emit('prefetch:complete', { path });
        } catch (error) {
            this.emit('prefetch:error', {
                path,
                message: error.message
            });

            // Prefetch failure must not break normal navigation.
        }
    }

    async navigate(path) {
        const resolved = this.#router.resolve(path);
        const previous = this.#currentPath;

        this.emit('navigation:start', {
            previous,
            destination: path
        });

        try {
            let payload = this.#prefetched.get(path);

            if (payload === undefined) {
                payload = {
                    route: resolved.route.pattern,
                    params: resolved.params
                };
            }

            this.#currentPath = path;

            this.emit('navigation:complete', {
                previous,
                current: path,
                route: resolved.route.pattern,
                payload
            });

            return {
                path,
                route: resolved.route.pattern,
                params: resolved.params
            };
        } catch (error) {
            this.emit('navigation:error', {
                path,
                message: error.message
            });

            throw error;
        }
    }

    get currentPath() {
        return this.#currentPath;
    }
}

function createApplication() {
    const router = new FileSystemRouter();

    const root = 'RootLayout';
    const blog = 'BlogLayout';
    const dashboard = 'DashboardLayout';

    const routes = [
        new RouteDefinition({
            pattern: '/',
            page: 'HomePage',
            layouts: [root]
        }),
        new RouteDefinition({
            pattern: '/about',
            page: 'AboutPage',
            layouts: [root]
        }),
        new RouteDefinition({
            pattern: '/blog',
            page: 'BlogIndexPage',
            layouts: [root, blog]
        }),
        new RouteDefinition({
            pattern: '/blog/[slug]',
            page: 'BlogPostPage',
            layouts: [root, blog]
        }),
        new RouteDefinition({
            pattern: '/dashboard',
            page: 'DashboardPage',
            layouts: [root, dashboard],
            metadata: { authenticated: true }
        }),
        new RouteDefinition({
            pattern: '/docs/[...slug]',
            page: 'DocumentationPage',
            layouts: [root]
        })
    ];

    routes.forEach(route => router.register(route));

    return router;
}

async function main() {
    console.log('NEXT.JS FUNDAMENTALS');
    console.log('='.repeat(50));

    const router = createApplication();

    console.log('\nREGISTERED ROUTES');
    console.table(router.listRoutes());

    console.log('\nROUTE RESOLUTION');

    for (const path of [
        '/',
        '/about',
        '/blog',
        '/blog/server-components',
        '/docs/app/routing/dynamic-segments',
        '/dashboard'
    ]) {
        const result = router.resolve(path);

        console.log({
            requested: path,
            page: result.route.page,
            params: result.params
        });
    }

    console.log('\nSERVER/CLIENT MODULE GRAPH');

    const analyzer = new ModuleAnalyzer();

    analyzer.add(new ComponentModule({
        name: 'Logo',
        kind: ComponentKind.SERVER
    }));

    analyzer.add(new ComponentModule({
        name: 'SearchInput',
        kind: ComponentKind.CLIENT,
        features: ['state', 'event-handler']
    }));

    analyzer.add(new ComponentModule({
        name: 'Navigation',
        kind: ComponentKind.SERVER,
        imports: ['Logo', 'SearchInput']
    }));

    console.log(
        'Client dependency graph:',
        analyzer.analyzeClientGraph('Navigation')
    );

    console.log('\nEVENT-DRIVEN NAVIGATION');

    const navigation = new NavigationController(router);

    for (const event of [
        'prefetch:start',
        'prefetch:complete',
        'navigation:start',
        'navigation:complete',
        'navigation:error'
    ]) {
        navigation.on(event, payload => {
            console.log(`[${event}]`, payload);
        });
    }

    navigation.setLayoutState('RootLayout', 'theme', 'dark');

    await navigation.prefetch('/blog/server-components', async path => {
        return {
            cachedPath: path,
            type: 'RSC navigation payload'
        };
    });

    await navigation.navigate('/blog/server-components');

    console.log(
        'Persistent layout state:',
        navigation.getLayoutState('RootLayout', 'theme')
    );

    console.log('\nFAILURE HANDLING');

    try {
        router.resolve('/missing');
    } catch (error) {
        console.log(error.code, error.message);
    }

    try {
        router.resolve('/%2e%2e/private');
    } catch (error) {
        console.log(error.code, error.message);
    }

    try {
        new ComponentModule({
            name: 'InvalidServerCounter',
            kind: ComponentKind.SERVER,
            features: ['state']
        }).validate();
    } catch (error) {
        console.log('Boundary validation:', error.message);
    }

    console.log('\nASSERTIONS');

    console.assert(router.resolve('/blog/next').params.slug === 'next');
    console.assert(router.resolve('/').route.page === 'HomePage');
    console.assert(
        router.resolve('/docs/app/routing').params.slug.length === 2
    );
    console.assert(navigation.currentPath === '/blog/server-components');

    console.log('All checks completed.');
}

main().catch(error => {
    console.error('Application failure:', error);
    process.exitCode = 1;
});
