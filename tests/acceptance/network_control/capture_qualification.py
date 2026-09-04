"""Exact-run AF_PACKET qualification for the privileged Network Control lane.

Qualification intentionally runs the Linux witness with all ``CaptureAssurance``
flags false.  Those flags are reviewed preflight facts that packet parsing cannot
prove by itself; pre-seeding them here would make the qualification circular.
The canary therefore tolerates only the four expected provisional-assurance
markers and fails closed on every other witness-integrity problem.  The final
assurance record is derived only after topology, ordering, capture statistics,
and real connection-cardinality checks succeed.
"""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .evidence_core import MaterializedEndpoint
from .toxiproxy_binding import DockerCli, ToxiproxyControlError, ToxiproxyPrerequisiteError
from .toxiproxy_live_lab import LabHelperArtifact, _RoleProcess
from .toxiproxy_worker import _endpoint_document

_QUALIFICATION_FORMAT = "avp-project-network-capture-qualification-v0.2"
_SLOT_COUNT = 32 * 256
_EXPECTED_PROVISIONAL_PROBLEMS = (
    "egress-coverage-unverified",
    "directionality-unverified",
    "offload-normalization-unverified",
    "pre-syn-connect-gap-unclosed",
)


@dataclass(frozen=True, slots=True)
class QualificationTopology:
    """Run-scoped private network distinct from TEL-002 allocation pools."""

    run_token: str
    network: str
    subnet: str
    source: str
    expected_target: str
    alternate_target: str

    @classmethod
    def for_run(cls, run_id: str) -> "QualificationTopology":
        if not run_id:
            raise ValueError("qualification run id must be non-empty")
        digest = hashlib.sha256(run_id.encode("utf-8")).hexdigest()
        slot = int(digest[:4], 16) % _SLOT_COUNT
        second = 192 + slot // 256
        third = slot % 256
        prefix = f"10.{second}.{third}"
        token = digest[:12]
        return cls(
            run_token=token,
            network=f"avp-nc-qual-{token}",
            subnet=f"{prefix}.0/28",
            source=f"{prefix}.2",
            expected_target=f"{prefix}.3",
            alternate_target=f"{prefix}.4",
        )


@dataclass(frozen=True, slots=True)
class CaptureQualificationResult:
    document: dict[str, object]
    raw_artifacts: tuple[tuple[str, bytes], ...]


