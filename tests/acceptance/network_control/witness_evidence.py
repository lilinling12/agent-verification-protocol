"""Pure transport-witness evidence model and normalization for TEL-001."""

from __future__ import annotations

import base64
import hashlib
import ipaddress
import json
from dataclasses import dataclass
from typing import Iterable

from .evidence_core import ArtifactRef, InitiationFacts, MaterializedEndpoint
from .tcp_packets import PacketParseError, build_synthetic_syn_frame, parse_initial_syn

_PACKET_OUTGOING = 4


@dataclass(frozen=True, slots=True)
class CaptureAssurance:
    """Reviewed preflight facts that packet parsing cannot prove by itself."""

    egress_coverage_verified: bool
    directionality_verified: bool
    offload_normalization_verified: bool
    pre_syn_connect_gap_closed: bool

    def problems(self) -> tuple[str, ...]:
        checks = (
            (self.egress_coverage_verified, "egress-coverage-unverified"),
            (self.directionality_verified, "directionality-unverified"),
            (self.offload_normalization_verified, "offload-normalization-unverified"),
            (self.pre_syn_connect_gap_closed, "pre-syn-connect-gap-unclosed"),
        )
        return tuple(problem for verified, problem in checks if not verified)


@dataclass(frozen=True, slots=True)
class WitnessScope:
    channel: str
    role_id: str
    source_addresses: tuple[str, ...]
    expected_target: MaterializedEndpoint

    def __post_init__(self) -> None:
        if not self.channel or not self.role_id:
            raise ValueError("witness channel and role identity must be non-empty")
        if not self.source_addresses:
            raise ValueError("witness scope must declare at least one literal role address")
        normalized = tuple(str(ipaddress.ip_address(address)) for address in self.source_addresses)
        if len(set(normalized)) != len(normalized):
            raise ValueError("witness role addresses must be unique")
        object.__setattr__(self, "source_addresses", normalized)

    def matches_source(self, address: str) -> bool:
        return str(ipaddress.ip_address(address)) in self.source_addresses


@dataclass(frozen=True, slots=True)
class TcpSynObservation:
    channel: str
    role_id: str
    attempt_id: str
    interface_name: str
    interface_index: int
    monotonic_ns: int
    family: str
    source_address: str
    source_port: int
    destination_address: str
    destination_port: int
    sequence: int
    packet_type: int
    raw_frame_sha256: str

    @property
    def initiation_key(self) -> tuple[object, ...]:
        # Tuple + initial sequence distinguishes a new connect from SYN
        # retransmission in the bounded attempt window. It stays diagnostic-only.
        return (
            self.family,
            self.source_address,
            self.source_port,
            self.destination_address,
            self.destination_port,
            self.sequence,
        )


@dataclass(frozen=True, slots=True)
class RawFrameRecord:
    attempt_id: str
    interface_name: str
    interface_index: int
    monotonic_ns: int
    packet_type: int
    frame: bytes


@dataclass(frozen=True, slots=True)
class WitnessResult:
    attempt_id: str
    channel_facts: tuple[InitiationFacts, ...]
    validity_problems: tuple[str, ...]
    raw_artifact_ref: ArtifactRef | None
    raw_artifact_bytes: bytes
    capture_packets: int | None
    capture_drops: int | None

    def facts_for(self, channel: str) -> InitiationFacts:
        matches = [facts for facts in self.channel_facts if facts.channel == channel]
        if len(matches) != 1:
            raise KeyError(f"expected exactly one witness facts record for {channel!r}")
        return matches[0]


def capture_integrity_problems(
    *,
    assurance: CaptureAssurance,
    admitted: bool,
    armed_interface_index: int | None,
    closing_interface_index: int | None,
    capture_drops: int | None,
) -> tuple[str, ...]:
    """Fail closed on any capture-integrity uncertainty."""

    problems = list(assurance.problems())
    if not admitted:
        problems.append("attempt-never-admitted")
    if armed_interface_index is None or closing_interface_index != armed_interface_index:
        problems.append("interface-identity-drift")
    if capture_drops is None:
        problems.append("capture-drop-statistics-unknown")
    elif capture_drops != 0:
        problems.append(f"capture-drops={capture_drops}")
    return tuple(dict.fromkeys(problems))


