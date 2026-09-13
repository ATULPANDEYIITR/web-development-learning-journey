# CSS Fundamentals

## Introduction

CSS stands for Cascading Style Sheets. It is the stylesheet language used to control the presentation of HTML documents.

HTML defines the structure and semantic meaning of content. CSS describes how that content should be presented. A heading, paragraph, button, card, or navigation element can be structurally represented in HTML and then styled through CSS.

CSS is commonly used for:

- Text color and typography
- Backgrounds
- Borders
- Spacing
- Element dimensions
- Visual states
- Layout
- Responsive behavior
- Accessibility-related presentation
- Component styling
- Design systems

The Python script accompanying this README teaches CSS from fundamental syntax through selector behavior, the cascade, specificity, inheritance, custom properties, validation, debugging, accessibility, performance, security, and production considerations. It also generates a real HTML and external CSS demonstration.

## Basic CSS structure

The fundamental CSS rule follows this structure:

    selector {
        property: value;
    }

For example:

    p {
        color: blue;
        font-size: 18px;
    }

The selector identifies the elements that should be affected. The property identifies the characteristic being changed. The value specifies the desired setting.

A property-value pair is called a declaration.

In the following declaration:

    color: blue;

`color` is the property and `blue` is the value.

A CSS rule can contain many declarations:

    .profile {
        color: #222;
        background-color: white;
        padding: 20px;
        border-radius: 8px;
    }

The curly braces contain the declarations associated with the selector. A colon separates each property from its value, and semicolons normally separate declarations.

## Selectors

Selectors are one of the most important parts of CSS because they determine which HTML elements receive a rule.

### Universal selector

The universal selector is:

    *

It can match elements generally within the document.

A common use is a box-sizing reset:

    *,
    *::before,
    *::after {
        box-sizing: border-box;
    }

### Type selector

A type selector targets HTML elements by element name:

    p {
        color: blue;
    }

This targets paragraph elements.

Other examples include:

    h1
    button
    article
    input
    nav

Type selectors have relatively low specificity.

### Class selector

A class selector begins with a period:

    .card {
        padding: 20px;
    }

It targets elements whose class list contains `card`.

Classes are generally the most useful selector type for reusable component styling.

### ID selector

An ID selector begins with a hash symbol:

    #main-title {
        color: navy;
    }

It targets an element with the corresponding ID.

IDs normally have greater specificity than classes and type selectors. For reusable visual styling, classes are usually easier to manage because multiple elements can share the same class.

### Attribute selector

Attribute selectors target elements according to their attributes.

Examples include:

    input[type="email"] {
        border-color: blue;
    }

    [disabled] {
        opacity: 0.6;
    }

Attribute selectors can also test whether an attribute begins with, ends with, or contains particular text.

Common forms include:

    [attr^="value"]

    [attr$="value"]

    [attr*="value"]

    [attr~="value"]

    [attr|="value"]

These provide more precise targeting without requiring additional classes in some situations.

## Selector combinators

Combinators express relationships between elements.

### Descendant combinator

    .card p

This selects paragraphs located anywhere inside an element with the `card` class.

### Child combinator

    .card > p

This selects paragraphs that are direct children of `.card`.

The distinction is important. A descendant can occur at any nesting depth, while a child must be immediately contained by the parent.

### Adjacent sibling combinator

    h2 + p

This selects a paragraph immediately following an `h2` element.

### General sibling combinator

    h2 ~ p

This selects paragraphs that occur later among the siblings of an `h2`.

## Grouped selectors

Several selectors can share a rule:

    h1, h2, h3 {
        font-family: sans-serif;
    }

Grouping reduces duplication when the same declarations genuinely apply to several selectors.

## Pseudo-classes

Pseudo-classes represent states or structural conditions.

Common examples include:

    :hover
    :focus
    :focus-visible
    :active
    :disabled
    :checked
    :first-child
    :nth-child()

For example:

    .button:hover {
        background-color: darkblue;
    }

A focus state is particularly important for keyboard accessibility:

    .button:focus-visible {
        outline: 3px solid #9db4ff;
        outline-offset: 2px;
    }

