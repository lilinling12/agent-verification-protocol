"""End-to-end validation for the AVP TCK report pipeline and checked-in example."""

from __future__ import annotations

import json
from pathlib import Path

from avp_ref.tck_adapter import TCKRepository, TCKRunner, validate_report

ROOT = Path(__file__).resolve().parents[1]
NORMAL = "AVP-TCK-LIFECYCLE-NORMAL-001"
PAUSE = "AVP-TCK-LIFECYCLE-PAUSE-001"
EXAMPLE_REPORT = ROOT / "conformance/tck/reports/avp-core-v0.1.example.json"


def main() -> None:
    repository = TCKRepository(ROOT)

    run = TCKRunner.for_reference(repository).run(selected_case_ids=(NORMAL, PAUSE))
    expected = {"total": 2, "passed": 1, "failed": 0, "skipped": 1}
    if run.report["summary"] != expected:
        raise SystemExit(
            f"TCK report pipeline FAIL: expected summary {expected}, got {run.report['summary']}"
        )

    try:
        example = json.loads(EXAMPLE_REPORT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"TCK report example FAIL: cannot parse {EXAMPLE_REPORT}: {exc}") from exc
    if not isinstance(example, dict):
        raise SystemExit("TCK report example FAIL: root must be a JSON object")
    validate_report(example, repository, expected_profile="avp-core-v0.1")

    print(
        "TCK report pipeline OK: "
        f"registry={repository.registry_digest}, summary={run.report['summary']}, example=valid"
    )


if __name__ == "__main__":
    main()
