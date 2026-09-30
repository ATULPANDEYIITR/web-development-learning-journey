# CSS Architecture: BEM, Utility Classes, Component Styles, CSS Variables, and Maintainability

## Scope

CSS architecture is the organization of selectors, declarations, reusable values, and styling responsibilities so that a stylesheet remains understandable as an application grows.

This repository models four closely related architectural mechanisms without treating them as interchangeable:

- **BEM** establishes a naming convention and ownership boundary for components.
- **Utility classes** encode small, reusable behavioral or layout decisions.
- **Component styles** own the visual structure and states of a particular UI component.
- **CSS variables** centralize values such as colors, spacing, radii, typography values, and shadows.

The architectural goal is not to minimize the number of CSS lines. The goal is to make ownership, reuse, dependencies, and change impact predictable.

The three implementations approach the subject differently. Python builds an executable architecture laboratory and linter. JavaScript models the architecture with objects, collections, and event-driven theme switching. C++ presents a repository-governance case study in which CSS architecture is validated as a technical quality gate.

---

## Architectural Problem

A small stylesheet can be written without an explicit architecture because the number of selectors and values is limited. As a product grows, the same CSS file can contain global rules, page-specific overrides, component styles, layout helpers, repeated color values, state selectors, and emergency fixes.

This creates several forms of coupling:

- A component may depend on a particular DOM hierarchy.
- A change to one literal color may require edits in many files.
- A utility class may accidentally become responsible for component-specific presentation.
- A generic class such as `.card` may be used by several unrelated components.
- A high-specificity selector may override a component unexpectedly.
- A developer may add an even more specific selector to defeat the previous rule.
- A theme change may require modifying component selectors instead of replacing semantic values.

Architecture addresses these problems by giving different kinds of styling different responsibilities.

A useful conceptual relationship is:

`CSS variables provide values -> component styles consume semantic values -> BEM identifies component ownership -> utilities compose independent concerns`

These mechanisms can coexist. They solve different problems.

---

## BEM

BEM means **Block, Element, Modifier**.

A block represents an independent component or conceptual UI unit:

`review-card`

An element represents a meaningful part of that block:

`review-card__title`

A modifier represents a variation or state of the block:

`review-card--approved`

The distinction is important because BEM is primarily a naming and ownership strategy. It does not itself provide spacing tokens, theming, or layout utilities.

### Blocks

A block should represent a meaningful component boundary.

Examples used by the implementations include:

- `review-card`
- `status-badge`
- `repository-header`

The block name should communicate ownership without depending on where the component happens to be rendered.

A class such as `.card` is much less explicit because another feature can independently decide that it also needs a card.

### Elements

Elements identify internal roles:

`review-card__header`

`review-card__title`

`review-card__meta`

`review-card__actions`

An element belongs conceptually to its block. It is not a global class intended to be reused independently.

The Python and C++ implementations validate element names and construct them from an explicit block.

### Modifiers

Modifiers express variations of a component:

`review-card--approved`

`review-card--changes-requested`

The modifier does not replace the base component. It augments the component's state or presentation.

A useful markup relationship is:

`review-card review-card--approved`

The first class supplies the base component contract. The second expresses its variation.

### BEM and DOM independence

A major benefit of BEM-style component selectors is that the CSS does not need to encode every ancestor in the DOM.

Prefer:

`.review-card__title`

over a selector such as:

`.repository-page .review-panel article header h2`

The second selector makes surrounding markup part of the styling contract. Moving the article to another container can unexpectedly change its appearance.

---

## Utility Classes

A utility class represents a narrowly scoped, reusable styling behavior.

Examples in the implementations include:

- `u-flex`
- `u-gap-md`
- `u-p-md`
- `u-text-center`
- `u-w-full`

A utility is intentionally different from a component.

`review-card` answers:

> Which component owns this markup?

`u-p-md` answers:

> Should this element receive the standard medium padding utility?

The utility does not need to know that the element is a review card.

### Utility boundaries

A useful utility has a narrow responsibility.

For example:

`u-gap-md`

can represent a standard gap value.

A component-specific class such as:

`review-card-approved-with-padding`

is not a useful general utility. It combines component identity, state, and spacing into one selector.

That type of abstraction becomes difficult to reuse because its meaning depends on one component.

### Specificity

Utilities normally benefit from single-class specificity:

`.u-gap-md`

has specificity equivalent to:

`(0, 1, 0)`

A selector such as:

`.review-card .u-gap-md`

has greater specificity and changes the utility's behavior from an independently composable rule into a rule coupled to a component hierarchy.

