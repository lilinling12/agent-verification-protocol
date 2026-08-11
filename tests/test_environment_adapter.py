import unittest

from avp_ref.environment import (
    FaultSpec,
    InMemoryCommerceAdapter,
    RestoreEquivalence,
    SnapshotNotFoundError,
    ToolExecutionError,
    ToolPermissionDenied,
    ToolRequest,
    UnknownEnvironmentHandle,
)
from avp_ref.reference import reference_scenario


class EnvironmentAdapterTest(unittest.TestCase):
    def setUp(self):
        self.adapter = InMemoryCommerceAdapter()
        self.handle = self.adapter.provision(reference_scenario())
        self.adapter.reset(self.handle)

    def test_description_identity_is_stable(self):
        first = self.adapter.describe()
        second = InMemoryCommerceAdapter().describe()
        self.assertEqual(first.identity_digest, second.identity_digest)

    def test_tool_permissions_come_from_scenario_capabilities(self):
        with self.assertRaises(ToolPermissionDenied):
            self.adapter.execute(self.handle, ToolRequest("subject", "customer.delete", {"customer_id": "cust_1"}))

    def test_snapshot_restore_is_state_equivalent(self):
        snapshot = self.adapter.snapshot(self.handle)
        self.adapter.execute(self.handle, ToolRequest("subject", "refund.create", {"order_id": "ord_1"}))
        result = self.adapter.restore(self.handle, snapshot)
        self.assertIs(result.equivalence, RestoreEquivalence.STATE_EQUIVALENT)
        self.assertEqual(snapshot.state_digest, self.adapter.digest(self.handle))

    def test_snapshot_diff_is_semantic(self):
        before = self.adapter.snapshot(self.handle)
        self.adapter.execute(self.handle, ToolRequest("subject", "refund.create", {"order_id": "ord_1"}))
        after = self.adapter.snapshot(self.handle)
        result = self.adapter.diff(self.handle, before, after)
        self.assertTrue(result.changes)
        self.assertTrue(any(item["entity"].startswith("refunds:") for item in result.to_dict()["changes"]))

    def test_snapshot_cannot_cross_handles(self):
        snapshot = self.adapter.snapshot(self.handle)
        other = self.adapter.provision(reference_scenario())
        with self.assertRaises(SnapshotNotFoundError):
            self.adapter.restore(other, snapshot)

    def test_fault_is_one_shot_and_machine_readable(self):
        fault = self.adapter.inject_fault(self.handle, FaultSpec("tool.error", "order.get", parameters={"error": "boom"}))
        with self.assertRaises(ToolExecutionError) as caught:
            self.adapter.execute(self.handle, ToolRequest("subject", "order.get", {"order_id": "ord_1"}))
        self.assertEqual(fault.fault_id, caught.exception.fault_observations[0].fault_id)
        result = self.adapter.execute(self.handle, ToolRequest("subject", "order.get", {"order_id": "ord_1"}))
        self.assertEqual("ord_1", result.result["id"])

    def test_release_invalidates_handle(self):
        self.adapter.release(self.handle)
        with self.assertRaises(UnknownEnvironmentHandle):
            self.adapter.digest(self.handle)


if __name__ == "__main__":
    unittest.main()
