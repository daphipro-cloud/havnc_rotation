(function (root) {
    "use strict";

    function scaleToFit(viewportWidth, viewportHeight, framebufferWidth, framebufferHeight) {
        var dimensions = [viewportWidth, viewportHeight, framebufferWidth, framebufferHeight];
        if (dimensions.some(function (value) {
            return !Number.isFinite(value) || value <= 0;
        })) {
            return 1;
        }

        return Math.min(
            viewportWidth / framebufferWidth,
            viewportHeight / framebufferHeight
        );
    }

    root.HAVNCViewport = { scaleToFit: scaleToFit };

    if (typeof module !== "undefined" && module.exports) {
        module.exports = { scaleToFit: scaleToFit };
    }
}(typeof window === "undefined" ? globalThis : window));
