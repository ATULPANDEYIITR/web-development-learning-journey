# HTML accessibility

## Introduction

HTML accessibility is the practice of creating web pages and interfaces that can be used by people with different abilities, technologies, and interaction methods.

Accessibility applies to much more than screen readers. A well-designed accessible website should support keyboard users, people who use screen magnification, people with visual, auditory, motor, speech, cognitive, or neurological disabilities, people using mobile devices, and users working in constrained environments.

HTML accessibility is strongly connected to four areas:

- semantic HTML
- keyboard and focus behavior
- accessible names, states, and relationships
- communication with assistive technologies

The Python study script presents these concepts through HTML examples, small simulations, validation functions, accessibility checklists, and progressively more advanced implementation patterns.

## Accessibility and a11y

Accessibility is commonly abbreviated as **a11y**. The abbreviation uses the first and last letters of the word and the number of letters between them.

Accessibility means that information and functionality can be:

- perceived
- understood
- navigated
- operated
- interpreted by assistive technology
- used through different input methods

Accessibility is not a separate layer that should be added after a website has been built. HTML structure, interaction design, CSS, JavaScript, content, forms, navigation, and testing all influence accessibility.

## Assistive technology

Assistive technology is technology that helps people interact with digital systems.

Examples include:

- screen readers
- screen magnifiers
- speech recognition systems
- alternative keyboards
- switch devices
- refreshable Braille displays
- specialized pointing devices

The browser acts as an important intermediary between web content and assistive technology. HTML semantics, CSS visibility, browser state, and ARIA can influence the information exposed through the browser's accessibility representation.

## Screen readers

A screen reader converts relevant accessibility information into speech or Braille.

A common misconception is that a screen reader simply reads the HTML source from top to bottom. In practice, browsers expose an accessibility representation containing concepts such as:

- role
- accessible name
- state
- property
- relationships
- structure

For example, a native button may be exposed conceptually as a button with the name "Save changes". A user can then navigate between controls rather than listening to every character in the source.

Screen-reader users may navigate by:

- headings
- landmarks
- links
- buttons
- form controls
- tables
- lists
- reading order

This makes meaningful HTML structure extremely important.

## WCAG

WCAG stands for **Web Content Accessibility Guidelines**.

WCAG organizes accessibility around four fundamental principles, commonly called **POUR**:

| Principle | Meaning |
|---|---|
| Perceivable | Information must be presented in ways users can perceive |
| Operable | Interface functionality must be usable |
| Understandable | Information and interaction must be understandable |
| Robust | Content must work reliably with different user agents and assistive technologies |

### Perceivable

Perceivable content can be accessed through appropriate sensory channels.

Examples include:

- text alternatives for meaningful images
- captions for relevant video
- sufficient contrast
- alternatives to color-only communication

### Operable

Operable interfaces can be controlled.

Examples include:

- keyboard accessibility
- visible focus
- logical focus order
- appropriate timing
- avoidance of inaccessible interaction patterns

### Understandable

Understandable content and controls behave predictably and communicate their purpose.

Examples include:

- clear labels
- understandable instructions
- consistent navigation
- useful validation errors

### Robust

Robust content can be interpreted by browsers and assistive technologies.

Semantic HTML is one of the strongest foundations for robustness because browsers already understand the semantics and behavior of native elements.

## WCAG conformance levels

WCAG commonly defines three conformance levels:

- **A**
- **AA**
- **AAA**

Level A represents the basic level of conformance. Level AA adds additional requirements. Level AAA is a more demanding level.

An organization should determine the applicable requirements based on its legal, contractual, product, and organizational context rather than assuming that every project must implement every AAA criterion.

## Semantic HTML

Semantic HTML means choosing elements according to their meaning and intended behavior.

Examples include:

- `header`
- `nav`
- `main`
- `section`
- `article`
- `aside`
- `footer`
- `button`
- `a`
- `form`
- `label`
- `fieldset`
- `legend`
- `h1` through `h6`

Semantic HTML helps browsers expose meaningful information to assistive technology.

It also reduces the amount of custom JavaScript required for standard interactions.

## Native HTML is usually the first choice

A native HTML control already has established semantics and browser behavior.

For example, a button can be represented with:

    <button type="button">Save</button>

A generic element such as a `div` does not automatically become a button merely because it has a click handler.

A custom version may require:

- a role
- focus behavior
- keyboard interaction
- accessible naming
- state management
- disabled-state handling
- focus styling
- testing across assistive technologies

The native element therefore provides a much stronger baseline.

## Links versus buttons

Links and buttons have different meanings.

A link normally navigates to another location or resource.

A button normally performs an action.

A navigation link can be represented as:

    <a href="/profile">View profile</a>

