"""Single Episode model used throughout the AVP reference implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from avp_ref.environment.models import SnapshotRef
from avp_ref.models import AVPEvent, Evidence, TaskVerdict, Validity, ValidityDetail, VerificationResult
from avp_ref.oracle_runner.models import OracleEvaluationRecord
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

    Oracle acceptance is frozen at terminal verification boundaries. A later
    Episode-wide infrastructure failure may invalidate the Episode, but it must
    not rewrite an Oracle result set that was already accepted by the verifier.
    """

    episode_id: str
    scenario: ScenarioInstance
    agent_system: AgentSystem
    manifest: EpisodeManifest
    state: EpisodeState = EpisodeState.CREATED
    validity: Validity = Validity.VALID
    validity_detail: ValidityDetail | None = None
    task_verdict: TaskVerdict = TaskVerdict.INCONCLUSIVE
    agent_report: str | None = None
    events: list[AVPEvent] = field(default_factory=list)
    evidence: dict[str, Evidence] = field(default_factory=dict)
    snapshots: dict[str, SnapshotRef] = field(default_factory=dict)
    verification: list[VerificationResult] = field(default_factory=list)
    telemetry: Any = field(default=None, repr=False)
    _oracle_evaluation: OracleEvaluationRecord | None = field(
        default=None,
        init=False,
        repr=False,
    )
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

    @property
    def oracle_evaluation(self) -> OracleEvaluationRecord | None:
        """Return the immutable verifier-side Oracle acceptance record."""

        return self._oracle_evaluation

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

        For verification terminal states, Oracle acceptance is frozen before the
        transition becomes observable. The freeze is conservative: infrastructure
        failure before a trustworthy execution record exists does not manufacture
        a successful Oracle Evaluation Record.
        """

        previous = self.state
        assert_transition(previous, target)
        if target in {EpisodeState.COMPLETED, EpisodeState.INVALID}:
            self._freeze_oracle_evaluation(target)
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

    def _freeze_oracle_evaluation(self, target: EpisodeState) -> None:
        """Freeze verifier acceptance only when the event/evidence chain is sufficient.

        Oracle failures may legitimately have no execution-record Artifact when
        failure occurs before the runner can produce one. A VALID acceptance
        record is stricter: it is never inferred without an immutable execution
        record, and on an INVALID Episode it is only inferred after verification
        results reached the verifier acceptance list. This prevents an Artifact
        publication failure from being misrepresented as successful acceptance.
        """

        if self._oracle_evaluation is not None:
            return
        started = next(
            (
                event
                for event in self.events
                if event.event_type == "episode.verification.started"
            ),
            None,
        )
        request = next(
            (
                event
                for event in self.events
                if event.event_type == "oracle.execution.started"
            ),
            None,
        )
        execution = next(
            (
                event
                for event in reversed(self.events)
                if event.event_type
                in {"oracle.execution.completed", "oracle.execution.failed"}
            ),
            None,
        )
        if started is None or request is None:
            return

        oracle_id = started.payload.get("oracle_id")
        oracle_version = started.payload.get("oracle_version")
        package_digest = started.payload.get("oracle_package_digest")
        input_digest = request.payload.get("input_digest")
        if not all(
            isinstance(value, str) and value
            for value in (oracle_id, oracle_version, package_digest, input_digest)
        ):
            return

        execution_record_digest = None
        if execution is not None:
            value = execution.payload.get("artifact_digest")
            if isinstance(value, str) and value:
                execution_record_digest = value

        oracle_failure = self.validity is Validity.ORACLE_FAILURE
        if not oracle_failure:
            if execution_record_digest is None:
                return
            if target is EpisodeState.INVALID and not self.verification:
                return

        accepted_results = () if oracle_failure else tuple(self.verification)
        if oracle_failure:
            oracle_task_verdict = TaskVerdict.INCONCLUSIVE
        else:
            oracle_task_verdict = (
                TaskVerdict.FAIL
                if any(
                    result.verdict == "FAIL" and result.severity == "critical"
                    for result in accepted_results
                )
                else TaskVerdict.PASS
            )
        evidence_ids = tuple(
            sorted(
                {
                    evidence_id
                    for result in accepted_results
                    for evidence_id in result.evidence_ids
                }
            )
        )
        self._oracle_evaluation = OracleEvaluationRecord(
            oracle_id=oracle_id,
            oracle_version=oracle_version,
            package_digest=package_digest,
            input_digest=input_digest,
            execution_record_digest=execution_record_digest,
            evaluation_validity=(
                Validity.ORACLE_FAILURE if oracle_failure else Validity.VALID
            ),
            task_verdict=oracle_task_verdict,
            accepted_results=accepted_results,
            evidence_ids=evidence_ids,
            validity_detail=self.validity_detail if oracle_failure else None,
        )
