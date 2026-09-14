# CSS selectors

## Topic introduction

CSS selectors are patterns used to identify HTML elements that should receive a set of CSS declarations. A selector determines the scope of a CSS rule.

A basic rule has two conceptual parts:

- A selector, which identifies elements.
- A declaration block, which contains properties and values applied to matching elements.

For example, an element selector such as `p` targets paragraph elements. A class selector such as `.card` targets elements carrying the `card` class. A selector can become much more precise by combining element names, classes, IDs, attributes, relationships, and pseudo-classes.

The accompanying Python script models a small HTML-like document and implements selector concepts so that matching behavior can be studied programmatically. Python is used as a teaching environment rather than as a replacement for a browser's CSS engine.

## What a selector does

Consider an HTML structure containing several paragraphs:

`p`

This selector identifies all paragraph elements.

A CSS rule conceptually follows this pattern:

`selector { property: value; }`

The selector is evaluated against the document structure. Every matching element becomes a candidate for the declarations associated with that rule.

Selector matching is therefore different from CSS property inheritance. A selector explicitly identifies elements, while inheritance determines whether certain property values are passed from ancestors to descendants.

## Universal selector

The universal selector is:

`*`

It matches every element.

A common use is global box sizing:

`* { box-sizing: border-box; }`

The universal selector can also be combined with other selectors. For example, `.card *` targets descendants of an element with the `card` class.

The universal selector is not inherently incorrect or inefficient. Its usefulness depends on context and the amount of styling it causes to be considered across the document.

## Element selectors

An element selector uses the name of an HTML element.

Examples include:

`p`

`h1`

`article`

`button`

`nav`

An element selector is appropriate when a style is fundamentally associated with that type of element.

For example, a stylesheet might establish a general paragraph line height with a `p` selector.

Element selectors are broad by design. A rule such as `p` affects every matching paragraph unless another part of the cascade changes the result.

## Class selectors

A class selector begins with a period.

Examples:

`.card`

`.button`

`.active`

`.featured`

An HTML element can contain one or multiple classes. A paragraph with `class="text highlight"` matches both `.text` and `.highlight`.

Classes are reusable. Many elements can share the same class, which makes classes the primary mechanism for reusable component and utility styling in many CSS architectures.

A compound class selector such as `.text.highlight` requires the same element to contain both classes.

This is different from `.text .highlight`, where `.highlight` must be a descendant of an element matching `.text`.

## ID selectors

An ID selector begins with `#`.

Example:

`#main-content`

It targets an element whose ID is `main-content`.

IDs are intended to identify unique elements within a document. They are also used by HTML relationships, fragment navigation, JavaScript DOM APIs, and accessibility mechanisms.

IDs have high specificity, so using them extensively for styling can make a stylesheet difficult to override. Reusable component styling is generally easier to manage with classes.

The distinction is:

`.main-content`

selects by class.

`#main-content`

selects by ID.

The two selectors are not interchangeable.

## Compound selectors

Simple selectors can be combined without whitespace.

Examples:

`p.text`

`article.featured`

`a.nav-link`

`h1#article-title.title`

A compound selector requires the conditions to apply to the same element.

For example:

`p.text.highlight`

means a paragraph that has both the `text` and `highlight` classes.

The absence of whitespace is significant.

`.card.title`

means one element having both classes.

`.card .title`

means a `.title` descendant inside a `.card`.

## Descendant selectors

A descendant selector uses whitespace between selector components.

Example:

`article p`

This matches paragraph elements at any descendant depth within an `article`.

For a structure such as:

`article > section > p`

the paragraph is a descendant of the article even though the section is between them.

Descendant selectors are useful when styling related content at different levels of a component hierarchy.

They can also become overly broad. A selector such as `.card p` may unintentionally affect paragraphs inside nested components. A more specific component class can sometimes communicate intent more clearly.

## Child selectors

The child combinator is `>`.

Example:

`article > p`

This matches only paragraphs that are direct children of an article.

Given:

