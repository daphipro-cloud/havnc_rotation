"use strict";

const assert = require("node:assert/strict");
const { mapPointer, rotationForViewport, scaleToFit } = require("../viewport_fit");

assert.equal(scaleToFit(1194, 834, 1024, 768), 834 / 768);
assert.equal(scaleToFit(834, 1194, 768, 1024), 834 / 768);
assert.equal(scaleToFit(1000, 800, 1200, 600), 1000 / 1200);
assert.equal(scaleToFit(0, 800, 1200, 600), 1);
assert.equal(scaleToFit(1194, 834, 768, 1024, true), 834 / 768);
assert.equal(rotationForViewport(1194, 834, 768, 1024), -90);
assert.equal(rotationForViewport(834, 1194, 768, 1024), 0);
assert.deepEqual(
    mapPointer(0, 0, {left: 0, top: 0, width: 200, height: 100}, 100, 200, -90),
    {x: 99, y: 0}
);
assert.deepEqual(
    mapPointer(200, 100, {left: 0, top: 0, width: 200, height: 100}, 100, 200, -90),
    {x: 0, y: 199}
);
assert.equal(mapPointer(0, 0, {left: 0, top: 0, width: 0, height: 100}, 100, 200, -90), null);

console.log("Viewport fit tests passed.");
