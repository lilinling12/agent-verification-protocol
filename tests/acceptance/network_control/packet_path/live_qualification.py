"""Concrete PTL-001 live-qualification orchestration contract.

This module binds the reviewed packet-path topology, controller, execution plan,
worker roles, Subject-egress witness, qualification facts, and cleanup sentinel.
It deliberately does not acquire privilege or define a GitHub Actions lane. A
future PTL-002 trusted-main runner may execute these exact responsibilities, but
must not replace independent observations with command acknowledgements.
"""

from __future__ import annotations

import ipaddress
import json
import sys
from dataclasses import dataclass
from typing import Mapping, Sequence

from ..attempt_client import ExchangeObservation
from ..evidence_core import EvidenceMaterializationError, MaterializedEndpoint
from ..witness_evidence import CaptureAssurance
from .controller import PacketPathController
from .execution import PacketPathExecutionPlan
from .qualification import (
    PacketPathQualificationPlan,
    PacketPathQualificationReport,
    QualificationFact,
    QualificationProperty,
    QualificationSource,
)
from .topology import PacketPathRunTopology
from .witness_binding import PacketPathWitnessBinding

_WORKER_MODULE = "acceptance.network_control.packet_path.worker"
_PROVISIONAL_ASSURANCE = CaptureAssurance(False, False, False, False)
_EXPECTED_PROVISIONAL_PROBLEMS = frozenset(_PROVISIONAL_ASSURANCE.problems())
_REQUIRED_TOOLS = ("ip", "nft", "setpriv", "python")
_REQUIRED_SUBJECT_ENVIRONMENT_KEYS = (
    "AVP_FUTURE_FAULT_SCHEDULE",
    "AVP_PACKET_PATH_CONTROL",
)
_REQUIRED_EXCHANGE_PHASES = (
    "subject-active-cut",
    "non-target-control",
    "recovery-1",
    "recovery-2",
    "stability",
)


@dataclass(frozen=True, slots=True)
class NamespaceInventoryObservation:
    namespace_name: str
    netns_identity: str
    ipv4_interfaces: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if not self.namespace_name or not self.netns_identity.startswith("net:["):
            raise EvidenceMaterializationError("packet-path namespace inventory identity is invalid")
        if not self.netns_identity.endswith("]"):
            raise EvidenceMaterializationError("packet-path namespace inventory netns identity is malformed")
        if len(dict(self.ipv4_interfaces)) != len(self.ipv4_interfaces):
            raise EvidenceMaterializationError("packet-path namespace inventory interface names must be unique")
        for interface, address in self.ipv4_interfaces:
            if not interface or ipaddress.ip_address(address).version != 4:
                raise EvidenceMaterializationError("PTL-001 namespace inventory must contain literal IPv4 interfaces")


@dataclass(frozen=True, slots=True)
class RouteCandidate:
    destination: str
    gateway: str | None
    device: str

    def __post_init__(self) -> None:
        if not self.device:
            raise EvidenceMaterializationError("packet-path route device is required")
        if ipaddress.ip_network(self.destination, strict=False).version != 4:
            raise EvidenceMaterializationError("PTL-001 route destination must be IPv4")
        if self.gateway is not None and ipaddress.ip_address(self.gateway).version != 4:
            raise EvidenceMaterializationError("PTL-001 route gateway must be IPv4")


@dataclass(frozen=True, slots=True)
class RouteObservation:
    subject_to_fixture: tuple[RouteCandidate, ...]
    fixture_to_subject: tuple[RouteCandidate, ...]


@dataclass(frozen=True, slots=True)
class PreflightObservation:
    uname: str
    effective_uid: int
    tool_versions: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if not self.uname.strip():
            raise EvidenceMaterializationError("packet-path preflight uname output is required")
        if isinstance(self.effective_uid, bool) or not isinstance(self.effective_uid, int):
            raise EvidenceMaterializationError("packet-path preflight effective uid must be integer")
        if len(dict(self.tool_versions)) != len(self.tool_versions):
            raise EvidenceMaterializationError("packet-path preflight tool names must be unique")
        if any(not name or not value.strip() for name, value in self.tool_versions):
            raise EvidenceMaterializationError("packet-path preflight tool versions must be non-empty")


@dataclass(frozen=True, slots=True)
class SubjectSecurityObservation:
    uid: int
    euid: int
    gid: int
    egid: int
    supplementary_groups: tuple[int, ...]
    no_new_privs: int
    capability_values: tuple[str, str, str, str, str]
    netns_identity: str
    environment_presence: tuple[tuple[str, bool], ...]