`article > section > p`

the paragraph is not matched by `article > p` because its direct parent is `section`, not `article`.

The key distinction is:

`article p`

means any paragraph descendant.

`article > p`

means a paragraph whose direct parent is the article.

## Adjacent sibling selectors

The adjacent sibling combinator is `+`.

Example:

`h1 + p`

This matches a paragraph immediately following an `h1`, provided both elements share the same parent.

The selector does not search arbitrary descendants. It operates on siblings.

This is useful for patterns such as styling the first paragraph immediately following a heading.

## General sibling selectors

The general sibling combinator is `~`.

Example:

`h1 ~ p`

This matches paragraphs appearing later than an `h1` under the same parent.

Unlike `+`, the paragraph does not have to be the immediately following sibling.

The distinction is:

`h1 + p`

selects the immediately following paragraph.

`h1 ~ p`

selects later paragraph siblings.

## Attribute selectors

Attribute selectors identify elements based on HTML attributes.

The basic forms include:

`[disabled]`

`[type="email"]`

`[href^="https"]`

`[href$=".pdf"]`

`[data-id*="user"]`

`[data-role~="admin"]`

`[lang|="en"]`

Attribute selectors are useful when the attribute itself represents meaningful state, configuration, metadata, or semantics.

### Attribute presence

`[disabled]`

matches elements that have a `disabled` attribute.

This is different from testing for a particular value.

### Attribute equality

`[type="email"]`

matches elements whose `type` attribute has the specified value.

### Attribute prefix matching

`[href^="https"]`

matches values beginning with `https`.

The `^=` operator means the attribute value starts with the specified string.

### Attribute suffix matching

`[href$=".pdf"]`

matches values ending with `.pdf`.

The `$=` operator means the attribute value ends with the specified string.

### Attribute substring matching

`[data-id*="user"]`

matches values containing `user`.

The `*=` operator means the specified string occurs somewhere within the attribute value.

### Attribute word matching

`[data-role~="admin"]`

treats the attribute value as a whitespace-separated collection of words and looks for the specified word.

This is different from substring matching. A word match respects whitespace-separated tokens.

### Attribute language matching

`[lang|="en"]`

has special semantics for language-like values. It can match `en` as well as values such as `en-US`.

The `|=` operator is therefore different from ordinary substring matching.

## Attribute case considerations

Attribute matching has nuanced case rules.

HTML attribute names are generally case-insensitive, while attribute values can have different rules depending on the attribute and document context.

CSS also supports explicit ASCII case modifiers for attribute selectors:

`[data-value="abc" i]`

requests ASCII case-insensitive matching.

`[data-value="abc" s]`

requests ASCII case-sensitive matching.

It is unsafe to assume that every attribute value in every context follows one universal case-sensitivity rule.

## Pseudo-classes

A pseudo-class begins with a single colon.

Examples include:

`:hover`

`:focus`

`:focus-visible`

`:active`

`:visited`

`:first-child`

`:last-child`

`:nth-child(2)`

`:not(...)`

`:is(...)`

`:where(...)`

`:has(...)`

Pseudo-classes describe states, structural conditions, relationships, or logical conditions.

They differ from ordinary classes because their matching behavior can depend on browser state or document structure.

For example, `.active` is an ordinary class stored on an element. `:hover` is a browser-determined interaction state.

## Structural pseudo-classes

Structural pseudo-classes depend on an element's position among its siblings.

Important examples include:

`:first-child`

`:last-child`

`:only-child`

`:nth-child()`

`:first-of-type`

`:last-of-type`

`:nth-of-type()`

### :first-child

`:first-child`

matches an element that is the first child of its parent.

### :last-child

`:last-child`

matches an element that is the last child of its parent.

### :only-child

`:only-child`

matches an element when it is the only child of its parent.

### :nth-child()

`:nth-child()` uses one-based positions.

Examples:

`:nth-child(1)`

`:nth-child(2)`

`:nth-child(odd)`

`:nth-child(even)`

