## Mon HAVNC Rotation

Local adaptation of [gnyman/havnc](https://github.com/gnyman/havnc), based on
upstream commit `290c61766d1eaabfa889ae570371d7a7741d1b25`. The upstream BSD
2-Clause license is retained in [LICENSE.md](./LICENSE.md).

HAVNC serves a Home Assistant dashboard through Chromium and noVNC. This local
version keeps the existing `url`, `resolution`, and `password` options and adds:

- The noVNC canvas rotates and fills the connected browser's portrait or
  landscape viewport, stretching slightly when the aspect ratios differ.
- Touch and mouse coordinates are mapped back to the rotated and stretched
  remote display.
- Touch, mouse, keyboard, page-load, and page-resume activity wakes Chromium.
- Chromium stops after 5 minutes without user interaction. The lightweight VNC
  service remains available so the next interaction can restart Chromium.

The app's existing noVNC address on port `8080` is unchanged. The add-on source
is in `havnc_rotation/`; Home Assistant Supervisor builds it when installing or
updating the app from this repository.

## Validation

Run the checks from the add-on source directory:

```sh
cd havnc_rotation
python3 -m unittest discover -s tests -v
node tests/test_viewport_fit.js
```

The device-orientation behavior requires a browser that reports viewport
orientation changes. Other browsers can still wake the dashboard through
touch, mouse, or keyboard activity.
