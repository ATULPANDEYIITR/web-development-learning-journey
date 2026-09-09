"""
Multimedia HTML: Images, Audio, Video, iframe, Responsive Images,
figure/figcaption, and Media Attributes

A self-contained study script for learning HTML multimedia from absolute
beginner through advanced concepts.

The examples are represented as Python strings so this file can be executed
without external packages. The script prints explanations, source examples,
comparisons, validation results, and progressively advanced HTML patterns.

Run:
    python multimedia_html.py
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Iterable, Optional
import re


# =============================================================================
# 1. LEARNING UTILITIES
# =============================================================================

def print_title(title: str) -> None:
    """Print a consistent section heading."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_subtitle(title: str) -> None:
    """Print a subsection heading."""
    print("\n" + "-" * 80)
    print(title)
    print("-" * 80)


def show_code(code: str) -> None:
    """Display an HTML example without requiring Markdown code fences."""
    print(code.strip())


def explain(text: str) -> None:
    """Print educational text."""
    print(text.strip())


# =============================================================================
# 2. FUNDAMENTAL HTML MULTIMEDIA CONCEPTS
# =============================================================================

def fundamentals() -> None:
    print_title("1. HTML MULTIMEDIA FUNDAMENTALS")

    explain(
        """
HTML multimedia means embedding or presenting visual and audio content in a
web document. The principal HTML elements covered in this study file are:

    <img>       Images
    <audio>     Audio playback
    <video>     Video playback
    <iframe>    Embedded external browsing content
    <figure>    Self-contained media/content unit
    <figcaption>Caption associated with a figure
    <picture>   Responsive and art-directed image selection
    <source>    Alternative media/image sources

Multimedia is not just about displaying a file. A production-quality
implementation must also consider semantics, accessibility, performance,
responsive behavior, browser compatibility, security, loading strategy,
fallbacks, and user experience.

HTML multimedia generally follows this model:

    HTML element
        |
        +-- Resource URL
        |
        +-- Attributes controlling behavior
        |
        +-- Optional fallback/source elements
        |
        +-- Accessibility metadata
        |
        +-- CSS for presentation and responsive layout
        """
    )


# =============================================================================
# 3. IMAGE BASICS
# =============================================================================

def image_basics() -> None:
    print_title("2. IMAGES WITH <img>")

    explain(
        """
The <img> element embeds an image resource into a document.

Important attributes include:

    src          The image URL or path.
    alt          Alternative text for accessibility.
    width        Intended rendered width.
    height       Intended rendered height.
    loading      Loading strategy such as lazy or eager.
    decoding     Image decoding hint.
    fetchpriority Resource priority hint.
    srcset       Multiple image candidates.
    sizes        Conditions describing the intended display size.
    crossorigin  Cross-origin loading behavior.
    referrerpolicy Controls referrer information.

Unlike many HTML elements, <img> is a void element. It does not require a
closing </img> tag.
        """
    )

    print_subtitle("Basic image")
    show_code(
        """
<img src="images/mountain.jpg"
     alt="Snow-covered mountain beneath a clear blue sky">
        """
    )

    print_subtitle("Image with intrinsic dimensions")
    show_code(
        """
<img src="images/product.jpg"
     alt="Black wireless headphones"
     width="800"
     height="600">
        """
    )

    print_subtitle("Why width and height matter")
    explain(
        """
Supplying width and height allows the browser to reserve layout space before
the image finishes loading. This can reduce layout movement.

The dimensions should describe the image's intrinsic aspect ratio. CSS may
still scale the image responsively.
        """
    )

    show_code(
        """
<img src="images/landscape.jpg"
     alt="Landscape photograph"
     width="1600"
     height="900"
     style="max-width: 100%; height: auto;">
        """
    )


# =============================================================================
# 4. ALT TEXT
# =============================================================================

def alt_text() -> None:
    print_title("3. ALT TEXT AND IMAGE ACCESSIBILITY")

    explain(
        """
The alt attribute provides a textual alternative to an image.

The correct value depends on the image's purpose.

Informative image:
    Describe the meaningful information conveyed by the image.

Decorative image:
    Use alt="" when the image adds no meaningful information and should be
    ignored by assistive technologies.

Functional image:
    Describe the action or destination rather than merely describing the
    pixels.

Text embedded in an image:
    If the text conveys important information, the alternative should preserve
    that meaning where appropriate.

Avoid meaningless values such as:
    alt="image"
    alt="picture"
    alt="photo"

The alt attribute is not a tooltip and should not be used to repeat an
adjacent caption unnecessarily.
        """
    )

    examples = {
        "informative": """
<img src="sales-chart.png"
     alt="Sales increased from 40,000 units in January to 65,000 in June.">
""",
        "decorative": """
<img src="decorative-divider.svg" alt="">
""",
        "functional": """
<a href="/search">
    <img src="search.svg" alt="Search">
</a>
""",
    }

    for name, code in examples.items():
        print_subtitle(name.title())
        show_code(code)


# =============================================================================
# 5. AUDIO
# =============================================================================

