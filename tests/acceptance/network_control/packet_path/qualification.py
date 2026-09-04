"""Fail-closed qualification contract for the PTL-001 packet-path lab.

The contract separates mechanism control acknowledgements from qualification
facts. A successful ``ip``/``nft`` command is never enough to qualify route
placement, Subject isolation, transport cut, recovery, witness integrity, or
cleanup. Those properties must be established by the reviewed evidence source
assigned to each requirement.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from ..evidence_core import EvidenceMaterializationError
from ..witness_evidence import CaptureAssurance
from .topology import PacketPathRunTopology


class QualificationProperty(str, Enum):
    """Mechanism-local properties required before packet-path evidence is admitted."""

    NATIVE_LINUX = "native-linux"
    PRIVILEGED_EVALUATOR = "privileged-evaluator"
    REQUIRED_TOOLS = "required-tools"
    THREE_NAMESPACE_MATERIALIZATION = "three-namespace-materialization"
    ROUTE_THROUGH_CONTROL = "route-through-control"
    NO_ROUTE_ESCAPE = "no-route-escape"
    SUBJECT_PRIVILEGE_ISOLATION = "subject-privilege-isolation"
    SUBJECT_CONTROL_ISOLATION = "subject-control-isolation"
    SELECTED_CUT = "selected-cut"
    NON_TARGET_SURVIVAL = "non-target-survival"
    RECOVERY_1 = "recovery-1"
    RECOVERY_2 = "recovery-2"
    STABILITY = "stability"
    WITNESS_RETRY_DISCRIMINATION = "witness-retry-discrimination"
    WITNESS_ALTERNATE_VISIBILITY = "witness-alternate-visibility"
    CLEANUP_RESIDUAL_FREE = "cleanup-residual-free"


class QualificationSource(str, Enum):
    """Reviewed evidence responsibilities, not provider/backend identities."""

    EVALUATOR_PREFLIGHT = "evaluator-preflight"
    NAMESPACE_INVENTORY = "namespace-inventory"
    ROUTE_OBSERVATION = "route-observation"
    SUBJECT_SECURITY_PROBE = "subject-security-probe"
    EXACT_EXCHANGE = "exact-exchange"
    TRANSPORT_WITNESS = "transport-witness"
    CLEANUP_SENTINEL = "cleanup-sentinel"


_REQUIRED_SOURCE: dict[QualificationProperty, QualificationSource] = {
    QualificationProperty.NATIVE_LINUX: QualificationSource.EVALUATOR_PREFLIGHT,
    QualificationProperty.PRIVILEGED_EVALUATOR: QualificationSource.EVALUATOR_PREFLIGHT,
    QualificationProperty.REQUIRED_TOOLS: QualificationSource.EVALUATOR_PREFLIGHT,
    QualificationProperty.THREE_NAMESPACE_MATERIALIZATION: QualificationSource.NAMESPACE_INVENTORY,
    QualificationProperty.ROUTE_THROUGH_CONTROL: QualificationSource.ROUTE_OBSERVATION,
    QualificationProperty.NO_ROUTE_ESCAPE: QualificationSource.ROUTE_OBSERVATION,
    QualificationProperty.SUBJECT_PRIVILEGE_ISOLATION: QualificationSource.SUBJECT_SECURITY_PROBE,
    QualificationProperty.SUBJECT_CONTROL_ISOLATION: QualificationSource.SUBJECT_SECURITY_PROBE,
    QualificationProperty.SELECTED_CUT: QualificationSource.EXACT_EXCHANGE,
    QualificationProperty.NON_TARGET_SURVIVAL: QualificationSource.EXACT_EXCHANGE,
    QualificationProperty.RECOVERY_1: QualificationSource.EXACT_EXCHANGE,
    QualificationProperty.RECOVERY_2: QualificationSource.EXACT_EXCHANGE,
    QualificationProperty.STABILITY: QualificationSource.EXACT_EXCHANGE,
    QualificationProperty.WITNESS_RETRY_DISCRIMINATION: QualificationSource.TRANSPORT_WITNESS,
    QualificationProperty.WITNESS_ALTERNATE_VISIBILITY: QualificationSource.TRANSPORT_WITNESS,
    QualificationProperty.CLEANUP_RESIDUAL_FREE: QualificationSource.CLEANUP_SENTINEL,
}

_REQUIRED_PROPERTIES = tuple(QualificationProperty)


@dataclass(frozen=True, slots=True)
class QualificationFact:
    """One retained qualification assertion produced by a reviewed responsibility."""

    property: QualificationProperty
    source: QualificationSource
    verified: bool
    detail: str

    def __post_init__(self) -> None:
        if not self.detail.strip():
            raise EvidenceMaterializationError("packet-path qualification fact detail is required")


@dataclass(frozen=True, slots=True)
class PacketPathQualificationPlan:
    """Immutable PTL-001 qualification requirements for one materialized run."""

    run_id: str
    topology: PacketPathRunTopology
    required_properties: tuple[QualificationProperty, ...] = _REQUIRED_PROPERTIES

    @classmethod
    def for_topology(cls, topology: PacketPathRunTopology) -> "PacketPathQualificationPlan":
        if len(set(topology.namespace_names)) != 3:
            raise EvidenceMaterializationError(
                "packet-path qualification requires three distinct namespace identities"
            )
        if topology.selected_endpoint.family != "ipv4" or topology.control_endpoint.family != "ipv4":
            raise EvidenceMaterializationError(
                "PTL-001 canonical packet-path qualification is explicitly IPv4-bound"
            )
        return cls(run_id=topology.run_id, topology=topology)

    def prerequisite_commands(
        self,
        *,
        python_executable: str | None = None,
    ) -> tuple[tuple[str, ...], ...]:
        """Return read-only preflight argv whose outputs must be parsed and retained.

        Command success alone does not verify any non-preflight requirement. The
        future privileged lane must derive facts from the observed outputs and
        from independent route/exchange/witness/security/cleanup checks.
        """

        python = python_executable or sys.executable
        if not isinstance(python, str) or not python:
            raise EvidenceMaterializationError("qualification Python executable is required")
        return (
            ("uname", "-srm"),
            ("id", "-u"),
            ("ip", "-Version"),
            ("nft", "--version"),
            ("setpriv", "--version"),
            (python, "--version"),
        )


@dataclass(frozen=True, slots=True)
class PacketPathQualificationReport:
    """Fail-closed qualification projection for one exact packet-path run."""

    plan: PacketPathQualificationPlan
    facts: tuple[QualificationFact, ...]
    capture_assurance: CaptureAssurance

    @classmethod
    def from_facts(
        cls,
        *,
        plan: PacketPathQualificationPlan,
        facts: Iterable[QualificationFact],
        capture_assurance: CaptureAssurance,
    ) -> "PacketPathQualificationReport":
        return cls(
            plan=plan,
            facts=tuple(facts),
            capture_assurance=capture_assurance,
        )

    @property
    def ready(self) -> bool:
        return not self.problems()

    def problems(self) -> tuple[str, ...]:
        """Return deterministic qualification failures without provider verdicts."""

        problems: list[str] = []
        by_property: dict[QualificationProperty, list[QualificationFact]] = {}
        for fact in self.facts:
            by_property.setdefault(fact.property, []).append(fact)

        expected = set(self.plan.required_properties)
        unexpected = sorted(
            set(by_property) - expected,
            key=lambda item: item.value,
        )
        problems.extend(f"unexpected-property:{item.value}" for item in unexpected)

        for requirement in self.plan.required_properties:
            matches = by_property.get(requirement, [])
            if not matches:
                problems.append(f"missing:{requirement.value}")
                continue
            if len(matches) != 1:
                problems.append(f"duplicate:{requirement.value}")
                continue
            fact = matches[0]
            required_source = _REQUIRED_SOURCE[requirement]
            if fact.source is not required_source:
                problems.append(
                    f"wrong-source:{requirement.value}:{fact.source.value}"
                )
            if not fact.verified:
                problems.append(f"unverified:{requirement.value}")

        problems.extend(
            f"capture-assurance:{problem}"
            for problem in self.capture_assurance.problems()
        )
        return tuple(dict.fromkeys(problems))


def expected_source(requirement: QualificationProperty) -> QualificationSource:
    """Expose the reviewed proof responsibility for ordinary-CI contract tests."""

    return _REQUIRED_SOURCE[requirement]