An action can be represented as:

    <button type="button">Open settings</button>

Using the correct element helps provide appropriate keyboard and semantic behavior.

A common mistake is using an anchor with a placeholder URL to implement an application action. A native button is normally the better choice when the purpose is an action rather than navigation.

## Document structure

HTML structure should communicate the organization of the page.

A typical document may contain:

- a header
- primary navigation
- a main content region
- supporting content
- a footer

A meaningful structure allows users to understand the page without depending exclusively on visual positioning.

## Headings

Headings communicate document hierarchy.

A typical hierarchy might look like:

- H1: Course catalog
  - H2: Python courses
  - H2: SQL courses
    - H3: Beginner SQL
    - H3: Advanced SQL
  - H2: Contact

Heading levels should describe structure rather than visual font size.

CSS should normally control visual appearance. An H3 should not be selected merely because its default text size looks appropriate.

Headings are particularly useful to screen-reader users because many screen readers allow navigation directly between headings.

## Heading hierarchy

A heading should normally fit into the conceptual hierarchy of the surrounding content.

A jump from H2 directly to H4 may indicate a structural problem, although automated rules cannot determine the meaning of an entire document.

The Python script therefore treats heading-level jumps as a heuristic rather than as absolute proof of an accessibility failure.

The important principle is meaningful information architecture.

## Landmarks

Landmarks identify major regions of a page.

Common landmark elements include:

- `header`
- `nav`
- `main`
- `aside`
- `footer`

Landmarks can make large pages easier to navigate.

If a page contains multiple navigation regions, accessible names can distinguish them.

For example:

    <nav aria-label="Primary">
        ...
    </nav>

and:

    <nav aria-label="Footer">
        ...
    </nav>

The purpose of the label is to help users distinguish otherwise similar navigation regions.

## The main landmark

The `main` element identifies the dominant content of the page.

A page should normally have a clear main content region.

A skip link can point directly to it:

    <a href="#main-content">Skip to main content</a>

    <main id="main-content">
        ...
    </main>

This can save keyboard users from repeatedly moving through large navigation sections.

## Skip links

A skip link provides a shortcut past repeated content.

This is particularly useful when a page contains:

- large headers
- navigation menus
- repeated promotional regions
- other content that appears before the main page content

A skip link is a practical example of accessibility improving efficiency rather than merely satisfying a technical rule.

## Forms

Forms are one of the most important areas of HTML accessibility.

A form control should have an understandable accessible name.

A strong basic pattern is:

    <label for="email">Email address</label>
    <input id="email" type="email">

The `for` attribute references the `id` of the control.

## Why labels matter

Labels help users:

- understand the purpose of a control
- identify the control after entering information
- use assistive technology
- click or tap the associated label
- distinguish multiple fields

Placeholder text should not replace a proper label.

## Placeholder text

A weak pattern is:

    <input type="email" placeholder="Email address">

A better pattern is:

    <label for="email">Email address</label>
    <input id="email" type="email" placeholder="name@example.com">

The placeholder can provide an example while the label provides the persistent name.

Placeholder text can disappear when users begin entering information and may have insufficient visual contrast.

## Grouping controls

Related controls can be grouped with `fieldset` and `legend`.

For example:

    <fieldset>
        <legend>Preferred contact method</legend>

        <label>
            <input type="radio" name="contact" value="email">
            Email
        </label>

        <label>
            <input type="radio" name="contact" value="phone">
            Phone
        </label>
    </fieldset>

The legend provides the context for the group.

## Input types

HTML provides specialized input types such as:

- `email`
- `search`
- `tel`
- `url`
- `number`
- `date`

Using an appropriate input type gives browsers and user agents useful information.

It can also affect available controls and mobile input behavior.

## Autocomplete

Autocomplete attributes communicate input purpose.

Example:

    <label for="given-name">First name</label>
    <input
        id="given-name"
        name="given-name"
        autocomplete="given-name">

Other examples include:

- `email`
- `username`
- `current-password`
- `new-password`
- `postal-code`

Correct autocomplete metadata can reduce unnecessary typing and support users with cognitive or motor difficulties.

## Form validation

Accessible validation should identify:

1. which field has a problem
2. what is wrong
3. how to correct it

A useful pattern associates an error message with the control.

For example:

    <label for="email">Email address</label>

    <input
        id="email"
        type="email"
        aria-invalid="true"
        aria-describedby="email-error">

    <p id="email-error" role="alert">
        Enter a valid email address.
    </p>

The visual presentation of the error should not be the only mechanism communicating the problem.

## Error summaries

For forms containing several errors, an error summary can provide a useful starting point.

A summary can contain links to invalid fields.