Removing focus indicators without providing a clear alternative can make an interface difficult or impossible to navigate effectively with a keyboard.

## Pseudo-elements

Pseudo-elements represent conceptual parts of an element.

Examples include:

    ::before
    ::after
    ::first-letter
    ::first-line
    ::selection

For example:

    .required::after {
        content: " *";
    }

Pseudo-elements are primarily presentation mechanisms. Essential information should not be placed only in CSS-generated content because CSS is not a substitute for semantic HTML.

## Declarations, properties, and values

A declaration has the general form:

    property: value;

Properties describe what is being changed.

Examples include:

    color
    background-color
    width
    height
    margin
    padding
    border
    font-size
    font-family
    display
    position

Values depend on the property.

For example:

    color: red;

uses a color keyword, while:

    width: 300px;

uses a length value.

CSS values can take many forms, including keywords, lengths, percentages, numbers, colors, functions, and custom properties.

## Common CSS value types

### Keywords

Some properties accept predefined keywords:

    display: block;

    position: relative;

### Lengths

A length can be specified with units such as:

    20px

    2rem

    10vw

Important length units include `px`, `em`, `rem`, `vw`, and `vh`.

### Percentages

Percentages are commonly used for dimensions relative to a containing context:

    width: 50%;

### Colors

CSS supports several color representations.

Examples include:

    red

    #3366ff

    rgb(51, 102, 255)

    rgba(51, 102, 255, 0.5)

    hsl(220 100% 60%)

### Functions

CSS provides functions for dynamic values and calculations.

For example:

    width: calc(100% - 40px);

The demonstration project also uses:

    width: min(100%, 360px);

### Custom properties

CSS custom properties behave as reusable design values:

    :root {
        --primary-color: #2457d6;
    }

They can then be referenced with:

    color: var(--primary-color);

Fallback values can be supplied:

    color: var(--missing-color, black);

## Inline CSS

Inline CSS is written directly in an HTML element:

    <p style="color: red;">Important text</p>

Inline CSS is useful for small demonstrations or highly localized situations, but it has significant maintainability disadvantages when used extensively.

Problems include:

- Reduced separation between structure and presentation
- Poor reuse
- Difficult large-scale maintenance
- Increased visual complexity in HTML
- Higher cascade priority than ordinary stylesheet rules

The generated HTML demonstration contains one inline declaration so that the technique can be observed directly.

## Internal CSS

Internal CSS is placed inside a `style` element in the HTML document:

    <style>
        p {
            color: blue;
        }
    </style>

Internal styles are useful when styles are specifically associated with one document.

They are less convenient when the same styles need to be shared across multiple pages.

The demonstration HTML uses internal CSS for a special example box.

## External CSS

External CSS is stored in a separate stylesheet.

HTML can reference the stylesheet with:

    <link rel="stylesheet" href="styles.css">

The external stylesheet can contain rules such as:

    body {
        margin: 0;
        font-family: Arial, sans-serif;
    }

External CSS provides strong separation between structure and presentation and makes styles reusable across documents.

For larger websites and applications, external stylesheets or equivalent stylesheet build systems are commonly preferred.

## Comparing the three CSS application methods

| Method | Location | Typical use | Main characteristic |
|---|---|---|---|
| Inline | HTML `style` attribute | Very local styling | High local priority and low reuse |
| Internal | HTML `style` element | Page-specific styles | Limited to the document |
| External | Separate CSS file | Shared site or application styling | Reusable and maintainable |

The script deliberately demonstrates all three methods in one generated page.

## The cascade

The term "cascading" refers to the mechanism used by CSS to resolve competing declarations.

Several CSS rules may match the same element and attempt to set the same property.

For example:

    p {
        color: blue;
    }

    p {
        color: red;
    }

When the declarations have equivalent cascade priority and specificity, the later declaration wins.

The complete cascade considers several factors, including origin and importance, cascade layers, specificity, scope, and source order.

A simple beginner model is useful, but production CSS should not be reduced to source order alone.

## Specificity

Specificity helps CSS determine which competing selector has greater priority.

A simplified hierarchy is:

    inline styles
        >
    ID selectors
        >
    class, attribute, and pseudo-class selectors
        >
    type selectors and pseudo-elements
        >
    universal selector

