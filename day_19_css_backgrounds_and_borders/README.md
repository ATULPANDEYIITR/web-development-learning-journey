# CSS backgrounds and borders

## Topic scope

CSS backgrounds and borders control a large part of the visual presentation of web interfaces. The subject includes background colors, background images, gradients, image positioning and sizing, repeated backgrounds, multiple background layers, borders, rounded corners, outlines, shadows, background clipping, background origins, and the relationship between these properties and the CSS box model.

The three implementations in this repository approach the topic from different perspectives:

- Python models CSS concepts as structured data, validation functions, calculations, generated stylesheets, and tests.
- JavaScript demonstrates CSS-oriented data generation, validation, browser DOM construction, responsive strategies, and executable testing.
- C++ develops an industry-style component and design-token system that models visual properties with typed structures and serializes them into CSS.

The implementations intentionally avoid browser-specific dependencies in their core logic. The JavaScript file contains an optional browser DOM demonstration, while the Python and C++ programs concentrate on modeling, validation, generation, and reasoning about CSS behavior.

## Fundamental concepts

### Background

A CSS background is the visual painting associated with an element behind its content. It can consist of a background color, one or more background images, gradients, or combinations of these.

A background does not normally create layout space. A background image is visual decoration attached to an element rather than a replacement for semantic HTML content.

A basic declaration is represented by:

`background-color: #0f172a;`

The longhand properties allow individual aspects to be controlled:

- `background-color`
- `background-image`
- `background-position`
- `background-size`
- `background-repeat`
- `background-attachment`
- `background-origin`
- `background-clip`

The `background` shorthand combines several of these properties into a more compact declaration.

### Border

A border surrounds the element's padding and content areas. A normal border has three principal characteristics:

- width
- style
- color

For example:

`border: 1px solid #334155;`

The sides can also be controlled independently:

`border-top`

`border-right`

`border-bottom`

`border-left`

Each side can have its own width, style, and color.

### Border radius

`border-radius` rounds the corners of an element.

A uniform radius can be written as:

`border-radius: 16px;`

Four values describe the four corners:

`border-radius: 4px 12px 20px 28px;`

The order is:

1. top-left
2. top-right
3. bottom-right
4. bottom-left

A large radius is often used to create pill-shaped controls:

`border-radius: 9999px;`

A circle can be produced when the element has equal dimensions:

`border-radius: 50%;`

CSS also supports elliptical radii by specifying horizontal and vertical radii separately.

## Background images

A background image is introduced with `background-image`.

`background-image: url("hero.jpg");`

A useful production pattern usually specifies at least the following properties:

`background-image: url("hero.jpg");`

`background-repeat: no-repeat;`

`background-position: center;`

`background-size: cover;`

The Python, JavaScript, and C++ implementations all represent this combination as a reusable visual configuration.

### Background position

`background-position` determines where the background image is initially positioned.

Common values include:

`left top`

`center`

`right bottom`

`50% 25%`

`20px 40px`

Position becomes particularly important when `background-size: cover` crops an image. A photograph can have an important subject near one edge, so simply using `center` may crop the wrong region.

For a portrait-oriented subject, a declaration such as `background-position: 70% center` may be more appropriate than a centered position, provided testing confirms the result.

## Background size

`background-size` determines the rendered size of a background image.

Important values include:

- `auto`
- explicit dimensions
- percentages
- `cover`
- `contain`

### Cover

`cover` scales the image until the entire background painting area is covered.

This can crop part of the source image.

The implementations calculate the conceptual scale using:

`max(container width / image width, container height / image height)`

For a 1200 × 500 container and a 1600 × 900 image, the height requirement determines the scale. The resulting image becomes larger than the container in one dimension, so cropping occurs.

### Contain

`contain` scales the image until the complete image fits within the available area.

The conceptual scale is:

`min(container width / image width, container height / image height)`

The complete source image remains visible, but empty space can remain around it.

### Cover versus contain

