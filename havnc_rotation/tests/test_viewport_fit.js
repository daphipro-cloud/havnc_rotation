"use strict";

const assert = require("node:assert/strict");
const {
    canvasSizeToFill,
    mapPointer,
    viewportDimensions
} = require("../viewport_fit");

assert.deepEqual(
    viewportDimensions(768, 1024, 90),
    {width: 1024, height: 768}
);
assert.deepEqual(
    viewportDimensions(768, 1024, -90),
    {width: 1024, height: 768}
);
assert.deepEqual(
    viewportDimensions(1024, 768, 0),
    {width: 768, height: 1024}
);
assert.deepEqual(
    viewportDimensions(768, 1024, undefined),
    {width: 768, height: 1024}
);
assert.equal(viewportDimensions(0, 1024, 90), null);

assert.deepEqual(
    canvasSizeToFill(1194, 834, 1024, 768),
    {width: 1194, height: 834}
);
assert.deepEqual(
    canvasSizeToFill(834, 1194, 768, 1024),
    {width: 834, height: 1194}
);
assert.equal(canvasSizeToFill(0, 800, 768, 1024), null);
assert.deepEqual(
    mapPointer(0, 0, {left: 0, top: 0, width: 200, height: 100}, 100, 200),
    {x: 0, y: 0}
);
assert.deepEqual(
    mapPointer(200, 100, {left: 0, top: 0, width: 200, height: 100}, 100, 200),
    {x: 99, y: 199}
);
assert.deepEqual(
    mapPointer(100, 50, {left: 0, top: 0, width: 200, height: 100}, 100, 200),
    {x: 50, y: 100}
);
assert.equal(mapPointer(0, 0, {left: 0, top: 0, width: 0, height: 100}, 100, 200), null);

console.log("Viewport fit tests passed.");
