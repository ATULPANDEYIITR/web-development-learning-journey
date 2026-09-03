"""
===============================================================================
DEVELOPMENT ENVIRONMENT
===============================================================================

Topic:
    Installing VS Code, browser DevTools, terminal basics, folders, files,
    extensions, and workspace configuration.

Primary tools:
    - Visual Studio Code (VS Code)
    - Google Chrome
    - Terminal / Command Prompt / PowerShell

Level:
    Beginner -> Intermediate -> Advanced

Purpose:
    This script is primarily an executable learning document. It explains the
    concepts using comments, demonstrations, and practical Python examples.

NOTE:
    This script does NOT automatically install VS Code, Chrome, or extensions.
    Installation of software is normally performed through the operating
    system or official installers.

===============================================================================
1. WHAT IS A DEVELOPMENT ENVIRONMENT?
===============================================================================

A development environment is the collection of tools, software, directories,
configuration files, runtimes, terminals, editors, browsers, extensions,
debuggers, and other utilities used to create and test software.

A basic web/software development environment may contain:

    Operating System
          |
          +-- File System
          |
          +-- Terminal
          |
          +-- Code Editor / IDE
          |
          +-- Programming Language Runtime
          |
          +-- Package Manager
          |
          +-- Version Control
          |
          +-- Browser
          |
          +-- Browser DevTools
          |
          +-- Extensions
          |
          +-- Workspace Configuration

Example:

    Windows
       |
       +-- VS Code
       |
       +-- Python
       |
       +-- pip
       |
       +-- Git
       |
       +-- Chrome
       |
       +-- Chrome DevTools

The development environment is important because software development is
not only about writing code. You must also:

    - create files
    - organize folders
    - execute programs
    - inspect errors
    - debug applications
    - install dependencies
    - inspect network requests
    - inspect browser storage
    - manage configuration
    - use version control
    - test applications

===============================================================================
2. VS CODE
===============================================================================

Visual Studio Code is a source-code editor developed by Microsoft.

It is commonly used for:

    - Python
    - JavaScript
    - TypeScript
    - HTML
    - CSS
    - Java
    - C/C++
    - Go
    - Rust
    - SQL
    - Markdown
    - configuration files
    - cloud development
    - web development
    - data science

VS Code is technically a code editor rather than a traditional full IDE,
although extensions can provide many IDE-like capabilities.

Important VS Code concepts:

    Editor
    Explorer
    Search
    Source Control
    Run and Debug
    Extensions
    Integrated Terminal
    Command Palette
    Workspace
    Settings
    Tasks
    Launch configurations

===============================================================================
3. INSTALLING VS CODE
===============================================================================

Typical installation process:

    1. Download VS Code from the official Microsoft website.
    2. Run the installer.
    3. Select installation options.
    4. Complete installation.
    5. Open VS Code.
    6. Configure the editor.
    7. Install required extensions.

After installation, verify that VS Code can be launched.

On many systems, the command:

    code .

opens the current directory as a VS Code workspace.

If "code" is not recognized, VS Code may not have been added to PATH.

===============================================================================
4. VS CODE INTERFACE
===============================================================================

The main VS Code interface contains several important areas.

EXPLORER
--------
Used to browse files and folders.

SEARCH
------
Used to search text throughout a project.

SOURCE CONTROL
--------------
Used to work with Git repositories.

RUN AND DEBUG
-------------
Used to execute and debug applications.

EXTENSIONS
----------
Used to install additional functionality.

EDITOR
------
The central area where files are opened and edited.

TERMINAL
--------
An integrated command-line interface.

STATUS BAR
----------
Displays information such as:

    - language
    - line/column
    - encoding
    - Git branch
    - formatter status
    - errors/warnings

===============================================================================
5. COMMAND PALETTE
===============================================================================

The Command Palette is one of the most powerful VS Code features.

It allows you to search for commands rather than manually navigating menus.

Typical shortcut:

    Ctrl + Shift + P

Examples:

    Format Document
    Reload Window
    Open Settings
    Configure Display Language
    Install Extensions
    Developer: Reload Window
    Git: Clone
    Python: Select Interpreter

The Command Palette becomes particularly useful when you do not remember
where a particular command is located.

===============================================================================
6. FILES AND FOLDERS
===============================================================================

A file is a container for data.

Examples:

    main.py
    README.md
    index.html
    styles.css
    config.json
    requirements.txt

A folder is a container used to organize files and other folders.

Example project:

    my_project/
    |
    +-- main.py
    +-- README.md
    +-- requirements.txt
    |
    +-- src/
    |   +-- app.py
    |   +-- utils.py
    |
    +-- tests/
    |   +-- test_app.py
    |
    +-- data/
    |   +-- input.csv
    |
    +-- docs/
    |   +-- architecture.md
    |
    +-- .gitignore

Good organization becomes increasingly important as projects grow.

===============================================================================
7. ABSOLUTE PATHS AND RELATIVE PATHS
===============================================================================

An absolute path describes a location starting from the root of the file
system.

Example on Windows:

    C:\\Users\\Developer\\Projects\\my_project\\main.py

Example on Linux/macOS:

    /home/developer/projects/my_project/main.py

A relative path describes a location relative to the current directory.

Example:

    src/app.py

    ../data/input.csv

    ./main.py

Important concepts:

    .   = current directory
    ..  = parent directory

Python can work with paths using pathlib.

"""

