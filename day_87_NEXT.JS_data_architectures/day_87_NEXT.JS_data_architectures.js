'use strict';

/*
 * Next.js Data Architecture
 *
 * Server-side fetching, cache management, tag and path invalidation,
 * stale-while-revalidate, dynamic rendering and event-driven updates.
 *
 * Runtime: Node.js 20+
 * Dependencies: Node.js standard library only.
 */

const { EventEmitter } = require('node:events');
const crypto = require('node:crypto');


class ArchitectureError extends Error {
    constructor(message, code = 'ARCHITECTURE_ERROR') {
        super(message);
        this.name = 'ArchitectureError';
        this.code = code;
    }
}


const CachePolicy = Object.freeze({
    CACHE: 'CACHE',
    NO_STORE: 'NO_STORE'
});


const RenderStrategy = Object.freeze({
    STATIC: 'STATIC',
    DYNAMIC: 'DYNAMIC',
    PARTIAL: 'PARTIAL'
});


const EntryState = Object.freeze({
    HIT: 'HIT',
    MISS: 'MISS',
    STALE: 'STALE'
});


function validatePositiveInteger(value, name) {
    if (!Number.isSafeInteger(value) || value <= 0) {
        throw new ArchitectureError(
            `${name} must be a positive safe integer.`,
            'INVALID_ARGUMENT'
        );
    }
}


function stableSerialize(value) {
    if (Array.isArray(value)) {
        return `[${value.map(stableSerialize).join(',')}]`;
    }

    if (value && typeof value === 'object') {
        return `{${Object.keys(value)
            .sort()
            .map(key => `${JSON.stringify(key)}:${stableSerialize(value[key])}`)
            .join(',')}}`;
    }

    return JSON.stringify(value);
}


function createCacheKey(namespace, parameters) {
    if (!namespace || typeof namespace !== 'string') {
        throw new ArchitectureError('Cache namespace is required.');
    }

    const digest = crypto
        .createHash('sha256')
        .update(stableSerialize(parameters))
        .digest('hex');

    return `${namespace}:${digest}`;
}


class Product {
    constructor({ id, name, price, category, stock, version = 1 }) {
        validatePositiveInteger(id, 'Product ID');

        if (typeof name !== 'string' || !name.trim()) {
            throw new ArchitectureError('Product name is required.');
        }

        if (!Number.isFinite(price) || price < 0) {
            throw new ArchitectureError('Invalid product price.');
        }

        validatePositiveInteger(version, 'Product version');

        if (!Number.isSafeInteger(stock) || stock < 0) {
            throw new ArchitectureError('Invalid stock quantity.');
        }

        this.id = id;
        this.name = name;
        this.price = price;
        this.category = category;
        this.stock = stock;
        this.version = version;

        Object.freeze(this);
    }
}


class ProductRepository {
    #products = new Map();

    constructor() {
        [
            new Product({
                id: 101,
                name: 'Laptop',
                price: 75000,
                category: 'Electronics',
                stock: 12
            }),
            new Product({
                id: 102,
                name: 'Keyboard',
                price: 2500,
                category: 'Accessories',
                stock: 45
            }),
            new Product({
                id: 103,
                name: 'Monitor',
                price: 18000,
                category: 'Electronics',
                stock: 8
            })
        ].forEach(product => this.#products.set(product.id, product));
    }

    async findById(id) {
        validatePositiveInteger(id, 'Product ID');

        // Represents database or external API latency.
        await new Promise(resolve => setTimeout(resolve, 20));

        const product = this.#products.get(id);

        if (!product) {
            throw new ArchitectureError(
                `Product ${id} does not exist.`,
                'NOT_FOUND'
            );
        }

        return product;
    }

    async findAll() {
        await new Promise(resolve => setTimeout(resolve, 20));
        return [...this.#products.values()];
    }

    async update(id, changes) {
        const existing = await this.findById(id);

        const updated = new Product({
            ...existing,
            ...changes,
            id,
            version: existing.version + 1
        });

        this.#products.set(id, updated);
        return updated;
    }
}


class CacheStore extends EventEmitter {
    #entries = new Map();
    #tagIndex = new Map();
    #pathIndex = new Map();
    #inflight = new Map();
    #refreshing = new Set();

    constructor() {
        super();

        this.metrics = {
            hits: 0,
            misses: 0,
            staleHits: 0,
            writes: 0,
            invalidations: 0,
            refreshFailures: 0
        };
    }

    #index(index, key, identifier) {
        if (!index.has(identifier)) {
            index.set(identifier, new Set());
        }

        index.get(identifier).add(key);
    }

    #removeIndex(index, key, identifier) {
        const keys = index.get(identifier);

        if (!keys) return;

        keys.delete(key);

        if (keys.size === 0) {
            index.delete(identifier);
        }
    }

    #removeEntry(key) {
        const entry = this.#entries.get(key);
        if (!entry) return false;

        for (const tag of entry.tags) {
            this.#removeIndex(this.#tagIndex, key, tag);
        }

