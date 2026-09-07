"""
HTML Forms: Beginner to Advanced Study Script

This Python script teaches HTML forms through structured explanations,
HTML examples stored as Python strings, validation simulations, form-data
processing examples, and demonstrations of important concepts.

HTML itself is not executed by Python. Python is used here as a teaching
tool to organize examples and simulate how form data and validation behave.

Topics covered:
1. What HTML forms are
2. The <form> element
3. Form attributes: action, method, enctype, target, autocomplete
4. <input> and major input types
5. Labels and accessibility
6. Textarea
7. Select and option
8. Checkboxes
9. Radio buttons
10. Submit and reset controls
11. HTML validation attributes
12. Form submission concepts
13. GET versus POST
14. Form data representation
15. Python validation simulations
16. Common mistakes
17. Accessibility and security considerations
18. Advanced form features
19. Production design considerations
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlencode


# ============================================================================
# 1. BASIC HTML FORM CONCEPTS
# ============================================================================

print("=" * 80)
print("HTML FORMS: BEGINNER TO ADVANCED")
print("=" * 80)

print(
    """
HTML forms collect information from users and send that information to a
server or make it available to client-side JavaScript.

A basic HTML form contains:

<form>
    form controls
</form>

A form control can be an input, textarea, select menu, checkbox, radio button,
or button.

Important concept:
The name attribute identifies data when the form is submitted.
The id attribute uniquely identifies an element in the document.
A label can connect to an input using the input's id.
"""
)


# ============================================================================
# 2. THE FORM ELEMENT
# ============================================================================

basic_form_example = """
<form action="/submit-profile" method="post">
    <label for="username">Username:</label>
    <input
        type="text"
        id="username"
        name="username"
    >

    <button type="submit">Submit</button>
</form>
"""

print("\n2. BASIC FORM STRUCTURE")
print(basic_form_example)

print(
    """
Important <form> attributes:

action
    The destination URL that receives submitted form data.

method
    Usually "get" or "post".

enctype
    Specifies how form data is encoded.
    Important for file uploads.

target
    Specifies where the server response is displayed.

autocomplete
    Controls browser autocomplete behavior.

novalidate
    Disables built-in browser constraint validation for the form.
"""
)


# ============================================================================
# 3. GET AND POST CONCEPTS
# ============================================================================

print("\n3. GET AND POST")

form_data = {
    "search": "html forms",
    "page": "1",
}

query_string = urlencode(form_data)

print("Example GET data:")
print(form_data)
print("Encoded query string:")
print(query_string)
print("Possible URL:")
print("https://example.com/search?" + query_string)

print(
    """
GET:

GET usually places form data in the URL query string.

Example concept:

GET /search?search=html+forms&page=1

Common uses:
- Search forms
- Filters
- Pagination
- Shareable query parameters

Limitations:
- Data may be visible in the URL
- URLs have practical length limits
- Not appropriate for sensitive information

POST:

POST usually sends form data in the HTTP request body.

Common uses:
- Creating accounts
- Logging in
- Sending large form payloads
- Uploading files
- Performing state-changing operations

Important security rule:
POST does not automatically encrypt data.
HTTPS is required to protect data during transmission.
"""
)


# ============================================================================
# 4. THE INPUT ELEMENT
# ============================================================================

print("\n4. THE <input> ELEMENT")

print(
    """
The <input> element is one of the most versatile form controls.

General structure:

<input type="..." id="..." name="..." value="...">

Important attributes:

type
    Determines the type of control.

id
    Unique identifier, commonly used by labels, CSS, and JavaScript.

name
    Key used when the form data is submitted.

value
    Initial or submitted value, depending on input type.

placeholder
    Short hint about expected input.

required
    Requires a value before submission.

disabled
    Prevents interaction and normally prevents submission of the control.

readonly
    Prevents editing while generally allowing the value to be submitted.
"""
)


# ============================================================================
# 5. TEXT INPUT
# ============================================================================

text_input_example = """
<label for="full-name">Full name:</label>
<input
    type="text"
    id="full-name"
    name="full_name"
    placeholder="Enter your full name"
    required
>
"""

print("\n5. TEXT INPUT")
print(text_input_example)

print(
    """
type="text" is used for ordinary single-line text.

Example submitted data:

full_name=Atul Pandey

Common mistake:
Using placeholder as a replacement for a label.

A placeholder disappears or becomes less prominent while typing.
A visible or programmatically accessible label should identify the field.
"""
)


# ============================================================================
# 6. EMAIL INPUT
# ============================================================================

email_example = """
<label for="email">Email address:</label>
<input
    type="email"
    id="email"
    name="email"
    required
    autocomplete="email"
>
"""

print("\n6. EMAIL INPUT")
print(email_example)

print(
    """
type="email" requests email-oriented input and enables browser validation.

Important limitation:
Browser email validation checks basic structural patterns.
It does not prove that an email address belongs to the user or even that the
mailbox exists.

Server-side validation remains necessary.
"""
)


# ============================================================================
# 7. PASSWORD INPUT
# ============================================================================

password_example = """
<label for="password">Password:</label>
<input
    type="password"
    id="password"
    name="password"
    minlength="8"
    required
    autocomplete="new-password"
>
"""

print("\n7. PASSWORD INPUT")
print(password_example)

print(
    """
type="password" masks characters visually.