from pathlib import Path

current_directory = Path.cwd()

print("Current directory:")
print(current_directory)

example_file = current_directory / "example.txt"

print("\nExample file path:")
print(example_file)

print("\nFile name:")
print(example_file.name)

print("\nFile suffix:")
print(example_file.suffix)

print("\nParent directory:")
print(example_file.parent)

"""
===============================================================================
8. CREATING DIRECTORIES WITH PYTHON
===============================================================================
"""

demo_directory = current_directory / "development_environment_demo"

demo_directory.mkdir(exist_ok=True)

print("\nCreated directory:")
print(demo_directory)

"""
===============================================================================
9. CREATING AND WRITING FILES
===============================================================================
"""

text_file = demo_directory / "hello.txt"

text_file.write_text(
    "Hello from the development environment learning script.\n",
    encoding="utf-8"
)

print("\nCreated file:")
print(text_file)

"""
===============================================================================
10. READING FILES
===============================================================================
"""

content = text_file.read_text(encoding="utf-8")

print("\nFile content:")
print(content)

"""
===============================================================================
11. CHECKING FILES AND DIRECTORIES
===============================================================================
"""

print("Does the file exist?", text_file.exists())
print("Is it a file?", text_file.is_file())
print("Is the directory a directory?", demo_directory.is_dir())

"""
===============================================================================
12. LISTING FILES
===============================================================================
"""

print("\nFiles in demo directory:")

for item in demo_directory.iterdir():
    print(" -", item.name)

"""
===============================================================================
13. TERMINAL BASICS
===============================================================================

A terminal is a text-based interface for interacting with the operating system.

Different systems provide different shells.

Windows:
    - Command Prompt
    - PowerShell
    - Windows Terminal

Linux/macOS:
    - Bash
    - Zsh
    - other shells

A shell interprets commands.

Important distinction:

    Terminal
        = application/interface through which you interact with a shell.

    Shell
        = command interpreter.

    Command
        = instruction given to the shell.

Examples:

    Windows:
        dir
        cd
        mkdir
        type

    Linux/macOS:
        ls
        cd
        mkdir
        cat

Cross-platform commands can also be performed through Python.

===============================================================================
14. IMPORTANT TERMINAL CONCEPTS
===============================================================================

CURRENT DIRECTORY
-----------------

The current directory is the location in the file system where your shell is
currently operating.

Conceptually:

    terminal
       |
       +-- current working directory
               |
               +-- files
               +-- folders

NAVIGATION
----------

Common concepts:

    cd folder
        Move into a folder.

    cd ..
        Move to the parent folder.

    cd .
        Refer to the current folder.

LISTING
-------

Linux/macOS:

    ls

Windows:

    dir

CREATING A DIRECTORY
--------------------

Common command:

    mkdir project

CREATING A FILE
---------------

The exact command differs between shells.

You can also use VS Code or Python to create files.

===============================================================================
15. TERMINAL COMMAND EXAMPLES
===============================================================================

The following are examples to learn conceptually.

    pwd
        Show current directory on Unix-like systems.

    ls
        List files.

    dir
        List files on Windows Command Prompt.

    cd project
        Enter project directory.

    cd ..
        Go to parent directory.

    mkdir project
        Create a directory.

    python --version
        Check Python version.

    pip --version
        Check pip version.

    git --version
        Check Git version.

    code .
        Open current directory in VS Code.

Do not blindly execute unfamiliar commands, especially commands involving
deletion, permissions, system configuration, or downloading scripts.

===============================================================================
16. PYTHON FROM THE TERMINAL
===============================================================================

A development environment becomes useful when the terminal can execute your
program.

Suppose a file contains:

    print("Hello World")

If the file is:

    hello.py

you can normally execute it using:

    python hello.py

Depending on the operating system, Python may also be invoked using:

    python3 hello.py

The exact command depends on how Python is installed and configured.

===============================================================================
17. PYTHON VERSION
===============================================================================
"""

import sys

print("\nPython version:")
print(sys.version)

print("\nPython executable:")
print(sys.executable)

