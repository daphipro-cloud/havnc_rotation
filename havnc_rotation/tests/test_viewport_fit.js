"use strict";

const assert = require("node:assert/strict");
const { scaleToFit } = require("../viewport_fit");

assert.equal(scaleToFit(1194, 834, 1024, 768), 834 / 768);
assert.equal(scaleToFit(834, 1194, 768, 1024), 834 / 768);
assert.equal(scaleToFit(1000, 800, 1200, 600), 1000 / 1200);
assert.equal(scaleToFit(0, 800, 1200, 600), 1);

console.log("Viewport fit tests passed.");
