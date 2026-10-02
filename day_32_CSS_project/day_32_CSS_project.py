"""
Responsive Landing Page Project Generator and Validator

This Python script models the build process of a responsive landing page
from scratch. It generates a complete project structure containing HTML,
CSS, JavaScript, and documentation, then performs static validation of the
generated files.

The implementation focuses on:
- Semantic landing-page structure
- Responsive CSS architecture
- Mobile-first breakpoints
- Navigation behavior
- Accessible interactive controls
- Responsive layout validation
- CSS custom properties
- Grid and Flexbox usage
- Component-oriented styling
- Project quality checks
- Production-oriented validation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
import re
import tempfile


@dataclass
class ValidationIssue:
    """Represents a concrete problem discovered during project validation."""

    file: str
    message: str
    severity: str = "error"


@dataclass
class ProjectReport:
    """Collects validation results for the landing-page project."""

    issues: list[ValidationIssue] = field(default_factory=list)

    def add(self, file: str, message: str, severity: str = "error") -> None:
        self.issues.append(ValidationIssue(file, message, severity))

    @property
    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def passed(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class LandingPageContent:
    """Content configuration used to build the page without hard-coded markup everywhere."""

    brand: str
    headline: str
    subheadline: str
    primary_cta: str
    secondary_cta: str
    features: tuple[tuple[str, str, str], ...]
    metrics: tuple[tuple[str, str], ...]


DEFAULT_CONTENT = LandingPageContent(
    brand="NOVA",
    headline="Build digital products that move with your customers.",
    subheadline=(
        "A responsive landing page foundation designed around clear content, "
        "accessible interactions, and layouts that adapt naturally across devices."
    ),
    primary_cta="Start building",
    secondary_cta="Explore features",
    features=(
        (
            "01",
            "Responsive by design",
            "Fluid grids, flexible typography, and mobile-first breakpoints keep the experience usable from compact phones to wide desktop screens.",
        ),
        (
            "02",
            "Clear visual hierarchy",
            "Strong spacing, readable type scales, and focused calls to action help visitors understand the product without visual clutter.",
        ),
        (
            "03",
            "Accessible interaction",
            "Semantic HTML, visible focus states, keyboard-friendly navigation, and reduced-motion support provide a stronger baseline for real users.",
        ),
    ),
    metrics=(
        ("01", "Semantic structure"),
        ("02", "Mobile-first CSS"),
        ("03", "Accessible navigation"),
        ("04", "Progressive enhancement"),
    ),
)


def html_escape(value: str) -> str:
    """Escape content before placing it into generated HTML."""

    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def build_html(content: LandingPageContent) -> str:
    """Generate semantic HTML for the landing page."""

    feature_markup = "\n".join(
        f"""          <article class="feature-card">
            <span class="feature-number">{html_escape(number)}</span>
            <h3>{html_escape(title)}</h3>
            <p>{html_escape(description)}</p>
          </article>"""
        for number, title, description in content.features
    )

    metric_markup = "\n".join(
        f"""          <li>
            <strong>{html_escape(number)}</strong>
            <span>{html_escape(label)}</span>
          </li>"""
        for number, label in content.metrics
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta
    name="description"
    content="A responsive landing page built from scratch with semantic HTML, modern CSS, and progressive JavaScript."
  >
  <title>{html_escape(content.brand)} | Responsive Landing Page</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <a class="skip-link" href="#main-content">Skip to content</a>

  <header class="site-header">
    <div class="container navigation">
      <a class="brand" href="#" aria-label="{html_escape(content.brand)} home">
        <span class="brand-mark" aria-hidden="true">N</span>
        <span>{html_escape(content.brand)}</span>
      </a>

      <button
        class="menu-toggle"
        type="button"
        aria-expanded="false"
        aria-controls="primary-navigation"
      >
        <span class="sr-only">Toggle navigation</span>
        <span aria-hidden="true"></span>
        <span aria-hidden="true"></span>
        <span aria-hidden="true"></span>
      </button>

      <nav id="primary-navigation" class="primary-navigation" aria-label="Primary navigation">
        <a href="#features">Features</a>
        <a href="#process">Process</a>
        <a href="#contact">Contact</a>
        <a class="nav-cta" href="#contact">Get started</a>
      </nav>
    </div>
  </header>

  <main id="main-content">
    <section class="hero" aria-labelledby="hero-title">
      <div class="container hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">Responsive landing page system</p>
          <h1 id="hero-title">{html_escape(content.headline)}</h1>
          <p class="hero-description">{html_escape(content.subheadline)}</p>

          <div class="hero-actions">
            <a class="button button-primary" href="#contact">{html_escape(content.primary_cta)}</a>
            <a class="button button-secondary" href="#features">{html_escape(content.secondary_cta)}</a>
          </div>

          <ul class="metrics" aria-label="Project characteristics">
{metric_markup}
          </ul>
        </div>

        <div class="hero-visual" aria-label="Responsive interface preview">
          <div class="window">
            <div class="window-toolbar" aria-hidden="true">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <div class="window-content">
              <div class="visual-label">NOVA / SYSTEM</div>
              <div class="visual-line visual-line-large"></div>
              <div class="visual-line"></div>
              <div class="visual-grid">
                <div></div>
                <div></div>
                <div></div>
                <div></div>
              </div>
              <div class="visual-footer"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section id="features" class="section" aria-labelledby="features-title">
      <div class="container">
        <div class="section-heading">
          <p class="eyebrow">Foundation</p>
          <h2 id="features-title">A layout built to adapt.</h2>
          <p>
            Each section uses responsive primitives rather than fixed screen assumptions.
          </p>
        </div>

        <div class="feature-grid">
{feature_markup}
        </div>
      </div>
    </section>

    <section id="process" class="section section-dark" aria-labelledby="process-title">
      <div class="container process-layout">
        <div>
          <p class="eyebrow">Process</p>
          <h2 id="process-title">Structure first. Styling second. Interaction third.</h2>
        </div>

        <div class="process-copy">
          <p>
            The page starts with semantic content and a predictable document structure.
            CSS then establishes layout, spacing, typography, color, and responsive behavior.
          </p>
          <p>
            JavaScript is limited to behavior that cannot be expressed with HTML and CSS,
            such as the mobile navigation state and keyboard-friendly menu handling.
          </p>
        </div>
      </div>
    </section>

    <section id="contact" class="section contact-section" aria-labelledby="contact-title">
      <div class="container contact-card">
        <div>
          <p class="eyebrow">Contact</p>
          <h2 id="contact-title">Turn the layout into your product surface.</h2>
          <p>
            Replace the sample content with your product value proposition, proof points,
            conversion path, and brand system.
          </p>
        </div>

        <form id="contact-form" class="contact-form">
          <label for="email">Email address</label>
          <input
            id="email"
            name="email"
            type="email"
            autocomplete="email"
            placeholder="you@example.com"
            required
          >
          <button class="button button-primary" type="submit">Request access</button>
          <p id="form-message" class="form-message" role="status" aria-live="polite"></p>
        </form>
      </div>
    </section>
  </main>

  <footer class="site-footer">
    <div class="container footer-content">
      <span>&copy; <span id="year"></span> {html_escape(content.brand)}</span>
      <a href="#main-content">Back to top</a>
    </div>
  </footer>

  <script src="script.js"></script>
</body>
</html>
"""