The individual controls should still communicate their own errors.

A useful error experience therefore provides both:

- an overview of the problems
- field-specific correction information

## Required fields

HTML provides native required semantics:

    <input id="email" type="email" required>

The interface should also make the required nature of the field understandable to users.

Required state should not be communicated solely through color.

## Keyboard accessibility

Keyboard accessibility means that functionality can be operated without a mouse.

Important keyboard interactions commonly include:

- Tab
- Shift+Tab
- Enter
- Space
- Arrow keys
- Escape

The exact behavior depends on the control.

Native buttons and links already provide much of the expected behavior.

## Keyboard focus

Focus identifies the element currently receiving keyboard interaction.

A logical focus sequence helps users understand the interface.

A typical sequence might be:

1. skip link
2. navigation
3. search
4. main content controls
5. footer navigation

The exact sequence depends on the page.

## Visible focus

Keyboard users need to know where focus is located.

A common CSS pattern is:

    button:focus-visible,
    a:focus-visible,
    input:focus-visible {
        outline: 3px solid currentColor;
        outline-offset: 3px;
    }

Removing the browser focus indicator without providing an equivalent visible indicator can make an interface difficult to operate.

## tabindex

`tabindex` controls focus behavior.

Important values include:

- no `tabindex`: native behavior
- `tabindex="0"`: includes an otherwise focusable custom element in normal sequential navigation
- `tabindex="-1"`: removes the element from sequential Tab navigation while allowing programmatic focus
- positive values: create a custom sequential focus order and are generally discouraged

Positive tabindex values can cause focus order to become difficult to understand and maintain.

## Focus management

Dynamic interfaces frequently need deliberate focus management.

A dialog is a typical example.

When a modal dialog opens:

1. focus should move into the dialog
2. keyboard interaction should remain within the modal while it is modal
3. Escape or another defined mechanism can close it
4. focus should return to a sensible element after closing

A common restoration target is the control that opened the dialog.

## Focus traps

A focus trap can be appropriate for a genuinely modal interface.

It becomes problematic when applied to ordinary page content because users may become unable to reach other controls.

A modal focus-management implementation needs to consider:

- first focus
- last focus
- Tab
- Shift+Tab
- Escape
- closing behavior
- focus restoration

## Images

Images should be classified according to purpose.

### Informative image

An informative image needs alternative text that communicates its meaningful information.

Example:

    <img
        src="sales-chart.png"
        alt="Sales increased from 2024 to 2025.">

### Decorative image

A decorative image can often use an empty alternative:

    <img src="decorative-line.svg" alt="">

This communicates that the image does not add meaningful information.

### Functional image

If an image is part of a control, the accessible name should communicate the control's purpose.

For example:

    <button type="button">
        <img src="search.svg" alt="Search">
    </button>

The correct approach depends on the complete context.

## Alternative text

Alternative text should communicate purpose rather than blindly describing every visible detail.

For example, a photograph used as an article header may need a different alternative from the same photograph used as a button.

The appropriate alternative depends on why the image exists.

## SVG accessibility

Decorative SVGs can often be hidden from assistive technology:

    <svg aria-hidden="true" focusable="false">
        ...
    </svg>

An informative SVG may instead need an accessible name.

Example:

    <svg role="img" aria-labelledby="chart-title">
        <title id="chart-title">
            Revenue increased by 15 percent.
        </title>
    </svg>

## Color

Color should not be the only mechanism used to communicate meaning.

A form error should not be communicated only through a red border.

A status should not be communicated only through green or red.

Useful additional mechanisms include:

- text
- labels
- icons
- patterns
- symbols
- explicit state information

## Contrast

WCAG includes requirements related to contrast.

The Python script implements a relative-luminance and contrast-ratio calculation to demonstrate the mathematical basis of contrast checking.

The calculation uses the relationship between two luminance values:

contrast ratio = (lighter luminance + 0.05) / (darker luminance + 0.05)

The resulting ratio is commonly expressed as a value such as 4.5:1 or 7:1.

The required ratio depends on the applicable WCAG criterion and content characteristics.

Contrast alone is not a complete accessibility test.

## ARIA

ARIA stands for **Accessible Rich Internet Applications**.

ARIA can communicate:

- roles
- states
- properties
- relationships

Examples include:

- `aria-expanded`
- `aria-pressed`
- `aria-checked`
- `aria-selected`
- `aria-current`
- `aria-disabled`
- `aria-invalid`
- `aria-describedby`
- `aria-labelledby`
- `aria-controls`

## The first rule of ARIA

A central principle is to prefer native HTML when it already provides the required semantics and behavior.

For example:

    <button type="button">Save</button>

is preferable to:

    <div role="button" tabindex="0">Save</div>

