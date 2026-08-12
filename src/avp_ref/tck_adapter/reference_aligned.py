"""Reference-runtime TCK probes that require implementation capability glue."""

from __future__ import annotations

from typing import Any, Mapping

from avp_ref.reference import (
    correct_subject,
    reference_agent_system,
    reference_environment,
    reference_oracle_package,
    reference_scenario,
    reference_subject_adapter,
)
from avp_ref.runtime import create_replay_episode

from .models import TCKCaseResult
from .reference import ReferenceTCKAdapter


class AlignedReferenceTCKAdapter(ReferenceTCKAdapter):
    """Reference adapter with reviewed replay-capability integration."""

    def _evaluate_replay_identity(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        runtime = self._runtime_factory()
        source = runtime.create_episode(
            scenario=reference_scenario(),
            agent_system=reference_agent_system(correct_subject.__name__),
            environment_adapter=reference_environment(),
            subject_adapter=reference_subject_adapter(correct_subject),
            oracle_package=reference_oracle_package(),
        )
        replay = create_replay_episode(
            runtime,
            source.episode_id,
            environment_adapter=reference_environment(),
            subject_adapter=reference_subject_adapter(correct_subject),
            oracle_package=reference_oracle_package(),
        )

        source_link = replay.replay_source
        if replay.episode_id == source.episode_id:
            return self._fail(case_id, "replay reused the source Episode identifier")
        if source_link is None:
            return self._fail(case_id, "replay does not expose an explicit source reference")
        if source_link.episode_id != source.episode_id:
            return self._fail(case_id, "replay source Episode identifier is incorrect")
        if source_link.manifest_digest != source.manifest.manifest_digest:
            return self._fail(case_id, "replay source manifest identity is incorrect")
        if source.replay_source is not None:
            return self._fail(case_id, "creating a replay mutated the source Episode identity")
        return self._pass(case_id, "replay uses a new Episode id and preserves source identity")