| Property | `cover` | `contain` |
|---|---|---|
| Entire container covered | Yes | Not necessarily |
| Entire source image visible | Not necessarily | Yes |
| Cropping possible | Yes | No |
| Empty space possible | Usually no | Yes |
| Typical use | Hero backgrounds | Complete image presentation |

The choice depends on whether filling the visual area or preserving the entire image is more important.

## Background repetition

`background-repeat` determines whether an image repeats.

Common values are:

- `repeat`
- `repeat-x`
- `repeat-y`
- `no-repeat`
- `space`
- `round`

`no-repeat` is common for photographs and hero images.

Repeating backgrounds are useful for textures, patterns, and decorative surfaces.

## Background attachment

`background-attachment` controls how a background behaves relative to scrolling.

Common values include:

- `scroll`
- `local`
- `fixed`

`fixed` can produce a visual parallax-like effect in some designs, but it should not be assumed to behave identically across all devices and browser configurations. Mobile performance and interaction should be tested before relying on it.

## Multiple backgrounds

CSS permits multiple background layers.

A typical example is:

`background-image: linear-gradient(rgb(15 23 42 / 0.88), rgb(15 23 42 / 0.88)), url("dashboard.jpg");`

The first listed background image is the uppermost image layer. Later layers are behind it.

This makes it possible to place a gradient overlay over an image without introducing a separate HTML element.

Multiple background layers can be combined with corresponding comma-separated values for properties such as position, size, and repeat.

## Gradients

A gradient is a generated CSS image. It does not require a bitmap file.

The three major gradient families demonstrated by the implementations are:

- linear gradients
- radial gradients
- conic gradients

CSS also provides repeating forms.

### Linear gradients

A linear gradient transitions colors along a line.

`linear-gradient(90deg, #0ea5e9, #8b5cf6)`

The angle determines the direction.

Color stops can specify explicit positions:

`linear-gradient(90deg, #0ea5e9 0%, #8b5cf6 55%, #ec4899 100%)`

The Python, JavaScript, and C++ examples also demonstrate the conceptual arithmetic of interpolating between two RGB colors.

### Radial gradients

A radial gradient expands from a point or region.

`radial-gradient(circle at center, #38bdf8, #0f172a)`

The center can be moved to another position:

`radial-gradient(circle at 20% 30%, #38bdf8, #0f172a)`

Radial gradients are useful for glows, spotlights, soft visual emphasis, and atmospheric backgrounds.

### Conic gradients

A conic gradient progresses around a center point.

`conic-gradient(from 45deg, #ef4444, #f59e0b, #22c55e, #3b82f6, #ef4444)`

They are useful for circular visualizations, color wheels, decorative rings, and certain progress indicators.

### Repeating gradients

Repeating gradients repeat their color-stop pattern.

A linear repeating pattern can be represented as:

`repeating-linear-gradient(45deg, #111827 0 10px, #1f2937 10px 20px)`

These patterns are useful for stripes and textures.

## Borders

A basic border is commonly written as:

`border: 2px solid #475569;`

The declaration contains:

- width: `2px`
- style: `solid`
- color: `#475569`

The examples demonstrate these styles:

- `none`
- `solid`
- `dashed`
- `dotted`
- `double`
- `groove`
- `ridge`
- `inset`
- `outset`

`solid`, `dashed`, and `dotted` are common application-interface choices. The other styles have more specialized visual uses.

### Individual border sides

Each side can have different properties.

For example:

`border-top-color: #38bdf8;`

`border-right-color: #8b5cf6;`

`border-bottom-color: #ec4899;`

`border-left-color: #22c55e;`

This can be useful for diagrams, status indicators, accent treatments, and asymmetric visual systems.

## Border images

CSS can use an image to construct a border through `border-image`.

Important properties include:

- `border-image-source`
- `border-image-slice`
- `border-image-width`
- `border-image-outset`
- `border-image-repeat`

A typical structure is:

`border: 12px solid transparent;`

`border-image-source: url("frame.png");`

`border-image-slice: 30;`

`border-image-repeat: round;`