        for (const path of entry.paths) {
            this.#removeIndex(this.#pathIndex, key, path);
        }

        this.#entries.delete(key);
        return true;
    }

    read(key) {
        const entry = this.#entries.get(key);

        if (!entry) {
            this.metrics.misses++;
            return { state: EntryState.MISS, value: null };
        }

        if (Date.now() >= entry.expiresAt) {
            this.metrics.staleHits++;
            return {
                state: EntryState.STALE,
                value: entry.value
            };
        }

        this.metrics.hits++;

        return {
            state: EntryState.HIT,
            value: entry.value
        };
    }

    write(key, value, {
        ttlMs,
        tags = [],
        paths = []
    }) {
        if (!Number.isFinite(ttlMs) || ttlMs <= 0) {
            throw new ArchitectureError('TTL must be positive.');
        }

        if (tags.some(tag => typeof tag !== 'string' || !tag.trim())) {
            throw new ArchitectureError('Invalid cache tag.');
        }

        if (paths.some(path =>
            typeof path !== 'string' || !path.startsWith('/')
        )) {
            throw new ArchitectureError('Invalid cache path.');
        }

        this.#removeEntry(key);

        const entry = {
            value,
            createdAt: Date.now(),
            expiresAt: Date.now() + ttlMs,
            tags: new Set(tags),
            paths: new Set(paths)
        };

        this.#entries.set(key, entry);

        for (const tag of entry.tags) {
            this.#index(this.#tagIndex, key, tag);
        }

        for (const path of entry.paths) {
            this.#index(this.#pathIndex, key, path);
        }

        this.metrics.writes++;
        this.emit('cache:write', { key });
    }

    async getOrLoad(key, loader, options) {
        const current = this.read(key);

        if (current.state === EntryState.HIT) {
            return current.value;
        }

        if (current.state === EntryState.STALE) {
            // Serve stale data immediately. One background refresh
            // is allowed per key in this process.
            this.#scheduleRefresh(key, loader, options);
            return current.value;
        }

        if (this.#inflight.has(key)) {
            return this.#inflight.get(key);
        }

        const promise = (async () => {
            try {
                const value = await loader();
                this.write(key, value, options);
                return value;
            } finally {
                this.#inflight.delete(key);
            }
        })();

        this.#inflight.set(key, promise);
        return promise;
    }

    #scheduleRefresh(key, loader, options) {
        if (this.#refreshing.has(key)) return;

        this.#refreshing.add(key);

        const refresh = async () => {
            try {
                const value = await loader();

                // Do not overwrite a newer value installed by another
                // operation while the refresh was running.
                const current = this.#entries.get(key);

                if (!current || Date.now() >= current.expiresAt) {
                    this.write(key, value, options);
                    this.emit('cache:refresh', { key });
                }
            } catch (error) {
                this.metrics.refreshFailures++;
                this.emit('cache:refresh-error', {
                    key,
                    message: error.message
                });
            } finally {
                this.#refreshing.delete(key);
            }
        };

        setImmediate(refresh);
    }

    invalidateTag(tag) {
        const keys = [...(this.#tagIndex.get(tag) || [])];

        for (const key of keys) {
            this.#removeEntry(key);
        }

        this.metrics.invalidations += keys.length;

        this.emit('cache:invalidate', {
            type: 'tag',
            identifier: tag,
            count: keys.length
        });

        return keys.length;
    }

    invalidatePath(path) {
        const keys = [...(this.#pathIndex.get(path) || [])];

        for (const key of keys) {
            this.#removeEntry(key);
        }

        this.metrics.invalidations += keys.length;

        this.emit('cache:invalidate', {
            type: 'path',
            identifier: path,
            count: keys.length
        });

        return keys.length;
    }

    getReport() {
        const requests =
            this.metrics.hits +
            this.metrics.misses +
            this.metrics.staleHits;

        return {
            ...this.metrics,
            entries: this.#entries.size,
            hitRatio: requests
                ? (this.metrics.hits + this.metrics.staleHits) / requests
                : 0
        };
    }
}


class ProductDataService {
    constructor(repository, cache) {
        this.repository = repository;
        this.cache = cache;
    }

    async getProduct(id, policy = CachePolicy.CACHE) {
        validatePositiveInteger(id, 'Product ID');

        if (policy === CachePolicy.NO_STORE) {
            return this.repository.findById(id);
        }

        const key = createCacheKey('product', { id });

        return this.cache.getOrLoad(
            key,
            () => this.repository.findById(id),
            {
                ttlMs: 5000,
                tags: [`product:${id}`, 'products'],
                paths: [`/products/${id}`, '/products']
            }
        );
    }

    async getCatalog() {
        const key = createCacheKey('catalog', {
            collection: 'products'
        });

        return this.cache.getOrLoad(
            key,
            () => this.repository.findAll(),
            {
                ttlMs: 10000,
                tags: ['products'],
                paths: ['/products']
            }
        );
    }

    async updateProduct(id, changes) {
        const updated = await this.repository.update(id, changes);

        // A mutation invalidates dependent representations.
        this.cache.invalidateTag(`product:${id}`);
        this.cache.invalidateTag('products');

        return updated;
    }
}


class RenderingPolicy {
    static evaluate({
        usesCookies = false,
        usesHeaders = false,
        personalized = false,
        hasUncachedData = false,
        cachedComponents = true
    }) {
        if (personalized || usesCookies || usesHeaders || hasUncachedData) {
            return RenderStrategy.DYNAMIC;
        }

        return cachedComponents
            ? RenderStrategy.PARTIAL
            : RenderStrategy.STATIC;
    }
}


class ServerPageRenderer {
    constructor(dataService) {
        this.dataService = dataService;
    }

    async renderProduct(id, requestContext = {}) {
        const product = await this.dataService.getProduct(id);

        const strategy = RenderingPolicy.evaluate({
            personalized: Boolean(requestContext.userId),
            usesCookies: Boolean(requestContext.cookies),
            usesHeaders: Boolean(requestContext.headers),
            hasUncachedData: Boolean(requestContext.liveData)
        });

        return Object.freeze({
            path: `/products/${id}`,
            strategy,
            product,
            userId: requestContext.userId || null,
            renderedAt: new Date().toISOString()
        });
    }
}


class ArchitectureController extends EventEmitter {
    constructor(dataService, cache) {
        super();

        this.dataService = dataService;
        this.cache = cache;

        this.cache.on('cache:write', event =>
            this.emit('architecture:event', {
                type: 'CACHE_WRITE',
                ...event
            })
        );

        this.cache.on('cache:invalidate', event =>
            this.emit('architecture:event', {
                type: 'CACHE_INVALIDATION',
                ...event
            })
        );
    }

    async processProductUpdate(id, changes) {
        const updated = await this.dataService.updateProduct(
            id,
            changes
        );

        this.emit('architecture:event', {
            type: 'PRODUCT_UPDATED',
            productId: id,
            version: updated.version
        });

        return updated;
    }
}


async function run() {
    console.log('\nNEXT.JS DATA ARCHITECTURE');
    console.log('='.repeat(55));

    const repository = new ProductRepository();
    const cache = new CacheStore();
    const dataService = new ProductDataService(repository, cache);
    const renderer = new ServerPageRenderer(dataService);
    const controller = new ArchitectureController(dataService, cache);

    controller.on('architecture:event', event => {
        console.log('EVENT:', event);
    });

    console.log('\n1. Server-side fetching');

    const first = await dataService.getProduct(101);
    console.log(first);

    console.log('\n2. Cache hit');

    const second = await dataService.getProduct(101);
    console.log('Same cached product:', first === second);

    console.log('\n3. Uncached fetching');

    const uncached = await dataService.getProduct(
        101,
        CachePolicy.NO_STORE
    );

    console.log('Uncached version:', uncached.version);

    console.log('\n4. Concurrent request coalescing');

    const parallel = await Promise.all(
        Array.from(
            { length: 10 },
            () => dataService.getProduct(102)
        )
    );

    console.log('Completed requests:', parallel.length);

    console.log('\n5. Rendering policy');

    const publicPage = await renderer.renderProduct(101);

    const privatePage = await renderer.renderProduct(101, {
        userId: 'customer-501',
        cookies: true
    });

    console.log('Public:', publicPage.strategy);
    console.log('Private:', privatePage.strategy);

    console.log('\n6. Updating product and invalidating tags');

    await controller.processProductUpdate(101, {
        price: 72000,
        stock: 15
    });

    const refreshed = await dataService.getProduct(101);
    console.log('New price:', refreshed.price);

    console.log('\n7. Path-based revalidation');

    const removed = cache.invalidatePath('/products');
    console.log('Invalidated entries:', removed);

    console.log('\n8. Cache statistics');

    console.log(cache.getReport());

    console.log('\n9. Validation');

    try {
        await dataService.getProduct(-1);
    } catch (error) {
        console.log('Rejected:', error.message);
    }

    try {
        await dataService.getProduct(999);
    } catch (error) {
        console.log('Missing record:', error.message);
    }

    console.log('\n10. Rendering policy edge cases');

    console.table([
        {
            scenario: 'Public cached page',
            result: RenderingPolicy.evaluate({})
        },
        {
            scenario: 'Authenticated page',
            result: RenderingPolicy.evaluate({
                personalized: true
            })
        },
        {
            scenario: 'Request cookies',
            result: RenderingPolicy.evaluate({
                usesCookies: true
            })
        },
        {
            scenario: 'Uncached external data',
            result: RenderingPolicy.evaluate({
                hasUncachedData: true
            })
        }
    ]);

    console.log('\nExecution completed.');
}


if (require.main === module) {
    run().catch(error => {
        console.error('Application failure:', error);
        process.exitCode = 1;
    });
}

module.exports = {
    Product,
    ProductRepository,
    CacheStore,
    ProductDataService,
    RenderingPolicy,
    ServerPageRenderer,
    ArchitectureController,
    CachePolicy,
    RenderStrategy,
    createCacheKey
};