Important:
Visual masking is not encryption.

A secure password system requires:
- HTTPS
- Secure server-side password handling
- Strong password hashing
- Protection against brute-force attacks
- Secure session management

Never rely only on client-side validation for security.
"""
)


# ============================================================================
# 8. NUMBER INPUT
# ============================================================================

number_example = """
<label for="age">Age:</label>
<input
    type="number"
    id="age"
    name="age"
    min="18"
    max="120"
    step="1"
    required
>
"""

print("\n8. NUMBER INPUT")
print(number_example)

print(
    """
type="number" represents numeric input.

Important attributes:

min
    Minimum allowed value.

max
    Maximum allowed value.

step
    Allowed increment.

Example:
min="0" max="100" step="0.5"

Common mistake:
Assuming type="number" automatically guarantees trustworthy server-side data.
Client-side values can be modified or requests can be sent manually.

Validate numeric data on the server.
"""
)


# ============================================================================
# 9. DATE, TIME, AND RELATED INPUT TYPES
# ============================================================================

date_example = """
<label for="birth-date">Date of birth:</label>
<input
    type="date"
    id="birth-date"
    name="birth_date"
    required
>
"""

print("\n9. DATE AND TIME INPUT TYPES")
print(date_example)

print(
    """
Common date and time input types:

date
    Date without a time.

time
    Time of day.

datetime-local
    Date and time without timezone information.

month
    Month and year.

week
    Week number and year.

Browser appearance may differ depending on browser and operating system.
Do not depend on one specific visual implementation.
"""
)


# ============================================================================
# 10. OTHER USEFUL INPUT TYPES
# ============================================================================

other_inputs_example = """
<label for="website">Website:</label>
<input type="url" id="website" name="website">

<label for="phone">Phone:</label>
<input type="tel" id="phone" name="phone">

<label for="search">Search:</label>
<input type="search" id="search" name="search">

<label for="favorite-color">Favorite color:</label>
<input type="color" id="favorite-color" name="favorite_color">

<label for="satisfaction">Satisfaction:</label>
<input
    type="range"
    id="satisfaction"
    name="satisfaction"
    min="1"
    max="10"
    value="5"
>
"""

print("\n10. OTHER INPUT TYPES")
print(other_inputs_example)

print(
    """
Important input types:

url
    Accepts URL-oriented input.

tel
    Used for telephone-related input.
    It does not automatically validate every international phone number.

search
    Semantically represents search input.

color
    Allows color selection.

range
    Provides a numeric range control.

hidden
    Stores data not visibly editable through the control.

file
    Allows file selection.

checkbox
    Represents independent yes/no or multiple-choice selections.

radio
    Represents mutually exclusive choices within a group.
"""
)


# ============================================================================
# 11. LABELS
# ============================================================================

print("\n11. LABELS")

label_example = """
<label for="username">Username:</label>
<input type="text" id="username" name="username">
"""

print(label_example)

wrapped_label_example = """
<label>
    Username:
    <input type="text" name="username">
</label>
"""

print("Alternative label structure:")
print(wrapped_label_example)

print(
    """
Labels improve usability and accessibility.

Explicit association:

<label for="username">Username</label>
<input id="username">

The label's for value matches the input's id.

Benefits:
- Screen readers can identify the control
- Clicking the label can focus the input
- Forms become easier to understand

Common mistake:
Using duplicate id values.

Each id should be unique within the document.
"""
)


# ============================================================================
# 12. TEXTAREA
# ============================================================================

textarea_example = """
<label for="message">Message:</label>
<textarea
    id="message"
    name="message"
    rows="6"
    cols="40"
    minlength="10"
    maxlength="1000"
    required
></textarea>
"""

print("\n12. TEXTAREA")
print(textarea_example)

print(
    """
<textarea> is used for multi-line text.

Important difference from input:
<textarea> is not written as a self-closing single-line input element.

The initial text, when present, appears between the opening and closing tags.

Example:

<textarea name="comment">Initial text</textarea>

Useful attributes include:
- rows
- cols
- minlength
- maxlength
- required
- placeholder
- readonly
- disabled
"""
)


# ============================================================================
# 13. SELECT AND OPTION
# ============================================================================

select_example = """
<label for="country">Country:</label>

<select id="country" name="country" required>
    <option value="">Select a country</option>
    <option value="IN">India</option>
    <option value="US">United States</option>
    <option value="JP">Japan</option>
</select>
"""

print("\n13. SELECT AND OPTION")
print(select_example)

print(
    """
<select> creates a selection control.

<option> represents an available choice.

The value attribute is usually the submitted value.

Example:

<option value="IN">India</option>

The user sees:
India

The submitted value is:
IN

A useful placeholder-like first option can use an empty value:

<option value="">Select a country</option>

When required is used, an empty value can help prevent an unselected placeholder
from being accepted.
"""
)


# ============================================================================
# 14. MULTIPLE SELECT
# ============================================================================

multiple_select_example = """
<label for="skills">Skills:</label>

<select
    id="skills"
    name="skills"
    multiple
    size="5"
>
    <option value="python">Python</option>
    <option value="javascript">JavaScript</option>
    <option value="sql">SQL</option>
    <option value="postgresql">PostgreSQL</option>
    <option value="html">HTML</option>
</select>
"""

print("\n14. MULTIPLE SELECT")
print(multiple_select_example)

print(
    """