Border images are more specialized than ordinary borders and should be tested carefully with different dimensions.

## Border radius

Rounded corners are produced with `border-radius`.

Uniform rounding:

`border-radius: 16px;`

Different corners:

`border-radius: 4px 12px 20px 28px;`

Elliptical rounding:

`border-radius: 30px / 15px;`

Circular geometry:

`border-radius: 50%;`

A large radius combined with a fixed height is frequently used for pills and badges.

The visual result also depends on the element's dimensions. `border-radius: 50%` does not automatically turn every rectangular element into a circle.

## Background clipping

`background-clip` controls the area through which the element's background is painted.

Common values include:

- `border-box`
- `padding-box`
- `content-box`
- `text`

The implementations explicitly model these values.

### Border-box

The background can be painted through the border box.

### Padding-box

The background is restricted to the padding box.

This is useful when a transparent border is being used as part of a gradient-border technique.

### Content-box

The background is restricted to the content box.

### Text

With appropriate browser support and related techniques, a background can be used as the visual source for text. This is commonly seen in gradient-text effects.

Background clipping should not be confused with descendant clipping.

## Background origin

`background-origin` determines the box used as the origin for positioning a background image.

The common values are:

- `border-box`
- `padding-box`
- `content-box`

This becomes important when padding and borders are significant and a background image must be positioned relative to a specific box.

## Overflow and clipping

`overflow` affects how overflowing content and descendants are handled.

For example:

`overflow: hidden;`

is frequently combined with:

`border-radius: 20px;`

when a child image must visually remain inside rounded corners.

This is conceptually different from `background-clip`.

`background-clip` controls the element's own background painting area.

`overflow` controls overflowing content and descendants.

This distinction is important when constructing cards containing images, overlays, pseudo-elements, and nested content.

## Outlines

An outline is visually similar to a border but behaves differently in layout.

A useful focus treatment is:

`outline: 3px solid #38bdf8;`

`outline-offset: 4px;`

The JavaScript and C++ case study explicitly models a `:focus-visible` rule.

Visible focus is an accessibility requirement for keyboard users. Removing outlines without providing an equivalent focus indicator can make interactive controls difficult to operate.

## Box shadows

`box-shadow` adds visual shadows to an element.

The general structure is:

`box-shadow: offset-x offset-y blur-radius spread-radius color;`

For example:

`box-shadow: 0 8px 24px rgb(0 0 0 / 0.20);`

An inset shadow uses the `inset` keyword:

`box-shadow: inset 0 2px 8px rgb(0 0 0 / 0.30);`

Multiple shadows can be specified:

`box-shadow: 0 2px 6px rgb(0 0 0 / 0.18), 0 12px 30px rgb(0 0 0 / 0.14);`

The order of multiple shadows matters because the visual layers interact.

## Text shadows

`text-shadow` applies a shadow to text.

Example:

`text-shadow: 0 3px 8px rgb(0 0 0 / 0.35);`

Text shadows should support readability rather than compensate for inadequate contrast.

## CSS custom properties

The implementations use CSS custom properties to represent reusable design tokens.

For example:

`--surface: #0f172a;`

`--border: #334155;`

`--radius: 16px;`

`--shadow: 0 12px 32px rgb(0 0 0 / 0.22);`

A component can then reference them:

`background: var(--surface);`

`border: 1px solid var(--border);`

`border-radius: var(--radius);`

`box-shadow: var(--shadow);`

This reduces repetition and makes large visual systems easier to maintain.

## Python implementation

The Python implementation is structured as an executable study file.

### CSSRule

`CSSRule` represents a selector and a collection of declarations. Its `render()` method serializes the internal representation into CSS.

This demonstrates an important relationship between programming data structures and generated stylesheet content.

### Background sizing

`describe_background_size()` calculates the dimensions produced by the conceptual `cover` and `contain` algorithms.

The function validates all dimensions and rejects zero or negative values.

### Gradient interpolation

`interpolate_color()` models the arithmetic of transitioning between two RGB colors.

