/*
 * CSS Cascade: Practical JavaScript Study File
 *
 * This file complements the Python cascade model by using browser-oriented
 * JavaScript concepts:
 *
 * - DOM elements
 * - classList
 * - inline styles
 * - computed styles
 * - CSSStyleDeclaration
 * - CSSOM rule inspection
 * - custom properties
 * - dynamic state changes
 * - specificity demonstrations
 * - debugging style conflicts
 * - MutationObserver
 * - performance-aware DOM updates
 *
 * Run in a browser by placing this file in an HTML page.
 *
 * It also contains a small fallback demo so that the file can be executed
 * with Node.js for the non-browser portions.
 */

"use strict";


// ============================================================================
// 1. Basic specificity model
// ============================================================================

function calculateSpecificity(selector) {
    /*
     * This educational implementation returns:
     * [ID, class/attribute/pseudo-class, type/pseudo-element]
     *
     * It intentionally does not implement every modern selector exception.
     */
    const idCount = (selector.match(/#[A-Za-z_][\w-]*/g) || []).length;
    const classCount = (selector.match(/\.[A-Za-z_][\w-]*/g) || []).length;
    const attributeCount = (selector.match(/\[[^\]]+\]/g) || []).length;
    const pseudoClassCount =
        (selector.match(/:(?!:)[A-Za-z_-][\w-]*(?:\([^)]*\))?/g) || []).length;
    const pseudoElementCount =
        (selector.match(/::[A-Za-z_-][\w-]*/g) || []).length;

    let simplified = selector
        .replace(/#[A-Za-z_][\w-]*/g, " ")
        .replace(/\.[A-Za-z_][\w-]*/g, " ")
        .replace(/\[[^\]]+\]/g, " ")
        .replace(/::?[A-Za-z_-][\w-]*(?:\([^)]*\))?/g, " ");

    const typeNames =
        simplified.match(/(?<![-\w])[A-Za-z][A-Za-z0-9_-]*/g) || [];

    return [
        idCount,
        classCount + attributeCount + pseudoClassCount,
        typeNames.length + pseudoElementCount
    ];
}

function compareSpecificity(first, second) {
    for (let index = 0; index < first.length; index += 1) {
        if (first[index] !== second[index]) {
            return first[index] - second[index];
        }
    }

    return 0;
}


// ============================================================================
// 2. Beginner cascade examples
// ============================================================================

function beginnerSpecificityDemo() {
    const selectors = [
        "p",
        ".card",
        "#main",
        "div.card",
        "#main .card"
    ];

    console.log("\nSpecificity examples:");

    for (const selector of selectors) {
        console.log(
            `${selector.padEnd(20)} -> ${calculateSpecificity(selector).join("-")}`
        );
    }
}

function sourceOrderDemo() {
    /*
     * Two declarations with equal specificity:
     *
     * .message { color: blue; }
     * .message { color: green; }
     *
     * The later declaration wins.
     */
    console.log("\nSource order concept:");
    console.log("Equal specificity + later applicable declaration = later value.");
}

function importantDemo() {
    /*
     * !important is not simply "stronger specificity."
     * It changes the importance level used during the cascade.
     */
    console.log("\n!important concept:");
    console.log(
        "A normal declaration and an important declaration do not compete on ordinary specificity first."
    );
}


// ============================================================================
// 3. Browser DOM demonstrations
// ============================================================================

function createDemoDOM() {
    if (typeof document === "undefined") {
        return null;
    }

    const existing = document.querySelector("#css-cascade-study");

    if (existing) {
        existing.remove();
    }

    const container = document.createElement("main");
    container.id = "css-cascade-study";
    container.className = "study-page";

    container.innerHTML = `
        <section class="card" id="featured-card">
            <h2 class="title">Cascade demonstration</h2>
            <p class="description">Inspect this element in DevTools.</p>
            <button class="button" id="save-button">Save</button>
        </section>
    `;

    document.body.appendChild(container);

    return container;
}

