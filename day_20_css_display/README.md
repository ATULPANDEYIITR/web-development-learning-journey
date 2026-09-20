<!-- File: README.md -->

# CSS Display Laboratory

## Project purpose

CSS controls how HTML elements are laid out, painted, clipped, and positioned. A large part of understanding CSS requires being able to distinguish properties that appear similar but operate at different stages of rendering.

This repository provides an executable browser laboratory focused on:

- `display: block`
- `display: inline`
- `display: inline-block`
- `display: none`
- `visibility`
- `overflow`
- `position: static`
- `position: relative`
- `position: absolute`
- `position: fixed`
- `position: sticky`

The application provides an interactive playground where CSS values can be changed without editing the source code.

## Repository structure

The repository is intentionally small because the subject is a browser-level CSS topic.

`index.html` contains the application structure and instructional content.

`css/styles.css` contains the complete visual design and demonstration styles.

`js/app.js` controls the interactive CSS playground.

`tests/display-playground.test.js` contains executable Node.js tests for the playground state model.

`.github/workflows/ci.yml` validates JavaScript syntax, runs tests, and verifies required project files.

`Dockerfile` packages the static site with Nginx.

`compose.yaml` provides a local container deployment.

## Prerequisites

For direct browser usage, no build tool is required.

For JavaScript tests:

- Node.js 20 or newer

For Docker:

- Docker Engine with Compose support

## Running locally

The project can be opened directly by loading `index.html` in a browser.

For a local HTTP server, run:

`python -m http.server 8000`

Then open `http://localhost:8000`.

A local HTTP server is useful because it serves the ES module used by `js/app.js` through a normal HTTP origin.

## Running tests

Install no packages because the test suite uses the Node.js built-in test runner.

Run:

`npm test`

The test suite checks:

- default CSS state
- block display
- inline display
- `display: none`
- `visibility: hidden`
- overflow values
- positioning values
- CSS dimension serialization

JavaScript syntax can also be checked directly with:

`node --check js/app.js`

## CSS box participation

The first important distinction is whether an element participates in normal layout.

With `display: block`, the element generates a block-level box. A typical block box starts on a new line and can accept width and height in the ordinary way.

With `display: inline`, the element participates in line layout. It is designed for content that belongs within a line of text. Width and height do not behave like they do for an ordinary block box.

With `display: inline-block`, the element remains part of inline formatting while retaining a rectangular box whose dimensions can be controlled. This makes it useful for compact controls and other elements that need to sit beside one another while still accepting box dimensions.

The important lesson is that `block`, `inline`, and `inline-block` describe different layout participation behavior. They do not simply mean large, small, and medium elements.

## `display: none`

`display: none` removes the element from the rendered layout.

For example:

`display: none;`

The element does not consume its normal layout space. Elements around it are laid out as though that rendered box were not present.

This is different from reducing opacity to zero. An element with `opacity: 0` can still occupy layout space and can still participate in interaction unless other controls are applied.

It is also different from `visibility: hidden`.

## `visibility`

`visibility` controls whether an element is visible while retaining its layout participation.

The common values are:

`visibility: visible;`

`visibility: hidden;`

`visibility: collapse;`

`visible` is the normal state.

`hidden` prevents normal visual rendering while the element's layout space remains.

`collapse` has specialized behavior and is particularly associated with table-related layout. Its behavior should not be treated as a general-purpose replacement for `hidden`.

A useful mental model is:

- `display` controls layout participation and the generated display box.
- `visibility` controls visibility while normally retaining layout space.

## `display: none` versus `visibility: hidden`

Consider two elements:

`display: none;`

and:

`visibility: hidden;`

The first does not retain its normal rendered layout space.

The second normally retains its layout space while becoming visually hidden.

This distinction matters when changing a user interface dynamically. Removing an element from layout can cause surrounding content to move. Hiding it with `visibility` can preserve the surrounding geometry.

The appropriate choice depends on the desired interface behavior rather than on a rule that one property is universally preferable.

## Overflow

A CSS box can have a finite width and height while its content is larger than that available area.

The `overflow` property controls this situation.

Common values include:

`overflow: visible;`

`overflow: hidden;`

`overflow: clip;`

`overflow: auto;`

`overflow: scroll;`

`visible` allows overflowing content to remain visible outside the box.

`hidden` clips overflowing content.

`clip` clips overflow without creating the scrolling behavior associated with a scroll container.

`auto` allows the browser to provide scrolling when needed according to the overflow situation.

`scroll` establishes scrolling behavior even when the content does not currently require scrolling in the same way as `auto`.

Overflow is especially important for:

- code panels
- tables
- dashboards
- cards with constrained dimensions
- horizontal navigation
- media containers
- application sidebars
- modal content

## Overflow and accessibility

Clipping content can make information difficult or impossible to access.