multiple allows more than one option to be selected.

Server-side processing must account for repeated values.

Conceptually:

skills=python
skills=sql
skills=html

Different server frameworks represent repeated form keys differently.
Some return a list directly while others require a method for retrieving all
values associated with the same name.
"""
)


# ============================================================================
# 15. CHECKBOXES
# ============================================================================

checkbox_example = """
<fieldset>
    <legend>Programming languages</legend>

    <label>
        <input type="checkbox" name="languages" value="python">
        Python
    </label>

    <label>
        <input type="checkbox" name="languages" value="javascript">
        JavaScript
    </label>

    <label>
        <input type="checkbox" name="languages" value="cpp">
        C++
    </label>
</fieldset>
"""

print("\n15. CHECKBOXES")
print(checkbox_example)

print(
    """
Checkboxes are independent selections.

Multiple checkboxes may use the same name when multiple values belong to one
logical category.

Example submitted values:

languages=python
languages=cpp

Important edge case:
An unchecked checkbox is normally not submitted.

Therefore, a server cannot always assume that an absent checkbox value means
the user explicitly sent the value False without considering the form design.
"""
)


# ============================================================================
# 16. RADIO BUTTONS
# ============================================================================

radio_example = """
<fieldset>
    <legend>Preferred contact method</legend>

    <label>
        <input
            type="radio"
            name="contact_method"
            value="email"
            required
        >
        Email
    </label>

    <label>
        <input
            type="radio"
            name="contact_method"
            value="phone"
        >
        Phone
    </label>

    <label>
        <input
            type="radio"
            name="contact_method"
            value="message"
        >
        Message
    </label>
</fieldset>
"""

print("\n16. RADIO BUTTONS")
print(radio_example)

print(
    """
Radio buttons are mutually exclusive when they share the same name.

Correct grouping:

name="contact_method"

for all options.

Common mistake:
Giving each radio button a different name.

Incorrect:

name="email"
name="phone"
name="message"

That allows multiple radio buttons to be selected because they become separate
groups.
"""
)


# ============================================================================
# 17. FIELDSET AND LEGEND
# ============================================================================

print("\n17. FIELDSET AND LEGEND")

fieldset_example = """
<fieldset>
    <legend>Account information</legend>

    <label for="account-name">Name:</label>
    <input
        type="text"
        id="account-name"
        name="account_name"
        required
    >

    <label for="account-email">Email:</label>
    <input
        type="email"
        id="account-email"
        name="account_email"
        required
    >
</fieldset>
"""

print(fieldset_example)

print(
    """
<fieldset> groups related controls.

<legend> provides a caption for the group.

They are especially useful for:
- Radio groups
- Checkbox groups
- Related personal information
- Billing sections
- Account settings

They improve semantic structure and accessibility.
"""
)


# ============================================================================
# 18. SUBMIT AND RESET CONTROLS
# ============================================================================

submit_example = """
<button type="submit">Create Account</button>
<button type="reset">Reset Form</button>

<input type="submit" value="Submit">
"""

print("\n18. SUBMIT AND RESET")
print(submit_example)

print(
    """
type="submit" sends the form according to its action and method.

A <button> inside a form defaults to submit behavior in many situations when
type is not explicitly specified.

Best practice:
Explicitly specify button types.

For example:

<button type="submit">Save</button>
<button type="button">Open Preview</button>

This avoids accidental form submission.

Reset buttons restore form controls to their initial values.
They may be confusing because users can accidentally lose entered information.
"""
)


# ============================================================================
# 19. VALIDATION ATTRIBUTES
# ============================================================================

print("\n19. HTML VALIDATION ATTRIBUTES")

validation_example = """
<label for="username">Username:</label>
<input
    type="text"
    id="username"
    name="username"
    required
    minlength="3"
    maxlength="20"
    pattern="[A-Za-z0-9_]+"
>

<label for="age">Age:</label>
<input
    type="number"
    id="age"
    name="age"
    required
    min="18"
    max="120"
>

<label for="email">Email:</label>
<input
    type="email"
    id="email"
    name="email"
    required
>
"""

print(validation_example)

print(
    """
Important validation attributes:

required
    Field must have an acceptable value.

minlength
    Minimum character length for supported text controls.

maxlength
    Maximum character length for supported text controls.

min
    Minimum numeric or date-related value.

max
    Maximum numeric or date-related value.

step
    Required increment for compatible numeric or date/time values.

pattern
    Regular-expression-based pattern constraint.

type
    Certain input types provide built-in constraint behavior.

Important:
HTML validation improves user experience.
It is not a security boundary.

