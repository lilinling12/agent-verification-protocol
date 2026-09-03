"""Required faulty assemblies for TEL-002 terminating evidence negatives.

This module is intentionally narrow.  It does not define a provider interface or
an alternate Network Control backend.  It materializes the second
HiddenRetry/Fallback negative required by the terminating-lab readiness audit:
a one-shot helper in the Toxiproxy network namespace creates an additional
fixture-bound upstream TCP initiation while the certified attempt witnesses are
armed.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .evidence_core import MaterializedEndpoint
from .toxiproxy_evidence import NegativeMode, PhaseExecution
from .toxiproxy_live_lab import ToxiproxyLiveLab

_UPSTREAM_VARIANT = "same-namespace-upstream-extra-connect"


class UpstreamHiddenRetryLiveLab(ToxiproxyLiveLab):
    """TEL-002 lab with the required same-namespace upstream retry negative.

    The existing phase runner still selects ``HiddenRetry/Fallback`` and the
    existing provider-neutral comparator still owns C10.  Only the faulty
    assembly changes: instead of asking the Subject exchange worker for a second
    front-side connect, this subclass injects one direct upstream initiation
    from the Toxiproxy network namespace while all certified-attempt witnesses
    remain armed.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._upstream_negative_attempt: dict[str, object] | None = None

    def certified_attempt(
        self,
        phase_id: str,
        privileged: bool,
        negative_mode: NegativeMode | None,
    ) -> PhaseExecution:
        execution = super().certified_attempt(phase_id, privileged, negative_mode)
        marker = self._upstream_negative_attempt
        self._upstream_negative_attempt = None
        if marker is None:
            return execution
        payload = json.dumps(marker, sort_keys=True, separators=(",", ":")).encode("utf-8")
        marker_ref = self.artifact_store.put_bytes(
            payload,
            logical_role=f"hidden-retry-upstream-negative-{phase_id}",
        )
        return PhaseExecution(
            observation=execution.observation,
            evidence_refs=(*execution.evidence_refs, marker_ref),
        )

    def _execute_role_exchange(
        self,
        *,
        container_name: str,
        endpoint: MaterializedEndpoint,
        attempt_document: dict[str, object],
        extra_connect: bool,
    ) -> dict[str, object]:
        # ``extra_connect`` is set only for the existing HiddenRetry/Fallback
        # subject-active-cut assembly.  Suppress the base front-side fault and
        # replace it with the independently required upstream-side fault.
        exchange = super()._execute_role_exchange(
            container_name=container_name,
            endpoint=endpoint,
            attempt_document=attempt_document,
            extra_connect=False,
        )
        if not extra_connect:
            return exchange

        materialization = self._require_materialization()
        upstream = materialization.selected_binding.upstream
        attempt_id = str(attempt_document["attemptId"])
        helper_name = self._helper_name(attempt_id)
        self._run_bounded(self._upstream_fault_command(helper_name, upstream))
        self._upstream_negative_attempt = {
            "format": "avp-project-hidden-retry-upstream-negative-v0.1",
            "variant": _UPSTREAM_VARIANT,
            "attemptId": attempt_id,
            "phaseId": str(attempt_document["phaseId"]),
            "namespaceContainer": self.topology.container_name,
            "sourceAddress": self.topology.data_address,
            "destination": {
                "family": upstream.family,
                "address": upstream.address,
                "port": upstream.port,
                "role": upstream.role,
            },
            "helperImage": self.helper_artifact.provenance_document(),
        }
        return exchange

    def _upstream_fault_command(
        self,
        helper_name: str,
        upstream: MaterializedEndpoint,
    ) -> list[str]:
        """Build one bounded, capability-minimized same-namespace connect helper."""

        if upstream.family != "ipv4":
            raise ValueError("TEL-002 canonical upstream negative requires the reviewed IPv4 topology")
        script = (
            "import socket,sys; "
            "s=socket.socket(socket.AF_INET,socket.SOCK_STREAM); s.settimeout(1.0); "
            f"s.bind(({self.topology.data_address!r},0)); "
            f"r=s.connect_ex(({upstream.address!r},{upstream.port})); "
            "s.close(); sys.exit(0 if r==0 else r)"
        )
        return [
            self.docker.executable,
            "run",
            "--rm",
            "--name",
            helper_name,
            "--network",
            f"container:{self.topology.container_name}",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            self.helper_artifact.image_ref,
            "python",
            "-c",
            script,
        ]

    def _helper_name(self, attempt_id: str) -> str:
        suffix = hashlib.sha256(attempt_id.encode("utf-8")).hexdigest()[:10]
        return f"avp-nc-upstream-negative-{self.topology.run_token}-{suffix}"


__all__ = ["UpstreamHiddenRetryLiveLab"]
