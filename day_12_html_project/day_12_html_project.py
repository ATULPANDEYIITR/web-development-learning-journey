"""
Semantic HTML Multi-Page Portfolio Study Project
================================================

This standalone Python script teaches and demonstrates how to build a complete
multi-page portfolio using semantic HTML.

The script covers:

- HTML document structure
- Elements, tags, attributes, and nesting
- Semantic HTML
- Headings and document hierarchy
- Header, navigation, main, section, article, aside, and footer
- Links and multi-page navigation
- Images and alternative text
- Lists
- Tables
- Forms and accessible labels
- Buttons and interactive controls
- Metadata
- SEO-oriented structure
- Accessibility
- Progressive enhancement
- Responsive viewport configuration
- Reusable page structure
- Project cards
- Contact pages
- Semantic distinctions between similar elements
- Validation and structural checks
- Common mistakes
- Security-oriented HTML considerations
- Maintainability
- Production considerations

The Python portion does not require external packages. It generates a complete
portfolio website from structured Python data and performs educational checks
against the generated HTML.

Run:

    python semantic_portfolio.py

The generated website is written to the "semantic_portfolio_site" directory.
Open "semantic_portfolio_site/index.html" in a browser to inspect the result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from pathlib import Path
import re
from typing import Iterable


# =============================================================================
# 1. FUNDAMENTAL HTML CONCEPTS
# =============================================================================

def demonstrate_html_fundamentals() -> None:
    """
    Demonstrate the basic vocabulary of HTML.

    HTML is a markup language. It describes the structure and meaning of
    content rather than providing application logic.

    Element:
        A complete unit such as <p>Hello</p>.

    Tag:
        The markup itself, such as <p> or </p>.

    Attribute:
        Additional information attached to an opening tag, such as href,
        src, alt, id, class, or lang.

    Nesting:
        Elements can exist inside other elements. Correct nesting is important
        for predictable browser interpretation and accessibility.
    """

    paragraph = "<p>Hello, portfolio visitor.</p>"
    link = '<a href="projects.html">View projects</a>'
    image = '<img src="images/profile.jpg" alt="Professional profile photograph">'

    print("\n=== HTML fundamentals ===")
    print("Element:", paragraph)
    print("Link with attribute:", link)
    print("Image with attributes:", image)

    # This illustrates nesting:
    nested_structure = """
    <section>
        <h2>Selected projects</h2>
        <p>Projects demonstrate practical experience.</p>
    </section>
    """

    print("Nested semantic structure:")
    print(nested_structure)


# =============================================================================
# 2. DATA MODEL FOR THE PORTFOLIO
# =============================================================================

@dataclass
class Project:
    """Represent one portfolio project."""

    title: str
    description: str
    technologies: list[str]
    url: str
    category: str
    year: int


@dataclass
class Experience:
    """Represent one professional experience entry."""

    role: str
    organization: str
    period: str
    description: str
    achievements: list[str] = field(default_factory=list)


@dataclass
class Portfolio:
    """Store the content used across all portfolio pages."""

    name: str
    role: str
    email: str
    location: str
    bio: str
    skills: list[str]
    projects: list[Project]
    experience: list[Experience]


PORTFOLIO = Portfolio(
    name="Alex Morgan",
    role="Software Developer",
    email="alex@example.com",
    location="India",
    bio=(
        "Software developer focused on building accessible, maintainable, "
        "and user-centered web applications."
    ),
    skills=[
        "HTML",
        "CSS",
        "JavaScript",
        "Python",
        "SQL",
        "Git",
        "REST APIs",
        "Responsive Web Design",
    ],
    projects=[
        Project(
            title="Market Analytics Dashboard",
            description=(
                "A browser-based dashboard for exploring market indicators "
                "and portfolio performance."
            ),
            technologies=["HTML", "CSS", "JavaScript", "Python"],
            url="https://example.com/market-dashboard",
            category="Web Application",
            year=2026,
        ),
        Project(
            title="Advanced Calculator",
            description=(
                "A responsive calculator supporting mathematical operations, "
                "history, memory functions, and multiple calculation modes."
            ),
            technologies=["HTML", "CSS", "JavaScript"],
            url="https://example.com/calculator",
            category="Frontend Application",
            year=2026,
        ),
        Project(
            title="Learning Portfolio",
            description=(
                "A structured educational portfolio presenting technical "
                "projects, skills, and professional experience."
            ),
            technologies=["HTML", "CSS"],
            url="https://example.com/learning-portfolio",
            category="Portfolio",
            year=2025,
        ),
    ],
    experience=[
        Experience(
            role="Software Developer",
            organization="Example Technology",
            period="2025 - Present",
            description=(
                "Develop and maintain web applications with emphasis on "
                "semantic structure, reliability, and usability."
            ),
            achievements=[
                "Improved page structure using semantic HTML.",
                "Implemented responsive interfaces.",
                "Collaborated on API-integrated applications.",
            ],
        ),
        Experience(
            role="Technology Intern",
            organization="Example Labs",
            period="2024 - 2025",
            description=(
                "Supported development and testing of internal web tools."
            ),
            achievements=[
                "Created reusable interface components.",
                "Documented development workflows.",
                "Performed browser-based testing.",
            ],
        ),
    ],
)


# =============================================================================
# 3. HTML ESCAPING
# =============================================================================

def safe_text(value: str) -> str:
    """
    Escape text before inserting it into HTML.

    This is important when content originates from users, databases, APIs,
    spreadsheets, or other external sources.

    html.escape converts characters such as:

        &  -> &amp;
        <  -> &lt;
        >  -> &gt;
        "  -> &quot;
        '  -> &#x27;

    Escaping HTML content reduces the risk of accidentally interpreting data
    as markup and is an important defense against HTML injection and XSS when
    combined with appropriate server-side security controls.
    """

    return escape(value, quote=True)


def safe_url(url: str) -> str:
    """
    Perform a conservative validation of URLs used in generated HTML.

    This function intentionally permits common web schemes only.

    A production application should use stronger URL validation appropriate
    for its threat model and should never rely on client-side validation alone.
    """

    stripped = url.strip()

    if stripped.startswith(("https://", "http://", "/", "#")):
        return safe_text(stripped)

    raise ValueError(f"Unsupported URL scheme: {url}")


# =============================================================================
# 4. REUSABLE SEMANTIC COMPONENTS
# =============================================================================

def render_document_start(
    title: str,
    description: str,
    canonical_path: str,
) -> str:
    """
    Create the beginning of an HTML5 document.

    Important semantic and metadata concepts demonstrated here:

    - <!doctype html> enables standards mode.
    - lang identifies the document language.
    - charset declares UTF-8.
    - viewport supports responsive layouts.
    - title identifies the page in browser tabs and search contexts.
    - description provides concise metadata.
    - canonical identifies the preferred URL representation.
    """

    return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta
        name="description"
        content="{safe_text(description)}"
    >
    <link rel="canonical" href="{safe_url(canonical_path)}">
    <title>{safe_text(title)}</title>
    <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
"""