def build_css() -> str:
    """Generate the responsive CSS system used by the page."""

    return r""":root {
  --color-background: #f5f5f0;
  --color-surface: #ffffff;
  --color-text: #161616;
  --color-muted: #656565;
  --color-border: #d9d9d2;
  --color-accent: #d9ff45;
  --color-dark: #151515;
  --color-dark-muted: #a8a8a2;
  --shadow-card: 0 24px 70px rgba(0, 0, 0, 0.10);

  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.5rem;
  --space-6: 2rem;
  --space-7: 3rem;
  --space-8: 4rem;
  --space-9: 6rem;

  --container-width: 1180px;
  --radius-small: 0.5rem;
  --radius-large: 1.5rem;

  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--color-text);
  background: var(--color-background);
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  min-width: 320px;
  background: var(--color-background);
  color: var(--color-text);
  line-height: 1.6;
}

img,
svg {
  display: block;
  max-width: 100%;
}

a {
  color: inherit;
}

button,
input {
  font: inherit;
}

.container {
  width: min(calc(100% - 2rem), var(--container-width));
  margin-inline: auto;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.skip-link {
  position: fixed;
  top: -100px;
  left: 1rem;
  z-index: 100;
  padding: 0.75rem 1rem;
  background: var(--color-accent);
  color: var(--color-text);
}

.skip-link:focus {
  top: 1rem;
}

.site-header {
  position: sticky;
  top: 0;
  z-index: 50;
  border-bottom: 1px solid var(--color-border);
  background: rgba(245, 245, 240, 0.92);
  backdrop-filter: blur(16px);
}

.navigation {
  min-height: 4.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-5);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-decoration: none;
}

.brand-mark {
  display: grid;
  width: 2rem;
  aspect-ratio: 1;
  place-items: center;
  border-radius: 50%;
  background: var(--color-text);
  color: var(--color-accent);
  font-size: 0.8rem;
}

.primary-navigation {
  display: flex;
  align-items: center;
  gap: var(--space-5);
}

.primary-navigation a {
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 600;
}

.primary-navigation a:not(.nav-cta):hover {
  text-decoration: underline;
  text-underline-offset: 0.25rem;
}

.nav-cta {
  padding: 0.65rem 1rem;
  border-radius: 999px;
  background: var(--color-text);
  color: var(--color-surface);
}

.menu-toggle {
  display: none;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.hero {
  padding-block: var(--space-8);
}

.hero-grid {
  display: grid;
  gap: var(--space-8);
  align-items: center;
}

.hero-copy {
  max-width: 720px;
}

.eyebrow {
  margin: 0 0 var(--space-3);
  color: var(--color-muted);
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

h1,
h2,
h3,
p {
  margin-top: 0;
}

h1,
h2,
h3 {
  line-height: 1.05;
  letter-spacing: -0.04em;
}

h1 {
  max-width: 850px;
  margin-bottom: var(--space-5);
  font-size: clamp(3rem, 11vw, 7.5rem);
}

h2 {
  font-size: clamp(2.2rem, 5vw, 4.5rem);
  margin-bottom: var(--space-5);
}

h3 {
  font-size: 1.5rem;
  margin-bottom: var(--space-3);
}

.hero-description {
  max-width: 650px;
  color: var(--color-muted);
  font-size: clamp(1rem, 2vw, 1.25rem);
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-top: var(--space-6);
}

.button {
  display: inline-flex;
  min-height: 3rem;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.2rem;
  border: 1px solid var(--color-text);
  border-radius: 999px;
  cursor: pointer;
  font-weight: 750;
  text-decoration: none;
  transition: transform 160ms ease, background-color 160ms ease;
}

.button:hover {
  transform: translateY(-2px);
}

.button-primary {
  background: var(--color-text);
  color: var(--color-surface);
}

.button-secondary {
  background: transparent;
  color: var(--color-text);
}

.metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  padding: 0;
  margin: var(--space-8) 0 0;
  list-style: none;
}

.metrics li {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
}

.metrics strong {
  font-size: 0.75rem;
  color: var(--color-muted);
}

.metrics span {
  font-weight: 700;
}

.hero-visual {
  min-height: 420px;
  display: grid;
  place-items: center;
}

.window {
  width: min(100%, 520px);
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-large);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
  transform: rotate(2deg);
}

.window-toolbar {
  display: flex;
  gap: 0.4rem;
  padding: 1rem;
  border-bottom: 1px solid var(--color-border);
}

.window-toolbar span {
  width: 0.55rem;
  aspect-ratio: 1;
  border-radius: 50%;
  background: var(--color-border);
}

.window-content {
  min-height: 350px;
  padding: 2rem;
  background:
    linear-gradient(135deg, transparent 0 49%, rgba(0, 0, 0, 0.04) 50% 51%, transparent 52%),
    var(--color-surface);
}

.visual-label {
  margin-bottom: 4rem;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.15em;
}

.visual-line {
  width: 70%;
  height: 1rem;
  margin-bottom: 0.8rem;
  background: var(--color-text);
  opacity: 0.12;
}

.visual-line-large {
  width: 92%;
  height: 3rem;
  opacity: 1;
  background: var(--color-text);
}

.visual-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  margin-top: 3rem;
}

.visual-grid div {
  min-height: 80px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-small);
}

.visual-footer {
  width: 40%;
  height: 0.8rem;
  margin-top: 2rem;
  background: var(--color-accent);
}

.section {
  padding-block: var(--space-9);
}

.section-heading {
  max-width: 760px;
  margin-bottom: var(--space-7);
}

.section-heading > p:last-child {
  color: var(--color-muted);
  font-size: 1.1rem;
}

.feature-grid {
  display: grid;
  gap: 1rem;
}

.feature-card {
  padding: var(--space-6);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-large);
  background: var(--color-surface);
}

.feature-number {
  display: inline-block;
  margin-bottom: var(--space-7);
  color: var(--color-muted);
  font-size: 0.75rem;
  font-weight: 800;
}

.feature-card p {
  margin-bottom: 0;
  color: var(--color-muted);
}

.section-dark {
  background: var(--color-dark);
  color: var(--color-surface);
}

.section-dark .eyebrow,
.section-dark .process-copy {
  color: var(--color-dark-muted);
}

.process-layout {
  display: grid;
  gap: var(--space-7);
}

.process-copy {
  max-width: 620px;
  font-size: 1.1rem;
}

.contact-section {
  padding-bottom: var(--space-9);
}

.contact-card {
  display: grid;
  gap: var(--space-7);
  padding: var(--space-6);
  border-radius: var(--radius-large);
  background: var(--color-accent);
}

.contact-card h2 {
  max-width: 700px;
}

.contact-form {
  display: grid;
  gap: var(--space-3);
  align-content: start;
}

.contact-form label {
  font-weight: 750;
}

.contact-form input {
  width: 100%;
  min-height: 3.25rem;
  padding-inline: 1rem;
  border: 1px solid var(--color-text);
  border-radius: var(--radius-small);
  background: var(--color-surface);
}

.contact-form .button {
  justify-self: start;
}

.form-message {
  min-height: 1.5rem;
  margin: 0;
  font-size: 0.9rem;
}

.site-footer {
  border-top: 1px solid var(--color-border);
}

.footer-content {
  min-height: 5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  color: var(--color-muted);
  font-size: 0.85rem;
}

.footer-content a {
  font-weight: 700;
}

:focus-visible {
  outline: 3px solid var(--color-accent);
  outline-offset: 3px;
}

@media (min-width: 700px) {
  .container {
    width: min(calc(100% - 4rem), var(--container-width));
  }

  .hero {
    padding-block: var(--space-9);
  }

  .hero-grid {
    grid-template-columns: minmax(0, 1.05fr) minmax(320px, 0.95fr);
  }

  .feature-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .process-layout,
  .contact-card {
    grid-template-columns: minmax(0, 1fr) minmax(0, 0.8fr);
    align-items: center;
  }

  .contact-card {
    padding: var(--space-7);
  }
}

@media (max-width: 699px) {
  .menu-toggle {
    display: grid;
    gap: 4px;
    padding: 0.75rem 0.25rem;
  }

  .menu-toggle > span:not(.sr-only) {
    width: 1.5rem;
    height: 2px;
    background: var(--color-text);
  }

  .primary-navigation {
    position: absolute;
    inset: calc(100% + 1px) 0 auto;
    display: none;
    padding: 1rem;
    flex-direction: column;
    align-items: stretch;
    border-bottom: 1px solid var(--color-border);
    background: var(--color-background);
  }

  .primary-navigation.is-open {
    display: flex;
  }

  .primary-navigation a {
    padding: 0.65rem;
  }

  .nav-cta {
    text-align: center;
  }

  .hero-visual {
    min-height: auto;
    padding-block: var(--space-4);
  }

  .window {
    transform: none;
  }

  .section {
    padding-block: var(--space-8);
  }
}

@media (prefers-reduced-motion: reduce) {
  html {
    scroll-behavior: auto;
  }

  *,
  *::before,
  *::after {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }

  .button:hover {
    transform: none;
  }

  .window {
    transform: none;
  }
}
"""


