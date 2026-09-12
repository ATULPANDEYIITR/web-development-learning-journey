# Semantic HTML multi-page portfolio

## Project introduction

This project demonstrates how semantic HTML can be used to build a complete multi-page portfolio website.

The website contains four independent HTML documents:

- `index.html` for the portfolio home page
- `about.html` for professional background and experience
- `projects.html` for detailed project information
- `contact.html` for professional contact and a form

The Python script generates these pages from structured portfolio data and places the shared stylesheet in an `assets` directory.

The project is intentionally centered on HTML structure and meaning. CSS provides presentation, while the HTML remains responsible for document structure, navigation, content relationships, forms, accessibility landmarks, and machine-readable information.

The generated architecture is:

    semantic_portfolio_site/
    ├── index.html
    ├── about.html
    ├── projects.html
    ├── contact.html
    └── assets/
        └── styles.css

The Python script can be executed without external packages.

## What semantic HTML means

Semantic HTML uses elements according to the meaning and role of their content.

For example, a page header should use `header`, primary navigation should use `nav`, the principal content should use `main`, independent content can use `article`, thematic groups can use `section`, complementary information can use `aside`, and footer information can use `footer`.

Semantic HTML is different from simply placing meaningful class names on generic elements.

A structure such as:

    <div class="header">
        ...
    </div>

communicates meaning primarily through the class name to developers.

A structure such as:

    <header>
        ...
    </header>

uses an HTML element whose purpose is already defined by the HTML specification.

Semantic structure gives browsers, assistive technologies, search systems, developers, and other consumers of the document a clearer representation of the content.

This does not mean that `div` is inherently incorrect. A `div` is appropriate when no more specific semantic element represents the content.

## Basic HTML document structure

The generated pages use the HTML5 document structure:

    <!doctype html>
    <html lang="en">
        <head>
            ...
        </head>
        <body>
            ...
        </body>
    </html>

The `doctype` tells the browser to use standards-oriented HTML parsing and rendering behavior.

The `html` element is the root of the document.

The `lang` attribute identifies the primary language of the page. This assists accessibility technologies and other software that needs to determine language.

The `head` contains metadata and document configuration rather than the primary visible content.

The `body` contains the document content presented to the user.

## Metadata

The generated pages contain several important metadata elements.

### Character encoding

The document declares UTF-8:

    <meta charset="utf-8">

UTF-8 supports a very broad range of characters and is the normal character encoding choice for modern HTML documents.

### Responsive viewport

The pages contain:

    <meta name="viewport" content="width=device-width, initial-scale=1">

This allows the page layout to respond appropriately to the device viewport, particularly on mobile devices.

Without an appropriate viewport declaration, mobile browsers may use a virtual layout viewport that produces unexpected scaling behavior.

### Page title

Each page has a distinct `title`.

The title is important for browser tabs, bookmarks, history, accessibility contexts, and search-result presentation.

A multi-page portfolio should not use exactly the same title for every page.

The generated project uses titles based on the current page and portfolio identity.

### Meta description

Each page also contains a description describing its content.

A description should accurately represent the page instead of being a collection of unrelated keywords.

### Canonical URL

The generated pages demonstrate a canonical link.

Canonical metadata can help identify the preferred URL representation when equivalent or duplicate URLs exist.

A production deployment should replace example paths with the actual deployed canonical URLs.

## Semantic page landmarks

The portfolio uses several important semantic regions.

### Header

`header` represents introductory or navigational content for a page or section.

At the document level, the portfolio header contains the site identity and primary navigation.

A header does not necessarily mean the topmost visual element on every page. It represents the appropriate introductory content for its surrounding context.

### Nav

`nav` identifies a major navigation block.

The portfolio has a primary navigation region containing links to:

- Home
- About
- Projects
- Contact

It also contains a footer navigation region.

The `aria-label` attribute distinguishes navigation landmarks when a page contains more than one navigation region.

### Main

`main` represents the primary content of the document.

Each generated page contains exactly one main element.

This provides a clear landmark for users of assistive technologies and establishes which content represents the principal purpose of the page.

### Section

`section` represents a thematic grouping of content.

The generated home page uses sections for areas such as featured projects and skills.

A meaningful section normally has a heading that identifies its subject.