@dataclass(frozen=True, slots=True)
class QualifiedExchangeObservation:
    """Bind an exact exchange to its execution-plan phase explicitly."""

    phase_id: str
    observation: ExchangeObservation

    def __post_init__(self) -> None:
        if self.phase_id not in _REQUIRED_EXCHANGE_PHASES:
            raise EvidenceMaterializationError("packet-path qualification exchange phase is not reviewed")


@dataclass(frozen=True, slots=True)
class WitnessCanaryObservation:
    label: str
    total_initiations: int
    expected_target_initiations: int
    alternate_target_initiations: int
    raw_syn_packets: int
    retransmitted_syn_packets: int
    capture_drops: int | None
    validity_problems: tuple[str, ...]
    ready_before_injection: bool


@dataclass(frozen=True, slots=True)
class CleanupObservation:
    cleanup_problems: tuple[str, ...]
    residual_resources: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PacketPathQualificationObservations:
    preflight: PreflightObservation
    namespaces: tuple[NamespaceInventoryObservation, ...]
    routes: RouteObservation
    subject_security: SubjectSecurityObservation
    exchanges: tuple[QualifiedExchangeObservation, ...]
    witness_canaries: tuple[WitnessCanaryObservation, ...]
    cleanup: CleanupObservation


@dataclass(frozen=True, slots=True)
class PacketPathWitnessCanarySpec:
    label: str
    expected_target: MaterializedEndpoint
    packets: tuple[tuple[MaterializedEndpoint, int, int], ...]