"""
sys.executable is extremely useful when debugging environment problems.

For example, VS Code may be using one Python interpreter while your terminal
is using another.

===============================================================================
18. PYTHON INTERPRETER
===============================================================================

A Python interpreter executes Python code.

This distinction is important:

    VS Code
        = editor

    Terminal
        = command interface

    Python
        = programming language/runtime

    Python interpreter
        = program that executes Python code

Example:

    VS Code
       |
       +-- edits main.py
       |
       +-- terminal
              |
              +-- Python interpreter
                       |
                       +-- executes main.py

===============================================================================
19. VIRTUAL ENVIRONMENTS
===============================================================================

A virtual environment creates an isolated Python environment for a project.

Why?

Suppose:

    Project A requires package version X.

    Project B requires package version Y.

Installing everything globally can create conflicts.

Virtual environments isolate project dependencies.

Typical command:

    python -m venv .venv

Then activate it according to your operating system.

Windows PowerShell commonly uses:

    .venv\\Scripts\\Activate.ps1

Windows Command Prompt commonly uses:

    .venv\\Scripts\\activate.bat

Linux/macOS commonly uses:

    source .venv/bin/activate

After activation:

    python
    pip

refer to the environment's tools.

===============================================================================
20. WHY .venv IS COMMON
===============================================================================

A common project structure is:

    project/
    |
    +-- .venv/
    +-- src/
    +-- tests/
    +-- README.md
    +-- requirements.txt
    +-- .gitignore

The .venv directory is normally excluded from Git because it contains an
environment-specific installation of dependencies.

===============================================================================
21. PYTHON PACKAGE INSTALLATION
===============================================================================

pip is Python's commonly used package installer.

Example:

    pip install requests

A project's dependencies can be represented in:

    requirements.txt

Example:

    requests
    pandas
    pytest

Then:

    pip install -r requirements.txt

Dependency management is an important part of reproducible development.

===============================================================================
22. BROWSER
===============================================================================

A browser is software that retrieves, interprets, and displays web content.

Google Chrome is a Chromium-based web browser.

Web applications commonly involve:

    HTML
    CSS
    JavaScript
    HTTP/HTTPS
    APIs
    cookies
    local storage
    sessions
    caching
    network requests

For developers, a browser is not merely a tool for viewing websites.

It is also a debugging environment.

===============================================================================
23. CHROME DEVELOPER TOOLS
===============================================================================

Chrome DevTools is a collection of browser-based development and debugging
tools.

It can be opened using:

    F12

or commonly:

    Ctrl + Shift + I

or through the browser menu.

Major DevTools panels include:

    Elements
    Console
    Sources
    Network
    Performance
    Memory
    Application
    Security
    Lighthouse
    Device emulation

The exact panel availability can vary by Chrome version.

===============================================================================
24. ELEMENTS PANEL
===============================================================================

The Elements panel allows you to inspect the HTML DOM and CSS.

Example HTML:

    <button class="primary">Login</button>

You can inspect:

    - HTML structure
    - classes
    - IDs
    - attributes
    - CSS rules
    - computed styles
    - box model
    - layout

The DOM is a browser representation of the page structure.

Conceptually:

    HTML source
         |
         v
       Browser
         |
         v
        DOM
         |
         +-- Elements
         +-- Attributes
         +-- Text
         +-- Styles

DevTools also allows temporary modifications to HTML and CSS.

These modifications generally do not modify the original source code on your
computer.

===============================================================================
25. CSS BOX MODEL
===============================================================================

When debugging layouts, the box model is fundamental.

An element can be understood as:

    content
       |
       +-- padding
              |
              +-- border
                     |
                     +-- margin

Understanding the box model helps diagnose:

    - unexpected spacing
    - oversized elements
    - alignment problems
    - overflow
    - responsive layout issues

===============================================================================
26. CONSOLE PANEL
===============================================================================

The Console allows developers to:

    - view JavaScript errors
    - inspect warnings
    - execute JavaScript
    - inspect values
    - debug browser behavior

Example JavaScript:

    console.log("Hello");

The console can also display:

    errors
    warnings
    network-related messages
    application logs

A frontend developer should become comfortable reading console errors.

===============================================================================
27. SOURCES PANEL
===============================================================================

The Sources panel is used for debugging application source code.

Important concepts include:

    breakpoints
    call stack
    scope
    variables
    stepping
    watch expressions

A breakpoint pauses execution at a selected line.

Typical debugging flow:

    application starts
          |
          v
    JavaScript executes
          |
          v
    breakpoint reached
          |
          v
    execution pauses
          |
          +-- inspect variables
          +-- inspect call stack
          +-- step over
          +-- step into
          +-- continue

===============================================================================
28. NETWORK PANEL
===============================================================================

The Network panel is one of the most important tools for web developers.

It allows inspection of network activity.

You can examine:

    - request URL
    - HTTP method
    - status code
    - request headers
    - response headers
    - request payload
    - response body
    - timing
    - initiator
    - cookies

Common HTTP methods:

    GET
    POST
    PUT
    PATCH
    DELETE

Common HTTP status codes:

    200 = success
    201 = created
    204 = success with no content
    301 = permanent redirect
    302 = temporary redirect
    400 = bad request
    401 = unauthorized
    403 = forbidden
    404 = not found
    429 = too many requests
    500 = server error
    502 = bad gateway
    503 = service unavailable

Understanding Network DevTools is extremely valuable when debugging APIs.

===============================================================================
29. API DEBUGGING
===============================================================================

Suppose a web application sends:

    POST /api/login

The Network panel can help determine:

    Was the request sent?

    What URL was requested?

    What method was used?

    What payload was sent?

    What status code returned?

    What did the server respond with?

    How long did the request take?

This allows you to distinguish between:

    frontend problem
    network problem
    API problem
    authentication problem
    backend problem

===============================================================================
30. APPLICATION PANEL
===============================================================================

The Application panel helps inspect browser-side storage and application
state.

Common areas include:

    Cookies
    Local Storage
    Session Storage
    IndexedDB
    Cache Storage
    Service Workers

LOCAL STORAGE
-------------

Local Storage stores key-value data in the browser.

Example conceptual data:

    theme = "dark"

SESSION STORAGE
---------------

Session Storage is also key-value storage but has different lifetime behavior.

COOKIES
-------

Cookies are commonly used for:

    - sessions
    - authentication state
    - preferences
    - tracking

Developers must understand security attributes such as:

    Secure
    HttpOnly
    SameSite

===============================================================================
31. RESPONSIVE DESIGN AND DEVICE EMULATION
===============================================================================

Modern applications must work across different screen sizes.

Chrome DevTools can emulate various viewport dimensions.

Developers can test:

    desktop
    tablet
    mobile

Important concepts:

    viewport
    responsive layout
    media queries
    touch simulation
    device pixel ratio

This is useful for detecting UI problems before testing on physical devices.

===============================================================================
32. PERFORMANCE PANEL
===============================================================================

The Performance panel helps investigate application performance.

Potential problems include:

    - slow JavaScript
    - expensive rendering
    - layout thrashing
    - long tasks
    - excessive network activity
    - rendering bottlenecks

Performance analysis involves measuring rather than guessing.

Important concept:

    "It feels slow"

is not a sufficient diagnosis.

A developer should identify:

    what is slow
    where it is slow
    why it is slow
    how much it costs
    whether optimization changes the measurement

===============================================================================
33. LIGHTHOUSE
===============================================================================

Lighthouse can analyze web applications against categories such as:

    - performance
    - accessibility
    - best practices
    - SEO

It can provide actionable findings.

Lighthouse results should be treated as engineering signals, not as absolute
proof that an application is good or bad.

===============================================================================
34. VS CODE EXTENSIONS
===============================================================================

Extensions add functionality to VS Code.

Examples of extension categories:

    Python support
    language servers
    formatters
    linters
    Git tools
    Docker tools
    database tools
    Markdown tools
    remote development
    testing tools

For Python development, useful functionality includes:

    - syntax highlighting
    - autocomplete
    - linting
    - formatting
    - debugging
    - test discovery
    - interpreter selection

Do not install extensions merely because they are popular.

Consider:

    publisher
    maintenance
    permissions
    reviews
    compatibility
    security
    necessity

Extensions execute code or integrate deeply with the editor, so they should
be treated as software dependencies.

===============================================================================
35. PYTHON EXTENSION CONCEPT
===============================================================================

A Python-oriented VS Code setup typically needs functionality for:

    - Python interpreter selection
    - IntelliSense
    - debugging
    - testing
    - formatting
    - linting

Depending on the chosen tooling, you may also use:

    Pylance
    Ruff
    Black
    Pytest
    MyPy

Tools can change over time, so always verify current recommendations before
standardizing a team environment.

===============================================================================
36. FORMATTERS
===============================================================================

A formatter automatically applies consistent formatting rules.

For example, a formatter may normalize:

    indentation
    line breaks
    spacing
    quote usage
    import formatting

Benefits:

    - consistent code
    - fewer style debates
    - easier reviews
    - improved readability

Formatting should be automated where practical.

===============================================================================
37. LINTERS
===============================================================================

A linter analyzes code for potential issues.

Examples of things a linter may detect:

    unused variables
    undefined names
    suspicious constructs
    style problems
    complexity issues
    possible bugs

Formatter and linter are not identical.

Formatter:

    "How should the code look?"

Linter:

    "What might be wrong with this code?"

===============================================================================
38. DEBUGGER
===============================================================================

A debugger lets you execute code while observing its state.

Core concepts:

    breakpoint
    variable inspection
    call stack
    stepping
    watch expressions
    exception handling

Example:

"""

