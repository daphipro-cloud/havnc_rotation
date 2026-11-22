import http.client
import json
import threading
import unittest
from types import SimpleNamespace

from controller import (
    Controller,
    ControllerHTTPServer,
    mode_line_arguments,
    resolution_for_orientation,
    validate_resolution,
)


class FakeCommandRunner:
    def __init__(self) -> None:
        self.status = "STOPPED"
        self.display_size = "1024x1024"
        self.modes = {"1024x1024"}
        self.calls: list[list[str]] = []

    def __call__(self, command: list[str], **_kwargs: object) -> SimpleNamespace:
        self.calls.append(command)
        status_command = [
            "supervisorctl",
            "-c",
            "/config/supervisord.conf",
            "status",
            "Chromium",
        ]
        start_command = [
            "supervisorctl",
            "-c",
            "/config/supervisord.conf",
            "start",
            "Chromium",
        ]
        stop_command = [
            "supervisorctl",
            "-c",
            "/config/supervisord.conf",
            "stop",
            "Chromium",
        ]
        if command == status_command:
            return SimpleNamespace(stdout=f"Chromium {self.status}")
        if command == start_command:
            self.status = "RUNNING"
        elif command == stop_command:
            self.status = "STOPPED"
        elif command == ["xrandr", "--query"]:
            mode_lines = "\n".join(f"   {mode} 60.00" for mode in sorted(self.modes))
            return SimpleNamespace(
                stdout=(
                    f"Screen 0: minimum 1 x 1, current {self.display_size.replace('x', ' x ')}, "
                    "maximum 1024 x 1024\n"
                    f"screen connected {self.display_size}+0+0 0mm x 0mm\n"
                    f"{mode_lines}\n"
                )
            )
        elif command[:2] == ["xrandr", "--newmode"]:
            return SimpleNamespace(stdout="")
        elif command[:2] == ["xrandr", "--addmode"]:
            self.modes.add(command[-1])
            return SimpleNamespace(stdout="")
        elif command[:2] == ["xrandr", "--output"]:
            self.display_size = command[command.index("--mode") + 1].removeprefix(
                "HAVNC-"
            )
        return SimpleNamespace(stdout="")


class ControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = 1_000.0
        self.runner = FakeCommandRunner()
        self.controller = Controller(
            command_runner=self.runner,
            clock=lambda: self.now,
        )

    def test_valid_resolution_is_preserved(self) -> None:
        self.assertEqual(validate_resolution("768x1024"), "768x1024")

    def test_invalid_resolution_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_resolution("0x768")

    def test_resolution_matches_requested_orientation(self) -> None:
        self.assertEqual(
            resolution_for_orientation("768x1024", "portrait"),
            "768x1024",
        )
        self.assertEqual(
            resolution_for_orientation("768x1024", "landscape"),
            "1024x768",
        )
        self.assertEqual(
            resolution_for_orientation("1024x768", "landscape"),
            "1024x768",
        )

    def test_mode_line_defines_requested_dimensions(self) -> None:
        mode = mode_line_arguments(1024, 768)

        self.assertEqual(mode[0], "HAVNC-1024x768")
        self.assertEqual(mode[2], "1024")
        self.assertEqual(mode[6], "768")

    def test_activity_sets_landscape_framebuffer_before_starting_browser(self) -> None:
        self.controller.record_activity("landscape")

        set_landscape = [
            "xrandr",
            "--output",
            "screen",
            "--mode",
            "HAVNC-1024x768",
        ]
        start_browser = [
            "supervisorctl",
            "-c",
            "/config/supervisord.conf",
            "start",
            "Chromium",
        ]
        self.assertLess(
            self.runner.calls.index(set_landscape),
            self.runner.calls.index(start_browser),
        )
        self.assertIn(
            ["xrandr", "--newmode", *mode_line_arguments(1024, 768)],
            self.runner.calls,
        )

    def test_activity_changes_framebuffer_when_orientation_changes(self) -> None:
        self.controller.record_activity("landscape")
        self.controller.record_activity("portrait")

        self.assertIn(
            ["xrandr", "--output", "screen", "--mode", "HAVNC-768x1024"],
            self.runner.calls,
        )

    def test_five_minutes_without_activity_stops_browser(self) -> None:
        self.controller.record_activity("portrait")

        self.assertFalse(self.controller.stop_if_idle(now=self.now + 299))
        self.assertTrue(self.controller.stop_if_idle(now=self.now + 300))
        self.assertFalse(self.controller.stop_if_idle(now=self.now + 301))
        self.assertEqual(
            self.runner.calls.count(
                [
                    "supervisorctl",
                    "-c",
                    "/config/supervisord.conf",
                    "stop",
                    "Chromium",
                ]
            ),
            1,
        )

    def test_activity_after_idle_restarts_browser(self) -> None:
        self.controller.record_activity("portrait")
        self.controller.stop_if_idle(now=self.now + 300)
        self.now += 301

        self.controller.record_activity("portrait")

        self.assertEqual(
            self.runner.calls.count(
                [
                    "supervisorctl",
                    "-c",
                    "/config/supervisord.conf",
                    "start",
                    "Chromium",
                ]
            ),
            2,
        )

    def test_invalid_orientation_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.controller.record_activity("sideways")

    def test_activity_endpoint_wakes_browser(self) -> None:
        server = ControllerHTTPServer(("127.0.0.1", 0), self.controller)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.start()
        connection = http.client.HTTPConnection(*server.server_address)

        try:
            connection.request(
                "POST",
                "/activity",
                body=json.dumps({"orientation": "landscape"}),
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()

            self.assertEqual(response.status, 204)
            self.assertIn(
                ["xrandr", "--output", "screen", "--mode", "HAVNC-1024x768"],
                self.runner.calls,
            )
            self.assertIn(
                [
                    "supervisorctl",
                    "-c",
                    "/config/supervisord.conf",
                    "start",
                    "Chromium",
                ],
                self.runner.calls,
            )
        finally:
            connection.close()
            server.shutdown()
            server.server_close()
            server_thread.join()


if __name__ == "__main__":
    unittest.main()
