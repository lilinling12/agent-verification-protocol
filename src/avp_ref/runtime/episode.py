"""Single Episode model used throughout the AVP reference implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from avp_ref.environment.models import SnapshotRef
from avp_ref.models import AVPEvent, Evidence, TaskVerdict, Validity, VerificationResult
from avp_ref.scenario.models import ScenarioInstance

from .agent import AgentSystem
from .lifecycle import EpisodeTransition, TransitionCause, default_transition_cause
from .manifest import EpisodeManifest
from .state import EpisodeState, assert_transition


@dataclass(slots=True)
class Episode:
    """Mutable execution record bound to immutable Scenario/Agent identities.

    Lifecycle history is append-only through the public API. A state change and
    its canonical transition record share one mutation boundary, while callers
    receive only an immutable tuple view of that history. Each canonical record
    is also projected onto the AVP event timeline for implementation-neutral
    observation by TCK adapters and protocol bindings.
    """

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
    snapshots: dict[str, SnapshotRef] = field(default_factory=dict)
    verification: list[VerificationResult] = field(default_factory=list)
    telemetry: Any = field(default=None, repr=False)
    _transition_records: list[EpisodeTransition] = field(
        default_factory=list,
        init=False,
        repr=False,
    )

    @property
    def transition_records(self) -> tuple[EpisodeTransition, ...]:
        """Return an immutable view of canonical lifecycle transition records."""

        return tuple(self._transition_records)

    def transition(
        self,
        target: EpisodeState,
        *,
        cause: TransitionCause | None = None,
    ) -> EpisodeTransition:
        """Apply one legal state change and append its canonical record.

        All validation completes before mutation. An illegal target or invalid
        explicit cause therefore leaves both state and transition history
        unchanged. Event emission happens after the canonical state/record pair
        is committed; telemetry failures cannot erase lifecycle evidence.
        """

        previous = self.state
        assert_transition(previous, target)
        resolved_cause = cause or default_transition_cause(previous, target)
        record = EpisodeTransition(
            episode_id=self.episode_id,
            sequence=len(self._transition_records) + 1,
            previous_state=previous,
            resulting_state=target,
            cause=resolved_cause,
        )
        self.state = target
        self._transition_records.append(record)

        # Local import avoids making the lifecycle value model depend on event
        # transport while still projecting every observable transition.
        from avp_ref.events import EventRecorder

        EventRecorder(self).emit(
            "episode.transition",
            "orchestrator",
            0,
            payload=record.to_dict(),
        )
        return record
