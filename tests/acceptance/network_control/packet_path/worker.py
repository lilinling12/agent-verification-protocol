"""Concrete PTL-001 process roles for the Linux packet-path evidence lab.

The worker is intentionally mechanism-local. It exposes only the process
boundaries required by the reviewed three-namespace lab: exact-byte fixtures,
one certified exchange, one optional deliberate fallback initiation, a one-shot
Subject-egress witness, read-only interface inventory, and a read-only Subject
security probe. It does not own fault control, lifecycle ordering, qualification,
or portable C1-C12 assessment.
"""

from __future__ import annotations

import argparse
import base64
import fcntl
import hashlib
import json
import math
import os
import socket
import struct
import sys
from typing import TextIO

from ..attempt_client import ExchangeObservation, execute_exact_exchange
from ..evidence_core import AttemptMaterial, EvidenceMaterializationError, MaterializedEndpoint
from ..fixture import ExactByteFixture, FixtureExchangeEvent
from ..witness import LinuxSynWitness
from ..witness_evidence import CaptureAssurance, WitnessScope

_SIOCGIFADDR = 0x8915
_MAX_JSON_LINE_CHARS = 1_048_576
_ALLOWED_WITNESS_ROLES = frozenset({"subject", "privileged-probe"})


def main(argv: list[str] | None = None) -> int:
    """Run exactly one concrete packet-path role."""

    parser = argparse.ArgumentParser(description="AVP PTL-001 packet-path role worker")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("fixture", help="run one exact-byte fixture endpoint")
    subparsers.add_parser("exchange", help="run one certified exact-byte Subject/probe exchange")
    subparsers.add_parser("witness", help="run one armed Subject-egress SYN witness")
    subparsers.add_parser("inventory", help="report read-only namespace interface inventory")
    subparsers.add_parser("security-probe", help="report read-only process authority facts")
    args = parser.parse_args(argv)

    if args.command == "fixture":
        return _fixture_worker(sys.stdin, sys.stdout)
    if args.command == "exchange":
        return _exchange_worker(sys.stdin, sys.stdout)
    if args.command == "witness":
        return _witness_worker(sys.stdin, sys.stdout)
    if args.command == "inventory":
        return _inventory_worker(sys.stdout)
    if args.command == "security-probe":
        return _security_probe_worker(sys.stdin, sys.stdout)
    raise AssertionError(f"unhandled PTL-001 packet-path worker command: {args.command}")


def _fixture_worker(stdin: TextIO, stdout: TextIO) -> int:
    configuration = _read_document(stdin)
    _require_shape(configuration, required={"endpoint"}, optional={"hygieneTimeoutS"})
    endpoint = _endpoint_from_document(configuration["endpoint"])
    hygiene_timeout_s = _positive_float(
        configuration.get("hygieneTimeoutS", 2.0),
        name="hygieneTimeoutS",
    )
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
            raise RuntimeError("packet-path fixture bound endpoint does not match materialized endpoint")
        _write_document(stdout, {"event": "ready", "endpoint": _endpoint_document(endpoint)})

        while True:
            command = _read_optional_document(stdin)
            if command is None:
                raise EOFError("packet-path fixture control stream closed before stop")
            operation = command.get("op")
            try:
                if operation == "arm":
                    _require_shape(command, required={"op", "attempt"})
                    fixture.arm(_attempt_from_document(command["attempt"]))
                    response: dict[str, object] = {"ok": True, "op": "arm"}
                elif operation == "disarm":
                    _require_shape(command, required={"op", "attemptId"})
                    fixture.disarm(_non_empty_string(command["attemptId"], name="attemptId"))
                    response = {"ok": True, "op": "disarm"}
                elif operation == "event":
                    _require_shape(command, required={"op", "attemptId", "timeoutS"})
                    event = fixture.wait_for_event(
                        _non_empty_string(command["attemptId"], name="attemptId"),
                        timeout_s=_positive_float(command["timeoutS"], name="timeoutS"),
                    )
                    response = {
                        "ok": True,
                        "op": "event",
                        "event": _fixture_event_document(event),
                    }
                elif operation == "stop":
                    _require_shape(command, required={"op"})
                    _write_document(stdout, {"ok": True, "op": "stop"})
                    return 0
                else:
                    response = {
                        "ok": False,
                        "error": f"unsupported packet-path fixture operation: {operation!r}",
                    }
            except BaseException as exc:
                response = {"ok": False, "error": f"{type(exc).__name__}:{exc}"}
            _write_document(stdout, response)
    finally:
        fixture.stop()