def render_header(active_page: str) -> str:
    """
    Render the site-wide header and primary navigation.

    <header> represents introductory or navigational content.

    <nav> identifies a major navigation block. Screen readers can expose
    navigation landmarks so users can move between page regions efficiently.

    aria-current="page" identifies the current page. It is useful because
    visual styling alone does not communicate state to every user.
    """

    pages = [
        ("index.html", "Home", "home"),
        ("about.html", "About", "about"),
        ("projects.html", "Projects", "projects"),
        ("contact.html", "Contact", "contact"),
    ]

    navigation_items = []

    for href, label, identifier in pages:
        current_attribute = (
            ' aria-current="page"' if active_page == identifier else ""
        )

        navigation_items.append(
            f'                <li><a href="{safe_url(href)}"{current_attribute}>'
            f"{safe_text(label)}</a></li>"
        )

    return f"""
<header class="site-header">
    <div class="container header-inner">
        <a class="site-brand" href="index.html" aria-label="Alex Morgan home">
            <span class="brand-name">Alex Morgan</span>
            <span class="brand-role">Software Developer</span>
        </a>

        <nav aria-label="Primary navigation">
            <ul class="navigation-list">
{chr(10).join(navigation_items)}
            </ul>
        </nav>
    </div>
</header>
"""


def render_footer() -> str:
    """
    Render the site footer.

    <footer> represents footer information for its nearest sectioning context.
    At document level it commonly contains copyright, contact information,
    legal links, or secondary navigation.
    """

    return """
<footer class="site-footer">
    <div class="container footer-inner">
        <p>&copy; 2026 Alex Morgan. All rights reserved.</p>

        <nav aria-label="Footer navigation">
            <ul class="footer-links">
                <li><a href="index.html">Home</a></li>
                <li><a href="about.html">About</a></li>
                <li><a href="projects.html">Projects</a></li>
                <li><a href="contact.html">Contact</a></li>
            </ul>
        </nav>
    </div>
</footer>
</body>
</html>
"""


def wrap_page(
    title: str,
    description: str,
    active_page: str,
    main_content: str,
    canonical_path: str,
) -> str:
    """Combine metadata, header, main content, and footer."""

    return (
        render_document_start(title, description, canonical_path)
        + render_header(active_page)
        + f"\n<main id=\"main-content\">\n{main_content}\n</main>\n"
        + render_footer()
    )


# =============================================================================
# 5. SEMANTIC CONTENT: HOME PAGE
# =============================================================================

def render_home_page(portfolio: Portfolio) -> str:
    """
    Create the home page.

    Semantic hierarchy:

        main
          section
            h1
            p
            navigation
          section
            h2
            article

    A page should generally have one clear primary <h1>. Lower-level headings
    should reflect the hierarchy of the content rather than merely visual size.
    """

    project_preview = portfolio.projects[:3]

    articles = []

    for project in project_preview:
        technology_items = "".join(
            f"<li>{safe_text(technology)}</li>"
            for technology in project.technologies
        )

        articles.append(
            f"""
            <article class="project-card">
                <header>
                    <p class="project-category">{safe_text(project.category)}</p>
                    <h3>{safe_text(project.title)}</h3>
                </header>

                <p>{safe_text(project.description)}</p>

                <ul class="technology-list" aria-label="Technologies used">
                    {technology_items}
                </ul>

                <footer>
                    <a href="{safe_url(project.url)}"
                       target="_blank"
                       rel="noopener noreferrer">
                        View project
                    </a>
                </footer>
            </article>
            """
        )

    content = f"""
<section class="hero" aria-labelledby="home-heading">
    <div class="container hero-grid">
        <div>
            <p class="eyebrow">Software development portfolio</p>
            <h1 id="home-heading">
                Building practical digital products with semantic web standards.
            </h1>

            <p class="hero-description">
                {safe_text(portfolio.bio)}
            </p>

            <nav aria-label="Primary calls to action" class="hero-actions">
                <a class="button" href="projects.html">Explore projects</a>
                <a class="button secondary" href="contact.html">Contact me</a>
            </nav>
        </div>

        <aside class="hero-aside" aria-label="Professional snapshot">
            <p><strong>Role</strong><br>{safe_text(portfolio.role)}</p>
            <p><strong>Location</strong><br>{safe_text(portfolio.location)}</p>
            <p><strong>Focus</strong><br>Accessible and maintainable web applications</p>
        </aside>
    </div>
</section>

<section class="section" aria-labelledby="featured-projects-heading">
    <div class="container">
        <header class="section-heading">
            <p class="eyebrow">Selected work</p>
            <h2 id="featured-projects-heading">Featured projects</h2>
        </header>

        <div class="project-grid">
            {''.join(articles)}
        </div>

        <p class="section-link">
            <a href="projects.html">See all projects</a>
        </p>
    </div>
</section>

<section class="section muted-section" aria-labelledby="skills-heading">
    <div class="container">
        <header class="section-heading">
            <h2 id="skills-heading">Core skills</h2>
        </header>

        <ul class="skill-list">
            {''.join(
                f'<li><span class="skill-chip">{safe_text(skill)}</span></li>'
                for skill in portfolio.skills
            )}
        </ul>
    </div>
</section>
"""

    return wrap_page(
        title=f"{portfolio.name} | {portfolio.role}",
        description=portfolio.bio,
        active_page="home",
        main_content=content,
        canonical_path="index.html",
    )


