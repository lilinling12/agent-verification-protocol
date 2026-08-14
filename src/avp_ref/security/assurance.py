"""Machine-readable AVP Security assurance declarations.

The declaration reports demonstrated properties independently. It is not a
shortcut for protocol conformance and must never infer stronger isolation from
a weaker verified dimension.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from importlib import resources
from typing import Any

from jsonschema import Draft202012Validator


class AssuranceClaim(str, Enum):
    """Portable claim values defined by SecurityAssurance v0.1."""

    VERIFIED = "verified"
    NOT_CLAIMED = "not-claimed"


@dataclass(frozen=True, slots=True)
class SecurityIsolationClaims:
    """Independent isolation dimensions; no dimension implies another."""

    api_capability: AssuranceClaim
    credential_context: AssuranceClaim
    process: AssuranceClaim
    network: AssuranceClaim
    tenant: AssuranceClaim
    sandbox: AssuranceClaim

    def to_dict(self) -> dict[str, str]:
        return {
            "apiCapability": self.api_capability.value,
            "credentialContext": self.credential_context.value,
            "process": self.process.value,
            "network": self.network.value,
            "tenant": self.tenant.value,
            "sandbox": self.sandbox.value,
        }


@dataclass(frozen=True, slots=True)
class SecurityAssurance:
    """SecurityAssurance resource conforming to ``avp.security/v0.1``."""

    isolation: SecurityIsolationClaims

    @classmethod
    def baseline_reference(cls) -> "SecurityAssurance":
        """Truthful declaration for the base in-process ReferenceRuntime.

        The base runtime demonstrates Subject API/capability separation but does
        not claim credential-context, process, network, tenant, or sandbox
        isolation. Optional reference primitives may demonstrate additional
        properties without silently upgrading this base declaration.
        """

        return cls(
            SecurityIsolationClaims(
                api_capability=AssuranceClaim.VERIFIED,
                credential_context=AssuranceClaim.NOT_CLAIMED,
                process=AssuranceClaim.NOT_CLAIMED,
                network=AssuranceClaim.NOT_CLAIMED,
                tenant=AssuranceClaim.NOT_CLAIMED,
                sandbox=AssuranceClaim.NOT_CLAIMED,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "apiVersion": "avp.security/v0.1",
            "kind": "SecurityAssurance",
            "isolation": self.isolation.to_dict(),
        }

    def validate(self) -> None:
        """Validate this declaration against the schema shipped in the wheel."""

        schema = load_security_assurance_schema()
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(self.to_dict())


def load_security_assurance_schema() -> dict[str, Any]:
    """Load the packaged SecurityAssurance schema without repository coupling."""

    text = (
        resources.files("avp_ref.resources")
        .joinpath("security-assurance.schema.json")
        .read_text(encoding="utf-8")
    )
    value = json.loads(text)
    if not isinstance(value, dict):
        raise TypeError("packaged SecurityAssurance schema root must be an object")
    return value
