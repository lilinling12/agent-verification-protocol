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
from .execution import PacketPathExecutionPlan, PacketPathStepId
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


@dataclass(frozen=True, slots=True)
class NamespaceInventoryObservation:
    """One evaluator-owned inventory result from a named network namespace."""

    namespace_name: str
    netns_identity: str
    ipv4_interfaces: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if not self.namespace_name or not self.netns_identity:
            raise EvidenceMaterializationError("packet-path namespace inventory identity is required")
        if not self.netns_identity.startswith("net:[") or not self.netns_identity.endswith("]"):
            raise EvidenceMaterializationError("packet-path namespace inventory netns identity is malformed")
        interfaces = dict(self.ipv4_interfaces)
        if len(interfaces) != len(self.ipv4_interfaces):
            raise EvidenceMaterializationError("packet-path namespace inventory interface names must be unique")
        for interface, address in self.ipv4_interfaces:
            if not interface:
                raise EvidenceMaterializationError("packet-path namespace inventory interface name is required")
            try:
                parsed = ipaddress.ip_address(address)
            except ValueError as exc:
                raise EvidenceMaterializationError("packet-path namespace inventory address is invalid") from exc
            if parsed.version != 4:
                raise EvidenceMaterializationError("PTL-001 namespace inventory is IPv4-bound")


@dataclass(frozen=True, slots=True)
class RouteCandidate:
    """One route-table entry whose destination covers the queried remote address."""

    destination: str
    gateway: str | None
    device: str
    table: str | int | None = None

    def __post_init__(self) -> None:
        if not self.destination or not self.device:
            raise EvidenceMaterializationError("packet-path route candidate destination/device is required")
        try:
            ipaddress.ip_network(self.destination, strict=False)
        except ValueError as exc:
            raise EvidenceMaterializationError("packet-path route candidate destination is invalid") from exc
        if self.gateway is not None:
            try:
                gateway = ipaddress.ip_address(self.gateway)
            except ValueError as exc:
                raise EvidenceMaterializationError("packet-path route candidate gateway is invalid") from exc
            if gateway.version != 4:
                raise EvidenceMaterializationError("PTL-001 route gateway is IPv4-bound")


@dataclass(frozen=True, slots=True)
class RouteObservation:
    """Exhaustive matching routes from Subject and fixture tables."""

    subject_to_fixture: tuple[RouteCandidate, ...]
    fixture_to_subject: tuple[RouteCandidate, ...]


@dataclass(frozen=True, slots=True)
class PreflightObservation:
    """Read-only evaluator preflight outputs retained before topology mutation."""

    uname: str
    effective_uid: int
    tool_versions: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if not self.uname.strip():
            raise EvidenceMaterializationError("packet-path preflight uname output is required")
        if isinstance(self.effective_uid, bool) or not isinstance(self.effective_uid, int):
            raise EvidenceMaterializationError("packet-path preflight effective uid must be integer")
        versions = dict(self.tool_versions)
        if len(versions) != len(self.tool_versions):
            raise EvidenceMaterializationError("packet-path preflight tool names must be unique")
        if any(not name or not value.strip() for name, value in self.tool_versions):
            raise EvidenceMaterializationError("packet-path preflight tool versions must be non-empty")


@dataclass(frozen=True, slots=True)
class SubjectSecurityObservation:
    """Observed Subject process authority; environment values are never retained."""

    uid: int
    euid: int
    gid: int
    egid: int
    supplementary_groups: tuple[int, ...]
    no_new_privs: int
    inheritable_caps: str
    permitted_caps: str
    effective_caps: str
    bounding_caps: str
    ambient_caps: str
    netns_identity: str
    environment_presence: tuple[tuple[str, bool], ...]

    @property
    def capability_values(self) -> tuple[str, ...]:
        return (
            self.inheritable_caps,
            self.permitted_caps,
            self.effective_caps,
            self.bounding_caps,
            self.ambient_caps,
        )


@dataclass(frozen=True, slots=True)
class WitnessCanaryObservation:
    """Normalized witness facts from one provisional-assurance canary window."""

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
    """All independent observations required to project a qualification report."""

    preflight: PreflightObservation
    namespaces: tuple[NamespaceInventoryObservation, ...]
    routes: RouteObservation
    subject_security: SubjectSecurityObservation
    exchanges: tuple[ExchangeObservation, ...]
    witness_canaries: tuple[WitnessCanaryObservation, ...]
    cleanup: CleanupObservation