A section should not be used merely because a visual box or spacing region is required. A generic container may be more appropriate when there is no semantic grouping.

### Article

`article` represents self-contained content that can make sense independently.

Portfolio projects are suitable examples because each project has its own title, description, technologies, and destination.

The projects page therefore uses an article for each project.

### Aside

`aside` represents content related to the surrounding content but not part of its primary flow.

The portfolio uses aside elements for complementary information such as a professional snapshot and direct contact details.

An aside should not simply mean "a box on the right side." Its semantic purpose is complementary content.

### Footer

`footer` represents footer information for its nearest sectioning context.

At the document level, the portfolio footer contains copyright information and secondary navigation.

A footer can also exist inside an article or section when the footer belongs to that particular content block.

## Heading hierarchy

HTML provides six heading levels:

- `h1`
- `h2`
- `h3`
- `h4`
- `h5`
- `h6`

The levels communicate hierarchy rather than visual size.

A typical portfolio page can follow a structure such as:

    h1
      h2
        h3
      h2
        h3

The `h1` represents the primary subject of the page.

`h2` identifies major subdivisions.

`h3` identifies subdivisions within an `h2` region.

The generated Python validator checks for an appropriate heading structure and reports suspicious jumps.

For example, moving directly from `h1` to `h4` can indicate that heading levels were selected for appearance rather than document hierarchy.

CSS should be used to control visual size.

## Links and navigation

The anchor element creates hyperlinks:

    <a href="projects.html">Projects</a>

The `href` attribute specifies the destination.

The multi-page portfolio uses ordinary relative links between documents.

This is different from a JavaScript-driven single-page application where one document may dynamically replace sections of the interface.

The multi-page approach has several practical advantages:

- Each page has its own URL.
- Each page can have independent metadata.
- Navigation can work without JavaScript.
- Browser history works naturally.
- Individual pages can be bookmarked directly.
- The architecture is easy to understand for beginners.
- Static hosting is sufficient for the basic website.

The trade-off is that navigating between pages normally loads another HTML document.

## Current-page indication

The navigation marks the current page using:

    aria-current="page"

This communicates state programmatically instead of relying exclusively on visual styling.

For example, the Projects navigation item can identify itself as the current page.

Visual styling can still be applied, but semantic state should not depend entirely on color, font weight, or another visual distinction.

## Lists

The portfolio uses unordered lists for collections where order is not inherently meaningful.

Examples include:

- Skills
- Technologies used by projects
- Navigation items
- Project achievements

An unordered list uses `ul`, with each item represented by `li`.

An ordered list uses `ol` when sequence or ranking is meaningful.

The choice should be based on content meaning rather than default browser appearance.

## Article versus section

These elements are related but not interchangeable.

An `article` represents independent, self-contained content.

A `section` represents a thematic grouping.

For the portfolio:

    <section>
        <h2>Featured projects</h2>

        <article>
            <h3>Advanced Calculator</h3>
            ...
        </article>

        <article>
            <h3>Market Analytics Dashboard</h3>
            ...
        </article>
    </section>

The section groups the projects under a common theme.

Each article represents an individual project.

A project could therefore be moved or reused elsewhere without losing its basic identity.

## Button versus link

A link and a button have different semantic responsibilities.

A link navigates to another resource or location.

A button performs an action.

Examples of links:

    <a href="projects.html">Projects</a>

    <a href="https://example.com">External project</a>

Examples of buttons:

    <button type="submit">Send message</button>

Using a button for ordinary navigation or a link for an action can create confusing semantics and accessibility behavior.

The portfolio follows the distinction by using links for page navigation and a button for form submission.

## Images and alternative text

The HTML `img` element represents an image.

Meaningful images require useful alternative text through the `alt` attribute.

Example:

    <img src="profile.jpg" alt="Professional profile photograph">

The alternative text should communicate the relevant meaning of the image.

A decorative image that does not add information can use an empty alternative text value:

    alt=""

This allows assistive technology to ignore the image when appropriate.

The generated validator checks for missing `alt` attributes.

Alternative text should not be treated as a place to insert large keyword lists or unrelated descriptions.

## Forms

The contact page demonstrates a semantic HTML form.

The main elements are:

- `form`
- `label`
- `input`
- `textarea`
- `button`

