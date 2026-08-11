import unittest
from avp_ref.canonical import digest
from avp_ref.runtime import ReferenceRuntime, false_success_subject, correct_subject, wrong_target_subject, recovering_subject, isolation_probe_subject
from avp_ref.oracle import BrokenOracle
from avp_ref.models import Validity
from avp_ref.failure import locate_first_bad_step
from avp_ref.reliability import run_repeated

class ReferenceRuntimeTest(unittest.TestCase):
    def test_digest_is_stable(self):
        self.assertEqual(digest({"b": 2, "a": 1}), digest({"a": 1, "b": 2}))
    def test_subject_session_isolation(self):
        rt=ReferenceRuntime(); ep=rt.create_episode("probe"); self.assertEqual("ISOLATED", rt.run_subject(ep.episode_id, isolation_probe_subject))
    def test_false_success_is_detected(self):
        rt=ReferenceRuntime(); ep=rt.create_episode("Refund ord_1"); rt.run_subject(ep.episode_id,false_success_subject); rt.verify(ep.episode_id,"ord_1"); self.assertEqual("FAIL",ep.task_verdict.value); self.assertTrue(ep.evidence); self.assertEqual("state.false_success", locate_first_bad_step(ep).taxonomy)
    def test_wrong_target_localization(self):
        rt=ReferenceRuntime(); ep=rt.create_episode("Refund ord_1"); rt.run_subject(ep.episode_id,wrong_target_subject); rt.verify(ep.episode_id,"ord_1"); failure=locate_first_bad_step(ep); self.assertEqual("tool.wrong_target",failure.taxonomy); self.assertIsNotNone(failure.first_bad_event_id)
    def test_correct_subject_passes(self):
        rt=ReferenceRuntime(); ep=rt.create_episode("Refund ord_1"); rt.run_subject(ep.episode_id,correct_subject); rt.verify(ep.episode_id,"ord_1"); self.assertEqual("PASS",ep.task_verdict.value)
    def test_snapshot_restore(self):
        rt=ReferenceRuntime(); ep=rt.create_episode("Refund ord_1"); rt.reset(ep.episode_id); snap=rt.snapshot(ep.episode_id); rt.run_subject(ep.episode_id,correct_subject); self.assertEqual("STATE_EQUIVALENT",rt.restore(ep.episode_id,snap.snapshot_id))
    def test_broken_oracle_is_invalid_eval(self):
        rt=ReferenceRuntime(); ep=rt.create_episode("Refund ord_1"); rt.run_subject(ep.episode_id,correct_subject); rt.verify(ep.episode_id,"ord_1",oracle=BrokenOracle()); self.assertEqual(Validity.ORACLE_FAILURE,ep.validity)
    def test_fault_recovery(self):
        rt=ReferenceRuntime(); ep=rt.create_episode("Refund ord_1"); rt.reset(ep.episode_id); rt.schedule_tool_error(ep.episode_id,"order.get",1); rt.run_subject(ep.episode_id,recovering_subject); rt.verify(ep.episode_id,"ord_1"); self.assertEqual("PASS",ep.task_verdict.value); types=[e.event_type for e in ep.events]; self.assertIn("fault.activated",types); self.assertIn("fault.cleared",types)
    def test_reliability_metrics(self):
        good=run_repeated(correct_subject,runs=4); bad=run_repeated(false_success_subject,runs=4); self.assertEqual(1.0,good.success_rate); self.assertEqual(1.0,good.all_success_k); self.assertEqual(0.0,bad.success_rate); self.assertEqual(0.0,bad.success_at_k)

if __name__ == "__main__": unittest.main()