# =============================================================================
# 6. SEMANTIC CONTENT: ABOUT PAGE
# =============================================================================

def render_about_page(portfolio: Portfolio) -> str:
    """
    Create the about page.

    This page demonstrates:

    - article for a self-contained professional profile
    - section for thematic content
    - aside for complementary information
    - ordered and unordered lists
    - time element for machine-readable dates
    """

    experience_articles = []

    for experience in portfolio.experience:
        achievements = "".join(
            f"<li>{safe_text(achievement)}</li>"
            for achievement in experience.achievements
        )

        experience_articles.append(
            f"""
            <article class="experience-card">
                <header>
                    <h3>{safe_text(experience.role)}</h3>
                    <p>
                        <strong>{safe_text(experience.organization)}</strong>
                        <br>
                        <time>{safe_text(experience.period)}</time>
                    </p>
                </header>

                <p>{safe_text(experience.description)}</p>

                <ul>
                    {achievements}
                </ul>
            </article>
            """
        )

    content = f"""
<section class="page-introduction" aria-labelledby="about-heading">
    <div class="container">
        <p class="eyebrow">Professional profile</p>
        <h1 id="about-heading">About</h1>

        <p class="lead">
            {safe_text(portfolio.bio)}
        </p>
    </div>
</section>

<section class="section" aria-labelledby="experience-heading">
    <div class="container">
        <header class="section-heading">
            <h2 id="experience-heading">Professional experience</h2>
            <p>
                A chronological presentation of selected professional roles.
            </p>
        </header>

        <div class="experience-list">
            {''.join(experience_articles)}
        </div>
    </div>
</section>

<section class="section" aria-labelledby="technical-skills-heading">
    <div class="container two-column">
        <article>
            <header>
                <h2 id="technical-skills-heading">Technical skills</h2>
            </header>

            <ul class="detailed-skill-list">
                {''.join(
                    f'<li><strong>{safe_text(skill)}</strong></li>'
                    for skill in portfolio.skills
                )}
            </ul>
        </article>

        <aside class="information-panel" aria-labelledby="working-principles-heading">
            <h2 id="working-principles-heading">Working principles</h2>

            <ol>
                <li>Use semantic structure before visual styling.</li>
                <li>Prefer accessible interfaces by default.</li>
                <li>Keep content and presentation maintainable.</li>
                <li>Validate assumptions through testing.</li>
            </ol>
        </aside>
    </div>
</section>
"""

    return wrap_page(
        title=f"About | {portfolio.name}",
        description="Professional background, experience, skills, and working principles.",
        active_page="about",
        main_content=content,
        canonical_path="about.html",
    )


# =============================================================================
# 7. SEMANTIC CONTENT: PROJECTS PAGE
# =============================================================================

def render_projects_page(portfolio: Portfolio) -> str:
    """
    Create a detailed projects page.

    Each project is an <article> because it represents an independent,
    reusable piece of content.

    A <section> would be appropriate for a thematic grouping of projects,
    while each project itself is better represented as an <article>.
    """

    project_articles = []

    for project in portfolio.projects:
        technologies = "".join(
            f"<li>{safe_text(technology)}</li>"
            for technology in project.technologies
        )

        project_articles.append(
            f"""
            <article class="project-detail-card">
                <header>
                    <p class="project-category">
                        {safe_text(project.category)}
                    </p>

                    <h2>{safe_text(project.title)}</h2>

                    <p class="project-year">
                        <time datetime="{project.year}">
                            {project.year}
                        </time>
                    </p>
                </header>

                <p>{safe_text(project.description)}</p>

                <section aria-labelledby="tech-{project.year}-{re.sub(r'[^a-z0-9]+', '-', project.title.lower()).strip('-')}">
                    <h3 id="tech-{project.year}-{re.sub(r'[^a-z0-9]+', '-', project.title.lower()).strip('-')}">
                        Technologies
                    </h3>

                    <ul class="technology-list">
                        {technologies}
                    </ul>
                </section>

                <footer>
                    <a href="{safe_url(project.url)}"
                       target="_blank"
                       rel="noopener noreferrer">
                        Open project
                    </a>
                </footer>
            </article>
            """
        )

    content = f"""
<section class="page-introduction" aria-labelledby="projects-heading">
    <div class="container">
        <p class="eyebrow">Selected work</p>
        <h1 id="projects-heading">Projects</h1>
        <p class="lead">
            A collection of projects demonstrating web development,
            programming, and practical problem solving.
        </p>
    </div>
</section>

<section class="section" aria-labelledby="project-list-heading">
    <div class="container">
        <header class="section-heading">
            <h2 id="project-list-heading">Project portfolio</h2>
        </header>

        <div class="project-detail-list">
            {''.join(project_articles)}
        </div>
    </div>
</section>
"""

    return wrap_page(
        title=f"Projects | {portfolio.name}",
        description="Selected software development projects and technologies.",
        active_page="projects",
        main_content=content,
        canonical_path="projects.html",
    )


# =============================================================================
# 8. SEMANTIC CONTENT: CONTACT PAGE
# =============================================================================