def _exchange_worker(stdin: TextIO, stdout: TextIO) -> int:
    document = _read_document(stdin)
    _require_shape(
        document,
        required={"endpoint", "attempt", "observationBudgetNs"},
        optional={"additionalConnectTarget"},
    )
    endpoint = _endpoint_from_document(document["endpoint"])
    attempt = _attempt_from_document(document["attempt"])
    observation_budget_ns = _positive_int(
        document["observationBudgetNs"],
        name="observationBudgetNs",
    )

    additional_target: MaterializedEndpoint | None = None
    if "additionalConnectTarget" in document:
        additional_target = _endpoint_from_document(document["additionalConnectTarget"])
        if _same_socket(endpoint, additional_target):
            raise EvidenceMaterializationError(
                "packet-path additional connect target must be a distinct literal socket"
            )

    observation = execute_exact_exchange(
        endpoint,
        attempt,
        observation_budget_ns=observation_budget_ns,
    )
    additional_native_result: int | None = None
    if additional_target is not None:
        # This is a single reviewed negative hook, not retry/fallback behavior in
        # the certified exact-byte client. The Subject-egress witness remains the
        # authority for the resulting initiation cardinality.
        additional_native_result = _emit_additional_connect(additional_target)

    response = _exchange_observation_document(observation)
    response["additionalConnectAttempted"] = additional_target is not None
    response["additionalConnectNativeResult"] = additional_native_result
    _write_document(stdout, response)
    return 0


def _witness_worker(stdin: TextIO, stdout: TextIO) -> int:
    document = _read_document(stdin)
    _require_shape(
        document,
        required={
            "interfaceName",
            "sourceAddress",
            "expectedTarget",
            "channel",
            "roleId",
            "attemptId",
            "assurance",
        },
    )
    interface_name = _non_empty_string(document["interfaceName"], name="interfaceName")
    source_address = _non_empty_string(document["sourceAddress"], name="sourceAddress")
    expected_target = _endpoint_from_document(document["expectedTarget"])
    channel = _non_empty_string(document["channel"], name="channel")
    role_id = _non_empty_string(document["roleId"], name="roleId")
    if role_id not in _ALLOWED_WITNESS_ROLES:
        raise EvidenceMaterializationError("packet-path witness role is outside reviewed authority set")
    attempt_id = _non_empty_string(document["attemptId"], name="attemptId")
    assurance = _assurance_from_document(document["assurance"])

    interface_index = _assert_interface_ipv4(interface_name, source_address)
    scope = WitnessScope(
        channel=channel,
        role_id=role_id,
        source_addresses=(source_address,),
        expected_target=expected_target,
    )
    witness = LinuxSynWitness(
        interface_name=interface_name,
        scopes=(scope,),
        assurance=assurance,
    )

    closed = False
    witness.arm(attempt_id)
    witness.admit(attempt_id)
    try:
        _write_document(
            stdout,
            {
                "event": "ready",
                "attemptId": attempt_id,
                "interface": interface_name,
                "interfaceIndex": interface_index,
                "sourceAddress": source_address,
            },
        )
        command = _read_document(stdin)
        _require_shape(command, required={"op", "attemptId"})
        if command.get("op") != "close" or command.get("attemptId") != attempt_id:
            raise RuntimeError("packet-path witness requires exact close command for armed attempt")
        result = witness.close(attempt_id)
        closed = True
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
    finally:
        if not closed:
            try:
                witness.close(attempt_id)
            except BaseException:
                pass


def _inventory_worker(stdout: TextIO) -> int:
    interfaces: list[dict[str, object]] = []
    for interface_index, interface_name in socket.if_nameindex():
        address = _ipv4_for_interface(interface_name)
        interfaces.append(
            {
                "interface": interface_name,
                "interfaceIndex": interface_index,
                "ipv4Address": address,
                "loopback": address is not None and address.startswith("127."),
            }
        )
    _write_document(
        stdout,
        {
            "netNamespace": _net_namespace_identity(),
            "interfaces": interfaces,
        },
    )
    return 0


def _security_probe_worker(stdin: TextIO, stdout: TextIO) -> int:
    document = _read_document(stdin)
    _require_shape(document, required=set(), optional={"environmentKeys"})
    environment_keys = _environment_keys(document.get("environmentKeys", []))
    status = _process_status()

    _write_document(
        stdout,
        {
            "uid": os.getuid(),
            "euid": os.geteuid(),
            "gid": os.getgid(),
            "egid": os.getegid(),
            "supplementaryGroups": list(os.getgroups()),
            "noNewPrivs": _status_int(status, "NoNewPrivs"),
            "capabilities": {
                "inheritable": _status_hex(status, "CapInh"),
                "permitted": _status_hex(status, "CapPrm"),
                "effective": _status_hex(status, "CapEff"),
                "bounding": _status_hex(status, "CapBnd"),
                "ambient": _status_hex(status, "CapAmb"),
            },
            "netNamespace": _net_namespace_identity(),
            # Only key presence is projected. Environment values may contain
            # evaluator-private material and are never serialized by this worker.
            "environmentPresence": {key: key in os.environ for key in environment_keys},
        },
    )
    return 0


