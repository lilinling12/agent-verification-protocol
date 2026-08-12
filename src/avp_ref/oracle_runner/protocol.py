"""Strict single-frame JSON protocol shared with isolated Oracle workers."""

from __future__ import annotations

import base64
import binascii
import json
from typing import Mapping

from avp_ref.artifacts import sha256_digest
from avp_ref.models import Validity, VerificationResult

from .errors import OracleProtocolError
from .models import OracleEvaluationContext, OracleEvaluationOutput, OracleEvidencePayload, OraclePackage, OracleRequest, ProjectionSnapshot

PROTOCOL_VERSION = "avp.oracle/v2"


def _json_bytes(value: Mapping[str, object]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def encode_request(request: OracleRequest, *, max_bytes: int) -> bytes:
    frame = _json_bytes({"protocol": PROTOCOL_VERSION, **request.to_dict()})
    if len(frame) > max_bytes:
        raise OracleProtocolError("Oracle request exceeds configured frame limit")
    return frame


def decode_request(frame: bytes, *, max_bytes: int) -> OracleRequest:
    raw = _decode_single_frame(frame, max_bytes=max_bytes)
    if raw.get("protocol") != PROTOCOL_VERSION:
        raise OracleProtocolError("unsupported Oracle protocol version")
    package_raw = _mapping(raw.get("package"), "package")
    context_raw = _mapping(raw.get("context"), "context")
    package = OraclePackage(
        oracle_id=_string(package_raw.get("oracle_id"), "package.oracle_id"),
        version=_string(package_raw.get("version"), "package.version"),
        entrypoint=_string(package_raw.get("entrypoint"), "package.entrypoint"),
        code_digest=_string(package_raw.get("code_digest"), "package.code_digest"),
        projections=tuple(_string_list(package_raw.get("projections"), "package.projections")),
        input_pointers={str(k): _string(v, f"package.input_pointers.{k}") for k, v in _mapping(package_raw.get("input_pointers", {}), "package.input_pointers").items()},
    )
    projections_raw = _mapping(context_raw.get("projections"), "context.projections")
    projections: dict[str, ProjectionSnapshot] = {}
    for key, value in projections_raw.items():
        item = _mapping(value, f"context.projections.{key}")
        projection_id = _string(item.get("projection_id"), f"context.projections.{key}.projection_id")
        if projection_id != key:
            raise OracleProtocolError("projection map key and projection_id differ")
        projections[key] = ProjectionSnapshot(projection_id, item.get("data"), _string(item.get("state_digest"), "projection.state_digest"))
    context = OracleEvaluationContext(
        episode_id=_string(context_raw.get("episode_id"), "context.episode_id"),
        scenario_instance_digest=_string(context_raw.get("scenario_instance_digest"), "context.scenario_instance_digest"),
        manifest_digest=_string(context_raw.get("manifest_digest"), "context.manifest_digest"),
        inputs=_mapping(context_raw.get("inputs", {}), "context.inputs"),
        projections=projections,
    )
    return OracleRequest(_string(raw.get("request_id"), "request_id"), package, context)


def encode_success(request_id: str, output: OracleEvaluationOutput, *, max_bytes: int) -> bytes:
    evidence_ids: set[str] = set()
    evidence_payload: list[dict[str, object]] = []
    for item in output.evidence:
        if item.evidence_id in evidence_ids:
            raise OracleProtocolError(f"duplicate Oracle evidence id: {item.evidence_id}")
        if sha256_digest(item.content) != item.digest:
            raise OracleProtocolError(f"Oracle evidence digest mismatch: {item.evidence_id}")
        evidence_ids.add(item.evidence_id)
        encoded: dict[str, object] = {
            "evidence_id": item.evidence_id,
            "type": item.evidence_type,
            "media_type": item.media_type,
            "digest": item.digest,
            "content_base64": base64.b64encode(item.content).decode("ascii"),
            "classification": item.classification,
        }
        if item.producer is not None:
            encoded["producer"] = item.producer
        evidence_payload.append(encoded)
    results_payload: list[dict[str, object]] = []
    for item in output.results:
        missing = set(item.evidence_ids) - evidence_ids
        if missing:
            raise OracleProtocolError(f"verification result references missing evidence: {sorted(missing)}")
        results_payload.append({"claim_id": item.claim_id, "dimension": item.dimension, "verdict": item.verdict, "severity": item.severity, "method": item.method, "evaluator_version": item.evaluator_version, "evidence_ids": list(item.evidence_ids), "confidence": item.confidence, "validity": item.validity.value})
    frame = _json_bytes({"protocol": PROTOCOL_VERSION, "request_id": request_id, "status": "SUCCESS", "results": results_payload, "evidence": evidence_payload})
    if len(frame) > max_bytes:
        raise OracleProtocolError("Oracle response exceeds configured frame limit")
    return frame


def decode_success(frame: bytes, *, expected_request_id: str, max_bytes: int) -> OracleEvaluationOutput:
    raw = _decode_single_frame(frame, max_bytes=max_bytes)
    if raw.get("protocol") != PROTOCOL_VERSION or raw.get("request_id") != expected_request_id or raw.get("status") != "SUCCESS":
        raise OracleProtocolError("Oracle response envelope does not match request")
    evidence_raw = raw.get("evidence")
    results_raw = raw.get("results")
    if not isinstance(evidence_raw, list) or not isinstance(results_raw, list):
        raise OracleProtocolError("Oracle response results/evidence must be arrays")
    evidence: list[OracleEvidencePayload] = []
    evidence_ids: set[str] = set()
    for raw_item in evidence_raw:
        item = _mapping(raw_item, "evidence item")
        evidence_id = _string(item.get("evidence_id"), "evidence_id")
        if evidence_id in evidence_ids:
            raise OracleProtocolError(f"duplicate Oracle evidence id: {evidence_id}")
        try:
            content = base64.b64decode(
                _string(item.get("content_base64"), "evidence.content_base64"),
                validate=True,
            )
        except (binascii.Error, ValueError) as exc:
            raise OracleProtocolError("Oracle evidence content is not valid canonical base64") from exc
        item_digest = _string(item.get("digest"), "evidence.digest")
        if sha256_digest(content) != item_digest:
            raise OracleProtocolError(f"Oracle evidence digest mismatch: {evidence_id}")
        try:
            payload = OracleEvidencePayload(
                evidence_id=evidence_id,
                evidence_type=_string(item.get("type"), "evidence.type"),
                content=content,
                media_type=_string(item.get("media_type"), "evidence.media_type"),
                digest=item_digest,
                classification=_string(item.get("classification", "evaluator-confidential"), "evidence.classification"),
                producer=_optional_string(item.get("producer"), "evidence.producer"),
            )
        except (TypeError, ValueError) as exc:
            raise OracleProtocolError(f"invalid Oracle evidence payload: {evidence_id}") from exc
        evidence_ids.add(evidence_id)
        evidence.append(payload)
    results: list[VerificationResult] = []
    for raw_item in results_raw:
        item = _mapping(raw_item, "result item")
        refs = tuple(_string_list(item.get("evidence_ids", []), "result.evidence_ids"))
        if set(refs) - evidence_ids:
            raise OracleProtocolError("Oracle result references evidence absent from response")
        verdict = _string(item.get("verdict"), "result.verdict")
        if verdict not in {"PASS", "PARTIAL", "FAIL", "INCONCLUSIVE"}:
            raise OracleProtocolError(f"unsupported Oracle verdict: {verdict}")
        confidence = item.get("confidence", 1.0)
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= float(confidence) <= 1:
            raise OracleProtocolError("Oracle result confidence must be between 0 and 1")
        try:
            validity = Validity(_string(item.get("validity", Validity.VALID.value), "result.validity"))
        except ValueError as exc:
            raise OracleProtocolError("Oracle result validity is unknown") from exc
        results.append(VerificationResult(_string(item.get("claim_id"), "result.claim_id"), _string(item.get("dimension"), "result.dimension"), verdict, _string(item.get("severity"), "result.severity"), _string(item.get("method"), "result.method"), _string(item.get("evaluator_version"), "result.evaluator_version"), refs, float(confidence), validity))
    return OracleEvaluationOutput(tuple(results), tuple(evidence))


def _decode_single_frame(frame: bytes, *, max_bytes: int) -> dict[str, object]:
    if len(frame) > max_bytes:
        raise OracleProtocolError("Oracle frame exceeds configured limit")
    try:
        text = frame.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OracleProtocolError("Oracle frame must be UTF-8") from exc
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) != 1:
        raise OracleProtocolError("Oracle protocol requires exactly one JSON frame")
    try:
        value = json.loads(lines[0])
    except json.JSONDecodeError as exc:
        raise OracleProtocolError("Oracle frame is not valid JSON") from exc
    return dict(_mapping(value, "frame"))


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise OracleProtocolError(f"{label} must be an object")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise OracleProtocolError(f"{label} must be a non-empty string")
    return value


def _optional_string(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _string(value, label)


def _string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise OracleProtocolError(f"{label} must be an array of non-empty strings")
    return list(value)