def render_contact_page(portfolio: Portfolio) -> str:
    """
    Create the contact page.

    Important form concepts:

    - <form> groups controls into a submission unit.
    - <label> provides a programmatic name for each control.
    - for="..." connects labels to controls through matching id values.
    - name identifies submitted fields.
    - type communicates the intended kind of data.
    - required expresses a client-side constraint.
    - autocomplete improves usability.
    - textarea provides a multi-line text control.
    - button type="submit" explicitly submits the form.

    Client-side validation is not a security boundary. A server must validate
    and sanitize submitted data independently.
    """

    content = f"""
<section class="page-introduction" aria-labelledby="contact-heading">
    <div class="container">
        <p class="eyebrow">Get in touch</p>
        <h1 id="contact-heading">Contact</h1>
        <p class="lead">
            Use the form below to send a professional enquiry.
        </p>
    </div>
</section>

<section class="section" aria-labelledby="contact-form-heading">
    <div class="container contact-layout">
        <article>
            <header>
                <h2 id="contact-form-heading">Send a message</h2>
            </header>

            <form action="/contact" method="post" class="contact-form">
                <div class="form-field">
                    <label for="name">Name</label>
                    <input
                        id="name"
                        name="name"
                        type="text"
                        autocomplete="name"
                        required
                    >
                </div>

                <div class="form-field">
                    <label for="email">Email address</label>
                    <input
                        id="email"
                        name="email"
                        type="email"
                        autocomplete="email"
                        required
                    >
                </div>

                <div class="form-field">
                    <label for="subject">Subject</label>
                    <input
                        id="subject"
                        name="subject"
                        type="text"
                        required
                    >
                </div>

                <div class="form-field">
                    <label for="message">Message</label>
                    <textarea
                        id="message"
                        name="message"
                        rows="8"
                        required
                    ></textarea>
                </div>

                <button type="submit">Send message</button>
            </form>
        </article>

        <aside class="information-panel" aria-labelledby="direct-contact-heading">
            <h2 id="direct-contact-heading">Direct contact</h2>

            <address>
                <p>
                    <strong>Email</strong><br>
                    <a href="mailto:{safe_text(portfolio.email)}">
                        {safe_text(portfolio.email)}
                    </a>
                </p>

                <p>
                    <strong>Location</strong><br>
                    {safe_text(portfolio.location)}
                </p>
            </address>
        </aside>
    </div>
</section>
"""

    return wrap_page(
        title=f"Contact | {portfolio.name}",
        description="Contact page for professional enquiries.",
        active_page="contact",
        main_content=content,
        canonical_path="contact.html",
    )


# =============================================================================
# 9. CSS FOR THE GENERATED WEBSITE
# =============================================================================

CSS = r"""
/*
    Portfolio stylesheet.

    The HTML remains meaningful without this CSS. This demonstrates
    progressive enhancement: structure and content are provided by HTML,
    while CSS controls presentation.
*/

:root {
    font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    color: #172033;
    background: #f7f8fc;
    line-height: 1.6;
}

* {
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {
    margin: 0;
    background: #f7f8fc;
}

img {
    max-width: 100%;
    height: auto;
}

a {
    color: #1646b5;
}

a:focus-visible,
button:focus-visible,
input:focus-visible,
textarea:focus-visible {
    outline: 3px solid #ff9f1c;
    outline-offset: 3px;
}

.container {
    width: min(1120px, calc(100% - 2rem));
    margin-inline: auto;
}

.site-header {
    background: #ffffff;
    border-bottom: 1px solid #dfe3eb;
}

.header-inner {
    min-height: 76px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 2rem;
}

.site-brand {
    display: grid;
    text-decoration: none;
    color: inherit;
}

.brand-name {
    font-weight: 800;
}

.brand-role {
    font-size: 0.85rem;
    color: #667085;
}

.navigation-list,
.footer-links,
.skill-list,
.technology-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.navigation-list {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.navigation-list a {
    text-decoration: none;
    font-weight: 650;
}

.navigation-list a[aria-current="page"] {
    text-decoration: underline;
    text-underline-offset: 0.25rem;
}

.hero {
    padding: 6rem 0;
    background: linear-gradient(135deg, #eaf1ff, #f8ecff);
}

.hero-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 3rem;
    align-items: center;
}

.hero h1,
.page-introduction h1 {
    max-width: 850px;
    font-size: clamp(2.4rem, 7vw, 5rem);
    line-height: 1.02;
    margin: 0.25rem 0 1.5rem;
}

.hero-description,
.lead {
    max-width: 760px;
    font-size: 1.2rem;
    color: #4b5565;
}

.eyebrow,
.project-category {
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-size: 0.78rem;
    font-weight: 800;
}

.hero-aside,
.information-panel {
    background: #ffffff;
    border: 1px solid #dfe3eb;
    border-radius: 1rem;
    padding: 1.5rem;
}

.hero-actions {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-top: 2rem;
}

.button,
button {
    display: inline-block;
    border: 0;
    border-radius: 0.6rem;
    padding: 0.8rem 1.1rem;
    background: #172033;
    color: #ffffff;
    text-decoration: none;
    font-weight: 700;
    cursor: pointer;
}

.button.secondary {
    background: #ffffff;
    color: #172033;
    border: 1px solid #bfc6d4;
}

.section {
    padding: 5rem 0;
}

.muted-section {
    background: #eef1f6;
}

.section-heading {
    margin-bottom: 2rem;
}

.section-heading h2 {
    font-size: clamp(1.8rem, 4vw, 3rem);
    margin: 0;
}

.project-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.25rem;
}

.project-card,
.project-detail-card,
.experience-card {
    background: #ffffff;
    border: 1px solid #dfe3eb;
    border-radius: 1rem;
    padding: 1.5rem;
}

.project-card {
    display: flex;
    flex-direction: column;
    min-height: 100%;
}

.project-card footer,
.project-detail-card footer {
    margin-top: auto;
    padding-top: 1.5rem;
}

.technology-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 1rem;
}

.technology-list li {
    background: #eef1f6;
    border-radius: 999px;
    padding: 0.25rem 0.65rem;
    font-size: 0.85rem;
}

.skill-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.7rem;
}

.skill-chip {
    display: inline-block;
    background: #ffffff;
    border: 1px solid #cfd5df;
    border-radius: 999px;
    padding: 0.55rem 0.8rem;
}

.page-introduction {
    padding: 5rem 0 2rem;
}

.experience-list,
.project-detail-list {
    display: grid;
    gap: 1rem;
}

.two-column,
.contact-layout {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 2rem;
}

.detailed-skill-list {
    columns: 2;
}

.contact-form {
    display: grid;
    gap: 1.2rem;
}

.form-field {
    display: grid;
    gap: 0.45rem;
}

.form-field label {
    font-weight: 700;
}

.form-field input,
.form-field textarea {
    width: 100%;
    border: 1px solid #aeb6c4;
    border-radius: 0.5rem;
    padding: 0.8rem;
    font: inherit;
    background: #ffffff;
}

.site-footer {
    background: #172033;
    color: #ffffff;
    padding: 2rem 0;
}

.footer-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
}

.footer-links {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.footer-links a {
    color: #ffffff;
}

@media (max-width: 800px) {
    .header-inner,
    .footer-inner {
        align-items: flex-start;
        flex-direction: column;
        padding-block: 1rem;
    }

    .hero-grid,
    .project-grid,
    .two-column,
    .contact-layout {
        grid-template-columns: 1fr;
    }

    .hero {
        padding: 4rem 0;
    }

    .detailed-skill-list {
        columns: 1;
    }
}

@media (prefers-reduced-motion: reduce) {
    html {
        scroll-behavior: auto;
    }
}
"""


