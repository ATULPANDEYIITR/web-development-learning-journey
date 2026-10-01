# Modern CSS: Custom Properties, Nesting, `:is()`, `:where()`, `:has()`, and Logical Properties

## Scope

Modern CSS provides several mechanisms that change how component styles are expressed and maintained.

This project focuses on six closely related but distinct capabilities:

- **Custom properties** provide runtime-resolvable CSS values that can be inherited, overridden by scope, and consumed through `var()`.
- **CSS nesting** allows related selectors and declarations to be expressed inside a parent rule, reducing repetition while preserving selector relationships.
- **`:is()`** groups alternative selectors into one selector expression and contributes the specificity of its most specific argument.
- **`:where()`** also groups selectors, but deliberately contributes zero specificity, making it useful for defaults and low-specificity component rules.
- **`:has()`** is a relational pseudo-class that allows a selector to depend on the existence of a matching relative element.
- **Logical properties** express layout in terms of block and inline axes instead of assuming physical top, right, bottom, and left directions.

The three implementations approach the subject differently. The Python program builds executable models and generates a stylesheet. The JavaScript program treats CSS as a browser-facing runtime system with feature detection, DOM interaction, theming, and event-driven form state. The C++ program models a component-library audit engine that checks design-token dependencies and CSS architecture rules.

## Custom Properties

Custom properties are CSS declarations whose names begin with `--`.

A token definition such as `--color-brand: #2563eb` does not itself style an element. It creates a value that other declarations can consume:

`color: var(--color-brand);`

The important distinction is that custom properties participate in CSS's value and inheritance model. They are not equivalent to preprocessor variables.

A preprocessor variable is normally replaced before CSS reaches the browser. A custom property remains part of the stylesheet and can be changed at runtime or overridden by a more specific scope.

The generated project uses tokens for colors, spacing, radii, and other design-system values. This makes a theme change possible by changing token values instead of duplicating component rules.

For example, the JavaScript stylesheet defines light values under `:root` and overrides selected tokens under `[data-theme="dark"]`. The `.card` component continues to use `var(--surface)`, `var(--text)`, and `var(--brand)`.

### Inheritance and scope

Custom properties normally inherit. A component can therefore consume a token defined on an ancestor:

`--color-text: #172033;`

and later:

`color: var(--color-text);`

A descendant can override the token for itself and its descendants by defining another value for the same custom property.

This makes token scope an architectural decision. Global tokens belong naturally on `:root`, while component-specific tokens can be defined closer to the component.

### Fallbacks

`var()` supports a fallback:

`padding-inline: var(--space-4, 1rem);`

If `--space-4` is unavailable in the relevant custom-property environment, the fallback provides a usable value.

The Python resolver demonstrates this concept and deliberately distinguishes an undefined dependency with a fallback from an undefined dependency without one.

A fallback is not merely documentation. It is part of the declaration's value-processing behavior.

### Dependency chains

Tokens can reference other tokens:

`--surface: white;`

`--surface-raised: var(--surface);`

This creates a dependency graph.

The Python implementation resolves this graph recursively and detects cycles. The C++ implementation models the same problem as a directed graph and reports undefined dependencies and cycles.

A cycle such as:

`--a: var(--b);`

`--b: var(--a);`

should not be treated as a valid token architecture. Token systems become easier to maintain when dependencies flow from primitive values toward semantic values rather than forming circular relationships.

### Registered custom properties

The JavaScript implementation includes `CSS.registerProperty()` when the browser exposes it.

Registration can specify information such as:

- the accepted CSS syntax
- whether the property inherits
- the property's initial value

This is different from an ordinary unregistered custom property because the browser can understand additional constraints associated with the registered property.

The example registers `--accent-angle` as an `<angle>` with `0deg` as its initial value. The code also handles the possibility that the browser does not expose the registration API or that the property has already been registered.

## CSS Nesting

CSS nesting expresses a selector relationship inside its parent rule.

A traditional component might be written as:

`.application > header { ... }`

and:

`.application .toolbar { ... }`

With nesting, those relationships can be expressed inside `.application`:

`.application { ... }`

with nested rules for `& > header` and `& .toolbar`.

The `&` represents the nesting selector and makes the relationship to the parent explicit.

### Why nesting is different from preprocessing