For each channel:

`interpolated = start + (end - start) × progress`

The implementation validates that progress remains between zero and one.

### Structured shadows

The `BoxShadow` class represents:

- offset X
- offset Y
- blur radius
- spread radius
- color
- inset state

It then serializes those values to CSS.

### Validation

The Python implementation validates:

- hexadecimal colors
- radius syntax
- image URL forms
- numerical dimensions

The validation is intentionally limited because a production CSS parser would need a complete CSS grammar rather than a handful of regular expressions.

### Visual audit

`VisualDesignAudit` demonstrates how engineering rules can be encoded as machine-checkable conditions.

The audit checks:

- focus visibility
- text over imagery
- decorative versus essential imagery
- shadow complexity
- fixed-background usage

This is not a replacement for accessibility testing. It is an example of how simple policy checks can be automated.

### Component generation

`create_component_styles()` constructs a complete card system containing:

- a dark surface
- border
- rounded corners
- shadow
- pseudo-element gradient overlay
- media background
- content surface
- gradient button
- visible focus state

This combines the individual properties into a realistic component rather than treating them as unrelated syntax examples.

### Testing

The Python file uses `unittest`.

The tests cover:

- color validation
- radius validation
- gradient interpolation
- shadow serialization
- background-size calculations
- generated component CSS

## JavaScript implementation

The JavaScript file complements the Python implementation by emphasizing executable application logic and browser behavior.

### CSSRule class

The JavaScript `CSSRule` class provides a mutable builder for CSS declarations.

It supports:

`set(property, value)`

and:

`render()`

This is useful for demonstrating how a web application could construct stylesheet fragments from application configuration.

### Gradient generators

The JavaScript implementation includes functions for:

- linear gradients
- radial gradients
- conic gradients

The functions validate the number of color stops before producing the CSS string.

### Browser DOM demonstration

`createBrowserDemo()` detects whether a DOM exists.

When executed in a browser, it:

1. creates a `<style>` element,
2. inserts CSS,
3. creates an article,
4. creates content,
5. creates a button,
6. appends the component to the document.

This demonstrates the relationship between JavaScript application logic and CSS presentation.

When executed in Node.js, the browser-only function is safely skipped because `document` is unavailable.

### JavaScript validation

The file validates:

- hexadecimal colors
- radius values
- image sources

The image-source check rejects `javascript:` URLs. Real applications should perform stronger validation and use a clearly defined allowlist for externally supplied assets.

### Responsive asset selection

`chooseBackgroundAsset()` illustrates how a program can choose between mobile, tablet, and desktop background assets based on viewport width.

In actual web development, responsive image strategies such as `<picture>`, `srcset`, and other image-specific techniques may be more appropriate when the image is meaningful content rather than decoration.

### Performance model

The JavaScript implementation contains a conceptual visual complexity calculation based on:

- background layers
- shadow layers
- gradient layers
- large blur effects

The result is not a browser benchmark. It is an educational heuristic showing that visual complexity can increase as more expensive effects are layered across many elements.

## C++ case study

The C++ program models a design system for a web application.

The scenario is a component library that needs reusable definitions for cards, media areas, controls, borders, gradients, rounded corners, shadows, clipping, and focus states.

### Problem being solved

A large web application can accumulate many CSS declarations across pages and components. If visual properties are represented only as scattered strings, consistency and validation become difficult.

The case study therefore represents visual properties as typed C++ structures before converting them into CSS.

### RGBColor

`RGBColor` stores:

- red
- green
- blue
- alpha

The constructor validates channel ranges and alpha values.

`toCSS()` serializes the object into modern CSS RGB syntax.

### Gradient interpolation

The `interpolate()` function performs numerical interpolation between two colors.

It validates the progress value and returns a new `RGBColor`.

This provides a computational model for a basic two-color gradient transition.

### BackgroundLayer

`BackgroundLayer` represents different background types through an enum:

- color
- image
- linear gradient
- radial gradient
- conic gradient