For example:

    p {
        color: blue;
    }

    .message {
        color: green;
    }

    #important-message {
        color: red;
    }

If one paragraph matches all three selectors, the ID selector normally has greater specificity than the class and type selectors.

A conceptual specificity notation is:

    inline - ID - class/attribute/pseudo-class - type/pseudo-element

Examples:

    p
        0-0-0-1

    .message
        0-0-1-0

    #message
        0-1-0-0

    #message .warning p
        0-1-1-1

Specificity should be kept manageable. Increasing specificity repeatedly to fix cascade problems often produces a fragile stylesheet.

## Source order

Source order becomes important when competing declarations have equivalent relevant priority and specificity.

For example:

    .notice {
        color: blue;
    }

    .notice {
        color: red;
    }

The later declaration can determine the final color.

This is one reason stylesheet organization matters.

## The `!important` declaration

CSS supports:

    color: red !important;

`!important` changes the priority of a declaration within the cascade.

It can be useful in specific situations, but using it everywhere creates difficult specificity and override problems.

A stylesheet that requires repeated `!important` declarations often has an underlying organization or specificity problem.

## Inheritance

Some CSS properties inherit from parent elements.

For example:

    body {
        color: #222;
        font-family: Arial, sans-serif;
    }

A paragraph inside the body can normally receive inherited values for properties that are inheritable.

Inheritance does not apply to every CSS property.

Properties such as `color` and `font-family` commonly inherit, while properties such as `margin`, `padding`, `border`, and `width` generally do not.

CSS provides keywords that explicitly control inheritance and cascade behavior:

    inherit
    initial
    unset
    revert
    revert-layer

For example:

    .child {
        color: inherit;
    }

## The CSS box model

The CSS box model is fundamental to understanding element dimensions.

The conceptual structure is:

    content
    padding
    border
    margin

Content is the actual content area.

Padding creates space inside the border.

Border surrounds the padding and content.

Margin creates space outside the border.

For example:

    .card {
        width: 300px;
        padding: 20px;
        border: 1px solid #ccc;
        margin: 30px;
    }

A common practice is:

    *,
    *::before,
    *::after {
        box-sizing: border-box;
    }

With `border-box`, the declared width and height calculations include the padding and border.

This often makes layout calculations easier to understand and maintain.

## Common fundamental properties

### Text

Common text-related properties include:

    color
    font-family
    font-size
    font-weight
    line-height
    text-align
    text-decoration

### Background

Common background properties include:

    background-color
    background-image
    background-size
    background-position

### Box model

Important box-related properties include:

    width
    height
    margin
    padding
    border
    box-sizing

### Display

Common display-related values include:

    block
    inline
    inline-block
    none
    flex
    grid

### Positioning

Common positioning properties include:

    position
    top
    right
    bottom
    left
    z-index

The script focuses on the fundamentals required to understand these properties rather than attempting to teach the entire CSS specification.

## Display behavior

`display` determines how an element participates in layout.

### Block

Block-level behavior generally causes an element to begin on a new line and occupy available horizontal space within its containing context.

### Inline

Inline elements participate in text flow. Their sizing behavior differs from block-level boxes.

### Inline-block

`inline-block` combines inline flow with a box that can accept dimensions.

### None

`display: none` removes the element from normal layout.

### Flex

`display: flex` creates a flex formatting context and is widely used for one-dimensional layout.

### Grid

`display: grid` creates a grid formatting context and is particularly useful for two-dimensional layouts.

The generated demonstration uses CSS Grid for its card layout.

## CSS custom properties

Custom properties are variables defined with names beginning with two hyphens.

Example:

    :root {
        --primary-color: #2457d6;
        --spacing-unit: 8px;
    }

They can be referenced with `var()`:

    .button {
        background-color: var(--primary-color);
        padding: var(--spacing-unit);
    }

Custom properties are useful for:

- Design tokens
- Repeated colors
- Spacing systems
- Typography values
- Theme values
- Component-level customization

The generated external stylesheet uses custom properties for its primary color, spacing, text color, border color, and other design values.