class CaptureQualification:
    """Qualify one exact native-Linux runner before TEL-003 assertions are admitted."""

    def __init__(
        self,
        *,
        workspace: Path,
        run_id: str,
        docker: DockerCli | None = None,
        helper: LabHelperArtifact | None = None,
        response_timeout_s: float = 5.0,
    ) -> None:
        self.workspace = Path(workspace).resolve()
        self.run_id = run_id
        self.docker = docker or DockerCli(command_timeout_s=20.0)
        self.helper = helper or LabHelperArtifact.reviewed_amd64()
        self.response_timeout_s = float(response_timeout_s)
        self.topology = QualificationTopology.for_run(run_id)
        self.source_name = f"avp-nc-qual-source-{self.topology.run_token}"
        self.expected_name = f"avp-nc-qual-expected-{self.topology.run_token}"
        self.alternate_name = f"avp-nc-qual-alternate-{self.topology.run_token}"

    def execute(self) -> CaptureQualificationResult:
        docker_info = self._preflight()
        self._prepare_helper()
        try:
            result = self._execute_materialized(docker_info)
        except BaseException as exc:
            for problem in self._cleanup():
                exc.add_note(problem)
            raise
        cleanup_problems = self._cleanup()
        if cleanup_problems:
            raise ToxiproxyPrerequisiteError(
                f"capture qualification cleanup failed: {cleanup_problems!r}"
            )
        return result

    def _execute_materialized(self, docker_info: dict[str, object]) -> CaptureQualificationResult:
        self.docker.run(
            "network",
            "create",
            "--internal",
            "--subnet",
            self.topology.subnet,
            self.topology.network,
        )
        self._start_anchor(self.source_name, self.topology.source)
        self._start_server(self.expected_name, self.topology.expected_target, 43001)
        self._start_server(self.alternate_name, self.topology.alternate_target, 43002)
        self._wait_for_server(self.topology.expected_target, 43001)
        self._wait_for_server(self.topology.alternate_target, 43002)

        inventory = self._source_inventory()
        if inventory != {self.topology.source}:
            raise ToxiproxyPrerequisiteError(
                f"qualification source has unexpected non-loopback IPv4 set: {inventory}"
            )

        raw: list[tuple[str, bytes]] = []
        one = self._observe(
            label="one-expected",
            expected=MaterializedEndpoint(
                "ipv4", self.topology.expected_target, 43001, "qualification-target"
            ),
            connect_targets=((self.topology.expected_target, 43001),),
        )
        raw.append(("one-expected.raw.json", one.pop("rawBytes")))
        _require_counts(one, total=1, expected=1, alternate=0)

        two = self._observe(
            label="two-expected",
            expected=MaterializedEndpoint(
                "ipv4", self.topology.expected_target, 43001, "qualification-target"
            ),
            connect_targets=(
                (self.topology.expected_target, 43001),
                (self.topology.expected_target, 43001),
            ),
        )
        raw.append(("two-expected.raw.json", two.pop("rawBytes")))
        _require_counts(two, total=2, expected=2, alternate=0)

        alternate = self._observe(
            label="expected-plus-alternate",
            expected=MaterializedEndpoint(
                "ipv4", self.topology.expected_target, 43001, "qualification-target"
            ),
            connect_targets=(
                (self.topology.expected_target, 43001),
                (self.topology.alternate_target, 43002),
            ),
        )
        raw.append(("expected-plus-alternate.raw.json", alternate.pop("rawBytes")))
        _require_counts(alternate, total=2, expected=1, alternate=1)

        document: dict[str, object] = {
            "format": _QUALIFICATION_FORMAT,
            "runId": self.run_id,
            "topology": {
                "network": self.topology.network,
                "subnet": self.topology.subnet,
                "source": self.topology.source,
                "expectedTarget": f"{self.topology.expected_target}:43001",
                "alternateTarget": f"{self.topology.alternate_target}:43002",
                "internalNetwork": True,
            },
            "sourceInventory": sorted(inventory),
            "helper": self.helper.provenance_document(),
            "runner": {
                "operatingSystem": str(docker_info.get("OperatingSystem", "")),
                "osType": str(docker_info.get("OSType", "")),
                "architecture": str(docker_info.get("Architecture", "")),
                "serverVersion": str(docker_info.get("ServerVersion", "")),
            },
            "canaries": [one, two, alternate],
            "provisionalWitnessAssurance": {
                "egressCoverageVerified": False,
                "directionalityVerified": False,
                "offloadNormalizationVerified": False,
                "preSynConnectGapClosed": False,
            },
            "captureAssurance": {
                "egressCoverageVerified": True,
                "directionalityVerified": True,
                "offloadNormalizationVerified": True,
                "preSynConnectGapClosed": True,
            },
            "qualificationBasis": [
                "source namespace has exactly one non-loopback IPv4 egress on an internal Docker network",
                "provisional witness runs with all CaptureAssurance inputs false; only the four expected unverified markers are tolerated",
                "witness arm/admit readiness acknowledgement precedes every canary connect admission",
                "one real connect normalizes to exactly one expected initiation",
                "two independent real connects normalize to exactly two expected initiations",
                "an alternate destination is retained and classified rather than hidden by target filtering",
                "all canaries expose packet statistics, zero capture drops, and no validity problem beyond provisional assurance markers",
                "raw SYN count is never below normalized initiation count for the SYN-only witness responsibility",
                "main-adopted terminal drain retains frames queued at the evaluator terminal boundary before witness sealing",
            ],
        }
        return CaptureQualificationResult(document=document, raw_artifacts=tuple(raw))

    def _preflight(self) -> dict[str, object]:
        info = self.docker.run("info", "--format", "{{json .}}")
        try:
            document = json.loads(info)
        except json.JSONDecodeError as exc:
            raise ToxiproxyPrerequisiteError("qualification Docker info is invalid JSON") from exc
        if not isinstance(document, dict):
            raise ToxiproxyPrerequisiteError("qualification Docker info is not an object")
        os_type = str(document.get("OSType", ""))
        architecture = str(document.get("Architecture", ""))
        operating_system = str(document.get("OperatingSystem", ""))
        if os_type != "linux" or architecture not in {"x86_64", "amd64"}:
            raise ToxiproxyPrerequisiteError(
                f"privileged Network Control evidence requires linux/amd64 Docker, got {os_type}/{architecture}"
            )
        if "docker desktop" in operating_system.lower():
            raise ToxiproxyPrerequisiteError("Docker Desktop is not a qualified TEL-003 evidence topology")
        return document

    def _prepare_helper(self) -> None:
        self.docker.run("pull", "--platform", self.helper.platform, self.helper.image_ref)
        value = self.docker.run(
            "image",
            "inspect",
            self.helper.image_ref,
            "--format",
            "{{json .RepoDigests}}",
        )
        try:
            repo_digests = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ToxiproxyPrerequisiteError("qualification helper RepoDigests are invalid") from exc
        if not isinstance(repo_digests, list) or self.helper.image_ref not in repo_digests:
            raise ToxiproxyPrerequisiteError("qualification helper exact digest cannot be verified")

    def _start_anchor(self, name: str, address: str) -> None:
        self.docker.run(
            "run",
            "-d",
            "--name",
            name,
            "--network",
            self.topology.network,
            "--ip",
            address,
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            self.helper.image_ref,
            "python",
            "-c",
            "import signal; signal.pause()",
        )

    def _start_server(self, name: str, address: str, port: int) -> None:
        script = (
            "import socket; "
            "s=socket.socket(); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); "
            f"s.bind(('{address}',{port})); s.listen(16)\n"
            "while True:\n"
            " c,_=s.accept(); c.close()"
        )
        self.docker.run(
            "run",
            "-d",
            "--name",
            name,
            "--network",
            self.topology.network,
            "--ip",
            address,
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            self.helper.image_ref,
            "python",
            "-u",
            "-c",
            script,
        )

    def _wait_for_server(self, address: str, port: int) -> None:
        deadline = time.monotonic() + self.response_timeout_s
        script = (
            "import socket,sys; s=socket.socket(); s.settimeout(0.5); "
            f"r=s.connect_ex(('{address}',{port})); s.close(); sys.exit(0 if r==0 else 1)"
        )
        last = ""
        while time.monotonic() < deadline:
            try:
                self.docker.run("exec", self.source_name, "python", "-c", script)
                return
            except RuntimeError as exc:
                last = type(exc).__name__
                remaining = max(0.0, deadline - time.monotonic())
                if remaining:
                    time.sleep(min(0.02, remaining))
        raise ToxiproxyPrerequisiteError(f"qualification target did not become ready: {last}")

    def _source_inventory(self) -> set[str]:
        completed = self.docker.run(
            "run",
            "--rm",
            "--network",
            f"container:{self.source_name}",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--mount",
            self._workspace_mount,
            "--workdir",
            "/workspace",
            "-e",
            "PYTHONPATH=/workspace/tests",
            "-e",
            "PYTHONDONTWRITEBYTECODE=1",
            self.helper.image_ref,
            "python",
            "-m",
            "acceptance.network_control.toxiproxy_worker",
            "inventory",
        )
        document = json.loads(completed)
        interfaces = document.get("interfaces")
        if not isinstance(interfaces, list):
            raise ToxiproxyControlError("qualification inventory lacks interfaces")
        return {
            str(item["ipv4Address"])
            for item in interfaces
            if isinstance(item, dict) and not bool(item.get("loopback", False))
        }

    def _observe(
        self,
        *,
        label: str,
        expected: MaterializedEndpoint,
        connect_targets: tuple[tuple[str, int], ...],
    ) -> dict[str, object]:
        name = f"avp-nc-qual-witness-{self.topology.run_token}-{label}"
        command = [
            self.docker.executable,
            "run",
            "--rm",
            "-i",
            "--name",
            name,
            "--network",
            f"container:{self.source_name}",
            "--read-only",
            "--cap-drop=ALL",
            "--cap-add=NET_RAW",
            "--security-opt=no-new-privileges",
            "--mount",
            self._workspace_mount,
            "--workdir",
            "/workspace",
            "-e",
            "PYTHONPATH=/workspace/tests",
            "-e",
            "PYTHONDONTWRITEBYTECODE=1",
            self.helper.image_ref,
            "python",
            "-m",
            "acceptance.network_control.toxiproxy_worker",
            "witness",
        ]
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        role = _RoleProcess(
            process,
            container_name=name,
            docker=self.docker,
            response_timeout_s=self.response_timeout_s,
        )
        attempt_id = f"capture-qualification-{label}-{self.topology.run_token}"
        try:
            role.send(
                {
                    "attemptId": attempt_id,
                    "sourceAddress": self.topology.source,
                    "expectedTarget": _endpoint_document(expected),
                    "channel": "W-qualification",
                    "roleId": "qualification-source",
                    "assurance": {
                        "egressCoverageVerified": False,
                        "directionalityVerified": False,
                        "offloadNormalizationVerified": False,
                        "preSynConnectGapClosed": False,
                    },
                }
            )
            ready = role.receive()
            if ready.get("event") != "ready" or ready.get("attemptId") != attempt_id:
                raise ToxiproxyPrerequisiteError(
                    "qualification witness did not acknowledge arm/admit barrier"
                )
            self._connect_sequence(connect_targets)
            role.send({"op": "close", "attemptId": attempt_id})
            result = role.receive()
            facts_values = result.get("channelFacts")
            if (
                not isinstance(facts_values, list)
                or len(facts_values) != 1
                or not isinstance(facts_values[0], dict)
            ):
                raise ToxiproxyControlError(
                    "qualification witness did not return one channel facts record"
                )
            facts = dict(facts_values[0])
            _require_provisional_validity(result.get("validityProblems"), scope="witness")
            _require_provisional_validity(facts.get("validityProblems"), scope="channel")
            if result.get("captureDrops") != 0:
                raise ToxiproxyPrerequisiteError(
                    f"qualification witness capture drops are non-zero: {result.get('captureDrops')!r}"
                )
            raw_bytes = base64.b64decode(str(result["rawArtifactB64"]), validate=True)
            capture_packets = result.get("capturePackets")
            if not isinstance(capture_packets, int):
                raise ToxiproxyPrerequisiteError(
                    "qualification witness packet statistics are unavailable"
                )
            return {
                "label": label,
                "interface": str(ready.get("interface", "")),
                "capturePackets": capture_packets,
                "captureDrops": int(result["captureDrops"]),
                "totalInitiations": int(facts["totalInitiations"]),
                "expectedTargetInitiations": int(facts["expectedTargetInitiations"]),
                "alternateTargetInitiations": int(facts["alternateTargetInitiations"]),
                "rawSynPackets": int(facts["rawSynPackets"]),
                "retransmittedSynPackets": int(facts["retransmittedSynPackets"]),
                "provisionalValidityProblems": list(_EXPECTED_PROVISIONAL_PROBLEMS),
                "rawSha256": hashlib.sha256(raw_bytes).hexdigest(),
                "rawSize": len(raw_bytes),
                "rawBytes": raw_bytes,
            }
        finally:
            role.close()

    def _connect_sequence(self, targets: tuple[tuple[str, int], ...]) -> None:
        script = (
            "import socket\n"
            f"targets={targets!r}\n"
            "for host,port in targets:\n"
            " s=socket.socket(); s.settimeout(1.0); r=s.connect_ex((host,port)); s.close()\n"
            " if r != 0: raise SystemExit(r)"
        )
        self.docker.run("exec", self.source_name, "python", "-c", script)

    def _cleanup(self) -> tuple[str, ...]:
        problems: list[str] = []
        for name in (self.source_name, self.expected_name, self.alternate_name):
            try:
                self.docker.run("rm", "-f", name, allow_failure=True)
            except RuntimeError as exc:
                problems.append(f"qualification-container-cleanup:{name}:{type(exc).__name__}")
        try:
            self.docker.run("network", "rm", self.topology.network, allow_failure=True)
        except RuntimeError as exc:
            problems.append(f"qualification-network-cleanup:{type(exc).__name__}")
        try:
            containers = self.docker.run("ps", "-a", "--format", "{{.Names}}")
            existing = set(containers.splitlines())
            for name in (self.source_name, self.expected_name, self.alternate_name):
                if name in existing:
                    problems.append(f"qualification-residual-container:{name}")
            networks = self.docker.run("network", "ls", "--format", "{{.Name}}")
            if self.topology.network in set(networks.splitlines()):
                problems.append(f"qualification-residual-network:{self.topology.network}")
        except RuntimeError as exc:
            problems.append(f"qualification-residual-check:{type(exc).__name__}")
        return tuple(problems)

    @property
    def _workspace_mount(self) -> str:
        return f"type=bind,src={self.workspace},dst=/workspace,readonly"


def _require_provisional_validity(value: object, *, scope: str) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ToxiproxyPrerequisiteError(
            f"qualification {scope} validity problems are malformed: {value!r}"
        )
    observed = tuple(dict.fromkeys(value))
    if observed != _EXPECTED_PROVISIONAL_PROBLEMS:
        raise ToxiproxyPrerequisiteError(
            f"qualification {scope} has unexpected validity problems: {observed!r}"
        )


def _require_counts(
    document: dict[str, object],
    *,
    total: int,
    expected: int,
    alternate: int,
) -> None:
    observed = (
        int(document["totalInitiations"]),
        int(document["expectedTargetInitiations"]),
        int(document["alternateTargetInitiations"]),
    )
    wanted = (total, expected, alternate)
    if observed != wanted:
        raise ToxiproxyPrerequisiteError(
            f"capture qualification initiation mismatch: observed={observed}, expected={wanted}"
        )
    if int(document["rawSynPackets"]) < total:
        raise ToxiproxyPrerequisiteError(
            "capture qualification raw SYN count is below normalized initiation count"
        )
