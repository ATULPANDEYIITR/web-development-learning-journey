'use strict';

/*
 * Modern CSS browser/Node.js laboratory.
 *
 * This file complements the Python model by treating modern CSS as a
 * browser-facing system. It can run directly in Node.js and can also be
 * copied into a browser environment where document and CSSStyleSheet are
 * available.
 *
 * Demonstrated mechanisms:
 *   - CSS custom-property inheritance and runtime token changes
 *   - CSS.registerProperty() when available
 *   - CSS nesting
 *   - :is() and :where()
 *   - :has() for relational state
 *   - logical properties
 *   - CSS.supports() feature detection
 *   - event-driven validation state
 *   - stylesheet generation and diagnostics
 *
 * No npm dependency is required.
 */

const cssFeatures = {
  customProperties: 'color: var(--demo-color)',
  nesting: 'selector(&)',
  isSelector: 'selector(:is(*))',
  whereSelector: 'selector(:where(*))',
  hasSelector: 'selector(:has(*))',
  logicalProperties: 'margin-inline',
};

const designTokens = {
  '--brand': '#2563eb',
  '--brand-strong': '#1d4ed8',
  '--surface': '#ffffff',
  '--surface-raised': '#f8fafc',
  '--text': '#172033',
  '--muted': '#64748b',
  '--danger': '#b91c1c',
  '--success': '#15803d',
  '--space-1': '0.25rem',
  '--space-2': '0.5rem',
  '--space-3': '0.75rem',
  '--space-4': '1rem',
  '--space-6': '1.5rem',
  '--radius': '0.75rem',
};

const darkThemeTokens = {
  '--surface': '#0f172a',
  '--surface-raised': '#111827',
  '--text': '#e5e7eb',
  '--muted': '#94a3b8',
  '--brand': '#60a5fa',
  '--brand-strong': '#93c5fd',
};

function supportsCss(expression, value = null) {
  if (
    typeof CSS === 'undefined' ||
    typeof CSS.supports !== 'function'
  ) {
    return false;
  }

  return value === null
    ? CSS.supports(expression)
    : CSS.supports(expression, value);
}

function detectFeatures() {
  const results = {};

  for (const [name, expression] of Object.entries(cssFeatures)) {
    results[name] = supportsCss(expression);
  }

  return results;
}

function printFeatureReport() {
  console.log('\nMODERN CSS FEATURE DETECTION');
  console.log('============================');

  const results = detectFeatures();

  for (const [feature, supported] of Object.entries(results)) {
    console.log(`${feature.padEnd(22)} ${supported ? 'supported' : 'not detected'}`);
  }

  if (typeof CSS === 'undefined') {
    console.log(
      '\nRunning outside a browser: CSS.supports() is unavailable. '
      + 'Browser detection will become active when this file is loaded '
      + 'in a page.'
    );
  }
}

/*
 * A stylesheet generated with CSS nesting rather than pre-expanded
 * descendant selectors. The nested '&' keeps the parent relationship
 * explicit, while :has() expresses a relationship based on descendants.
 */
function buildModernStylesheet() {
  return `
:root {
  --brand: ${designTokens['--brand']};
  --brand-strong: ${designTokens['--brand-strong']};
  --surface: ${designTokens['--surface']};
  --surface-raised: ${designTokens['--surface-raised']};
  --text: ${designTokens['--text']};
  --muted: ${designTokens['--muted']};
  --danger: ${designTokens['--danger']};
  --success: ${designTokens['--success']};
  --space-1: ${designTokens['--space-1']};
  --space-2: ${designTokens['--space-2']};
  --space-3: ${designTokens['--space-3']};
  --space-4: ${designTokens['--space-4']};
  --space-6: ${designTokens['--space-6']};
  --radius: ${designTokens['--radius']};

  color-scheme: light;
  font-family: system-ui, sans-serif;
}

:root[data-theme="dark"] {
  --brand: ${darkThemeTokens['--brand']};
  --brand-strong: ${darkThemeTokens['--brand-strong']};
  --surface: ${darkThemeTokens['--surface']};
  --surface-raised: ${darkThemeTokens['--surface-raised']};
  --text: ${darkThemeTokens['--text']};
  --muted: ${darkThemeTokens['--muted']};
  color-scheme: dark;
}

.application {
  max-inline-size: 72rem;
  margin-inline: auto;
  padding-block: var(--space-6);
  padding-inline: var(--space-4);
  color: var(--text);
  background: var(--surface);

  & > header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-4);
  }

  & .toolbar {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);

    &:has(button[aria-expanded="true"]) {
      outline: 2px solid var(--brand);
      outline-offset: 0.25rem;
    }
  }
}

.card {
  padding-block: var(--space-4);
  padding-inline: var(--space-4);
  border: 1px solid var(--muted);
  border-radius: var(--radius);
  background: var(--surface-raised);

  &:is(:hover, :focus-within) {
    border-color: var(--brand);
  }

  &:where(.compact) {
    padding-block: var(--space-2);
  }

  &:has(.error-message) {
    border-color: var(--danger);
  }
}

.field {
  display: grid;
  gap: var(--space-2);

  &:has(input:invalid) {
    & > label {
      color: var(--danger);
    }

    & > input {
      border-color: var(--danger);
    }
  }

  &:has(input:valid) {
    & > .status {
      color: var(--success);
    }
  }
}

.field :is(input, select, textarea) {
  inline-size: 100%;
  box-sizing: border-box;
  padding-block: var(--space-2);
  padding-inline: var(--space-3);
}

.field :where(.help, .status) {
  font-size: 0.875rem;
  color: var(--muted);
}

.notice {
  margin-block: var(--space-4);
  padding-block: var(--space-3);
  padding-inline: var(--space-4);
  border-inline-start: 4px solid var(--brand);
}
`.trim();
}

