"""Immutable identity of the complete Agent System under verification."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from avp_ref.canonical import digest


@dataclass(frozen=True, slots=True)
class AgentSystem:
    """Versioned identity for the whole Agent, not just its foundation model.

    AVP comparisons are only meaningful when changes to prompts, tools, memory,
    policy and runtime configuration can be attributed. Optional component
    digests therefore remain explicit instead of being hidden in one opaque
    application version.
    """

    name: str
    version: str
    adapter: str
    config_digest: str
    model_ref: str | None = None
    prompt_digest: str | None = None
    toolset_digest: str | None = None
    memory_digest: str | None = None
    policy_digest: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "adapter": self.adapter,
            "config_digest": self.config_digest,
            "model_ref": self.model_ref,
            "prompt_digest": self.prompt_digest,
            "toolset_digest": self.toolset_digest,
            "memory_digest": self.memory_digest,
            "policy_digest": self.policy_digest,
            "metadata": dict(self.metadata),
        }

    def subject_projection(self) -> dict[str, Any]:
        """Return stable Agent identity safe for a remote Subject boundary.

        Arbitrary AgentSystem metadata remains evaluator-side because the model
        deliberately permits implementation-specific metadata and therefore
        cannot prove that every metadata value is Subject-visible. Stable
        identity/component references are sufficient for Subject-side binding.
        """

        return {
            "identity_digest": self.identity_digest,
            "name": self.name,
            "version": self.version,
            "adapter": self.adapter,
            "config_digest": self.config_digest,
            "model_ref": self.model_ref,
            "prompt_digest": self.prompt_digest,
            "toolset_digest": self.toolset_digest,
            "memory_digest": self.memory_digest,
            "policy_digest": self.policy_digest,
        }

    @property
    def identity_digest(self) -> str:
        """Canonical identity used by EpisodeManifest and experiment pairing."""

        return digest(self.to_dict())
