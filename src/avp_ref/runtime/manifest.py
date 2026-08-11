"""Immutable, reproducibility-oriented Episode manifest."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from avp_ref.canonical import digest
from avp_ref.environment.models import EnvironmentDescription
from avp_ref.scenario.models import ScenarioInstance

from .agent import AgentSystem


def _resolved_reference_digest(scenario: ScenarioInstance, path: str) -> str | None:
    compilation = scenario.document.get("compilation", {})
    for item in compilation.get("resolved_references", ()):
        if item.get("path") == path:
            return str(item.get("digest"))
    return None


@dataclass(frozen=True, slots=True)
class EpisodeManifest:
    """Immutable identities required to explain exactly what was evaluated."""

    protocol_version: str
    runtime_version: str
    scenario_instance_digest: str
    scenario_template_digest: str
    seed_bundle_digest: str
    agent_system_digest: str
    environment_ref_digest: str | None
    environment_adapter_digest: str
    oracle_bundle_digest: str | None = None
    resource_manifest_digest: str | None = None

    @classmethod
    def create(
        cls,
        scenario: ScenarioInstance,
        agent: AgentSystem,
        environment: EnvironmentDescription,
        runtime_version: str,
        *,
        resource_manifest_digest: str | None = None,
    ) -> "EpisodeManifest":
        seed_bundle: Mapping[str, Any] = scenario.document.get("compilation", {}).get("seed_bundle", {})
        return cls(
            protocol_version=str(scenario.document.get("apiVersion", "avp.spec/v0.1")),
            runtime_version=runtime_version,
            scenario_instance_digest=scenario.instance_digest,
            scenario_template_digest=scenario.template_digest,
            seed_bundle_digest=digest(dict(seed_bundle)),
            agent_system_digest=agent.identity_digest,
            environment_ref_digest=_resolved_reference_digest(scenario, "$.environment.ref"),
            environment_adapter_digest=environment.identity_digest,
            oracle_bundle_digest=_resolved_reference_digest(scenario, "$.oracle.ref"),
            resource_manifest_digest=resource_manifest_digest,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_version": self.protocol_version,
            "runtime_version": self.runtime_version,
            "scenario_instance_digest": self.scenario_instance_digest,
            "scenario_template_digest": self.scenario_template_digest,
            "seed_bundle_digest": self.seed_bundle_digest,
            "agent_system_digest": self.agent_system_digest,
            "environment_ref_digest": self.environment_ref_digest,
            "environment_adapter_digest": self.environment_adapter_digest,
            "oracle_bundle_digest": self.oracle_bundle_digest,
            "resource_manifest_digest": self.resource_manifest_digest,
        }

    @property
    def manifest_digest(self) -> str:
        return digest(self.to_dict())