def normalize_channel(
    scope: WitnessScope,
    observations: Iterable[TcpSynObservation],
    *,
    global_validity_problems: tuple[str, ...] = (),
) -> InitiationFacts:
    observations_tuple = tuple(observations)
    problems = list(global_validity_problems)
    unique: dict[tuple[object, ...], TcpSynObservation] = {}
    for observation in observations_tuple:
        if observation.channel != scope.channel:
            raise ValueError("observation channel does not match normalization scope")
        if observation.packet_type != _PACKET_OUTGOING:
            problems.append("ambiguous-packet-direction")
        unique.setdefault(observation.initiation_key, observation)

    expected = sum(_matches_endpoint(item, scope.expected_target) for item in unique.values())
    alternate = len(unique) - expected
    return InitiationFacts(
        channel=scope.channel,
        total_initiations=len(unique),
        expected_target_initiations=expected,
        alternate_target_initiations=alternate,
        raw_syn_packets=len(observations_tuple),
        retransmitted_syn_packets=max(0, len(observations_tuple) - len(unique)),
        validity_problems=tuple(dict.fromkeys(problems)),
    )


def serialize_raw_witness(
    *,
    attempt_id: str,
    records: tuple[RawFrameRecord, ...],
    observations: tuple[TcpSynObservation, ...],
    validity_problems: tuple[str, ...],
    capture_packets: int | None,
    capture_drops: int | None,
) -> bytes:
    document = {
        "format": "avp-project-network-transport-witness-v0.1",
        "attemptId": attempt_id,
        "capturePackets": capture_packets,
        "captureDrops": capture_drops,
        "validityProblems": list(validity_problems),
        "rawFrames": [
            {
                "interface": item.interface_name,
                "interfaceIndex": item.interface_index,
                "monotonicNs": item.monotonic_ns,
                "packetType": item.packet_type,
                "frameB64": base64.b64encode(item.frame).decode("ascii"),
                "frameSha256": hashlib.sha256(item.frame).hexdigest(),
            }
            for item in records
        ],
        "normalizationInputs": [
            {
                "channel": item.channel,
                "roleId": item.role_id,
                "interface": item.interface_name,
                "interfaceIndex": item.interface_index,
                "monotonicNs": item.monotonic_ns,
                "family": item.family,
                "sourceAddress": item.source_address,
                "sourcePort": item.source_port,
                "destinationAddress": item.destination_address,
                "destinationPort": item.destination_port,
                "sequence": item.sequence,
                "packetType": item.packet_type,
                "rawFrameSha256": item.raw_frame_sha256,
            }
            for item in observations
        ],
    }
    return json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")


def synthetic_observation(
    scope: WitnessScope,
    *,
    attempt_id: str,
    source_port: int,
    destination_address: str | None = None,
    destination_port: int | None = None,
    sequence: int = 1,
    monotonic_ns: int = 1,
    packet_type: int = _PACKET_OUTGOING,
) -> TcpSynObservation:
    source_address = scope.source_addresses[0]
    target_address = destination_address or scope.expected_target.address
    target_port = destination_port or scope.expected_target.port
    frame = build_synthetic_syn_frame(
        source_address=source_address,
        destination_address=target_address,
        source_port=source_port,
        destination_port=target_port,
        sequence=sequence,
    )
    parsed = parse_initial_syn(frame)
    if parsed is None:
        raise AssertionError("synthetic SYN frame did not parse")
    return TcpSynObservation(
        channel=scope.channel,
        role_id=scope.role_id,
        attempt_id=attempt_id,
        interface_name="synthetic0",
        interface_index=1,
        monotonic_ns=monotonic_ns,
        family=parsed.family,
        source_address=parsed.source_address,
        source_port=parsed.source_port,
        destination_address=parsed.destination_address,
        destination_port=parsed.destination_port,
        sequence=parsed.sequence,
        packet_type=packet_type,
        raw_frame_sha256=hashlib.sha256(frame).hexdigest(),
    )


def scope_for_source(scopes: tuple[WitnessScope, ...], address: str) -> WitnessScope | None:
    matches = [scope for scope in scopes if scope.matches_source(address)]
    if len(matches) > 1:
        raise PacketParseError("role-source-address-maps-to-multiple-witness-scopes")
    return matches[0] if matches else None


def _matches_endpoint(observation: TcpSynObservation, endpoint: MaterializedEndpoint) -> bool:
    return (
        observation.family == endpoint.family
        and observation.destination_address == endpoint.address
        and observation.destination_port == endpoint.port
    )