def _emit_additional_connect(endpoint: MaterializedEndpoint) -> int:
    """Emit exactly one additional TCP initiation for the reviewed negative hook."""

    family = socket.AF_INET if endpoint.family == "ipv4" else socket.AF_INET6
    sock = socket.socket(family, socket.SOCK_STREAM)
    try:
        sock.setblocking(False)
        address: tuple[object, ...]
        if endpoint.family == "ipv4":
            address = (endpoint.address, endpoint.port)
        else:
            address = (endpoint.address, endpoint.port, 0, 0)
        return int(sock.connect_ex(address))
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
        raise EvidenceMaterializationError("packet-path attempt document must be an object")
    _require_shape(
        document,
        required={
            "runId",
            "phaseId",
            "ordinal",
            "pathId",
            "attemptId",
            "challengeB64",
            "challengeSha256",
            "requestB64",
            "expectedResponseB64",
            "requestSha256",
            "responseSha256",
        },
    )
    ordinal = document["ordinal"]
    if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 0:
        raise EvidenceMaterializationError("packet-path attempt ordinal must be non-negative integer")

    attempt = AttemptMaterial(
        run_id=_non_empty_string(document["runId"], name="runId"),
        phase_id=_non_empty_string(document["phaseId"], name="phaseId"),
        ordinal=ordinal,
        path_id=_non_empty_string(document["pathId"], name="pathId"),
        attempt_id=_non_empty_string(document["attemptId"], name="attemptId"),
        challenge=_decode_b64(document["challengeB64"], name="challengeB64"),
        challenge_sha256=_digest_string(document["challengeSha256"], name="challengeSha256"),
        request_bytes=_decode_b64(document["requestB64"], name="requestB64"),
        expected_response_bytes=_decode_b64(
            document["expectedResponseB64"],
            name="expectedResponseB64",
        ),
        request_sha256=_digest_string(document["requestSha256"], name="requestSha256"),
        response_sha256=_digest_string(document["responseSha256"], name="responseSha256"),
    )
    _validate_attempt_integrity(attempt)
    return attempt


