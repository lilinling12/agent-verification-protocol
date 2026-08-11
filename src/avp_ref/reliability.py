from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable, Mapping, Any

from avp_ref.models import Validity
from avp_ref.oracle import RefundOracle
from avp_ref.reference import reference_agent_system, reference_environment, reference_scenario
from avp_ref.runtime import ReferenceRuntime, SubjectSession


@dataclass(frozen=True, slots=True)
class ReliabilityReport:
    runs: int
    valid_runs: int
    invalid_runs: int
    passes: int
    success_rate: float
    success_at_k: float
    all_success_k: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_repeated(subject: Callable[[SubjectSession, Mapping[str, Any]], str], runs: int = 8) -> ReliabilityReport:
    """Run the same Scenario/Agent identity repeatedly and separate invalid evals."""

    outcomes: list[bool] = []
    invalid = 0
    for _ in range(runs):
        runtime = ReferenceRuntime()
        episode = runtime.create_episode(reference_scenario(), reference_agent_system(subject.__name__), reference_environment())
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id, subject)
        runtime.verify(episode.episode_id, RefundOracle())
        if episode.validity is not Validity.VALID:
            invalid += 1
            continue
        outcomes.append(episode.task_verdict.value == "PASS")
    valid = len(outcomes)
    passes = sum(outcomes)
    rate = passes / valid if valid else 0.0
    return ReliabilityReport(runs, valid, invalid, passes, rate, 1.0 if any(outcomes) else 0.0, 1.0 if outcomes and all(outcomes) else 0.0)
