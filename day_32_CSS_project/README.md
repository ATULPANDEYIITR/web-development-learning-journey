# Responsive Landing Page From Scratch

A technical landing-page project built around semantic HTML, responsive CSS, and lightweight JavaScript. The implementation demonstrates how a landing page can adapt to different viewport sizes without maintaining separate desktop and mobile versions of the page.

The project also includes a Python generator and validator and a C++ constraint-based case study. These implementations approach the same responsive-design problem from different technical perspectives.

## Project structure

| File | Responsibility |
|---|---|
| `index.html` | Semantic document structure, navigation, hero content, features, process section, contact form, and footer |
| `styles.css` | Design tokens, typography, Grid, Flexbox, responsive breakpoints, accessibility states, and reduced-motion behavior |
| `script.js` | Mobile navigation state, keyboard interaction, viewport-state synchronization, form feedback, and dynamic footer year |
| `responsive_landing_page.py` | Generates the landing page files and performs static structural validation |
| C++ case study | Models responsive layout decisions through viewport and component constraints |

## Responsive design principles

Responsive design is the process of allowing a user interface to adapt to the space and conditions available to it. The page does not assume that a visitor has a particular device. Instead, its layout responds to available width.

The implementation uses a mobile-first baseline. The narrow layout is the default CSS state, and the larger-screen layout is introduced through a media query.

At narrow widths:

- Navigation collapses behind a menu button.
- Hero content and the visual preview are stacked.
- Feature cards occupy one column.
- Contact content and the form are stacked.
- The decorative rotation on the visual preview is removed.

At larger widths:

- Navigation becomes a horizontal row.
- Hero copy and visual content use two Grid columns.
- Feature cards use three columns.
- Process and contact sections can use two columns.
- More horizontal space is used without changing the underlying HTML structure.

This approach prevents the page from becoming dependent on a fixed desktop canvas.

## Why mobile-first CSS is used

The stylesheet defines the smallest practical layout first. Larger layouts are enhancements of that baseline.

This reduces the amount of CSS required for narrow screens and makes the basic content structure usable even when advanced layout rules are unavailable or overridden.

The principal responsive breakpoint is `700px`. It is a content-driven breakpoint for this particular design rather than a universal definition of a mobile device or tablet.

The important question is whether the navigation, hero content, and cards have enough room to maintain their intended hierarchy. A different landing page with different content could legitimately require a different breakpoint.

## Container behavior

The `.container` class uses a fluid width with a maximum width.

Its narrow-screen behavior uses `calc(100% - 2rem)`, which creates horizontal breathing room. At larger widths, the gutter increases while `max-width` prevents the content from expanding indefinitely.

This is preferable to a fixed width such as `width: 1200px`, because a fixed width can produce horizontal scrolling on small screens.

The container also keeps very wide displays from producing excessively long text lines.

## Fluid typography

The hero heading uses `clamp()`:

`font-size: clamp(3rem, 11vw, 7.5rem);`

The first value establishes a lower bound, the middle expression provides fluid scaling, and the final value establishes an upper bound.

This gives the heading three useful properties:

- It remains large enough to preserve the visual hierarchy.
- It responds to intermediate viewport widths.
- It stops growing once it reaches a practical maximum.

Using `clamp()` avoids creating many breakpoint-specific font-size declarations.

## CSS custom properties

The stylesheet defines design tokens in `:root`.

Examples include:

- `--color-background` for the page surface.
- `--color-text` for primary typography.
- `--color-muted` for secondary content.
- `--color-accent` for high-priority visual emphasis.
- `--color-border` for component boundaries.
- `--space-*` variables for spacing.
- `--radius-*` variables for component shape.
- `--container-width` for the maximum content width.

This separates design decisions from individual selectors. If the accent color changes, the component rules can continue to reference the same variable.

## Grid and Flexbox

The project uses both major CSS layout systems for different relationships.

Flexbox is appropriate for one-dimensional alignment. The header navigation, hero action buttons, metrics, and footer use Flexbox because their primary requirement is arranging items along a row or column.

CSS Grid is used for two-dimensional page structures. The hero changes from one column to two columns, and the feature cards change from a stacked arrangement to a three-column grid.

This distinction prevents the page from relying on excessive absolute positioning.

## Semantic HTML structure

The document contains a `header`, `nav`, `main`, several `section` elements, `article` elements for independent features, a `form`, and a `footer`.

