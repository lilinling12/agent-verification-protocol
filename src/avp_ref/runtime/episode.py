"""Single Episode model used throughout the AVP reference implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from avp_ref.environment.models import SnapshotRef
from avp_ref.models import AVPEvent, Evidence, TaskVerdict, Validity, VerificationResult
from avp_ref.scenario.models import ScenarioInstance

from .agent import AgentSystem
from .identity import ReplaySourceIdentity
from .lifecycle import EpisodeTransition, TransitionCause, default_transition_cause
from .manifest import EpisodeManifest
from .state import EpisodeState, InvalidEpisodeTransition, assert_transition


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
    _replay_source: ReplaySourceIdentity | None = field(
        default=None,
        init=False,
        repr=False,
    )

    @property
    def transition_records(self) -> tuple[EpisodeTransition, ...]:
        """Return an immutable view of canonical lifecycle transition records."""

        return tuple(self._transition_records)

    @property
    def replay_source(self) -> ReplaySourceIdentity | None:
        """Return the immutable source relationship when this Episode is a replay."""

        return self._replay_source

    def bind_replay_source(self, source: ReplaySourceIdentity) -> None:
        """Bind replay identity exactly once before execution begins.

        Replay ancestry is identity metadata, not mutable runtime state. Binding
        after a lifecycle transition would make the observable Episode identity
        history ambiguous and is therefore rejected.
        """

        if self.state is not EpisodeState.CREATED or self._transition_records:
            raise InvalidEpisodeTransition(
                "replay source must be bound while the Episode is CREATED"
            )
        if self._replay_source is not None:
            raise InvalidEpisodeTransition("replay source is already bound")
        if source.episode_id == self.episode_id:
            raise ValueError("a replay Episode cannot reference itself as its source")
        self._replay_source = source

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

        from avp_ref.events import EventRecorder

        EventRecorder(self).emit(
            "episode.transition",
            "orchestrator",
            0,
            payload=record.to_dict(),
        )
        return record