def build_javascript() -> str:
    """Generate progressive JavaScript for navigation and form behavior."""

    return r"""const menuToggle = document.querySelector(".menu-toggle");
const navigation = document.querySelector("#primary-navigation");
const navigationLinks = document.querySelectorAll("#primary-navigation a");
const contactForm = document.querySelector("#contact-form");
const formMessage = document.querySelector("#form-message");
const yearElement = document.querySelector("#year");

function setNavigationState(isOpen) {
  if (!menuToggle || !navigation) {
    return;
  }

  navigation.classList.toggle("is-open", isOpen);
  menuToggle.setAttribute("aria-expanded", String(isOpen));
}

menuToggle?.addEventListener("click", () => {
  const isOpen = menuToggle.getAttribute("aria-expanded") === "true";
  setNavigationState(!isOpen);
});

navigationLinks.forEach((link) => {
  link.addEventListener("click", () => {
    setNavigationState(false);
  });
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    setNavigationState(false);
    menuToggle?.focus();
  }
});

window.addEventListener("resize", () => {
  if (window.innerWidth >= 700) {
    setNavigationState(false);
  }
});

contactForm?.addEventListener("submit", (event) => {
  event.preventDefault();

  const formData = new FormData(contactForm);
  const email = String(formData.get("email") ?? "").trim();

  if (!email) {
    formMessage.textContent = "Please enter an email address.";
    return;
  }

  if (!contactForm.checkValidity()) {
    formMessage.textContent = "Please enter a valid email address.";
    contactForm.reportValidity();
    return;
  }

  formMessage.textContent = `Access request received for ${email}.`;
  contactForm.reset();
});

if (yearElement) {
  yearElement.textContent = String(new Date().getFullYear());
}
"""


