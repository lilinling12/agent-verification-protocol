"""Packet-path binding for the provider-neutral Linux SYN witness.

This module binds one evaluator-owned witness to the Subject egress boundary of
the PTL-001 Linux namespace topology. It does not execute the witness, does not
weaken capture assurance, and does not create a terminating-style upstream
channel for a non-terminating forwarding path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..evidence_core import ArtifactStore, EvidenceMaterializationError, EvidencePlan, MaterializedEndpoint
from ..witness import LinuxSynWitness
from ..witness_evidence import CaptureAssurance, WitnessScope
from .topology import PacketPathRunTopology

_FRONT_CHANNEL = "W-front"
_SUBJECT_ROLE = "subject"
_PRIVILEGED_PROBE_ROLE = "privileged-probe"


@dataclass(frozen=True, slots=True)
class PacketPathWitnessBinding:
    """One attempt-local Subject-egress witness binding.

    The observer is evaluator-owned and must execute inside ``namespace_name`` so
    ``LinuxSynWitness`` can bind the real Subject veth and observe
    ``PACKET_OUTGOING`` frames. The Subject probe is a separate process and must
    continue to use ``PacketPathController.subject_command`` for privilege drop.
    """

    namespace_name: str
    interface_name: str
    scope: WitnessScope
    assurance: CaptureAssurance

    @classmethod
    def for_attempt(
        cls,
        *,
        topology: PacketPathRunTopology,
        plan: EvidencePlan,
        expected_target: MaterializedEndpoint,
        assurance: CaptureAssurance,
        privileged_probe: bool = False,
    ) -> "PacketPathWitnessBinding":
        """Bind one selected/control attempt without inventing upstream evidence."""

        _validate_non_terminating_plan(topology=topology, plan=plan)
        allowed_targets = {plan.subject_destination}
        if plan.non_target_subject_destination is not None:
            allowed_targets.add(plan.non_target_subject_destination)
        if expected_target not in allowed_targets:
            raise EvidenceMaterializationError(
                "packet-path witness target is not a sealed Subject destination"
            )

        return cls(
            namespace_name=topology.subject_namespace,
            interface_name=topology.subject_interface,
            scope=WitnessScope(
                channel=_FRONT_CHANNEL,
                role_id=_PRIVILEGED_PROBE_ROLE if privileged_probe else _SUBJECT_ROLE,
                source_addresses=(topology.subject_address,),
                expected_target=expected_target,
            ),
            assurance=assurance,
        )

    def evaluator_namespace_command(self, argv: Sequence[str]) -> tuple[str, ...]:
        """Enter the Subject namespace as evaluator-owned observation authority.

        This command intentionally does *not* use ``setpriv``: the witness needs
        packet-observation authority such as CAP_NET_RAW. It must never be used as
        the Subject execution command or exposed through the Subject surface.
        """

        if not argv or any(not isinstance(item, str) or not item for item in argv):
            raise EvidenceMaterializationError(
                "packet-path evaluator witness command must contain non-empty argv"
            )
        return (
            "ip",
            "netns",
            "exec",
            self.namespace_name,
            *tuple(argv),
        )

    def build_witness(self, *, artifact_store: ArtifactStore | None = None) -> LinuxSynWitness:
        """Construct the one-shot witness for execution inside ``namespace_name``."""

        return LinuxSynWitness(
            interface_name=self.interface_name,
            scopes=(self.scope,),
            assurance=self.assurance,
            artifact_store=artifact_store,
        )


def _validate_non_terminating_plan(
    *,
    topology: PacketPathRunTopology,
    plan: EvidencePlan,
) -> None:
    """Fail closed unless the sealed plan exactly matches packet-path topology."""

    if plan.run_id != topology.run_id:
        raise EvidenceMaterializationError("packet-path witness run identity drift")
    if plan.subject_destination != topology.selected_endpoint:
        raise EvidenceMaterializationError("packet-path selected Subject destination drift")
    if plan.upstream_fixture != plan.subject_destination:
        raise EvidenceMaterializationError(
            "packet-path forwarding must not materialize a distinct selected upstream socket"
        )
    if plan.non_target_subject_destination != topology.control_endpoint:
        raise EvidenceMaterializationError("packet-path non-target Subject destination drift")
    if plan.non_target_upstream_fixture != plan.non_target_subject_destination:
        raise EvidenceMaterializationError(
            "packet-path forwarding must not materialize a distinct control upstream socket"
        )
