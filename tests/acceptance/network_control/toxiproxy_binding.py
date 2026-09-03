"""Concrete Toxiproxy v2.12.0 binding for Network Control TEL-002.

This module is project acceptance-evidence plumbing, not a public backend API or
portable AVP contract. Toxiproxy/container identities remain implementation
provenance; portable outcomes continue to be owned by ``portable_comparator``.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import math
import re
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

from .evidence_core import EvidenceMaterializationError, MaterializedEndpoint

_TOXIPROXY_VERSION = "2.12.0"
_TOXIPROXY_IMAGE_REPOSITORY = "ghcr.io/shopify/toxiproxy"
_TOXIPROXY_INDEX_DIGEST = "sha256:9378ed52a28bc50edc1350f936f518f31fa95f0d15917d6eb40b8e376d1a214e"
_TOXIPROXY_PLATFORM_DIGESTS = {
    "linux/amd64": "sha256:a3e244375123dad8849091bcc59775e188624d3f602db01901f9af855682fef8",
    "linux/arm64": "sha256:5ab4b4e8f476fd5452eb9584a608dd7cf8c11135878a8f7953722a9fcb9b3d87",
}
_RUN_TOKEN_RE = re.compile(r"[^a-z0-9-]+")


class ToxiproxyPrerequisiteError(RuntimeError):
    """Raised when the reviewed local TEL-002 execution prerequisites are absent."""


class ToxiproxyControlError(RuntimeError):
    """Raised for bounded Docker/Toxiproxy control-plane failures."""


@dataclass(frozen=True, slots=True)
class ToxiproxyArtifact:
    """Exact reviewed Toxiproxy execution identity for one platform."""

    platform: str
    version: str
    source_commit: str
    index_digest: str
    platform_digest: str

    @classmethod
    def reviewed(cls, platform: str) -> "ToxiproxyArtifact":
        try:
            platform_digest = _TOXIPROXY_PLATFORM_DIGESTS[platform]
        except KeyError as exc:
            raise ToxiproxyPrerequisiteError(
                f"TEL-002 reviewed Toxiproxy platform is unsupported: {platform!r}"
            ) from exc
        return cls(
            platform=platform,
            version=_TOXIPROXY_VERSION,
            source_commit="3ccd6a79cbc6c6a72b884d295ad314b75cdf3962",
            index_digest=_TOXIPROXY_INDEX_DIGEST,
            platform_digest=platform_digest,
        )

    @property
    def image_ref(self) -> str:
        return f"{_TOXIPROXY_IMAGE_REPOSITORY}@{self.platform_digest}"

    def provenance_document(self) -> dict[str, str]:
        return {
            "repository": _TOXIPROXY_IMAGE_REPOSITORY,
            "version": self.version,
            "sourceCommit": self.source_commit,
            "ociIndexDigest": self.index_digest,
            "platform": self.platform,
            "platformManifestDigest": self.platform_digest,
            "imageRef": self.image_ref,
        }


@dataclass(frozen=True, slots=True)
class ToxiproxyRunTopology:
    """Run-scoped concrete container/network identities and literal addresses."""

    run_token: str
    admin_network: str
    data_network: str
    container_name: str
    admin_address: str
    data_address: str

    @classmethod
    def for_run(cls, run_id: str) -> "ToxiproxyRunTopology":
        if not run_id:
            raise EvidenceMaterializationError("run id must be non-empty")
        normalized = _RUN_TOKEN_RE.sub("-", run_id.lower()).strip("-")[:24] or "run"
        suffix = hashlib.sha256(run_id.encode("utf-8")).hexdigest()[:8]
        token = f"{normalized}-{suffix}"
        # Distinct RFC1918 /28s are derived from the run identity. Docker will fail
        # closed if either subnet overlaps an existing local network.
        octet = 16 + (int(suffix[:2], 16) % 200)
        return cls(
            run_token=token,
            admin_network=f"avp-nc-admin-{token}",
            data_network=f"avp-nc-data-{token}",
            container_name=f"avp-nc-toxiproxy-{token}",
            admin_address=f"172.29.{octet}.2",
            data_address=f"172.30.{octet}.2",
        )

    @property
    def admin_subnet(self) -> str:
        return str(ipaddress.ip_network(f"{self.admin_address}/28", strict=False))

    @property
    def data_subnet(self) -> str:
        return str(ipaddress.ip_network(f"{self.data_address}/28", strict=False))


@dataclass(frozen=True, slots=True)
class ProxyBinding:
    name: str
    listen: MaterializedEndpoint
    upstream: MaterializedEndpoint

    def __post_init__(self) -> None:
        if not self.name:
            raise EvidenceMaterializationError("proxy name must be non-empty")
        if self.listen.family != self.upstream.family:
            raise EvidenceMaterializationError("proxy listener/upstream families must match")


@dataclass(frozen=True, slots=True)
class ControlSnapshot:
    operation: str
    status_code: int
    response_bytes: bytes


class DockerCli:
    """Concrete bounded Docker CLI seam for the local TEL-002 lab."""

    def __init__(
        self,
        *,
        executable: str = "docker",
        command_timeout_s: float = 15.0,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        if not executable:
            raise ValueError("docker executable must be non-empty")
        if not math.isfinite(command_timeout_s) or command_timeout_s <= 0:
            raise ValueError("Docker command timeout must be positive and finite")
        self.executable = executable
        self.command_timeout_s = float(command_timeout_s)
        self._runner = runner

    def run(self, *args: str, allow_failure: bool = False) -> str:
        command = [self.executable, *args]
        try:
            completed = self._runner(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.command_timeout_s,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ToxiproxyPrerequisiteError(
                f"cannot execute bounded Docker control command: {command!r}"
            ) from exc
        if completed.returncode != 0 and not allow_failure:
            detail = (completed.stderr or completed.stdout or "docker command failed").strip()
            raise ToxiproxyControlError(f"docker control failed ({completed.returncode}): {detail}")
        return completed.stdout.strip()


class ToxiproxyAdminClient:
    """Minimal concrete v2.12.0 admin client; no provider-generic interface."""

    def __init__(
        self,
        *,
        admin_address: str,
        port: int = 8474,
        timeout_s: float = 3.0,
        opener: Callable[..., object] = urllib.request.urlopen,
    ) -> None:
        parsed = ipaddress.ip_address(admin_address)
        if parsed.version != 4:
            raise EvidenceMaterializationError("TEL-002 admin client currently requires literal IPv4")
        if not (1 <= port <= 65535):
            raise EvidenceMaterializationError("Toxiproxy admin port must be in [1, 65535]")
        if not math.isfinite(timeout_s) or timeout_s <= 0:
            raise EvidenceMaterializationError("Toxiproxy admin timeout must be positive and finite")
        self._base = f"http://{parsed}:{port}"
        self._timeout_s = float(timeout_s)
        self._opener = opener

    def version(self) -> tuple[str, ControlSnapshot]:
        snapshot = self._request("GET", "/version")
        value = snapshot.response_bytes.decode("utf-8").strip()
        return value, snapshot

    def create_proxy(self, binding: ProxyBinding) -> ControlSnapshot:
        payload = {
            "name": binding.name,
            "listen": _endpoint_socket(binding.listen),
            "upstream": _endpoint_socket(binding.upstream),
            "enabled": True,
        }
        return self._request("POST", "/proxies", payload)

    def create_upstream_timeout_cut(self, proxy_name: str, *, toxic_name: str) -> ControlSnapshot:
        if not proxy_name or not toxic_name:
            raise EvidenceMaterializationError("proxy/toxic names must be non-empty")
        payload = {
            "name": toxic_name,
            "type": "timeout",
            "stream": "upstream",
            "toxicity": 1.0,
            "attributes": {"timeout": 0},
        }
        return self._request("POST", f"/proxies/{proxy_name}/toxics", payload)

    def delete_toxic(self, proxy_name: str, toxic_name: str) -> ControlSnapshot:
        return self._request("DELETE", f"/proxies/{proxy_name}/toxics/{toxic_name}")

    def delete_proxy(self, proxy_name: str) -> ControlSnapshot:
        return self._request("DELETE", f"/proxies/{proxy_name}")

    def proxies(self) -> tuple[dict[str, object], ControlSnapshot]:
        snapshot = self._request("GET", "/proxies")
        value = json.loads(snapshot.response_bytes.decode("utf-8"))
        if not isinstance(value, dict):
            raise ToxiproxyControlError("Toxiproxy /proxies response is not an object")
        return value, snapshot

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
    ) -> ControlSnapshot:
        body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            self._base + path,
            data=body,
            method=method,
            headers={"Content-Type": "application/json"} if body is not None else {},
        )
        try:
            response = self._opener(request, timeout=self._timeout_s)
            with response:  # type: ignore[attr-defined]
                status = int(response.status)  # type: ignore[attr-defined]
                response_bytes = bytes(response.read())  # type: ignore[attr-defined]
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ToxiproxyControlError(f"Toxiproxy admin request failed: {method} {path}") from exc
        if not (200 <= status < 300):
            raise ToxiproxyControlError(f"Toxiproxy admin returned HTTP {status}: {method} {path}")
        return ControlSnapshot(
            operation=f"{method} {path}",
            status_code=status,
            response_bytes=response_bytes,
        )


class ToxiproxyContainer:
    """Own one exact-digest Toxiproxy process and its two run-scoped networks."""

    def __init__(
        self,
        *,
        artifact: ToxiproxyArtifact,
        topology: ToxiproxyRunTopology,
        docker: DockerCli,
    ) -> None:
        self.artifact = artifact
        self.topology = topology
        self.docker = docker
        self._started = False

    def start(self) -> ToxiproxyAdminClient:
        if self._started:
            raise RuntimeError("Toxiproxy container is already started")
        self.docker.run("pull", "--platform", self.artifact.platform, self.artifact.image_ref)
        self._verify_pulled_digest()
        self.docker.run(
            "network",
            "create",
            "--internal",
            "--subnet",
            self.topology.admin_subnet,
            self.topology.admin_network,
        )
        try:
            self.docker.run(
                "network",
                "create",
                "--internal",
                "--subnet",
                self.topology.data_subnet,
                self.topology.data_network,
            )
            self.docker.run(
                "run",
                "-d",
                "--name",
                self.topology.container_name,
                "--network",
                self.topology.admin_network,
                "--ip",
                self.topology.admin_address,
                "--read-only",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                self.artifact.image_ref,
                f"-host={self.topology.admin_address}",
            )
            self.docker.run(
                "network",
                "connect",
                "--ip",
                self.topology.data_address,
                self.topology.data_network,
                self.topology.container_name,
            )
        except BaseException:
            self.cleanup()
            raise
        self._started = True
        return ToxiproxyAdminClient(admin_address=self.topology.admin_address)

    def verify_version(self, admin: ToxiproxyAdminClient) -> ControlSnapshot:
        value, snapshot = admin.version()
        normalized = value.removeprefix("toxiproxy-server version ").strip()
        if normalized != self.artifact.version:
            raise ToxiproxyControlError(
                f"unexpected Toxiproxy runtime version {value!r}; expected {self.artifact.version!r}"
            )
        return snapshot

    def cleanup(self) -> tuple[str, ...]:
        """Best-effort idempotent cleanup that reports, rather than masks, failures."""

        problems: list[str] = []
        for args in (
            ("rm", "-f", self.topology.container_name),
            ("network", "rm", self.topology.data_network),
            ("network", "rm", self.topology.admin_network),
        ):
            try:
                self.docker.run(*args, allow_failure=True)
            except RuntimeError as exc:
                problems.append(f"docker-cleanup:{args[0]}:{type(exc).__name__}")
        self._started = False
        return tuple(problems)

    def residual_resources(self) -> tuple[str, ...]:
        problems: list[str] = []
        container = self.docker.run(
            "ps",
            "-a",
            "--filter",
            f"name=^{self.topology.container_name}$",
            "--format",
            "{{.Names}}",
        )
        if container.strip() == self.topology.container_name:
            problems.append(f"residual-container:{self.topology.container_name}")
        networks = self.docker.run("network", "ls", "--format", "{{.Name}}")
        existing = set(networks.splitlines())
        for network in (self.topology.data_network, self.topology.admin_network):
            if network in existing:
                problems.append(f"residual-network:{network}")
        return tuple(problems)

    def _verify_pulled_digest(self) -> None:
        repo_digests = self.docker.run(
            "image",
            "inspect",
            self.artifact.image_ref,
            "--format",
            "{{json .RepoDigests}}",
        )
        try:
            values = json.loads(repo_digests)
        except json.JSONDecodeError as exc:
            raise ToxiproxyControlError("Docker image inspect returned invalid RepoDigests JSON") from exc
        expected = self.artifact.image_ref
        if not isinstance(values, list) or expected not in values:
            raise ToxiproxyControlError(
                f"pulled Toxiproxy image does not retain expected exact digest {expected!r}"
            )


def selected_and_control_bindings(
    *,
    topology: ToxiproxyRunTopology,
    selected_listen_port: int,
    selected_upstream: MaterializedEndpoint,
    control_listen_port: int,
    control_upstream: MaterializedEndpoint,
) -> tuple[ProxyBinding, ProxyBinding]:
    """Materialize distinct selected/control provider bindings on the data address."""

    selected = ProxyBinding(
        name=f"selected-{topology.run_token}",
        listen=MaterializedEndpoint(
            family="ipv4",
            address=topology.data_address,
            port=selected_listen_port,
            role="subject-destination",
        ),
        upstream=selected_upstream,
    )
    control = ProxyBinding(
        name=f"control-{topology.run_token}",
        listen=MaterializedEndpoint(
            family="ipv4",
            address=topology.data_address,
            port=control_listen_port,
            role="control-subject-destination",
        ),
        upstream=control_upstream,
    )
    if selected.listen.port == control.listen.port:
        raise EvidenceMaterializationError("selected/control proxy listener ports must be distinct")
    if selected.upstream == control.upstream:
        raise EvidenceMaterializationError("selected/control upstream endpoints must be distinct")
    return selected, control


def _endpoint_socket(endpoint: MaterializedEndpoint) -> str:
    if endpoint.family == "ipv6":
        return f"[{endpoint.address}]:{endpoint.port}"
    return f"{endpoint.address}:{endpoint.port}"