Server-side validation is mandatory for important data.
"""
)


# ============================================================================
# 20. PYTHON SIMULATION OF FORM VALIDATION
# ============================================================================

print("\n20. PYTHON VALIDATION SIMULATION")


def validate_required(value: Any) -> bool:
    """
    Simulates the general idea of a required text-like field.

    None and empty/whitespace-only strings are treated as missing.
    """
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    return True


def validate_length(value: str, minimum: int, maximum: int) -> List[str]:
    """Validate string length and return all detected errors."""
    errors = []

    if len(value) < minimum:
        errors.append(
            f"Value must contain at least {minimum} characters."
        )

    if len(value) > maximum:
        errors.append(
            f"Value must contain at most {maximum} characters."
        )

    return errors


sample_username = "atul_pandey"

print("Username:", sample_username)
print("Required valid:", validate_required(sample_username))
print("Length validation:", validate_length(sample_username, 3, 20))


# ============================================================================
# 21. PATTERN VALIDATION WITH PYTHON
# ============================================================================

import re

print("\n21. PATTERN VALIDATION")


def validate_username_pattern(username: str) -> bool:
    """
    Similar in spirit to:

    pattern="[A-Za-z0-9_]+"

    This accepts letters, numbers, and underscores.
    """
    return re.fullmatch(r"[A-Za-z0-9_]+", username) is not None


username_tests = [
    "atul",
    "atul_pandey",
    "user123",
    "user-name",
    "user name",
    "",
]

for username in username_tests:
    print(
        f"{username!r:20} -> "
        f"{validate_username_pattern(username)}"
    )


# ============================================================================
# 22. EMAIL VALIDATION SIMULATION
# ============================================================================

print("\n22. EMAIL VALIDATION")


def basic_email_validation(email: str) -> bool:
    """
    Demonstration only.

    Real email validation is more complicated than a simple regular expression.
    Server-side systems often use additional checks and confirmation workflows.
    """
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.fullmatch(pattern, email) is not None


email_tests = [
    "person@example.com",
    "student@university.edu",
    "invalid-email",
    "missing@domain",
    "@missing-user.com",
]

for email in email_tests:
    print(
        f"{email!r:30} -> "
        f"{basic_email_validation(email)}"
    )


# ============================================================================
# 23. NUMERIC VALIDATION
# ============================================================================

print("\n23. NUMERIC VALIDATION")


def validate_number(
    value: Any,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
    step: Optional[float] = None,
) -> List[str]:
    """
    Validate numeric input.

    This demonstrates the ideas behind min, max, and step.
    """
    errors = []

    try:
        number = float(value)
    except (TypeError, ValueError):
        return ["Value is not a valid number."]

    if minimum is not None and number < minimum:
        errors.append(f"Value must be at least {minimum}.")

    if maximum is not None and number > maximum:
        errors.append(f"Value must be at most {maximum}.")

    if step is not None and minimum is not None:
        difference = (number - minimum) / step

        # Floating-point arithmetic can produce tiny precision errors.
        if abs(difference - round(difference)) > 1e-9:
            errors.append(
                f"Value must follow increments of {step} "
                f"starting from {minimum}."
            )

    return errors


number_tests = [
    18,
    17,
    25,
    120,
    121,
    "not-a-number",
]

for test_value in number_tests:
    result = validate_number(
        test_value,
        minimum=18,
        maximum=120,
        step=1,
    )

    print(f"{test_value!r:15} -> {result or 'Valid'}")


# ============================================================================
# 24. REPRESENTING FORM FIELDS IN PYTHON
# ============================================================================

print("\n24. FORM FIELD MODEL")


@dataclass
class FormField:
    """
    A simplified representation of a form field.

    HTML itself does not use this Python class.
    The class demonstrates how applications may model validation rules.
    """

    name: str
    label: str
    required: bool = False
    validator: Optional[Callable[[Any], List[str]]] = None

    def validate(self, value: Any) -> List[str]:
        errors = []

        if self.required and not validate_required(value):
            errors.append(f"{self.label} is required.")

            # Stop here for an empty required field.
            # Running validators against missing values can create misleading errors.
            return errors

        # Optional empty values are accepted here.
        if not validate_required(value):
            return errors

        if self.validator is not None:
            errors.extend(self.validator(value))

        return errors


def username_validator(value: str) -> List[str]:
    errors = []

    if not isinstance(value, str):
        return ["Username must be text."]

    errors.extend(validate_length(value, 3, 20))

    if not validate_username_pattern(value):
        errors.append(
            "Username may contain only letters, numbers, and underscores."
        )

    return errors


username_field = FormField(
    name="username",
    label="Username",
    required=True,
    validator=username_validator,
)

for value in ["atul", "a", "atul pandey", ""]:
    print(
        f"Value: {value!r:15} "
        f"Errors: {username_field.validate(value)}"
    )


# ============================================================================
# 25. COMPLETE FORM MODEL
# ============================================================================

print("\n25. COMPLETE FORM VALIDATION MODEL")


@dataclass
class Form:
    """
    A simplified server-side-style form validator.

    It demonstrates why server-side validation must independently verify data.
    """

    fields: List[FormField] = field(default_factory=list)

    def validate(self, submitted_data: Dict[str, Any]) -> Dict[str, List[str]]:
        validation_errors: Dict[str, List[str]] = {}

        for form_field in self.fields:
            value = submitted_data.get(form_field.name)
            errors = form_field.validate(value)

            if errors:
                validation_errors[form_field.name] = errors

        return validation_errors


def email_validator(value: str) -> List[str]:
    if basic_email_validation(value):
        return []

    return ["Enter a valid email address."]


def age_validator(value: Any) -> List[str]:
    return validate_number(
        value,
        minimum=18,
        maximum=120,
        step=1,
    )


registration_form = Form(
    fields=[
        FormField(
            name="username",
            label="Username",
            required=True,
            validator=username_validator,
        ),
        FormField(
            name="email",
            label="Email address",
            required=True,
            validator=email_validator,
        ),
        FormField(
            name="age",
            label="Age",
            required=True,
            validator=age_validator,
        ),
    ]
)

valid_submission = {
    "username": "atul_pandey",
    "email": "atul@example.com",
    "age": "33",
}

invalid_submission = {
    "username": "a",
    "email": "invalid-email",
    "age": "15",
}

print("Valid submission errors:")
print(registration_form.validate(valid_submission))

print("\nInvalid submission errors:")
print(registration_form.validate(invalid_submission))


# ============================================================================
# 26. CHECKBOX SUBMISSION BEHAVIOR
# ============================================================================

print("\n26. CHECKBOX SUBMISSION BEHAVIOR")


def simulate_checkbox_submission(
    selected_languages: List[str],
) -> List[tuple]:
    """
    Simulates repeated name/value pairs from multiple checked checkboxes.
    """
    submitted_pairs = []

    for language in selected_languages:
        submitted_pairs.append(("languages", language))

    return submitted_pairs


selected = ["python", "sql", "html"]

checkbox_pairs = simulate_checkbox_submission(selected)

print("Selected values:")
print(selected)

print("Submitted key/value pairs:")
print(checkbox_pairs)

print(
    """