# =============================================================================
# 10. ACCESSIBILITY-ORIENTED HTML CHECKS
# =============================================================================

@dataclass
class ValidationIssue:
    """Represent one structural or accessibility issue."""

    severity: str
    message: str


def count_tag(html: str, tag: str) -> int:
    """Count opening HTML tags approximately for educational validation."""

    pattern = rf"<{re.escape(tag)}(?:\s|>)"
    return len(re.findall(pattern, html, flags=re.IGNORECASE))


def extract_ids(html: str) -> list[str]:
    """Extract id attributes from HTML."""

    return re.findall(r'\bid="([^"]+)"', html, flags=re.IGNORECASE)


def extract_for_attributes(html: str) -> list[str]:
    """Extract label-for relationships."""

    return re.findall(r'\bfor="([^"]+)"', html, flags=re.IGNORECASE)


def validate_html_structure(html: str, filename: str) -> list[ValidationIssue]:
    """
    Perform educational checks.

    This is not a replacement for a standards-compliant HTML validator.
    Parsing HTML reliably requires understanding HTML parsing rules, malformed
    markup, foreign content, character references, and browser error recovery.

    The checks here deliberately focus on concepts taught by the project.
    """

    issues: list[ValidationIssue] = []

    if "<!doctype html>" not in html.lower():
        issues.append(
            ValidationIssue("error", "Missing HTML5 doctype.")
        )

    if '<html lang="' not in html.lower():
        issues.append(
            ValidationIssue(
                "warning",
                "The document does not declare a language on <html>.",
            )
        )

    if "<title>" not in html.lower():
        issues.append(
            ValidationIssue("error", "Missing <title>.")
        )

    if '<meta charset="utf-8">' not in html.lower():
        issues.append(
            ValidationIssue(
                "warning",
                "UTF-8 charset declaration is missing.",
            )
        )

    if '<meta name="viewport"' not in html.lower():
        issues.append(
            ValidationIssue(
                "warning",
                "Responsive viewport metadata is missing.",
            )
        )

    if count_tag(html, "main") != 1:
        issues.append(
            ValidationIssue(
                "error",
                f"{filename}: expected exactly one <main> element.",
            )
        )

    if count_tag(html, "h1") != 1:
        issues.append(
            ValidationIssue(
                "warning",
                f"{filename}: expected one primary <h1> for this portfolio design.",
            )
        )

    if count_tag(html, "nav") < 1:
        issues.append(
            ValidationIssue(
                "warning",
                f"{filename}: no navigation landmark found.",
            )
        )

    ids = extract_ids(html)

    if len(ids) != len(set(ids)):
        issues.append(
            ValidationIssue(
                "error",
                f"{filename}: duplicate id attributes detected.",
            )
        )

    labels = extract_for_attributes(html)

    for label_target in labels:
        if label_target not in ids:
            issues.append(
                ValidationIssue(
                    "error",
                    f"{filename}: label references missing id '{label_target}'.",
                )
            )

    # External links opened in a new browsing context should use an explicit
    # rel value. "noopener" prevents the opened page from controlling the
    # opener window through window.opener.
    external_links = re.findall(
        r'<a\b[^>]*target="_blank"[^>]*>',
        html,
        flags=re.IGNORECASE,
    )

    for link in external_links:
        if "noopener" not in link.lower():
            issues.append(
                ValidationIssue(
                    "warning",
                    f"{filename}: target=\"_blank\" link lacks rel=\"noopener\".",
                )
            )

    # Images need alternative text. The generated project intentionally does
    # not use decorative images, but the check demonstrates the rule.
    image_tags = re.findall(
        r"<img\b[^>]*>",
        html,
        flags=re.IGNORECASE,
    )

    for image in image_tags:
        if not re.search(r'\balt="[^"]*"', image, flags=re.IGNORECASE):
            issues.append(
                ValidationIssue(
                    "error",
                    f"{filename}: image is missing an alt attribute.",
                )
            )

    return issues


# =============================================================================
# 11. HEADING HIERARCHY CHECK
# =============================================================================

def check_heading_hierarchy(html: str, filename: str) -> list[ValidationIssue]:
    """
    Check heading levels.

    A heading hierarchy should represent content relationships.

    Example:

        h1
          h2
            h3
          h2

    Jumping directly from h1 to h4 is often a sign that heading levels were
    chosen for appearance rather than structure.
    """

    headings = re.findall(
        r"<h([1-6])\b[^>]*>",
        html,
        flags=re.IGNORECASE,
    )

    issues: list[ValidationIssue] = []

    if not headings:
        return [
            ValidationIssue(
                "error",
                f"{filename}: no headings were found.",
            )
        ]

    previous = int(headings[0])

    if previous != 1:
        issues.append(
            ValidationIssue(
                "warning",
                f"{filename}: document begins with h{previous} instead of h1.",
            )
        )

    for value in headings[1:]:
        current = int(value)

        if current > previous + 1:
            issues.append(
                ValidationIssue(
                    "warning",
                    f"{filename}: heading jumps from h{previous} to h{current}.",
                )
            )

        previous = current

    return issues


# =============================================================================
# 12. LINK VALIDATION
# =============================================================================

def validate_internal_links(
    html: str,
    filename: str,
    known_files: Iterable[str],
) -> list[ValidationIssue]:
    """
    Verify that internal page links point to generated portfolio files.

    This demonstrates why navigation should be treated as a system rather than
    isolated links copied manually across pages.
    """

    known = set(known_files)
    issues: list[ValidationIssue] = []

    links = re.findall(
        r'<a\b[^>]*href="([^"]+)"',
        html,
        flags=re.IGNORECASE,
    )

    for link in links:
        if link.startswith(("http://", "https://", "mailto:", "#", "/")):
            continue

        clean_link = link.split("#", 1)[0]

        if clean_link and clean_link not in known:
            issues.append(
                ValidationIssue(
                    "error",
                    f"{filename}: internal link points to missing file '{clean_link}'.",
                )
            )

    return issues


