import unittest
from typing import Any, Mapping

from avp_ref.reference import (
    reference_agent_system,
    reference_scenario,
    reference_subject_adapter,
)
from avp_ref.runtime.subject_policy import SubjectCapabilityRequest, SubjectExecutionDenied
from avp_ref.security import CapabilityGuardedSubjectAdapter, CapabilityGuardPolicy
from avp_ref.subject import SubjectInvocation


class _RecordingGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def observe(self) -> Mapping[str, Any]:
        return {"ok": True}

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> Any:
        self.calls.append((name, dict(arguments)))
        return {"name": name, "arguments": dict(arguments)}

    def trace_headers(self) -> Mapping[str, str]:
        return {"traceparent": "00-test"}


class CapabilityGuardPolicyTest(unittest.TestCase):
    def test_policy_state_is_episode_scoped_and_release_is_targeted(self):
        policy = CapabilityGuardPolicy()
        scenario = reference_scenario()
        policy.bind("ep_a", scenario)
        policy.bind("ep_b", scenario)

        policy.release("ep_a")

        with self.assertRaises(SubjectExecutionDenied) as denied:
            policy.authorize(SubjectCapabilityRequest("ep_a", "subject", "order.get"))
        self.assertEqual("POLICY_UNAVAILABLE", denied.exception.code)

        policy.authorize(SubjectCapabilityRequest("ep_b", "subject", "order.get"))

    def test_denial_record_is_audit_safe(self):
        policy = CapabilityGuardPolicy()
        scenario = reference_scenario()
        policy.bind("ep_security", scenario)

        with self.assertRaises(SubjectExecutionDenied):
            policy.authorize(
                SubjectCapabilityRequest("ep_security", "subject", "refund.delete")
            )

        records = policy.denial_records("ep_security")
        self.assertEqual(1, len(records))
        self.assertEqual("CAPABILITY_DENIED", records[0].code)
        self.assertEqual("refund.delete", records[0].capability)
        self.assertIsNotNone(records[0].policy_digest)


class CapabilityGuardedSubjectAdapterTest(unittest.TestCase):
    def test_allowed_tool_is_forwarded(self):
        def subject(session, task):
            del task
            result = session.call_tool("order.get", {"order_id": "ord_1"})
            return str(result["name"])

        scenario = reference_scenario()
        policy = CapabilityGuardPolicy()
        adapter = CapabilityGuardedSubjectAdapter(
            reference_subject_adapter(subject),
            scenario,
            policy,
        )
        handle = adapter.open(reference_agent_system("allowed-subject"))
        gateway = _RecordingGateway()
        result = adapter.invoke(
            handle,
            SubjectInvocation("ep_allowed", {"instruction": "test"}, 4, 1.0),
            gateway,
        )

        self.assertEqual("order.get", result.report)
        self.assertEqual([("order.get", {"order_id": "ord_1"})], gateway.calls)
        adapter.release(handle)

    def test_denied_tool_does_not_reach_downstream_gateway(self):
        def subject(session, task):
            del task
            try:
                session.call_tool("refund.delete", {"order_id": "ord_1"})
            except RuntimeError:
                return "DENIED"
            return "UNEXPECTED"

        scenario = reference_scenario()
        policy = CapabilityGuardPolicy()
        inner = reference_subject_adapter(subject)
        adapter = CapabilityGuardedSubjectAdapter(inner, scenario, policy)
        handle = adapter.open(reference_agent_system("denied-subject"))
        gateway = _RecordingGateway()
        result = adapter.invoke(
            handle,
            SubjectInvocation("ep_denied", {"instruction": "test"}, 4, 1.0),
            gateway,
        )

        self.assertEqual("DENIED", result.report)
        self.assertEqual([], gateway.calls)
        records = policy.denial_records("ep_denied")
        self.assertEqual(1, len(records))
        self.assertEqual("refund.delete", records[0].capability)
        adapter.release(handle)

    def test_description_identity_binds_inner_adapter_and_scenario(self):
        scenario = reference_scenario()
        inner = reference_subject_adapter(lambda session, task: "ok")
        adapter = CapabilityGuardedSubjectAdapter(inner, scenario, CapabilityGuardPolicy())

        description = adapter.describe()
        self.assertEqual("capability-guard", description.adapter)
        self.assertEqual(
            inner.describe().identity_digest,
            description.metadata["innerSubjectAdapterDigest"],
        )
        self.assertEqual(
            scenario.instance_digest,
            description.metadata["scenarioInstanceDigest"],
        )


if __name__ == "__main__":
    unittest.main()