def calculate_total(price, quantity):
    subtotal = price * quantity
    tax = subtotal * 0.18
    total = subtotal + tax
    return total


print("\nDebugger example:")
print(calculate_total(1000, 2))

"""
You could place a breakpoint inside calculate_total and inspect:

    price
    quantity
    subtotal
    tax
    total

===============================================================================
39. WORKSPACE
===============================================================================

A VS Code workspace represents the project environment and its configuration.

For a simple project, opening a folder can be enough.

For more complex projects, VS Code can use workspace configuration files.

Typical structure:

    project/
    |
    +-- .vscode/
    |   +-- settings.json
    |   +-- launch.json
    |   +-- tasks.json
    |
    +-- src/
    +-- tests/
    +-- README.md

===============================================================================
40. .VSCODE DIRECTORY
===============================================================================

The .vscode directory can contain project-specific configuration.

Important files include:

    settings.json
    launch.json
    tasks.json

settings.json
-------------
Editor and project settings.

launch.json
-----------
Debugging configurations.

tasks.json
----------
Automation tasks.

Not every project needs all three.

===============================================================================
41. WORKSPACE SETTINGS
===============================================================================

Workspace settings allow project-specific behavior.

Conceptually:

    User settings
          |
          v
    Workspace settings
          |
          v
    Project-specific behavior

Example:

    Project A
        Python interpreter = environment A

    Project B
        Python interpreter = environment B

This is why workspace configuration is useful.

===============================================================================
42. EXAMPLE settings.json
===============================================================================

A conceptual example:

    {
        "editor.formatOnSave": true,
        "editor.tabSize": 4,
        "files.exclude": {
            "**/__pycache__": true
        }
    }

These settings control editor behavior.

Be careful when copying configuration from the internet because settings can
change and some may be inappropriate for your project.

===============================================================================
43. DEBUG CONFIGURATION
===============================================================================

launch.json can define debugging configurations.

Conceptually:

    {
        "name": "Python: Current File",
        "type": "debugpy",
        "request": "launch",
        "program": "${file}"
    }

The exact schema depends on the extension and current VS Code tooling.

The key idea is:

    VS Code
       |
       +-- debugger configuration
                |
                +-- launch program
                +-- set environment
                +-- pass arguments
                +-- attach to process

===============================================================================
44. TASKS
===============================================================================

Tasks automate repetitive commands.

For example, a task might run:

    pytest

or:

    python main.py

or:

    npm test

or:

    docker compose up

Tasks are useful when a project has repeatable workflows.

===============================================================================
45. ENVIRONMENT VARIABLES
===============================================================================

Environment variables allow configuration to be supplied outside source code.

Examples:

    DATABASE_URL
    API_KEY
    DEBUG
    PORT

Never hard-code sensitive secrets in source code.

Bad:

    API_KEY = "my-real-secret"

Better concept:

    API_KEY = environment variable

Python example:

"""

