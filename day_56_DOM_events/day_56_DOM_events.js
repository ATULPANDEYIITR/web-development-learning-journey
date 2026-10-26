'use strict';

/*
 * DOM Events: a browser-style event system implemented with Node.js
 * standard JavaScript features.
 *
 * The implementation models:
 * - capturing
 * - target phase
 * - bubbling
 * - delegated listeners
 * - preventDefault
 * - stopPropagation
 * - stopImmediatePropagation
 * - once listeners
 * - passive listeners
 * - asynchronous event dispatch
 * - validation and event logging
 *
 * It deliberately models the mechanics instead of depending on a browser DOM.
 */

class EventDispatchError extends Error {}

const EventPhase = Object.freeze({
    CAPTURING: 'capturing',
    AT_TARGET: 'at-target',
    BUBBLING: 'bubbling'
});

class DomEvent {
    constructor(type, target, options = {}) {
        if (!type || typeof type !== 'string') {
            throw new EventDispatchError('Event type must be a non-empty string.');
        }

        this.type = type;
        this.target = target;
        this.bubbles = options.bubbles ?? true;
        this.cancelable = options.cancelable ?? true;
        this.defaultPrevented = false;
        this.propagationStopped = false;
        this.immediatePropagationStopped = false;
        this.phase = null;
        this.currentTarget = null;
        this.defaultAction = options.defaultAction ?? null;
    }

    stopPropagation() {
        this.propagationStopped = true;
    }

    stopImmediatePropagation() {
        this.immediatePropagationStopped = true;
        this.propagationStopped = true;
    }

    preventDefault() {
        if (this.cancelable) {
            this.defaultPrevented = true;
        }
    }
}

class EventTargetNode {
    constructor(name, options = {}) {
        if (!name) {
            throw new EventDispatchError('Node name is required.');
        }

        this.name = name;
        this.id = options.id ?? null;
        this.classes = new Set(options.classes ?? []);
        this.parent = null;
        this.children = [];
        this.listeners = new Map();
    }

    appendChild(child) {
        if (!(child instanceof EventTargetNode)) {
            throw new EventDispatchError('Child must be an EventTargetNode.');
        }

        if (child === this) {
            throw new EventDispatchError('A node cannot contain itself.');
        }

        let cursor = this;
        while (cursor) {
            if (cursor === child) {
                throw new EventDispatchError('Cannot create a cyclic tree.');
            }
            cursor = cursor.parent;
        }

        if (child.parent) {
            child.parent.children =
                child.parent.children.filter(node => node !== child);
        }

        child.parent = this;
        this.children.push(child);
    }

    addEventListener(type, callback, options = {}) {
        if (!type || typeof callback !== 'function') {
            throw new EventDispatchError(
                'An event type and callable listener are required.'
            );
        }

        const listener = {
            callback,
            capture: Boolean(options.capture),
            once: Boolean(options.once),
            passive: Boolean(options.passive),
            selector: options.selector ?? null
        };

        if (!this.listeners.has(type)) {
            this.listeners.set(type, []);
        }

        this.listeners.get(type).push(listener);
    }

    removeEventListener(type, callback, options = {}) {
        const listeners = this.listeners.get(type) ?? [];
        const capture = Boolean(options.capture);

        const index = listeners.findIndex(
            listener =>
                listener.callback === callback &&
                listener.capture === capture
        );

        if (index === -1) {
            return false;
        }

        listeners.splice(index, 1);
        return true;
    }

    matches(selector) {
        if (selector.startsWith('#')) {
            return this.id === selector.slice(1);
        }

        if (selector.startsWith('.')) {
            return this.classes.has(selector.slice(1));
        }

        return this.name === selector;
    }

    getPath() {
        const path = [];
        let current = this;

        while (current) {
            path.push(current);
            current = current.parent;
        }

        return path.reverse();
    }

    async dispatchEvent(event) {
        if (!(event instanceof DomEvent)) {
            throw new EventDispatchError('dispatchEvent requires a DomEvent.');
        }

        if (event.target !== this) {
            throw new EventDispatchError(
                'The event target must be the dispatching node.'
            );
        }

        const path = this.getPath();

        for (const node of path.slice(0, -1)) {
            if (event.propagationStopped) break;

            event.phase = EventPhase.CAPTURING;
            event.currentTarget = node;
            await this.invokeListeners(node, event, true);
        }

        if (!event.propagationStopped) {
            event.phase = EventPhase.AT_TARGET;
            event.currentTarget = this;

            await this.invokeListeners(this, event, true);

            if (!event.immediatePropagationStopped) {
                await this.invokeListeners(this, event, false);
            }
        }

        if (event.bubbles && !event.propagationStopped) {
            for (const node of path.slice(0, -1).reverse()) {
                if (event.propagationStopped) break;

                event.phase = EventPhase.BUBBLING;
                event.currentTarget = node;
                await this.invokeListeners(node, event, false);
            }
        }

        event.phase = null;
        event.currentTarget = null;

        if (!event.defaultPrevented && event.defaultAction) {
            await event.defaultAction();
        }

        return !event.defaultPrevented;
    }