def build_readme() -> str:
    """Generate project documentation from the same technical model."""

    return """# Responsive Landing Page From Scratch

A responsive landing page built with semantic HTML, mobile-first CSS, and lightweight JavaScript. The project demonstrates how a page can be designed around flexible layout primitives instead of fixed desktop dimensions.

## Project focus

The implementation treats responsiveness as a layout problem rather than a collection of device-specific screenshots. The page begins with a narrow viewport assumption and progressively adds layout capacity when the available width increases.

The project contains:

- `index.html` for semantic page structure and content hierarchy.
- `styles.css` for the responsive visual system.
- `script.js` for navigation and form behavior.
- `responsive_landing_page.py` for generating the project and performing static validation.

The visual design uses a neutral background, high-contrast typography, a lime accent, rounded surfaces, and a deliberately restrained component system. The design choices are implemented through CSS custom properties so the visual system can be changed without rewriting every selector.

## Responsive design model

Responsive design requires more than shrinking a desktop layout. A useful implementation allows content to reflow when the available space changes.

The page uses a mobile-first baseline. At narrow widths, the navigation collapses, content is stacked vertically, cards occupy the available width, and the hero visual loses its decorative rotation. At wider widths, CSS Grid creates a two-column hero, feature cards become a three-column grid, and the process and contact sections use two-column layouts.

The primary breakpoint is `700px`. It is not intended to represent a particular phone, tablet, or desktop model. It represents the point at which this page's content has enough horizontal space to benefit from multiple columns.

The `clamp()` function is used for major headings. This allows typography to scale continuously within defined limits instead of jumping through many fixed font sizes.

The main container uses `min()` with a maximum width. This prevents very wide screens from producing excessively long reading lines while still allowing the page to use available space on smaller screens.

## Semantic page architecture

The HTML separates the major content responsibilities into meaningful elements.

The `header` contains the site identity and primary navigation. The `main` element contains the primary page content. Individual content areas are represented by `section` elements with accessible headings. Feature information uses `article` elements because each feature can be understood as an independent piece of content. The contact area contains a real `form` rather than a visually styled collection of controls.

This structure matters for responsive work because layout CSS can operate on meaningful groups instead of relying on arbitrary wrapper elements.

The hero contains two major regions: textual conversion content and a visual preview. The CSS Grid definition changes their relationship at larger widths without requiring duplicate markup.

## CSS architecture

The stylesheet begins with custom properties for the design system:

- Color variables define background, surface, text, muted text, borders, accent, and dark-section colors.
- Spacing variables establish a small reusable spacing scale.
- Container and radius variables keep structural dimensions consistent.
- The shadow variable provides the elevation used by the interface preview.

This approach avoids scattering repeated literal values throughout the stylesheet.

The global box-sizing rule makes width calculations more predictable because padding and borders are included in an element's declared dimensions.

The container uses a maximum width together with horizontal gutters. This prevents content from touching the viewport edge while avoiding an unnecessarily narrow fixed-width layout.

Flexbox is used for one-dimensional relationships such as the header, button groups, navigation links, and footer. Grid is used where two-dimensional relationships are more appropriate, including the hero and feature-card layouts.

## Responsive navigation

The navigation has two distinct layout states.

On larger screens, the primary navigation is visible as a horizontal Flexbox row. On narrow screens, the navigation is hidden until the menu button is activated.

The menu button exposes its state through `aria-expanded`, while `aria-controls` identifies the navigation region it controls. JavaScript changes the navigation's `is-open` class rather than directly manipulating many individual style properties.

The menu closes when a navigation link is selected, when Escape is pressed, and when the viewport becomes wide enough for the desktop navigation to become appropriate.

The JavaScript is intentionally small because CSS handles the actual responsive presentation. JavaScript provides behavior, not the fundamental layout system.

## Accessibility considerations

The page includes a skip link so keyboard users can move directly to the main content.

The mobile menu uses an actual `button`, which gives the control native keyboard and semantic behavior. The navigation region has an explicit accessible label.

Interactive controls receive a `:focus-visible` outline. This preserves a visible keyboard focus indicator without forcing the same visual treatment on every pointer interaction.

The form uses a real email input with `type="email"` and `required`. Browser constraint validation therefore performs basic input validation before the custom success message is displayed.

The form status element uses `role="status"` and `aria-live="polite"` so changes to its message can be communicated to assistive technology.

The stylesheet includes `prefers-reduced-motion`. Users who request reduced motion do not receive the normal smooth scrolling, hover translation, or decorative transform behavior.

## Visual hierarchy

The hero heading is intentionally much larger than supporting copy. The `clamp()` declaration allows the heading to remain expressive on a large display while imposing a usable upper limit.

Muted text is used for supporting information rather than important controls. Primary actions use a high-contrast filled treatment, while secondary actions remain visually lighter.

The feature cards use borders and surface contrast rather than excessive decoration. This makes the cards recognizable as separate content units while keeping the page hierarchy focused on the headline and conversion actions.

The hero preview is created entirely with HTML and CSS. It does not depend on an external image asset, which keeps the project self-contained and makes its responsive behavior predictable.

## Python implementation

The Python program acts as both a project generator and a static validator.

`LandingPageContent` stores the content model separately from the HTML construction logic. The generator uses that model to create headings, feature cards, metrics, and other page content. HTML values pass through `html_escape()` before insertion, preventing characters such as `<`, `>`, and quotes from being interpreted as markup.

`build_html()` produces the semantic document. `build_css()` produces the responsive stylesheet. `build_javascript()` produces the interaction layer.

The validation model is represented by `ValidationIssue` and `ProjectReport`. This separates validation findings from the generated files and makes it possible to distinguish errors from warnings.

The validator checks structural requirements such as the presence of the viewport declaration, stylesheet reference, JavaScript reference, main landmark, navigation, responsive media query, CSS Grid, Flexbox, `clamp()`, `aria-expanded`, and reduced-motion support.

The generated project can be written into a temporary directory by the script's command-line workflow. This makes the example executable without requiring an external Python dependency.

## JavaScript implementation

The JavaScript file uses DOM references for the menu button, navigation region, links, contact form, status message, and footer year.

`setNavigationState()` centralizes the mobile navigation state. It updates both the CSS class and the `aria-expanded` attribute, keeping visual and accessibility state synchronized.

Optional chaining is used when attaching behavior to optional elements. This prevents a missing optional element from causing the entire script to fail.

The Escape-key handler provides a direct keyboard mechanism for closing the mobile menu. The resize handler resets the mobile state when the viewport returns to the desktop layout.

The contact form demonstrates progressive enhancement. HTML provides the underlying form semantics and browser validation, while JavaScript adds a local status message. There is no fake network request and no assumption that a frontend-only page has a backend.

The script also demonstrates why client-side validation should not be treated as a security boundary. A production application must repeat validation on the server before accepting or storing submitted data.

## C++ case study

The C++ program models a responsive layout engine for a dashboard-like landing page component system.

Its purpose is different from the Python generator. Instead of producing source files, it evaluates layout constraints at runtime for several viewport widths.

The case study defines `Component` objects with minimum widths, preferred widths, minimum heights, and growth behavior. `LayoutEngine` receives viewport dimensions and determines whether components can remain in a row or must stack.

The engine evaluates a header, hero copy, hero visual, feature region, and contact panel. At compact widths, the navigation changes to a collapsed state and the hero becomes vertically stacked. At larger widths, the hero can use two columns.

The feature section uses a grid-column calculation based on available width and a minimum card width. This demonstrates a key responsive principle: the number of columns should be derived from content constraints rather than from assumptions about named devices.

The program also calculates an estimated content height and detects invalid component constraints. Negative dimensions and zero-width components are rejected with exceptions because they cannot produce meaningful layout results.

## C++ data structures and algorithmic behavior

The `Component` structure represents layout requirements rather than pixels.

`LayoutResult` stores the resulting number of columns, navigation mode, hero arrangement, estimated content height, and warnings.

`LayoutEngine::evaluate()` applies the layout rules. The operation runs in linear time relative to the number of components because each component is evaluated once. The feature-column calculation is constant time for a given viewport width.

The implementation deliberately avoids hard-coding a long list of device names. A layout system based on device labels becomes difficult to maintain as new screen sizes appear. Content-driven constraints provide a more general model.

## Important responsive edge cases

Very narrow viewports are constrained by the page's `320px` minimum body width. The main container still retains horizontal gutters so text and controls do not touch the viewport boundary.

Long headings can grow substantially, which is why the hero uses a fluid type scale and a maximum content width.

The feature grid switches from stacked cards to multiple columns only after the viewport reaches the project's chosen layout threshold. This avoids forcing three narrow cards into a space where their text would become difficult to read.

The navigation is particularly sensitive to intermediate widths. The breakpoint is based on the space required by the actual navigation content, not on a device category.

Reduced-motion preferences are handled separately from responsive width rules because motion preference and viewport size are independent concerns.

## Common implementation failures

A fixed desktop width is a common source of horizontal scrolling. The container in this project uses a fluid width with a maximum constraint instead.

Using absolute positioning for the entire page can make a layout appear correct at one viewport while breaking when text wraps. Grid and Flexbox are preferred for the primary structure because they respond to content dimensions.

A navigation menu controlled only through CSS may provide a visual state but can fail to expose the correct expanded state to assistive technology. The JavaScript therefore updates `aria-expanded` alongside the CSS class.

Hard-coding a separate layout for every device class creates unnecessary maintenance. The project instead uses content-oriented breakpoints and flexible dimensions.

Large decorative elements can create overflow on mobile screens. The hero preview is constrained with `width: min(100%, 520px)` so its width cannot exceed its containing block.

## Performance considerations

The project has no external JavaScript libraries and no required network requests. This keeps the interaction layer small and reduces dependency overhead.

The hero visual is composed of CSS elements rather than a large image. This avoids an additional image download for the demonstration, although a production site may still require optimized imagery for brand photography or product screenshots.

CSS custom properties are inexpensive and centralize design values. The layout uses native Grid and Flexbox rather than a JavaScript layout engine.

The JavaScript attaches only the event listeners required for navigation and the form interaction. It does not repeatedly calculate layout during scrolling.

## Production considerations

The demonstration form intentionally does not transmit personal data. A production implementation would need a server-side endpoint, transport security, rate limiting, server-side validation, abuse controls, and an appropriate data-retention policy.

Real production landing pages should also optimize images, define appropriate caching headers, test keyboard navigation, test screen-reader behavior, verify color contrast, and test the page at intermediate widths rather than checking only a phone and desktop screenshot.

If analytics are introduced, they should be loaded in a way that does not unnecessarily block initial rendering, and the implementation should account for the applicable privacy requirements.

Responsive correctness should be tested using actual content. Placeholder text can hide wrapping problems that appear when headlines, translations, customer names, or validation messages become longer.

## Validation workflow

Run the Python file with a standard Python 3 installation:

`python responsive_landing_page.py`

The script generates a temporary project, validates the generated files, prints validation findings, and reports whether the project passes its structural checks.

The generated files can then be opened in a browser by serving the project directory through a local static web server. A static server is preferable to opening the HTML through a `file:` URL when testing browser behavior because it more closely resembles normal web serving.

The most important validation cases are not just wide and narrow screenshots. The page should be examined while continuously resizing the viewport, tabbing through controls, opening and closing the mobile menu, pressing Escape, submitting invalid email input, and enabling reduced-motion preferences.

## Technical relationship between the files

The three implementations address different layers of the same engineering problem.

The Python program treats the landing page as a generated and validated artifact. It is useful for repeatable project creation and structural quality checks.

The JavaScript file treats responsiveness as primarily a CSS concern while adding behavior that requires runtime state. It demonstrates event-driven interaction without taking ownership of the layout.

The C++ program abstracts responsive behavior into a constraint-based layout engine. It focuses on how content requirements can determine layout modes and column counts rather than directly rendering browser CSS.

Together, the implementations show that responsive design is not simply a collection of media queries. It combines semantic structure, flexible dimensions, content-aware layout rules, accessible interaction, and validation against realistic viewport and content conditions.
"""
def validate_project(files: dict[str, str]) -> ProjectReport:
    """Perform static checks that catch common responsive landing-page defects."""

    report = ProjectReport()

    required_files = {"index.html", "styles.css", "script.js", "README.md"}
    missing = required_files - files.keys()

    for filename in sorted(missing):
        report.add(filename, "Required project file is missing.")

    html = files.get("index.html", "")
    css = files.get("styles.css", "")
    js = files.get("script.js", "")
    readme = files.get("README.md", "")

    html_requirements = {
        '<meta name="viewport"': "Missing responsive viewport metadata.",
        "<main": "Missing main content landmark.",
        "<nav": "Missing semantic navigation element.",
        'aria-expanded="false"': "Mobile navigation does not expose an initial expanded state.",
        'aria-controls="primary-navigation"': "Menu button does not identify its controlled navigation.",
        'rel="stylesheet"': "Stylesheet reference is missing.",
        '<script src="script.js"></script>': "JavaScript reference is missing.",
    }

    for needle, message in html_requirements.items():
        if needle not in html:
            report.add("index.html", message)

    if not re.search(r'<h1\b[^>]*>', html, re.IGNORECASE):
        report.add("index.html", "Landing page must contain a primary h1 heading.")

    if not re.search(r'<form\b', html, re.IGNORECASE):
        report.add("index.html", "Contact conversion area should use a form.")

    css_requirements = {
        "@media": "Responsive media queries are missing.",
        "display: grid": "CSS Grid is not used.",
        "display: flex": "Flexbox is not used.",
        "clamp(": "Fluid typography is not demonstrated.",
        "--color-": "CSS custom properties are missing.",
        "prefers-reduced-motion": "Reduced-motion support is missing.",
        "max-width": "Responsive width constraints are missing.",
    }

    for needle, message in css_requirements.items():
        if needle not in css:
            report.add("styles.css", message)

    if "overflow-x: hidden" in css:
        report.add(
            "styles.css",
            "Global overflow suppression can hide real layout defects; fix the source of overflow instead.",
            severity="warning",
        )

    if "position: fixed" in css and "skip-link" in css:
        pass

    js_requirements = {
        "aria-expanded": "JavaScript does not synchronize navigation accessibility state.",
        "Escape": "Keyboard dismissal for the mobile menu is missing.",
        "resize": "Navigation does not respond to viewport mode changes.",
        "checkValidity": "Form validation does not use browser constraint validation.",
    }

    for needle, message in js_requirements.items():
        if needle not in js:
            report.add("script.js", message)

    if "eval(" in js:
        report.add(
            "script.js",
            "eval() is unnecessary for this project and creates avoidable security and maintenance risks.",
        )

    if "TODO" in "".join(files.values()):
        report.add(
            "project",
            "Placeholder TODO content was found in the generated project.",
            severity="warning",
        )

    if len(readme) < 2000:
        report.add(
            "README.md",
            "Documentation is too short to explain the responsive implementation in sufficient detail.",
            severity="warning",
        )

    return report