function addDemoStyles() {
    if (typeof document === "undefined") {
        return null;
    }

    const oldStyle = document.querySelector("#cascade-study-styles");

    if (oldStyle) {
        oldStyle.remove();
    }

    const style = document.createElement("style");
    style.id = "cascade-study-styles";

    /*
     * These rules intentionally conflict so that DevTools can be used to
     * inspect the cascade.
     */
    style.textContent = `
        .study-page {
            color: #333;
            font-family: Arial, sans-serif;
        }

        .card {
            padding: 20px;
            color: blue;
            background: white;
        }

        .card {
            color: green;
        }

        #featured-card {
            color: purple;
        }

        .card .title {
            color: navy;
        }

        #featured-card .title {
            color: crimson;
        }

        .button {
            color: white;
            background: royalblue;
        }

        #save-button {
            background: darkgreen;
        }
    `;

    document.head.appendChild(style);

    return style;
}


// ============================================================================
// 4. Computed style inspection
// ============================================================================

function inspectComputedStyle(selector) {
    if (typeof document === "undefined") {
        console.log("Computed styles require a browser DOM.");
        return null;
    }

    const element = document.querySelector(selector);

    if (!element) {
        console.warn(`Element not found: ${selector}`);
        return null;
    }

    const computedStyle = window.getComputedStyle(element);

    const selectedProperties = [
        "color",
        "background-color",
        "font-family",
        "font-size",
        "font-weight",
        "display",
        "padding",
        "margin"
    ];

    const result = {};

    for (const propertyName of selectedProperties) {
        result[propertyName] = computedStyle.getPropertyValue(propertyName);
    }

    console.table(result);

    return result;
}


// ============================================================================
// 5. Inline style and CSSStyleDeclaration
// ============================================================================

function inlineStyleDemo() {
    if (typeof document === "undefined") {
        console.log("Inline style demonstration requires a browser.");
        return;
    }

    const button = document.querySelector("#save-button");

    if (!button) {
        return;
    }

    /*
     * Inline styles are author declarations attached directly to an element.
     */
    button.style.backgroundColor = "orange";
    button.style.padding = "12px 20px";

    console.log("\nInline style attribute:");
    console.log(button.getAttribute("style"));

    console.log(
        "Computed background:",
        getComputedStyle(button).backgroundColor
    );
}


// ============================================================================
// 6. !important demonstration
// ============================================================================

function importantBrowserDemo() {
    if (typeof document === "undefined") {
        return;
    }

    const button = document.querySelector("#save-button");

    if (!button) {
        return;
    }

    /*
     * setProperty accepts a third argument for priority.
     *
     * setProperty(property, value, "important")
     */
    button.style.setProperty(
        "background-color",
        "red",
        "important"
    );

    console.log(
        "\n!important background:",
        getComputedStyle(button).backgroundColor
    );
}


// ============================================================================
// 7. Inheritance demonstration
// ============================================================================

function inheritanceDemo() {
    if (typeof document === "undefined") {
        return;
    }

    const container = document.querySelector("#featured-card");
    const description = document.querySelector(".description");

    if (!container || !description) {
        return;
    }

    container.style.color = "teal";

    /*
     * color is inherited by default.
     * The paragraph receives the parent's color unless another declaration
     * wins for the paragraph itself.
     */
    console.log(
        "\nInherited paragraph color:",
        getComputedStyle(description).color
    );

    /*
     * background-color does not normally inherit.
     */
    container.style.backgroundColor = "lightyellow";

    console.log(
        "Paragraph background:",
        getComputedStyle(description).backgroundColor
    );
}


// ============================================================================
// 8. CSS-wide keywords
// ============================================================================

function cssWideKeywordDemo() {
    if (typeof document === "undefined") {
        return;
    }

    const description = document.querySelector(".description");

    if (!description) {
        return;
    }

    description.style.color = "inherit";
    console.log(
        "\ncolor: inherit ->",
        getComputedStyle(description).color
    );

    description.style.color = "initial";
    console.log(
        "color: initial ->",
        getComputedStyle(description).color
    );

    description.style.color = "unset";
    console.log(
        "color: unset ->",
        getComputedStyle(description).color
    );

    /*
     * revert is useful when an author declaration should give way to an
     * earlier cascade origin or user-agent behavior where applicable.
     */
    description.style.color = "revert";
    console.log(
        "color: revert ->",
        getComputedStyle(description).color
    );
}