def audio_basics() -> None:
    print_title("4. AUDIO WITH <audio>")

    explain(
        """
The <audio> element provides native audio playback.

Common attributes:

    controls     Displays browser playback controls.
    autoplay     Requests automatic playback.
    loop         Repeats playback.
    muted        Starts muted.
    preload      Indicates how much resource loading is desired.
    crossorigin  Controls cross-origin resource behavior.

A basic implementation should normally provide controls.
        """
    )

    print_subtitle("Basic audio")
    show_code(
        """
<audio controls>
    <source src="audio/interview.mp3" type="audio/mpeg">
    Your browser does not support HTML audio.
</audio>
        """
    )

    print_subtitle("Multiple audio formats")
    show_code(
        """
<audio controls preload="metadata">
    <source src="audio/interview.ogg" type="audio/ogg">
    <source src="audio/interview.mp3" type="audio/mpeg">
    Your browser does not support HTML audio.
</audio>
        """
    )

    explain(
        """
The <source> elements provide alternative resources. The browser can choose
a supported source.

Common audio formats include:

    MP3   Broad compatibility and practical general-purpose delivery.
    Ogg   Open format with good browser support but not universal coverage.
    WAV   Usually large and more suitable for high-quality/raw audio workflows.
    AAC   Common in many media ecosystems and containers.

The appropriate choice depends on browser requirements, quality, encoding,
bandwidth, and distribution architecture.
        """
    )


# =============================================================================
# 6. AUDIO ATTRIBUTES
# =============================================================================

def audio_attributes() -> None:
    print_title("5. AUDIO ATTRIBUTES IN DETAIL")

    attributes = {
        "controls": """
<audio controls src="audio/podcast.mp3"></audio>
""",
        "loop": """
<audio controls loop src="audio/background.mp3"></audio>
""",
        "muted": """
<audio controls muted src="audio/preview.mp3"></audio>
""",
        "preload metadata": """
<audio controls preload="metadata" src="audio/lecture.mp3"></audio>
""",
        "preload none": """
<audio controls preload="none" src="audio/lecture.mp3"></audio>
""",
    }

    for label, code in attributes.items():
        print_subtitle(label)
        show_code(code)

    explain(
        """
preload is a hint, not an absolute command. Its purpose is to communicate
loading preference to the user agent.

For large audio resources, preload="none" can avoid unnecessary downloads.
For interfaces where duration or metadata should be available early,
preload="metadata" can be useful.

autoplay requires particular care because browsers may restrict unsolicited
media playback, especially when audio is audible. Do not design critical
functionality around guaranteed autoplay.
        """
    )


# =============================================================================
# 7. VIDEO
# =============================================================================

def video_basics() -> None:
    print_title("6. VIDEO WITH <video>")

    explain(
        """
The <video> element provides native video playback.

Important attributes include:

    controls
    autoplay
    muted
    loop
    playsinline
    poster
    preload
    width
    height
    crossorigin

A production video should normally have controls unless the media is purely
background content and the interaction model explicitly does not require
them.
        """
    )

    print_subtitle("Basic video")
    show_code(
        """
<video controls width="1280" height="720">
    <source src="video/course.mp4" type="video/mp4">
    Your browser does not support HTML video.
</video>
        """
    )

    print_subtitle("Video with poster")
    show_code(
        """
<video controls
       width="1280"
       height="720"
       poster="images/course-poster.jpg"
       preload="metadata">
    <source src="video/course.mp4" type="video/mp4">
    Your browser does not support HTML video.
</video>
        """
    )

    print_subtitle("Multiple video sources")
    show_code(
        """
<video controls width="1280" height="720">
    <source src="video/course.webm" type="video/webm">
    <source src="video/course.mp4" type="video/mp4">
    Your browser does not support HTML video.
</video>
        """
    )


# =============================================================================
# 8. VIDEO-SPECIFIC CONCEPTS
# =============================================================================

def video_advanced() -> None:
    print_title("7. ADVANCED VIDEO FEATURES")

    print_subtitle("Autoplay background video")
    show_code(
        """
<video autoplay muted loop playsinline aria-hidden="true">
    <source src="video/background.mp4" type="video/mp4">
</video>
        """
    )

    explain(
        """
A common background-video pattern uses:

    autoplay
    muted
    loop
    playsinline

muted is important because browsers commonly restrict autoplay of audible
media.

playsinline is particularly important for controlling inline playback on
mobile devices.

A decorative background video should not communicate essential information
that is unavailable elsewhere. If it is decorative, its accessibility impact
should be handled accordingly.
        """
    )

    print_subtitle("Video with captions")
    show_code(
        """
<video controls width="1280" height="720">
    <source src="video/lesson.mp4" type="video/mp4">
    <track src="captions/lesson-en.vtt"
           kind="captions"
           srclang="en"
           label="English"
           default>
</video>
        """
    )

    explain(
        """
The <track> element can provide timed text.

Important track attributes:

    kind
        captions, subtitles, descriptions, chapters, or metadata

    src
        Location of the WebVTT file.

    srclang
        Language code.

    label
        Human-readable track name.

    default
        Requests that this track be selected by default.

Captions are particularly important for accessibility and for users who
cannot or do not want to hear audio.
        """
    )


# =============================================================================
# 9. RESPONSIVE IMAGES
# =============================================================================

def responsive_images() -> None:
    print_title("8. RESPONSIVE IMAGES")

    explain(
        """
Responsive images address two related problems:

1. Resolution switching:
   Serve an image with an appropriate pixel density or rendered size.

2. Art direction:
   Use different image crops or compositions at different viewport sizes.

The two main mechanisms are:

    srcset + sizes
    picture + source
        """
    )

    print_subtitle("srcset with width descriptors")
    show_code(
        """
<img src="images/article-800.jpg"
     srcset="
         images/article-400.jpg 400w,
         images/article-800.jpg 800w,
         images/article-1200.jpg 1200w,
         images/article-1600.jpg 1600w"
     sizes="
         (max-width: 600px) 100vw,
         (max-width: 1000px) 80vw,
         1200px"
     alt="Aerial view of a coastal city"
     width="1600"
     height="900">
        """
    )

    explain(
        """
The width descriptors tell the browser the intrinsic candidate widths.

The sizes attribute describes the expected rendered width under viewport
conditions.

Example:

    (max-width: 600px) 100vw

means that when the viewport is at most 600 CSS pixels wide, the image is
expected to occupy approximately the full viewport width.

Without a useful sizes value, the browser may make poorer candidate choices
for width-descriptor srcset implementations.
        """
    )

    print_subtitle("Density descriptors")
    show_code(
        """
<img src="logo.png"
     srcset="logo.png 1x, logo@2x.png 2x"
     alt="Company logo"
     width="200"
     height="80">
        """
    )

    explain(
        """
Density descriptors such as 1x and 2x are appropriate when the candidate
images correspond to device pixel density rather than different responsive
layout widths.

Do not mix width descriptors and density descriptors within the same srcset.
        """
    )