import os

api_key = os.getenv("API_KEY")

if api_key:
    print("\nAPI_KEY environment variable is available.")
else:
    print("\nAPI_KEY is not configured.")

"""
For security reasons, this script does not print the actual secret.

===============================================================================
46. .ENV FILES
===============================================================================

Many projects use a .env file for local configuration.

Example concept:

    API_KEY=example
    DEBUG=true
    DATABASE_URL=example

A .env file commonly should not be committed when it contains secrets.

Instead:

    .env

can be excluded through:

    .gitignore

A safe pattern is to provide:

    .env.example

containing placeholder values.

===============================================================================
47. .GITIGNORE
===============================================================================

A .gitignore file tells Git which files should generally not be tracked.

Typical entries for a Python project may include:

    .venv/
    __pycache__/
    *.pyc
    .env
    .pytest_cache/
    .vscode/

Whether .vscode should be ignored depends on the project.

Some teams intentionally commit workspace settings.

Others keep personal editor settings out of the repository.

The correct decision is project-specific.

===============================================================================
48. SOURCE CONTROL IN VS CODE
===============================================================================

VS Code integrates with Git.

Common workflow:

    Working directory
          |
          v
       git add
          |
          v
       staging area
          |
          v
       git commit
          |
          v
       local repository
          |
          v
       git push
          |
          v
       remote repository

Useful concepts:

    clone
    branch
    commit
    stage
    push
    pull
    merge
    pull request

===============================================================================
49. INTEGRATED TERMINAL
===============================================================================

VS Code includes an integrated terminal.

This is useful because you can:

    edit code
    run commands
    inspect files
    run tests
    activate environments
    execute Git commands

without switching applications.

Example workflow:

    VS Code
       |
       +-- Explorer
       +-- Editor
       +-- Terminal
       +-- Debugger
       +-- Source Control

This makes the development workflow highly integrated.

===============================================================================
50. COMMAND PALETTE VS TERMINAL
===============================================================================

They serve different purposes.

Command Palette:

    VS Code-specific commands.

Terminal:

    Operating-system shell commands and development tools.

Example:

    Command Palette:
        Format Document

    Terminal:
        python main.py

Understanding this distinction prevents confusion.

===============================================================================
51. SEARCH IN VS CODE
===============================================================================

VS Code provides project-wide search.

Useful for finding:

    function definitions
    variable references
    TODO comments
    configuration values
    API endpoints
    error messages

Common shortcut:

    Ctrl + Shift + F

Search is particularly valuable in large codebases.

===============================================================================
52. MULTI-CURSOR EDITING
===============================================================================

VS Code supports multiple cursors.

This allows simultaneous editing of multiple locations.

Useful for:

    renaming repeated patterns
    editing structured text
    changing multiple lines

This is a productivity feature rather than a programming language feature.

===============================================================================
53. COMMAND-LINE PROJECT OPENING
===============================================================================

Suppose the project is:

    C:\\Projects\\my_app

You can navigate there in the terminal and use:

    code .

The dot means:

    current directory

This opens the directory as the VS Code workspace.

===============================================================================
54. PROJECT STRUCTURE
===============================================================================

A clean beginner-friendly Python project could look like:

    my_project/
    |
    +-- .venv/
    |
    +-- src/
    |   +-- main.py
    |   +-- utils.py
    |
    +-- tests/
    |   +-- test_main.py
    |
    +-- .gitignore
    +-- README.md
    +-- requirements.txt

Larger applications may have significantly more structure.

The objective is not to create unnecessary folders.

The objective is to create understandable boundaries.

===============================================================================
55. IMPORTANCE OF THE CURRENT WORKING DIRECTORY
===============================================================================

Consider:

    project/
        main.py
        data/
            input.csv

If Python executes from:

    project/

then:

    data/input.csv

refers to the expected relative location.

If the program is launched from another directory, assumptions about relative
paths may fail.

This is a common beginner debugging issue.

===============================================================================
56. ROBUST PATH MANAGEMENT
===============================================================================

Instead of relying heavily on fragile string paths, pathlib is recommended
for many Python applications.

Example:

"""

