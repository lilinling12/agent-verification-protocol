from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Callable
from .runtime import ReferenceRuntime, SubjectSession


@dataclass(frozen=True)
class ReliabilityReport:
    runs: int
    valid_runs: int
    invalid_runs: int
    passes: int
    success_rate: float
    success_at_k: float
    all_success_k: float

    def to_dict(self):
        return asdict(self)


def run_repeated(subject: Callable[[SubjectSession, str], str], runs: int = 8,
                 target_order_id: str = "ord_1") -> ReliabilityReport:
    outcomes: list[bool] = []
    invalid = 0
    for _ in range(runs):
        rt = ReferenceRuntime()
        ep = rt.create_episode(f"Refund {target_order_id}")
        rt.run_subject(ep.episode_id, subject)
        rt.verify(ep.episode_id, target_order_id)
        if ep.validity.value != "VALID":
            invalid += 1
            continue
        outcomes.append(ep.task_verdict.value == "PASS")

    valid = len(outcomes)
    passes = sum(outcomes)
    rate = passes / valid if valid else 0.0
    success_at_k = 1.0 if any(outcomes) else 0.0
    all_success_k = 1.0 if outcomes and all(outcomes) else 0.0
    return ReliabilityReport(runs, valid, invalid, passes, rate, success_at_k, all_success_k)