`:nth-child(2n)`

`:nth-child(2n + 1)`

CSS uses the An+B mathematical form for generalized positional matching.

For example, `2n` produces even positions, while `2n + 1` produces odd positions.

### :nth-of-type()

`:nth-of-type()` counts only siblings of the same element type.

This creates an important distinction.

`:nth-child(2)`

means the element is the second child of its parent.

`:nth-of-type(2)`

means the element is the second sibling of its element type.

Suppose a parent contains:

`h2`

`p`

`div`

`p`

The second paragraph is the fourth child overall, but it is the second `p` of its type.

Consequently:

`p:nth-child(4)`

and

`p:nth-of-type(2)`

can refer to the same paragraph in this structure, while the conceptual counting mechanisms are different.

## State pseudo-classes

State pseudo-classes describe conditions that can change while a page is being used.

Important examples include:

`:hover`

`:focus`

`:focus-visible`

`:active`

`:visited`

`:checked`

`:disabled`

`:enabled`

`:required`

`:optional`

`:valid`

`:invalid`

`:read-only`

`:read-write`

`:placeholder-shown`

These are particularly useful for interactive interfaces and forms.

For example:

`input:invalid`

can style a form control whose current value does not satisfy its validation constraints.

## :hover

`:hover` matches when the pointing device is positioned over an element according to browser interaction rules.

It is commonly used for visual feedback.

Hover should not be treated as the only interaction state because keyboard and touch users may not interact through hover.

## :focus

`:focus` identifies an element that currently has focus.

Focus is important for keyboard navigation and accessibility.

A stylesheet should not remove focus indicators without providing an equally effective replacement.

## :focus-visible

`:focus-visible` is useful when a visible focus indicator should be presented according to browser focus heuristics.

A common accessible pattern is to provide a strong outline for keyboard-visible focus.

Removing all focus outlines without a replacement can make keyboard navigation difficult or impossible to follow visually.

## Form pseudo-classes

Form controls expose several useful pseudo-classes.

Examples include:

`:required`

`:optional`

`:valid`

`:invalid`

`:in-range`

`:out-of-range`

`:checked`

`:indeterminate`

`:disabled`

`:enabled`

These allow CSS to respond to native form states.

A selector such as:

`input:invalid`

can provide immediate visual feedback when a value is invalid.

CSS styling should complement proper HTML validation and accessible form labeling. Styling alone is not a substitute for semantic form structure.

## Link pseudo-classes

Common link states include:

`:link`

`:visited`

`:hover`

`:focus`

`:active`

The sequence and interaction of these states matter when designing links.

Keyboard users should receive a visible focus state, and visited-link styling is subject to browser privacy restrictions.

## Logical pseudo-classes

Modern CSS provides logical selector functions that reduce repetitive selector lists.

Important examples are:

`:is()`

`:not()`

`:where()`

`:has()`

These functions make it possible to express conditions directly in selectors.

## :is()

`:is()` matches an element when at least one selector in its argument list matches.

Conceptually:

`:is(h1, h2, h3)`

can group heading selectors.

It is useful when multiple alternatives should receive the same styling.

The specificity behavior is important. `:is()` takes the specificity of its most specific argument.

## :where()

`:where()` is similar to `:is()` in grouping selector alternatives, but it has zero specificity.

This makes it useful for establishing low-specificity defaults.

For example:

`:where(article, section) p`

can provide broad styling that is intentionally easy to override.

The distinction is:

`:is()`

uses the specificity of its most specific argument.

`:where()`

contributes zero specificity.

## :not()

`:not()` excludes elements matching its argument.

Example:

`button:not(.primary)`

matches buttons that do not have the `primary` class.

`:not()` is useful for exceptions and selective styling.

Its specificity should not be assumed to be zero. Modern CSS specificity rules account for the specificity of the selector passed to `:not()`.

## :has()

`:has()` is a relational pseudo-class.

Example:

`article:has(h1)`

selects an article containing an `h1` descendant.

Another example is:

`nav:has(a.active)`

which can select a navigation container containing an active link.

`:has()` is powerful because it allows an element to be selected based on a related element.

Traditional selectors often move from an ancestor toward a descendant, while `:has()` allows the selector condition to depend on a related descendant or other relative selector relationship.

Because it can express complex relationships, it should be used deliberately in large and frequently changing interfaces.

## Selector lists

A comma creates a selector list.

For example:

`h1, h2, h3`

means that the same CSS rule can apply to all three selector alternatives.

This is different from whitespace.

`h1 h2`

means an `h2` descendant of an `h1`.

The comma creates alternatives, while whitespace expresses a descendant relationship.

## Selector whitespace

Whitespace is one of the most important details in CSS selector syntax.

Compare:

`.card.title`

with:

`.card .title`

The first requires one element with both classes.

The second requires a `.title` descendant of `.card`.

Similarly:

`nav > a`

requires a direct child.

`nav a`

allows any descendant.

Small syntax differences can completely change the matching scope.

## Selector specificity

Specificity is a mechanism used during the CSS cascade to compare competing declarations when appropriate.

A simplified specificity representation can be expressed as:

`(inline, IDs, classes/attributes/pseudo-classes, elements/pseudo-elements)`

Examples include:

`p`

has conceptual specificity `(0, 0, 0, 1)`.

`.text`

has conceptual specificity `(0, 0, 1, 0)`.

`#article-title`

has conceptual specificity `(0, 1, 0, 0)`.

`article.featured p`

has conceptual specificity `(0, 0, 1, 2)`.

`#main-content article.featured p`

has conceptual specificity `(0, 1, 1, 2)`.

Specificity is compared from the highest-order component toward the lower-order components.

Specificity is not the complete CSS cascade. Cascade origins, importance, cascade layers, scoping considerations, specificity, and source order can all affect the final result.

The statement that "the most specific selector always wins" is therefore incomplete.

## Source order

When applicable cascade conditions and specificity are equal, source order can determine the winning declaration.

For example, if two equally applicable rules with equal specificity assign different values to the same property, the declaration appearing later can win.

This is one reason CSS organization and predictable stylesheet structure are important.

## Pseudo-class versus pseudo-element

A pseudo-class describes a state or condition.

Examples:

`:hover`

`:focus`

`:first-child`

A pseudo-element represents a conceptual subpart or generated portion of an element.

Examples:

`::before`

`::after`

`::first-letter`

`::first-line`

`::selection`

Modern CSS generally uses double-colon syntax for pseudo-elements.

The two concepts should not be confused.

## Combinator reference

The four major relationship combinators covered by the script are:

| Symbol | Name | Example | Meaning |
|---|---|---|---|
| whitespace | Descendant | `article p` | Any matching descendant |
| `>` | Child | `article > p` | Direct child |
| `+` | Adjacent sibling | `h1 + p` | Immediately following sibling |
| `~` | General sibling | `h1 ~ p` | Later sibling with the same parent |

These relationships are fundamental to understanding how CSS navigates document structure.

## Attribute selector reference

| Selector | Meaning |
|---|---|
| `[disabled]` | Attribute exists |
| `[type="email"]` | Exact attribute value |
| `[href^="https"]` | Value begins with a string |
| `[href$=".pdf"]` | Value ends with a string |
| `[data-id*="user"]` | Value contains a string |
| `[data-role~="admin"]` | Value contains a whitespace-separated word |
| `[lang|="en"]` | Exact language value or dash-prefixed language value |

Attribute selectors are especially valuable when an attribute represents actual state or semantic information.

## Data attributes

Custom data attributes use the `data-*` convention.

Example:

`data-status="published"`

CSS can select such state using:

`[data-status="published"]`

Data attributes can be appropriate when a value represents state or metadata that is genuinely part of the document.

They should not automatically replace classes. A class is often clearer when the concept is primarily a reusable visual or component state.

## Accessibility and selectors

CSS selectors can influence accessibility.