// ============================================================================
// 9. Custom properties
// ============================================================================

function customPropertyDemo() {
    if (typeof document === "undefined") {
        return;
    }

    const card = document.querySelector("#featured-card");
    const title = document.querySelector(".title");

    if (!card || !title) {
        return;
    }

    card.style.setProperty("--accent-color", "darkorange");

    /*
     * Custom properties inherit by default.
     */
    title.style.color = "var(--accent-color)";

    console.log(
        "\nCustom property:",
        getComputedStyle(title).getPropertyValue("--accent-color")
    );

    console.log(
        "Resolved title color:",
        getComputedStyle(title).color
    );
}


// ============================================================================
// 10. Inspecting stylesheet rules
// ============================================================================

function inspectStyleSheets() {
    if (typeof document === "undefined") {
        return [];
    }

    const stylesheetInformation = [];

    for (const styleSheet of document.styleSheets) {
        const information = {
            href: styleSheet.href,
            ruleCount: 0,
            rules: []
        };

        /*
         * Access to cssRules can fail for cross-origin stylesheets because
         * of browser security restrictions.
         */
        try {
            const rules = styleSheet.cssRules;

            information.ruleCount = rules.length;

            for (const rule of rules) {
                information.rules.push(rule.cssText);
            }
        } catch (error) {
            information.rules.push(
                "Rules unavailable because of stylesheet security restrictions."
            );
        }

        stylesheetInformation.push(information);
    }

    console.log("\nStylesheet inspection:");
    console.dir(stylesheetInformation, { depth: null });

    return stylesheetInformation;
}


// ============================================================================
// 11. Finding matching rules
// ============================================================================

function findRulesForElement(element, propertyName) {
    if (
        typeof document === "undefined" ||
        !element ||
        !propertyName
    ) {
        return [];
    }

    const matches = [];

    for (const styleSheet of document.styleSheets) {
        let rules;

        try {
            rules = styleSheet.cssRules;
        } catch {
            continue;
        }

        for (const rule of rules) {
            if (!rule.selectorText || !rule.style) {
                continue;
            }

            let selectorMatches = false;

            try {
                selectorMatches = element.matches(rule.selectorText);
            } catch {
                selectorMatches = false;
            }

            if (!selectorMatches) {
                continue;
            }

            const value = rule.style.getPropertyValue(propertyName);

            if (value) {
                matches.push({
                    selector: rule.selectorText,
                    property: propertyName,
                    value,
                    important: rule.style.getPropertyPriority(propertyName),
                    specificity: calculateSpecificity(rule.selectorText)
                });
            }
        }
    }

    return matches;
}

function debugProperty(selector, propertyName) {
    if (typeof document === "undefined") {
        console.log("Style debugging requires a browser.");
        return;
    }

    const element = document.querySelector(selector);

    if (!element) {
        console.warn(`Cannot debug ${selector}: element not found.`);
        return;
    }

    const matches = findRulesForElement(element, propertyName);

    console.group(`Debugging ${propertyName} on ${selector}`);

    console.table(matches);

    console.log(
        "Computed value:",
        getComputedStyle(element).getPropertyValue(propertyName)
    );

    console.log(
        "Inline value:",
        element.style.getPropertyValue(propertyName)
    );

    console.groupEnd();
}


// ============================================================================
// 12. State-driven styling
// ============================================================================

function stateDrivenDemo() {
    if (typeof document === "undefined") {
        return;
    }

    const card = document.querySelector("#featured-card");

    if (!card) {
        return;
    }

    /*
     * A class is usually preferable to repeatedly writing individual inline
     * styles because the class keeps styling rules in CSS.
     */
    card.classList.add("is-selected");

    console.log(
        "\nCurrent classes:",
        [...card.classList]
    );

    card.classList.toggle("is-selected");

    console.log(
        "After toggle:",
        [...card.classList]
    );
}


