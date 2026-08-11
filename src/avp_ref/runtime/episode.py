"""Single Episode model used throughout the AVP reference implementation."""

from __future__ import annotations

from dataclasses import dataclass, field

from avp_ref.models import AVPEvent, Evidence, Snapshot, TaskVerdict, Validity, VerificationResult
from avp_ref.scenario.models import ScenarioInstance

from .agent import AgentSystem
from .manifest import EpisodeManifest
from .state import EpisodeState, assert_transition


@dataclass(slots=True)
class Episode:
    """Mutable execution record bound to immutable Scenario/Agent identities."""

    episode_id: str
    scenario: ScenarioInstance
    agent_system: AgentSystem
    manifest: EpisodeManifest
    state: EpisodeState = EpisodeState.CREATED
    validity: Validity = Validity.VALID
    task_verdict: TaskVerdict = TaskVerdict.INCONCLUSIVE
    agent_report: str | None = None
    events: list[AVPEvent] = field(default_factory=list)
    evidence: dict[str, Evidence] = field(default_factory=dict)
    snapshots: dict[str, Snapshot] = field(default_factory=dict)
    verification: list[VerificationResult] = field(default_factory=list)

    def transition(self, target: EpisodeState) -> None:
        assert_transition(self.state, target)
        self.state = target
