"""Semantic RelationalStateManifest integrity checks.

JSON Schema owns serialized shape. ``RelationalManifest.validate_integrity``
executes the cross-reference constraints of AVP-RELATIONAL-017 at the resource
admission boundary. This module preserves the focused validator entry point for
TCK use without creating a second semantic implementation.
"""

from __future__ import annotations

from .relational import RelationalManifest


def validate_manifest_integrity(manifest: RelationalManifest) -> None:
    """Reject ambiguous or dangling logical Manifest references fail closed."""

    manifest.validate_integrity()