Before using `overflow: hidden`, check whether the content is genuinely decorative, intentionally clipped, or available through another interaction.

A visually elegant fixed-height component can become inaccessible if meaningful text is silently clipped.

For user interfaces containing large amounts of content, scrolling containers should have sufficient visual and keyboard usability.

## Positioning

The `position` property describes how an element is positioned relative to normal document flow and its containing environment.

The principal values demonstrated by the application are:

- `static`
- `relative`
- `absolute`
- `fixed`
- `sticky`

## Static positioning

`position: static` is the normal default positioning mode.

The element participates in normal document flow.

Offset properties such as `top`, `right`, `bottom`, and `left` do not reposition an ordinary statically positioned element.

Example:

`position: static;`

This is the baseline against which the other positioning modes can be understood.

## Relative positioning

`position: relative` keeps the element's normal position in document flow while allowing its visual position to be shifted.

Example:

`position: relative;`

followed by an offset such as:

`top: 10px;`

The original position remains part of the layout calculation even though the element is visually shifted.

Relative positioning is also commonly used to establish a positioning context for descendants using absolute positioning.

For example:

`.card { position: relative; }`

and:

`.badge { position: absolute; top: 12px; right: 12px; }`

The badge can then be positioned relative to the appropriate positioned ancestor.

## Absolute positioning

`position: absolute` removes the element from normal document flow.

Its final position is established using its containing block and offsets.

A common pattern is:

`.card { position: relative; }`

with:

`.badge { position: absolute; top: 10px; right: 10px; }`

The parent establishes the positioning context and the child is positioned inside it.

Absolute positioning is useful for:

- badges
- notification indicators
- overlays
- icons inside controls
- decorative layers
- precisely positioned UI elements

It should not automatically be used for constructing an entire page layout. Normal flow, flexbox, and grid are usually more appropriate for relationships between major page regions.

## Fixed positioning

`position: fixed` removes the element from normal flow and normally positions it relative to the viewport.

A typical example is a control that remains visible while the page scrolls.

Example:

`position: fixed;`

A fixed element can cover other content if its size and stacking order are not considered carefully.

Common uses include:

- persistent navigation
- floating controls
- utility buttons
- overlays
- application-level controls

## Sticky positioning

`position: sticky` combines characteristics of normal flow and positioned behavior.

A sticky element participates in flow until a specified scroll threshold is reached.

The repository demonstrates this with:

`position: sticky;`

and:

`top: 68px;`

The `top` value establishes the threshold at which the element sticks.

Sticky positioning depends on the scrolling environment. Ancestor overflow settings, container dimensions, and available scrolling space can affect its behavior.

## Display and positioning are separate concepts

It is important not to treat `display` and `position` as alternatives.

They solve different problems.

For example, an element can use:

`display: block;`

and:

`position: relative;`

at the same time.

Another element can use:

`display: inline-block;`

and:

`position: relative;`

The display value describes how the element's box participates in layout, while position describes how the element is positioned in relation to normal flow and its positioning context.

## Formatting context

CSS layout is affected by formatting contexts.

Normal block flow arranges block-level boxes vertically.

Inline formatting arranges inline-level content into lines.

Other layout systems such as flexbox and grid create their own layout behavior and can be selected through `display`.

For this repository, the emphasis is on the foundational distinction between traditional block and inline formatting and the separate concerns of visibility, overflow, and positioning.

## Width and height behavior

The playground changes the target box's width and height.

For a normal block or inline-block box, explicit dimensions can be observed directly.

For an inline element, width and height do not operate like they do for a standard block-level box. This is one of the reasons inline and inline-block should not be considered interchangeable.

The dimensions of a CSS box are also affected by box sizing, padding, borders, min/max constraints, and the layout context.

This project intentionally keeps the demonstration focused on display behavior rather than introducing every box-model variable at the same time.

## Box model interaction

CSS dimensions are not isolated from the box model.

The rendered size of an element can involve:

- content
- padding
- border
- margin

The default `box-sizing` behavior for most elements is `content-box`, meaning an explicitly declared width generally refers to the content box.

This repository sets:

`box-sizing: border-box;`

globally.

That makes width and height calculations easier to reason about in the laboratory because declared dimensions include padding and borders.

The universal selector is used only for this educational sizing normalization:

`* { box-sizing: border-box; }`

## Common mistakes

### Using `display: none` when layout space should remain

If an interface must preserve the position of surrounding elements, `display: none` may cause unwanted movement. `visibility: hidden` can preserve layout space when that is the intended behavior.

### Expecting width and height to behave identically on inline elements

Inline formatting is line-oriented. A developer should not expect an inline element to behave like an ordinary rectangular block.

### Using absolute positioning for ordinary page layout

Absolute positioning can make elements overlap and can disconnect them from normal document flow. It is most useful when the element has a genuine positional relationship with a containing block.

### Forgetting the containing block

