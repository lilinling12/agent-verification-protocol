"""TEL-002 unit tests for the concrete pinned Toxiproxy mechanism binding."""

from __future__ import annotations

import io
import json
import subprocess
import unittest
import urllib.error
from dataclasses import dataclass
from typing import Any

from acceptance.network_control.evidence_core import EvidenceMaterializationError, MaterializedEndpoint
from acceptance.network_control.toxiproxy_binding import (
    DockerCli,
    ProxyBinding,
    ToxiproxyAdminClient,
    ToxiproxyArtifact,
    ToxiproxyContainer,
    ToxiproxyControlError,
    ToxiproxyPrerequisiteError,
    ToxiproxyRunTopology,
    selected_and_control_bindings,
)

_AMD64_DIGEST = "sha256:a3e244375123dad8849091bcc59775e188624d3f602db01901f9af855682fef8"
_INDEX_DIGEST = "sha256:9378ed52a28bc50edc1350f936f518f31fa95f0d15917d6eb40b8e376d1a214e"


def endpoint(address: str, port: int, role: str) -> MaterializedEndpoint:
    return MaterializedEndpoint(family="ipv4", address=address, port=port, role=role)


@dataclass
class FakeResponse:
    status: int
    payload: bytes

    def read(self) -> bytes:
        return self.payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None


class RecordingOpener:
    def __init__(self, responses: list[FakeResponse] | None = None) -> None:
        self.responses = list(responses or [FakeResponse(200, b"{}")])
        self.requests: list[tuple[str, str, bytes | None, float]] = []

    def __call__(self, request: Any, *, timeout: float) -> FakeResponse:
        self.requests.append((request.method, request.full_url, request.data, timeout))
        if not self.responses:
            raise AssertionError("unexpected additional HTTP request")
        return self.responses.pop(0)