The implementations therefore treat utility specificity as an architectural constraint.

### Utility growth

Utilities can become difficult to govern when every declaration is converted into a class.

A utility layer should have a coherent vocabulary. Common layout, spacing, visibility, alignment, and sizing behaviors are reasonable candidates when the design system actually uses them.

Creating hundreds of arbitrary one-off utilities can simply move the maintainability problem from component CSS into a different namespace.

---

## Component Styles

Component styles own the presentation of a specific UI component.

For `review-card`, component styles may define:

- surface appearance
- border
- radius
- internal layout
- title typography
- component-specific state
- status presentation

The component selector should normally be locally understandable.

For example:

`.review-card`

`.review-card__header`

`.review-card__title`

`.review-card--approved`

These selectors express component responsibility directly.

### Component styles versus utilities

Component styles should contain decisions intrinsic to the component.

For example, a review card may always require a particular border radius because that radius is part of the component design.

A generic spacing relationship may instead be composed through:

`u-gap-md`

The distinction prevents component styles from becoming a collection of every possible layout choice.

### Component styles versus BEM

BEM and component styles are related but not identical.

BEM answers a naming question:

> How do selectors identify the block, its elements, and its modifiers?

Component styling answers an ownership question:

> Which stylesheet layer is responsible for this component's presentation?

A project can use BEM naming without having a disciplined component layer. Conversely, a component architecture can use another naming convention.

The implementations use BEM because the requested architecture specifically demonstrates explicit component naming.

---

## CSS Variables

CSS custom properties provide runtime-resolvable values.

A token such as:

`--color-surface`

can be consumed as:

`var(--color-surface)`

This separates a semantic value from the selectors that consume it.

### Semantic tokens

A semantic token communicates intent:

`--color-text-muted`

is more meaningful to a design system than repeatedly scattering a literal color value throughout components.

The implementations define token groups such as:

- `color`
- `space`
- `radius`
- `font`

Examples include:

`--color-surface`

`--color-border`

`--space-md`

`--radius-md`

`--font-weight-bold`

### Runtime theming

CSS custom properties participate in the cascade. A theme can therefore override a variable at a higher or more local scope.

The JavaScript implementation models theme switching through `ThemeManager`.

A dark theme can define:

`--color-surface: #10141c`

while a light theme can replace it with:

`--color-surface: #f7f8fa`

The component selector does not need to change.

This is a major architectural distinction:

**The component expresses which semantic value it needs. The theme determines the actual value.**

### Fallback values

CSS supports fallbacks such as:

`var(--color-success, #86efac)`

If the custom property is unavailable, the fallback can provide a safe value.

Fallbacks should still be used deliberately. Excessive fallback chains can make the source difficult to understand.

---

## CSS Layer Organization

The examples use an architectural order:

`reset -> tokens -> base -> components -> utilities -> overrides`

The exact organization can differ between projects, but the important principle is that the ordering should be intentional.

### Reset

Reset rules establish baseline browser behavior.

The example includes the common box-sizing normalization:

`* { box-sizing: border-box; }`

The reset should remain small and should not become a hidden component layer.

### Tokens

Token definitions establish reusable values.

Components consume those values rather than duplicating every literal.

### Base

Base rules establish document-level behavior such as body typography and page background.

They should not unexpectedly style every instance of a component.

### Components

Component selectors own component presentation.

The example places `review-card` and `status-badge` rules here.

### Utilities

Utilities provide explicit composition points.

They are intentionally low-specificity and independent of component markup.

### Overrides

An override layer can exist when a project has a deliberate reason for exceptions. It should not become the normal place where unresolved architectural problems accumulate.

---

## Python Implementation

The Python program is an executable architecture laboratory rather than a generic Python tutorial.

### BEM model

The `bem_block`, `bem_element`, and `bem_modifier` functions construct valid names and reject invalid identifiers.

`bem_parts` parses a BEM class into its block, element, and modifier components.

This makes the naming convention executable rather than merely documenting it.

### Utility model

The `UTILITY_NAMES` set defines an explicit utility vocabulary.

`utility_class` rejects unknown utilities. This demonstrates one governance approach: utilities can be treated as an intentionally controlled architectural surface rather than arbitrary class names.

### Component model

The `Component` class stores:

- block identity
- elements
- modifiers
- composed utilities

The resulting class contract demonstrates how component ownership and utility composition can coexist.

### Design-token model

`DesignTokens` stores colors, spacing, typography, radii, and shadows.

The `to_css` method converts these values into CSS custom properties.

The `Theme` class demonstrates scoped overrides for light and dark themes.

