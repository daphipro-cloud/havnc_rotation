from __future__ import annotations

import json
import logging
import re
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

LOGGER = logging.getLogger("havnc.controller")
IDLE_TIMEOUT_SECONDS = 300
IDLE_CHECK_INTERVAL_SECONDS = 1
OPTIONS_PATH = Path("/data/options.json")

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


def validate_resolution(resolution: object) -> str:
    if not isinstance(resolution, str):
        raise ValueError("The configured resolution must be a string")

    if re.fullmatch(r"([1-9]\d*)x([1-9]\d*)", resolution) is None:
        raise ValueError(f"Invalid configured resolution: {resolution!r}")

    return resolution


def resolution_for_orientation(resolution: str, orientation: str) -> str:
    validate_resolution(resolution)
    if orientation not in {"portrait", "landscape"}:
        raise ValueError(f"Unsupported orientation: {orientation!r}")

    width, height = (int(value) for value in resolution.split("x"))
    if (orientation == "landscape") == (width > height):
        return resolution
    return f"{height}x{width}"


def mode_line_arguments(width: int, height: int) -> list[str]:
    horizontal_front_porch = max(8, round(width * 0.02))
    horizontal_sync = max(8, round(width * 0.08))
    horizontal_back_porch = max(16, round(width * 0.10))
    vertical_front_porch = 3
    vertical_sync = 5
    vertical_back_porch = max(10, round(height * 0.02))
    horizontal_total = (
        width + horizontal_front_porch + horizontal_sync + horizontal_back_porch
    )
    vertical_total = (
        height + vertical_front_porch + vertical_sync + vertical_back_porch
    )
    pixel_clock = horizontal_total * vertical_total * 60 / 1_000_000

    return [
        f"HAVNC-{width}x{height}",
        f"{pixel_clock:.2f}",
        str(width),
        str(width + horizontal_front_porch),
        str(width + horizontal_front_porch + horizontal_sync),
        str(horizontal_total),
        str(height),
        str(height + vertical_front_porch),
        str(height + vertical_front_porch + vertical_sync),
        str(vertical_total),
        "-HSync",
        "+VSync",
    ]


def configured_resolution(options_path: Path = OPTIONS_PATH) -> str:
    with options_path.open(encoding="utf-8") as options_file:
        options = json.load(options_file)
    if not isinstance(options, dict):
        raise ValueError("The app options must be a JSON object")
    return validate_resolution(options.get("resolution", "768x1024"))


