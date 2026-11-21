# Changelog

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