### Specificity analysis

`calculate_specificity` produces an approximate `(IDs, classes, elements)` tuple for the selectors used in the case study.

The implementation intentionally states its scope because a complete CSS selector parser is considerably more complex.

### Architecture linting

`ArchitectureLinter` checks architectural boundaries.

It detects issues such as:

- utility rules containing unexpected selectors
- utility rules with excessive specificity
- component selectors containing utilities
- deep descendant selectors
- ID-based component selectors
- generic class names

The deliberately invalid examples show how an architecture tool can turn style conventions into executable checks.

### Maintainability metrics

The Python program reports:

- rule count
- declaration count
- average declarations per rule
- high-specificity rule count
- deep-selector count

These values are diagnostics rather than universal quality scores. They help identify structural pressure but cannot determine whether a component's design is appropriate.

---

## JavaScript Implementation

The JavaScript program approaches the same architecture through runtime-oriented objects and event handling.

### Object-oriented component representation

The `Component` class maintains a block and sets of elements and modifiers.

JavaScript `Set` is useful here because an element or modifier should not accidentally appear multiple times in the component contract.

### Token registry

`DesignTokenRegistry` uses nested `Map` objects.

A token is defined by group, name, and value:

`color -> surface -> #10141c`

The registry then resolves it to:

`var(--color-surface)`

This separates token storage from component declarations.

### Theme switching

`ThemeManager` stores named themes and resolves base variables with theme overrides.

`ThemePreviewController` adds an event-driven layer.

When a theme changes, it emits a `themeChanged` event containing:

- theme name
- selector
- resolved variables

This reflects a browser-oriented architectural concern: CSS variables can change at runtime without reconstructing component styles.

### CSS architecture object

`CssArchitecture` stores rules with an explicit layer.

It validates that layers appear in the intended sequence before rendering the stylesheet.

The validation is important because an architecture expressed only through filenames or comments is easier to violate accidentally. A programmatic representation can make the ordering testable.

### Linter

`ArchitectureLinter` performs similar boundary checks to the Python implementation but uses JavaScript collections, regular expressions, and object-based violation records.

The JavaScript version deliberately does not simply translate every Python data structure. It emphasizes runtime state, theme events, `Map`, `Set`, and object-oriented organization.

---

## C++ Repository Governance Case Study

The C++ program models a CSS design-system repository used by a developer portal.

The architectural question is:

> Should a stylesheet change be accepted when its selectors violate the repository's CSS architecture?

The program treats architecture validation as a governance mechanism.

### Scenario

The repository contains:

`review-card`

and:

`status-badge`

The review card contains elements such as:

`review-card__header`

`review-card__title`

`review-card__meta`

`review-card__actions`

Its state is represented by:

`review-card--approved`

A status badge can use:

`status-badge--success`

Independent layout concerns can be composed using utilities such as:

`u-p-md`

and:

`u-gap-md`

### Data structures

`CssRule` represents a stylesheet rule containing:

- selector
- declaration map
- CSS layer
- source description

`Component` represents a component contract.

`TokenRegistry` manages semantic design values.

`CssArchitecture` owns the ordered rule collection.

`ArchitectureLinter` evaluates rules against architectural policies.

`Violation` provides structured failure information.

These structures model a real repository-quality workflow rather than isolated language syntax.

### Algorithmic behavior

Selector classes are extracted with a regular expression.

Specificity is calculated into an ordered tuple:

`(IDs, classes, elements)`

The tuple allows lexicographic comparison because CSS specificity is hierarchical.

Layer validation walks the rules once and ensures that a later rule never moves backward into an earlier architectural layer.

The basic layer validation therefore operates in O(n) time for `n` stylesheet rules.

The linter processes each rule and its extracted selector information. Its cost is approximately proportional to the total size of the selector text and rule collection for the limited selector grammar used by the case study.

### Why specificity is checked

Consider:

`.review-card`

versus:

`#dashboard .review-card`

The second selector has an ID component and therefore introduces significantly more cascade pressure.

If developers repeatedly solve conflicts with higher specificity, future changes become increasingly difficult because each new rule must defeat previous rules in the cascade.

The case study therefore treats ID selectors inside component architecture as a governance violation.

### Why descendant depth is checked

A selector such as:

`.repository-page .sidebar .card .title`

contains assumptions about several ancestors.

If the title moves to another component or the sidebar hierarchy changes, the style may stop applying.

A selector such as:

`.review-card__title`

contains less structural information and therefore creates a smaller coupling surface.

### Failure handling

