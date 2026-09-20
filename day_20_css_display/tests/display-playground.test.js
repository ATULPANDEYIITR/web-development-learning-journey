// File: tests/display-playground.test.js
import { strict as assert } from "node:assert";
import test from "node:test";

function buildCssState({
    display = "block",
    visibility = "visible",
    overflow = "visible",
    position = "static",
    width = 180,
    height = 120,
} = {}) {
    return {
        display,
        visibility,
        overflow,
        position,
        width: `${width}px`,
        height: `${height}px`,
    };
}

test("defaults represent a normal block box", () => {
    assert.deepEqual(buildCssState(), {
        display: "block",
        visibility: "visible",
        overflow: "visible",
        position: "static",
        width: "180px",
        height: "120px",
    });
});

test("inline display is represented without modifying unrelated properties", () => {
    const state = buildCssState({ display: "inline" });

    assert.equal(state.display, "inline");
    assert.equal(state.visibility, "visible");
    assert.equal(state.position, "static");
});

test("display none is different from visibility hidden", () => {
    const removed = buildCssState({ display: "none" });
    const hidden = buildCssState({ visibility: "hidden" });

    assert.equal(removed.display, "none");
    assert.equal(hidden.visibility, "hidden");
    assert.equal(hidden.display, "block");
});

test("overflow modes are accepted as independent CSS values", () => {
    for (const value of ["visible", "hidden", "clip", "auto", "scroll"]) {
        const state = buildCssState({ overflow: value });
        assert.equal(state.overflow, value);
    }
});

test("positioning mode can change without changing display", () => {
    const state = buildCssState({
        display: "inline-block",
        position: "relative",
    });

    assert.equal(state.display, "inline-block");
    assert.equal(state.position, "relative");
});

test("dimensions are serialized as CSS lengths", () => {
    const state = buildCssState({
        width: 320,
        height: 220,
    });

    assert.equal(state.width, "320px");
    assert.equal(state.height, "220px");
});