The form contains fields for:

- Name
- Email address
- Subject
- Message

A form control should have an accessible name.

The generated form connects labels and controls through matching `for` and `id` attributes.

For example:

    <label for="email">Email address</label>

    <input id="email" name="email" type="email">

The label identifies the purpose of the control.

The `name` attribute identifies the field when form data is submitted.

The `type="email"` provides browser-level information about the expected data.

The `required` attribute expresses a client-side requirement.

## Client-side validation versus security

HTML validation is useful for usability but is not a security boundary.

Attributes such as:

- `required`
- `type="email"`
- `min`
- `max`
- `pattern`

can help users provide valid data.

A malicious or modified client can bypass browser validation.

If the contact form is connected to a backend, the server must independently validate incoming data.

The server should also apply appropriate authorization, rate limiting, input handling, logging, and output encoding according to the application requirements.

## Autocomplete

The contact form uses appropriate autocomplete values.

Examples include:

    autocomplete="name"

and:

    autocomplete="email"

These values help browsers and password or form-management systems understand the purpose of fields.

Correct autocomplete values can improve usability, especially on mobile devices.

## Address element

The contact page uses `address` for contact information associated with the portfolio.

`address` is not a generic substitute for every physical address.

It represents contact information for the relevant document or article.

## Time element

The experience and project pages use `time`.

For example, a project year can be represented as temporal information.

The element can optionally contain a `datetime` attribute that provides machine-readable information.

This distinction allows human-readable content and machine-readable representation to coexist.

## Accessibility

Semantic HTML is an important foundation for accessibility.

The project demonstrates several accessibility practices.

### Language declaration

The `lang` attribute identifies the document language.

### Landmark structure

The use of `header`, `nav`, `main`, `section`, `article`, `aside`, and `footer` provides meaningful document regions.

### Heading hierarchy

Correct heading levels help users understand relationships between sections.

### Form labels

Every contact field has an associated visible label.

### Keyboard focus

The stylesheet provides visible focus indicators for links, buttons, and form controls.

Removing visible focus indicators can make keyboard navigation difficult.

### Reduced motion

The stylesheet respects the `prefers-reduced-motion` media feature.

This avoids forcing smooth scrolling behavior on users who have requested reduced motion.

### Color independence

Important information should not depend only on color.

For example, the current navigation state is represented semantically using `aria-current`, not only by a different color.

### Link descriptions

Links should communicate their destination or purpose.

Generic text such as "click here" provides less useful information than descriptive link text.

## Semantic HTML and CSS

HTML and CSS have different responsibilities.

HTML should represent:

- Structure
- Meaning
- Relationships
- Content
- Navigation
- Forms

CSS should represent:

- Color
- Spacing
- Typography
- Layout
- Borders
- Visual states
- Responsive presentation

A heading should remain a heading because of its semantic role, even if CSS changes its visual size.

This separation improves maintainability.

## Progressive enhancement

The portfolio follows the principle of progressive enhancement.

The fundamental content and navigation are provided by HTML.

The stylesheet improves presentation.

The website does not require JavaScript to display the portfolio or navigate between its pages.

This approach creates a resilient baseline.

JavaScript can later provide additional behavior without making basic content dependent on scripting.

## Responsive structure

The stylesheet uses a responsive grid.

On wider screens, the home page can display multiple project cards in a row.

On smaller screens, the layout changes to a single column.

The responsive behavior is implemented through CSS media queries rather than separate HTML pages for desktop and mobile.

This keeps the semantic document structure consistent across devices.

## External links and security

The project uses:

    target="_blank"

for selected external project links.

When opening a new browsing context, the generated links also use:

    rel="noopener noreferrer"

`noopener` prevents the opened document from receiving an opener reference that could be used to interact with the original window.

`noreferrer` also suppresses the HTTP referrer in supported browser behavior.

The exact `rel` policy should be selected according to the site's requirements.

## HTML escaping

The Python generator uses Python's standard-library HTML escaping functions before inserting structured data into generated markup.

This is important because portfolio content may eventually come from:

- A database
- A CMS
- A form
- An API
- A spreadsheet
- A user-management system

Untrusted text must not automatically become executable markup.