If no checkbox is selected, the corresponding field may be absent entirely.

Application code should distinguish between:
- A missing field
- An empty list
- A false-like value
- An intentionally selected value

The correct interpretation depends on the application's data model.
"""
)


# ============================================================================
# 27. RADIO BUTTON VALIDATION
# ============================================================================

print("\n27. RADIO BUTTON VALIDATION")


def validate_choice(
    selected_value: Optional[str],
    allowed_values: List[str],
) -> List[str]:
    """Validate a mutually exclusive selection."""
    if selected_value is None:
        return ["A selection is required."]

    if selected_value not in allowed_values:
        return ["Selected value is not allowed."]

    return []


allowed_contact_methods = [
    "email",
    "phone",
    "message",
]

radio_tests = [
    "email",
    "phone",
    "unknown",
    None,
]

for selected_value in radio_tests:
    errors = validate_choice(
        selected_value,
        allowed_contact_methods,
    )

    print(
        f"Selection: {selected_value!r:10} "
        f"Result: {errors or 'Valid'}"
    )


# ============================================================================
# 28. SELECT VALIDATION
# ============================================================================

print("\n28. SELECT VALIDATION")


def validate_country(country_code: str) -> List[str]:
    allowed_countries = {"IN", "US", "JP"}

    if not country_code:
        return ["Country selection is required."]

    if country_code not in allowed_countries:
        return ["Unsupported country selection."]

    return []


country_tests = ["IN", "US", "", "XX"]

for country in country_tests:
    print(
        f"Country: {country!r:5} "
        f"Result: {validate_country(country) or 'Valid'}"
    )


# ============================================================================
# 29. MULTIPLE SELECT VALIDATION
# ============================================================================

print("\n29. MULTIPLE SELECT VALIDATION")


def validate_multiple_choices(
    selected_values: List[str],
    allowed_values: set,
    minimum_selections: int = 0,
    maximum_selections: Optional[int] = None,
) -> List[str]:
    errors = []

    if len(selected_values) < minimum_selections:
        errors.append(
            f"Select at least {minimum_selections} value(s)."
        )

    if (
        maximum_selections is not None
        and len(selected_values) > maximum_selections
    ):
        errors.append(
            f"Select no more than {maximum_selections} value(s)."
        )

    invalid_values = [
        value
        for value in selected_values
        if value not in allowed_values
    ]

    if invalid_values:
        errors.append(
            f"Invalid selections: {invalid_values}"
        )

    return errors


skill_result = validate_multiple_choices(
    selected_values=["python", "sql"],
    allowed_values={"python", "javascript", "sql", "html"},
    minimum_selections=1,
    maximum_selections=3,
)

print("Skill validation:", skill_result or "Valid")


# ============================================================================
# 30. DISABLED VERSUS READONLY
# ============================================================================

print("\n30. DISABLED VS READONLY")

print(
    """
disabled:

<input
    type="text"
    name="account_id"
    value="123"
    disabled
>

A disabled control cannot normally be edited and is generally not submitted.

readonly:

<input
    type="text"
    name="account_id"
    value="123"
    readonly
>

A readonly control cannot normally be edited by the user, but its value is
generally included in form submission.

Important design consideration:
Do not use readonly or hidden fields as security controls.
A user can manipulate client-side data before sending a request.
"""
)


# ============================================================================
# 31. HIDDEN INPUTS
# ============================================================================

hidden_input_example = """
<input
    type="hidden"
    name="form_version"
    value="registration_v2"
>
"""

print("\n31. HIDDEN INPUTS")
print(hidden_input_example)

print(
    """
Hidden inputs are not visible controls.

They can carry values such as:
- Form metadata
- Record identifiers
- State information
- Tokens

Security warning:
Hidden does not mean secret.

Users can inspect and modify hidden fields.
Sensitive authorization decisions must be verified on the server.
"""
)


# ============================================================================
# 32. FILE INPUTS AND ENCTYPE
# ============================================================================

file_upload_example = """
<form
    action="/upload"
    method="post"
    enctype="multipart/form-data"
>
    <label for="document">Upload document:</label>

    <input
        type="file"
        id="document"
        name="document"
        accept=".pdf,.doc,.docx"
        required
    >

    <button type="submit">Upload</button>
