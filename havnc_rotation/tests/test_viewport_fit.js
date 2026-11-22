"use strict";

const assert = require("node:assert/strict");
const {
    canvasSizeToFill,
    mapPointer,
    rotationForViewport,
    setElementRotation
} = require("../viewport_fit");

assert.equal(rotationForViewport(1194, 834, 768, 1024), -90);
assert.equal(rotationForViewport(834, 1194, 768, 1024), 0);
assert.deepEqual(
    canvasSizeToFill(1194, 834, 768, 1024, true),
    {width: 834, height: 1194}
);
assert.deepEqual(
    canvasSizeToFill(834, 1194, 768, 1024, false),
    {width: 834, height: 1194}
);
assert.equal(canvasSizeToFill(0, 800, 768, 1024, false), null);
assert.deepEqual(
    mapPointer(0, 0, {left: 0, top: 0, width: 200, height: 100}, 100, 200, -90),
    {x: 99, y: 0}
);
assert.deepEqual(
    mapPointer(200, 100, {left: 0, top: 0, width: 200, height: 100}, 100, 200, -90),
    {x: 0, y: 199}
);
assert.deepEqual(
    mapPointer(100, 50, {left: 0, top: 0, width: 200, height: 100}, 100, 200, 0),
    {x: 50, y: 100}
);
assert.equal(mapPointer(0, 0, {left: 0, top: 0, width: 0, height: 100}, 100, 200, -90), null);

const standardStyle = {transform: "", transformOrigin: ""};
setElementRotation({style: standardStyle}, -90);
assert.equal(standardStyle.transform, "rotate(-90deg)");
assert.equal(standardStyle.transformOrigin, "50% 50%");

const webkitStyle = {WebkitTransform: "", WebkitTransformOrigin: ""};
setElementRotation({style: webkitStyle}, -90);
assert.equal(webkitStyle.WebkitTransform, "rotate(-90deg)");
assert.equal(webkitStyle.WebkitTransformOrigin, "50% 50%");

const lowercaseWebkitStyle = {webkitTransform: "", webkitTransformOrigin: ""};
setElementRotation({style: lowercaseWebkitStyle}, -90);
assert.equal(lowercaseWebkitStyle.webkitTransform, "rotate(-90deg)");
assert.equal(lowercaseWebkitStyle.webkitTransformOrigin, "50% 50%");

assert.throws(
    () => setElementRotation({style: {}}, -90),
    /CSS transforms are not supported/
);

console.log("Viewport fit tests passed.");
