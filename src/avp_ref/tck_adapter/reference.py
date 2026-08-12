"""Adapter between AVP TCK vectors and the Python reference runtime.

The adapter is deliberately thin:

* TCK remains the authority for expected behavior.
* ReferenceRuntime remains an implementation under evaluation.
* A failing reference runtime result is reported as FAIL, not rewritten.
* SKIP is reserved for an explicit, unsatisfied applicability condition.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from avp_ref.models import TaskVerdict, Validity
from avp_ref.reference import (
    correct_subject,
    reference_agent_system,
    reference_environment,
    reference_oracle_package,
    reference_scenario,
    reference_subject_adapter,
)
from avp_ref.runtime import (
    Episode,
    EpisodeState,
    InvalidEpisodeTransition,
    ReferenceRuntime,
    SubjectSession,
)
from avp_ref.runtime.state import assert_transition, is_terminal

from .models import TCKAdapterError, TCKCaseResult, TCKStatus


class ReferenceTCKAdapter:
    """Evaluate AVP lifecycle TCK vectors against the Python reference runtime.

    TCK expectations are never weakened to accommodate implementation drift.
    Runtime differences therefore remain observable as ordinary FAIL results.
    """

    _SUPPORTED_CASES = frozenset(
        {
            "AVP-TCK-LIFECYCLE-NORMAL-001",
            "AVP-TCK-LIFECYCLE-TRANSITION-RECORD-001",
            "AVP-TCK-LIFECYCLE-TRANSITION-MATRIX-001",
            "AVP-TCK-LIFECYCLE-ILLEGAL-001",
            "AVP-TCK-LIFECYCLE-TERMINAL-001",
            "AVP-TCK-LIFECYCLE-RESULT-SEPARATION-001",
            "AVP-TCK-LIFECYCLE-QUIESCING-001",
            "AVP-TCK-LIFECYCLE-REPLAY-001",
            "AVP-TCK-LIFECYCLE-PAUSE-001",
        }
    )

    def __init__(
        self,
        *,
        capabilities: frozenset[str] | set[str] | tuple[str, ...] = (),
        runtime_factory: Callable[[], ReferenceRuntime] = ReferenceRuntime,
    ) -> None:
        self._capabilities = frozenset(capabilities)
        self._runtime_factory = runtime_factory

    @property
    def supported_case_ids(self) -> frozenset[str]:
        """Return the exact TCK case identities implemented by this adapter."""

        return self._SUPPORTED_CASES

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        """Dispatch a validated lifecycle case to its implementation probe."""

        case_id = self._case_id(case)
        when = case.get("when")
        applicability = case.get("applicability")
        if applicability == "conditional":
            if not isinstance(when, str) or not when:
                raise TCKAdapterError(f"{case_id} conditional case is missing when")
            if when not in self._capabilities:
                return TCKCaseResult(
                    case_id=case_id,
                    status=TCKStatus.SKIP,
                    detail=f"condition {when!r} is not declared",
                    skip_reason=f"condition-not-declared:{when}",
                )

        dispatch = {
            "AVP-TCK-LIFECYCLE-NORMAL-001": self._evaluate_normal_path,
            "AVP-TCK-LIFECYCLE-TRANSITION-RECORD-001": self._evaluate_transition_record,
            "AVP-TCK-LIFECYCLE-TRANSITION-MATRIX-001": self._evaluate_transition_matrix,
            "AVP-TCK-LIFECYCLE-ILLEGAL-001": self._evaluate_illegal_transitions,
            "AVP-TCK-LIFECYCLE-TERMINAL-001": self._evaluate_terminal_immutability,
            "AVP-TCK-LIFECYCLE-RESULT-SEPARATION-001": self._evaluate_result_separation,
            "AVP-TCK-LIFECYCLE-QUIESCING-001": self._evaluate_quiescing_boundary,
            "AVP-TCK-LIFECYCLE-REPLAY-001": self._evaluate_replay_identity,
            "AVP-TCK-LIFECYCLE-PAUSE-001": self._evaluate_pause_semantics,
        }
        evaluator = dispatch.get(case_id)
        if evaluator is None:
            raise TCKAdapterError(f"reference adapter does not implement TCK case {case_id}")
        return evaluator(case)

    def _evaluate_normal_path(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        transitions = self._transition_pairs(case.get("vector", {}).get("transitions"), case_id)
        rejected = [pair for pair in transitions if not self._transition_allowed(*pair)]
        if rejected:
            return self._fail(case_id, f"normal path rejects required transitions: {rejected}")
        if transitions[0][0] != "CREATED" or transitions[-1][1] != "COMPLETED":
            raise TCKAdapterError(f"{case_id} normal path must run CREATED -> COMPLETED")
        return self._pass(case_id, "normal lifecycle path is accepted")

    def _evaluate_transition_record(self, case: Mapping[str, Any]) -> TCKCaseResult:
        """Check whether runtime execution exposes ordered protocol transition records."""

        case_id = self._case_id(case)
        runtime, episode = self._run_to_completion()
        try:
            records = [event for event in episode.events if event.event_type == "episode.transition"]
            if not records:
                return self._fail(
                    case_id,
                    "reference runtime does not expose episode.transition records required by AVP-CORE-002/004",
                )
            sequences = [event.sequence for event in records]
            if sequences != sorted(sequences) or len(sequences) != len(set(sequences)):
                return self._fail(case_id, "transition records are not strictly ordered")
            required_payload = {"previousState", "resultingState", "cause"}
            for event in records:
                if event.episode_id != episode.episode_id:
                    return self._fail(case_id, "transition record episode identity changed")
                if not required_payload <= event.payload.keys():
                    return self._fail(case_id, "transition record payload is missing required fields")
            return self._pass(case_id, "ordered transition records are exposed")
        finally:
            runtime.release(episode.episode_id)

    def _evaluate_transition_matrix(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        states = case.get("states")
        matrix = case.get("allowedTransitions")
        if not isinstance(states, Mapping) or not isinstance(matrix, Mapping):
            raise TCKAdapterError(f"{case_id} requires states and allowedTransitions mappings")

        required = self._string_set(states.get("required"), f"{case_id} required states")
        optional = self._string_set(states.get("optional"), f"{case_id} optional states", allow_empty=True)
        expected_states = required | optional
        runtime_states = {state.value for state in EpisodeState}
        missing = required - runtime_states
        unknown = runtime_states - expected_states
        if missing or unknown:
            return self._fail(
                case_id,
                f"state projection mismatch missing={sorted(missing)} unknown={sorted(unknown)}",
            )

        expected_pairs: set[tuple[str, str]] = set()
        for source, targets in matrix.items():
            if source not in expected_states:
                raise TCKAdapterError(f"{case_id} matrix contains unknown source state {source!r}")
            for target in self._string_set(targets, f"{case_id} targets for {source}", allow_empty=True):
                expected_pairs.add((source, target))

        actual_pairs = {
            (source.value, target.value)
            for source in EpisodeState
            for target in EpisodeState
            if self._transition_allowed(source.value, target.value)
        }

        if "pause-capability-advertised" not in self._capabilities:
            expected_pairs = {pair for pair in expected_pairs if "PAUSED" not in pair}
            actual_pairs = {pair for pair in actual_pairs if "PAUSED" not in pair}

        if actual_pairs != expected_pairs:
            return self._fail(
                case_id,
                "transition relation drift "
                f"missing={sorted(expected_pairs - actual_pairs)} "
                f"extra={sorted(actual_pairs - expected_pairs)}",
            )
        return self._pass(case_id, "runtime transition relation matches applicable TCK matrix")

    def _evaluate_illegal_transitions(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        transitions = self._transition_pairs(case.get("vector", {}).get("transitions"), case_id)
        accepted = [pair for pair in transitions if self._transition_allowed(*pair)]
        if accepted:
            return self._fail(case_id, f"forbidden transitions were accepted: {accepted}")
        return self._pass(case_id, "all forbidden lifecycle transitions are rejected")

    def _evaluate_terminal_immutability(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        terminal_states = self._string_set(
            case.get("vector", {}).get("terminalStates"),
            f"{case_id} terminal states",
        )
        bad_terminal_classification = [
            state for state in terminal_states if not is_terminal(self._state(state))
        ]
        if bad_terminal_classification:
            return self._fail(
                case_id,
                f"states are not terminal in runtime: {sorted(bad_terminal_classification)}",
            )
        outbound = [
            (source, target.value)
            for source in sorted(terminal_states)
            for target in EpisodeState
            if self._transition_allowed(source, target.value)
        ]
        if outbound:
            return self._fail(case_id, f"terminal states have outbound transitions: {outbound}")
        return self._pass(case_id, "terminal states are immutable")

    def _evaluate_result_separation(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        required_fields = {"state", "task_verdict", "validity"}
        if not required_fields <= Episode.__dataclass_fields__.keys():
            return self._fail(case_id, "Episode does not represent lifecycle/verdict/validity separately")
        terminal_values = {state.value for state in EpisodeState if is_terminal(state)}
        verdict_values = {item.value for item in TaskVerdict}
        validity_values = {item.value for item in Validity}
        if terminal_values & verdict_values:
            return self._fail(
                case_id,
                f"terminal states overlap TaskVerdict values: {sorted(terminal_values & verdict_values)}",
            )
        if EpisodeState is TaskVerdict or EpisodeState is Validity or TaskVerdict is Validity:
            return self._fail(case_id, "result dimensions share one enum type")
        return self._pass(
            case_id,
            f"lifecycle, TaskVerdict and Validity are separate dimensions ({len(validity_values)} validity values)",
        )

    def _evaluate_quiescing_boundary(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        runtime = self._runtime_factory()
        episode = runtime.create_episode(
            scenario=reference_scenario(),
            agent_system=reference_agent_system(correct_subject.__name__),
            environment_adapter=reference_environment(),
            subject_adapter=reference_subject_adapter(correct_subject),
            oracle_package=reference_oracle_package(),
        )
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id)
        try:
            if episode.state is not EpisodeState.QUIESCING:
                return self._fail(case_id, f"fixture did not reach QUIESCING: {episode.state.value}")
            session = SubjectSession(runtime, episode.episode_id)
            try:
                session.call_tool("order.get", {"order_id": "ord_1"})
            except InvalidEpisodeTransition:
                return self._pass(case_id, "new Subject tool side effect is rejected after QUIESCING")
            return self._fail(case_id, "Subject tool invocation was accepted after QUIESCING")
        finally:
            runtime.release(episode.episode_id)

    def _evaluate_replay_identity(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        runtime = self._runtime_factory()
        replay = getattr(runtime, "replay", None)
        if replay is None or not callable(replay):
            return self._fail(
                case_id,
                "reference runtime has no replay API carrying a new episode id and source episode reference",
            )
        raise TCKAdapterError(
            f"{case_id} detected a replay API but the reference adapter has not reviewed its contract"
        )

    def _evaluate_pause_semantics(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = case.get("vector")
        if not isinstance(vector, Mapping):
            raise TCKAdapterError(f"{case_id} vector must be a mapping")
        allowed = self._transition_pairs(vector.get("allowed"), f"{case_id} allowed")
        forbidden = self._transition_pairs(vector.get("forbidden"), f"{case_id} forbidden")
        rejected_allowed = [pair for pair in allowed if not self._transition_allowed(*pair)]
        accepted_forbidden = [pair for pair in forbidden if self._transition_allowed(*pair)]
        if rejected_allowed or accepted_forbidden:
            return self._fail(
                case_id,
                f"pause semantics drift rejected_allowed={rejected_allowed} "
                f"accepted_forbidden={accepted_forbidden}",
            )
        return self._pass(case_id, "pause transitions satisfy the declared capability contract")

    def _run_to_completion(self) -> tuple[ReferenceRuntime, Episode]:
        runtime = self._runtime_factory()
        episode = runtime.create_episode(
            scenario=reference_scenario(),
            agent_system=reference_agent_system(correct_subject.__name__),
            environment_adapter=reference_environment(),
            subject_adapter=reference_subject_adapter(correct_subject),
            oracle_package=reference_oracle_package(),
        )
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id)
        runtime.verify(episode.episode_id)
        return runtime, episode

    @staticmethod
    def _case_id(case: Mapping[str, Any]) -> str:
        metadata = case.get("metadata")
        if not isinstance(metadata, Mapping) or not isinstance(metadata.get("id"), str):
            raise TCKAdapterError("TCK case metadata.id is missing")
        return metadata["id"]

    @staticmethod
    def _state(value: str) -> EpisodeState:
        try:
            return EpisodeState(value)
        except ValueError as exc:
            raise TCKAdapterError(f"unknown lifecycle state {value!r}") from exc

    def _transition_allowed(self, source: str, target: str) -> bool:
        try:
            assert_transition(self._state(source), self._state(target))
        except InvalidEpisodeTransition:
            return False
        return True

    @classmethod
    def _transition_pairs(cls, value: Any, context: str) -> tuple[tuple[str, str], ...]:
        if not isinstance(value, list) or not value:
            raise TCKAdapterError(f"{context} must be a non-empty transition list")
        pairs: list[tuple[str, str]] = []
        for item in value:
            if not isinstance(item, list) or len(item) != 2 or not all(isinstance(v, str) for v in item):
                raise TCKAdapterError(f"{context} contains an invalid transition pair")
            pair = (item[0], item[1])
            cls._state(pair[0])
            cls._state(pair[1])
            pairs.append(pair)
        if len(pairs) != len(set(pairs)):
            raise TCKAdapterError(f"{context} contains duplicate transitions")
        return tuple(pairs)

    @staticmethod
    def _string_set(value: Any, context: str, *, allow_empty: bool = False) -> set[str]:
        if not isinstance(value, list) or (not value and not allow_empty):
            qualifier = "non-empty " if not allow_empty else ""
            raise TCKAdapterError(f"{context} must be a {qualifier}list")
        if not all(isinstance(item, str) and item for item in value):
            raise TCKAdapterError(f"{context} must contain non-empty strings")
        if len(value) != len(set(value)):
            raise TCKAdapterError(f"{context} contains duplicate values")
        return set(value)

    @staticmethod
    def _pass(case_id: str, detail: str) -> TCKCaseResult:
        return TCKCaseResult(case_id=case_id, status=TCKStatus.PASS, detail=detail)

    @staticmethod
    def _fail(case_id: str, detail: str) -> TCKCaseResult:
        return TCKCaseResult(case_id=case_id, status=TCKStatus.FAIL, detail=detail)