It also stores:

- position
- size
- repeat
- attachment

The object can serialize itself into CSS.

### Border

The `Border` class stores:

- width
- style
- color

`BorderStyle` provides a strongly typed representation of CSS border styles.

This avoids repeatedly passing arbitrary style strings through the application.

### BorderRadius

`BorderRadius` represents four corner values and serializes them into the four-value CSS shorthand.

### BoxShadow

`BoxShadow` models:

- horizontal offset
- vertical offset
- blur
- spread
- color
- inset state

It validates the blur radius and serializes the result to CSS.

### Design tokens

`DesignTokens` provides centralized values for:

- surfaces
- borders
- accent colors
- radii
- shadows

The object generates a `:root` block containing CSS custom properties.

This resembles a common design-system architecture where visual values are centrally defined and components reference those values.

### UIComponent

`UIComponent` represents a CSS selector and its declarations.

It supports property assignment and nested component representations.

The resulting CSS can be generated with `toCSS()`.

The design demonstrates how typed application configuration can be transformed into stylesheet output.

### Product card

`createProductCard()` produces a realistic card component containing:

- a card surface
- border
- rounded corners
- clipping
- shadow
- background media
- content section
- gradient button
- visible focus state

This makes the C++ implementation a system-level case study rather than a collection of isolated syntax demonstrations.

## Background layers and painting order

When multiple background images are specified, the first image layer is visually above subsequent image layers.

For example:

`background-image: linear-gradient(...), url("hero.jpg");`

places the gradient above the photograph.

This is particularly useful for improving text readability over photographs.

A separate overlay element is not always necessary.

## Box model relationship

A normal CSS box can be understood in layers:

- content
- padding
- border
- margin

Background painting and borders interact with these regions.

A border contributes to the element's outer dimensions under the default `content-box` sizing model.

With:

`box-sizing: border-box;`

the declared width and height refer to the border box, which makes dimensional reasoning easier for many component systems.

The topic of backgrounds and borders therefore cannot be separated completely from the CSS box model.

## Important distinctions

### Background image versus HTML image

A CSS background is generally appropriate when an image is decorative or part of the presentation.

An HTML `<img>` is usually preferable when the image is meaningful content, needs alternative text, participates in document semantics, or should be treated as content by assistive technologies.

### Border versus outline

A border participates in the box model.

An outline is painted outside the border and does not normally affect layout dimensions.

Focus indicators are a common use for outlines.

### Background clip versus overflow

`background-clip` controls the region in which the element's own background is painted.

`overflow` controls overflowing content and descendants.

A rounded card containing an image may need both `border-radius` and overflow clipping depending on how the child content is constructed.

### Border radius versus clip-path

`border-radius` is designed around rounded box corners.

`clip-path` can create much more general shapes.

They solve related but different geometric problems.

### Box shadow versus border

A border is a defined edge around the element and participates in layout.

A shadow is a visual effect around the element and does not normally affect layout dimensions.

## Edge cases

### `cover` cropping

`cover` can remove important parts of an image. The visual focal point must therefore be tested at different viewport sizes.

### `contain` empty space

`contain` preserves the entire image but can produce unused areas.

### Transparent borders

A transparent border still consumes border-box space even though its color is transparent.

This can be useful when a component switches between border states without changing dimensions.

### Large border radii

Large radii can produce visually unexpected geometry when an element becomes very small or its width and height differ significantly.

### Background layer mismatch

When multiple background images are used, comma-separated properties should be structured consistently. The number and ordering of values can affect which layer receives which configuration.

### Shadow accumulation

A single component can look reasonable with one shadow but become expensive or visually muddy when dozens or hundreds of components each use large blurred shadows.

### Text over imagery

A technically valid background does not guarantee readable text. Contrast must be checked against the actual rendered background.

## Common mistakes

### Using background images for essential information

Important content should not depend only on a CSS background. Semantic HTML should carry meaningful information.

### Ignoring image cropping

A `cover` background can crop faces, logos, products, or other important subjects.

