"""Deterministic reference resolution for AVS resources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from avp_ref.canonical import digest

from .errors import CompileDiagnostic, ReferenceResolutionError
from .models import ResolvedReference


class ReferenceResolver(Protocol):
    """Resolve a versioned AVS URI to an immutable content identity."""

    def resolve(self, path: str, uri: str) -> ResolvedReference:
        ...


@dataclass(frozen=True, slots=True)
class SymbolicReferenceResolver:
    """Alpha resolver that records a stable symbolic URI identity.

    This deliberately does *not* claim that ``digest(uri)`` is an Environment or
    Oracle package digest. Strict compilation must use a resolver backed by an
    actual registry/artifact store.
    """

    def resolve(self, path: str, uri: str) -> ResolvedReference:
        return ResolvedReference(path=path, uri=uri, digest=digest({"uri": uri}), mode="symbolic")


@dataclass(frozen=True, slots=True)
class StaticReferenceResolver:
    """Simple content resolver useful for tests and local package locks."""

    records: dict[str, dict[str, str]]

    def resolve(self, path: str, uri: str) -> ResolvedReference:
        record = self.records.get(uri)
        if not record:
            raise ReferenceResolutionError(
                f"unresolved AVS reference: {uri}",
                (CompileDiagnostic("AVS-REF-001", f"unresolved reference '{uri}'", path),),
            )
        return ResolvedReference(
            path=path,
            uri=uri,
            digest=record["digest"],
            mode="content",
            media_type=record.get("media_type"),
            version=record.get("version"),
        )