// ============================================================================
// 13. Avoiding unnecessary specificity
// ============================================================================

function specificityComparison() {
    const selectors = [
        ".button",
        ".card .button",
        ".page .card .button",
        "#application .page .card .button"
    ];

    console.log("\nSpecificity growth:");

    for (const selector of selectors) {
        console.log(
            selector,
            calculateSpecificity(selector)
        );
    }

    console.log(
        "Deep selector chains create stronger dependencies and can make later overrides harder."
    );
}


// ============================================================================
// 14. MutationObserver and dynamic debugging
// ============================================================================

function observeStyleChanges() {
    if (typeof MutationObserver === "undefined") {
        return null;
    }

    const target = document.querySelector("#featured-card");

    if (!target) {
        return null;
    }

    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            console.log(
                "DOM/style mutation:",
                mutation.type,
                mutation.attributeName
            );
        }
    });

    /*
     * Observing attributes is useful for diagnosing class/style changes that
     * dynamically alter the cascade.
     */
    observer.observe(target, {
        attributes: true,
        attributeFilter: ["class", "style"]
    });

    return observer;
}


// ============================================================================
// 15. Performance-aware DOM updates
// ============================================================================

function performanceDemo() {
    if (typeof document === "undefined") {
        return;
    }

    const card = document.querySelector("#featured-card");

    if (!card) {
        return;
    }

    /*
     * Prefer one class update when several visual properties belong to the
     * same state. This keeps the cascade in CSS and reduces JavaScript
     * style mutations.
     */
    card.classList.add("is-loading");

    /*
     * Reading computed style after a large batch of writes can cause the
     * browser to perform synchronization work. In performance-sensitive code,
     * separate write-heavy and read-heavy phases when possible.
     */
    const display = getComputedStyle(card).display;

    console.log("Display after state update:", display);

    card.classList.remove("is-loading");
}


// ============================================================================
// 16. CSS cascade debugging checklist
// ============================================================================

function printDebuggingChecklist() {
    console.log(`
CSS CASCADE DEBUGGING CHECKLIST

1. Inspect the exact element.
2. Identify the property that has the unexpected result.
3. Check which selectors match the element.
4. Look for declarations crossed out in DevTools.
5. Check whether one declaration is !important.
6. Compare specificity.
7. Compare source order if specificity ties.
8. Check inheritance from ancestors.
9. Check browser user-agent styles.
10. Check media queries and container queries.
11. Check CSS cascade layers.
12. Check custom-property definitions.
13. Check inline styles.
14. Check pseudo-class state such as :hover or :focus.
15. Check whether JavaScript changed classes or inline styles.
`);
}


// ============================================================================
// 17. Browser execution
// ============================================================================

function runBrowserStudy() {
    if (typeof document === "undefined") {
        return;
    }

    createDemoDOM();
    addDemoStyles();

    beginnerSpecificityDemo();
    sourceOrderDemo();
    importantDemo();

    inspectComputedStyle("#featured-card");
    inspectComputedStyle(".title");

    inlineStyleDemo();
    importantBrowserDemo();
    inheritanceDemo();
    cssWideKeywordDemo();
    customPropertyDemo();

    inspectStyleSheets();
    debugProperty("#featured-card", "color");
    debugProperty(".title", "color");

    specificityComparison();
    stateDrivenDemo();

    const observer = observeStyleChanges();

    performanceDemo();
    printDebuggingChecklist();

    /*
     * Disconnect the observer after the demonstration to avoid keeping an
     * unnecessary observer alive indefinitely.
     */
    if (observer) {
        setTimeout(() => observer.disconnect(), 1000);
    }
}


// ============================================================================
// 18. Node.js fallback
// ============================================================================

function runNodeStudy() {
    console.log("Running non-browser CSS cascade concepts in Node.js.");
    beginnerSpecificityDemo();
    sourceOrderDemo();
    importantDemo();
    specificityComparison();
    printDebuggingChecklist();
}

if (typeof window !== "undefined" && typeof document !== "undefined") {
    runBrowserStudy();
} else {
    runNodeStudy();
}