An absolutely positioned child does not simply position itself relative to whichever parent visually looks closest. The relevant containing block depends on the positioning rules of its ancestors.

### Using `overflow: hidden` without checking content

Clipping can hide information and can make content difficult to access.

### Expecting `sticky` to work in every container

Sticky behavior depends on scrolling containers, offsets, available space, and ancestor layout conditions.

### Confusing visibility with accessibility

A CSS technique that changes visual rendering should not automatically be assumed to produce the desired accessibility semantics.

## Edge cases

### Empty elements

An empty block can still generate a box whose dimensions are controlled by CSS.

### Long unbroken content

Long strings can expose overflow behavior differently from ordinary prose. Text wrapping and word-breaking properties can become relevant.

### Nested positioned elements

Nested `relative` and `absolute` elements can produce different containing blocks depending on which ancestor establishes the relevant positioning context.

### Multiple overflow axes

CSS also supports separate horizontal and vertical overflow properties:

`overflow-x`

and:

`overflow-y`

This matters when horizontal and vertical scrolling need different behavior.

### Sticky inside a scrolling ancestor

A sticky element's behavior can change when an ancestor establishes a scrolling mechanism. The complete containing and scrolling structure must be considered when debugging sticky layouts.

## Performance considerations

The CSS properties in this project are generally inexpensive compared with application-level operations such as large JavaScript computations or repeated network requests.

Performance problems can still appear when complex layouts are repeatedly recalculated or when large numbers of elements are dynamically modified.

Practical considerations include:

- avoid unnecessary style changes in tight JavaScript loops
- batch DOM updates where possible
- avoid repeatedly forcing layout measurements after writes
- use browser developer tools to inspect layout and paint behavior
- keep scrolling containers purposeful
- test interactive layouts on lower-powered devices

The project does not claim a universal performance advantage for one property over another. Rendering cost depends on the complete document, browser engine, content, and interaction pattern.

## Security considerations

The application contains no server-side processing, authentication, user accounts, or secret credentials.

The interactive playground assigns predefined values selected from HTML controls. It does not evaluate arbitrary CSS or execute user-supplied JavaScript.

The repository should continue to avoid inserting untrusted strings into `innerHTML` if the playground is expanded to accept free-form user input.

When deploying a static site, the hosting environment should use HTTPS and appropriate security headers.

## Browser behavior and developer tools

Modern browser developer tools provide direct ways to inspect these concepts.

Useful inspection tasks include:

- toggling `display` declarations
- toggling `visibility`
- changing overflow values
- inspecting computed styles
- viewing the box model
- identifying positioned ancestors
- inspecting sticky positioning
- observing layout shifts

The browser's computed-style view is particularly useful when a rule appears correct in source code but is overridden by another selector.

## Docker

The static application is served by Nginx.

Build the image with:

`docker compose build`

Start it with:

`docker compose up -d`

Open:

`http://localhost:8080`

Stop it with:

`docker compose down`

The container does not require a Node.js runtime because the browser executes the JavaScript and Nginx serves the static files.

## CI/CD

The GitHub Actions workflow performs lightweight repository validation.

It:

- checks out the repository
- installs Node.js 20
- validates JavaScript syntax
- executes the Node.js test suite
- verifies required files exist

No deployment credentials are stored in the repository.

## Production considerations

For a production static deployment, the application can be served from a CDN or static hosting provider.

A production deployment should consider:

- HTTPS
- cache policy
- compression
- security headers
- content type correctness
- asset versioning
- monitoring
- accessibility testing
- browser compatibility testing
- responsive behavior
- error handling at the hosting layer

The Docker configuration is suitable for a simple static deployment but does not attempt to provide a complete enterprise infrastructure platform.

## Real-world applications

The concepts demonstrated here appear throughout web interfaces.

Block and inline formatting are foundational to document layout.

Inline-block is useful for compact legacy-style controls and certain component arrangements.

`display: none` is common in conditional interfaces, menus, dialogs, and responsive layouts.

`visibility` can be useful when visual presence must change without changing layout geometry.

Overflow is fundamental to scrollable panels, data tables, dashboards, media areas, and constrained application windows.

Relative and absolute positioning are frequently used for badges, overlays, icons, and component-level placement.

Fixed positioning is common for viewport-level utilities.

Sticky positioning is frequently used for persistent section headers, table headers, navigation elements, and reading interfaces.

## Architectural model

The repository follows a simple static architecture:

Browser → `index.html` → `css/styles.css` and `js/app.js`

The browser renders the semantic HTML, applies the CSS cascade and layout rules, and executes the JavaScript module that updates selected style properties.

The test suite is separate from browser rendering. It verifies the state transformation logic using the Node.js built-in test runner.

The Docker deployment adds:

Browser → Nginx container → static application files

This separation keeps the educational subject visible without introducing an unnecessary backend service.
