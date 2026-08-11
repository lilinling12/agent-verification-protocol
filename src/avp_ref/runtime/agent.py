"""Agent system identity models used by AVP runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any


@dataclass(frozen=True, slots=True)
class AgentSystem:
    """Identity of the Agent under verification.

    AVP evaluates a complete Agent System, not only a language model. The
    identity therefore includes the deployed version and configuration digest
    so results remain comparable across releases.
    """

    name: str
    version: str
    protocol: str = "in-process"
    config_digest: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "protocol": self.protocol,
            "config_digest": self.config_digest,
        }