@dataclass(frozen=True, slots=True)
class PacketPathWitnessCanarySpec:
    """Qualification-only SYN assembly observed at the Subject egress boundary."""

    label: str
    expected_target: MaterializedEndpoint
    packets: tuple[tuple[MaterializedEndpoint, int, int], ...]

    def injector_command(
        self,
        *,
        topology: PacketPathRunTopology,
        python_executable: str,
    ) -> tuple[str, ...]:
        if not python_executable:
            raise EvidenceMaterializationError("packet-path canary Python executable is required")
        script = _raw_syn_injector_script(
            source_address=topology.subject_address,
            packets=self.packets,
        )
        return (
            "ip",
            "netns",
            "exec",
            topology.subject_namespace,
            python_executable,
            "-c",
            script,
        )


@dataclass(frozen=True, slots=True)
class PacketPathQualificationCommands:
    """Concrete read/worker command bindings future PTL-002 must preserve."""

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
        return cls(
            topology=topology,
            controller=controller,
            execution_plan=execution_plan,
            qualification_plan=qualification_plan,
            python_executable=python,
        )

    def inventory_commands(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        worker = (self.python_executable, "-m", _WORKER_MODULE, "inventory")
        return (
            (
                self.topology.subject_namespace,
                ("ip", "netns", "exec", self.topology.subject_namespace, *worker),
            ),
            (
                self.topology.control_namespace,
                ("ip", "netns", "exec", self.topology.control_namespace, *worker),
            ),
            (
                self.topology.fixture_namespace,
                self.controller.fixture_command(worker),
            ),
        )

    def route_commands(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return (
            (
                "ip",
                "-j",
                "-n",
                self.topology.subject_namespace,
                "route",
                "show",
                "table",
                "all",
            ),
            (
                "ip",
                "-j",
                "-n",
                self.topology.fixture_namespace,
                "route",
                "show",
                "table",
                "all",
            ),
        )

    def subject_security_command(self) -> tuple[str, ...]:
        return self.controller.subject_command(
            (
                self.python_executable,
                "-m",
                _WORKER_MODULE,
                "security-probe",
            )
        )

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
        command = binding.evaluator_namespace_command(
            (self.python_executable, "-m", _WORKER_MODULE, "witness")
        )
        document = {
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
        }
        return command, document

    def capture_canaries(self) -> tuple[PacketPathWitnessCanarySpec, ...]:
        selected = self.topology.selected_endpoint
        control = self.topology.control_endpoint
        return (
            PacketPathWitnessCanarySpec(
                label="one-expected",
                expected_target=selected,
                packets=((selected, 43101, 0x4A560101),),
            ),
            PacketPathWitnessCanarySpec(
                label="two-expected",
                expected_target=selected,
                packets=(
                    (selected, 43102, 0x4A560201),
                    (selected, 43103, 0x4A560301),
                ),
            ),
            PacketPathWitnessCanarySpec(
                label="expected-plus-alternate",
                expected_target=selected,
                packets=(
                    (selected, 43104, 0x4A560401),
                    (control, 43105, 0x4A560501),
                ),
            ),
            PacketPathWitnessCanarySpec(
                label="duplicate-syn-normalization",
                expected_target=selected,
                packets=(
                    (selected, 43106, 0x4A560601),
                    (selected, 43106, 0x4A560601),
                ),
            ),
        )


class PacketPathLiveQualification:
    """Project independently observed PTL-001 facts into the fail-closed report."""

    def __init__(self, commands: PacketPathQualificationCommands) -> None:
        self.commands = commands

    def project_report(
        self,
        observations: PacketPathQualificationObservations,
    ) -> PacketPathQualificationReport:
        facts = self._facts(observations)
        assurance = derive_capture_assurance(observations.witness_canaries)
        return PacketPathQualificationReport.from_facts(
            plan=self.commands.qualification_plan,
            facts=facts,
            capture_assurance=assurance,
        )

    def _facts(
        self,
        observations: PacketPathQualificationObservations,
    ) -> tuple[QualificationFact, ...]:
        topology = self.commands.topology
        preflight = observations.preflight
        tools = dict(preflight.tool_versions)
        native_linux = preflight.uname.strip().lower().startswith("linux")
        privileged = preflight.effective_uid == 0
        required_tools = all(name in tools and bool(tools[name].strip()) for name in _REQUIRED_TOOLS)

        namespace_ok, namespace_detail, subject_netns = _namespace_fact(topology, observations.namespaces)
        route_ok, no_escape, route_detail = _route_facts(topology, observations.routes)
        privilege_ok, control_ok, security_detail = _security_facts(
            observations.subject_security,
            subject_netns=subject_netns,
        )
        exchanges = _exchange_map(observations.exchanges)
        selected_cut = _cut_exchange(exchanges.get("subject-active-cut"))
        non_target = _successful_exchange(exchanges.get("non-target-control"))
        recovery_1 = _successful_exchange(exchanges.get("recovery-1"))
        recovery_2 = _successful_exchange(exchanges.get("recovery-2"))
        stability = _successful_exchange(exchanges.get("stability"))
        assurance = derive_capture_assurance(observations.witness_canaries)
        retry_discrimination = (
            assurance.egress_coverage_verified
            and assurance.directionality_verified
            and assurance.offload_normalization_verified
            and assurance.pre_syn_connect_gap_closed
        )
        alternate_visibility = _canary_matches(
            observations.witness_canaries,
            label="expected-plus-alternate",
            total=2,
            expected=1,
            alternate=1,
            retransmitted=0,
        )
        cleanup_ok = not observations.cleanup.cleanup_problems and not observations.cleanup.residual_resources

        return (
            _fact(QualificationProperty.NATIVE_LINUX, QualificationSource.EVALUATOR_PREFLIGHT, native_linux, preflight.uname),
            _fact(QualificationProperty.PRIVILEGED_EVALUATOR, QualificationSource.EVALUATOR_PREFLIGHT, privileged, f"euid={preflight.effective_uid}"),
            _fact(QualificationProperty.REQUIRED_TOOLS, QualificationSource.EVALUATOR_PREFLIGHT, required_tools, "tools=" + ",".join(sorted(tools))),
            _fact(QualificationProperty.THREE_NAMESPACE_MATERIALIZATION, QualificationSource.NAMESPACE_INVENTORY, namespace_ok, namespace_detail),
            _fact(QualificationProperty.ROUTE_THROUGH_CONTROL, QualificationSource.ROUTE_OBSERVATION, route_ok, route_detail),
            _fact(QualificationProperty.NO_ROUTE_ESCAPE, QualificationSource.ROUTE_OBSERVATION, no_escape, route_detail),
            _fact(QualificationProperty.SUBJECT_PRIVILEGE_ISOLATION, QualificationSource.SUBJECT_SECURITY_PROBE, privilege_ok, security_detail),
            _fact(QualificationProperty.SUBJECT_CONTROL_ISOLATION, QualificationSource.SUBJECT_SECURITY_PROBE, control_ok, security_detail),
            _fact(QualificationProperty.SELECTED_CUT, QualificationSource.EXACT_EXCHANGE, selected_cut, _exchange_detail(exchanges.get("subject-active-cut"))),
            _fact(QualificationProperty.NON_TARGET_SURVIVAL, QualificationSource.EXACT_EXCHANGE, non_target, _exchange_detail(exchanges.get("non-target-control"))),
            _fact(QualificationProperty.RECOVERY_1, QualificationSource.EXACT_EXCHANGE, recovery_1, _exchange_detail(exchanges.get("recovery-1"))),
            _fact(QualificationProperty.RECOVERY_2, QualificationSource.EXACT_EXCHANGE, recovery_2, _exchange_detail(exchanges.get("recovery-2"))),
            _fact(QualificationProperty.STABILITY, QualificationSource.EXACT_EXCHANGE, stability, _exchange_detail(exchanges.get("stability"))),
            _fact(QualificationProperty.WITNESS_RETRY_DISCRIMINATION, QualificationSource.TRANSPORT_WITNESS, retry_discrimination, "four provisional-assurance canaries including duplicate-SYN normalization"),
            _fact(QualificationProperty.WITNESS_ALTERNATE_VISIBILITY, QualificationSource.TRANSPORT_WITNESS, alternate_visibility, "expected-plus-alternate canary"),
            _fact(QualificationProperty.CLEANUP_RESIDUAL_FREE, QualificationSource.CLEANUP_SENTINEL, cleanup_ok, _cleanup_detail(observations.cleanup)),
        )


def derive_capture_assurance(
    canaries: Sequence[WitnessCanaryObservation],
) -> CaptureAssurance:
    """Derive assurance only from real provisional-assurance canary observations."""

    one = _canary_matches(
        canaries,
        label="one-expected",
        total=1,
        expected=1,
        alternate=0,
        retransmitted=0,
    )
    two = _canary_matches(
        canaries,
        label="two-expected",
        total=2,
        expected=2,
        alternate=0,
        retransmitted=0,
    )
    alternate = _canary_matches(
        canaries,
        label="expected-plus-alternate",
        total=2,
        expected=1,
        alternate=1,
        retransmitted=0,
    )
    duplicate = _canary_matches(
        canaries,
        label="duplicate-syn-normalization",
        total=1,
        expected=1,
        alternate=0,
        retransmitted=1,
        minimum_raw=2,
    )
    all_ready = _all_canaries_ready(canaries)
    return CaptureAssurance(
        egress_coverage_verified=one and two,
        directionality_verified=one and alternate,
        offload_normalization_verified=duplicate,
        pre_syn_connect_gap_closed=all_ready and one and two and alternate and duplicate,
    )


def parse_namespace_inventory(
    *,
    namespace_name: str,
    document: Mapping[str, object],
) -> NamespaceInventoryObservation:
    netns = document.get("netNamespace")
    interfaces = document.get("interfaces")
    if not isinstance(netns, str) or not isinstance(interfaces, list):
        raise EvidenceMaterializationError("packet-path inventory document shape is invalid")
    ipv4: list[tuple[str, str]] = []
    for item in interfaces:
        if not isinstance(item, dict):
            raise EvidenceMaterializationError("packet-path inventory interface entry is invalid")
        address = item.get("ipv4Address")
        if bool(item.get("loopback", False)) or address is None:
            continue
        name = item.get("interface")
        if not isinstance(name, str) or not isinstance(address, str):
            raise EvidenceMaterializationError("packet-path inventory interface identity is invalid")
        ipv4.append((name, address))
    return NamespaceInventoryObservation(namespace_name, netns, tuple(sorted(ipv4)))


def parse_route_candidates(payload: str, *, target_address: str) -> tuple[RouteCandidate, ...]:
    """Select every route entry whose destination can route the remote target."""

    try:
        target = ipaddress.ip_address(target_address)
        value = json.loads(payload)
    except (ValueError, json.JSONDecodeError) as exc:
        raise EvidenceMaterializationError("packet-path route observation is invalid") from exc
    if target.version != 4 or not isinstance(value, list):
        raise EvidenceMaterializationError("PTL-001 route observation must be IPv4 JSON array")

    matches: list[RouteCandidate] = []
    for item in value:
        if not isinstance(item, dict):
            raise EvidenceMaterializationError("packet-path route entry must be an object")
        destination_value = item.get("dst", "default")
        if destination_value == "default":
            network = ipaddress.ip_network("0.0.0.0/0")
            destination = "0.0.0.0/0"
        else:
            try:
                network = ipaddress.ip_network(str(destination_value), strict=False)
            except ValueError:
                continue
            destination = str(network)
        if target not in network:
            continue
        device = item.get("dev")
        if not isinstance(device, str) or not device:
            continue
        gateway_value = item.get("gateway")
        gateway = None if gateway_value is None else str(gateway_value)
        matches.append(
            RouteCandidate(
                destination=destination,
                gateway=gateway,
                device=device,
                table=item.get("table"),
            )
        )
    return tuple(matches)


def _namespace_fact(
    topology: PacketPathRunTopology,
    observations: Sequence[NamespaceInventoryObservation],
) -> tuple[bool, str, str | None]:
    by_name = {item.namespace_name: item for item in observations}
    if len(by_name) != len(observations):
        return False, "duplicate namespace inventory", None
    expected_names = set(topology.namespace_names)
    if set(by_name) != expected_names:
        return False, "namespace inventory names differ from sealed topology", None
    identities = {item.netns_identity for item in observations}
    if len(identities) != 3:
        return False, "namespace kernel identities are not three-way distinct", None

    expected_interfaces = {
        topology.subject_namespace: {(topology.subject_interface, topology.subject_address)},
        topology.control_namespace: {
            (topology.router_subject_interface, topology.router_subject_address),
            (topology.router_fixture_interface, topology.router_fixture_address),
        },
        topology.fixture_namespace: {(topology.fixture_interface, topology.fixture_address)},
    }
    for namespace, expected in expected_interfaces.items():
        if set(by_name[namespace].ipv4_interfaces) != expected:
            return False, f"unexpected IPv4 interface inventory in {namespace}", None
    return True, "three distinct netns with exact reviewed IPv4 interfaces", by_name[topology.subject_namespace].netns_identity


def _route_facts(topology: PacketPathRunTopology, observation: RouteObservation) -> tuple[bool, bool, str]:
    expected_subject = RouteCandidate(
        destination=topology.fixture_subnet,
        gateway=topology.router_subject_address,
        device=topology.subject_interface,
    )
    expected_fixture = RouteCandidate(
        destination=topology.subject_subnet,
        gateway=topology.router_fixture_address,
        device=topology.fixture_interface,
    )

    def matches(candidate: RouteCandidate, expected: RouteCandidate) -> bool:
        return (
            candidate.destination == expected.destination
            and candidate.gateway == expected.gateway
            and candidate.device == expected.device
        )

    through_control = (
        len(observation.subject_to_fixture) == 1
        and len(observation.fixture_to_subject) == 1
        and matches(observation.subject_to_fixture[0], expected_subject)
        and matches(observation.fixture_to_subject[0], expected_fixture)
    )
    no_escape = through_control
    detail = (
        f"subject-matches={len(observation.subject_to_fixture)},"
        f"fixture-matches={len(observation.fixture_to_subject)}"
    )
    return through_control, no_escape, detail


def _security_facts(
    observation: SubjectSecurityObservation,
    *,
    subject_netns: str | None,
) -> tuple[bool, bool, str]:
    zero_caps = all(value and set(value) <= {"0"} for value in observation.capability_values)
    privilege_ok = (
        observation.uid == 65534
        and observation.euid == 65534
        and observation.gid == 65534
        and observation.egid == 65534
        and not observation.supplementary_groups
        and observation.no_new_privs == 1
        and zero_caps
    )
    environment = dict(observation.environment_presence)
    required_environment_observed = set(environment) == set(_REQUIRED_SUBJECT_ENVIRONMENT_KEYS)
    control_ok = (
        privilege_ok
        and subject_netns is not None
        and observation.netns_identity == subject_netns
        and required_environment_observed
        and not any(environment.values())
    )
    detail = (
        f"uid={observation.euid},groups={len(observation.supplementary_groups)},"
        f"no-new-privs={observation.no_new_privs},zero-caps={zero_caps},"
        f"subject-netns-match={subject_netns == observation.netns_identity if subject_netns else False}"
    )
    return privilege_ok, control_ok, detail


def _exchange_map(observations: Sequence[ExchangeObservation]) -> dict[str, ExchangeObservation]:
    result: dict[str, ExchangeObservation] = {}
    for observation in observations:
        phase = observation.attempt_id.split(":", 1)[0] if ":" in observation.attempt_id else ""
        # Live PTL-001 retains phase identity separately when collecting the
        # worker result; ordinary-CI fixtures encode it as the attempt-id prefix.
        if not phase:
            raise EvidenceMaterializationError(
                "packet-path qualification exchange attempt id must retain phase prefix"
            )
        if phase in result:
            raise EvidenceMaterializationError("packet-path qualification exchange phase is duplicated")
        result[phase] = observation
    return result


def _cut_exchange(observation: ExchangeObservation | None) -> bool:
    return bool(
        observation is not None
        and not observation.completed
        and not observation.mismatch_observed
        and observation.observation_budget_expired
        and observation.native_error is None
    )


def _successful_exchange(observation: ExchangeObservation | None) -> bool:
    return bool(
        observation is not None
        and observation.completed
        and not observation.mismatch_observed
        and not observation.observation_budget_expired
        and observation.native_error is None
    )


def _canary_matches(
    canaries: Sequence[WitnessCanaryObservation],
    *,
    label: str,
    total: int,
    expected: int,
    alternate: int,
    retransmitted: int,
    minimum_raw: int | None = None,
) -> bool:
    matches = [item for item in canaries if item.label == label]
    if len(matches) != 1:
        return False
    item = matches[0]
    if not item.ready_before_injection or item.capture_drops != 0:
        return False
    if set(item.validity_problems) != _EXPECTED_PROVISIONAL_PROBLEMS:
        return False
    raw_floor = total if minimum_raw is None else minimum_raw
    return (
        item.total_initiations == total
        and item.expected_target_initiations == expected
        and item.alternate_target_initiations == alternate
        and item.raw_syn_packets >= raw_floor
        and item.retransmitted_syn_packets == retransmitted
    )


def _all_canaries_ready(canaries: Sequence[WitnessCanaryObservation]) -> bool:
    expected = {
        "one-expected",
        "two-expected",
        "expected-plus-alternate",
        "duplicate-syn-normalization",
    }
    return len(canaries) == 4 and {item.label for item in canaries} == expected and all(
        item.ready_before_injection for item in canaries
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
    return (
        f"completed={observation.completed},expired={observation.observation_budget_expired},"
        f"mismatch={observation.mismatch_observed},native-error={observation.native_error}"
    )


def _cleanup_detail(observation: CleanupObservation) -> str:
    return (
        f"cleanup-problems={len(observation.cleanup_problems)},"
        f"residual-resources={len(observation.residual_resources)}"
    )


def _endpoint_document(endpoint: MaterializedEndpoint) -> dict[str, object]:
    return {
        "family": endpoint.family,
        "address": endpoint.address,
        "port": endpoint.port,
        "role": endpoint.role,
    }


def _raw_syn_injector_script(
    *,
    source_address: str,
    packets: Sequence[tuple[MaterializedEndpoint, int, int]],
) -> str:
    """Build qualification-only raw SYN injection with no provider dependency."""

    if not packets:
        raise EvidenceMaterializationError("packet-path qualification SYN canary cannot be empty")
    packet_rows: list[tuple[str, int, int, int]] = []
    for endpoint, source_port, sequence in packets:
        if endpoint.family != "ipv4":
            raise EvidenceMaterializationError("PTL-001 qualification SYN injector is IPv4-bound")
        if not (1024 <= source_port <= 65535) or not (0 <= sequence <= 0xFFFFFFFF):
            raise EvidenceMaterializationError("packet-path qualification SYN identity is out of range")
        packet_rows.append((endpoint.address, endpoint.port, source_port, sequence))
    return (
        "import socket,struct,time\n"
        f"src={source_address!r}; rows={packet_rows!r}\n"
        "def checksum(data):\n"
        " if len(data)%2: data+=b'\\x00'\n"
        " words=struct.unpack(f'!{len(data)//2}H',data); total=sum(words)\n"
        " while total>>16: total=(total&0xffff)+(total>>16)\n"
        " return (~total)&0xffff\n"
        "src_b=socket.inet_aton(src)\n"
        "sock=socket.socket(socket.AF_INET,socket.SOCK_RAW,socket.IPPROTO_RAW)\n"
        "sock.setsockopt(socket.IPPROTO_IP,socket.IP_HDRINCL,1)\n"
        "for dst,dport,sport,seq in rows:\n"
        " dst_b=socket.inet_aton(dst); ver_ihl=(4<<4)|5\n"
        " ip=struct.pack('!BBHHHBBH4s4s',ver_ihl,0,40,0x4A11,0,64,socket.IPPROTO_TCP,0,src_b,dst_b)\n"
        " ip=struct.pack('!BBHHHBBH4s4s',ver_ihl,0,40,0x4A11,0,64,socket.IPPROTO_TCP,checksum(ip),src_b,dst_b)\n"
        " flags=(5<<12)|0x002\n"
        " tcp=struct.pack('!HHLLHHHH',sport,dport,seq,0,flags,65535,0,0)\n"
        " pseudo=struct.pack('!4s4sBBH',src_b,dst_b,0,socket.IPPROTO_TCP,len(tcp))\n"
        " tcp=struct.pack('!HHLLHHHH',sport,dport,seq,0,flags,65535,checksum(pseudo+tcp),0)\n"
        " sock.sendto(ip+tcp,(dst,0)); time.sleep(0.01)\n"
        "sock.close()\n"
    )