Escaping is one component of secure output handling. A complete production security model also requires appropriate input validation, content security policies, HTTP security headers, authentication controls where applicable, and safe server-side processing.

## URL validation

The generator includes conservative URL handling.

It permits common web destinations such as:

- `https://`
- `http://`
- Relative paths
- Fragment references

A production application should use stronger validation when URLs are dynamic.

Special attention is required for dangerous URL schemes and user-controlled destinations.

A URL accepted from external data should never be assumed to be safe merely because it appears syntactically valid.

## Performance considerations

A portfolio is normally a relatively small website, but performance still matters.

Important considerations include:

### Images

Large images can dominate page size.

Images should be appropriately sized, compressed, and delivered in formats suitable for the target browser environment.

### CSS

Unused CSS increases transfer and parsing cost.

A small portfolio should avoid unnecessarily large frameworks when the site requires only a small amount of styling.

### JavaScript

JavaScript should be added only when it provides necessary behavior.

Navigation and basic content do not require JavaScript in this architecture.

### Fonts

Large numbers of external font files can increase network requests and page weight.

System fonts can provide good performance when custom typography is not required.

### Third-party resources

Analytics, embedded widgets, social media components, advertising scripts, and external libraries create additional network requests and trust relationships.

They should be introduced deliberately.

## SEO-oriented HTML

Semantic HTML does not guarantee search ranking.

It does provide a clearer representation of the document.

The project includes several useful structural features:

- Page-specific titles
- Meta descriptions
- One primary page heading
- Heading hierarchy
- Semantic landmarks
- Descriptive links
- Canonical metadata
- Machine-readable time information

Search visibility also depends on factors outside HTML structure, including content quality, site accessibility, performance, crawlability, server configuration, reputation, and search-engine policies.

## Multi-page architecture

The portfolio uses separate documents rather than placing every page into one HTML file.

The pages are:

### Home

`index.html` introduces the portfolio, provides a professional snapshot, presents featured projects, and lists core skills.

### About

`about.html` presents professional experience, technical skills, and working principles.

### Projects

`projects.html` provides detailed project information and technology lists.

### Contact

`contact.html` provides a structured contact form and direct contact information.

This separation gives each page a clear purpose.

## Reusable structure

The Python generator avoids manually constructing every page from unrelated fragments.

Reusable functions generate:

- Document metadata
- Site header
- Navigation
- Footer
- Home page
- About page
- Projects page
- Contact page

This is important because repeated HTML is a common source of inconsistency.

If the navigation were manually edited independently on four pages, it would be easy for one page to contain an outdated link or missing navigation item.

The generator provides a single source for the navigation structure.

## Data-driven project cards

The project information is represented using Python dataclasses.

Each project has:

- Title
- Description
- Technologies
- URL
- Category
- Year

This separates content from the rendering process.

The same conceptual model could later be populated from:

- JSON
- YAML
- CSV
- A database
- A CMS
- An API

The HTML structure can remain consistent while the source of the content changes.

## Testing

The script includes assertions for portfolio data and generated pages.

The tests verify basic assumptions such as:

- A portfolio name exists.
- A role exists.
- A plausible email value exists.
- Projects exist.
- Skills exist.
- Project titles are unique.
- Required HTML document elements exist.
- Expected page files are generated.

Assertions are useful for catching unexpected states during development.

They are not a substitute for comprehensive application testing.

## Structural validation

The Python script includes an educational validator.

It checks for:

- HTML5 doctype
- Language declaration
- Title
- UTF-8 declaration
- Viewport metadata
- Exactly one main element
- A primary heading
- Navigation
- Duplicate IDs
- Label-to-control relationships
- Secure handling of new-tab links
- Missing image alternative text
- Heading hierarchy
- Broken internal links

The validator intentionally uses simple regular-expression-based checks.

It is not a standards-compliant HTML parser or full accessibility auditing system.

Real HTML parsing is significantly more complicated because browsers implement detailed parsing and error-recovery rules.

The validator should therefore be viewed as a learning mechanism rather than a replacement for professional validation and browser testing.

## IDs and labels

The `id` attribute identifies an element uniquely within the document.

For example:

    <input id="email" name="email">

A label can reference it:

    <label for="email">Email address</label>

The `for` value must match the control's `id`.

