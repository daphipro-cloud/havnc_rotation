# Changelog

# 1.1.15

- Debounce viewport fitting and orientation updates to avoid intermediate
  scaling and repeated framebuffer changes while the screen rotates.

# 1.1.14

- Include the XRandR command-line utility required by the orientation
  controller.

# 1.1.13

- Fix Supervisor configuration parsing so Xvfb can start with the resolution
  validation and dynamic framebuffer setup enabled.

# 1.1.12

- Resize the Xvfb display for the browser orientation so Chromium renders the
  dashboard natively instead of rotating a portrait capture.

# 1.1.11

- Reconcile Safari's viewport dimensions with the iPad's orientation and refit
  after iOS orientation changes settle.

# 1.1.10

- Use the original Safari viewport dimensions and apply rotation through both
  WebKit-prefixed style property spellings.

# 1.1.9

- Measure the actual noVNC viewport container and support WebKit-prefixed
  transforms on older iPad browsers.

# 1.1.8

- Rotate a wrapper around the noVNC canvas so viewport rotation does not
  overwrite the canvas transform used internally by noVNC.

# 1.1.7

- Use the broadly supported CSS transform property for landscape rotation on
  older iPad browsers.

# 1.1.6

- Version the viewport fitting script URL and disable browser caching for the
  main page and viewport fitting script.

# 1.1.5

- Fill the entire browser viewport in portrait and landscape, stretching the
  remote image slightly when its aspect ratio differs from the device.
- Map mouse and touch input across the stretched canvas.

# 1.1.4

- Rotate the noVNC canvas client-side when viewport and remote display
  orientations differ, including transformed mouse and touch coordinates.
- Wake Chromium without relying on unsupported XRandR output rotation.

# 1.1.3

- Include the viewport scaling script in the built image.
- Restore the previous Xvfb with x0vncserver display stack.

# 1.1.2

- Scale the noVNC canvas to fit the available viewport after orientation or
  framebuffer changes.

# 1.1.1

- Replace Xvfb with TigerVNC Xvnc, which supports the requested screen rotation.
- Detect the active RandR output and include command details in rotation errors.

# 1.1.0

- Restore the local app from the upstream HAVNC source.
- Follow the connected browser's portrait or landscape orientation.
- Stop Chromium after five minutes without user activity and wake it on return.

## [0.0.9]

- Improve security (where improve actually means add some basic security so not everyone on the network can access your HA dashboard).
**Note**: Because a password is required the upgrade will end with a error telling you to check the supervisor logs. It's because there is no password set. After the upgrade, go to Configuration and add a password and then start the add-on again.

## [0.0.8]

- Initial public release.