# =============================================================================
# 10. PICTURE AND ART DIRECTION
# =============================================================================

def picture_element() -> None:
    print_title("9. <picture> AND ART DIRECTION")

    explain(
        """
<picture> is a container for multiple image candidates.

It is particularly useful when different viewport conditions require
different crops, compositions, or formats.

The fallback <img> remains essential. The browser uses the <source>
conditions to determine whether an alternative candidate applies.
        """
    )

    print_subtitle("Art-directed image")
    show_code(
        """
<picture>
    <source media="(max-width: 600px)"
            srcset="images/portrait-mobile.jpg">

    <source media="(max-width: 1000px)"
            srcset="images/portrait-tablet.jpg">

    <img src="images/portrait-desktop.jpg"
         alt="Architect standing beside a modern building"
         width="1600"
         height="900">
</picture>
        """
    )

    print_subtitle("Format negotiation")
    show_code(
        """
<picture>
    <source srcset="images/photo.avif" type="image/avif">
    <source srcset="images/photo.webp" type="image/webp">
    <img src="images/photo.jpg"
         alt="Forest landscape"
         width="1600"
         height="900">
</picture>
        """
    )

    explain(
        """
The <picture> pattern can combine media conditions and MIME-type
selection.

The fallback <img> should remain usable because not every browser or
environment supports every modern image format or source condition.
        """
    )


# =============================================================================
# 11. FIGURE AND FIGCAPTION
# =============================================================================

def figure_and_figcaption() -> None:
    print_title("10. <figure> AND <figcaption>")

    explain(
        """
<figure> represents self-contained content that is related to the main
document but can be moved away from the surrounding flow without losing
its meaning.

<figcaption> provides a caption or explanation for the figure.

The content of a figure does not have to be an image. It can also contain
audio, video, diagrams, code, tables, illustrations, or other self-contained
content.
        """
    )

    print_subtitle("Image figure")
    show_code(
        """
<figure>
    <img src="images/architecture.jpg"
         alt="Aerial view of a historic city center"
         width="1200"
         height="800">
    <figcaption>
        Historic city center viewed from above.
    </figcaption>
</figure>
        """
    )

    print_subtitle("Video figure")
    show_code(
        """
<figure>
    <video controls width="1280" height="720">
        <source src="video/demo.mp4" type="video/mp4">
    </video>
    <figcaption>
        Demonstration of the application's dashboard.
    </figcaption>
</figure>
        """
    )

    explain(
        """
A figcaption is semantic content. It should not be confused with an alt
attribute.

alt:
    Alternative representation of an image.

figcaption:
    Visible caption associated with a figure.

They can coexist when each serves a distinct purpose.
        """
    )


# =============================================================================
# 12. IFRAMES
# =============================================================================

def iframe_basics() -> None:
    print_title("11. EMBEDDING CONTENT WITH <iframe>")

    explain(
        """
An iframe creates a nested browsing context inside the current document.

Typical uses include:

    Maps
    Video platforms
    Documents
    Dashboards
    Third-party widgets
    Trusted external applications

Important attributes include:

    src
    title
    width
    height
    loading
    allow
    sandbox
    referrerpolicy

The iframe is fundamentally different from <img>, <audio>, and <video>.
Those elements consume particular media resources, while an iframe embeds
another browsing context.
        """
    )

    print_subtitle("Basic iframe")
    show_code(
        """
<iframe
    src="https://example.com"
    title="Example website"
    width="800"
    height="600">
</iframe>
        """
    )

    print_subtitle("Lazy-loaded iframe")
    show_code(
        """
<iframe
    src="https://example.com"
    title="Embedded documentation"
    width="800"
    height="600"
    loading="lazy">
</iframe>
        """
    )

    explain(
        """
A descriptive title is important for accessibility because users of
assistive technologies need to understand the purpose of the embedded
browsing context.
        """
    )


# =============================================================================
# 13. IFRAME SECURITY
# =============================================================================

def iframe_security() -> None:
    print_title("12. IFRAME SECURITY")

    explain(
        """
Third-party iframe content should be treated as an independent security
boundary.

The sandbox attribute can restrict capabilities of framed content.

A restrictive baseline is:

    sandbox

Specific capabilities can then be granted using tokens when genuinely
required.

Common sandbox tokens include:

    allow-scripts
    allow-forms
    allow-popups
    allow-downloads
    allow-modals
    allow-presentation
    allow-same-origin

Granting permissions increases the iframe's capabilities. The policy should
therefore follow least privilege.

Do not blindly combine permissions merely to make a third-party application
work without understanding what those permissions enable.
        """
    )

    print_subtitle("Sandboxed iframe")
    show_code(
        """
<iframe
    src="https://example.com/widget"
    title="Embedded widget"
    sandbox="allow-scripts"
    loading="lazy">
</iframe>
        """
    )

    print_subtitle("Controlled permissions")
    show_code(
        """
<iframe
    src="https://example.com/video-player"
    title="Course video"
    allow="fullscreen; picture-in-picture"
    sandbox="allow-scripts allow-same-origin"
    loading="lazy">
</iframe>
        """
    )

    explain(
        """
The exact permissions required depend on the embedded application.

Other useful defenses can be applied through HTTP response headers and
Content Security Policy. HTML attributes are only one part of a complete
web security architecture.
        """
    )