unless there is a genuine reason for a custom implementation.

ARIA does not automatically add all required interaction behavior.

## ARIA does not create behavior

Adding:

    role="button"

does not automatically implement all button behavior.

A custom button may require:

- keyboard handling
- focus handling
- visible focus
- disabled behavior
- accessible naming
- state synchronization

Native controls already provide these browser-level behaviors.

## Accessible names

An accessible name is the name exposed to assistive technology for an interface object.

Common sources include:

- visible text
- associated labels
- `aria-label`
- `aria-labelledby`

For example:

    <button>Save changes</button>

already has a clear name.

An icon-only button may need:

    <button aria-label="Close dialog">
        ...
    </button>

When possible, visible text should normally be preferred over an unnecessary `aria-label`.

## aria-labelledby

`aria-labelledby` can reference visible content that supplies an accessible name.

Example:

    <h2 id="dialog-title">Delete account</h2>

    <div role="dialog" aria-labelledby="dialog-title">
        ...
    </div>

This can preserve a relationship between the visible heading and the accessible name.

## aria-describedby

`aria-describedby` associates additional descriptive content with an element.

Example:

    <label for="account-number">Account number</label>

    <input
        id="account-number"
        aria-describedby="account-help">

    <p id="account-help">
        Enter the 10-digit account number shown on your statement.
    </p>

The description is supplementary information rather than the primary name.

## aria-expanded

`aria-expanded` communicates whether a control's associated content is expanded.

Example:

    <button
        type="button"
        aria-expanded="false"
        aria-controls="account-menu">
        Account
    </button>

The value should change when the state changes.

## aria-pressed

`aria-pressed` communicates the state of a toggle button.

Example:

    <button
        type="button"
        aria-pressed="false">
        Favorite
    </button>

After activation, the application should update the state:

    aria-pressed="true"

The visual and semantic states must remain synchronized.

## aria-selected

`aria-selected` is used in applicable composite widgets such as tabs.

It should not be added indiscriminately to ordinary buttons or navigation links.

## aria-current

`aria-current` identifies the current item in a set.

For example:

    <a href="/courses" aria-current="page">Courses</a>

This is useful in navigation because users can identify which page is currently active.

## aria-controls

`aria-controls` identifies content affected by a control.

For example:

    <button
        aria-expanded="false"
        aria-controls="filters">
        Filters
    </button>

The referenced ID should correspond to an actual related element.

## aria-invalid

`aria-invalid="true"` communicates that an input currently contains an invalid value.

It is most useful when combined with an understandable error message and an appropriate description relationship.

## aria-disabled

`aria-disabled="true"` communicates that a control is disabled or unavailable.

It is not a security mechanism.

A server must never rely on an ARIA attribute to enforce authorization or permissions.

## aria-hidden

`aria-hidden="true"` requests that content be excluded from the accessibility tree.

It is commonly useful for decorative icons.

It should not be placed on content that users need to access through assistive technology.

It should also not be applied to a focusable control because that can create a mismatch where the keyboard can focus something that is not represented to assistive technology.

## Live regions

Dynamic content can change without a traditional page navigation.

ARIA live regions can communicate relevant changes.

A status message can use:

    <div role="status" aria-live="polite">
        3 results found.
    </div>

An important alert can use:

    <div role="alert">
        Payment failed.
    </div>

Announcements should be used carefully.

Too many announcements can interrupt users and make an interface difficult to navigate.

## Status versus alert

A status message generally communicates information without demanding immediate interruption.

An alert is intended for information requiring more immediate attention.

Examples:

Status:

    Your profile has been saved.

Alert:

    Your payment could not be processed.

The distinction helps avoid unnecessary interruption.

## Hidden content

Different hiding mechanisms have different accessibility consequences.

Examples include:

- `display: none`
- `hidden`
- `visibility: hidden`
- `aria-hidden="true"`

They should not be treated as interchangeable.

In particular, `aria-hidden` changes accessibility-tree exposure rather than simply changing visual appearance.

## Semantic navigation

A normal website navigation structure can be represented using `nav`, links, and lists.

Example:

    <nav aria-label="Primary">
        <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/products">Products</a></li>
            <li><a href="/support">Support</a></li>
        </ul>
    </nav>

Not every navigation interface should use the ARIA `menu` pattern.

## Navigation menu versus ARIA menu

A standard website navigation area is not automatically an ARIA menu.

The ARIA menu pattern represents a more specialized application-style widget with specific keyboard behavior.

Using ARIA menu semantics for ordinary website navigation can introduce unnecessary complexity and unexpected interaction behavior.

## Tabs

Tabs are a composite widget.

A complete tab implementation generally requires:

- a tablist
- tabs
- tab panels
- selection state
- relationships
- keyboard interaction
- focus behavior
- visibility management

A tab cannot be made fully accessible by adding only:

    role="tab"

The implementation must also behave like a tab interface.

## Disclosure widgets

A disclosure pattern exposes and hides related content.

A native button can provide a strong foundation:

    <button
        type="button"
        aria-expanded="false"
        aria-controls="details">
        Show details
    </button>

The state should become `true` when the content is expanded.

The controlled content must also be hidden or shown consistently with the state.

## Dialogs

Dialogs need:

- an accessible name
- optional description
- appropriate role or native dialog semantics
- correct focus placement
- keyboard operation
- appropriate modal behavior when applicable
- focus restoration

A useful structure may include:

    <dialog
        aria-labelledby="dialog-title"
        aria-describedby="dialog-description">

        <h2 id="dialog-title">Delete account</h2>

        <p id="dialog-description">
            This action permanently removes your account.
        </p>

        <button type="button">Cancel</button>
        <button type="button">Delete account</button>
    </dialog>

## Tables

Tables should be used for actual tabular relationships rather than layout.

An accessible data table can include:

- `caption`
- `thead`
- `tbody`
- `th`
- `td`
- `scope`

Example structure:

    <table>
        <caption>Quarterly revenue by region</caption>
        <thead>
            <tr>
                <th scope="col">Region</th>
                <th scope="col">Q1</th>
                <th scope="col">Q2</th>
            </tr>
        </thead>
        <tbody>
            ...
        </tbody>
    </table>

## Language

The document language should be declared.

Example:

    <html lang="en">

If part of a document uses another language, the change can be identified:

    <span lang="fr">Bonjour</span>

Language metadata helps assistive technology use appropriate pronunciation and language-specific behavior.

## Text direction

Language and writing direction can also matter.

For right-to-left content:

    <html lang="ar" dir="rtl">

Direction should reflect the actual content rather than simply the visual design.

## Page title

Every page should have a meaningful document title.

Example:

    <title>Course catalog | Example University</title>

The title can help users identify pages among browser tabs, history, and assistive-technology navigation.

## Media accessibility

Relevant video should provide captions.

Example:

    <video controls>
        <source src="lecture.mp4" type="video/mp4">
        <track
            kind="captions"
            src="lecture-en.vtt"
            srclang="en"
            label="English">
    </video>

Captions communicate spoken dialogue and relevant audio information.

Transcripts provide an additional text representation of audio or video.

## Motion

Some users can experience discomfort or other problems from animation and motion.

CSS can respond to a user's reduced-motion preference:

    @media (prefers-reduced-motion: reduce) {
        ...
    }

Motion should be purposeful and should not make content difficult to read or operate.

## Responsive accessibility

Accessibility applies to mobile and responsive interfaces as well as desktop websites.

Important considerations include:

- text resizing
- zoom
- reflow
- orientation
- touch interaction
- screen-reader interaction
- keyboard input where available
- responsive focus management

A responsive layout should not destroy logical reading order or make controls unreachable.

## Source order

Visual order and DOM order can diverge through CSS.

A page should normally maintain a logical source order because keyboard users and assistive technologies can encounter content according to the underlying structure.

Source order should generally correspond to the intended reading and interaction sequence.

## Single-page applications

Single-page applications introduce additional accessibility responsibilities because route changes may happen without a traditional browser page load.

Important considerations include:

- updating `document.title`
- providing a clear page heading
- managing focus after navigation
- preserving browser history
- communicating important asynchronous updates
- ensuring old controls do not retain inappropriate focus

A visual route change does not automatically provide an equivalent navigation experience for screen-reader or keyboard users.

## Dynamic content

Dynamic updates should be communicated without unnecessarily stealing focus.

For example, a search result count can be represented using a status region:

    <p role="status">
        12 courses found.
    </p>

Moving focus every time data changes can be disruptive.

Focus should normally move only when the user's task requires it.

## Infinite scrolling

Infinite scrolling can create challenges involving:

- context
- document position
- dynamic announcements
- focus
- keyboard navigation
- content discoverability

When infinite scrolling is used, the implementation should ensure that newly inserted content does not unexpectedly disrupt the user's location or interaction.

## Drag and drop

Drag-and-drop should not be the only way to perform an important operation.

An alternative can use ordinary controls:

    <button type="button">Move item up</button>
    <button type="button">Move item down</button>

This allows users who cannot perform precise dragging to complete the same task.

## Tooltips

Essential information should not exist only inside hover-based tooltips.

Hover interactions can exclude:

- keyboard users
- touch users
- users with certain motor limitations

Persistent explanatory text associated with the relevant control is often more robust.

