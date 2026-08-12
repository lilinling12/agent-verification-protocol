"""End-to-end smoke validation for the AVP TCK report pipeline."""

from __future__ import annotations

from pathlib import Path

from avp_ref.tck_adapter import TCKRepository, TCKRunner

ROOT = Path(__file__).resolve().parents[1]
NORMAL = "AVP-TCK-LIFECYCLE-NORMAL-001"
PAUSE = "AVP-TCK-LIFECYCLE-PAUSE-001"


def main() -> None:
    repository = TCKRepository(ROOT)
    run = TCKRunner.for_reference(repository).run(selected_case_ids=(NORMAL, PAUSE))
    expected = {"total": 2, "passed": 1, "failed": 0, "skipped": 1}
    if run.report["summary"] != expected:
        raise SystemExit(
            f"TCK report pipeline FAIL: expected summary {expected}, got {run.report['summary']}"
        )
    print(
        "TCK report pipeline OK: "
        f"registry={repository.registry_digest}, summary={run.report['summary']}"
    )


if __name__ == "__main__":
    main()