The C++ program rejects invalid BEM names, invalid design-token references, invalid architecture ordering, and failed test assertions.

The main function converts exceptions into a non-zero process result.

This models an important production property: architectural validation can fail a build or quality gate rather than merely printing a warning that developers may ignore.

---

## BEM, Utilities, Components, and Variables: Responsibility Boundaries

| Mechanism | Primary responsibility | Example | Should know about a specific component? |
|---|---|---|---|
| BEM block | Component identity | `.review-card` | Yes |
| BEM element | Internal component role | `.review-card__title` | Yes |
| BEM modifier | Component variation/state | `.review-card--approved` | Yes |
| Utility | Reusable isolated behavior | `.u-gap-md` | No |
| Component style | Component-owned presentation | `.review-card` | Yes |
| CSS variable | Reusable semantic value | `--color-surface` | Usually no |
| Theme override | Value substitution | `--color-surface: #fff` | No |

The distinctions prevent one abstraction from absorbing the responsibilities of another.

A utility should not become a component.

A component selector should not become a global layout utility.

A token should not encode an entire component.

A BEM modifier should not be used as a replacement for every reusable layout behavior.

---

## Maintainability

Maintainability depends heavily on how easily a developer can answer four questions:

- Who owns this style?
- What does this value mean?
- What else will change if I modify this rule?
- Which rule will win when multiple selectors apply?

The architecture in these implementations addresses those questions differently.

### Ownership

BEM gives selectors recognizable component ownership.

`review-card__title` immediately identifies its parent component.

### Value centralization

CSS variables reduce duplication for values that need coordinated change.

Changing `--space-md` can affect every consumer that intentionally references that token.

### Composition

Utilities allow orthogonal concerns to be composed without creating a new component-specific selector for every combination.

### Cascade predictability

Low-specificity selectors reduce the amount of work required to understand the cascade.

An architecture that consistently uses component classes and small utilities is generally easier to inspect than one containing deeply nested selectors and ID overrides.

---

## Common Architectural Mistakes

### Generic global component names

Using `.card`, `.title`, `.header`, or `.active` as broad application classes makes ownership unclear.

The problem is not that these names are syntactically invalid. The problem is that unrelated features can independently want the same concept.

A component-oriented architecture benefits from explicit ownership.

### Deep descendant selectors

A selector such as:

`.repository-page .review-panel article .title`

couples styling to the current DOM structure.

Markup refactoring can therefore become a CSS-breaking change even when the component itself has not changed.

### Mixing utility and component responsibilities

A selector such as:

`.review-card .u-p-md`

means the utility is no longer an independent composition mechanism.

The better architectural separation is to put both classes on the element when both responsibilities are needed.

### Repeating literal values

Repeated declarations such as the same color or spacing value across many components make design-system changes expensive.

Semantic variables provide a central replacement point.

### Specificity escalation

Adding `!important`, IDs, or deeper selectors can solve an immediate cascade conflict while creating a larger architectural problem.

The root cause should be investigated before adding another layer of cascade pressure.

### Uncontrolled custom properties

CSS variables are not automatically design tokens merely because they begin with `--`.

A project benefits from naming conventions that communicate whether a variable represents a semantic color, spacing value, component-private value, or temporary implementation detail.

---

## Edge Cases

### Component states

A component may have several states that need different presentation.

BEM modifiers can make these states explicit:

`review-card--approved`

`review-card--changes-requested`

The base component remains responsible for shared presentation.

### Responsive behavior

Responsive rules belong to the component or utility layer according to responsibility.

A component-specific responsive change should remain with the component. A general layout utility can remain independent.

The architecture should avoid creating selectors whose only purpose is to compensate for unrelated markup structure at one viewport width.

### Theme values

A theme may override a variable without redefining the component.

This is one reason semantic CSS variables are useful for design systems: the same component can consume different resolved values.

### Missing variables

A CSS variable reference can include a fallback:

`var(--color-success, #86efac)`

Fallbacks provide resilience but should not hide systematic token-definition errors.

### Browser support and generated CSS

The C++ and Python programs generate CSS text for architectural demonstration. They are not browser engines and therefore do not attempt to validate the complete CSS language.

The specificity calculations similarly cover the selector forms used in the case study rather than implementing every selector feature defined by CSS specifications.

---

## Security and Production Considerations

CSS architecture is not a security boundary.

A well-structured stylesheet does not replace HTML sanitization, authorization, content-security controls, or server-side validation.

There are still production considerations around CSS values and generated styles.

User-controlled strings should not be inserted directly into CSS selectors or custom-property values without appropriate validation and escaping.

