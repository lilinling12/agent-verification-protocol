import unittest

from avp_ref.canonical import digest
from avp_ref.environment import FaultSpec
from avp_ref.failure import locate_first_bad_step
from avp_ref.models import Validity
from avp_ref.oracle import broken_oracle_package
from avp_ref.reference import (
    correct_subject,
    false_success_subject,
    isolation_probe_subject,
    recovering_subject,
    reference_agent_system,
    reference_environment,
    reference_oracle_package,
    reference_scenario,
    reference_subject_adapter,
    wrong_target_subject,
)
from avp_ref.reliability import run_repeated
from avp_ref.runtime import EpisodeState, InvalidEpisodeTransition, ReferenceRuntime


class ReferenceRuntimeTest(unittest.TestCase):
    def make_episode(self, subject=correct_subject, oracle_package=None):
        runtime = ReferenceRuntime()
        episode = runtime.create_episode(
            scenario=reference_scenario(),
            agent_system=reference_agent_system(subject.__name__),
            environment_adapter=reference_environment(),
            subject_adapter=reference_subject_adapter(subject),
            oracle_package=oracle_package or reference_oracle_package(),
        )
        return runtime, episode

    def test_digest_is_stable(self):
        self.assertEqual(digest({"b": 2, "a": 1}), digest({"a": 1, "b": 2}))

    def test_runtime_requires_provision_before_subject(self):
        runtime, episode = self.make_episode()
        with self.assertRaises(InvalidEpisodeTransition):
            runtime.run_subject(episode.episode_id)

    def test_subject_session_isolation(self):
        runtime, episode = self.make_episode(isolation_probe_subject)
        runtime.provision(episode.episode_id)
        self.assertEqual("ISOLATED", runtime.run_subject(episode.episode_id))

    def test_false_success_is_detected(self):
        runtime, episode = self.make_episode(false_success_subject)
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id)
        runtime.verify(episode.episode_id)
        self.assertEqual("FAIL", episode.task_verdict.value)
        self.assertTrue(episode.evidence)
        self.assertEqual("state.false_success", locate_first_bad_step(episode).taxonomy)

    def test_wrong_target_localization(self):
        runtime, episode = self.make_episode(wrong_target_subject)
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id)
        runtime.verify(episode.episode_id)
        failure = locate_first_bad_step(episode)
        self.assertEqual("tool.wrong_target", failure.taxonomy)
        self.assertIsNotNone(failure.first_bad_event_id)

    def test_correct_subject_passes(self):
        runtime, episode = self.make_episode(correct_subject)
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id)
        runtime.verify(episode.episode_id)
        self.assertEqual("PASS", episode.task_verdict.value)
        self.assertIs(Validity.VALID, episode.validity)
        self.assertIsNone(episode.validity_detail)
        self.assertIs(EpisodeState.COMPLETED, episode.state)

    def test_snapshot_restore(self):
        runtime, episode = self.make_episode(correct_subject)
        runtime.provision(episode.episode_id)
        snapshot = runtime.snapshot(episode.episode_id)
        runtime.run_subject(episode.episode_id)
        self.assertEqual("STATE_EQUIVALENT", runtime.restore(episode.episode_id, snapshot.snapshot_id))

    def test_broken_oracle_is_invalid_eval(self):
        runtime, episode = self.make_episode(correct_subject, broken_oracle_package())
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id)
        runtime.verify(episode.episode_id)
        self.assertIs(Validity.ORACLE_FAILURE, episode.validity)
        self.assertIsNotNone(episode.validity_detail)
        self.assertEqual("ORACLE_CRASH", episode.validity_detail.code)
        self.assertIs(EpisodeState.INVALID, episode.state)
        self.assertEqual("INCONCLUSIVE", episode.task_verdict.value)

    def test_fault_recovery(self):
        runtime, episode = self.make_episode(recovering_subject)
        runtime.provision(episode.episode_id)
        runtime.inject_fault(episode.episode_id, FaultSpec("tool.error", "order.get", 1))
        runtime.run_subject(episode.episode_id)
        runtime.verify(episode.episode_id)
        self.assertEqual("PASS", episode.task_verdict.value)
        types = [event.event_type for event in episode.events]
        self.assertIn("fault.activated", types)
        self.assertIn("fault.cleared", types)

    def test_manifest_is_reproducible_for_same_adapter_types(self):
        scenario = reference_scenario(seed=77)
        agent = reference_agent_system("same-agent")
        runtime = ReferenceRuntime()
        first = runtime.create_episode(
            scenario=scenario,
            agent_system=agent,
            environment_adapter=reference_environment(),
            subject_adapter=reference_subject_adapter(correct_subject),
            oracle_package=reference_oracle_package(),
        )
        second = runtime.create_episode(
            scenario=scenario,
            agent_system=agent,
            environment_adapter=reference_environment(),
            subject_adapter=reference_subject_adapter(correct_subject),
            oracle_package=reference_oracle_package(),
        )
        self.assertNotEqual(first.episode_id, second.episode_id)
        self.assertEqual(first.manifest.manifest_digest, second.manifest.manifest_digest)

    def test_reliability_metrics(self):
        good = run_repeated(correct_subject, runs=4)
        bad = run_repeated(false_success_subject, runs=4)
        self.assertEqual(1.0, good.success_rate)
        self.assertEqual(0.0, bad.success_rate)


if __name__ == "__main__":
    unittest.main()