</form>
"""

print("\n32. FILE INPUTS")
print(file_upload_example)

print(
    """
File uploads normally require:

enctype="multipart/form-data"

Important security considerations for file uploads:
- Validate file size
- Validate allowed content
- Do not trust only the file extension
- Use safe server-side filenames
- Prevent path traversal
- Store files outside executable directories when appropriate
- Scan or process untrusted files safely
- Apply authorization checks
- Limit upload size and rate
"""
)


# ============================================================================
# 33. FORM ENCODING CONCEPTS
# ============================================================================

print("\n33. FORM ENCODING")

sample_submission = {
    "username": "atul pandey",
    "email": "atul@example.com",
    "country": "IN",
}

encoded_submission = urlencode(sample_submission)

print("Form data:", sample_submission)
print("application/x-www-form-urlencoded representation:")
print(encoded_submission)

print(
    """
Common enctype values:

application/x-www-form-urlencoded
    Standard encoding for many forms.

multipart/form-data
    Required for typical file uploads.

text/plain
    Limited use and generally not preferred for structured application data.

The server must understand how incoming data is encoded.
"""
)


# ============================================================================
# 34. FORM ACTION AND BUTTON OVERRIDES
# ============================================================================

print("\n34. FORM ACTION AND BUTTON BEHAVIOR")

advanced_button_example = """
<form action="/save-profile" method="post">

    <input
        type="text"
        name="username"
        required
    >

    <button type="submit">
        Save
    </button>

    <button
        type="submit"
        formaction="/preview-profile"
        formmethod="post"
    >
        Preview
    </button>

</form>
"""

print(advanced_button_example)

print(
    """
Certain submit buttons can override form behavior.

Examples include:
- formaction
- formmethod
- formenctype
- formtarget
- formnovalidate

This allows different submission actions from the same form.

Use carefully because multiple submission paths increase testing and maintenance
requirements.
"""
)


# ============================================================================
# 35. AUTOCOMPLETE
# ============================================================================

print("\n35. AUTOCOMPLETE")

autocomplete_example = """
<label for="given-name">First name:</label>
<input
    type="text"
    id="given-name"
    name="given_name"
    autocomplete="given-name"
>

<label for="family-name">Last name:</label>
<input
    type="text"
    id="family-name"
    name="family_name"
    autocomplete="family-name"
>

<label for="email-address">Email:</label>
<input
    type="email"
    id="email-address"
    name="email"
    autocomplete="email"
>
"""

print(autocomplete_example)

print(
    """
Autocomplete tokens help browsers understand the purpose of fields.

Benefits:
- Faster form completion
- Better usability
- Better compatibility with password managers
- Improved accessibility in some workflows

Do not disable autocomplete without a strong reason.
"""
)


# ============================================================================
# 36. ACCESSIBILITY CONSIDERATIONS
# ============================================================================

print("\n36. ACCESSIBILITY")

print(
    """
Accessible form design should include:

1. Clear labels
   Every important input should have an understandable label.

2. Logical grouping
   Use fieldset and legend for related controls.

3. Clear required-field communication
   Do not rely only on color or symbols.

4. Understandable error messages
   Explain what is wrong and how to correct it.

5. Keyboard usability
   Users should be able to navigate and operate controls with a keyboard.

6. Semantic HTML
   Prefer native HTML controls when they satisfy the requirement.

7. Focus management
   Dynamic interfaces should maintain predictable focus behavior.

8. Error association
   Error information should be programmatically associated with the relevant
   field when building advanced custom interfaces.

Native HTML controls often provide substantial accessibility behavior by default.
Replacing them with custom controls increases implementation responsibility.
"""
)


# ============================================================================
# 37. CLIENT-SIDE VS SERVER-SIDE VALIDATION
# ============================================================================

print("\n37. CLIENT-SIDE VS SERVER-SIDE VALIDATION")

print(
    """
Client-side validation:

Examples:
- required
- minlength
- maxlength
- pattern
- min
- max
- input type constraints

Benefits:
- Immediate feedback
- Reduced accidental invalid submissions
- Better user experience

Limitations:
- Can be bypassed
- Browser behavior may vary
- Cannot be trusted for authorization or security

Server-side validation:

The server independently verifies:
- Required fields
- Data types
- Length limits
- Allowed values
- Permissions
- Business rules
- Security constraints