Theme data loaded from an external source should be treated as data rather than trusted stylesheet source.

Build-time CSS generation should use deterministic inputs so that unexpected stylesheet changes can be identified during code review.

Architectural linting should be integrated into the same quality process used for other static checks. A rule that exists only in documentation is easier to violate than a rule represented by executable validation.

---

## Debugging Strategy

When a component appears incorrectly styled, inspect the problem in architectural order.

First determine which selector owns the expected property.

Then inspect whether a utility is also setting the property.

Next compare selector specificity.

Then inspect source order and layer order.

Finally inspect the resolved CSS variable value if the declaration uses a custom property.

This sequence helps distinguish different failure classes:

- **Wrong owner**: the component selector is not responsible for the expected style.
- **Wrong composition**: a utility is being used where component styling is required.
- **Cascade conflict**: another selector has higher specificity or later precedence.
- **Token problem**: the selector is correct but the resolved custom property is incorrect or missing.
- **Markup dependency**: the selector assumes a DOM structure that no longer exists.

---

## Practical Design-System Workflow

A maintainable CSS architecture can be organized around the following relationship rather than around a single universal naming rule:

`semantic tokens -> component styles -> utility composition -> page composition`

A review of a new component should ask whether each declaration belongs to the component itself or represents an independent reusable behavior.

A spacing decision intrinsic to a component can remain inside its component styles.

A reusable layout relationship can be represented by a utility.

A color that participates in the design system can use a semantic custom property.

A component variation can use a modifier when the variation belongs to the component's state or design.

This keeps abstractions aligned with responsibility.

---

## Implementation Comparison

| Concern | Python | JavaScript | C++ |
|---|---|---|---|
| BEM validation | Functions and regular expressions | Functions and parser objects | Validated naming functions |
| Component model | Dataclass | Class with `Set` collections | Class with `std::set` |
| Utilities | Controlled set | `Map` of utility declarations | `std::set` vocabulary |
| CSS variables | Dataclass token model | `Map`-based token registry | `TokenRegistry` |
| Themes | Static theme rendering | Runtime event-driven switching | Token-focused governance |
| Specificity | Tuple calculation | Array calculation | Structured `Specificity` |
| Architecture checks | Linter | Linter | Repository governance linter |
| Failure handling | Exceptions and assertions | Exceptions and assertions | Exceptions and process exit status |
| Primary perspective | Educational architecture laboratory | Runtime/browser-oriented model | Build/governance case study |

The implementations intentionally use different technical perspectives so that CSS architecture is not reduced to translating one program between three languages.

---

## Production Architecture Principles Demonstrated

The codebase supports several concrete principles.

### Explicit ownership

Component selectors should make it clear which component owns the presentation.

### Narrow abstractions

A utility should remain a utility. A token should remain a value. A component should own component behavior and presentation.

### Low cascade pressure

Selectors should avoid unnecessary IDs and deep structural dependencies.

### Semantic values

CSS variables should represent meaningful design decisions rather than arbitrary unnamed literals.

### Controlled composition

Utilities should be composed explicitly rather than hidden inside component selectors.

### Executable governance

Important architecture rules can be validated automatically rather than existing only as team conventions.

### Measurable structural pressure

Metrics such as selector depth, rule count, declaration count, and specificity can reveal areas that deserve investigation without pretending that one numerical threshold defines maintainability.

---

## Repository File Roles

The four artifacts form a coherent technical set:

`css_architecture.py` provides an executable Python architecture laboratory with validation, token modeling, theme examples, linting, metrics, and tests.

`css-architecture.js` provides a JavaScript implementation using classes, `Map`, `Set`, runtime theme management, event-driven updates, CSS rendering, and architecture linting.

`css_architecture.cpp` presents a repository governance engine that treats CSS architecture as a build-quality concern and validates component naming, utilities, specificity, layers, tokens, and failure conditions.

`README.md` documents the architectural distinctions and the mechanisms implemented by those programs without reproducing their complete source code.

---

## Key Architectural Distinctions

BEM is not a replacement for CSS variables.

Utility classes are not a replacement for component styles.

Component styles are not a replacement for utilities.

CSS variables are not a naming convention.

The strongest architecture comes from keeping these responsibilities distinct while allowing them to cooperate.

A `review-card` can therefore use:

`review-card`

`review-card__title`

`review-card--approved`

`u-p-md`

and:

`var(--color-surface-raised)`

without those mechanisms competing for the same responsibility.

The component name identifies ownership, the modifier identifies state, the utility provides an independent reusable behavior, and the custom property supplies a centrally governed value.