## Custom widgets

When a native element cannot satisfy a legitimate product requirement, a custom widget may be necessary.

A custom component should have a defined accessibility contract covering:

- role
- accessible name
- state
- properties
- keyboard behavior
- pointer behavior
- focus management
- visible focus
- disabled behavior
- dynamic announcements
- relationships
- responsive behavior

Custom widgets therefore require significantly more testing than simple native controls.

## Accessible component contracts

A component specification should define accessibility behavior before implementation.

For a disclosure component, a contract might state:

- role: button
- accessible name: visible button text
- keyboard behavior: native button interaction
- state: `aria-expanded`
- relationship: `aria-controls`

This approach makes accessibility a component requirement rather than an afterthought.

## Design systems

A design system should define accessibility behavior for reusable components such as:

- buttons
- links
- inputs
- selects
- checkboxes
- radio groups
- dialogs
- disclosures
- tabs
- alerts
- status messages
- tooltips
- navigation

Reusable accessibility behavior reduces the likelihood of different teams implementing the same component inconsistently.

## Progressive enhancement

Progressive enhancement begins with a robust HTML foundation and then adds richer behavior.

For example:

    <form action="/search" method="get">
        <label for="query">Search</label>
        <input id="query" name="q" type="search">
        <button type="submit">Search</button>
    </form>

JavaScript can enhance this experience with asynchronous search while the basic semantic structure remains understandable.

This approach improves resilience.

## Security and accessibility

Accessibility attributes are not security mechanisms.

For example:

    <button aria-disabled="true">Submit</button>

The attribute communicates an accessibility state, but it does not provide authorization or server-side enforcement.

Security controls must remain enforced by appropriate application and server-side mechanisms.

Accessibility and security also intersect in authentication, error messages, sensitive announcements, and alternative interaction mechanisms.

## Accessibility and performance

Performance affects accessibility.

Slow applications can increase the burden on users who:

- use older hardware
- use slower connections
- rely on assistive technologies
- have cognitive disabilities
- require additional time for interaction

Performance-aware accessibility includes:

- meaningful loading states
- stable focus
- limited unnecessary DOM complexity
- efficient asynchronous updates
- avoiding excessive live-region announcements

## Accessibility testing

No single testing method is sufficient.

The script demonstrates a layered approach.

### Automated testing

Automated checks can detect problems such as:

- missing alternative text attributes
- missing document language
- missing page titles
- some naming problems
- problematic tabindex values
- some ARIA errors

Automation is useful but incomplete.

### Keyboard testing

Keyboard testing should verify:

- all controls are reachable
- focus order is logical
- focus is visible
- buttons work with expected keyboard input
- dialogs can be entered and exited
- menus and composite widgets behave correctly
- no unintended focus traps exist

### Screen-reader testing

Screen-reader testing should consider:

- headings
- landmarks
- links
- buttons
- accessible names
- states
- descriptions
- form errors
- dynamic updates
- reading order
- dialog behavior

### Zoom and reflow testing

Users may enlarge content substantially.

The interface should remain usable without unnecessary:

- horizontal scrolling
- clipped content
- overlapping controls
- inaccessible menus

### Human testing

Automated rules cannot determine every usability problem.

Human testing can reveal:

- confusing labels
- poor interaction models
- unexpected focus behavior
- unclear instructions
- excessive announcements
- difficult workflows

People with disabilities can provide especially valuable evidence about practical accessibility.

## Automated versus manual testing

Some checks are well suited to automation.

Examples include:

- presence of an `alt` attribute
- existence of an HTML language attribute
- basic color contrast calculations
- some ARIA validation
- some form-label relationships

Other issues require human evaluation.

Examples include:

- whether the alternative text is actually appropriate
- whether keyboard interaction is intuitive
- whether the heading structure represents the intended information architecture
- whether instructions are understandable
- whether a dynamic interaction creates confusion

Automated testing should therefore be treated as one layer of an accessibility strategy rather than as proof of complete accessibility.

## The educational Python linter

The script contains an `AccessibilityLinter` class.

It demonstrates checks for:

- missing image `alt` attributes
- unnamed buttons
- unnamed links
- missing document language
- missing page titles
- potentially unlabeled inputs
- positive tabindex
- focusable elements marked `aria-hidden`

The linter is intentionally limited.

It uses regular expressions for educational purposes and is not a complete HTML parser or WCAG conformance engine.

Real accessibility analysis requires consideration of DOM structure, computed accessibility information, browser behavior, CSS, JavaScript, content, and user interaction.

## Accessible name calculation

The script also includes a simplified function demonstrating how an accessible name may be reasoned about.

It considers examples such as:

- `aria-label`
- `aria-labelledby`
- text content

The actual accessible-name computation is considerably more detailed and includes element-specific rules and precedence.

The simplified implementation should therefore be understood as a teaching model rather than a standards-complete implementation.

## Accessibility tree

The DOM and accessibility tree are related but are not identical.

The DOM represents the document structure.

The accessibility tree provides information needed by accessibility services.

Factors affecting accessibility-tree representation can include:

- semantic HTML
- ARIA
- CSS visibility
- hidden state
- accessible names
- element state
- browser behavior

This explains why a visually present element can sometimes be absent from assistive-technology output.

## Accessible relationships

Important relationships include:

| Relationship | Purpose |
|---|---|
| `for` to `id` | Associates a form label with its control |
| `aria-labelledby` | References content used for an accessible name |
| `aria-describedby` | References supplementary descriptive content |
| `aria-controls` | Identifies content affected by a control |
| `aria-owns` | Can express ownership relationships when appropriate |

Ordinary DOM structure should generally be preferred over ARIA relationships when it already communicates the required relationship.

## Disabled states

Native disabled behavior and `aria-disabled` are not identical.

Native:

    <button disabled>Submit</button>

The browser provides built-in disabled behavior.

ARIA:

    <div
        role="button"
        tabindex="0"
        aria-disabled="true">
        Submit
    </div>

The second example communicates state but does not automatically reproduce every native disabled behavior.

Application logic must enforce the intended interaction.

## Current navigation

`aria-current` can identify the active page.

Example:

    <nav aria-label="Primary">
        <a href="/">Home</a>
        <a href="/courses" aria-current="page">Courses</a>
        <a href="/contact">Contact</a>
    </nav>

This is particularly useful when users navigate through links independently of surrounding visual context.

## Meaningful link text

Weak link text:

    <a href="/report">Click here</a>

More meaningful:

    <a href="/report">
        Download the annual accessibility report
    </a>

Meaningful link text is especially important because screen-reader users can navigate through a list of links without necessarily hearing the surrounding paragraph.

## Lists

Lists should represent actual lists.

An unordered list is appropriate when sequence does not matter:

    <ul>
        <li>Home</li>
        <li>Courses</li>
        <li>Contact</li>
    </ul>

An ordered list is appropriate when sequence matters:

    <ol>
        <li>Create an account.</li>
        <li>Verify your email.</li>
        <li>Submit the application.</li>
    </ol>

Semantic list structure gives assistive technology useful grouping information.

## Embedded content

An iframe should have a meaningful title when users need to understand its purpose.

Example:

    <iframe
        title="University campus map"
        src="/campus-map">
    </iframe>

The title gives users useful context before they interact with the embedded browsing context.

## Canvas

Canvas is a drawing surface rather than a semantic document.

Interactive canvas applications therefore require careful accessibility design.

A canvas-based interface should not assume that visual pixels alone provide enough information to assistive technology.

An equivalent semantic interaction model may be necessary.

## Common mistakes

Common accessibility mistakes include:

### Using div elements as buttons

Prefer:

    <button type="button">Save</button>

### Using placeholders as labels

Provide an actual label.

### Removing focus indicators

Maintain visible focus.

### Using color alone

Provide redundant text or other cues.

### Adding ARIA everywhere

Prefer native HTML semantics.

### Hiding focusable elements with aria-hidden

Do not create a mismatch between keyboard focus and accessibility-tree exposure.

### Using positive tabindex

Prefer natural document order.

### Using hover-only interactions

Provide keyboard and touch equivalents.

### Ignoring route-change focus

Manage focus intentionally in dynamic applications.

### Treating automated testing as proof

Combine automation with manual testing.

## Edge cases

Accessibility often involves contextual decisions.

### Icon-only buttons

An icon-only button needs an accessible name.

### Decorative icons

Decorative icons should generally not create unnecessary screen-reader output.

### Clickable cards

A large generic container should not be made into a complex custom control when a semantic link or button can express the actual action.

### Multiple navigation regions

Distinguish multiple navigation landmarks when necessary.

### Dynamic validation

Do not move focus unexpectedly for every minor validation update.

### Repeated headings

Repeated heading text is not automatically an accessibility failure. Context determines whether users can understand the structure.

## Accessibility and design trade-offs

Accessibility involves real implementation trade-offs.

Custom components can provide specialized interaction but require more testing.

Animations can communicate information but can create motion problems.

Live announcements can communicate dynamic changes but can become disruptive when overused.

Client-side routing can provide fast transitions but requires deliberate focus and title management.

Visual simplification can reduce clutter but should not remove information users need to understand an interface.

The correct decision depends on the user's task and the complete interaction model.

## Accessibility acceptance criteria