class RecordingRunner:
    def __init__(self, *, fail_on_prefix: tuple[str, ...] | None = None) -> None:
        self.commands: list[list[str]] = []
        self.fail_on_prefix = fail_on_prefix

    def __call__(self, command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.commands.append(list(command))
        if self.fail_on_prefix is not None and tuple(command[1 : 1 + len(self.fail_on_prefix)]) == self.fail_on_prefix:
            return subprocess.CompletedProcess(command, 1, "", "forced failure")
        if command[1:3] == ["image", "inspect"]:
            image = command[3]
            return subprocess.CompletedProcess(command, 0, json.dumps([image]), "")
        if command[1:3] == ["ps", "-a"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[1:3] == ["network", "ls"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, 0, "ok", "")


class ArtifactTests(unittest.TestCase):
    def test_reviewed_artifact_uses_exact_platform_digest(self) -> None:
        artifact = ToxiproxyArtifact.reviewed("linux/amd64")
        self.assertEqual(artifact.version, "2.12.0")
        self.assertEqual(artifact.index_digest, _INDEX_DIGEST)
        self.assertEqual(artifact.platform_digest, _AMD64_DIGEST)
        self.assertEqual(artifact.image_ref, f"ghcr.io/shopify/toxiproxy@{_AMD64_DIGEST}")
        self.assertNotIn(":latest", artifact.image_ref)
        self.assertNotIn(":2.12.0", artifact.image_ref)

    def test_unsupported_platform_fails_closed(self) -> None:
        with self.assertRaises(ToxiproxyPrerequisiteError):
            ToxiproxyArtifact.reviewed("linux/s390x")


class TopologyTests(unittest.TestCase):
    def test_run_topology_is_deterministic_and_separates_admin_data(self) -> None:
        first = ToxiproxyRunTopology.for_run("Run 001/Example")
        second = ToxiproxyRunTopology.for_run("Run 001/Example")
        other = ToxiproxyRunTopology.for_run("Run 002/Example")
        self.assertEqual(first, second)
        self.assertNotEqual(first.run_token, other.run_token)
        self.assertNotEqual(first.admin_network, first.data_network)
        self.assertNotEqual(first.admin_subnet, first.data_subnet)
        self.assertNotEqual(first.admin_address, first.data_address)

    def test_selected_and_control_bindings_are_distinct(self) -> None:
        topology = ToxiproxyRunTopology.for_run("run-001")
        selected, control = selected_and_control_bindings(
            topology=topology,
            selected_listen_port=41001,
            selected_upstream=endpoint("172.30.10.3", 42001, "upstream-fixture"),
            control_listen_port=41002,
            control_upstream=endpoint("172.30.10.4", 42002, "control-fixture"),
        )
        self.assertNotEqual(selected.name, control.name)
        self.assertEqual(selected.listen.address, topology.data_address)
        self.assertEqual(control.listen.address, topology.data_address)
        self.assertNotEqual(selected.listen.port, control.listen.port)

        with self.assertRaises(EvidenceMaterializationError):
            selected_and_control_bindings(
                topology=topology,
                selected_listen_port=41001,
                selected_upstream=selected.upstream,
                control_listen_port=41001,
                control_upstream=control.upstream,
            )


class AdminClientTests(unittest.TestCase):
    def test_proxy_and_timeout_toxic_payloads_are_exact(self) -> None:
        opener = RecordingOpener([FakeResponse(200, b"{}"), FakeResponse(200, b"{}")])
        client = ToxiproxyAdminClient(admin_address="172.29.20.2", opener=opener)
        binding = ProxyBinding(
            name="selected-run",
            listen=endpoint("172.30.20.2", 41001, "subject-destination"),
            upstream=endpoint("172.30.20.3", 42001, "upstream-fixture"),
        )

        client.create_proxy(binding)
        client.create_upstream_timeout_cut("selected-run", toxic_name="cut-run")

        method, url, body, timeout = opener.requests[0]
        self.assertEqual(method, "POST")
        self.assertEqual(url, "http://172.29.20.2:8474/proxies")
        self.assertEqual(timeout, 3.0)
        self.assertEqual(
            json.loads((body or b"").decode("utf-8")),
            {
                "name": "selected-run",
                "listen": "172.30.20.2:41001",
                "upstream": "172.30.20.3:42001",
                "enabled": True,
            },
        )

        method, url, body, _timeout = opener.requests[1]
        self.assertEqual(method, "POST")
        self.assertEqual(url, "http://172.29.20.2:8474/proxies/selected-run/toxics")
        self.assertEqual(
            json.loads((body or b"").decode("utf-8")),
            {
                "name": "cut-run",
                "type": "timeout",
                "stream": "upstream",
                "toxicity": 1.0,
                "attributes": {"timeout": 0},
            },
        )

    def test_http_error_fails_closed(self) -> None:
        def failing_opener(request: Any, *, timeout: float) -> object:
            del request, timeout
            raise urllib.error.HTTPError(
                "http://172.29.20.2:8474/version",
                500,
                "failure",
                {},
                io.BytesIO(b"provider failure"),
            )

        client = ToxiproxyAdminClient(admin_address="172.29.20.2", opener=failing_opener)
        with self.assertRaises(ToxiproxyControlError):
            client.version()


class DockerLifecycleTests(unittest.TestCase):
    def test_start_uses_exact_digest_admin_only_internal_networks_then_data_connect(self) -> None:
        runner = RecordingRunner()
        docker = DockerCli(runner=runner)
        artifact = ToxiproxyArtifact.reviewed("linux/amd64")
        topology = ToxiproxyRunTopology.for_run("run-start")
        container = ToxiproxyContainer(artifact=artifact, topology=topology, docker=docker)

        admin = container.start()
        self.assertIsInstance(admin, ToxiproxyAdminClient)
        commands = runner.commands
        self.assertEqual(commands[0][1:4], ["pull", "--platform", "linux/amd64"])
        self.assertEqual(commands[0][4], artifact.image_ref)
        self.assertIn(
            [
                "docker",
                "network",
                "create",
                "--internal",
                "--subnet",
                topology.admin_subnet,
                topology.admin_network,
            ],
            commands,
        )
        self.assertIn(
            [
                "docker",
                "network",
                "create",
                "--internal",
                "--subnet",
                topology.data_subnet,
                topology.data_network,
            ],
            commands,
        )

        run_command = next(command for command in commands if command[1] == "run")
        self.assertIn(artifact.image_ref, run_command)
        self.assertIn("--read-only", run_command)
        self.assertIn("--cap-drop=ALL", run_command)
        self.assertIn("--security-opt=no-new-privileges", run_command)
        self.assertIn(topology.admin_network, run_command)
        self.assertIn(topology.admin_address, run_command)
        self.assertNotIn(topology.data_network, run_command)
        self.assertIn(f"-host={topology.admin_address}", run_command)

        connect_command = next(command for command in commands if command[1:3] == ["network", "connect"])
        self.assertIn(topology.data_network, connect_command)
        self.assertIn(topology.data_address, connect_command)

    def test_partial_start_failure_runs_cleanup(self) -> None:
        runner = RecordingRunner(fail_on_prefix=("network", "connect"))
        docker = DockerCli(runner=runner)
        container = ToxiproxyContainer(
            artifact=ToxiproxyArtifact.reviewed("linux/amd64"),
            topology=ToxiproxyRunTopology.for_run("partial-failure"),
            docker=docker,
        )
        with self.assertRaises(ToxiproxyControlError):
            container.start()
        self.assertTrue(any(command[1:3] == ["rm", "-f"] for command in runner.commands))
        self.assertGreaterEqual(sum(command[1:3] == ["network", "rm"] for command in runner.commands), 2)

    def test_cleanup_and_residual_detection_do_not_retry_unboundedly(self) -> None:
        runner = RecordingRunner()
        topology = ToxiproxyRunTopology.for_run("cleanup")
        container = ToxiproxyContainer(
            artifact=ToxiproxyArtifact.reviewed("linux/amd64"),
            topology=topology,
            docker=DockerCli(runner=runner),
        )
        self.assertEqual(container.cleanup(), ())
        self.assertEqual(container.cleanup(), ())
        self.assertEqual(container.residual_resources(), ())

    def test_docker_execution_failure_is_typed(self) -> None:
        def broken_runner(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            del kwargs
            raise FileNotFoundError(command[0])

        docker = DockerCli(runner=broken_runner)
        with self.assertRaises(ToxiproxyPrerequisiteError):
            docker.run("version")


if __name__ == "__main__":
    unittest.main()