@dataclass(frozen=True, slots=True)
class PacketPathQualificationCommands:
    """Concrete command bindings that future PTL-002 must preserve."""

    topology: PacketPathRunTopology
    controller: PacketPathController
    execution_plan: PacketPathExecutionPlan
    qualification_plan: PacketPathQualificationPlan
    python_executable: str

    @classmethod
    def build(
        cls,
        *,
        topology: PacketPathRunTopology,
        controller: PacketPathController,
        execution_plan: PacketPathExecutionPlan,
        qualification_plan: PacketPathQualificationPlan,
        python_executable: str | None = None,
    ) -> "PacketPathQualificationCommands":
        python = python_executable or sys.executable
        if controller.topology != topology:
            raise EvidenceMaterializationError("packet-path qualification controller topology drift")
        if execution_plan.topology != topology or execution_plan.negative_mode is not None:
            raise EvidenceMaterializationError("packet-path qualification requires positive execution topology")
        if qualification_plan.topology != topology or qualification_plan.run_id != topology.run_id:
            raise EvidenceMaterializationError("packet-path qualification plan topology drift")
        if not python:
            raise EvidenceMaterializationError("packet-path qualification Python executable is required")
        return cls(topology, controller, execution_plan, qualification_plan, python)

    def inventory_commands(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        worker = (self.python_executable, "-m", _WORKER_MODULE, "inventory")
        return (
            (self.topology.subject_namespace, ("ip", "netns", "exec", self.topology.subject_namespace, *worker)),
            (self.topology.control_namespace, ("ip", "netns", "exec", self.topology.control_namespace, *worker)),
            (self.topology.fixture_namespace, self.controller.fixture_command(worker)),
        )

    def route_commands(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return (
            ("ip", "-j", "-n", self.topology.subject_namespace, "route", "show", "table", "all"),
            ("ip", "-j", "-n", self.topology.fixture_namespace, "route", "show", "table", "all"),
        )

    def subject_security_command(self) -> tuple[str, ...]:
        return self.controller.subject_command((self.python_executable, "-m", _WORKER_MODULE, "security-probe"))

    def subject_security_input(self) -> dict[str, object]:
        return {"environmentKeys": list(_REQUIRED_SUBJECT_ENVIRONMENT_KEYS)}

    def witness_command_and_input(
        self,
        *,
        spec: PacketPathWitnessCanarySpec,
        attempt_id: str,
    ) -> tuple[tuple[str, ...], dict[str, object]]:
        if not attempt_id:
            raise EvidenceMaterializationError("packet-path qualification canary attempt id is required")
        binding = PacketPathWitnessBinding.for_attempt(
            topology=self.topology,
            plan=self.execution_plan.evidence_plan,
            expected_target=spec.expected_target,
            assurance=_PROVISIONAL_ASSURANCE,
        )
        return (
            binding.evaluator_namespace_command((self.python_executable, "-m", _WORKER_MODULE, "witness")),
            {
                "interfaceName": binding.interface_name,
                "sourceAddress": self.topology.subject_address,
                "expectedTarget": _endpoint_document(spec.expected_target),
                "channel": binding.scope.channel,
                "roleId": binding.scope.role_id,
                "attemptId": attempt_id,
                "assurance": {
                    "egressCoverageVerified": False,
                    "directionalityVerified": False,
                    "offloadNormalizationVerified": False,
                    "preSynConnectGapClosed": False,
                },
            },
        )

    def capture_canaries(self) -> tuple[PacketPathWitnessCanarySpec, ...]:
        selected = self.topology.selected_endpoint
        control = self.topology.control_endpoint
        return (
            PacketPathWitnessCanarySpec("one-expected", selected, ((selected, 43101, 0x4A560101),)),
            PacketPathWitnessCanarySpec("two-expected", selected, ((selected, 43102, 0x4A560201), (selected, 43103, 0x4A560301))),
            PacketPathWitnessCanarySpec("expected-plus-alternate", selected, ((selected, 43104, 0x4A560401), (control, 43105, 0x4A560501))),
            PacketPathWitnessCanarySpec("duplicate-syn-normalization", selected, ((selected, 43106, 0x4A560601), (selected, 43106, 0x4A560601))),
        )


class PacketPathLiveQualification:
    """Project only independent observations into the fail-closed report."""

    def __init__(self, commands: PacketPathQualificationCommands) -> None:
        self.commands = commands

    def project_report(self, observations: PacketPathQualificationObservations) -> PacketPathQualificationReport:
        assurance = derive_capture_assurance(observations.witness_canaries)
        return PacketPathQualificationReport.from_facts(
            plan=self.commands.qualification_plan,
            facts=self._facts(observations, assurance),
            capture_assurance=assurance,
        )

    def _facts(
        self,
        observations: PacketPathQualificationObservations,
        assurance: CaptureAssurance,
    ) -> tuple[QualificationFact, ...]:
        topology = self.commands.topology
        tools = dict(observations.preflight.tool_versions)
        namespace_ok, namespace_detail, subject_netns = _namespace_fact(topology, observations.namespaces)
        route_ok, route_detail = _route_fact(topology, observations.routes)
        privilege_ok, control_ok, security_detail = _security_facts(observations.subject_security, subject_netns)
        exchanges = _exchange_map(observations.exchanges)
        cleanup_ok = not observations.cleanup.cleanup_problems and not observations.cleanup.residual_resources
        witness_ready = not assurance.problems()
        alternate_visible = _canary_matches(observations.witness_canaries, "expected-plus-alternate", 2, 1, 1, 0)

        return (
            _fact(QualificationProperty.NATIVE_LINUX, QualificationSource.EVALUATOR_PREFLIGHT, observations.preflight.uname.lower().startswith("linux"), observations.preflight.uname),
            _fact(QualificationProperty.PRIVILEGED_EVALUATOR, QualificationSource.EVALUATOR_PREFLIGHT, observations.preflight.effective_uid == 0, f"euid={observations.preflight.effective_uid}"),
            _fact(QualificationProperty.REQUIRED_TOOLS, QualificationSource.EVALUATOR_PREFLIGHT, all(name in tools and tools[name].strip() for name in _REQUIRED_TOOLS), "tools=" + ",".join(sorted(tools))),
            _fact(QualificationProperty.THREE_NAMESPACE_MATERIALIZATION, QualificationSource.NAMESPACE_INVENTORY, namespace_ok, namespace_detail),
            _fact(QualificationProperty.ROUTE_THROUGH_CONTROL, QualificationSource.ROUTE_OBSERVATION, route_ok, route_detail),
            _fact(QualificationProperty.NO_ROUTE_ESCAPE, QualificationSource.ROUTE_OBSERVATION, route_ok, route_detail),
            _fact(QualificationProperty.SUBJECT_PRIVILEGE_ISOLATION, QualificationSource.SUBJECT_SECURITY_PROBE, privilege_ok, security_detail),
            _fact(QualificationProperty.SUBJECT_CONTROL_ISOLATION, QualificationSource.SUBJECT_SECURITY_PROBE, control_ok, security_detail),
            _fact(QualificationProperty.SELECTED_CUT, QualificationSource.EXACT_EXCHANGE, _cut_exchange(exchanges.get("subject-active-cut")), _exchange_detail(exchanges.get("subject-active-cut"))),
            _fact(QualificationProperty.NON_TARGET_SURVIVAL, QualificationSource.EXACT_EXCHANGE, _successful_exchange(exchanges.get("non-target-control")), _exchange_detail(exchanges.get("non-target-control"))),
            _fact(QualificationProperty.RECOVERY_1, QualificationSource.EXACT_EXCHANGE, _successful_exchange(exchanges.get("recovery-1")), _exchange_detail(exchanges.get("recovery-1"))),
            _fact(QualificationProperty.RECOVERY_2, QualificationSource.EXACT_EXCHANGE, _successful_exchange(exchanges.get("recovery-2")), _exchange_detail(exchanges.get("recovery-2"))),
            _fact(QualificationProperty.STABILITY, QualificationSource.EXACT_EXCHANGE, _successful_exchange(exchanges.get("stability")), _exchange_detail(exchanges.get("stability"))),
            _fact(QualificationProperty.WITNESS_RETRY_DISCRIMINATION, QualificationSource.TRANSPORT_WITNESS, witness_ready, "four provisional-assurance canaries including duplicate-SYN normalization"),
            _fact(QualificationProperty.WITNESS_ALTERNATE_VISIBILITY, QualificationSource.TRANSPORT_WITNESS, alternate_visible, "expected-plus-alternate canary"),
            _fact(QualificationProperty.CLEANUP_RESIDUAL_FREE, QualificationSource.CLEANUP_SENTINEL, cleanup_ok, f"cleanup-problems={len(observations.cleanup.cleanup_problems)},residual={len(observations.cleanup.residual_resources)}"),
        )


def derive_capture_assurance(canaries: Sequence[WitnessCanaryObservation]) -> CaptureAssurance:
    one = _canary_matches(canaries, "one-expected", 1, 1, 0, 0)
    two = _canary_matches(canaries, "two-expected", 2, 2, 0, 0)
    alternate = _canary_matches(canaries, "expected-plus-alternate", 2, 1, 1, 0)
    duplicate = _canary_matches(canaries, "duplicate-syn-normalization", 1, 1, 0, 1, minimum_raw=2)
    labels = {item.label for item in canaries}
    ready = len(canaries) == 4 and labels == {
        "one-expected",
        "two-expected",
        "expected-plus-alternate",
        "duplicate-syn-normalization",
    } and all(item.ready_before_injection for item in canaries)
    return CaptureAssurance(
        egress_coverage_verified=one and two,
        directionality_verified=one and alternate,
        offload_normalization_verified=duplicate,
        pre_syn_connect_gap_closed=ready and one and two and alternate and duplicate,
    )


def parse_namespace_inventory(*, namespace_name: str, document: Mapping[str, object]) -> NamespaceInventoryObservation:
    netns = document.get("netNamespace")
    interfaces = document.get("interfaces")
    if not isinstance(netns, str) or not isinstance(interfaces, list):
        raise EvidenceMaterializationError("packet-path inventory document shape is invalid")
    values: list[tuple[str, str]] = []
    for item in interfaces:
        if not isinstance(item, dict):
            raise EvidenceMaterializationError("packet-path inventory interface entry is invalid")
        if bool(item.get("loopback", False)) or item.get("ipv4Address") is None:
            continue
        name, address = item.get("interface"), item.get("ipv4Address")
        if not isinstance(name, str) or not isinstance(address, str):
            raise EvidenceMaterializationError("packet-path inventory interface identity is invalid")
        values.append((name, address))
    return NamespaceInventoryObservation(namespace_name, netns, tuple(sorted(values)))


def parse_route_candidates(payload: str, *, target_address: str) -> tuple[RouteCandidate, ...]:
    try:
        value = json.loads(payload)
        target = ipaddress.ip_address(target_address)
    except (json.JSONDecodeError, ValueError) as exc:
        raise EvidenceMaterializationError("packet-path route observation is invalid") from exc
    if target.version != 4 or not isinstance(value, list):
        raise EvidenceMaterializationError("PTL-001 route observation must be an IPv4 JSON array")
    result: list[RouteCandidate] = []
    for item in value:
        if not isinstance(item, dict):
            raise EvidenceMaterializationError("packet-path route entry must be an object")
        raw_destination = item.get("dst", "default")
        try:
            network = ipaddress.ip_network("0.0.0.0/0" if raw_destination == "default" else str(raw_destination), strict=False)
        except ValueError:
            continue
        if target not in network:
            continue
        device = item.get("dev")
        if not isinstance(device, str) or not device:
            continue
        gateway = item.get("gateway")
        result.append(RouteCandidate(str(network), None if gateway is None else str(gateway), device))
    return tuple(result)


def _namespace_fact(
    topology: PacketPathRunTopology,
    observations: Sequence[NamespaceInventoryObservation],
) -> tuple[bool, str, str | None]:
    by_name = {item.namespace_name: item for item in observations}
    if len(by_name) != len(observations) or set(by_name) != set(topology.namespace_names):
        return False, "namespace inventory names differ from sealed topology", None
    if len({item.netns_identity for item in observations}) != 3:
        return False, "namespace kernel identities are not distinct", None
    expected = {
        topology.subject_namespace: {(topology.subject_interface, topology.subject_address)},
        topology.control_namespace: {
            (topology.router_subject_interface, topology.router_subject_address),
            (topology.router_fixture_interface, topology.router_fixture_address),
        },
        topology.fixture_namespace: {(topology.fixture_interface, topology.fixture_address)},
    }
    if any(set(by_name[name].ipv4_interfaces) != interfaces for name, interfaces in expected.items()):
        return False, "namespace IPv4 inventory differs from reviewed topology", None
    return True, "three distinct netns with exact reviewed IPv4 interfaces", by_name[topology.subject_namespace].netns_identity


def _route_fact(topology: PacketPathRunTopology, observation: RouteObservation) -> tuple[bool, str]:
    subject = RouteCandidate(topology.fixture_subnet, topology.router_subject_address, topology.subject_interface)
    fixture = RouteCandidate(topology.subject_subnet, topology.router_fixture_address, topology.fixture_interface)
    ok = observation.subject_to_fixture == (subject,) and observation.fixture_to_subject == (fixture,)
    return ok, f"subject-matches={len(observation.subject_to_fixture)},fixture-matches={len(observation.fixture_to_subject)}"


def _security_facts(
    observation: SubjectSecurityObservation,
    subject_netns: str | None,
) -> tuple[bool, bool, str]:
    zero_caps = all(value and set(value) <= {"0"} for value in observation.capability_values)
    privilege_ok = (
        observation.uid == observation.euid == 65534
        and observation.gid == observation.egid == 65534
        and not observation.supplementary_groups
        and observation.no_new_privs == 1
        and zero_caps
    )
    environment = dict(observation.environment_presence)
    control_ok = (
        privilege_ok
        and subject_netns is not None
        and observation.netns_identity == subject_netns
        and set(environment) == set(_REQUIRED_SUBJECT_ENVIRONMENT_KEYS)
        and not any(environment.values())
    )
    return privilege_ok, control_ok, f"euid={observation.euid},groups={len(observation.supplementary_groups)},zero-caps={zero_caps},netns-match={subject_netns == observation.netns_identity if subject_netns else False}"


def _exchange_map(observations: Sequence[QualifiedExchangeObservation]) -> dict[str, ExchangeObservation]:
    result: dict[str, ExchangeObservation] = {}
    for item in observations:
        if item.phase_id in result:
            raise EvidenceMaterializationError("packet-path qualification exchange phase is duplicated")
        result[item.phase_id] = item.observation
    if set(result) != set(_REQUIRED_EXCHANGE_PHASES):
        raise EvidenceMaterializationError("packet-path qualification exchange phase set is incomplete")
    return result


def _cut_exchange(observation: ExchangeObservation | None) -> bool:
    return bool(observation is not None and not observation.completed and not observation.mismatch_observed and observation.observation_budget_expired and observation.native_error is None)


def _successful_exchange(observation: ExchangeObservation | None) -> bool:
    return bool(observation is not None and observation.completed and not observation.mismatch_observed and not observation.observation_budget_expired and observation.native_error is None)


def _canary_matches(
    canaries: Sequence[WitnessCanaryObservation],
    label: str,
    total: int,
    expected: int,
    alternate: int,
    retransmitted: int,
    *,
    minimum_raw: int | None = None,
) -> bool:
    matches = [item for item in canaries if item.label == label]
    if len(matches) != 1:
        return False
    item = matches[0]
    return (
        item.ready_before_injection
        and item.capture_drops == 0
        and set(item.validity_problems) == _EXPECTED_PROVISIONAL_PROBLEMS
        and item.total_initiations == total
        and item.expected_target_initiations == expected
        and item.alternate_target_initiations == alternate
        and item.raw_syn_packets >= (total if minimum_raw is None else minimum_raw)
        and item.retransmitted_syn_packets == retransmitted
    )


def _fact(
    property: QualificationProperty,
    source: QualificationSource,
    verified: bool,
    detail: str,
) -> QualificationFact:
    return QualificationFact(property=property, source=source, verified=bool(verified), detail=detail)


def _exchange_detail(observation: ExchangeObservation | None) -> str:
    if observation is None:
        return "missing exchange observation"
    return f"completed={observation.completed},expired={observation.observation_budget_expired},mismatch={observation.mismatch_observed},native-error={observation.native_error}"


def _endpoint_document(endpoint: MaterializedEndpoint) -> dict[str, object]:
    return {"family": endpoint.family, "address": endpoint.address, "port": endpoint.port, "role": endpoint.role}