# =============================================================================
# 14. MEDIA ATTRIBUTE COMPARISON
# =============================================================================

def media_attribute_comparison() -> None:
    print_title("13. IMPORTANT MEDIA ATTRIBUTES")

    table = [
        ("controls", "img", "audio", "video", "Shows native controls"),
        ("autoplay", "No", "Yes", "Yes", "Requests automatic playback"),
        ("loop", "No", "Yes", "Yes", "Repeats media"),
        ("muted", "No", "Yes", "Yes", "Starts muted"),
        ("preload", "No", "Yes", "Yes", "Loading preference"),
        ("poster", "No", "No", "Yes", "Video preview image"),
        ("playsinline", "No", "No", "Yes", "Requests inline video playback"),
        ("loading", "Yes", "No", "No", "Lazy/eager loading hint for image/iframe"),
    ]

    print(f"{'Attribute':<15} {'img':<8} {'audio':<8} {'video':<8} Purpose")
    print("-" * 80)

    for attribute, image, audio, video, purpose in table:
        print(
            f"{attribute:<15} {image:<8} {audio:<8} "
            f"{video:<8} {purpose}"
        )

    explain(
        """
Not every media element accepts the same attributes. Attribute applicability
must be checked against the element's HTML semantics rather than assuming
that an attribute works everywhere.
        """
    )


# =============================================================================
# 15. PRELOAD, AUTOPLAY, AND USER EXPERIENCE
# =============================================================================

def playback_design() -> None:
    print_title("14. PLAYBACK DESIGN AND LOADING STRATEGY")

    explain(
        """
Media files can be large. A page containing several videos, high-resolution
images, and audio tracks can consume significant bandwidth and memory.

Useful principles:

    1. Do not download media that the user is unlikely to need.
    2. Use lazy loading where appropriate.
    3. Prefer metadata loading for large media when early metadata is useful.
    4. Avoid audible autoplay.
    5. Give users controls for interactive media.
    6. Use responsive image candidates.
    7. Provide suitable dimensions to reduce layout movement.
    8. Compress and encode media appropriately.
    9. Use a poster image when a meaningful video preview improves UX.
    10. Consider mobile bandwidth and device constraints.
        """
    )

    show_code(
        """
<video controls
       preload="metadata"
       poster="images/video-preview.jpg"
       width="1280"
       height="720">
    <source src="video/lesson.mp4" type="video/mp4">
</video>
        """
    )

    show_code(
        """
<img src="images/report.jpg"
     alt="Quarterly sales report"
     width="1600"
     height="900"
     loading="lazy"
     decoding="async">
        """
    )


# =============================================================================
# 16. COMPLETE MULTIMEDIA PAGE
# =============================================================================

def complete_page() -> None:
    print_title("15. COMPLETE MULTIMEDIA PAGE")

    page = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Multimedia Learning Page</title>
</head>
<body>

<header>
    <h1>Multimedia Demonstration</h1>
</header>

<main>
    <section>
        <h2>Responsive Image</h2>

        <figure>
            <picture>
                <source media="(max-width: 600px)"
                        srcset="images/city-mobile.jpg">

                <source srcset="images/city.avif"
                        type="image/avif">

                <img src="images/city.jpg"
                     alt="Modern city skyline at sunset"
                     width="1600"
                     height="900"
                     loading="lazy"
                     decoding="async">
            </picture>

            <figcaption>
                City skyline photographed at sunset.
            </figcaption>
        </figure>
    </section>

    <section>
        <h2>Audio Lesson</h2>

        <audio controls preload="metadata">
            <source src="audio/lesson.ogg" type="audio/ogg">
            <source src="audio/lesson.mp3" type="audio/mpeg">
            Your browser does not support HTML audio.
        </audio>
    </section>

    <section>
        <h2>Video Lesson</h2>

        <figure>
            <video controls
                   preload="metadata"
                   poster="images/lesson-poster.jpg"
                   width="1280"
                   height="720"
                   playsinline>
                <source src="video/lesson.webm" type="video/webm">
                <source src="video/lesson.mp4" type="video/mp4">

                <track src="captions/lesson-en.vtt"
                       kind="captions"
                       srclang="en"
                       label="English"
                       default>

                Your browser does not support HTML video.
            </video>

            <figcaption>
                Introduction to the multimedia lesson.
            </figcaption>
        </figure>
    </section>

    <section>
        <h2>External Content</h2>

        <iframe
            src="https://example.com"
            title="Example external resource"
            width="800"
            height="600"
            loading="lazy"
            referrerpolicy="strict-origin-when-cross-origin"
            sandbox="allow-scripts">
        </iframe>
    </section>
</main>

</body>
</html>
"""

    show_code(page)


# =============================================================================
# 17. PYTHON-BASED HTML GENERATION
# =============================================================================

def safe_image_tag(
    src: str,
    alt: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> str:
    """
    Generate an image element while escaping attribute values.

    This demonstrates a basic security principle: never insert untrusted
    strings into HTML without appropriate escaping.
    """
    attributes = [
        f'src="{escape(src, quote=True)}"',
        f'alt="{escape(alt, quote=True)}"',
    ]

    if width is not None:
        attributes.append(f'width="{int(width)}"')

    if height is not None:
        attributes.append(f'height="{int(height)}"')

    return "<img " + " ".join(attributes) + ">"


def html_generation_demo() -> None:
    print_title("16. PROGRAMMATIC HTML GENERATION")

    explain(
        """
