from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from avp_ref.reference import (
    correct_subject,
    reference_agent_system,
    reference_environment,
    reference_oracle_package,
    reference_scenario,
    reference_subject_adapter,
)
from avp_ref.runtime import (
    EpisodeState,
    InvalidEpisodeTransition,
    ReferenceRuntime,
    TransitionCause,
)

ROOT = Path(__file__).resolve().parents[1]


class LifecycleConformanceTest(unittest.TestCase):
    def make_episode(self):
        runtime = ReferenceRuntime()
        episode = runtime.create_episode(
            scenario=reference_scenario(),
            agent_system=reference_agent_system(correct_subject.__name__),
            environment_adapter=reference_environment(),
            subject_adapter=reference_subject_adapter(correct_subject),
            oracle_package=reference_oracle_package(),
        )
        return runtime, episode

    def test_normal_path_records_are_schema_valid_and_episode_local(self) -> None:
        runtime, episode = self.make_episode()
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id)
        runtime.verify(episode.episode_id)

        records = episode.transition_records
        self.assertEqual(6, len(records))
        self.assertEqual(list(range(1, 7)), [record.sequence for record in records])
        self.assertEqual({episode.episode_id}, {record.episode_id for record in records})
        self.assertEqual(
            [
                EpisodeState.PROVISIONING,
                EpisodeState.READY,
                EpisodeState.RUNNING,
                EpisodeState.QUIESCING,
                EpisodeState.VERIFYING,
                EpisodeState.COMPLETED,
            ],
            [record.resulting_state for record in records],
        )

        schema = json.loads(
            (ROOT / "schemas/episode-lifecycle.schema.json").read_text(encoding="utf-8")
        )
        validator = Draft202012Validator(schema)
        for record in records:
            validator.validate(record.to_dict())

        projected = [event for event in episode.events if event.event_type == "episode.transition"]
        self.assertEqual([record.to_dict() for record in records], [event.payload for event in projected])

    def test_illegal_transition_is_side_effect_free(self) -> None:
        _, episode = self.make_episode()
        before_events = tuple(episode.events)
        with self.assertRaises(InvalidEpisodeTransition):
            episode.transition(EpisodeState.RUNNING)
        self.assertIs(EpisodeState.CREATED, episode.state)
        self.assertEqual((), episode.transition_records)
        self.assertEqual(before_events, tuple(episode.events))

    def test_explicit_cause_is_preserved(self) -> None:
        _, episode = self.make_episode()
        cause = TransitionCause("test.provision.requested", "controlled fixture")
        record = episode.transition(EpisodeState.PROVISIONING, cause=cause)
        self.assertEqual(cause, record.cause)
        self.assertEqual(cause.to_dict(), record.to_dict()["cause"])

    def test_invalid_cause_code_is_rejected_before_transition(self) -> None:
        _, episode = self.make_episode()
        with self.assertRaises(ValueError):
            TransitionCause("contains whitespace")
        self.assertIs(EpisodeState.CREATED, episode.state)
        self.assertEqual((), episode.transition_records)


if __name__ == "__main__":
    unittest.main()