function createStylesheetInBrowser() {
  if (typeof document === 'undefined') {
    console.log(
      '\ncreateStylesheetInBrowser(): document is unavailable in Node.js.'
    );
    return null;
  }

  const style = document.createElement('style');
  style.dataset.modernCssDemo = 'true';
  style.textContent = buildModernStylesheet();
  document.head.appendChild(style);

  return style;
}

/*
 * Runtime custom-property changes demonstrate why custom properties are
 * useful for theming: component rules remain unchanged while the values
 * consumed through var() change at the scope where they are overridden.
 */
function applyTheme(theme) {
  if (typeof document === 'undefined') {
    throw new Error('applyTheme() requires a browser document.');
  }

  const root = document.documentElement;

  if (theme === 'dark') {
    root.dataset.theme = 'dark';
  } else if (theme === 'light') {
    delete root.dataset.theme;
  } else {
    throw new RangeError('Theme must be "light" or "dark".');
  }
}

function readComputedToken(name) {
  if (typeof document === 'undefined') {
    throw new Error('readComputedToken() requires a browser document.');
  }

  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();

  if (!value) {
    throw new Error(`Custom property ${name} is not defined.`);
  }

  return value;
}

/*
 * CSS.registerProperty() gives a custom property a known syntax, inheritance
 * behavior, and initial value. This matters for typed animation and for
 * catching invalid values at the CSS property boundary.
 */
function registerAccentProperty() {
  if (
    typeof CSS === 'undefined' ||
    typeof CSS.registerProperty !== 'function'
  ) {
    return false;
  }

  try {
    CSS.registerProperty({
      name: '--accent-angle',
      syntax: '<angle>',
      inherits: false,
      initialValue: '0deg',
    });
    return true;
  } catch (error) {
    /*
     * Registration can fail if the property was already registered. That is
     * a recoverable setup condition rather than a reason to stop the demo.
     */
    console.warn('Custom property registration:', error.message);
    return false;
  }
}

/*
 * :has() is especially useful when the state belongs semantically to a child
 * but the visual response belongs to the containing component.
 */
function bindFormStateLogging(form) {
  if (!(form instanceof HTMLFormElement)) {
    throw new TypeError('bindFormStateLogging() expects an HTMLFormElement.');
  }

  const update = () => {
    const invalid = form.querySelector(':invalid');

    /*
     * The CSS stylesheet can react directly with .field:has(input:invalid).
     * JavaScript only observes the state here so that the event-driven
     * behavior is visible during this demonstration.
     */
    console.log(
      invalid
        ? `Form contains invalid control: ${invalid.name || invalid.type}`
        : 'Form has no invalid controls'
    );
  };

  form.addEventListener('input', update);
  form.addEventListener('change', update);
  update();

  return () => {
    form.removeEventListener('input', update);
    form.removeEventListener('change', update);
  };
}

function createDemoMarkup() {
  return `
<section class="application" aria-labelledby="demo-title">
  <header>
    <div>
      <h1 id="demo-title">Modern CSS laboratory</h1>
      <p>Custom properties, nesting, relational selectors, and logical layout.</p>
    </div>

    <div class="toolbar">
      <button type="button" data-theme-button="light">Light</button>
      <button type="button" data-theme-button="dark">Dark</button>
    </div>
  </header>

  <article class="card">
    <h2>Profile settings</h2>

    <form class="settings-form">
      <div class="field">
        <label for="email">Email</label>
        <input
          id="email"
          name="email"
          type="email"
          required
          aria-describedby="email-help"
        >
        <span id="email-help" class="help">
          Enter a valid email address.
        </span>
        <span class="status" aria-live="polite"></span>
      </div>
    </form>
  </article>

  <p class="notice">
    The notice uses border-inline-start, so its leading edge follows the
    writing direction.
  </p>
</section>
`.trim();
}

function initializeBrowserDemo() {
  if (typeof document === 'undefined') {
    return;
  }

  createStylesheetInBrowser();

  document.body.insertAdjacentHTML(
    'afterbegin',
    createDemoMarkup()
  );

  for (const button of document.querySelectorAll('[data-theme-button]')) {
    button.addEventListener('click', () => {
      applyTheme(button.dataset.themeButton);
    });
  }

  const form = document.querySelector('.settings-form');

  if (form) {
    bindFormStateLogging(form);
  }

  registerAccentProperty();

  console.log('Initial --brand:', readComputedToken('--brand'));
}

