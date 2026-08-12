"""Seed derivation for reproducible AVS compilation."""

from __future__ import annotations

import hashlib
import secrets
from typing import Any, Mapping

from .errors import CompileDiagnostic, ParameterResolutionError
from .models import SeedBundle

SEED_DIMENSIONS = (
    "scenario",
    "environment",
    "data",
    "user",
    "adversary",
    "fault",
    "agent_sampling",
    "judge",
)
_MAX_SEED = (1 << 63) - 1


def _derive_seed(root_seed: int, label: str) -> int:
    payload = f"avp-seed-v1:{root_seed}:{label}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & _MAX_SEED


def derive_child_seed(parent_seed: int, label: str) -> int:
    """Derive an order-independent child seed for generators/mutations."""

    return _derive_seed(parent_seed, label)


def resolve_seed_bundle(spec: Mapping[str, Any] | None, root_seed: int | None) -> SeedBundle:
    """Resolve explicit/``auto`` AVS seeds to immutable integer values."""

    root = secrets.randbits(63) if root_seed is None else int(root_seed)
    if root < 0:
        raise ParameterResolutionError(
            "root seed must be non-negative",
            (CompileDiagnostic("AVS-SEED-001", "root seed must be non-negative", "$.seeds"),),
        )

    source = spec or {}
    resolved: dict[str, int] = {}
    for dimension in SEED_DIMENSIONS:
        raw = source.get(dimension, "auto")
        if raw == "auto" or raw is None:
            resolved[dimension] = _derive_seed(root, dimension)
            continue
        if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
            raise ParameterResolutionError(
                f"invalid seed for {dimension}",
                (
                    CompileDiagnostic(
                        "AVS-SEED-002",
                        f"seed '{dimension}' must be a non-negative integer or 'auto'",
                        f"$.seeds.{dimension}",
                    ),
                ),
            )
        resolved[dimension] = raw

    return SeedBundle(**resolved)