def _validate_attempt_integrity(attempt: AttemptMaterial) -> None:
    if not attempt.challenge or not attempt.request_bytes or not attempt.expected_response_bytes:
        raise EvidenceMaterializationError("packet-path attempt exact material must be non-empty")
    expected = (
        (attempt.challenge, attempt.challenge_sha256, "challenge"),
        (attempt.request_bytes, attempt.request_sha256, "request"),
        (attempt.expected_response_bytes, attempt.response_sha256, "response"),
    )
    for payload, declared, label in expected:
        actual = hashlib.sha256(payload).hexdigest()
        if actual != declared:
            raise EvidenceMaterializationError(
                f"packet-path attempt {label} digest does not match exact bytes"
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
        raise EvidenceMaterializationError("packet-path endpoint document must be an object")
    _require_shape(document, required={"family", "address", "port", "role"})
    family = _non_empty_string(document["family"], name="family")
    address = _non_empty_string(document["address"], name="address")
    role = _non_empty_string(document["role"], name="role")
    port = document["port"]
    if isinstance(port, bool) or not isinstance(port, int):
        raise EvidenceMaterializationError("packet-path endpoint port must be an integer")
    return MaterializedEndpoint(family=family, address=address, port=port, role=role)


def _assurance_from_document(document: object) -> CaptureAssurance:
    if not isinstance(document, dict):
        raise EvidenceMaterializationError("packet-path assurance document must be an object")
    _require_shape(
        document,
        required={
            "egressCoverageVerified",
            "directionalityVerified",
            "offloadNormalizationVerified",
            "preSynConnectGapClosed",
        },
    )
    values: dict[str, bool] = {}
    for key in (
        "egressCoverageVerified",
        "directionalityVerified",
        "offloadNormalizationVerified",
        "preSynConnectGapClosed",
    ):
        value = document[key]
        if not isinstance(value, bool):
            raise EvidenceMaterializationError(f"packet-path assurance {key} must be boolean")
        values[key] = value
    return CaptureAssurance(
        egress_coverage_verified=values["egressCoverageVerified"],
        directionality_verified=values["directionalityVerified"],
        offload_normalization_verified=values["offloadNormalizationVerified"],
        pre_syn_connect_gap_closed=values["preSynConnectGapClosed"],
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


def _assert_interface_ipv4(interface_name: str, source_address: str) -> int:
    matches = [
        (interface_index, name)
        for interface_index, name in socket.if_nameindex()
        if name == interface_name and _ipv4_for_interface(name) == source_address
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "packet-path witness requires exactly one interface/source-address binding; "
            f"found {matches!r}"
        )
    return int(matches[0][0])


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


def _process_status() -> dict[str, str]:
    status: dict[str, str] = {}
    try:
        with open("/proc/self/status", "r", encoding="utf-8") as handle:
            for line in handle:
                key, separator, value = line.partition(":")
                if separator:
                    status[key] = value.strip()
    except OSError as exc:
        raise RuntimeError("packet-path security probe cannot read /proc/self/status") from exc
    return status


def _status_int(status: dict[str, str], key: str) -> int:
    raw = status.get(key)
    if raw is None:
        raise RuntimeError(f"packet-path security probe status field {key!r} is missing")
    try:
        return int(raw, 10)
    except ValueError as exc:
        raise RuntimeError(f"packet-path security probe status field {key!r} is invalid") from exc


def _status_hex(status: dict[str, str], key: str) -> str:
    raw = status.get(key)
    if raw is None or not raw or any(character not in "0123456789abcdefABCDEF" for character in raw):
        raise RuntimeError(f"packet-path security probe capability field {key!r} is invalid")
    return raw.lower()


def _net_namespace_identity() -> str:
    try:
        identity = os.readlink("/proc/self/ns/net")
    except OSError as exc:
        raise RuntimeError("packet-path worker cannot read network namespace identity") from exc
    if not identity.startswith("net:[") or not identity.endswith("]"):
        raise RuntimeError("packet-path worker network namespace identity is malformed")
    return identity


def _environment_keys(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > 64:
        raise EvidenceMaterializationError("packet-path environmentKeys must be a list of at most 64 names")
    keys: list[str] = []
    for item in value:
        key = _non_empty_string(item, name="environment key")
        if len(key) > 128 or "=" in key or "\x00" in key:
            raise EvidenceMaterializationError("packet-path environment key has invalid shape")
        keys.append(key)
    if len(set(keys)) != len(keys):
        raise EvidenceMaterializationError("packet-path environment keys must be unique")
    return tuple(keys)


def _read_document(stream: TextIO) -> dict[str, object]:
    document = _read_optional_document(stream)
    if document is None:
        raise EOFError("packet-path worker input closed before a JSON document was received")
    return document


def _read_optional_document(stream: TextIO) -> dict[str, object] | None:
    line = stream.readline(_MAX_JSON_LINE_CHARS + 1)
    if line == "":
        return None
    if len(line) > _MAX_JSON_LINE_CHARS:
        raise EvidenceMaterializationError("packet-path worker JSON command exceeds size limit")
    if not line.strip():
        raise EvidenceMaterializationError("packet-path worker JSON command must not be blank")
    try:
        value = json.loads(line)
    except json.JSONDecodeError as exc:
        raise EvidenceMaterializationError("packet-path worker command must be valid JSON") from exc
    if not isinstance(value, dict):
        raise EvidenceMaterializationError("packet-path worker command must be a JSON object")
    return value


def _write_document(stream: TextIO, document: dict[str, object]) -> None:
    stream.write(json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n")
    stream.flush()


def _require_shape(
    document: dict[str, object],
    *,
    required: set[str],
    optional: set[str] | None = None,
) -> None:
    optional_keys = set() if optional is None else optional
    keys = set(document)
    missing = required - keys
    unexpected = keys - required - optional_keys
    if missing:
        raise EvidenceMaterializationError(
            f"packet-path worker document missing field: {sorted(missing)[0]}"
        )
    if unexpected:
        raise EvidenceMaterializationError(
            f"packet-path worker document has unexpected field: {sorted(unexpected)[0]}"
        )


def _non_empty_string(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise EvidenceMaterializationError(f"packet-path {name} must be a non-empty string")
    return value


def _digest_string(value: object, *, name: str) -> str:
    digest = _non_empty_string(value, name=name)
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise EvidenceMaterializationError(f"packet-path {name} must be 64 lowercase hex characters")
    return digest


def _decode_b64(value: object, *, name: str) -> bytes:
    encoded = _non_empty_string(value, name=name)
    try:
        return base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise EvidenceMaterializationError(f"packet-path {name} must be canonical base64 bytes") from exc


def _positive_int(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise EvidenceMaterializationError(f"packet-path {name} must be a positive integer")
    return value


def _positive_float(value: object, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvidenceMaterializationError(f"packet-path {name} must be positive and finite")
    converted = float(value)
    if not math.isfinite(converted) or converted <= 0:
        raise EvidenceMaterializationError(f"packet-path {name} must be positive and finite")
    return converted


def _same_socket(first: MaterializedEndpoint, second: MaterializedEndpoint) -> bool:
    return (
        first.family == second.family
        and first.address == second.address
        and first.port == second.port
    )


if __name__ == "__main__":
    raise SystemExit(main())