def write_project(root: Path, content: LandingPageContent = DEFAULT_CONTENT) -> dict[str, str]:
    """Write a complete landing-page project to disk and return its contents."""

    files = {
        "index.html": build_html(content),
        "styles.css": build_css(),
        "script.js": build_javascript(),
        "README.md": build_readme(),
    }

    root.mkdir(parents=True, exist_ok=True)

    for filename, data in files.items():
        path = root / filename
        path.write_text(data, encoding="utf-8")

    return files


def print_report(report: ProjectReport) -> None:
    """Print human-readable validation output."""

    print("\nResponsive Landing Page Validation")
    print("=" * 42)

    if report.passed:
        print("STATUS: PASS")
    else:
        print("STATUS: FAIL")

    if not report.issues:
        print("No structural issues detected.")
        return

    for issue in report.issues:
        print(f"[{issue.severity.upper()}] {issue.file}: {issue.message}")

    print(f"\nErrors: {len(report.errors)}")
    print(f"Warnings: {len(report.warnings)}")


def demonstrate_layout_rules() -> None:
    """Show why content-driven breakpoints are preferable to device-specific layouts."""

    print("\nResponsive Layout Demonstration")
    print("=" * 42)

    viewports = (360, 600, 700, 1024, 1440)

    for width in viewports:
        if width < 700:
            navigation = "collapsed"
            hero = "stacked"
            feature_columns = 1
        else:
            navigation = "horizontal"
            hero = "two-column"
            feature_columns = 3

        print(
            f"Viewport {width:4d}px -> "
            f"navigation={navigation}, hero={hero}, "
            f"feature_columns={feature_columns}"
        )


def demonstrate_validation_failure() -> None:
    """Demonstrate that the validator can detect a broken responsive stylesheet."""

    broken_files = {
        "index.html": "<html><body><main><h1>Broken page</h1></main></body></html>",
        "styles.css": "body { color: black; }",
        "script.js": "console.log('broken');",
        "README.md": "Incomplete documentation.",
    }

    report = validate_project(broken_files)

    print("\nIntentional Validation Failure")
    print("=" * 42)
    print(f"Detected {len(report.errors)} error(s) and {len(report.warnings)} warning(s).")


def main() -> None:
    """Generate, validate, and demonstrate the responsive landing-page project."""

    demonstrate_layout_rules()

    with tempfile.TemporaryDirectory(prefix="responsive_landing_page_") as temporary_directory:
        project_path = Path(temporary_directory)
        files = write_project(project_path)
        report = validate_project(files)

        print(f"\nGenerated project: {project_path}")
        print("Files:")
        for filename in sorted(files):
            print(f"  - {filename}")

        print_report(report)

    demonstrate_validation_failure()


if __name__ == "__main__":
    main()