### Removing focus indicators

Global rules such as removing all outlines can harm keyboard navigation.

A custom `:focus-visible` treatment should be at least as visible as the browser's default indication.

### Using unnecessarily large images

A background image that is several megabytes can create unnecessary network and decoding costs.

Images should be appropriately sized for their rendered role.

### Excessive shadows

Large blur radii and many shadow layers can increase rendering work and create poor visual hierarchy.

### Mixing unrelated visual values

Hard-coded colors, radii, and shadows throughout a large application can create inconsistency. Design tokens provide a centralized alternative.

### Trusting unvalidated external CSS values

Applications that dynamically construct CSS from user-controlled data should treat CSS values as untrusted input. URL schemes and injected declarations should be validated and constrained.

## Limitations of the implementations

The Python and C++ programs do not implement a complete browser rendering engine.

They model CSS properties and generate CSS strings.

The JavaScript browser demonstration constructs actual DOM and style content, but it is still not a replacement for testing in real browsers.

The regular-expression validators are intentionally small. CSS is a complex grammar with many valid forms, custom functions, escaped identifiers, browser-specific features, and context-sensitive parsing requirements.

The visual complexity score is a conceptual engineering heuristic rather than a performance measurement.

Actual rendering performance depends on the browser engine, device hardware, viewport size, number of elements, compositing behavior, image decoding, animation, and other factors.

## Performance considerations

### Image size

Background images should be appropriately sized for their display context.

A huge source image used in a small card wastes bandwidth and may increase memory use.

### Modern formats

Modern image formats can reduce transfer size when supported by the target browser environment.

### Number of layers

Multiple background layers are useful, but excessive layers can make styles harder to maintain and can increase rendering complexity.

### Large blur effects

Large shadows and blur-based visual effects can be more expensive than simple colors and borders.

### Fixed backgrounds

`background-attachment: fixed` should be tested on mobile devices and lower-powered systems.

### CSS complexity

A simple declaration such as:

`background: #0f172a;`

has substantially less visual work than a component combining several large gradients, multiple shadows, large blur regions, and high-resolution images.

## Accessibility considerations

Backgrounds and borders are visual presentation. They should not be the only mechanism communicating essential information.

Text placed over an image must maintain sufficient contrast.

Decorative backgrounds should not carry critical instructions or state information that is unavailable elsewhere.

Interactive elements require visible focus indicators.

Rounded corners and shadows should not be treated as accessibility mechanisms. They are presentation choices.

A visual hierarchy should remain understandable without depending on subtle shadows or color differences alone.

## Security considerations

CSS is often treated as harmless presentation, but dynamically generated CSS can become a security concern when untrusted values are inserted into stylesheets.

Potential risks include:

- unsafe URLs
- CSS injection
- unexpected external resource loading
- untrusted style declarations
- data leakage through inappropriate resource references

Applications should validate and constrain dynamic CSS values.

The examples reject `javascript:` image sources as a basic demonstration, but a production system should use a stronger URL parser, a suitable allowlist, and context-specific security controls.

## Implementation considerations

A maintainable visual system generally benefits from separating:

- design tokens
- component structure
- state styles
- responsive rules
- asset selection
- accessibility rules

CSS custom properties are particularly useful for centralizing colors, radii, and shadows.

For example:

`--surface: #0f172a;`

can be consumed by many components without duplicating the actual color value.

The C++ implementation models this concept with `DesignTokens`.

The Python implementation models the same idea through dictionaries and dataclasses.

The JavaScript implementation uses objects and generated rules.

## Practical applications

CSS backgrounds and borders are used in:

- navigation bars
- dashboards
- authentication screens
- landing pages
- product cards
- profile interfaces
- notification panels
- pricing tables
- data visualization containers
- media galleries
- buttons
- badges
- status indicators
- hero sections
- modal dialogs
- application shells
- design systems

A typical modern card can combine:

`background`

`border`

`border-radius`

`box-shadow`

`overflow`

and a `:focus-visible` rule into one reusable visual component.

