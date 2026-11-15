## Mon HAVNC Rotation

Local adaptation of [gnyman/havnc](https://github.com/gnyman/havnc), based on
upstream commit `290c61766d1eaabfa889ae570371d7a7741d1b25`. The upstream BSD
2-Clause license is retained in [LICENSE.md](./LICENSE.md).

HAVNC serves a Home Assistant dashboard through Chromium and noVNC. This local
version keeps the existing `url`, `resolution`, and `password` options and adds:

- The virtual display follows the orientation of the connected browser (portrait
  or landscape).
- Touch, mouse, keyboard, page-load, and page-resume activity wakes Chromium.
- Chromium stops after 5 minutes without user interaction. The lightweight VNC
  service remains available so the next interaction can restart Chromium.

The app's existing noVNC address on port `8080` is unchanged. Install this
source in the Supervisor local-app repository directory for
`local_havnc_rotation` and rebuild it through Home Assistant Apps; Supervisor
handles the build.

## Validation

Run the controller unit tests with:

```sh
python3 -m unittest discover -s tests -v
```

The device-orientation behavior requires a browser that reports viewport
orientation changes. Other browsers can still wake the dashboard through
touch, mouse, or keyboard activity.
