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


def orientation_from_resolution(resolution: object) -> str:
    if not isinstance(resolution, str):
        raise ValueError("The configured resolution must be a string")

    match = re.fullmatch(r"([1-9]\d*)x([1-9]\d*)", resolution)
    if match is None:
        raise ValueError(f"Invalid configured resolution: {resolution!r}")

    width, height = (int(value) for value in match.groups())
    return "portrait" if height > width else "landscape"


def configured_orientation(options_path: Path = OPTIONS_PATH) -> str:
    with options_path.open(encoding="utf-8") as options_file:
        options = json.load(options_file)
    if not isinstance(options, dict):
        raise ValueError("The app options must be a JSON object")
    return orientation_from_resolution(options.get("resolution", "768x1024"))


class Controller:
    def __init__(
        self,
        default_orientation: str,
        command_runner: CommandRunner = subprocess.run,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if default_orientation not in {"portrait", "landscape"}:
            raise ValueError(f"Unsupported default orientation: {default_orientation!r}")

        self._default_orientation = default_orientation
        self._orientation: str | None = None
        self._command_runner = command_runner
        self._clock = clock
        self._last_activity: float | None = None
        self._lock = threading.Lock()

    def record_activity(self, orientation: str) -> None:
        if orientation not in {"portrait", "landscape"}:
            raise ValueError(f"Unsupported orientation: {orientation!r}")

        with self._lock:
            if orientation != self._orientation:
                rotation = (
                    "normal"
                    if orientation == self._default_orientation
                    else "left"
                )
                self._command_runner(
                    ["xrandr", "--output", "screen", "--rotate", rotation],
                    check=True,
                    capture_output=True,
                    text=True,
                )
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
    controller = Controller(configured_orientation())
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
