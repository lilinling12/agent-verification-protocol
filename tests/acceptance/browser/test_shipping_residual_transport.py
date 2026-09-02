from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tests.acceptance.browser import shipping_residual_evidence_runner as runner


class ShippingResidualTransportTest(unittest.TestCase):
    """Verify transport lifecycle without requiring a locally installed browser."""

    def test_safari_reuses_one_service_across_multiple_session_creations(self) -> None:
        progress = runner._ExecutionProgress()
        service = Mock()
        drivers = [Mock(), Mock(), Mock()]

        with (
            patch.object(runner, "_new_safari_service", return_value=service) as new_service,
            patch.object(runner, "_create_driver", side_effect=drivers) as create_driver,
        ):
            with runner._DriverTransport(
                "safari",
                progress,
                safari_diagnostic_log=Path("browser-evidence/safaridriver.log"),
            ) as transport:
                created = [
                    transport.create("clean"),
                    transport.create("residual"),
                    transport.create("recreated"),
                ]

        self.assertEqual(drivers, created)
        new_service.assert_called_once_with(Path("browser-evidence/safaridriver.log"))
        service.start.assert_called_once_with()
        service.stop.assert_called_once_with()
        self.assertEqual(3, progress.created_session_count)
        self.assertTrue(progress.safari_service_reused)
        self.assertTrue(progress.safari_service_started)
        self.assertTrue(progress.safari_service_stopped)
        self.assertEqual(3, create_driver.call_count)
        for call in create_driver.call_args_list:
            self.assertEqual("safari", call.args[0])
            self.assertIs(service, call.kwargs["safari_service"])

    def test_session_cleanup_does_not_mask_primary_failure(self) -> None:
        progress = runner._ExecutionProgress()
        driver = Mock()
        driver.quit.side_effect = RuntimeError("quit failed")
        transport = Mock()
        transport.create.return_value = driver

        with self.assertRaisesRegex(ValueError, "primary failure"):
            with runner._browser_session(transport, "residual", progress):
                progress.enter("residual:semantic-probe")
                raise ValueError("primary failure")

        self.assertEqual("residual:semantic-probe", progress.failure_stage)
        self.assertEqual(1, len(progress.cleanup_errors))
        cleanup = progress.cleanup_errors[0]
        self.assertEqual("residual:session-quit-after-failure", cleanup["stage"])
        self.assertEqual("RuntimeError", cleanup["error_type"])
        self.assertEqual("quit failed", cleanup["error"])

    def test_transport_cleanup_does_not_mask_primary_failure(self) -> None:
        progress = runner._ExecutionProgress()
        service = Mock()
        service.stop.side_effect = RuntimeError("service stop failed")

        with patch.object(runner, "_new_safari_service", return_value=service):
            with self.assertRaisesRegex(ValueError, "primary failure"):
                with runner._DriverTransport(
                    "safari",
                    progress,
                    safari_diagnostic_log=Path("browser-evidence/safaridriver.log"),
                ):
                    progress.enter("recreated:semantic-probe")
                    raise ValueError("primary failure")

        self.assertEqual("recreated:semantic-probe", progress.failure_stage)
        self.assertEqual(1, len(progress.cleanup_errors))
        self.assertEqual(
            "transport:safari-driver-service-stop",
            progress.cleanup_errors[0]["stage"],
        )

    def test_diagnostic_tail_is_bounded_to_failure_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "safaridriver.log"
            log.write_text("a" * (runner._DIAGNOSTIC_TAIL_LIMIT + 17), encoding="utf-8")

            tail = runner._diagnostic_tail(log)

        self.assertIsNotNone(tail)
        self.assertEqual(runner._DIAGNOSTIC_TAIL_LIMIT, len(tail or ""))
        self.assertEqual("a" * runner._DIAGNOSTIC_TAIL_LIMIT, tail)


if __name__ == "__main__":
    unittest.main()
