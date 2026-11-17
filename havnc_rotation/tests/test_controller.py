import http.client
import json
import threading
import unittest
from types import SimpleNamespace

from controller import Controller, ControllerHTTPServer, orientation_from_resolution


class FakeCommandRunner:
    def __init__(self) -> None:
        self.status = "STOPPED"
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
        return SimpleNamespace(stdout="")


class ControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = 1_000.0
        self.runner = FakeCommandRunner()
        self.controller = Controller(
            "portrait",
            command_runner=self.runner,
            clock=lambda: self.now,
        )

    def test_resolution_sets_default_orientation(self) -> None:
        self.assertEqual(orientation_from_resolution("768x1024"), "portrait")
        self.assertEqual(orientation_from_resolution("1024x768"), "landscape")

    def test_invalid_resolution_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            orientation_from_resolution("0x768")

    def test_orientation_change_rotates_virtual_display_and_starts_browser(self) -> None:
        self.controller.record_activity("landscape")

        self.assertIn(
            ["xrandr", "--output", "screen", "--rotate", "left"],
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

    def test_initial_orientation_resets_virtual_display(self) -> None:
        self.controller.record_activity("portrait")

        self.assertIn(
            ["xrandr", "--output", "screen", "--rotate", "normal"],
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

    def test_activity_endpoint_wakes_and_orients_browser(self) -> None:
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
                ["xrandr", "--output", "screen", "--rotate", "left"],
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