project_root = Path.cwd()

data_directory = project_root / "data"
input_file = data_directory / "input.csv"

print("\nProject root:", project_root)
print("Data directory:", data_directory)
print("Input file:", input_file)

"""
For production systems, project-root discovery may require a deliberate
architecture rather than simply using Path.cwd().

===============================================================================
57. BROWSER + VS CODE WORKFLOW
===============================================================================

A modern web-development workflow may look like:

    VS Code
       |
       +-- HTML
       +-- CSS
       +-- JavaScript
       +-- configuration
       |
       +-- Terminal
               |
               +-- development server
               |
               v
             Chrome
               |
               +-- rendered application
               |
               +-- DevTools
                       |
                       +-- Elements
                       +-- Console
                       +-- Network
                       +-- Sources
                       +-- Application
                       +-- Performance

This creates a development feedback loop.

===============================================================================
58. DEBUGGING WORKFLOW
===============================================================================

A disciplined debugging process is:

    1. Reproduce the problem.
    2. Observe the exact symptom.
    3. Check the browser Console.
    4. Check Network requests.
    5. Inspect the relevant DOM/CSS.
    6. Inspect application state.
    7. Reproduce in VS Code.
    8. Add breakpoints or logs.
    9. Identify the root cause.
    10. Fix the cause.
    11. Test the fix.
    12. Test related scenarios.
    13. Commit the change.

Avoid changing random code until the problem disappears.

That approach often creates new bugs.

===============================================================================
59. FRONTEND ERROR CATEGORIES
===============================================================================

A browser application can fail in several layers.

HTML problem
    |
    v
DOM structure

CSS problem
    |
    v
Visual/layout problem

JavaScript problem
    |
    v
Runtime error

Network problem
    |
    v
API/request failure

Backend problem
    |
    v
Server response

Authentication problem
    |
    v
Unauthorized/forbidden request

Configuration problem
    |
    v
Wrong environment/settings

Understanding layers makes debugging faster.

===============================================================================
60. NETWORK DEBUGGING EXAMPLE
===============================================================================

Imagine a frontend sends:

    GET /api/users

The response is:

    404 Not Found

Possible causes:

    - wrong endpoint
    - incorrect base URL
    - backend route does not exist
    - reverse proxy configuration
    - incorrect deployment configuration

The correct debugging approach is to inspect evidence rather than assume the
frontend is necessarily broken.

===============================================================================
61. SECURITY IN THE DEVELOPMENT ENVIRONMENT
===============================================================================

Your development environment is part of your security boundary.

Important practices:

    - keep software updated
    - install extensions carefully
    - avoid unknown scripts
    - protect API keys
    - avoid committing secrets
    - use trusted dependencies
    - review permissions
    - use HTTPS when appropriate
    - protect authentication credentials
    - use environment variables appropriately
    - keep development and production secrets separate

Do not assume:

    "It is only development, so security does not matter."

Development environments often contain:

    source code
    credentials
    API keys
    cloud access
    databases
    customer data

===============================================================================
62. EXTENSION SECURITY
===============================================================================

Extensions can have significant access to your development environment.

Before installing an extension, consider:

    Who publishes it?

    Is it actively maintained?

    Is the publisher trustworthy?

    What permissions does it require?

    Does the project actually need it?

    Are there known security concerns?

The principle is:

    Minimize unnecessary software.

===============================================================================
63. DEPENDENCY SECURITY
===============================================================================

The same principle applies to packages.

Every dependency can introduce:

    bugs
    vulnerabilities
    compatibility issues
    maintenance requirements

Dependency management should therefore include:

    version awareness
    updates
    vulnerability monitoring
    reproducible environments

===============================================================================
64. REPRODUCIBLE DEVELOPMENT ENVIRONMENT
===============================================================================

A reproducible environment allows another developer to recreate the project
environment reliably.

Important components may include:

    requirements.txt
    pyproject.toml
    lock files
    .gitignore
    .env.example
    workspace configuration
    README instructions
    Python version specification

A strong README should explain:

    installation
    environment setup
    dependency installation
    execution
    testing
    configuration
    troubleshooting

===============================================================================
65. CONFIGURATION AS CODE
===============================================================================

Modern development increasingly represents configuration as files.

Examples:

    .vscode/settings.json
    .vscode/launch.json
    pyproject.toml
    requirements.txt
    .gitignore
    Dockerfile
    compose.yaml
    CI configuration

Advantages:

    - repeatability
    - documentation
    - automation
    - collaboration
    - version control

===============================================================================
66. IDE VS CODE EDITOR DISTINCTION
===============================================================================

An IDE traditionally integrates:

    editor
    compiler/interpreter
    debugger
    build system
    project management

VS Code starts as a lightweight editor and becomes much more capable through
extensions.

Therefore:

    VS Code + extensions + runtime + tools

can form a highly capable development environment.

===============================================================================
67. DEVELOPMENT ENVIRONMENT LAYERS
===============================================================================

A useful mental model is:

    Layer 1: Hardware
             |
    Layer 2: Operating System
             |
    Layer 3: File System
             |
    Layer 4: Terminal / Shell
             |
    Layer 5: Runtime
             |
    Layer 6: Package Manager
             |
    Layer 7: Git
             |
    Layer 8: VS Code
             |
    Layer 9: Extensions
             |
    Layer 10: Browser
             |
    Layer 11: DevTools
             |
    Layer 12: Application

Each layer solves a different problem.

===============================================================================
68. TROUBLESHOOTING CHECKLIST
===============================================================================

If Python does not execute:

    1. Check Python installation.
    2. Run python --version.
    3. Check sys.executable.
    4. Check VS Code interpreter.
    5. Check virtual environment.
    6. Check PATH.
    7. Check terminal shell.
    8. Check project directory.

If a website does not work:

    1. Check Console.
    2. Check Network.
    3. Check status code.
    4. Check request URL.
    5. Check request payload.
    6. Check response.
    7. Check authentication.
    8. Check backend logs.
    9. Check environment variables.
    10. Reproduce systematically.

===============================================================================
69. PRACTICAL ENVIRONMENT VALIDATION
===============================================================================
"""