The hierarchy gives the content meaning independently of its visual appearance.

The hero contains the primary `h1`. Subsequent sections use `h2` headings, while individual feature cards use `h3` headings.

The markup therefore provides a useful structural outline before CSS is applied.

## Mobile navigation

The desktop navigation is visible without JavaScript.

At narrow widths, CSS hides the navigation until it receives the `is-open` class. JavaScript controls that class and synchronizes the button's `aria-expanded` attribute.

The menu button uses:

`aria-expanded="false"`

as its initial state and:

`aria-controls="primary-navigation"`

to identify the navigation region it controls.

This means the interaction has both a visual state and an accessible state.

The JavaScript closes the menu when:

- A navigation link is activated.
- Escape is pressed.
- The viewport changes to the desktop layout.

The resize behavior prevents stale mobile state from remaining in the DOM after the layout switches to the larger-screen mode.

## Accessibility

Responsive behavior must not be separated from accessibility.

The skip link allows keyboard users to bypass repeated navigation.

The menu uses a native `button` rather than a clickable `div`, giving it appropriate keyboard semantics.

The focus-visible rule creates a visible focus indicator for keyboard navigation.

The contact form uses a real email input and the HTML `required` constraint. JavaScript calls `checkValidity()` and `reportValidity()` rather than replacing the browser's validation system.

The status message uses `aria-live="polite"` so its contents can be announced without aggressively interrupting the user.

The stylesheet also supports `prefers-reduced-motion`. This disables unnecessary motion for users who have requested reduced animation.

## Hero visual

The hero visual is generated entirely with HTML and CSS.

It consists of:

- A window-like outer surface.
- A toolbar.
- A label.
- CSS-generated lines.
- A small Grid of content blocks.
- An accent footer element.

Because it is not a raster image, it scales without requiring an additional image asset.

The visual uses `width: min(100%, 520px)` so it cannot exceed the width of its containing area.

The desktop presentation includes a small rotation as decoration. The rotation is removed on narrow screens and when reduced motion is requested.

## Contact form behavior

The form is deliberately local and does not pretend to submit data to a backend.

The HTML layer provides the input semantics and basic constraint validation.

The JavaScript layer:

- Reads the submitted email value.
- Trims surrounding whitespace.
- Checks that a value exists.
- Uses browser constraint validation.
- Displays a local status message.
- Resets the form after successful validation.

A production implementation must not rely on this client-side validation as a security control. Any real backend receiving form data must validate the input again on the server.

## Python implementation

The Python program takes a different role from the browser implementation.

`LandingPageContent` represents page content as structured data. The generator uses this model to create the hero, features, metrics, and other sections.

`html_escape()` protects generated content from being interpreted as arbitrary HTML. This is especially important when generated content eventually comes from external data rather than fixed source strings.

`build_html()`, `build_css()`, and `build_javascript()` create the individual project files.

The validator uses `ValidationIssue` and `ProjectReport` to separate findings from validation logic. It checks for structural requirements including responsive viewport metadata, semantic landmarks, accessibility attributes, Grid, Flexbox, fluid typography, media queries, and reduced-motion support.

The script also demonstrates a deliberate failure case by passing an incomplete project to the validator. This shows that validation is useful not only for successful projects but also for detecting missing responsive infrastructure.

## JavaScript implementation

The JavaScript file focuses on runtime interaction rather than layout.

The `setNavigationState()` function is the central state transition for the mobile menu. It updates the CSS class and the accessibility attribute together.

`isMobileLayout()` reads the current viewport width against the same breakpoint used by the stylesheet.

Optional chaining allows the script to remain resilient if an optional element is absent from a page.

The Escape-key handler improves keyboard operation, while the resize handler keeps the menu state synchronized with the responsive layout.

The form logic uses `FormData` to retrieve the submitted field and browser constraint validation to verify the email input.

No external npm package is required.

## C++ responsive layout case study

The C++ program models a different problem: how a layout engine can reason about content constraints before a browser renders the page.

Each `Component` contains:

- A component name.
- A minimum width.
- A preferred width.
- A minimum height.
- A flag indicating whether it can grow.

The `validate()` method rejects invalid constraints such as an empty component name, non-positive dimensions, or a preferred width smaller than the minimum width.