/*
 * This helper does not attempt to parse all CSS. It performs targeted checks
 * that are useful for a small design-system stylesheet.
 */
function analyzeStylesheet(cssText) {
  const patterns = {
    customProperties: /--[\w-]+\s*:/g,
    varFunctions: /\bvar\(/g,
    nestingAmpersands: /&/g,
    isSelectors: /:is\(/g,
    whereSelectors: /:where\(/g,
    hasSelectors: /:has\(/g,
    logicalProperties:
      /\b(?:margin|padding|border|inset)-(?:block|inline)(?:-[\w]+)?\s*:/g,
  };

  const counts = {};

  for (const [name, pattern] of Object.entries(patterns)) {
    counts[name] = (cssText.match(pattern) || []).length;
  }

  return counts;
}

function detectPotentialArchitectureProblems(cssText) {
  const warnings = [];

  if (/\!important\b/.test(cssText)) {
    warnings.push(
      'Found !important. Review whether the cascade can be expressed '
      + 'through layers, specificity, or component boundaries instead.'
    );
  }

  if (/\b(?:margin|padding)-(?:left|right)\s*:/.test(cssText)) {
    warnings.push(
      'Physical left/right spacing appears. Check whether logical '
      + 'margin-inline or padding-inline better expresses the intent.'
    );
  }

  if (/\b(?:left|right|top|bottom)\s*:/.test(cssText)) {
    warnings.push(
      'Physical directional positioning appears. Check writing-mode and '
      + 'bidirectional-layout requirements.'
    );
  }

  if ((cssText.match(/:has\(/g) || []).length > 8) {
    warnings.push(
      'Many :has() selectors are present. Test representative DOM trees '
      + 'and style recalculation behavior.'
    );
  }

  return warnings;
}

function demonstrateIsAndWhere() {
  console.log('\n:is() AND :where()');
  console.log('==================');

  if (typeof document === 'undefined') {
    console.log(
      ':is() and :where() require a DOM for selector matching; '
      + 'their semantics are represented in the generated stylesheet.'
    );
    return;
  }

  const sample = document.createElement('div');

  sample.innerHTML = `
    <button class="primary">Save</button>
    <a class="secondary">Cancel</a>
    <span class="help">Help text</span>
  `;

  const isMatches = sample.querySelectorAll(
    ':is(button, a)'
  ).length;

  const whereMatches = sample.querySelectorAll(
    ':where(.help, .secondary)'
  ).length;

  console.log(':is(button, a) matches:', isMatches);
  console.log(':where(.help, .secondary) matches:', whereMatches);

  console.log(
    ':is() and :where() can group selectors for matching, but they differ '
    + 'in specificity: :where() contributes zero specificity.'
  );
}

function demonstrateLogicalProperties() {
  const declarations = {
    'padding-block': '1rem',
    'padding-inline': '1.25rem',
    'margin-inline': 'auto',
    'border-inline-start': '4px solid var(--brand)',
    'inset-block-start': '1rem',
  };

  console.log('\nLOGICAL PROPERTIES');
  console.log('==================');

  for (const [property, value] of Object.entries(declarations)) {
    console.log(`${property}: ${value};`);
  }

  console.log(
    'Logical properties express layout in terms of block and inline axes, '
    + 'allowing the same component rules to adapt to writing direction.'
  );
}

function runNodeLaboratory() {
  console.log('MODERN CSS JAVASCRIPT LABORATORY');
  console.log('================================');

  console.log('\nGenerated stylesheet size:', buildModernStylesheet().length);

  console.log('\nTargeted stylesheet analysis');
  console.log('----------------------------');

  const counts = analyzeStylesheet(buildModernStylesheet());

  for (const [feature, count] of Object.entries(counts)) {
    console.log(`${feature.padEnd(24)} ${count}`);
  }

  const warnings = detectPotentialArchitectureProblems(
    buildModernStylesheet()
  );

  if (warnings.length === 0) {
    console.log('\nArchitecture checks: no targeted warnings.');
  } else {
    console.log('\nArchitecture checks:');
    for (const warning of warnings) {
      console.log(`- ${warning}`);
    }
  }

  demonstrateIsAndWhere();
  demonstrateLogicalProperties();
  printFeatureReport();

  if (typeof document !== 'undefined') {
    initializeBrowserDemo();
  } else {
    console.log(
      '\nBrowser phase skipped. Load this file from an HTML page to activate '
      + 'runtime theming, DOM matching, form state, and CSSOM behavior.'
    );
  }
}

runNodeLaboratory();

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    analyzeStylesheet,
    applyTheme,
    buildModernStylesheet,
    createStylesheetInBrowser,
    detectFeatures,
    detectPotentialArchitectureProblems,
    designTokens,
    registerAccentProperty,
    supportsCss,
  };
}