HTML is often generated by server-side applications or templating systems.
The important security rule is that external input must not be inserted into
HTML without context-appropriate escaping or trusted templating mechanisms.
        """
    )

    print_subtitle("Safe generated image")
    generated = safe_image_tag(
        'images/profile.jpg',
        'User profile photo',
        400,
        400,
    )
    show_code(generated)

    print_subtitle("Escaping hostile attribute input")
    hostile_filename = '" onerror="alert(1)'
    safe_result = safe_image_tag(
        hostile_filename,
        "Example image",
    )
    show_code(safe_result)


# =============================================================================
# 18. MEDIA MODEL
# =============================================================================

@dataclass
class MediaAsset:
    """Represent a multimedia asset for educational HTML generation."""

    url: str
    media_type: str
    title: str
    alt_text: str = ""
    width: Optional[int] = None
    height: Optional[int] = None

    def validate(self) -> list[str]:
        """Return validation errors for common media metadata issues."""
        errors: list[str] = []

        if not self.url.strip():
            errors.append("URL cannot be empty.")

        allowed_types = {"image", "audio", "video", "iframe"}

        if self.media_type not in allowed_types:
            errors.append(
                f"Unsupported media type: {self.media_type!r}."
            )

        if self.media_type == "image" and not self.alt_text:
            errors.append(
                "Images should have meaningful alt text or explicitly use "
                "an empty alt attribute when decorative."
            )

        if self.width is not None and self.width <= 0:
            errors.append("Width must be positive.")

        if self.height is not None and self.height <= 0:
            errors.append("Height must be positive.")

        return errors


def media_validation_demo() -> None:
    print_title("17. MEDIA VALIDATION")

    assets = [
        MediaAsset(
            url="images/logo.svg",
            media_type="image",
            title="Company logo",
            alt_text="Company logo",
            width=240,
            height=80,
        ),
        MediaAsset(
            url="",
            media_type="image",
            title="Missing image",
        ),
        MediaAsset(
            url="video/demo.mp4",
            media_type="video",
            title="Demo video",
            width=1280,
            height=720,
        ),
        MediaAsset(
            url="data.bin",
            media_type="unknown",
            title="Unknown asset",
        ),
    ]

    for asset in assets:
        print(f"\nAsset: {asset.title}")
        errors = asset.validate()

        if errors:
            for error in errors:
                print(f"  ERROR: {error}")
        else:
            print("  VALID")


# =============================================================================
# 19. RESPONSIVE IMAGE CANDIDATE MODEL
# =============================================================================

@dataclass(frozen=True)
class ImageCandidate:
    """Represent one responsive image candidate."""

    url: str
    width: int

    def __post_init__(self) -> None:
        if self.width <= 0:
            raise ValueError("Candidate width must be positive.")

        if not self.url.strip():
            raise ValueError("Candidate URL cannot be empty.")


def sort_candidates(candidates: Iterable[ImageCandidate]) -> list[ImageCandidate]:
    """Sort responsive image candidates from smallest to largest."""
    return sorted(candidates, key=lambda candidate: candidate.width)


def generate_srcset(candidates: Iterable[ImageCandidate]) -> str:
    """Generate a width-descriptor srcset."""
    sorted_candidates = sort_candidates(candidates)

    return ", ".join(
        f"{escape(candidate.url, quote=True)} {candidate.width}w"
        for candidate in sorted_candidates
    )


def responsive_image_demo() -> None:
    print_title("18. RESPONSIVE IMAGE GENERATION")

    candidates = [
        ImageCandidate("images/article-1600.jpg", 1600),
        ImageCandidate("images/article-400.jpg", 400),
        ImageCandidate("images/article-800.jpg", 800),
        ImageCandidate("images/article-1200.jpg", 1200),
    ]

    srcset = generate_srcset(candidates)

    show_code(
        f"""
<img src="images/article-800.jpg"
     srcset="{srcset}"
     sizes="(max-width: 700px) 100vw, 800px"
     alt="Researchers examining a scientific instrument"
     width="1600"
     height="900">
        """
    )


# =============================================================================
# 20. COMMON MISTAKES
# =============================================================================

def common_mistakes() -> None:
    print_title("19. COMMON MISTAKES")

    mistakes = [
        (
            "Missing alt text",
            """
<img src="product.jpg">
""",
            """
<img src="product.jpg" alt="Black wireless headphones">
""",
        ),
        (
            "Using alt as a caption",
            """
<img src="mountain.jpg"
     alt="Beautiful mountain photograph showing a beautiful mountain">
""",
            """
<figure>
    <img src="mountain.jpg"
         alt="Snow-covered mountain above a valley">
    <figcaption>View from the northern trail.</figcaption>
</figure>
""",
        ),
        (
            "Uncontrolled autoplay",
            """
<video autoplay src="video.mp4"></video>
""",
            """
<video controls preload="metadata">
    <source src="video.mp4" type="video/mp4">
</video>
""",
        ),
        (
            "Ignoring responsive images",
            """
<img src="large-4000px.jpg" alt="City skyline">
""",
            """
<img src="city-800.jpg"
     srcset="city-400.jpg 400w,
             city-800.jpg 800w,
             city-1600.jpg 1600w"
     sizes="100vw"
     alt="City skyline">