## Responsive CSS

Responsive CSS allows a layout to adapt to different viewport sizes.

Media queries provide conditional rules.

Example:

    @media (max-width: 800px) {
        .card-grid {
            grid-template-columns: 1fr;
        }
    }

The generated demonstration initially uses three columns and changes to one column at narrower viewport widths.

Responsive design is not simply about shrinking elements. It involves adapting layout, spacing, typography, navigation, and interaction patterns to the available space.

## Educational CSS parsing

The Python script includes a deliberately limited CSS parser.

It can parse simple rules such as:

    .card {
        color: red;
        padding: 20px;
    }

The parser converts the rule into a Python representation containing:

- Selector
- Property names
- Property values

This demonstrates the conceptual relationship between CSS source text and structured rules.

The parser is intentionally not a standards-compliant CSS parser. Real CSS supports considerably more syntax, including at-rules, comments, escaping, nesting-related features, functions, custom properties, layers, media queries, and other constructs.

A lightweight parser is therefore useful for education but should not be treated as a replacement for a browser's CSS parser.

## Validation

The script contains a small validation function for its educational CSS representation.

It checks conditions such as:

- Whether the selector is empty
- Whether property names have a reasonable structure
- Whether values are empty
- Whether values contain suspicious CSS delimiters

This illustrates an important engineering principle: structured input can be validated before it is written to an output file.

The validation is intentionally limited. Complete CSS validation requires understanding the CSS grammar and the specifications associated with individual properties.

## Common CSS mistakes

### Missing colon

Incorrect:

    color red;

Correct:

    color: red;

### Missing semicolon

Incorrect:

    color: red

Although the final declaration can often omit the semicolon, consistently writing semicolons is safer and clearer.

Correct:

    color: red;

### Wrong selector

These selectors are different:

    button

    .button

The first targets button elements. The second targets elements with the `button` class.

### Invalid property names

CSS property names must follow CSS syntax.

For example, the standard property is:

    background-color

not:

    backgroundcolour

### Incorrect units

CSS lengths require valid units where a unit is required.

For example:

    width: 20px;

is valid, while:

    width: 20 px;

is not equivalent.

### Confusing margin and padding

Margin is outside the border.

Padding is inside the border.

This distinction is essential for understanding layout spacing.

### Excessive `!important`

Repeated use of `!important` makes the cascade harder to control.

### Excessive selector specificity

A selector such as:

    main .content article.card div.title span

is generally more difficult to override than a simple component class.

### Removing focus indicators

Removing outlines without providing an accessible replacement can harm keyboard navigation.

### Using CSS as a security mechanism

CSS can hide content visually, but visual hiding is not authorization.

Sensitive information must be protected by application logic and appropriate server-side access controls.

## Edge cases and subtle behavior

### Invalid declarations

Browsers generally ignore declarations they cannot understand.

For example, an unknown property does not normally invalidate unrelated valid declarations in the same rule.

### Invalid property values

If a value is invalid for a property, that declaration may be discarded.

### Repeated properties

A rule can contain the same property more than once:

    p {
        color: blue;
        color: red;
    }

When the declarations have equivalent cascade priority, the later one wins.

### Shorthand properties

CSS provides shorthand properties.

For example:

    margin: 10px 20px;

represents top and bottom margins of `10px` and left and right margins of `20px`.

Longhand properties include:

    margin-top
    margin-right
    margin-bottom
    margin-left

Shorthand properties are convenient but should be used carefully when some individual sides need to retain different values.

### Missing custom properties

A declaration such as:

    color: var(--missing);

can become invalid at computed-value time if the custom property is unavailable and no fallback is provided.

A fallback can be supplied:

    color: var(--missing, black);

## CSS comments

CSS comments use the form:

    /* This is a CSS comment */

Comments can explain:

- Non-obvious decisions
- Component sections
- Temporary compatibility considerations
- Design-system organization

Comments should not be used to compensate for unclear naming or unnecessarily complicated CSS.

## CSS naming and maintainability

Reusable classes should generally communicate the role or purpose of a component.

Less useful:

    .blue-box-2

More meaningful:

    .profile-card

