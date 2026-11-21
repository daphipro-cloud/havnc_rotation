(function (root) {
    "use strict";

    function validDimensions(width, height) {
        return Number.isFinite(width) && width > 0 &&
            Number.isFinite(height) && height > 0;
    }

    function scaleToFit(viewportWidth, viewportHeight, framebufferWidth, framebufferHeight, rotated) {
        var dimensions = [viewportWidth, viewportHeight, framebufferWidth, framebufferHeight];
        if (dimensions.some(function (value) {
            return !Number.isFinite(value) || value <= 0;
        })) {
            return 1;
        }

        if (rotated) {
            var swap = framebufferWidth;
            framebufferWidth = framebufferHeight;
            framebufferHeight = swap;
        }

        return Math.min(
            viewportWidth / framebufferWidth,
            viewportHeight / framebufferHeight
        );
    }

    function rotationForViewport(viewportWidth, viewportHeight, framebufferWidth, framebufferHeight) {
        if (!validDimensions(viewportWidth, viewportHeight) ||
            !validDimensions(framebufferWidth, framebufferHeight)) {
            return 0;
        }

        return (viewportWidth > viewportHeight) ===
            (framebufferWidth > framebufferHeight) ? 0 : -90;
    }

    function mapPointer(clientX, clientY, rect, framebufferWidth, framebufferHeight, rotation) {
        if (!Number.isFinite(clientX) || !Number.isFinite(clientY) ||
            !rect || !Number.isFinite(rect.left) || !Number.isFinite(rect.top) ||
            !validDimensions(rect.width, rect.height) ||
            !validDimensions(framebufferWidth, framebufferHeight)) {
            return null;
        }

        var horizontal = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
        var vertical = Math.max(0, Math.min(1, (clientY - rect.top) / rect.height));
        var x;
        var y;

        if (rotation === -90) {
            x = 1 - vertical;
            y = horizontal;
        } else if (rotation === 90) {
            x = vertical;
            y = 1 - horizontal;
        } else {
            x = horizontal;
            y = vertical;
        }

        return {
            x: Math.round(x * (framebufferWidth - 1)),
            y: Math.round(y * (framebufferHeight - 1))
        };
    }

    root.HAVNCViewport = {
        mapPointer: mapPointer,
        rotationForViewport: rotationForViewport,
        scaleToFit: scaleToFit
    };

    if (typeof module !== "undefined" && module.exports) {
        module.exports = {
            mapPointer: mapPointer,
            rotationForViewport: rotationForViewport,
            scaleToFit: scaleToFit
        };
    }
}(typeof window === "undefined" ? globalThis : window));
