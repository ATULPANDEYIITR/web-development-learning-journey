'use strict';

/*
 * Browser APIs case study.
 *
 * This file is intended to run in a browser as a normal JavaScript file.
 * It models:
 *   - localStorage
 *   - sessionStorage
 *   - cookies
 *   - History API
 *   - URL and URLSearchParams
 *
 * The implementation uses browser APIs directly and adds validation,
 * quota handling, navigation events, and state management.
 */

class BrowserStateManager {
    constructor() {
        this.storagePrefix = 'browser-api-demo:';
        this.listeners = new Set();
    }

    validateKey(key) {
        if (typeof key !== 'string' || key.trim() === '') {
            throw new TypeError('Storage keys must be non-empty strings.');
        }
    }

    setPersistent(key, value) {
        this.validateKey(key);

        if (typeof value !== 'string') {
            throw new TypeError('localStorage values must be strings.');
        }

        localStorage.setItem(`${this.storagePrefix}${key}`, value);
    }

    getPersistent(key) {
        this.validateKey(key);
        return localStorage.getItem(`${this.storagePrefix}${key}`);
    }

    removePersistent(key) {
        this.validateKey(key);
        localStorage.removeItem(`${this.storagePrefix}${key}`);
    }

    setSession(key, value) {
        this.validateKey(key);

        if (typeof value !== 'string') {
            throw new TypeError('sessionStorage values must be strings.');
        }

        sessionStorage.setItem(`${this.storagePrefix}${key}`, value);
    }

    getSession(key) {
        this.validateKey(key);
        return sessionStorage.getItem(`${this.storagePrefix}${key}`);
    }

    subscribe(listener) {
        if (typeof listener !== 'function') {
            throw new TypeError('Storage listener must be a function.');
        }

        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    notify(event) {
        for (const listener of this.listeners) {
            try {
                listener(event);
            } catch (error) {
                console.error('Storage listener failed:', error);
            }
        }
    }

    setCookie(name, value, options = {}) {
        if (!/^[A-Za-z0-9_-]+$/.test(name)) {
            throw new TypeError('Cookie name contains unsupported characters.');
        }

        const encodedValue = encodeURIComponent(String(value));
        const parts = [`${name}=${encodedValue}`];

        parts.push(`Path=${options.path ?? '/'}`);

        if (options.maxAge !== undefined) {
            if (!Number.isInteger(options.maxAge) || options.maxAge < 0) {
                throw new RangeError('maxAge must be a non-negative integer.');
            }
            parts.push(`Max-Age=${options.maxAge}`);
        }

        if (options.sameSite !== undefined) {
            const allowed = new Set(['Strict', 'Lax', 'None']);
            if (!allowed.has(options.sameSite)) {
                throw new TypeError('Invalid SameSite value.');
            }

            if (options.sameSite === 'None' && options.secure !== true) {
                throw new Error('SameSite=None cookies require Secure.');
            }

            parts.push(`SameSite=${options.sameSite}`);
        }

        if (options.secure === true) {
            parts.push('Secure');
        }

        /*
         * HttpOnly cannot be created through document.cookie.
         * It is an HTTP response attribute and must be configured by a server.
         */
        document.cookie = parts.join('; ');
    }

    deleteCookie(name) {
        this.setCookie(name, '', {
            maxAge: 0,
            path: '/',
            sameSite: 'Lax',
            secure: location.protocol === 'https:'
        });
    }

    readCookie(name) {
        const target = `${name}=`;
        const cookie = document.cookie
            .split('; ')
            .find(entry => entry.startsWith(target));

        if (!cookie) {
            return null;
        }

        return decodeURIComponent(cookie.slice(target.length));
    }

    updateUrlParameter(name, value) {
        if (!name) {
            throw new TypeError('URL parameter name cannot be empty.');
        }

        const url = new URL(window.location.href);
        url.searchParams.set(name, value);

        /*
         * replaceState changes the address without causing a navigation.
         * It does not automatically reload the page.
         */
        window.history.replaceState(
            { source: 'browser-api-demo', updatedParameter: name },
            '',
            url
        );

        this.notify({
            type: 'history',
            operation: 'replaceState',
            url: url.href
        });
    }

    navigateWithHistory(path, state = {}) {
        const url = new URL(path, window.location.origin);

        window.history.pushState(
            {
                source: 'browser-api-demo',
                ...state
            },
            '',
            url
        );

        this.notify({
            type: 'history',
            operation: 'pushState',
            url: url.href,
            state: window.history.state
        });
    }

    currentUrlDetails() {
        const url = new URL(window.location.href);

        return {
            href: url.href,
            origin: url.origin,
            protocol: url.protocol,
            hostname: url.hostname,
            pathname: url.pathname,
            search: url.search,
            hash: url.hash,
            parameters: Object.fromEntries(url.searchParams.entries())
        };
    }
}

function renderState(container, state) {
    container.textContent = JSON.stringify(state, null, 2);
}

async function simulateAsyncWorkflow(manager) {
    await new Promise(resolve => setTimeout(resolve, 50));

    manager.setSession('workflow', 'profile-loaded');

    await new Promise(resolve => setTimeout(resolve, 50));

    manager.setPersistent('lastVisit', new Date().toISOString());

    return {
        sessionState: manager.getSession('workflow'),
        lastVisit: manager.getPersistent('lastVisit')
    };
}

function runBrowserApiDemo() {
    const manager = new BrowserStateManager();

    const output = document.createElement('pre');
    output.id = 'browser-api-output';
    document.body.appendChild(output);

    manager.subscribe(event => {
        console.debug('Browser state event:', event);
        renderState(output, {
            event,
            url: manager.currentUrlDetails(),
            session: manager.getSession('workflow'),
            persistent: manager.getPersistent('lastVisit')
        });
    });

    try {
        manager.setPersistent('theme', 'dark');
        manager.setSession('checkoutStep', 'payment');

        manager.setCookie('consent', 'essential', {
            sameSite: 'Lax',
            secure: location.protocol === 'https:',
            maxAge: 86400
        });

        manager.navigateWithHistory('/browser-api-demo?view=storage', {
            view: 'storage'
        });

        manager.updateUrlParameter('mode', 'interactive');

        console.table(manager.currentUrlDetails());
        console.log('Cookie:', manager.readCookie('consent'));

        window.addEventListener('popstate', event => {
            console.log('popstate:', {
                state: event.state,
                url: window.location.href
            });
        });

        simulateAsyncWorkflow(manager)
            .then(result => {
                console.log('Async workflow completed:', result);
                renderState(output, {
                    status: 'complete',
                    result,
                    url: manager.currentUrlDetails()
                });
            })
            .catch(error => {
                console.error('Async workflow failed:', error);
            });
    } catch (error) {
        console.error('Browser API operation failed:', error);
        renderState(output, {
            status: 'error',
            message: error.message
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runBrowserApiDemo, {
        once: true
    });
} else {
    runBrowserApiDemo();
}