def environment_report():
    """
    Produce a small diagnostic report about the current Python environment.
    """

    print("\n" + "=" * 70)
    print("DEVELOPMENT ENVIRONMENT REPORT")
    print("=" * 70)

    print("Python version:")
    print(sys.version)

    print("\nPython executable:")
    print(sys.executable)

    print("\nCurrent working directory:")
    print(Path.cwd())

    print("\nPlatform:")
    print(sys.platform)

    print("\nEnvironment variables available:")
    print("PATH:", bool(os.getenv("PATH")))
    print("HOME:", bool(os.getenv("HOME")))
    print("USERPROFILE:", bool(os.getenv("USERPROFILE")))

    print("=" * 70)


environment_report()

"""
===============================================================================
70. PRACTICAL MINI PROJECT
===============================================================================

The following creates a miniature project structure.

This demonstrates:

    - folders
    - files
    - pathlib
    - configuration
    - README
    - source code
    - tests
"""

mini_project = Path.cwd() / "mini_development_project"

directories = [
    mini_project,
    mini_project / "src",
    mini_project / "tests",
    mini_project / "docs",
    mini_project / ".vscode",
]

for directory in directories:
    directory.mkdir(parents=True, exist_ok=True)

files = {
    mini_project / "README.md":
        "# Mini Development Project\n\nLearning development environments.\n",

    mini_project / ".gitignore":
        ".venv/\n__pycache__/\n*.pyc\n.env\n",

    mini_project / "src" / "main.py":
        'print("Hello from the mini project!")\n',

    mini_project / "tests" / "test_main.py":
        'def test_example():\n    assert 1 + 1 == 2\n',

    mini_project / "docs" / "notes.md":
        "# Development Notes\n\nProject documentation.\n",

    mini_project / ".vscode" / "settings.json":
        '{\n    "editor.formatOnSave": true\n}\n',
}

for file_path, file_content in files.items():
    file_path.write_text(file_content, encoding="utf-8")

print("\nMini project created at:")
print(mini_project)

print("\nMini project structure:")