Modern CSS nesting is a browser CSS feature. It should not automatically be thought of as a Sass-style preprocessing convenience.

The browser receives CSS that contains nested rules when the syntax is supported. The browser's CSS parser and style system determine how the nested rules participate in selector construction and the cascade.

This matters for debugging, browser support, tooling, and the precise selector semantics of nested rules.

### Nested state

The project uses nesting for states that are naturally associated with a component.

For example, the form field contains a nested relationship for an invalid descendant:

`.form-field { &:has(input:invalid) { ... } }`

The nesting expresses the component boundary, while `:has()` expresses the descendant relationship. These mechanisms solve different problems and are deliberately combined rather than treated as interchangeable.

## `:is()`

`:is()` represents a selector list as one functional pseudo-class.

A component can use:

`.field > :is(input, select, textarea)`

when the same declarations should apply to several form-control types.

This avoids repeating the declaration block for `input`, `select`, and `textarea`.

### Specificity behavior

`:is()` is not specificity-neutral.

Its specificity contribution is based on the most specific selector in its argument list. This means a selector using `:is()` must still be considered during cascade design.

The Python implementation includes a targeted specificity model and prints the calculated values for representative selectors. The purpose is to make the distinction from `:where()` explicit.

`:is()` is therefore appropriate when selector grouping is the main objective and the resulting specificity is acceptable for the component architecture.

## `:where()`

`:where()` has selector-grouping behavior similar to `:is()`, but its specificity contribution is zero.

The project uses it for supporting form text:

`.field :where(.help, .status)`

This is useful because helper and status styles are intended to provide defaults without becoming difficult for application-level styles to override.

### Choosing between `:is()` and `:where()`

The matching behavior can look similar while the cascade behavior is different.

| Mechanism | Selector grouping | Specificity contribution |
|---|---|---|
| `:is()` | Yes | Specificity of the most specific argument |
| `:where()` | Yes | Zero |
| `:has()` | Relational matching | Based on its selector argument |

A practical component library can use `:where()` for intentionally weak defaults and `:is()` where the grouped selector should retain meaningful cascade weight.

The distinction becomes particularly important in large component systems where accidental specificity accumulation produces long override chains.

## `:has()`

`:has()` is a relational pseudo-class.

Instead of asking only whether the selected element itself matches a condition, it can select an element based on a related element.

The project uses:

`.form-field:has(input:invalid)`

This means the `.form-field` becomes selectable when it contains a matching invalid input.

The CSS can therefore style the field boundary and label based on the input's state without requiring JavaScript to add a separate `.invalid` class to the field.

### Parent-aware component state

A common reason to use `:has()` is that the semantic state originates in one element while the visual response belongs to another.

In the form example:

- the `input` owns the browser's validity state
- the `.form-field` owns the component presentation
- `:has()` connects the two

The relationship is represented directly in CSS.

The JavaScript file listens to `input` and `change` events only to log the state for demonstration. The stylesheet itself contains the actual visual relationship through `:has()`.

### Scope and selector design

Broad selectors such as `.container:has(*)` communicate very little architectural intent and can make relationships difficult to reason about.

The project instead uses meaningful relationships such as:

`.toolbar:has(button[aria-expanded="true"])`

and:

`.form-field:has(input:invalid)`

These selectors express a concrete component state.

`:has()` should therefore be treated as a relational design tool rather than simply as a way to avoid adding classes.

## Logical Properties

Physical properties assume physical directions:

`margin-left`

`padding-right`

`border-top`

`left`

Logical properties instead describe CSS layout through block and inline axes.

Examples used by this project include:

`margin-inline: auto;`

`padding-inline: 1rem;`

`padding-block: 1rem;`

`border-block-start: 2px solid var(--color-danger);`

`min-inline-size: 0;`

This vocabulary separates layout intent from physical coordinates.

### Block and inline axes

The inline axis generally follows the direction in which text progresses.

The block axis generally represents the direction in which block-level content accumulates.

The exact physical orientation depends on the writing mode and direction.

This means a component using `padding-inline` does not need to hard-code separate left and right declarations merely to express horizontal spacing in a conventional left-to-right layout.

### Writing-mode-aware components

A notification using:

`border-inline-start: 4px solid var(--brand);`

expresses a leading-edge border rather than specifically saying that the border belongs on the left.