Duplicate IDs create ambiguous references and can cause incorrect behavior in scripts, CSS selectors, accessibility relationships, and fragment navigation.

The generated validator checks for duplicate IDs.

## Common mistakes

### Using headings for visual size

Incorrect reasoning:

    "This text should look large, so I will use h2."

Heading levels represent hierarchy, not typography.

Use CSS for visual sizing.

### Using div for every region

`div` is useful, but using it for every meaningful region discards semantic information that could have been represented by more appropriate elements.

### Missing alternative text

An image without an appropriate `alt` attribute can create an accessibility problem.

### Missing form labels

A placeholder is not a reliable replacement for a proper form label.

Labels should identify controls programmatically and visually.

### Incorrect link semantics

Navigation should generally use links.

Actions should generally use buttons.

### Relying on color

Important state should not be communicated only through color.

### Trusting client-side validation

Browser validation improves the user experience but cannot protect a backend.

### Broken internal links

A multi-page portfolio can become unusable if navigation paths are inconsistent.

The Python validator checks generated internal links against the known page set.

## Edge cases

### Decorative images

If an image contributes no meaningful information, empty alternative text can be appropriate.

### Informative images

If an image communicates information, its alternative text should communicate the relevant information.

### Multiple navigation regions

A page can contain multiple `nav` elements.

When that happens, accessible labels help users distinguish their purposes.

### Nested articles

An article can contain sections and other structural elements when the content relationships justify them.

### Sections without headings

A thematic section generally benefits from a heading. If there is no meaningful heading or thematic grouping, another container may be more appropriate.

### External versus internal links

Internal links usually use relative paths.

External links use complete web URLs.

The security and trust considerations differ between these cases.

### Contact forms

A static HTML form does not automatically send email.

The `action` attribute points to the endpoint that should process the form.

A production implementation needs a backend or an appropriate form-processing service.

### Static hosting

The portfolio pages can be hosted on a static web server because the core website does not require server-side rendering.

The contact form is different because actual submission processing requires a server-side endpoint or another form-processing mechanism.

## Limitations of the project

The generated portfolio is an educational static website.

The contact form does not include a production backend.

The Python HTML checks are intentionally lightweight and are not a complete HTML, accessibility, security, or SEO audit.

The sample external URLs are placeholders.

The site does not implement authentication, a database, content management, analytics, or dynamic application behavior.

These limitations are deliberate because the main subject is semantic HTML and multi-page document architecture.

## Production considerations

Before deploying a portfolio publicly, the following areas should be reviewed:

- Replace placeholder portfolio data.
- Replace example external project URLs.
- Configure real canonical URLs.
- Add actual portfolio images where useful.
- Provide accurate image alternative text.
- Connect the contact form to a secure processing endpoint if required.
- Validate all submitted form data server-side.
- Use HTTPS.
- Configure appropriate HTTP security headers.
- Review Content Security Policy requirements.
- Optimize images.
- Test responsive layouts.
- Test keyboard navigation.
- Test with screen readers.
- Check heading hierarchy.
- Check link destinations.
- Check form error handling.
- Test across relevant browsers.
- Verify that every page has an appropriate title and description.
- Confirm that no private information or secrets are included in public HTML.

## Static site versus dynamic application

A semantic multi-page portfolio can remain entirely static.

Static architecture is appropriate when the site's primary requirements are:

- Presenting information
- Providing navigation
- Showing projects
- Publishing professional experience
- Providing contact information
- Linking to external resources

A dynamic architecture becomes useful when the website needs functionality such as:

- User accounts
- Database-backed content
- Personalized dashboards
- Administrative editing
- Server-side form processing
- Search across a large content collection
- Authentication
- Transactional workflows

The important principle is that dynamic functionality should be introduced because the requirements justify it, not simply because a technology is available.

## Why semantic HTML matters in a portfolio

A portfolio is more than a visual arrangement of cards and text.

Its document structure describes the relationship between:

- Identity
- Navigation
- Professional introduction
- Experience
- Projects
- Skills
- Contact information

Semantic HTML expresses those relationships directly in the document.

This makes the resulting website easier to understand, navigate, maintain, test, and extend.

The project therefore treats semantic HTML as the structural foundation of the portfolio rather than as a styling technique.