# =============================================================================
# 13. GENERATING THE WEBSITE
# =============================================================================

def build_pages(portfolio: Portfolio) -> dict[str, str]:
    """
    Build all HTML pages.

    Multi-page architecture means each page is a separate HTML document.
    Navigation connects those documents through ordinary hyperlinks.
    """

    return {
        "index.html": render_home_page(portfolio),
        "about.html": render_about_page(portfolio),
        "projects.html": render_projects_page(portfolio),
        "contact.html": render_contact_page(portfolio),
    }


def write_site(
    output_directory: Path,
    pages: dict[str, str],
) -> None:
    """
    Write the complete website to disk.

    Existing files with these names are replaced. The function does not delete
    unrelated files from the output directory.
    """

    output_directory.mkdir(parents=True, exist_ok=True)

    assets_directory = output_directory / "assets"
    assets_directory.mkdir(parents=True, exist_ok=True)

    for filename, content in pages.items():
        path = output_directory / filename
        path.write_text(content, encoding="utf-8")

    (assets_directory / "styles.css").write_text(
        CSS,
        encoding="utf-8",
    )


# =============================================================================
# 14. TESTING THE GENERATED WEBSITE
# =============================================================================

def test_portfolio_data(portfolio: Portfolio) -> None:
    """Test basic assumptions about the portfolio data."""

    assert portfolio.name.strip(), "Portfolio name cannot be empty."
    assert portfolio.role.strip(), "Portfolio role cannot be empty."
    assert "@" in portfolio.email, "Portfolio email should contain @."
    assert portfolio.projects, "At least one project is required."
    assert portfolio.skills, "At least one skill is required."

    project_titles = [project.title for project in portfolio.projects]

    assert len(project_titles) == len(set(project_titles)), (
        "Project titles should be unique."
    )

    for project in portfolio.projects:
        assert project.title.strip()
        assert project.description.strip()
        assert project.technologies
        assert project.url.startswith(("http://", "https://"))

    print("Portfolio data tests: PASSED")


def test_generated_pages(pages: dict[str, str]) -> None:
    """Test that every generated page has essential HTML structure."""

    required_files = {
        "index.html",
        "about.html",
        "projects.html",
        "contact.html",
    }

    assert set(pages) == required_files

    for filename, html in pages.items():
        assert "<!doctype html>" in html.lower()
        assert "<html" in html.lower()
        assert "</html>" in html.lower()
        assert "<head>" in html.lower()
        assert "</head>" in html.lower()
        assert "<body>" in html.lower()
        assert "</body>" in html.lower()
        assert "<main" in html.lower()
        assert "</main>" in html.lower()

    print("Generated page tests: PASSED")


# =============================================================================
# 15. EDUCATIONAL COMPARISONS
# =============================================================================

def demonstrate_semantic_vs_nonsemantic() -> None:
    """
    Show the conceptual difference between semantic and generic containers.

    Non-semantic markup:

        <div class="header">...</div>

    Semantic markup:

        <header>...</header>

    A class name may describe meaning to developers, but the browser and
    assistive technologies do not receive the same semantic information from
    a generic <div>.

    The distinction does not mean <div> is bad. It means <div> should be used
    when no more appropriate semantic element exists.
    """

    nonsemantic = """
    <div class="header">
        <div class="navigation">
            ...
        </div>
    </div>
    """

    semantic = """
    <header>
        <nav aria-label="Primary navigation">
            ...
        </nav>
    </header>
    """

    print("\n=== Semantic vs generic markup ===")
    print("Generic structure:")
    print(nonsemantic)
    print("Semantic structure:")
    print(semantic)


def demonstrate_article_vs_section() -> None:
    """
    Explain a subtle semantic distinction.

    <article>:
        Represents self-contained content that could be distributed or reused
        independently.

    <section>:
        Represents a thematic grouping within a document, normally with a
        heading.

    A project card can be an article because it represents a self-contained
    project. A group of project cards can be a section because the group has
    a shared theme.
    """

    article_example = """
    <article>
        <h2>Advanced Calculator</h2>
        <p>A self-contained project description.</p>
    </article>
    """

    section_example = """
    <section>
        <h2>Featured projects</h2>
        <article>...</article>
        <article>...</article>
    </section>
    """

    print("\n=== Article vs section ===")
    print(article_example)
    print(section_example)


def demonstrate_nav_vs_list() -> None:
    """
    Explain why navigation commonly contains a list.

    <nav> identifies a navigation landmark.

    <ul> represents an unordered collection.

    <li> represents each list item.

    <a> provides the actual destination.

    These elements have different responsibilities and can be combined.
    """

    example = """
    <nav aria-label="Primary navigation">
        <ul>
            <li><a href="index.html">Home</a></li>
            <li><a href="projects.html">Projects</a></li>
        </ul>
    </nav>
    """

    print("\n=== Navigation structure ===")
    print(example)


# =============================================================================
# 16. EDGE CASES AND COMMON HTML MISTAKES
# =============================================================================

def demonstrate_common_mistakes() -> None:
    """
    Print representative mistakes and their preferred alternatives.

    These are deliberately examples rather than generated site content.
    """

    examples = {
        "Using headings only for size": (
            "Mistake: <h4>Large-looking text</h4>\n"
            "Better: use the heading level representing the actual hierarchy "
            "and style it with CSS."
        ),
        "Missing image alternative text": (
            'Mistake: <img src="profile.jpg">\n'
            'Better: <img src="profile.jpg" alt="Professional profile photograph">'
        ),
        "Unlabelled form input": (
            'Mistake: <input type="email" name="email">\n'
            'Better: associate a visible <label> with the input id.'
        ),
        "Using div for everything": (
            "Mistake: represent every region with <div>.\n"
            "Better: use header, nav, main, section, article, aside, and footer "
            "where their semantics match the content."
        ),
        "Broken target blank security": (
            'Mistake: <a target="_blank" href="...">Link</a>\n'
            'Better: use rel="noopener noreferrer" for external links when '
            "opening a new browsing context."
        ),
        "Client-side validation as security": (
            "Mistake: trusting required, pattern, or type validation as a "
            "security boundary.\n"
            "Better: validate all submitted data on the server."
        ),
    }

    print("\n=== Common mistakes ===")

    for name, explanation in examples.items():
        print(f"\n{name}:")
        print(explanation)