""",
        ),
        (
            "Iframe without title",
            """
<iframe src="https://example.com"></iframe>
""",
            """
<iframe
    src="https://example.com"
    title="External documentation">
</iframe>
""",
        ),
    ]

    for name, bad, good in mistakes:
        print_subtitle(name)
        print("Problematic:")
        show_code(bad)
        print("Improved:")
        show_code(good)


# =============================================================================
# 21. EDGE CASES
# =============================================================================

def edge_cases() -> None:
    print_title("20. EDGE CASES AND SUBTLE BEHAVIOR")

    explain(
        """
Edge case 1: Decorative image
    If an image is purely decorative, alt="" is generally preferable to a
    meaningless description.

Edge case 2: Image containing important text
    Important information should not be made inaccessible merely because it
    exists inside a raster image.

Edge case 3: Image used as a link
    The alternative text should communicate the link's purpose.

Edge case 4: Responsive image with incorrect sizes
    An inaccurate sizes value can lead to a poor candidate choice and
    unnecessary bandwidth consumption.

Edge case 5: Missing media fallback
    A media element can fail because of unsupported codecs, network failure,
    or unavailable resources. Meaningful fallback content is valuable.

Edge case 6: Autoplay restrictions
    Autoplay is subject to browser policy and user preferences. Audible
    autoplay should never be assumed.

Edge case 7: Cross-origin media
    Some operations involving media can require appropriate CORS response
    headers. The crossorigin attribute alone does not grant permission.

Edge case 8: Third-party iframe
    The embedded origin is different from the parent document. Permissions,
    isolation, privacy, and security need explicit consideration.

Edge case 9: Very large media
    A technically valid resource can still produce a poor user experience
    because of bandwidth, memory, decoding cost, or startup delay.

Edge case 10: Missing dimensions
    Images without dimensions can contribute to layout instability while the
    browser waits for intrinsic information.
        """
    )


# =============================================================================
# 22. PERFORMANCE CONSIDERATIONS
# =============================================================================

def performance() -> None:
    print_title("21. PERFORMANCE CONSIDERATIONS")

    explain(
        """
Image performance:

    Use appropriate dimensions.
    Use responsive image candidates.
    Compress images.
    Prefer modern formats where browser support and fallback strategy permit.
    Lazy-load below-the-fold images.
    Avoid unnecessarily huge source files.
    Reserve layout space with dimensions or an equivalent CSS strategy.

Audio and video performance:

    Use appropriate codecs and bitrates.
    Avoid loading large media before it is needed.
    Consider preload behavior.
    Use streaming or adaptive delivery for large-scale media systems where
    appropriate.
    Provide poster images for videos where useful.

Iframe performance:

    Lazy-load noncritical iframes.
    Avoid embedding unnecessary third-party applications.
    Limit the number of independently loaded browsing contexts.

A media optimization strategy should balance:

    visual/audio quality
    bandwidth
    decoding cost
    storage
    startup latency
    browser support
    accessibility
    cacheability
        """
    )

    print_subtitle("Performance-oriented image")
    show_code(
        """
<img src="images/article-800.webp"
     srcset="
         images/article-400.webp 400w,
         images/article-800.webp 800w,
         images/article-1200.webp 1200w"
     sizes="(max-width: 700px) 100vw, 800px"
     alt="Researchers working in a laboratory"
     width="1200"
     height="800"
     loading="lazy"
     decoding="async">
        """
    )


# =============================================================================
# 23. ACCESSIBILITY
# =============================================================================

def accessibility() -> None:
    print_title("22. ACCESSIBILITY BEST PRACTICES")

    explain(
        """
Images:

    Provide meaningful alt text when the image conveys information.
    Use alt="" for decorative images.
    Do not put essential information only in an image.
    Use visible captions when a figure needs explanatory context.

Audio:

    Provide controls.
    Consider transcripts.
    Do not depend on sound alone to communicate essential information.

Video:

    Provide controls.
    Provide captions for spoken content.
    Consider audio descriptions when visual information is essential.
    Avoid inaccessible autoplay behavior.
    Ensure keyboard operation is possible through the browser/player controls.

Iframes:

    Provide a descriptive title.
    Avoid embedding unnecessary content.
    Consider keyboard and focus behavior of the embedded application.

Accessibility is not a single attribute. It is the combination of semantic
markup, alternative representations, operability, understandable controls,
and equivalent access to information.
        """
    )


# =============================================================================
# 24. SECURITY CONSIDERATIONS
# =============================================================================

def security() -> None:
    print_title("23. SECURITY CONSIDERATIONS")

    explain(
        """
HTML multimedia introduces several security considerations.

1. Untrusted URLs
   Do not blindly accept arbitrary URLs for embedded content.

2. HTML injection
   Do not concatenate untrusted input directly into HTML. Use safe templating
   or appropriate escaping.

3. Third-party iframes
   Treat embedded applications as untrusted boundaries unless their trust
   relationship is explicitly established.

4. iframe sandbox
   Restrict iframe capabilities where practical.

5. Permissions
   The iframe allow attribute should grant only required capabilities.

6. Content Security Policy
   CSP can restrict where scripts, frames, images, media, and other resources
   can originate.

7. Cross-origin behavior
   CORS policies determine whether certain cross-origin operations are
   permitted. Cross-origin resources are not automatically trusted.

8. Privacy
   Third-party media and embeds can introduce external requests and tracking
   implications.

9. Malicious media
   Media processing occurs in complex software stacks. Keep server-side
   media processing components appropriately maintained and isolate
   untrusted uploads.

