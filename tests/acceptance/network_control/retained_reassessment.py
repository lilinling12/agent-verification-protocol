"""Integrity envelope for committed NPR-011 cross-mechanism reassessment bytes.

Source-bundle reconstruction remains in ``cross_mechanism``. This module owns the
smaller long-lived boundary used after the derived record is committed: bounded
archive decoding plus source/plan lineage checks that the portable comparator does
not itself consume.
"""

from __future__ import annotations

import base64
import binascii
import zlib
from typing import Mapping

from .cross_mechanism import SemanticBinding, verify_reassessment_record
from .evidence_core import EvidenceMaterializationError

_MAX_ARCHIVE_BYTES = 1024 * 1024
_MAX_JSON_BYTES = 4 * 1024 * 1024
_DETERMINISTIC_GZIP_HEADER = b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff"


def decode_retained_reassessment_archive(archive_bytes: bytes) -> bytes:
    """Decode one bounded deterministic text archive without unbounded inflation."""

    if len(archive_bytes) > _MAX_ARCHIVE_BYTES:
        raise EvidenceMaterializationError("reassessment archive exceeds bounded size")
    if not archive_bytes.endswith(b"\n") or b"\n" in archive_bytes[:-1]:
        raise EvidenceMaterializationError("reassessment archive must contain one base64 line")
    try:
        compressed = base64.b64decode(archive_bytes[:-1], validate=True)
    except (binascii.Error, ValueError) as exc:
        raise EvidenceMaterializationError("reassessment archive is not strict base64") from exc
    if not compressed.startswith(_DETERMINISTIC_GZIP_HEADER):
        raise EvidenceMaterializationError("reassessment archive gzip header is not deterministic")
    try:
        decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
        exact = decoder.decompress(compressed, _MAX_JSON_BYTES + 1)
    except zlib.error as exc:
        raise EvidenceMaterializationError("reassessment archive gzip payload is invalid") from exc
    if len(exact) > _MAX_JSON_BYTES or decoder.unconsumed_tail or not decoder.eof:
        raise EvidenceMaterializationError("reassessment JSON exceeds bounded size or is incomplete")
    return exact


def verify_retained_reassessment(
    exact_bytes: bytes,
    *,
    semantic_binding: SemanticBinding | None = None,
) -> dict[str, object]:
    """Verify comparator output and non-comparator source/plan lineage invariants."""

    document = verify_reassessment_record(exact_bytes, semantic_binding=semantic_binding)
    mechanisms = _object(document, "mechanisms")
    for mechanism_class in ("terminating-intercepting", "packet-path"):
        mechanism = _object(mechanisms, mechanism_class)
        source = _object(mechanism, "source")
        source_commit = _lower_hex(source.get("sourceCommit"), 40, "source commit")
        _lower_hex(source.get("zipSha256"), 64, "source ZIP sha256")
        cases = mechanism.get("cases")
        if not isinstance(cases, list) or not cases:
            raise EvidenceMaterializationError(f"{mechanism_class} retained cases are missing")
        plan_commits = {
            _source_commit_from_case(item, mechanism_class)
            for item in cases
        }
        if plan_commits != {source_commit}:
            raise EvidenceMaterializationError(
                f"{mechanism_class} sealed-plan/source commit binding drift"
            )
    return document


def _source_commit_from_case(value: object, mechanism_class: str) -> str:
    case = _mapping(value)
    plan = _object(case, "sealedPlan")
    semantic = _object(plan, "semanticBaseline")
    return _lower_hex(
        semantic.get("commit"), 40, f"{mechanism_class} sealed-plan semantic commit"
    )


def _object(document: Mapping[str, object], key: str) -> dict[str, object]:
    return _mapping(document.get(key))


def _mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise EvidenceMaterializationError("retained reassessment field must be an object")
    return value


def _lower_hex(value: object, length: int, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != length
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise EvidenceMaterializationError(
            f"{label} must be {length} lowercase hex characters"
        )
    return value
