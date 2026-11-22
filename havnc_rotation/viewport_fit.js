(function (root) {
    "use strict";

    function validDimensions(width, height) {
        return Number.isFinite(width) && width > 0 &&
            Number.isFinite(height) && height > 0;
    }

    function canvasSizeToFill(viewportWidth, viewportHeight, framebufferWidth, framebufferHeight, rotated) {
        if (!validDimensions(viewportWidth, viewportHeight) ||
            !validDimensions(framebufferWidth, framebufferHeight)) {
            return null;
        }

        return {
            width: rotated ? viewportHeight : viewportWidth,
            height: rotated ? viewportWidth : viewportHeight
        };
    }

    function rotationForViewport(viewportWidth, viewportHeight, framebufferWidth, framebufferHeight) {
        if (!validDimensions(viewportWidth, viewportHeight) ||
            !validDimensions(framebufferWidth, framebufferHeight)) {
            return 0;
        }

        return (viewportWidth > viewportHeight) ===
            (framebufferWidth > framebufferHeight) ? 0 : -90;
    }

    function setElementRotation(element, rotation) {
        if (!element || !element.style) {
            throw new TypeError("A styled element is required");
        }

        var style = element.style;
        var transform = rotation ? "rotate(" + rotation + "deg)" : "none";
        var properties = [
            ["transform", "transformOrigin"],
            ["webkitTransform", "webkitTransformOrigin"],
            ["WebkitTransform", "WebkitTransformOrigin"]
        ];
        var supported = false;

        for (var index = 0; index < properties.length; index += 1) {
            var transformProperty = properties[index][0];
            var originProperty = properties[index][1];
            if (typeof style[transformProperty] === "undefined") {
                continue;
            }

            style[transformProperty] = transform;
            style[originProperty] = "50% 50%";
            supported = true;
        }

        if (!supported) {
            throw new Error("CSS transforms are not supported");
        }
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
        canvasSizeToFill: canvasSizeToFill,
        mapPointer: mapPointer,
        rotationForViewport: rotationForViewport,
        setElementRotation: setElementRotation
    };

    if (typeof module !== "undefined" && module.exports) {
        module.exports = {
            canvasSizeToFill: canvasSizeToFill,
            mapPointer: mapPointer,
            rotationForViewport: rotationForViewport,
            setElementRotation: setElementRotation
        };
    }
}(typeof window === "undefined" ? globalThis : window));