## Language comparison

| Concern | Python | JavaScript | C++ |
|---|---|---|---|
| Rapid modeling | Strong | Strong | Moderate |
| CSS string generation | Strong | Strong | Strong |
| Browser interaction | Indirect | Native | Not native |
| Validation demonstrations | Strong | Strong | Strong |
| Data structures | Dataclasses and dictionaries | Objects and classes | Typed structures and classes |
| DOM integration | Not native | Native in browsers | Not native |
| Static type enforcement | Optional/type hints | Dynamic | Strong compile-time types |
| Low-level control | Limited compared with C++ | Limited | Strong |
| Unit testing in supplied file | `unittest` | Custom assertions | Custom assertions |
| Design-system modeling | Strong | Strong | Strong |

Python is effective for educational modeling, data validation, generation, and testing.

JavaScript is the natural complement when CSS must interact with the browser DOM, viewport state, events, and application logic.

C++ demonstrates how a strongly typed system can represent a visual design language and generate deterministic CSS from structured objects.

## Best practices

Use `background-color` as a reliable fallback when an image or gradient is unavailable.

Use semantic HTML for meaningful content.

Use `background-image` primarily for presentation and decorative imagery.

Choose `cover` when filling the entire area is more important than preserving every pixel of the source image.

Choose `contain` when preserving the entire image is more important than filling the entire area.

Test `background-position` at multiple viewport sizes.

Use design tokens for repeated colors, radii, borders, and shadows.

Keep focus indicators visible.

Avoid excessive visual effects.

Optimize image assets.

Use `overflow` deliberately when child content must respect rounded geometry.

Use `background-clip` when the requirement concerns the element's own background painting region.

Validate dynamic CSS input.

Test the result at narrow and wide viewport sizes.

## Real-world component pattern

A robust card component can combine the concepts studied here:

`background: #0f172a;`

`border: 1px solid #334155;`

`border-radius: 20px;`

`overflow: hidden;`

`box-shadow: 0 16px 40px rgb(0 0 0 / 0.22);`

A media region can use:

`background: url("product.jpg") center / cover no-repeat;`

A visual overlay can use:

`linear-gradient(...)`

An interactive button can use a gradient background, rounded border, restrained shadow, and an explicit `:focus-visible` outline.

This pattern demonstrates why backgrounds, borders, radius, shadows, and clipping are often designed together rather than independently.

## Testing strategy

Testing visual CSS should include more than checking whether a declaration is syntactically valid.

Useful test dimensions include:

- narrow viewport
- wide viewport
- short viewport
- tall viewport
- large image
- small image
- different image aspect ratios
- keyboard navigation
- focus states
- high zoom
- long text
- missing image
- slow image loading
- dark and light surfaces
- high contrast environments
- mobile browsers

The supplied programs automate the portions that can be represented deterministically, such as validation, serialization, dimension calculations, and generated CSS structure.

Visual behavior itself still requires browser rendering tests.

## Complexity considerations

Most property assignments are constant-time from the perspective of application code.

The complexity of the supplied generation structures is approximately:

- inserting a declaration into the C++ `std::map`: `O(log n)`
- iterating through `n` declarations: `O(n)`
- rendering `n` CSS rules: `O(n)` relative to the number of stored declarations
- interpolating one RGB color: `O(1)`
- validating one simple hexadecimal color: `O(k)` where `k` is the input length

Browser rendering complexity is different. It depends on the actual visual tree, style recalculation, layout, painting, rasterization, compositing, image decoding, and device characteristics.

The source-code complexity of a CSS declaration therefore should not be confused with its possible browser rendering cost.

## Files and execution

The Python implementation can be executed with a standard Python 3 installation.

The JavaScript implementation can be executed with a modern JavaScript runtime such as Node.js. The browser-specific function requires a browser DOM.

The C++ implementation targets C++17 or later and uses only the C++ standard library.

The generated CSS can be copied into a browser-based HTML environment to inspect the visual effects represented by the programs.
