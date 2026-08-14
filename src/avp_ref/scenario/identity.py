"""Language-neutral ScenarioInstance identity helpers.

AVP Scenario v0.1 defines ScenarioInstance identity as SHA-256 over the RFC
8785 JCS canonical bytes of the serialized instance after removing the
non-semantic top-level ``provenance`` field and the self-referential
``instanceDigest`` field.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

import rfc8785

from .errors import ScenarioIdentityError


_EXCLUDED_TOP_LEVEL_FIELDS = frozenset({"instanceDigest", "provenance"})


def identity_preimage(document: Mapping[str, Any]) -> dict[str, Any]:
    """Return the semantic ScenarioInstance document covered by identity.

    The returned mapping is detached from the top-level input mapping. Nested
    values are not mutated by this function; RFC 8785 serialization is read-only.
    """

    return {
        str(key): value
        for key, value in document.items()
        if str(key) not in _EXCLUDED_TOP_LEVEL_FIELDS
    }


def canonical_instance_bytes(document: Mapping[str, Any]) -> bytes:
    """Serialize the ScenarioInstance identity preimage using RFC 8785 JCS."""

    return rfc8785.dumps(identity_preimage(document))


def scenario_instance_digest(document: Mapping[str, Any]) -> str:
    """Return the AVP Scenario v0.1 content identity for ``document``."""

    payload = canonical_instance_bytes(document)
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def verify_scenario_instance_identity(
    document: Mapping[str, Any],
    *,
    expected_digest: str | None = None,
) -> str:
    """Fail closed unless declared and computed ScenarioInstance identity agree."""

    declared = document.get("instanceDigest")
    if not isinstance(declared, str) or not declared:
        raise ScenarioIdentityError("ScenarioInstance instanceDigest is missing")

    computed = scenario_instance_digest(document)
    if declared != computed:
        raise ScenarioIdentityError(
            "ScenarioInstance instanceDigest does not match RFC 8785 semantic content"
        )
    if expected_digest is not None and expected_digest != declared:
        raise ScenarioIdentityError(
            "ScenarioInstance object identity does not match serialized instanceDigest"
        )
    return computed
