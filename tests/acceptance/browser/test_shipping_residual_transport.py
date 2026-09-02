from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tests.acceptance.browser import shipping_residual_evidence_runner as runner


class ShippingResidualTransportTest(unittest.TestCase):
    """Verify transport lifecycle without requiring a locally installed browser."""

    def test_safari_uses_one_stopped_service_generation_per_session(self) -> None:
        progress = runner._ExecutionProgress()
        services = [Mock(), Mock(), Mock()]
        drivers = [Mock(), Mock(), Mock()]
        for service in services:
            service.process.poll.return_value = 0

        with (
            patch.object(runner, "_new_safari_service", side_effect=services) as new_service,
            patch.object(runner, "_create_driver", side_effect=drivers) as create_driver,
        ):
            transport = runner._DriverTransport(
                "safari",
                progress,
                safari_diagnostic_dir=Path("browser-evidence/diagnostics"),
            )
            for role, expected_driver, expected_service in zip(
                ("clean", "residual", "recreated"),
                drivers,
                services,
                strict=True,
            ):
                with runner._browser_session(transport, role, progress) as driver:
                    self.assertIs(expected_driver, driver)
                expected_driver.quit.assert_called_once_with()
                expected_service.start.assert_called_once_with()
                expected_service.stop.assert_called_once_with()

        self.assertEqual(3, new_service.call_count)
        self.assertEqual(3, create_driver.call_count)
        self.assertEqual(3, progress.created_session_count)
        self.assertEqual(3, progress.completed_session_count)
        self.assertEqual(3, progress.safari_service_generations_started)
        self.assertEqual(3, progress.safari_service_generations_stopped)
        for call, service in zip(create_driver.call_args_list, services, strict=True):
            self.assertEqual("safari", call.args[0])
            self.assertIs(service, call.kwargs["safari_service"])

    def test_safari_service_is_stopped_when_session_creation_fails(self) -> None:
        progress = runner._ExecutionProgress()
        service = Mock()
        service.process.poll.return_value = 0

        with (
            patch.object(runner, "_new_safari_service", return_value=service),
            patch.object(runner, "_create_driver", side_effect=RuntimeError("create failed")),
        ):
            transport = runner._DriverTransport(
                "safari",
                progress,
                safari_diagnostic_dir=Path("browser-evidence/diagnostics"),
            )
            with self.assertRaisesRegex(RuntimeError, "create failed"):
                with runner._browser_session(transport, "residual", progress):
                    self.fail("session body must not execute")

        self.assertEqual("residual:session-create", progress.failure_stage)
        service.stop.assert_called_once_with()
        self.assertEqual(1, progress.safari_service_generations_started)
        self.assertEqual(1, progress.safari_service_generations_stopped)
        self.assertEqual(0, progress.created_session_count)

    def test_session_cleanup_does_not_mask_primary_failure(self) -> None:
        progress = runner._ExecutionProgress()
        driver = Mock()
        driver.quit.side_effect = RuntimeError("quit failed")
        transport = Mock()
        transport.create.return_value = (driver, None)

        # Use the real cleanup implementation while keeping driver creation mocked.
        real_transport = runner._DriverTransport(
            "chrome",
            progress,
            safari_diagnostic_dir=Path("browser-evidence/diagnostics"),
        )
        real_transport.create = transport.create

        with self.assertRaisesRegex(ValueError, "primary failure"):
            with runner._browser_session(real_transport, "residual", progress):
                progress.enter("residual:semantic-probe")
                raise ValueError("primary failure")

        self.assertEqual("residual:semantic-probe", progress.failure_stage)
        self.assertEqual(1, len(progress.cleanup_errors))
        cleanup = progress.cleanup_errors[0]
        self.assertEqual("residual:session-quit-after-failure", cleanup["stage"])
        self.assertEqual("RuntimeError", cleanup["error_type"])
        self.assertEqual("quit failed", cleanup["error"])

    def test_service_cleanup_does_not_mask_primary_failure(self) -> None:
        progress = runner._ExecutionProgress()
        driver = Mock()
        service = Mock()
        service.stop.side_effect = RuntimeError("service stop failed")
        transport = runner._DriverTransport(
            "safari",
            progress,
            safari_diagnostic_dir=Path("browser-evidence/diagnostics"),
        )
        transport.create = Mock(return_value=(driver, service))

        with self.assertRaisesRegex(ValueError, "primary failure"):
            with runner._browser_session(transport, "recreated", progress):
                progress.enter("recreated:semantic-probe")
                raise ValueError("primary failure")

        self.assertEqual("recreated:semantic-probe", progress.failure_stage)
        self.assertEqual(1, len(progress.cleanup_errors))
        self.assertEqual(
            "recreated:safaridriver-service-stop",
            progress.cleanup_errors[0]["stage"],
        )

    def test_diagnostic_tails_are_bounded_and_role_scoped(self) -> None:
        progress = runner._ExecutionProgress()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            clean_log = root / "clean.log"
            residual_log = root / "residual.log"
            clean_log.write_text("a" * (runner._DIAGNOSTIC_TAIL_LIMIT + 17), encoding="utf-8")
            residual_log.write_text("residual diagnostic", encoding="utf-8")
            progress.safari_diagnostic_logs = {
                "clean": clean_log,
                "residual": residual_log,
            }

            tails = runner._safari_diagnostic_tails(progress)

        self.assertEqual(runner._DIAGNOSTIC_TAIL_LIMIT, len(tails["clean"]))
        self.assertEqual("a" * runner._DIAGNOSTIC_TAIL_LIMIT, tails["clean"])
        self.assertEqual("residual diagnostic", tails["residual"])


if __name__ == "__main__":
    unittest.main()