The browser's security model is broader than HTML alone. HTTP headers,
origin isolation, server-side validation, and application architecture all
matter.
        """
    )


# =============================================================================
# 25. COMPARISONS
# =============================================================================

def comparisons() -> None:
    print_title("24. IMPORTANT DISTINCTIONS")

    print_subtitle("<img> vs <picture>")
    explain(
        """
<img>
    Displays an image resource and can use srcset/sizes for candidate
    selection.

<picture>
    Provides conditional source selection and is especially useful for
    art direction and format switching.

<picture> normally contains an <img> fallback.
        """
    )

    print_subtitle("<figure> vs ordinary container")
    explain(
        """
<figure>
    Semantic representation of self-contained content.

<div>
    Generic container without the same semantic meaning.

Use <figure> when the content forms a self-contained figure-like unit.
        """
    )

    print_subtitle("<iframe> vs <video>")
    explain(
        """
<iframe>
    Embeds another browsing context.

<video>
    Plays video media natively within the document.

An embedded video platform may use an iframe, while a locally hosted video
can use the native <video> element.
        """
    )

    print_subtitle("alt vs figcaption")
    explain(
        """
alt
    Alternative textual representation of an image.

figcaption
    Visible caption associated with a figure.

They answer different questions and should not automatically replace one
another.
        """
    )


# =============================================================================
# 26. MEDIA URL AND ATTRIBUTE VALIDATION
# =============================================================================

def validate_media_url(url: str) -> list[str]:
    """Perform conservative validation of a media URL."""
    errors: list[str] = []

    if not url.strip():
        return ["URL is empty."]

    if any(character in url for character in "\r\n"):
        errors.append("URL must not contain newline characters.")

    scheme_match = re.match(r"^([a-zA-Z][a-zA-Z0-9+.-]*):", url)

    if scheme_match:
        scheme = scheme_match.group(1).lower()

        if scheme not in {"https", "http"}:
            errors.append(
                f"Unexpected URL scheme: {scheme!r}."
            )
    elif not url.startswith(("/", "./", "../")):
        errors.append(
            "URL should be absolute HTTP(S) or a recognized relative path."
        )

    return errors


def url_validation_demo() -> None:
    print_title("25. BASIC MEDIA URL VALIDATION")

    urls = [
        "https://example.com/image.jpg",
        "/images/photo.webp",
        "../media/video.mp4",
        "javascript:alert(1)",
        "",
        "https://example.com/a\nb.jpg",
    ]

    for url in urls:
        errors = validate_media_url(url)

        print(f"\nURL: {url!r}")

        if errors:
            for error in errors:
                print(f"  ERROR: {error}")
        else:
            print("  VALID")


# =============================================================================
# 27. TESTS
# =============================================================================

def run_tests() -> None:
    print_title("26. EXECUTABLE TESTS")

    candidate_list = [
        ImageCandidate("small.jpg", 400),
        ImageCandidate("large.jpg", 1600),
        ImageCandidate("medium.jpg", 800),
    ]

    assert [c.width for c in sort_candidates(candidate_list)] == [
        400,
        800,
        1600,
    ]

    srcset = generate_srcset(candidate_list)

    assert "small.jpg 400w" in srcset
    assert "medium.jpg 800w" in srcset
    assert "large.jpg 1600w" in srcset

    escaped = safe_image_tag(
        'photo" onerror="alert(1)',
        'A "quoted" image',
    )

    assert "&quot;" in escaped
    assert "<img" in escaped

    valid_asset = MediaAsset(
        url="photo.jpg",
        media_type="image",
        title="Photo",
        alt_text="A photo",
    )

    assert valid_asset.validate() == []

    invalid_asset = MediaAsset(
        url="",
        media_type="unknown",
        title="Invalid",
    )

    errors = invalid_asset.validate()

    assert "URL cannot be empty." in errors
    assert "Unsupported media type: 'unknown'." in errors
    assert any("alt text" in error for error in errors)

    assert validate_media_url("https://example.com/a.jpg") == []
    assert validate_media_url("javascript:alert(1)")
    assert validate_media_url("https://example.com/a\nb.jpg")

    print("All tests passed.")


# =============================================================================
# 28. PRODUCTION CHECKLIST
# =============================================================================

def production_checklist() -> None:
    print_title("27. PRODUCTION CHECKLIST")

    checklist = [
        "Images have meaningful alt text or explicitly use alt=\"\" when decorative.",
        "Important image information is not inaccessible because it exists only in pixels.",
        "Width and height or an equivalent layout-reservation strategy is used where appropriate.",
        "Responsive images use suitable srcset and sizes values when beneficial.",
        "Art direction uses picture when different crops/compositions are required.",
        "Modern image formats have suitable fallbacks where compatibility requires them.",
        "Audio has usable controls when user interaction is expected.",
        "Video has controls unless the UX intentionally uses a noninteractive decorative pattern.",
        "Captions are supplied for video content where needed.",
        "Autoplay is not treated as guaranteed behavior.",
        "Background video is muted when autoplay is intentionally used.",
        "Large media uses an appropriate loading strategy.",
        "Noncritical iframes use lazy loading when beneficial.",
        "Iframes have descriptive titles.",
        "Third-party iframes receive only necessary permissions.",
        "Sandboxing is considered for untrusted embedded applications.",
        "Untrusted values are not concatenated directly into HTML.",
        "Content Security Policy and HTTP security controls are considered.",
        "Media resources are optimized for bandwidth and device capability.",
        "Fallback content is considered for media failures and unsupported formats.",
    ]

    for number, item in enumerate(checklist, start=1):
        print(f"[ ] {number:02d}. {item}")


# =============================================================================
# 29. MINI PROJECT
# =============================================================================

def mini_project() -> None:
    print_title("28. INTEGRATED MINI PROJECT")

    explain(
        """