Rule:
Client-side validation improves usability.
Server-side validation protects application integrity.
"""
)


# ============================================================================
# 38. CROSS-FIELD VALIDATION
# ============================================================================

print("\n38. CROSS-FIELD VALIDATION")


def validate_password_confirmation(
    password: str,
    confirmation: str,
) -> List[str]:
    """
    Demonstrates validation involving multiple fields.

    A single HTML attribute cannot express every business rule.
    """
    errors = []

    if password != confirmation:
        errors.append("Password and confirmation do not match.")

    return errors


password_tests = [
    ("SecurePassword123", "SecurePassword123"),
    ("SecurePassword123", "DifferentPassword"),
]

for password, confirmation in password_tests:
    result = validate_password_confirmation(
        password,
        confirmation,
    )

    print(
        f"Passwords match: {not result}"
        f" | Errors: {result}"
    )


# ============================================================================
# 39. FORM DATA NORMALIZATION
# ============================================================================

print("\n39. FORM DATA NORMALIZATION")


def normalize_text(value: Optional[str]) -> str:
    """
    Demonstrates a common server-side preprocessing step.

    Trimming surrounding whitespace can be useful for many text fields.

    Caution:
    Not every field should be transformed.
    Passwords and other sensitive values should generally not be altered
    automatically because whitespace may be intentional.
    """
    if value is None:
        return ""

    return value.strip()


raw_name = "   Atul Pandey   "
normalized_name = normalize_text(raw_name)

print("Raw value:", repr(raw_name))
print("Normalized value:", repr(normalized_name))


# ============================================================================
# 40. COMPLETE HTML REGISTRATION FORM
# ============================================================================

complete_registration_form = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >
    <title>Registration Form</title>
</head>

<body>

    <h1>Create an Account</h1>

    <form
        action="/register"
        method="post"
        autocomplete="on"
    >

        <fieldset>
            <legend>Personal Information</legend>

            <p>
                <label for="full-name">
                    Full name:
                </label>

                <input
                    type="text"
                    id="full-name"
                    name="full_name"
                    required
                    minlength="2"
                    maxlength="100"
                    autocomplete="name"
                >
            </p>

            <p>
                <label for="email">
                    Email address:
                </label>

                <input
                    type="email"
                    id="email"
                    name="email"
                    required
                    autocomplete="email"
                >
            </p>

            <p>
                <label for="age">
                    Age:
                </label>

                <input
                    type="number"
                    id="age"
                    name="age"
                    min="18"
                    max="120"
                    required
                >
            </p>

            <p>
                <label for="country">
                    Country:
                </label>

                <select
                    id="country"
                    name="country"
                    required
                >
                    <option value="">
                        Select a country
                    </option>

                    <option value="IN">
                        India
                    </option>

                    <option value="US">
                        United States
                    </option>

                    <option value="JP">
                        Japan
                    </option>
                </select>
            </p>

        </fieldset>

        <fieldset>
            <legend>Account Information</legend>

            <p>
                <label for="username">
                    Username:
                </label>

                <input
                    type="text"
                    id="username"
                    name="username"
                    required
                    minlength="3"
                    maxlength="20"
                    pattern="[A-Za-z0-9_]+"
                    autocomplete="username"
                >
            </p>

            <p>
                <label for="password">
                    Password:
                </label>

                <input
                    type="password"
                    id="password"
                    name="password"
                    required
                    minlength="8"
                    autocomplete="new-password"
                >
            </p>

        </fieldset>

        <fieldset>
            <legend>Preferences</legend>

            <p>
                Preferred contact method:
            </p>

            <label>
                <input
                    type="radio"
                    name="contact_method"
                    value="email"
                    required
                >
                Email
            </label>

            <label>
                <input
                    type="radio"
                    name="contact_method"
                    value="phone"
                >
                Phone
            </label>

            <label>
                <input
                    type="radio"
                    name="contact_method"
                    value="message"
                >
                Message
            </label>

            <p>
                Skills:
            </p>

            <label>
                <input
                    type="checkbox"
                    name="skills"
                    value="python"
                >
                Python
            </label>

            <label>
                <input
                    type="checkbox"
                    name="skills"
                    value="sql"
                >
                SQL
            </label>

            <label>
                <input
                    type="checkbox"
                    name="skills"
                    value="javascript"
                >
                JavaScript
            </label>

        </fieldset>

        <p>
            <label for="message">
                Additional information:
            </label>

            <textarea
                id="message"
                name="message"
                rows="6"
                maxlength="1000"
            ></textarea>
        </p>

        <p>
            <label>
                <input
                    type="checkbox"
                    name="terms_accepted"
                    value="yes"
                    required
                >
                I accept the terms.
            </label>
        </p>

        <button type="submit">
            Create Account
        </button>

        <button type="reset">
            Reset
        </button>

    </form>

</body>
</html>
"""

print("\n40. COMPLETE REGISTRATION FORM")
print(complete_registration_form)


# ============================================================================
# 41. COMMON MISTAKES
# ============================================================================

print("\n41. COMMON HTML FORM MISTAKES")

common_mistakes = [
    (
        "Missing name attribute",
        "The field may not produce the expected submitted key/value data."
    ),
    (
        "Using placeholder instead of label",
        "Users and assistive technologies may lack a persistent field name."
    ),
    (
        "Duplicate id values",
        "Label association, CSS, and JavaScript behavior can become ambiguous."
    ),
    (
        "Different names for radio buttons",
        "The buttons stop behaving as one mutually exclusive group."
    ),
    (
        "Relying only on HTML validation",
        "Requests can bypass browser validation."
    ),
    (
        "Using hidden inputs for authorization",
        "Users can modify hidden values."
    ),
    (
        "Using disabled when submission is required",
        "Disabled controls are generally not submitted."
    ),
    (
        "Forgetting multipart/form-data for file uploads",
        "The server may not receive uploaded files correctly."
    ),
    (
        "Omitting explicit button types",
        "Buttons may accidentally submit forms."
    ),
    (
        "Trusting client-side values",
        "Attackers can alter requests before they reach the server."
    ),
]

for number, (mistake, explanation) in enumerate(
    common_mistakes,
    start=1,
):
    print(f"{number}. {mistake}")
    print(f"   {explanation}")


# ============================================================================
# 42. SECURITY CONSIDERATIONS
# ============================================================================

