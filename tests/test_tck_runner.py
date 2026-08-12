from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from avp_ref import cli
from avp_ref.tck_adapter import (
    TCKAdapterError,
    TCKCaseResult,
    TCKRepository,
    TCKRunner,
    TCKStatus,
    validate_report,
)

ROOT = Path(__file__).resolve().parents[1]
NORMAL = "AVP-TCK-LIFECYCLE-NORMAL-001"
MATRIX = "AVP-TCK-LIFECYCLE-TRANSITION-MATRIX-001"
PAUSE = "AVP-TCK-LIFECYCLE-PAUSE-001"


class _SkippingMandatoryAdapter:
    supported_case_ids = frozenset({NORMAL})

    def evaluate(self, case):
        return TCKCaseResult(
            case_id=NORMAL,
            status=TCKStatus.SKIP,
            detail="invalid synthetic skip",
            skip_reason="synthetic",
        )


class TCKRunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = TCKRepository(ROOT)

    def test_repository_loads_registered_lifecycle_cases(self) -> None:
        cases = self.repository.load_cases("avp-core-v0.1")
        self.assertEqual(9, len(cases))
        self.assertEqual(9, len({item.case_id for item in cases}))

    def test_reference_runner_emits_valid_pass_and_conditional_skip(self) -> None:
        runner = TCKRunner.for_reference(self.repository)
        run = runner.run(selected_case_ids=(NORMAL, PAUSE))
        self.assertTrue(run.conformant)
        self.assertEqual(
            {"total": 2, "passed": 1, "failed": 0, "skipped": 1},
            run.report["summary"],
        )
        pause_result = next(item for item in run.case_results if item.case_id == PAUSE)
        self.assertIs(TCKStatus.SKIP, pause_result.status)
        self.assertEqual("condition-not-declared:pause-capability-advertised", pause_result.skip_reason)
        validate_report(run.report, self.repository, expected_profile="avp-core-v0.1")

    def test_reference_runtime_drift_is_reported_as_fail(self) -> None:
        runner = TCKRunner.for_reference(self.repository)
        run = runner.run(selected_case_ids=(MATRIX,))
        self.assertFalse(run.conformant)
        self.assertEqual(1, run.report["summary"]["failed"])
        self.assertIs(TCKStatus.FAIL, run.case_results[0].status)

    def test_declared_pause_capability_executes_instead_of_skipping(self) -> None:
        runner = TCKRunner.for_reference(
            self.repository,
            capabilities=("pause-capability-advertised",),
        )
        run = runner.run(selected_case_ids=(PAUSE,))
        self.assertEqual(0, run.report["summary"]["skipped"])
        self.assertIsNot(TCKStatus.SKIP, run.case_results[0].status)

    def test_report_validator_rejects_tampered_summary(self) -> None:
        run = TCKRunner.for_reference(self.repository).run(selected_case_ids=(NORMAL,))
        tampered = copy.deepcopy(run.report)
        tampered["summary"]["total"] = 99
        with self.assertRaisesRegex(TCKAdapterError, "summary mismatch"):
            validate_report(tampered, self.repository)

    def test_mandatory_case_cannot_be_skipped(self) -> None:
        runner = TCKRunner(
            self.repository,
            adapter=_SkippingMandatoryAdapter(),
            implementation={"name": "synthetic", "version": "1.0.0"},
        )
        with self.assertRaisesRegex(TCKAdapterError, "cannot be skipped"):
            runner.run(selected_case_ids=(NORMAL,))

    def test_case_path_cannot_escape_tck_case_root(self) -> None:
        with self.assertRaisesRegex(TCKAdapterError, "escapes case root"):
            self.repository._resolve_case_path("../../pyproject.toml")

    def test_skip_result_requires_reason(self) -> None:
        with self.assertRaisesRegex(ValueError, "require skip_reason"):
            TCKCaseResult(case_id=PAUSE, status=TCKStatus.SKIP, detail="not applicable")

    def test_cli_tck_run_outputs_json_and_zero_for_applicable_passes(self) -> None:
        output = io.StringIO()
        argv = [
            "avp",
            "tck",
            "run",
            "--repository-root",
            str(ROOT),
            "--case",
            NORMAL,
            "--case",
            PAUSE,
        ]
        with patch.object(sys, "argv", argv), redirect_stdout(output):
            cli.main()
        report = json.loads(output.getvalue())
        self.assertEqual(0, report["summary"]["failed"])
        self.assertEqual(1, report["summary"]["skipped"])

    def test_cli_writes_report_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "report.json"
            output = io.StringIO()
            argv = [
                "avp",
                "tck",
                "run",
                "--repository-root",
                str(ROOT),
                "--case",
                NORMAL,
                "--out",
                str(target),
            ]
            with patch.object(sys, "argv", argv), redirect_stdout(output):
                cli.main()
            report = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual({"total": 1, "passed": 1, "failed": 0, "skipped": 0}, report["summary"])
            acknowledgement = json.loads(output.getvalue())
            self.assertEqual(str(target), acknowledgement["output"])


if __name__ == "__main__":
    unittest.main()
