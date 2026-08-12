from __future__ import annotations

import unittest

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
    ReplaySourceIdentity,
    create_replay_episode,
)


class ReplayIdentityTest(unittest.TestCase):
    def make_source(self):
        runtime = ReferenceRuntime()
        source = runtime.create_episode(
            scenario=reference_scenario(),
            agent_system=reference_agent_system(correct_subject.__name__),
            environment_adapter=reference_environment(),
            subject_adapter=reference_subject_adapter(correct_subject),
            oracle_package=reference_oracle_package(),
        )
        return runtime, source

    def test_replay_has_new_id_and_explicit_source_identity(self) -> None:
        runtime, source = self.make_source()
        replay = create_replay_episode(
            runtime,
            source.episode_id,
            environment_adapter=reference_environment(),
            subject_adapter=reference_subject_adapter(correct_subject),
            oracle_package=reference_oracle_package(),
        )

        self.assertNotEqual(source.episode_id, replay.episode_id)
        self.assertEqual(
            ReplaySourceIdentity(source.episode_id, source.manifest.manifest_digest),
            replay.replay_source,
        )
        self.assertIsNone(source.replay_source)
        self.assertIs(EpisodeState.CREATED, replay.state)
        self.assertEqual((), replay.transition_records)
        replay_events = [event for event in replay.events if event.event_type == "episode.replay.linked"]
        self.assertEqual(1, len(replay_events))
        self.assertEqual(source.episode_id, replay_events[0].payload["source"]["episodeId"])

    def test_replay_can_execute_as_independent_episode(self) -> None:
        runtime, source = self.make_source()
        replay = create_replay_episode(
            runtime,
            source.episode_id,
            environment_adapter=reference_environment(),
            subject_adapter=reference_subject_adapter(correct_subject),
            oracle_package=reference_oracle_package(),
        )
        runtime.provision(replay.episode_id)
        runtime.run_subject(replay.episode_id)
        runtime.verify(replay.episode_id)
        self.assertIs(EpisodeState.COMPLETED, replay.state)
        self.assertIs(EpisodeState.CREATED, source.state)

    def test_replay_source_cannot_be_rebound_after_execution_starts(self) -> None:
        runtime, source = self.make_source()
        runtime.provision(source.episode_id)
        with self.assertRaises(InvalidEpisodeTransition):
            source.bind_replay_source(
                ReplaySourceIdentity("ep_other", source.manifest.manifest_digest)
            )

    def test_unknown_source_is_rejected(self) -> None:
        runtime = ReferenceRuntime()
        with self.assertRaisesRegex(KeyError, "unknown source episode"):
            create_replay_episode(
                runtime,
                "missing",
                environment_adapter=reference_environment(),
                subject_adapter=reference_subject_adapter(correct_subject),
                oracle_package=reference_oracle_package(),
            )


if __name__ == "__main__":
    unittest.main()
