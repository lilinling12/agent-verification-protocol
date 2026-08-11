from __future__ import annotations

from dataclasses import asdict

from avp_ref.reference import correct_subject, false_success_subject, wrong_target_subject
from avp_ref.reliability import run_repeated


def run_reference_benchmark(runs: int = 4) -> dict:
    subjects = {"correct": correct_subject, "false-success": false_success_subject, "wrong-target": wrong_target_subject}
    return {name: asdict(run_repeated(subject, runs=runs)) for name, subject in subjects.items()}