# =============================================================================
# 17. SECURITY CONSIDERATIONS
# =============================================================================

def demonstrate_security_principles() -> None:
    """
    Explain security considerations relevant to HTML portfolios.

    The generated site is static, so the major risks are limited compared with
    a database-backed application. The principles remain important when HTML
    becomes part of a larger application.
    """

    principles = [
        "Escape untrusted content before inserting it into HTML.",
        "Validate URLs before rendering links when values are dynamic.",
        "Do not treat browser-side validation as server-side validation.",
        "Use HTTPS in production.",
        "Use appropriate Content Security Policy headers for deployed sites.",
        "Avoid inserting untrusted strings through innerHTML in client-side code.",
        "Use rel=noopener when opening untrusted external destinations in a new tab.",
        "Do not expose secrets, API keys, passwords, or private tokens in HTML.",
        "Validate and sanitize uploaded files on the server if uploads are supported.",
        "Keep third-party scripts to a minimum and understand their trust boundary.",
    ]

    print("\n=== Security principles ===")

    for principle in principles:
        print(f"- {principle}")


# =============================================================================
# 18. PERFORMANCE CONSIDERATIONS
# =============================================================================

def demonstrate_performance_principles() -> None:
    """
    Explain practical performance principles for a static portfolio.
    """

    principles = [
        "Keep HTML concise and structurally meaningful.",
        "Compress images and choose appropriate dimensions.",
        "Use modern image formats when browser support and requirements permit.",
        "Avoid unnecessary JavaScript.",
        "Load only the CSS and scripts actually needed.",
        "Avoid excessive third-party fonts and tracking scripts.",
        "Use browser caching through appropriate production headers.",
        "Prefer system fonts when custom typography is not necessary.",
        "Use lazy loading for below-the-fold images where appropriate.",
        "Test the final production site rather than optimizing only source files.",
    ]

    print("\n=== Performance principles ===")

    for principle in principles:
        print(f"- {principle}")


# =============================================================================
# 19. ACCESSIBILITY PRINCIPLES
# =============================================================================

def demonstrate_accessibility_principles() -> None:
    """
    Demonstrate accessibility concepts relevant to semantic HTML.
    """

    principles = [
        "Declare the document language.",
        "Use a logical heading hierarchy.",
        "Use semantic landmarks.",
        "Provide useful alternative text for meaningful images.",
        "Use empty alt text for genuinely decorative images.",
        "Associate form labels with their controls.",
        "Make keyboard focus visible.",
        "Do not communicate important information through color alone.",
        "Use sufficiently descriptive link text.",
        "Preserve readable text contrast.",
        "Respect reduced-motion preferences where animation is used.",
        "Do not remove keyboard accessibility with inappropriate CSS or JavaScript.",
    ]

    print("\n=== Accessibility principles ===")

    for principle in principles:
        print(f"- {principle}")


# =============================================================================
# 20. SEO-ORIENTED STRUCTURE
# =============================================================================

def demonstrate_seo_structure() -> None:
    """
    Demonstrate basic HTML structures that support discoverability.

    Semantic HTML does not guarantee search ranking. It provides clearer
    document structure, which can help machines interpret page content.
    """

    elements = {
        "<title>": "Provides the document title.",
        "meta description": "Provides a concise description of page content.",
        "<h1>": "Identifies the primary heading of the page.",
        "<h2>/<h3>": "Organize subordinate content.",
        "<main>": "Identifies primary page content.",
        "<nav>": "Identifies important navigation.",
        "<article>": "Identifies self-contained content.",
        "<time>": "Can provide machine-readable temporal information.",
        "canonical link": "Helps identify the preferred URL representation.",
    }

    print("\n=== SEO-oriented HTML structure ===")

    for element, purpose in elements.items():
        print(f"{element}: {purpose}")


# =============================================================================
# 21. COMPLETE VALIDATION REPORT
# =============================================================================

def validate_site(pages: dict[str, str]) -> list[ValidationIssue]:
    """
    Validate every generated page.

    The returned list is intentionally separate from printing so the function
    can be reused in automated tests or CI workflows.
    """

    all_issues: list[ValidationIssue] = []
    known_files = set(pages.keys())

    for filename, html in pages.items():
        all_issues.extend(
            validate_html_structure(
                html,
                filename,
            )
        )

        all_issues.extend(
            check_heading_hierarchy(
                html,
                filename,
            )
        )

        all_issues.extend(
            validate_internal_links(
                html,
                filename,
                known_files,
            )
        )

    return all_issues


def print_validation_report(issues: list[ValidationIssue]) -> None:
    """Print a human-readable validation report."""

    print("\n=== Validation report ===")

    if not issues:
        print("No educational validation issues found.")
        return

    for issue in issues:
        print(f"[{issue.severity.upper()}] {issue.message}")


# =============================================================================
# 22. FILE TREE
# =============================================================================

def print_expected_file_tree() -> None:
    """
    Explain the generated multi-page architecture.
    """

    tree = """
semantic_portfolio_site/
├── index.html
├── about.html
├── projects.html
├── contact.html
└── assets/
    └── styles.css
"""

    print("\n=== Generated file tree ===")
    print(tree)


# =============================================================================
# 23. ADVANCED DESIGN DISCUSSION
# =============================================================================

def demonstrate_advanced_design_concepts() -> None:
    """
    Print advanced implementation considerations.

    These principles become increasingly important when a portfolio grows from
    a small personal site into a production website.
    """

    concepts = [
        (
            "Separation of concerns",
            "HTML describes structure and meaning; CSS describes presentation; "
            "JavaScript handles behavior when behavior is actually required."
        ),
        (
            "Progressive enhancement",
            "The essential portfolio content and navigation should remain usable "
            "without depending on JavaScript."
        ),
        (
            "Reusable content models",
            "Portfolio information can be stored as structured data and rendered "
            "consistently instead of duplicating content manually."
        ),
        (
            "Component boundaries",
            "Header, navigation, project cards, forms, and footer can be treated "
            "as reusable conceptual components."
        ),
        (
            "Accessibility-first structure",
            "Correct semantics should be established before visual styling is "
            "used to imitate meaning."
        ),
        (
            "Static-site architecture",
            "A portfolio can be deployed as static HTML and CSS when dynamic "
            "server behavior is unnecessary."
        ),
        (
            "Server-side integration",
            "If contact forms become functional, the browser should submit data "
            "to a secure backend that validates and processes it."
        ),
        (
            "Content management",
            "A larger portfolio may store project information in a CMS or "
            "database while preserving the same semantic output structure."
        ),
    ]

    print("\n=== Advanced design concepts ===")

    for concept, explanation in concepts:
        print(f"\n{concept}:")
        print(explanation)


