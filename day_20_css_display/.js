// File: js/app.js
const controls = {
    display: document.querySelector("#display-select"),
    visibility: document.querySelector("#visibility-select"),
    overflow: document.querySelector("#overflow-select"),
    position: document.querySelector("#position-select"),
    width: document.querySelector("#width-range"),
    height: document.querySelector("#height-range"),
};

const target = document.querySelector("#playground-target");
const output = document.querySelector("#computed-output");
const widthValue = document.querySelector("#width-value");
const heightValue = document.querySelector("#height-value");
const resetButton = document.querySelector("#reset-playground");

const defaults = {
    display: "block",
    visibility: "visible",
    overflow: "visible",
    position: "static",
    width: 180,
    height: 120,
};

function applyPlaygroundState() {
    const width = `${controls.width.value}px`;
    const height = `${controls.height.value}px`;

    target.style.display = controls.display.value;
    target.style.visibility = controls.visibility.value;
    target.style.overflow = controls.overflow.value;
    target.style.position = controls.position.value;
    target.style.width = width;
    target.style.height = height;

    widthValue.value = width;
    heightValue.value = height;

    output.textContent = [
        `display: ${controls.display.value};`,
        `visibility: ${controls.visibility.value};`,
        `overflow: ${controls.overflow.value};`,
        `position: ${controls.position.value};`,
        `width: ${width};`,
        `height: ${height};`,
    ].join("\n");
}

function resetPlayground() {
    controls.display.value = defaults.display;
    controls.visibility.value = defaults.visibility;
    controls.overflow.value = defaults.overflow;
    controls.position.value = defaults.position;
    controls.width.value = String(defaults.width);
    controls.height.value = String(defaults.height);

    applyPlaygroundState();
}

Object.values(controls).forEach((control) => {
    control.addEventListener("input", applyPlaygroundState);
    control.addEventListener("change", applyPlaygroundState);
});

resetButton.addEventListener("click", resetPlayground);

applyPlaygroundState();
