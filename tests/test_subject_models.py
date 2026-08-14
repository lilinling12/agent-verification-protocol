from __future__ import annotations

import unittest

from avp_ref.subject import SubjectResult, SubjectStatus


class SubjectResultInvariantTest(unittest.TestCase):
    def test_completed_result_accepts_optional_string_report(self) -> None:
        result = SubjectResult(SubjectStatus.COMPLETED, "done", 1)
        self.assertIs(SubjectStatus.COMPLETED, result.status)
        self.assertEqual("done", result.report)

        without_report = SubjectResult(SubjectStatus.COMPLETED, None, 0)
        self.assertIsNone(without_report.report)

    def test_non_completion_or_malformed_report_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SubjectResult("FAILED", "invalid", 1)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            SubjectResult(SubjectStatus.COMPLETED, {"invalid": True}, 1)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