Likewise:

`margin-inline: auto;`

expresses horizontal centering in a normal horizontal writing mode without encoding the two physical side properties.

The Python `LogicalBox` model and the C++ audit engine both treat logical properties as architectural signals rather than simply as alternate spellings.

## How the Mechanisms Relate

These features operate at different layers of CSS architecture.

A useful component relationship is:

`custom properties -> component values`

`nesting -> component selector structure`

`:is()` -> grouped selector matching`

`:where()` -> grouped low-specificity defaults`

`:has()` -> relational component state`

`logical properties -> writing-mode-aware layout`

They can be combined without making them interchangeable.

For example, the form field implementation uses a custom property for the error color, nesting to keep field-specific rules together, `:has()` to detect invalid descendants, `:is()` to group form controls, `:where()` to keep supporting text weak in the cascade, and logical properties for spacing.

The important architectural point is that each feature solves a different problem.

## Python Implementation

The Python program is an executable laboratory and stylesheet generator.

Its `DesignTokens` class represents custom properties as a dictionary and validates the required `--` naming convention. The `resolve_custom_property()` function models dependency resolution for common `var()` expressions and detects circular token dependencies.

The script creates a realistic token set containing:

- semantic and primitive colors
- spacing values
- component radius
- focus-ring information
- surface relationships

It then generates CSS using those values.

The Python program also contains a small DOM-like `Element` model. This is not intended to reproduce a browser selector engine. Its purpose is to demonstrate the relationship represented by `.field:has(.error)` by recursively examining descendants.

The `specificity()` function provides a targeted model for the selectors used in the demonstration. It specifically distinguishes the zero specificity of `:where()` from the specificity behavior of `:is()` and `:has()`.

The stylesheet analyzer counts custom-property definitions, `var()` calls, nested selectors, functional pseudo-classes, and logical properties. It also performs targeted architecture checks for physical directional properties and `!important`.

Running the script creates `modern-css-demo.css` and `modern-css-report.json`.

The generated stylesheet includes a dark-theme token override, nested application rules, interaction selectors, form validation state, and logical properties.

The Python model intentionally does not claim to be a complete CSS parser. A browser has substantially more responsibility around parsing, cascade origins, inheritance, layers, computed values, selector matching, layout, and rendering.

## JavaScript Implementation

The JavaScript file provides the browser-oriented implementation.

It uses `CSS.supports()` to test feature support instead of hard-coding assumptions about a particular browser. The expressions cover custom properties, nesting, `:is()`, `:where()`, `:has()`, and logical properties.

The `buildModernStylesheet()` function constructs a complete stylesheet using JavaScript-controlled token values. This provides a concrete demonstration of how application code can produce a stylesheet while the browser remains responsible for interpreting CSS.

The browser phase adds the stylesheet to the document through a dynamically created `<style>` element.

### Runtime theming

`applyTheme()` changes `data-theme` on the root element.

The CSS responds to that attribute by overriding selected custom properties. Component declarations remain unchanged.

This illustrates the distinction between changing a token and changing component structure.

### CSSOM and registered properties

`readComputedToken()` retrieves the resolved value of a custom property through `getComputedStyle()`.

`registerAccentProperty()` demonstrates the optional `CSS.registerProperty()` API. The implementation checks for API availability and catches registration errors.

This is deliberately different from the Python token resolver: JavaScript can interact with the actual browser CSS environment when executed in a browser.

### Event-driven form behavior

The form demonstration listens to `input` and `change` events.

The JavaScript reports whether the form currently contains an invalid control, while CSS independently styles the containing `.field` through `:has(input:invalid)`.

This separation demonstrates a useful architecture: JavaScript handles application behavior and event observation, while CSS handles presentation that can be derived directly from browser-recognized form state.

## C++ Case Study

The C++ program models a design-system governance and audit engine.

Its scenario is a component library containing an application shell, toolbar, cards, and form fields.

The `TokenGraph` class treats custom-property references as a dependency graph. A token such as `--color-surface-raised: var(--color-surface)` becomes an edge from one token to another.

The graph implementation checks:

- undefined token references
- circular dependencies
- successful resolution of simple token chains

The `CssAuditor` then examines structured `SelectorRule` records.

The selector audit identifies use of:

- `:is()`
- `:where()`
- `:has()`

The declaration audit distinguishes logical properties from physical directional properties.

The production case study uses declarations such as `padding-inline`, `padding-block`, `margin-inline`, `border-block-start`, and `min-inline-size`.

A deliberately broken system is also created. It contains an undefined custom-property reference, a token cycle, and physical directional declarations. The resulting audit demonstrates how architecture validation can catch issues before the stylesheet becomes part of a larger component system.

The C++ program does not attempt to implement browser rendering. A complete CSS implementation would require parsing the CSS grammar, selector matching, cascade evaluation, computed values, inheritance, layout, and rendering. The case study instead concentrates on the subset of architecture that can reasonably be represented as structured design-system data.

## CSS Cascade and Specificity

Modern selector functions make specificity easier to misuse if their matching behavior is considered without their cascade behavior.

A selector such as:

`.card:where(.compact)`

can provide a compact variant without adding specificity from `.compact` through `:where()`.

A selector such as:

`.card:is(.selected, :focus-within)`

does not have the same specificity behavior because `:is()` contributes according to its most specific argument.

`:has()` also participates in specificity according to its selector argument rather than behaving like an unconditional zero-specificity relationship.

This distinction is important when designing reusable components. Selector grouping should not automatically result in increasingly strong selectors.

## Theme Architecture

The project treats global tokens and semantic component values separately.

Primitive values such as a blue color can be represented as a token, while components consume semantic values such as `--color-brand` or `--color-danger`.

A theme can then override semantic tokens:

`[data-theme="dark"] { --surface: #0f172a; }`

The `.card` component does not need a second dark-mode implementation.

This approach also makes the relationship between component structure and theme data clearer. CSS nesting describes where a component rule applies, while custom properties determine the values used by that rule.

## Form State Architecture

The form example demonstrates an important use of relational selectors.

A field contains an input whose validity can change:

`.field:has(input:invalid)`

The field can respond visually without maintaining a duplicate state class.

The stylesheet can then style the label, input, and other descendants through nested rules.

The JavaScript layer still has a role when application behavior is required, such as displaying server-side validation, sending data, or coordinating asynchronous state. CSS `:has()` is most useful when the relationship can be derived directly from the DOM and CSS-recognized state.

## Practical Selector Design

Modern selectors should be designed around relationships that communicate component intent.

Good examples from the project include:

`.form-field:has(input:invalid)`

This describes a form field whose descendant input is invalid.

`.toolbar:has(button[aria-expanded="true"])`

This describes a toolbar containing an expanded control.

`.field > :is(input, select, textarea)`

This groups form controls sharing the same presentation.

`.field > :where(.help, .status)`

This groups supporting content while keeping its selector specificity deliberately low.

The value of these selectors comes from the relationship they express, not merely from their syntactic compactness.

## Edge Cases

### Undefined custom properties

A declaration using `var(--unknown-token)` without a valid fallback can become unusable when the custom property cannot provide a value.

The Python and C++ implementations explicitly check token dependencies.

### Circular token dependencies

A chain such as `--a -> --b -> --a` should be treated as an invalid token dependency architecture.

Both the Python and C++ implementations detect this condition.

### Specificity surprises

Replacing repeated selectors with `:is()` can alter the specificity profile of a component. A selector that looks shorter is not necessarily weaker.

`:where()` exists specifically for situations where grouped selectors should not add specificity.

### Broad relational selectors

A selector such as `.component:has(*)` creates a very broad relationship.

The audit engine flags this pattern because a more specific relationship normally communicates component intent more clearly.

### Physical directional properties

`margin-left`, `padding-right`, and `border-left` encode physical directions.

They may be appropriate when a design explicitly requires a physical coordinate, but they should not be used automatically when the actual requirement is an inline or block relationship.

### Unsupported features

The JavaScript implementation checks `CSS.supports()` where browser APIs are available.

This is preferable to assuming that every execution environment has identical CSS support.

A production compatibility strategy may require a combination of feature detection, CSS fallbacks, build tooling, and a defined browser-support policy.

## Common Architectural Mistakes

### Treating custom properties like preprocessor variables

Custom properties remain part of the runtime CSS system. They can inherit, be overridden, and be read through browser APIs.

### Using `:is()` without considering specificity

Grouping selectors can reduce duplication while still producing a stronger selector than expected.

### Using `:where()` when specificity is intentionally required

`:where()` always contributes zero specificity. It should be selected when weak defaults are desirable, not merely because it looks similar to `:is()`.

### Using JavaScript for CSS-only relational state

A component that only needs to style a parent based on a descendant state may not need a JavaScript-maintained state class when `:has()` can express the relationship directly.

### Replacing every directional property mechanically

Logical properties should represent layout intent. They are not a requirement to eliminate every physical property regardless of context.

### Treating nesting as a complete architecture

Nesting can make component relationships clearer, but excessive nesting can still produce complicated selectors. Component boundaries and selector depth remain architectural concerns.

## Performance Considerations

CSS selector matching and style recalculation are browser implementation concerns, so source-level intuition should not be treated as a precise performance measurement.

The practical approach is to keep selectors meaningful, avoid unnecessarily broad relationships, and measure representative DOM structures when a component contains many dynamic states.

`:has()` deserves particular attention in highly dynamic interfaces because its purpose is to establish relationships between elements. The relevant cost depends on selector structure, DOM shape, mutation frequency, and browser implementation.

Custom properties can also participate in large inheritance trees. A design system should therefore keep token scopes intentional rather than defining every possible token at every component level.

Nesting affects stylesheet structure and selector relationships. Deeply nested component styles can still become difficult to reason about even when the syntax is valid.

## Security and Reliability Considerations

Custom properties are CSS values, not a general-purpose security boundary.

When CSS is generated from external data, values should be validated according to the allowed CSS syntax rather than concatenating arbitrary strings into a stylesheet.

The JavaScript implementation treats theme names as a constrained set of `light` and `dark` rather than inserting arbitrary user-controlled CSS.

`CSS.registerProperty()` also demonstrates why property syntax can matter when custom properties are used in more advanced animation or typed-value scenarios.

For applications accepting untrusted content, CSS generation should be separated from arbitrary user content, and HTML/CSS injection risks should be considered at the application boundary.

## Debugging Strategy

For custom-property failures, inspect the computed value of the property and trace the `var()` dependency chain.

For specificity problems, compare the complete selector specificity rather than only counting visible classes.

For `:has()` problems, inspect the actual DOM relationship. The selector succeeds only when the relative selector can match the expected descendant or related element.

For logical-property issues, inspect the document's writing mode and direction rather than assuming left-to-right horizontal layout.

For nesting problems, inspect the final browser-parsed stylesheet and verify that the intended parent-child relationship is represented.

The JavaScript implementation's `CSS.supports()` checks can also distinguish a browser feature problem from an incorrect selector or declaration.

## Production Considerations

A production design system should define a token naming strategy, semantic token boundaries, component ownership, and acceptable selector complexity.

Custom properties should be organized so that component rules consume stable semantic values rather than depending on arbitrary implementation details.

Nesting should preserve readable component boundaries rather than becoming an excuse for deeply coupled selector trees.

`:is()` should be used when selector grouping is useful and its specificity behavior is intentional.

`:where()` is especially suitable for foundational styles that should remain easy to override.

`:has()` should describe meaningful component relationships and should be tested against realistic DOM structures.

Logical properties should be preferred when the design requirement is based on block and inline relationships rather than fixed physical coordinates.

Browser feature detection and the project's defined support policy should determine whether modern syntax can be used directly or requires an alternate delivery strategy.

## Implementation Relationship

The three files intentionally do not implement the same program in three languages.

| File | Technical perspective |
|---|---|
| Python | Executable CSS models, token dependency resolution, selector analysis, stylesheet generation, and architecture checks |
| JavaScript | Browser-facing CSS feature detection, CSSOM interaction, runtime theming, DOM relationships, and event-driven form state |
| C++ | Design-system governance case study with token graphs, selector classification, logical-property auditing, and failure detection |

The Python implementation emphasizes learning through executable models.

The JavaScript implementation emphasizes the boundary between CSS and browser runtime behavior.

The C++ implementation emphasizes how a larger engineering organization could represent and audit CSS architecture as structured data.

Together, the implementations distinguish value management, selector structure, relational matching, specificity, and writing-mode-aware layout instead of treating modern CSS as one undifferentiated feature set.