`LayoutEngine` evaluates viewport dimensions and produces a `LayoutResult`.

The result records:

- Navigation mode.
- Hero arrangement.
- Feature-column count.
- Estimated page height.
- Responsive warnings.

The program evaluates multiple viewport widths ranging from `320px` through `1440px`.

## Content-driven column calculation

The feature grid uses a minimum card width instead of identifying specific devices.

The model assumes that a feature card should have at least `260px` of usable width. The available content width is calculated after accounting for page gutters.

The number of possible columns is derived from:

`(usable_width + gap) / (minimum_card_width + gap)`

The result is then limited to the range from one to three columns.

This is a simplified model of a real responsive constraint. A browser's CSS Grid engine performs more sophisticated layout calculations, but the principle is the same: content requirements should influence layout decisions.

The algorithm operates in constant time for the feature grid because the calculation contains a fixed number of arithmetic operations.

## Why device-specific breakpoints are avoided

A design that says "mobile is 375px, tablet is 768px, desktop is 1440px" can become fragile because real viewport widths are continuous.

Users can resize browser windows to intermediate widths. Foldable devices, embedded browsers, split-screen windows, and unusual desktop dimensions also challenge rigid device categories.

A content-driven breakpoint asks a more useful question: does the current arrangement still have enough space to remain readable and usable?

The C++ case study illustrates this principle by evaluating component constraints rather than device names.

## Failure conditions

The C++ engine rejects a viewport below `320px` because the model explicitly defines that as its supported minimum.

It rejects non-positive viewport heights.

It rejects components with:

- Empty names.
- Non-positive minimum widths.
- Non-positive preferred widths.
- Non-positive minimum heights.
- Preferred widths smaller than their minimum widths.

These checks demonstrate an important engineering principle: invalid layout constraints should be detected at the boundary rather than allowed to propagate through later calculations.

## Performance considerations

The browser implementation uses native CSS layout rather than JavaScript-driven resize calculations.

The JavaScript does not continuously calculate element dimensions during scrolling. It reacts to meaningful events such as clicks, keyboard input, form submission, and viewport changes.

The C++ layout model evaluates a fixed set of components in linear time relative to the number of components. Feature-column calculation is constant time.

The generated page has no mandatory third-party JavaScript dependency.

The visual preview avoids a large image asset for the demonstration, which removes an image request. Real production landing pages may still require photographs, product screenshots, or illustrations and should optimize those assets appropriately.

## Security considerations

The demonstration does not send form data to a server.

If the contact form becomes connected to an API, client-side validation must not be treated as sufficient protection. Server-side validation is required because a client can be bypassed or modified.

The Python generator escapes dynamic HTML content before insertion. This is particularly important if the content model is later populated from user-controlled or external data.

The JavaScript does not use `eval()` or dynamically execute submitted strings.

Production form endpoints should also consider authentication where appropriate, rate limiting, abuse prevention, transport security, input validation, output encoding, and privacy requirements.

## Testing the responsive behavior

Responsive testing should include more than checking one phone and one desktop viewport.

Useful manual cases include:

- A very narrow viewport around `320px`.
- Intermediate widths near the `700px` breakpoint.
- A wide desktop viewport.
- Long hero headlines.
- Long feature descriptions.
- Keyboard-only navigation.
- Opening and closing the mobile menu repeatedly.
- Closing the menu with Escape.
- Switching between narrow and wide viewport modes while the menu is open.
- Submitting an empty email field.
- Submitting an invalid email value.
- Testing the page with reduced-motion preferences enabled.

The purpose of these cases is to test behavior at boundaries where responsive implementations are most likely to fail.

## Production implications

A production landing page should preserve the same separation of responsibilities demonstrated here.

HTML should describe the content and interaction semantics. CSS should control the responsive visual system. JavaScript should add behavior that genuinely requires runtime state.

The actual production content should be tested at its longest realistic lengths. Marketing copy, translations, customer names, pricing information, and validation messages can all be significantly longer than development placeholders.

Images should use appropriate dimensions and formats, and important content should not depend exclusively on decorative graphics.

The page should also be tested for keyboard access, focus visibility, semantic structure, contrast, reduced-motion preferences, and intermediate viewport widths.

The strongest responsive implementation is therefore not the one with the largest number of media queries. It is the one in which content, layout constraints, interaction behavior, and accessibility continue to work when the viewport and content change.