The most important interaction-related consideration is focus visibility.

A rule such as:

`button:focus-visible`

can provide a visible indication when an interactive element receives focus.

Selectors can also respond to accessibility-related attributes such as:

`[aria-expanded="true"]`

This can synchronize visual state with an existing accessibility state.

CSS should not be used to manufacture accessibility semantics. The underlying HTML and ARIA implementation must remain correct.

## Semantic HTML and selectors

Semantic HTML makes selectors easier to reason about.

Important semantic elements include:

`header`

`nav`

`main`

`article`

`section`

`footer`

`button`

`form`

`label`

Using an element selector such as `nav` can be appropriate when the rule genuinely applies to navigation.

Generic structural selectors based heavily on `div` nesting are usually harder to maintain.

## Selector architecture

A maintainable stylesheet generally assigns different responsibilities to different selector types.

Element selectors are useful for broad semantic defaults.

Classes are useful for reusable components and visual states.

IDs are generally best reserved for unique document relationships or situations where their high specificity is intentional.

Attribute selectors are useful when meaningful attributes represent state.

Combinators are useful for relationship-dependent styling.

Pseudo-classes are useful for interaction, form state, and structural conditions.

Logical pseudo-classes can express exceptions and alternatives without excessive repetition.

A selector should communicate why an element is being styled rather than simply describing the current path through the DOM.

## Brittle selectors

A deeply nested selector such as:

`body main section article div ul li a span`

depends heavily on a particular document structure.

If the HTML changes, the selector may stop matching.

A component-oriented selector such as:

`.product-card__title`

communicates the intended role more directly.

Structural selectors are not inherently wrong. They are useful when the relationship itself is the design requirement. The problem arises when unnecessary structural depth is used as a substitute for meaningful component classes.

## Selector specificity and maintainability

High specificity can create a chain of overrides.

For example, styling a component through multiple IDs, classes, and ancestors can make later changes difficult.

Using a predictable class-based architecture can keep specificity low and make the cascade easier to understand.

`:where()` can also be useful for deliberately low-specificity defaults.

`!important` should not be treated as the standard solution to specificity problems. Repeated use of `!important` can conceal architectural problems and make future overrides harder.

## CSS and JavaScript

CSS selector syntax is also used by browser DOM APIs.

Common JavaScript APIs include:

`document.querySelector()`

`document.querySelectorAll()`

`element.matches()`

`element.closest()`

For example, JavaScript can use a selector string to retrieve the first matching element or a collection of all matching elements.

This means CSS selector knowledge is useful when working with JavaScript DOM manipulation, event delegation, component behavior, and frontend testing.

## Dynamic selectors and security

Selectors constructed from dynamic input require care.

Suppose an application constructs a selector by concatenating a user-controlled ID with `#`.

Special CSS characters can alter the meaning of the selector.

In browser JavaScript, dynamically generated identifiers can be escaped with the platform's `CSS.escape()` functionality before being incorporated into a selector.

An even better design can sometimes avoid dynamic selector construction entirely by using DOM APIs that directly compare or retrieve attributes.

The security issue is primarily about unsafe string construction and unintended selection, not ordinary static CSS selector syntax.

## CSS escaping

CSS identifiers have syntax rules.

Most common class and ID names are straightforward, but HTML can contain identifiers with characters that have special meaning in CSS.

For example, an ID containing a colon may require escaping when used in a selector.

The conceptual transformation is:

`item:123`

to a selector representation containing an escaped colon.

The browser's CSS parser has comprehensive escaping rules. The Python script contains only an educational approximation and should not be treated as a replacement for the browser's `CSS.escape()` implementation.

## Performance considerations

Modern browsers contain sophisticated CSS selector matching and style recalculation systems. Simple assumptions such as "every complex selector is slow" are therefore misleading.

Nevertheless, selector architecture can influence style matching, invalidation, and maintainability.

Potentially problematic patterns include unnecessarily deep selector chains and selectors that encode large amounts of incidental DOM structure.