for path in sorted(mini_project.rglob("*")):
    relative = path.relative_to(mini_project)

    if path.is_dir():
        print("[DIR] ", relative)
    else:
        print("[FILE]", relative)

"""
===============================================================================
71. ADVANCED CONCEPT: PATH ENVIRONMENT
===============================================================================

PATH is an environment variable containing directories where the operating
system looks for executable programs.

Conceptually:

    command:
        python

        |
        v

    operating system searches PATH

        |
        +-- directory A
        +-- directory B
        +-- directory C
        +-- Python installation
                 |
                 v
              python.exe

If an executable cannot be found, you may see an error such as:

    'python' is not recognized...

or:

    command not found

This does not necessarily mean Python is not installed.

It may mean the executable is not available through PATH.

===============================================================================
72. ADVANCED CONCEPT: MULTIPLE PYTHON INTERPRETERS
===============================================================================

A computer can have multiple Python installations.

For example:

    Python A
        C:\\Python...

    Python B
        C:\\Users\\...\\.venv...

VS Code may select one interpreter while the terminal uses another.

Symptoms:

    package installed but import fails
    wrong Python version
    tests use different environment
    application behaves differently

Diagnostic command:

    python -c "import sys; print(sys.executable)"

The output tells you which Python executable is running.

===============================================================================
73. ADVANCED CONCEPT: WORKSPACE REPRODUCIBILITY
===============================================================================

A professional project should make it easy for another developer to understand:

    1. What tools are required?
    2. What Python version is required?
    3. How is the environment created?
    4. Which dependencies are required?
    5. How is the application started?
    6. How are tests executed?
    7. Which environment variables are needed?
    8. How is debugging performed?

This transforms a personal environment into a reproducible engineering
environment.

===============================================================================
74. DEVELOPMENT ENVIRONMENT MATURITY MODEL
===============================================================================

BEGINNER:

    VS Code
    Python
    Chrome
    Terminal

INTERMEDIATE:

    Git
    virtual environments
    extensions
    debugging
    testing
    formatting
    linting

ADVANCED:

    workspace configuration
    environment variables
    reproducible environments
    CI/CD
    containers
    dependency locking
    automated testing
    security scanning
    performance profiling

PROFESSIONAL:

    standardized tooling
    onboarding documentation
    dev containers
    automated environment setup
    secrets management
    observability
    secure supply chain
    reproducible builds

===============================================================================
75. GOLDEN RULES
===============================================================================

Rule 1:
    Know where your project files are.

Rule 2:
    Know your current working directory.

Rule 3:
    Know which Python interpreter is executing your code.

Rule 4:
    Use virtual environments for project isolation.

Rule 5:
    Do not commit secrets.

Rule 6:
    Treat extensions as software dependencies.

Rule 7:
    Use browser DevTools systematically.

Rule 8:
    Read error messages carefully.

Rule 9:
    Reproduce problems before changing code.

Rule 10:
    Automate repetitive development tasks.

Rule 11:
    Document environment setup.

Rule 12:
    Prefer reproducible environments.

===============================================================================
76. FINAL PRACTICAL WORKFLOW
===============================================================================

A mature development workflow can be summarized as:

    Install tools
        |
        v
    Create project directory
        |
        v
    Open project in VS Code
        |
        v
    Create virtual environment
        |
        v
    Select interpreter
        |
        v
    Install dependencies
        |
        v
    Configure workspace
        |
        v
    Write code
        |
        v
    Run from terminal
        |
        v
    Debug in VS Code
        |
        v
    Test in browser
        |
        v
    Inspect Chrome DevTools
        |
        +-- Elements
        +-- Console
        +-- Network
        +-- Sources
        +-- Application
        +-- Performance
        |
        v
    Fix problems
        |
        v
    Test again
        |
        v
    Commit with Git
        |
        v
    Document changes

===============================================================================
77. FINAL TAKEAWAY
===============================================================================

A development environment is the foundation on which software development
takes place.

VS Code provides the coding and project-management interface.

The terminal provides direct interaction with the operating system and
development tools.

The file system provides the structure in which projects exist.

Python provides the runtime for Python applications.

Virtual environments provide dependency isolation.

Extensions customize and expand VS Code.

Workspace configuration makes project behavior more reproducible.

Chrome provides the execution environment for web applications.

Chrome DevTools provides visibility into:

    HTML
    CSS
    JavaScript
    network requests
    storage
    performance
    browser behavior

The most important lesson is not memorizing every button or command.

The important skill is understanding how the pieces connect:

    Files
       |
    Terminal
       |
    Runtime
       |
    VS Code
       |
    Extensions
       |
    Application
       |
    Browser
       |
    DevTools
       |
    Debugging
       |
    Testing
       |
    Version Control

Once this mental model is clear, installing tools, creating projects,
debugging errors, managing environments, and working on larger software
projects becomes much easier.

===============================================================================
END OF DEVELOPMENT ENVIRONMENT GUIDE
===============================================================================
"""
