"""Immutable domain models produced by the AVS compiler."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


FrozenValue = Any


def deep_freeze(value: Any) -> FrozenValue:
    """Recursively freeze JSON-compatible data.

    ``dataclass(frozen=True)`` only protects attribute reassignment; without a
    recursive freeze, nested dictionaries could still mutate after a digest was
    calculated. AVP relies on instance digests as audit identities, so deep
    immutability is a protocol invariant rather than a style preference.
    """

    if isinstance(value, Mapping):
        return MappingProxyType({str(key): deep_freeze(item) for key, item in value.items()})
    if isinstance(value, list | tuple):
        return tuple(deep_freeze(item) for item in value)
    return value


def deep_thaw(value: FrozenValue) -> Any:
    """Convert frozen domain data back to plain JSON-compatible containers."""

    if isinstance(value, Mapping):
        return {key: deep_thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [deep_thaw(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class SeedBundle:
    """Independent deterministic seeds for AVS nondeterminism dimensions."""

    scenario: int
    environment: int
    data: int
    user: int
    adversary: int
    fault: int
    agent_sampling: int
    judge: int

    def to_dict(self) -> dict[str, int]:
        return {
            "scenario": self.scenario,
            "environment": self.environment,
            "data": self.data,
            "user": self.user,
            "adversary": self.adversary,
            "fault": self.fault,
            "agent_sampling": self.agent_sampling,
            "judge": self.judge,
        }


@dataclass(frozen=True, slots=True)
class ResolvedReference:
    """Deterministic record of one AVS URI resolution."""

    path: str
    uri: str
    digest: str
    mode: str
    media_type: str | None = None
    version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "path": self.path,
            "uri": self.uri,
            "digest": self.digest,
            "mode": self.mode,
        }
        if self.media_type:
            result["media_type"] = self.media_type
        if self.version:
            result["version"] = self.version
        return result


@dataclass(frozen=True, slots=True)
class GeneratorRecord:
    """Audit record for a parameter value produced by a generator."""

    parameter: str
    generator_type: str
    generator_version: str
    seed: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter": self.parameter,
            "generator_type": self.generator_type,
            "generator_version": self.generator_version,
            "seed": self.seed,
        }


@dataclass(frozen=True, slots=True)
class ScenarioInstance:
    """Immutable, fully materialized AVS ScenarioInstance.

    The ``instance_digest`` is computed from all other serialized fields and is
    therefore an audit identity. Consumers should use :meth:`to_dict` when a
    mutable JSON representation is required for transport.
    """

    template_digest: str
    instance_digest: str
    document: Mapping[str, FrozenValue]

    def to_dict(self) -> dict[str, Any]:
        return deep_thaw(self.document)

    def subject_projection(self, actor_id: str = "subject") -> Mapping[str, FrozenValue]:
        """Return the conservative Agent-Plane view of this instance.

        Verification conditions, faults, graders, validity rules and
        contamination controls intentionally remain evaluator-only. The Subject
        receives what it needs to act, not the benchmark answer key.
        """

        doc = self.document
        actors = [deep_thaw(actor) for actor in doc.get("actors", ()) if actor.get("id") == actor_id]
        capabilities = doc.get("capabilities", {})
        actor_capabilities = capabilities.get(actor_id, {}) if isinstance(capabilities, Mapping) else {}
        public = {
            "apiVersion": doc["apiVersion"],
            "kind": doc["kind"],
            "metadata": deep_thaw(doc.get("metadata", {})),
            "task": deep_thaw(doc.get("task", {})),
            "actors": actors,
            "capabilities": {actor_id: deep_thaw(actor_capabilities)},
            "budgets": deep_thaw(doc.get("budgets", {})),
        }
        return deep_freeze(public)