A selector such as:

`body main section article div p`

is tightly coupled to structure.

A component class such as:

`.article-text`

can provide a more stable styling target.

Selectors involving relationships such as `:has()` can express powerful conditions and should be used with an understanding of the size and mutation frequency of the DOM.

The most important practical performance principle is to prioritize clear, maintainable selectors and measure real application behavior rather than optimizing selectors based solely on theoretical assumptions.

## Debugging selectors

A CSS rule can fail for several different reasons.

The selector may match no elements.

The selector may match too many elements.

The selector may match the intended element, but another declaration may win in the cascade.

The selector may have lower specificity than a competing selector.

A pseudo-class may not currently be active.

An attribute may be absent or have a different value.

A child relationship may actually be a descendant relationship.

A selector can therefore be syntactically correct while still being logically incorrect for the intended component.

A useful debugging question is:

"Which elements does this selector actually match?"

The browser's developer tools can be used to inspect matched rules, computed styles, specificity, and DOM structure.

## Common mistakes

### Confusing a compound selector with a descendant selector

`.card.title`

requires one element to have both classes.

`.card .title`

requires `.title` to be inside `.card`.

### Confusing child and descendant selectors

`.card > .title`

requires a direct parent-child relationship.

`.card .title`

allows arbitrary descendant depth.

### Confusing adjacent and general siblings

`h2 + p`

requires the paragraph to immediately follow the heading.

`h2 ~ p`

allows any later paragraph sibling.

### Confusing :nth-child() and :nth-of-type()

`:nth-child(2)` counts all element children.

`:nth-of-type(2)` counts only elements of the same type.

### Overusing IDs

IDs create high specificity and reduce styling flexibility.

Reusable classes are usually more appropriate for reusable visual patterns.

### Removing focus indicators

Removing focus outlines without an accessible replacement can make keyboard navigation difficult.

### Assuming specificity controls everything

The cascade contains more than specificity.

### Using arbitrary DOM depth

Long structural selectors are often fragile.

### Constructing selectors from unescaped input

Dynamic selector strings should be handled carefully.

## Limitations of CSS selectors

CSS selectors are powerful matching mechanisms, but they are not general-purpose application logic.

Selectors do not perform arbitrary business calculations, database operations, network requests, or complex procedural workflows.

CSS can respond to document state when that state is represented through HTML structure, classes, attributes, or supported pseudo-classes.

For example, CSS can style an order marked as `data-status="loss"`, but the calculation determining whether the order is profitable belongs to application logic.

## Real-world applications

CSS selectors are used throughout web development.

Typical applications include:

- Styling semantic HTML elements.
- Building reusable UI components.
- Styling navigation states.
- Highlighting active pages.
- Styling form validation states.
- Creating responsive component layouts.
- Applying alternating table-row styles.
- Styling checked controls.
- Representing component state through classes or attributes.
- Creating accessible focus indicators.
- Selecting elements through JavaScript DOM APIs.
- Building component systems with predictable class structures.
- Styling content based on semantic relationships.
- Applying conditional visual states through `:not()`, `:is()`, `:where()`, and `:has()`.

## Production best practices

Use selectors that communicate intent.

Prefer reusable classes for reusable visual patterns.

Use semantic element selectors for broad element-level defaults.

Keep specificity under control.

Avoid unnecessary ID selectors for component styling.

Avoid excessive DOM-dependent selector chains.

Use child selectors only when the direct relationship is genuinely important.

Use descendant selectors when any descendant at the required scope should match.

Use attribute selectors when the attribute represents meaningful information.

Use state pseudo-classes for actual interaction or form state.

Preserve visible focus behavior.

Use `:where()` when low specificity is deliberately desirable.

Use `:is()` to reduce repeated alternatives when its specificity behavior is understood.

Use `:not()` for clear exclusions.

Use `:has()` for meaningful relational conditions rather than replacing every component class with structural logic.

Escape dynamic selector input when selector construction is unavoidable.

Test selectors against realistic HTML structures.