# =============================================================================
# 24. PRACTICAL PAGE-BY-PAGE ANALYSIS
# =============================================================================

def analyze_pages(pages: dict[str, str]) -> None:
    """
    Report important semantic features used by each generated page.
    """

    print("\n=== Page analysis ===")

    for filename, html in pages.items():
        print(f"\n{filename}")
        print(f"  header:   {count_tag(html, 'header')}")
        print(f"  nav:      {count_tag(html, 'nav')}")
        print(f"  main:     {count_tag(html, 'main')}")
        print(f"  section:  {count_tag(html, 'section')}")
        print(f"  article:  {count_tag(html, 'article')}")
        print(f"  aside:    {count_tag(html, 'aside')}")
        print(f"  footer:   {count_tag(html, 'footer')}")
        print(f"  headings: {sum(count_tag(html, f'h{i}') for i in range(1, 7))}")
        print(f"  links:    {count_tag(html, 'a')}")
        print(f"  forms:    {count_tag(html, 'form')}")


# =============================================================================
# 25. DEMONSTRATING EDGE CASES
# =============================================================================

def demonstrate_edge_cases() -> None:
    """
    Demonstrate subtle cases that commonly affect portfolio HTML.
    """

    print("\n=== Important edge cases ===")

    edge_cases = [
        (
            "Decorative image",
            'A purely decorative image can use alt="". Do not put meaningless '
            "descriptions into alt text merely to satisfy a checklist."
        ),
        (
            "Informative image",
            "An image that communicates information needs alternative text "
            "that conveys its useful meaning."
        ),
        (
            "External link",
            "A new-tab external link should be treated as a separate trust "
            "boundary and should use appropriate rel attributes."
        ),
        (
            "mailto link",
            "mailto: links open the user's configured email application. "
            "They do not provide a server-side contact form."
        ),
        (
            "Single-page versus multi-page",
            "A multi-page site uses separate HTML documents. A single-page "
            "application can update views dynamically but has different routing "
            "and accessibility considerations."
        ),
        (
            "Empty section",
            "A section normally benefits from a heading. If a grouping has no "
            "meaningful heading or thematic purpose, a generic container may "
            "be more appropriate."
        ),
        (
            "Button versus link",
            "Use a link to navigate. Use a button to perform an action."
        ),
        (
            "Div versus section",
            "Use section when the content forms a meaningful thematic group. "
            "Use div when no semantic element is appropriate."
        ),
        (
            "Form validation",
            "required and input types improve browser validation and usability, "
            "but submitted values still require server-side validation."
        ),
    ]

    for title, explanation in edge_cases:
        print(f"\n{title}:")
        print(explanation)


# =============================================================================
# 26. MINI SEMANTIC HTML REFERENCE
# =============================================================================

def print_semantic_reference() -> None:
    """
    Print a compact reference of the major elements used in this project.
    """

    reference = [
        ("html", "Root element of an HTML document."),
        ("head", "Metadata and document configuration."),
        ("title", "Document title."),
        ("meta", "Metadata such as charset and viewport."),
        ("body", "Visible document content."),
        ("header", "Introductory or navigational content."),
        ("nav", "Major navigation block."),
        ("main", "Primary content of the document."),
        ("section", "Thematic grouping of content."),
        ("article", "Self-contained content."),
        ("aside", "Complementary content."),
        ("footer", "Footer information for a document or section."),
        ("h1-h6", "Heading hierarchy."),
        ("p", "Paragraph."),
        ("a", "Hyperlink."),
        ("ul", "Unordered list."),
        ("ol", "Ordered list."),
        ("li", "List item."),
        ("form", "Form submission region."),
        ("label", "Accessible name for a form control."),
        ("input", "Single-line or specialized form control."),
        ("textarea", "Multi-line text control."),
        ("button", "Action control."),
        ("address", "Contact information for the relevant content."),
        ("time", "Date or time information."),
    ]

    print("\n=== Semantic HTML reference ===")

    for element, meaning in reference:
        print(f"<{element}>: {meaning}")


# =============================================================================
# 27. MAIN PROGRAM
# =============================================================================

def main() -> None:
    """
    Run the complete educational demonstration and generate the website.
    """

    print("=" * 72)
    print("SEMANTIC HTML MULTI-PAGE PORTFOLIO STUDY PROJECT")
    print("=" * 72)

    demonstrate_html_fundamentals()

    demonstrate_semantic_vs_nonsemantic()
    demonstrate_article_vs_section()
    demonstrate_nav_vs_list()

    demonstrate_common_mistakes()
    demonstrate_security_principles()
    demonstrate_performance_principles()
    demonstrate_accessibility_principles()
    demonstrate_seo_structure()
    demonstrate_advanced_design_concepts()
    demonstrate_edge_cases()
    print_semantic_reference()

    test_portfolio_data(PORTFOLIO)

    pages = build_pages(PORTFOLIO)

    test_generated_pages(pages)

    issues = validate_site(pages)
    print_validation_report(issues)

    output_directory = Path("semantic_portfolio_site")

    write_site(
        output_directory=output_directory,
        pages=pages,
    )

    analyze_pages(pages)
    print_expected_file_tree()

    print("\n=== Generation complete ===")
    print(f"Website directory: {output_directory.resolve()}")
    print(f"Home page: {(output_directory / 'index.html').resolve()}")

    if issues:
        print(
            "\nThe site was generated, but the educational validator reported "
            f"{len(issues)} issue(s)."
        )
    else:
        print(
            "\nThe generated pages passed all educational structural checks."
        )


if __name__ == "__main__":
    main()
