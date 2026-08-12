from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from avp_ref.models import Validity
from avp_ref.reference import reference_agent_system, reference_environment, reference_oracle_package, reference_scenario, reference_subject_adapter
from avp_ref.runtime import ReferenceRuntime


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


def run_repeated(subject, runs: int = 8) -> ReliabilityReport:
    outcomes: list[bool] = []
    invalid = 0
    for _ in range(runs):
        runtime = ReferenceRuntime()
        episode = runtime.create_episode(reference_scenario(), reference_agent_system(subject.__name__), reference_environment(), reference_subject_adapter(subject), reference_oracle_package())
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id)
        if episode.validity is not Validity.VALID:
            invalid += 1
            continue
        runtime.verify(episode.episode_id)
        if episode.validity is not Validity.VALID:
            invalid += 1
            continue
        outcomes.append(episode.task_verdict.value == "PASS")
    valid = len(outcomes)
    passes = sum(outcomes)
    rate = passes / valid if valid else 0.0
    return ReliabilityReport(runs, valid, invalid, passes, rate, 1.0 if any(outcomes) else 0.0, 1.0 if outcomes and all(outcomes) else 0.0)
