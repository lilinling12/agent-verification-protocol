import unittest

from avp_ref.canonical import digest
from avp_ref.failure import locate_first_bad_step
from avp_ref.models import Validity
from avp_ref.oracle import BrokenOracle, RefundOracle
from avp_ref.reference import correct_subject, false_success_subject, isolation_probe_subject, recovering_subject, reference_agent_system, reference_environment, reference_scenario, wrong_target_subject
from avp_ref.reliability import run_repeated
from avp_ref.runtime import EpisodeState, InvalidEpisodeTransition, ReferenceRuntime


class ReferenceRuntimeTest(unittest.TestCase):
    def make_episode(self, subject_name="test-subject"):
        runtime = ReferenceRuntime()
        episode = runtime.create_episode(reference_scenario(), reference_agent_system(subject_name), reference_environment())
        return runtime, episode

    def test_digest_is_stable(self):
        self.assertEqual(digest({"b": 2, "a": 1}), digest({"a": 1, "b": 2}))

    def test_runtime_requires_provision_before_subject(self):
        runtime, episode = self.make_episode()
        with self.assertRaises(InvalidEpisodeTransition):
            runtime.run_subject(episode.episode_id, correct_subject)

    def test_subject_session_isolation(self):
        runtime, episode = self.make_episode("isolation")
        runtime.provision(episode.episode_id)
        self.assertEqual("ISOLATED", runtime.run_subject(episode.episode_id, isolation_probe_subject))

    def test_false_success_is_detected(self):
        runtime, episode = self.make_episode("false-success")
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id, false_success_subject)
        runtime.verify(episode.episode_id, RefundOracle())
        self.assertEqual("FAIL", episode.task_verdict.value)
        self.assertTrue(episode.evidence)
        self.assertEqual("state.false_success", locate_first_bad_step(episode).taxonomy)

    def test_wrong_target_localization(self):
        runtime, episode = self.make_episode("wrong-target")
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id, wrong_target_subject)
        runtime.verify(episode.episode_id, RefundOracle())
        failure = locate_first_bad_step(episode)
        self.assertEqual("tool.wrong_target", failure.taxonomy)
        self.assertIsNotNone(failure.first_bad_event_id)

    def test_correct_subject_passes(self):
        runtime, episode = self.make_episode("correct")
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id, correct_subject)
        runtime.verify(episode.episode_id, RefundOracle())
        self.assertEqual("PASS", episode.task_verdict.value)
        self.assertIs(EpisodeState.COMPLETED, episode.state)

    def test_snapshot_restore(self):
        runtime, episode = self.make_episode("snapshot")
        runtime.provision(episode.episode_id)
        snapshot = runtime.snapshot(episode.episode_id)
        runtime.run_subject(episode.episode_id, correct_subject)
        self.assertEqual("STATE_EQUIVALENT", runtime.restore(episode.episode_id, snapshot.snapshot_id))

    def test_broken_oracle_is_invalid_eval(self):
        runtime, episode = self.make_episode("broken-oracle")
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id, correct_subject)
        runtime.verify(episode.episode_id, BrokenOracle())
        self.assertIs(Validity.ORACLE_FAILURE, episode.validity)
        self.assertIs(EpisodeState.INVALID, episode.state)
        self.assertEqual("INCONCLUSIVE", episode.task_verdict.value)

    def test_fault_recovery(self):
        runtime, episode = self.make_episode("recovering")
        runtime.provision(episode.episode_id)
        runtime.schedule_tool_error(episode.episode_id, "order.get", 1)
        runtime.run_subject(episode.episode_id, recovering_subject)
        runtime.verify(episode.episode_id, RefundOracle())
        self.assertEqual("PASS", episode.task_verdict.value)
        types = [event.event_type for event in episode.events]
        self.assertIn("fault.activated", types)
        self.assertIn("fault.cleared", types)

    def test_manifest_is_reproducible(self):
        scenario = reference_scenario(seed=77)
        agent = reference_agent_system("same-agent")
        runtime = ReferenceRuntime()
        first = runtime.create_episode(scenario, agent, reference_environment())
        second = runtime.create_episode(scenario, agent, reference_environment())
        self.assertNotEqual(first.episode_id, second.episode_id)
        self.assertEqual(first.manifest.manifest_digest, second.manifest.manifest_digest)

    def test_reliability_metrics(self):
        good = run_repeated(correct_subject, runs=4)
        bad = run_repeated(false_success_subject, runs=4)
        self.assertEqual(1.0, good.success_rate)
        self.assertEqual(1.0, good.all_success_k)
        self.assertEqual(0.0, bad.success_rate)
        self.assertEqual(0.0, bad.success_at_k)


if __name__ == "__main__":
    unittest.main()
