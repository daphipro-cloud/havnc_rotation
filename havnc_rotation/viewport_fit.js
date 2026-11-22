(function (root) {
    "use strict";

    function validDimensions(width, height) {
        return Number.isFinite(width) && width > 0 &&
            Number.isFinite(height) && height > 0;
    }

    function viewportDimensions(width, height, orientation) {
        if (!validDimensions(width, height)) {
            return null;
        }

        var viewportIsLandscape = width > height;
        var absoluteOrientation = Math.abs(orientation);
        var hasDeviceOrientation = absoluteOrientation === 0 ||
            absoluteOrientation === 90 || absoluteOrientation === 180;
        var deviceIsLandscape = absoluteOrientation === 90;
        if (hasDeviceOrientation && viewportIsLandscape !== deviceIsLandscape) {
            return {width: height, height: width};
        }

        return {width: width, height: height};
    }

    function canvasSizeToFill(viewportWidth, viewportHeight, framebufferWidth, framebufferHeight) {
        if (!validDimensions(viewportWidth, viewportHeight) ||
            !validDimensions(framebufferWidth, framebufferHeight)) {
            return null;
        }

        return {
            width: viewportWidth,
            height: viewportHeight
        };
    }

    function mapPointer(clientX, clientY, rect, framebufferWidth, framebufferHeight) {
        if (!Number.isFinite(clientX) || !Number.isFinite(clientY) ||
            !rect || !Number.isFinite(rect.left) || !Number.isFinite(rect.top) ||
            !validDimensions(rect.width, rect.height) ||
            !validDimensions(framebufferWidth, framebufferHeight)) {
            return null;
        }

        var horizontal = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
        var vertical = Math.max(0, Math.min(1, (clientY - rect.top) / rect.height));

        return {
            x: Math.round(horizontal * (framebufferWidth - 1)),
            y: Math.round(vertical * (framebufferHeight - 1))
        };
    }

    root.HAVNCViewport = {
        canvasSizeToFill: canvasSizeToFill,
        mapPointer: mapPointer,
        viewportDimensions: viewportDimensions
    };

    if (typeof module !== "undefined" && module.exports) {
        module.exports = {
            canvasSizeToFill: canvasSizeToFill,
            mapPointer: mapPointer,
            viewportDimensions: viewportDimensions
        };
    }
}(typeof window === "undefined" ? globalThis : window));