    async invokeListeners(node, event, capture) {
        const listeners = node.listeners.get(event.type) ?? [];
        const removeAfterDispatch = [];

        for (const listener of [...listeners]) {
            if (listener.capture !== capture) continue;

            if (
                listener.selector &&
                !EventTargetNode.matchesDelegatedTarget(
                    event.target,
                    node,
                    listener.selector
                )
            ) {
                continue;
            }

            const previousPrevented = event.defaultPrevented;

            await listener.callback(event);

            if (listener.passive && event.defaultPrevented) {
                event.defaultPrevented = previousPrevented;
            }

            if (listener.once) {
                removeAfterDispatch.push(listener);
            }

            if (event.immediatePropagationStopped) {
                break;
            }
        }

        for (const listener of removeAfterDispatch) {
            const index = listeners.indexOf(listener);
            if (index !== -1) {
                listeners.splice(index, 1);
            }
        }
    }

    static matchesDelegatedTarget(target, root, selector) {
        let current = target;

        while (current) {
            if (current.matches(selector)) return true;
            if (current === root) break;
            current = current.parent;
        }

        return false;
    }
}

function logEvent(label) {
    return event => {
        console.log(
            `${label}: target=${event.target.name}, ` +
            `current=${event.currentTarget.name}, phase=${event.phase}`
        );
    };
}

async function main() {
    const documentNode = new EventTargetNode('document');
    const application = new EventTargetNode('section', { id: 'app' });
    const list = new EventTargetNode('ul', { id: 'users' });
    const row = new EventTargetNode('li', {
        id: 'user-17',
        classes: ['user-row']
    });
    const button = new EventTargetNode('button', { id: 'delete' });

    documentNode.appendChild(application);
    application.appendChild(list);
    list.appendChild(row);
    row.appendChild(button);

    console.log('=== Capture -> target -> bubble ===');

    documentNode.addEventListener(
        'click',
        logEvent('document capture'),
        { capture: true }
    );

    application.addEventListener(
        'click',
        logEvent('application capture'),
        { capture: true }
    );

    button.addEventListener('click', logEvent('button target'));

    application.addEventListener('click', logEvent('application bubble'));
    documentNode.addEventListener('click', logEvent('document bubble'));

    await button.dispatchEvent(new DomEvent('click', button));

    console.log('\n=== Delegation ===');

    list.addEventListener(
        'click',
        event => {
            console.log(
                `delegated handler accepted ${event.target.id}`
            );
        },
        { selector: '.user-row' }
    );

    await row.dispatchEvent(new DomEvent('click', row));

    console.log('\n=== Default action cancellation ===');

    button.addEventListener('navigate', event => {
        console.log('navigation policy: cancelling default behavior');
        event.preventDefault();
    });

    const navigation = new DomEvent('navigate', button, {
        defaultAction: async () => {
            console.log('DEFAULT: navigation executed');
        }
    });

    const navigationAllowed = await button.dispatchEvent(navigation);
    console.log(`default action allowed: ${navigationAllowed}`);

    console.log('\n=== Immediate propagation stop ===');

    const securityNode = new EventTargetNode('button');

    securityNode.addEventListener('secure', event => {
        console.log('security listener');
        event.stopImmediatePropagation();
    });

    securityNode.addEventListener('secure', () => {
        console.log('this listener must not execute');
    });

    await securityNode.dispatchEvent(new DomEvent('secure', securityNode));

    console.log('\n=== Once listener ===');

    let invocationCount = 0;

    securityNode.addEventListener(
        'audit',
        () => {
            invocationCount++;
            console.log(`audit listener invocation ${invocationCount}`);
        },
        { once: true }
    );

    await securityNode.dispatchEvent(new DomEvent('audit', securityNode));
    await securityNode.dispatchEvent(new DomEvent('audit', securityNode));

    if (invocationCount !== 1) {
        throw new Error('once listener invariant failed.');
    }

    console.log('\n=== Passive listener ===');

    const scrollingArea = new EventTargetNode('div');

    scrollingArea.addEventListener(
        'wheel',
        event => {
            event.preventDefault();
        },
        { passive: true }
    );

    const wheel = new DomEvent('wheel', scrollingArea, {
        defaultAction: async () => {
            console.log('DEFAULT: scrolling remains enabled');
        }
    });

    const scrollingAllowed = await scrollingArea.dispatchEvent(wheel);

    if (!scrollingAllowed) {
        throw new Error('Passive listener incorrectly cancelled scrolling.');
    }

    console.log('\n=== Non-bubbling event ===');

    const form = new EventTargetNode('form');
    const input = new EventTargetNode('input');

    form.appendChild(input);

    form.addEventListener('focus', () => {
        throw new Error('Non-bubbling focus event reached parent.');
    });

    await input.dispatchEvent(
        new DomEvent('focus', input, { bubbles: false })
    );

    console.log('\nAll assertions passed.');
}

main().catch(error => {
    console.error(`Event system failure: ${error.message}`);
    process.exitCode = 1;
});