The following example combines the major concepts into one educational
course-media page. It includes responsive images, figure/figcaption, audio,
video, captions, and a controlled iframe.
        """
    )

    project = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>Course Multimedia</title>

    <style>
        img,
        video {
            max-width: 100%;
            height: auto;
        }

        figure {
            margin: 0 0 2rem;
        }

        figcaption {
            margin-top: 0.5rem;
        }

        iframe {
            width: 100%;
            min-height: 400px;
            border: 0;
        }
    </style>
</head>

<body>
    <main>
        <article>
            <header>
                <h1>Introduction to Digital Systems</h1>
            </header>

            <section aria-labelledby="course-image-heading">
                <h2 id="course-image-heading">Course Illustration</h2>

                <figure>
                    <picture>
                        <source
                            media="(max-width: 600px)"
                            srcset="images/system-mobile.webp">

                        <source
                            srcset="images/system.webp"
                            type="image/webp">

                        <img
                            src="images/system.jpg"
                            srcset="
                                images/system-600.jpg 600w,
                                images/system-1000.jpg 1000w,
                                images/system-1600.jpg 1600w"
                            sizes="(max-width: 700px) 100vw, 1000px"
                            alt="Diagram of interconnected digital systems"
                            width="1600"
                            height="900"
                            loading="lazy"
                            decoding="async">
                    </picture>

                    <figcaption>
                        Conceptual representation of interconnected digital systems.
                    </figcaption>
                </figure>
            </section>

            <section aria-labelledby="audio-heading">
                <h2 id="audio-heading">Audio Lecture</h2>

                <audio controls preload="metadata">
                    <source
                        src="audio/lecture.mp3"
                        type="audio/mpeg">

                    <source
                        src="audio/lecture.ogg"
                        type="audio/ogg">

                    Your browser does not support HTML audio.
                </audio>
            </section>

            <section aria-labelledby="video-heading">
                <h2 id="video-heading">Video Lecture</h2>

                <figure>
                    <video
                        controls
                        preload="metadata"
                        playsinline
                        poster="images/lecture-poster.jpg"
                        width="1280"
                        height="720">

                        <source
                            src="video/lecture.webm"
                            type="video/webm">

                        <source
                            src="video/lecture.mp4"
                            type="video/mp4">

                        <track
                            src="captions/lecture-en.vtt"
                            kind="captions"
                            srclang="en"
                            label="English"
                            default>

                        Your browser does not support HTML video.
                    </video>

                    <figcaption>
                        Video lecture explaining the architecture of the system.
                    </figcaption>
                </figure>
            </section>

            <section aria-labelledby="resource-heading">
                <h2 id="resource-heading">External Resource</h2>

                <iframe
                    src="https://example.com"
                    title="External course reference"
                    loading="lazy"
                    referrerpolicy="strict-origin-when-cross-origin"
                    sandbox="allow-scripts">
                </iframe>
            </section>
        </article>
    </main>
</body>
</html>
"""

    show_code(project)


# =============================================================================
# 30. KNOWLEDGE CHECK
# =============================================================================

def knowledge_check() -> None:
    print_title("29. KNOWLEDGE CHECK")

    questions = [
        (
            "1. Which attribute provides alternative text for an image?",
            "alt",
        ),
        (
            "2. Which element provides native video playback?",
            "<video>",
        ),
        (
            "3. Which element provides native audio playback?",
            "<audio>",
        ),
        (
            "4. Which element creates a nested browsing context?",
            "<iframe>",
        ),
        (
            "5. Which element provides responsive source selection?",
            "<picture>",
        ),
        (
            "6. Which attribute provides multiple width-based image candidates?",
            "srcset",
        ),
        (
            "7. Which attribute describes expected rendered image width?",
            "sizes",
        ),
        (
            "8. Which element provides a visible figure caption?",
            "<figcaption>",
        ),
        (
            "9. Which video element attribute specifies a preview image?",
            "poster",
        ),
        (
            "10. Which iframe attribute can restrict embedded capabilities?",
            "sandbox",
        ),
    ]

    for question, answer in questions:
        print(f"{question}")
        print(f"   Answer: {answer}")


# =============================================================================
# 31. MAIN PROGRAM
# =============================================================================

def main() -> None:
    """
    Run the complete multimedia HTML course in logical order.

    Every section is executable and demonstrates actual concepts rather than
    serving only as prose documentation.
    """
    print_title("MULTIMEDIA HTML: COMPLETE STUDY SCRIPT")

    explain(
        """
Topic:
    Images, audio, video, iframe, responsive images,
    figure/figcaption, and media attributes.

Level:
    Absolute beginner through advanced practical implementation.

This program does not require third-party Python packages.
It prints HTML examples and executes small validation/generation examples.
        """
    )

    fundamentals()
    image_basics()
    alt_text()
    audio_basics()
    audio_attributes()
    video_basics()
    video_advanced()
    responsive_images()
    picture_element()
    figure_and_figcaption()
    iframe_basics()
    iframe_security()
    media_attribute_comparison()
    playback_design()
    complete_page()
    html_generation_demo()
    media_validation_demo()
    responsive_image_demo()
    common_mistakes()
    edge_cases()
    performance()
    accessibility()
    security()
    comparisons()
    url_validation_demo()
    run_tests()
    production_checklist()
    mini_project()
    knowledge_check()

    print_title("END OF MULTIMEDIA HTML STUDY SCRIPT")


if __name__ == "__main__":
    main()
