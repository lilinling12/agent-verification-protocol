"""Process entry points used by the concrete TEL-002 Docker lab roles.

These commands execute the already-reviewed fixture/client/witness responsibilities
inside isolated container network namespaces. They are test infrastructure only;
they do not expose a public AVP API or provider-neutral extension contract.
"""

from __future__ import annotations

import argparse
import base64
import fcntl
import json
import socket
import struct
import sys
from typing import TextIO

from .attempt_client import ExchangeObservation, execute_exact_exchange
from .evidence_core import AttemptMaterial, MaterializedEndpoint
from .fixture import ExactByteFixture, FixtureExchangeEvent
from .witness import LinuxSynWitness
from .witness_evidence import CaptureAssurance, WitnessScope

_SIOCGIFADDR = 0x8915


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AVP TEL-002 concrete lab role worker")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("fixture", help="run a controlled exact-byte fixture")
    subparsers.add_parser("exchange", help="execute one certified Subject exchange")
    subparsers.add_parser("witness", help="run one armed AF_PACKET witness window")
    subparsers.add_parser("inventory", help="report network namespace IPv4 interface inventory")
    args = parser.parse_args(argv)

    if args.command == "fixture":
        return _fixture_worker(sys.stdin, sys.stdout)
    if args.command == "exchange":
        return _exchange_worker(sys.stdin, sys.stdout)
    if args.command == "witness":
        return _witness_worker(sys.stdin, sys.stdout)
    if args.command == "inventory":
        return _inventory_worker(sys.stdout)
    raise AssertionError(f"unhandled TEL-002 worker command: {args.command}")


def _fixture_worker(stdin: TextIO, stdout: TextIO) -> int:
    configuration = _read_document(stdin)
    endpoint = _endpoint_from_document(configuration["endpoint"])
    hygiene_timeout_s = float(configuration.get("hygieneTimeoutS", 2.0))
    fixture = ExactByteFixture(
        family=endpoint.family,
        address=endpoint.address,
        role=endpoint.role,
        bind_port=endpoint.port,
        hygiene_timeout_s=hygiene_timeout_s,
    )
    fixture.start()
    try:
        if fixture.endpoint != endpoint:
            raise RuntimeError("fixture bound endpoint does not match materialized endpoint")
        _write_document(stdout, {"event": "ready", "endpoint": _endpoint_document(endpoint)})
        for line in stdin:
            if not line.strip():
                continue
            command = json.loads(line)
            operation = command.get("op")
            try:
                if operation == "arm":
                    fixture.arm(_attempt_from_document(command["attempt"]))
                    response: dict[str, object] = {"ok": True, "op": "arm"}
                elif operation == "disarm":
                    fixture.disarm(str(command["attemptId"]))
                    response = {"ok": True, "op": "disarm"}
                elif operation == "event":
                    event = fixture.wait_for_event(
                        str(command["attemptId"]),
                        timeout_s=float(command["timeoutS"]),
                    )
                    response = {"ok": True, "op": "event", "event": _fixture_event_document(event)}
                elif operation == "stop":
                    _write_document(stdout, {"ok": True, "op": "stop"})
                    return 0
                else:
                    response = {"ok": False, "error": f"unsupported fixture operation: {operation!r}"}
            except BaseException as exc:
                response = {"ok": False, "error": f"{type(exc).__name__}:{exc}"}
            _write_document(stdout, response)
    finally:
        fixture.stop()
    return 0


def _exchange_worker(stdin: TextIO, stdout: TextIO) -> int:
    document = _read_document(stdin)
    endpoint = _endpoint_from_document(document["endpoint"])
    attempt = _attempt_from_document(document["attempt"])
    observation = execute_exact_exchange(
        endpoint,
        attempt,
        observation_budget_ns=int(document["observationBudgetNs"]),
    )
    if bool(document.get("extraConnect", False)):
        _emit_extra_connect(endpoint)
    _write_document(stdout, _exchange_observation_document(observation))
    return 0


def _witness_worker(stdin: TextIO, stdout: TextIO) -> int:
    document = _read_document(stdin)
    source_address = str(document["sourceAddress"])
    expected_target = _endpoint_from_document(document["expectedTarget"])
    interface_name = _interface_for_ipv4(source_address)
    assurance_document = document["assurance"]
    assurance = CaptureAssurance(
        egress_coverage_verified=bool(assurance_document["egressCoverageVerified"]),
        directionality_verified=bool(assurance_document["directionalityVerified"]),
        offload_normalization_verified=bool(assurance_document["offloadNormalizationVerified"]),
        pre_syn_connect_gap_closed=bool(assurance_document["preSynConnectGapClosed"]),
    )
    scope = WitnessScope(
        channel=str(document["channel"]),
        role_id=str(document["roleId"]),
        source_addresses=(source_address,),
        expected_target=expected_target,
    )
    attempt_id = str(document["attemptId"])
    witness = LinuxSynWitness(
        interface_name=interface_name,
        scopes=(scope,),
        assurance=assurance,
    )
    witness.arm(attempt_id)
    witness.admit(attempt_id)
    _write_document(
        stdout,
        {
            "event": "ready",
            "attemptId": attempt_id,
            "interface": interface_name,
            "sourceAddress": source_address,
        },
    )
    command = _read_document(stdin)
    if command.get("op") != "close" or command.get("attemptId") != attempt_id:
        raise RuntimeError("witness worker requires exact close command for armed attempt")
    result = witness.close(attempt_id)
    _write_document(
        stdout,
        {
            "event": "result",
            "attemptId": result.attempt_id,
            "channelFacts": [
                {
                    "channel": facts.channel,
                    "totalInitiations": facts.total_initiations,
                    "expectedTargetInitiations": facts.expected_target_initiations,
                    "alternateTargetInitiations": facts.alternate_target_initiations,
                    "rawSynPackets": facts.raw_syn_packets,
                    "retransmittedSynPackets": facts.retransmitted_syn_packets,
                    "validityProblems": list(facts.validity_problems),
                }
                for facts in result.channel_facts
            ],
            "validityProblems": list(result.validity_problems),
            "rawArtifactB64": base64.b64encode(result.raw_artifact_bytes).decode("ascii"),
            "capturePackets": result.capture_packets,
            "captureDrops": result.capture_drops,
        },
    )
    return 0