The second name describes what the component represents rather than its current color or visual implementation.

This distinction matters because designs change. A component called `.blue-box` becomes misleading if the design later changes to green.

## CSS architecture

A small website may need only one stylesheet.

Larger projects often organize styles conceptually into areas such as:

- Base styles
- Layout styles
- Components
- Utilities
- Themes
- Design tokens

The exact architecture should match the size and complexity of the application.

Creating a highly complicated CSS architecture for a small page can introduce unnecessary complexity.

## Debugging CSS

Browser developer tools are essential for practical CSS debugging.

A systematic debugging process is:

1. Verify that the stylesheet loaded.
2. Verify that the selector matches the intended element.
3. Inspect the element.
4. Check the Styles panel.
5. Look for declarations that are crossed out.
6. Check specificity.
7. Check source order.
8. Check inheritance.
9. Inspect the computed value.
10. Inspect the box model.
11. Test different viewport sizes.

If a color is not changing, possible causes include:

- The stylesheet was not loaded.
- The selector does not match.
- The declaration contains a syntax error.
- A different rule has higher priority.
- An inline declaration overrides the stylesheet.
- An inherited value is being misunderstood.
- The selected property is not the property actually controlling the visual result.

Randomly changing values is less effective than determining which stage of the cascade or layout process is responsible.

## Accessibility considerations

CSS should support accessible interaction and presentation.

### Focus

Keyboard users need a visible indication of the currently focused control.

The script demonstrates:

    :focus-visible

This can provide an appropriate focus style without removing the browser's ability to distinguish keyboard interaction.

### Contrast

Text and important interface components need sufficient visual contrast.

Color selection should be evaluated as part of accessibility rather than treated purely as a visual design choice.

### Text scaling

Layouts should tolerate reasonable increases in text size and should avoid rigid dimensions that unnecessarily cause content to become inaccessible.

### Reduced motion

Interfaces containing animations or transitions should consider user preferences for reduced motion.

### Color dependence

Important information should not be communicated through color alone.

For example, an error should not be identified only by making text red. Text, icons, structure, or another meaningful indication can provide additional communication.

### Semantic HTML

CSS controls presentation, not document meaning.

A visually styled `div` does not automatically become a semantic button. The HTML element should represent the correct purpose, while CSS controls its appearance.

## Security considerations

CSS is not an authorization mechanism.

For example:

    display: none;

can visually hide an element, but it does not make sensitive information secure.

Applications should protect sensitive information through appropriate access control and server-side logic.

### CSS injection

Applications that accept user-controlled CSS must treat the input as potentially dangerous.

Untrusted values should not be blindly inserted into style attributes or stylesheets.

### HTML injection

CSS does not protect an application from HTML injection. Applications generating HTML must handle untrusted input safely.

### External resources

Stylesheets can reference resources, and production applications should understand how their content security policy and resource-loading rules interact with CSS.

### Content Security Policy

A Content Security Policy can restrict style and resource sources. Its configuration should match the actual architecture of the application rather than being treated as a universal CSS solution.

## Performance considerations

CSS performance involves more than selector matching.

Important considerations include:

- Stylesheet size
- Unused CSS
- Resource loading
- Style recalculation
- Layout work
- Painting
- Rendering effects
- DOM complexity
- Animation behavior

Useful practices include:

- Remove unnecessary CSS in production.
- Avoid unnecessary duplication.
- Reuse styles where appropriate.
- Keep selector complexity reasonable.
- Avoid unnecessary DOM complexity.
- Use expensive visual effects deliberately.
- Compress production CSS when appropriate.

Modern browsers are highly optimized, so maintainability and correctness should not normally be sacrificed for tiny selector-level performance gains.

## Production considerations

Production CSS should be evaluated for:

### Correctness

Rules should behave correctly across supported browsers and viewport sizes.

### Maintainability

Another developer should be able to understand the stylesheet and modify it without creating unpredictable side effects.

### Accessibility

Focus, contrast, text scaling, motion preferences, semantic structure, and keyboard interaction should be considered.

### Performance

Unused CSS and unnecessary duplication should be controlled.

### Consistency

Repeated design values should be managed consistently. CSS custom properties can help establish design tokens.