## Selector design reference

| Requirement | Appropriate selector |
|---|---|
| All elements | `*` |
| All paragraphs | `p` |
| Reusable component | `.card` |
| Unique element | `#main` |
| Element with an attribute | `[disabled]` |
| Exact attribute value | `[type="email"]` |
| Descendant relationship | `.card .title` |
| Direct child relationship | `.card > .title` |
| Immediate sibling | `h2 + p` |
| Later sibling | `h2 ~ p` |
| First child | `:first-child` |
| Last child | `:last-child` |
| Specific child position | `:nth-child(2)` |
| Position among same type | `:nth-of-type(2)` |
| Hover state | `:hover` |
| Keyboard-visible focus | `:focus-visible` |
| Invalid form state | `:invalid` |
| Exclusion | `:not(...)` |
| Selector alternatives | `:is(...)` |
| Zero-specificity grouping | `:where(...)` |
| Related-element condition | `:has(...)` |

## Important distinctions

| First concept | Second concept | Distinction |
|---|---|---|
| `p` | `.p` | Element selector vs class selector |
| `.card.title` | `.card .title` | Same element vs descendant |
| `article p` | `article > p` | Any descendant vs direct child |
| `h1 + p` | `h1 ~ p` | Immediate sibling vs later sibling |
| `:nth-child(2)` | `:nth-of-type(2)` | All children vs same element type |
| `:is(...)` | `:where(...)` | Normal specificity behavior vs zero specificity |
| `:hover` | `.hover` | Browser state vs ordinary class |
| `[disabled]` | `[disabled="true"]` | Attribute presence vs exact value |
| `#main` | `.main` | Unique ID vs reusable class |
| `:not(...)` | `:has(...)` | Exclusion vs relational condition |

## Practical selector patterns

A reusable component may use:

`.card`

`.card__title`

`.card__description`

`.card--featured`

`.card:hover`

`.card:focus-within`

`.card:has(.badge)`

A navigation component may use:

`nav > a`

`nav > a.active`

`nav > a[aria-current="page"]`

A form may use:

`form input:invalid`

`input:required`

`input:disabled`

`input:checked`

A content layout may use:

`article > h1`

`article p`

`article p:first-of-type`

These patterns are effective because they combine selector syntax with clear component or semantic intent.

## Implementation concepts demonstrated by the Python script

The script builds an HTML-like tree using Python objects. Each element stores:

- Its tag name.
- Its ID.
- Its classes.
- Its attributes.
- Its children.
- Its parent.

The model supports:

- Descendant traversal.
- Ancestor traversal.
- Sibling inspection.
- Parent-child relationships.
- Class matching.
- ID matching.
- Attribute matching.
- Structural pseudo-class simulation.
- Selector predicate composition.
- Basic selector tokenization.
- Simplified identifier validation.
- Specificity modeling.
- Selector testing with assertions.

The script deliberately does not attempt to implement the complete CSS grammar or browser rendering engine. Its purpose is to make the important selector concepts executable and observable.

## Selector study checklist

- Understand the purpose of CSS selectors.
- Recognize the universal selector.
- Write element selectors.
- Write class selectors.
- Write ID selectors.
- Combine simple selectors.
- Understand compound selectors.
- Understand descendant selectors.
- Understand child selectors.
- Understand adjacent sibling selectors.
- Understand general sibling selectors.
- Use attribute presence selectors.
- Use attribute equality selectors.
- Understand attribute prefix, suffix, substring, word, and language matching.
- Understand structural pseudo-classes.
- Understand state pseudo-classes.
- Distinguish `:nth-child()` from `:nth-of-type()`.
- Understand `:not()`.
- Understand `:is()`.
- Understand `:where()`.
- Understand `:has()`.
- Understand selector lists.
- Understand specificity.
- Understand that specificity is only one part of the cascade.
- Design selectors for maintainability.
- Preserve accessible focus states.
- Handle dynamic selectors carefully.
- Test selector scope when debugging.