class Controller:
    def __init__(
        self,
        command_runner: CommandRunner = subprocess.run,
        clock: Callable[[], float] = time.monotonic,
        resolution: str = "768x1024",
    ) -> None:
        self._resolution = validate_resolution(resolution)
        self._command_runner = command_runner
        self._clock = clock
        self._last_activity: float | None = None
        self._lock = threading.Lock()
        self._orientation: str | None = None
        self._output_name: str | None = None

    def record_activity(self, orientation: str) -> None:
        if orientation not in {"portrait", "landscape"}:
            raise ValueError(f"Unsupported orientation: {orientation!r}")

        with self._lock:
            if orientation != self._orientation:
                self._set_display_orientation(orientation)
                self._orientation = orientation

            if not self._browser_is_active():
                self._command_runner(
                    [
                        "supervisorctl",
                        "-c",
                        "/config/supervisord.conf",
                        "start",
                        "Chromium",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

            self._last_activity = self._clock()

    def _set_display_orientation(self, orientation: str) -> None:
        width, height = (
            int(value)
            for value in resolution_for_orientation(
                self._resolution,
                orientation,
            ).split("x")
        )
        query = self._command_runner(
            ["xrandr", "--query"],
            check=True,
            capture_output=True,
            text=True,
        )

        outputs = []
        for line in query.stdout.splitlines():
            fields = line.split()
            if len(fields) >= 2 and fields[1] == "connected":
                outputs.append(fields[0])
        if len(outputs) != 1:
            raise RuntimeError(
                "Could not identify the active XRandR output: "
                f"{query.stdout!r} {query.stderr!r}"
            )
        self._output_name = outputs[0]

        mode_name = f"HAVNC-{width}x{height}"
        available_modes = set(
            re.findall(r"^\s+(\S+)\s+[\d.]+", query.stdout, re.MULTILINE)
        )
        if mode_name not in available_modes:
            self._command_runner(
                ["xrandr", "--newmode", *mode_line_arguments(width, height)],
                check=True,
                capture_output=True,
                text=True,
            )
            self._command_runner(
                ["xrandr", "--addmode", self._output_name, mode_name],
                check=True,
                capture_output=True,
                text=True,
            )

        self._command_runner(
            [
                "xrandr",
                "--output",
                self._output_name,
                "--mode",
                mode_name,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        current_screen = self._command_runner(
            ["xrandr", "--query"],
            check=True,
            capture_output=True,
            text=True,
        )
        screen_size = re.search(
            r"^Screen \d+: .*current (\d+) x (\d+)",
            current_screen.stdout,
            re.MULTILINE,
        )
        if screen_size is None or (int(screen_size[1]), int(screen_size[2])) != (
            width,
            height,
        ):
            raise RuntimeError(
                f"XRandR did not set the requested screen size {width}x{height}: "
                f"{current_screen.stdout!r}"
            )
        LOGGER.info(
            "Set Xvfb display orientation to %s (%dx%d)",
            orientation,
            width,
            height,
        )

    def stop_if_idle(self, now: float | None = None) -> bool:
        with self._lock:
            current_time = self._clock() if now is None else now
            if (
                self._last_activity is None
                or current_time - self._last_activity < IDLE_TIMEOUT_SECONDS
                or not self._browser_is_active()
            ):
                return False

            self._command_runner(
                [
                    "supervisorctl",
                    "-c",
                    "/config/supervisord.conf",
                    "stop",
                    "Chromium",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            LOGGER.info("Stopped Chromium after five minutes without user activity")
            return True

    def run_idle_watchdog(self) -> None:
        while True:
            try:
                self.stop_if_idle()
            except (OSError, RuntimeError, subprocess.CalledProcessError):
                LOGGER.exception("Could not check or stop the idle Chromium process")
            time.sleep(IDLE_CHECK_INTERVAL_SECONDS)

    def _browser_is_active(self) -> bool:
        result = self._command_runner(
            [
                "supervisorctl",
                "-c",
                "/config/supervisord.conf",
                "status",
                "Chromium",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        status = result.stdout.split(maxsplit=2)
        if len(status) < 2 or status[0] != "Chromium":
            raise RuntimeError(
                f"Could not read Chromium status (exit {result.returncode}): "
                f"{result.stdout!r} {result.stderr!r}"
            )
        if status[1] in {"RUNNING", "STARTING"}:
            return True
        if status[1] in {"STOPPED", "EXITED", "FATAL", "BACKOFF"}:
            return False
        raise RuntimeError(
            f"Unknown Chromium status (exit {result.returncode}): "
            f"{result.stdout!r} {result.stderr!r}"
        )


class ControllerHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], controller: Controller) -> None:
        self.controller = controller
        super().__init__(address, ActivityHandler)


class ActivityHandler(BaseHTTPRequestHandler):
    server: ControllerHTTPServer

    def do_GET(self) -> None:
        if self.path != "/health":
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"ok\n")

    def do_POST(self) -> None:
        if self.path != "/activity":
            self.send_error(404)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400, "Invalid Content-Length")
            return

        if content_length <= 0:
            self.send_error(400, "A request body is required")
            return

        if content_length > 1024:
            self.send_error(413, "Invalid request size")
            return

        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_error(400, "Invalid JSON body")
            return

        if not isinstance(payload, dict) or not isinstance(payload.get("orientation"), str):
            self.send_error(400, "An orientation is required")
            return

        try:
            self.server.controller.record_activity(payload["orientation"])
        except ValueError as error:
            self.send_error(400, str(error))
            return
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            LOGGER.exception("Could not apply user activity")
            self.send_error(503, "Could not wake or orient the browser")
            return

        self.send_response(204)
        self.end_headers()

    def log_message(self, format_string: str, *args: object) -> None:
        LOGGER.info("%s - %s", self.address_string(), format_string % args)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    configured_resolution()
    controller = Controller(resolution=configured_resolution())
    threading.Thread(
        target=controller.run_idle_watchdog,
        name="idle-watchdog",
        daemon=True,
    ).start()

    server = ControllerHTTPServer(("127.0.0.1", 8081), controller)
    LOGGER.info("HAVNC activity controller listening on 127.0.0.1:8081")
    server.serve_forever()


if __name__ == "__main__":
    main()