print("\n42. SECURITY CONSIDERATIONS")

print(
    """
HTML forms are interfaces, not security boundaries.

Important security practices:

1. Use HTTPS
   Protect data in transit.

2. Validate on the server
   Never trust client-side validation alone.

3. Authorize server-side actions
   A submitted identifier does not prove permission.

4. Protect against cross-site request forgery
   State-changing authenticated requests may require anti-CSRF protections.

5. Escape output appropriately
   Untrusted submitted text must not automatically be rendered as executable HTML.

6. Use parameterized database queries
   Avoid constructing database queries directly from form values.

7. Limit request size
   Prevent excessively large requests and uploads.

8. Validate uploaded files
   Treat uploaded files as untrusted.

9. Protect authentication workflows
   Use secure password storage and rate limiting where appropriate.

10. Avoid exposing secrets
    Hidden inputs and browser-side code are not secure secret storage.
"""
)


# ============================================================================
# 43. PERFORMANCE AND USER EXPERIENCE
# ============================================================================

print("\n43. PERFORMANCE AND USER EXPERIENCE")

print(
    """
Form design affects application performance and usability.

Useful practices:

- Keep forms focused on necessary information.
- Avoid requesting data that is not needed.
- Use appropriate input types for mobile and desktop interfaces.
- Avoid unnecessary network requests while users type.
- Debounce expensive client-side checks.
- Keep validation feedback understandable.
- Preserve user-entered data after recoverable server-side errors.
- Avoid large client-side dependencies for simple validation.
- Test slow network conditions when forms perform asynchronous operations.

A technically valid form can still provide a poor experience if users cannot
understand errors or recover from mistakes.
"""
)


# ============================================================================
# 44. DEBUGGING FORM DATA
# ============================================================================

print("\n44. DEBUGGING FORM DATA")


def inspect_submission(
    submitted_data: Dict[str, Any],
) -> None:
    """
    Simple debugging helper demonstrating inspection of submitted data.
    """
    print("Received form fields:")

    for key, value in submitted_data.items():
        print(
            f"  {key!r}: {value!r} "
            f"(type={type(value).__name__})"
        )


debug_submission = {
    "username": "atul_pandey",
    "age": "33",
    "country": "IN",
    "skills": ["python", "sql"],
}

inspect_submission(debug_submission)

print(
    """
Important debugging questions:

- Does the control have a name attribute?
- Is the control disabled?
- Is the expected value being submitted?
- Are repeated values represented correctly?
- Does the server parse the encoding correctly?
- Are validation rules consistent between client and server?
- Are values strings when the server expects numbers?
- Are empty fields absent or explicitly represented?
"""
)


# ============================================================================
# 45. FORM DATA TYPE CONVERSION
# ============================================================================

print("\n45. FORM DATA TYPE CONVERSION")


def parse_integer(value: str) -> Optional[int]:
    """
    Convert a submitted string to an integer safely.

    HTML form submissions are frequently represented as strings by the time
    application code processes them.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


age_inputs = ["33", "18", "not-a-number", "", None]

for age_value in age_inputs:
    parsed_age = parse_integer(age_value)
    print(
        f"Raw: {age_value!r:15} "
        f"Parsed: {parsed_age!r}"
    )


# ============================================================================
# 46. BUSINESS RULE VALIDATION
# ============================================================================

print("\n46. BUSINESS RULE VALIDATION")


def validate_registration_business_rules(
    submitted_data: Dict[str, Any],
) -> List[str]:
    """
    Demonstrates rules beyond basic HTML attributes.
    """
    errors = []

    age = parse_integer(submitted_data.get("age"))

    if age is None:
        errors.append("Age must be a valid integer.")
    elif age < 18:
        errors.append("Registration is available only to adults.")

    selected_skills = submitted_data.get("skills", [])

    if not isinstance(selected_skills, list):
        selected_skills = [selected_skills]

    if "python" in selected_skills and age is not None and age < 18:
        errors.append(
            "Python training registration requires adult eligibility."
        )

    return errors


business_rule_submission = {
    "age": "17",
    "skills": ["python"],
}

print(
    validate_registration_business_rules(
        business_rule_submission
    )
)


# ============================================================================
# 47. FINAL FORM DESIGN CHECKLIST
# ============================================================================

print("\n47. FORM DESIGN CHECKLIST")

form_checklist = [
    "Every important control has a meaningful label.",
    "Each id value is unique.",
    "Every submitted control has an appropriate name.",
    "Radio buttons in one group share the same name.",
    "Checkbox behavior is correctly handled when unchecked.",
    "Select options have meaningful submitted values.",
    "Required fields are clearly communicated.",
    "Client-side validation improves usability.",
    "Server-side validation independently verifies data.",
    "Sensitive data is transmitted through HTTPS.",
    "Authorization decisions are made on the server.",
    "File uploads use appropriate encoding and validation.",
    "Buttons have explicit types.",
    "Errors explain how users can correct invalid input.",
    "Keyboard navigation works.",
    "The form is tested with empty, invalid, extreme, and unexpected values.",
]

for item_number, item in enumerate(form_checklist, start=1):
    print(f"{item_number}. {item}")


# ============================================================================
# 48. END OF STUDY SCRIPT
# ============================================================================

print("\n" + "=" * 80)
print("END OF HTML FORMS STUDY SCRIPT")
print("=" * 80)