def _inventory_worker(stdout: TextIO) -> int:
    addresses = []
    for interface_index, interface_name in socket.if_nameindex():
        address = _ipv4_for_interface(interface_name)
        if address is not None:
            addresses.append(
                {
                    "interface": interface_name,
                    "interfaceIndex": interface_index,
                    "ipv4Address": address,
                    "loopback": address.startswith("127."),
                }
            )
    _write_document(stdout, {"interfaces": addresses})
    return 0


def _interface_for_ipv4(address: str) -> str:
    matches = [
        interface_name
        for _index, interface_name in socket.if_nameindex()
        if _ipv4_for_interface(interface_name) == address
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one interface for role source address {address!r}, found {matches!r}"
        )
    return matches[0]


def _ipv4_for_interface(interface_name: str) -> str | None:
    control = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        request = struct.pack("256s", interface_name.encode("utf-8")[:15])
        try:
            response = fcntl.ioctl(control.fileno(), _SIOCGIFADDR, request)
        except OSError:
            return None
        return socket.inet_ntoa(response[20:24])
    finally:
        control.close()


def _emit_extra_connect(endpoint: MaterializedEndpoint) -> None:
    family = socket.AF_INET if endpoint.family == "ipv4" else socket.AF_INET6
    sock = socket.socket(family, socket.SOCK_STREAM)
    try:
        sock.setblocking(False)
        address: tuple[object, ...]
        if endpoint.family == "ipv4":
            address = (endpoint.address, endpoint.port)
        else:
            address = (endpoint.address, endpoint.port, 0, 0)
        sock.connect_ex(address)
    finally:
        sock.close()


def _attempt_document(attempt: AttemptMaterial) -> dict[str, object]:
    return {
        "runId": attempt.run_id,
        "phaseId": attempt.phase_id,
        "ordinal": attempt.ordinal,
        "pathId": attempt.path_id,
        "attemptId": attempt.attempt_id,
        "challengeB64": base64.b64encode(attempt.challenge).decode("ascii"),
        "challengeSha256": attempt.challenge_sha256,
        "requestB64": base64.b64encode(attempt.request_bytes).decode("ascii"),
        "expectedResponseB64": base64.b64encode(attempt.expected_response_bytes).decode("ascii"),
        "requestSha256": attempt.request_sha256,
        "responseSha256": attempt.response_sha256,
    }


def _attempt_from_document(document: object) -> AttemptMaterial:
    if not isinstance(document, dict):
        raise ValueError("attempt document must be an object")
    return AttemptMaterial(
        run_id=str(document["runId"]),
        phase_id=str(document["phaseId"]),
        ordinal=int(document["ordinal"]),
        path_id=str(document["pathId"]),
        attempt_id=str(document["attemptId"]),
        challenge=base64.b64decode(str(document["challengeB64"]), validate=True),
        challenge_sha256=str(document["challengeSha256"]),
        request_bytes=base64.b64decode(str(document["requestB64"]), validate=True),
        expected_response_bytes=base64.b64decode(
            str(document["expectedResponseB64"]), validate=True
        ),
        request_sha256=str(document["requestSha256"]),
        response_sha256=str(document["responseSha256"]),
    )


def _endpoint_document(endpoint: MaterializedEndpoint) -> dict[str, object]:
    return {
        "family": endpoint.family,
        "address": endpoint.address,
        "port": endpoint.port,
        "role": endpoint.role,
    }


def _endpoint_from_document(document: object) -> MaterializedEndpoint:
    if not isinstance(document, dict):
        raise ValueError("endpoint document must be an object")
    return MaterializedEndpoint(
        family=str(document["family"]),
        address=str(document["address"]),
        port=int(document["port"]),
        role=str(document["role"]),
    )


def _exchange_observation_document(observation: ExchangeObservation) -> dict[str, object]:
    return {
        "attemptId": observation.attempt_id,
        "completed": observation.completed,
        "mismatchObserved": observation.mismatch_observed,
        "observationBudgetExpired": observation.observation_budget_expired,
        "elapsedNs": observation.elapsed_ns,
        "responseSize": observation.response_size,
        "responseSha256": observation.response_sha256,
        "nativeError": observation.native_error,
    }


def _fixture_event_document(event: FixtureExchangeEvent) -> dict[str, object]:
    return {
        "ordinal": event.ordinal,
        "attemptId": event.attempt_id,
        "peer": event.peer,
        "receivedSize": event.received_size,
        "receivedSha256": event.received_sha256,
        "requestValid": event.request_valid,
        "responseEmitted": event.response_emitted,
        "problem": event.problem,
    }


def _read_document(stream: TextIO) -> dict[str, object]:
    line = stream.readline()
    if not line:
        raise EOFError("TEL-002 worker input closed before a JSON document was received")
    value = json.loads(line)
    if not isinstance(value, dict):
        raise ValueError("TEL-002 worker command must be a JSON object")
    return value


def _write_document(stream: TextIO, document: dict[str, object]) -> None:
    stream.write(json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n")
    stream.flush()


if __name__ == "__main__":
    raise SystemExit(main())