Accessibility can be incorporated into normal acceptance criteria.

Useful criteria include:

- every interactive control has an accessible name
- all functionality is keyboard operable
- focus is visible
- focus order is logical
- dialogs manage focus correctly
- form controls have appropriate labels
- errors are understandable
- meaningful images have suitable alternatives
- headings and landmarks form a meaningful structure
- dynamic states are exposed correctly
- color is not the only communication mechanism
- content remains usable when enlarged

## Accessibility code review

A code review can inspect several layers.

### HTML

Check whether semantic elements are used appropriately.

### Navigation

Check landmarks, links, current state, and skip navigation.

### Forms

Check labels, instructions, required states, and errors.

### Keyboard

Check that all interactions are possible without a mouse.

### Focus

Check visibility and dynamic focus management.

### ARIA

Check whether ARIA is necessary and whether states remain synchronized.

### Images

Check whether alternatives match the purpose of each image.

### Dynamic updates

Check whether important updates are communicated without unnecessary focus changes.

## Accessibility regression testing

Accessibility can regress during ordinary development.

Examples include:

- replacing a button with a generic element
- removing a focus outline during CSS refactoring
- changing a label ID
- breaking an ARIA relationship
- changing route handling
- introducing a new custom widget
- changing the DOM order
- changing visible text without updating accessible naming

Accessibility should therefore be part of normal regression testing.

## Production workflow

A practical production workflow includes:

1. Define accessibility requirements during discovery.
2. Use semantic HTML during implementation.
3. Design keyboard and focus behavior.
4. Define accessible names and states.
5. Implement form validation accessibly.
6. Run automated checks.
7. Test keyboard operation.
8. Test screen-reader behavior.
9. Test zoom, responsive layouts, and relevant user preferences.
10. Record accessibility defects with reproducible steps.
11. Fix regressions during normal development.
12. Include accessibility in release criteria.

## The end-to-end example

The Python script includes a complete example of an accessible course-search page.

The page demonstrates:

- document language
- metadata
- viewport configuration
- meaningful page title
- skip navigation
- semantic navigation
- current-page state
- main landmark
- heading hierarchy
- labeled search field
- native form controls
- status communication
- article semantics
- meaningful links
- footer structure

The example demonstrates how individual accessibility techniques combine into a complete page rather than existing as isolated rules.

## Practical accessibility checklist

### Structure

- [ ] Document language is declared
- [ ] Page title is meaningful
- [ ] Headings form a logical hierarchy
- [ ] Semantic landmarks identify major regions
- [ ] Source order is logical

### Navigation

- [ ] Keyboard navigation works
- [ ] Focus is visible
- [ ] Skip navigation is available when appropriate
- [ ] Current navigation state is communicated
- [ ] No unintended focus trap exists

### Forms

- [ ] Controls have accessible labels
- [ ] Instructions are available when needed
- [ ] Required states are understandable
- [ ] Errors are clearly identified
- [ ] Errors are associated with affected controls

### Images and media

- [ ] Meaningful images have suitable alternatives
- [ ] Decorative images do not create unnecessary output
- [ ] Relevant video has captions
- [ ] Audio and video have appropriate text alternatives

### ARIA

- [ ] Native HTML was considered first
- [ ] Roles are appropriate
- [ ] States remain synchronized
- [ ] Relationships reference the correct elements
- [ ] Focusable content is not incorrectly hidden from assistive technology

### Responsive behavior

- [ ] Content remains usable when enlarged
- [ ] Important information does not depend only on hover
- [ ] Touch interaction is usable
- [ ] Keyboard interaction remains usable
- [ ] Motion preferences are respected where applicable

### Testing

- [ ] Automated checks have been performed
- [ ] Keyboard testing has been performed
- [ ] Screen-reader testing has been performed
- [ ] Real workflows have been tested
- [ ] Accessibility regressions are covered by testing

## Important distinction: compliance versus usability

Technical conformance and practical accessibility are related but not identical.

A page can satisfy some automated rules while still being confusing.

For example, a button might technically have an accessible name but still use a vague label such as "Continue" when several different actions are possible.

A page can also have technically valid headings while presenting an information hierarchy that is difficult to understand.

Accessibility therefore requires both technical correctness and meaningful user experience.

## Implementation considerations

The most reliable implementation principles are:

- prefer native HTML
- preserve logical document structure
- keep source order meaningful
- make keyboard interaction explicit
- maintain visible focus
- manage focus during dynamic changes
- give controls meaningful names
- synchronize visual and semantic states
- use ARIA only when necessary
- keep form errors understandable
- avoid relying on color alone
- test real workflows

These practices reduce both accessibility defects and unnecessary implementation complexity.