### Specificity

Components should be easy to override without continuously increasing selector specificity.

### Browser compatibility

CSS features should be selected according to the browser support requirements of the application.

### Security

User-controlled data should not be blindly transformed into CSS or HTML.

### Deployment

Production CSS should be served correctly, cached appropriately, and compressed when suitable for the deployment environment.

## Generated demonstration project

The Python script generates a temporary project containing:

    index.html

    styles.css

The HTML document demonstrates external CSS through the stylesheet link, internal CSS through a `style` element, and inline CSS through a `style` attribute.

The external stylesheet demonstrates:

- CSS custom properties
- Universal selectors
- Element selectors
- Class selectors
- Descendant selectors
- Pseudo-classes
- Box sizing
- Grid layout
- Responsive media queries
- Borders
- Padding
- Margins
- Typography
- Colors
- Focus styling

The generated page can be opened in a browser and inspected with browser developer tools.

## Python implementation details

The Python program is deliberately self-contained and uses only the standard library.

The `CSSRule` class represents a CSS rule using:

- A selector
- A dictionary of declarations

Its `to_css()` method converts the structured representation into CSS source text.

The validation function checks the basic structure of these objects.

The parser function demonstrates how a restricted subset of CSS can be converted into Python objects.

The generated project uses Python's `pathlib` for filesystem handling and the standard `tempfile` module for temporary project creation.

The browser demonstration uses Python's standard `webbrowser` module.

## Testing

The script includes automated assertions covering:

- Valid CSS rule generation
- CSS property and value storage
- Simple CSS parsing
- Detection of invalid rule structures

These tests are intentionally small because the primary purpose of the program is educational. They demonstrate how CSS-related utility code can still be tested systematically.

## Important distinctions

### HTML versus CSS

HTML describes structure and semantics.

CSS describes presentation.

### Selector versus declaration

A selector identifies target elements.

A declaration specifies a property and its value.

### Property versus value

A property identifies what is being changed.

A value identifies how that property should be configured.

### Margin versus padding

Margin is outside the border.

Padding is inside the border.

### Class versus ID

Classes are reusable and generally suited to component styling.

IDs are intended to identify unique elements and carry greater specificity.

### Inline versus external CSS

Inline CSS is attached directly to an element.

External CSS is stored separately and can be reused across documents.

### Inheritance versus cascade

Inheritance transfers certain values from parent elements.

The cascade determines which competing declarations ultimately apply.

These mechanisms are related but are not the same.

## Practical CSS example

The script includes a complete profile-card example:

    .profile {
        width: min(100%, 360px);
        padding: 24px;
        background-color: white;
        color: #202735;
        border: 1px solid #d7deea;
        border-radius: 12px;
    }

    .profile h2 {
        margin-top: 0;
    }

    .profile .role {
        color: #64748b;
    }

This example demonstrates several important CSS concepts at once.

`.profile` is a class selector.

`width` is a property.

`min(100%, 360px)` is a function-based value.

`padding` controls internal spacing.

`background-color` controls the background.

`#202735` is a hexadecimal color value.

`.profile h2` is a descendant selector.

The example illustrates how selectors and declarations combine to style a reusable component.

## CSS fundamentals checklist

A strong understanding of CSS fundamentals includes the ability to:

- Explain the purpose of CSS.
- Recognize a CSS rule.
- Identify selectors.
- Identify declarations.
- Distinguish properties from values.
- Use type selectors.
- Use class selectors.
- Understand ID selectors.
- Use attribute selectors.
- Use descendant and child combinators.
- Understand pseudo-classes.
- Understand pseudo-elements.
- Explain the cascade.
- Explain specificity.
- Explain inheritance.
- Understand the box model.
- Distinguish margin from padding.
- Explain inline CSS.
- Explain internal CSS.
- Explain external CSS.
- Use CSS custom properties.
- Understand media queries.
- Debug CSS systematically.
- Preserve accessible focus states.
- Consider contrast and responsive behavior.
- Understand basic CSS performance considerations.
- Understand why CSS cannot provide application security.
- Use maintainable class names.
- Keep selector specificity under control.
