"""Regression checks for both required HiddenRetry/Fallback faulty assemblies."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import MethodType, SimpleNamespace
from unittest.mock import patch

from acceptance.network_control.evidence_core import (
    ArtifactStore,
    MaterializedEndpoint,
)
from acceptance.network_control.portable_comparator import AttemptObservation
from acceptance.network_control.toxiproxy_binding import (
    DockerCli,
    ToxiproxyRunTopology,
)
from acceptance.network_control.toxiproxy_evidence import PhaseExecution
from acceptance.network_control.toxiproxy_live_lab import (
    LabHelperArtifact,
    ToxiproxyLiveLab,
)
from acceptance.network_control.toxiproxy_negative_assemblies import UpstreamHiddenRetryLiveLab

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_network_control_toxiproxy_evidence.py"


def endpoint(address: str, port: int) -> MaterializedEndpoint:
    return MaterializedEndpoint("ipv4", address, port, "upstream-fixture")


class UpstreamFaultCommandTests(unittest.TestCase):
    def lab(self) -> UpstreamHiddenRetryLiveLab:
        lab = object.__new__(UpstreamHiddenRetryLiveLab)
        lab.topology = ToxiproxyRunTopology.for_run("upstream-hidden-retry")  # type: ignore[attr-defined]
        lab.helper_artifact = LabHelperArtifact.reviewed_amd64()  # type: ignore[attr-defined]
        lab.docker = DockerCli(executable="docker")  # type: ignore[attr-defined]
        return lab

    def test_helper_shares_toxiproxy_namespace_and_has_no_packet_capability(self) -> None:
        lab = self.lab()
        fixture = endpoint(lab.topology.data_address.rsplit(".", 1)[0] + ".3", 42001)
        command = lab._upstream_fault_command("negative-helper", fixture)  # noqa: SLF001

        self.assertIn(f"container:{lab.topology.container_name}", command)
        self.assertIn("--read-only", command)
        self.assertIn("--cap-drop=ALL", command)
        self.assertIn("--security-opt=no-new-privileges", command)
        self.assertNotIn("--cap-add=NET_RAW", command)
        self.assertNotIn("/var/run/docker.sock", " ".join(command))
        self.assertIn(lab.helper_artifact.image_ref, command)

        script = command[-1]
        self.assertIn(repr(lab.topology.data_address), script)
        self.assertIn(repr(fixture.address), script)
        self.assertIn(str(fixture.port), script)
        self.assertIn("s.bind", script)
        self.assertIn("connect_ex", script)

    def test_upstream_variant_suppresses_front_extra_connect_and_injects_inside_window(self) -> None:
        lab = self.lab()
        fixture = endpoint(lab.topology.data_address.rsplit(".", 1)[0] + ".3", 42001)
        lab._materialization = SimpleNamespace(  # type: ignore[attr-defined]
            selected_binding=SimpleNamespace(upstream=fixture)
        )
        commands: list[list[str]] = []

        def run_bounded(self: UpstreamHiddenRetryLiveLab, command: list[str], **_kwargs: object) -> object:
            del self
            commands.append(command)
            return SimpleNamespace(stdout="", stderr="", returncode=0)

        lab._run_bounded = MethodType(run_bounded, lab)  # type: ignore[method-assign]
        attempt = {"attemptId": "attempt-1", "phaseId": "subject-active-cut"}
        visible = MaterializedEndpoint("ipv4", lab.topology.data_address, 41001, "subject-destination")

        with patch.object(
            ToxiproxyLiveLab,
            "_execute_role_exchange",
            return_value={"completed": False},
        ) as parent:
            result = lab._execute_role_exchange(  # noqa: SLF001
                container_name="subject",
                endpoint=visible,
                attempt_document=attempt,
                extra_connect=True,
            )

        self.assertEqual(result, {"completed": False})
        parent.assert_called_once_with(
            container_name="subject",
            endpoint=visible,
            attempt_document=attempt,
            extra_connect=False,
        )
        self.assertEqual(len(commands), 1)
        self.assertIsNotNone(lab._upstream_negative_attempt)  # noqa: SLF001
        assert lab._upstream_negative_attempt is not None  # noqa: SLF001
        self.assertEqual(
            lab._upstream_negative_attempt["variant"],  # noqa: SLF001
            "same-namespace-upstream-extra-connect",
        )

    def test_negative_assembly_marker_is_retained_as_phase_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            lab = self.lab()
            lab.artifact_store = ArtifactStore(Path(temporary))  # type: ignore[attr-defined]
            lab._upstream_negative_attempt = {  # type: ignore[attr-defined]
                "format": "avp-project-hidden-retry-upstream-negative-v0.1",
                "variant": "same-namespace-upstream-extra-connect",
                "attemptId": "attempt-1",
            }
            observation = AttemptObservation(
                phase_id="subject-active-cut",
                path_id="selected-path",
                attempt_id="attempt-1",
                completed=False,
                mismatch_observed=False,
                observation_budget_expired=True,
            )
            base = PhaseExecution(observation=observation)
            with patch.object(ToxiproxyLiveLab, "certified_attempt", return_value=base):
                result = lab.certified_attempt("subject-active-cut", False, None)

            self.assertEqual(len(result.evidence_refs), 1)
            payload = lab.artifact_store.read_verified(result.evidence_refs[0])
            self.assertIn(b"same-namespace-upstream-extra-connect", payload)
            self.assertIsNone(lab._upstream_negative_attempt)  # noqa: SLF001


class HiddenRetryCliVariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("run_network_control_toxiproxy_evidence", SCRIPT)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load TEL-002 evidence runner")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.module = module

    def test_default_hidden_retry_variant_preserves_front_assembly(self) -> None:
        variant, lab_type = self.module._resolve_hidden_retry_variant(  # noqa: SLF001
            negative_mode="HiddenRetry/Fallback",
            requested=None,
        )
        self.assertEqual(variant, "front-extra-connect")
        self.assertIs(lab_type, ToxiproxyLiveLab)

    def test_upstream_variant_selects_same_namespace_faulty_lab(self) -> None:
        variant, lab_type = self.module._resolve_hidden_retry_variant(  # noqa: SLF001
            negative_mode="HiddenRetry/Fallback",
            requested="upstream-extra-connect",
        )
        self.assertEqual(variant, "upstream-extra-connect")
        self.assertIs(lab_type, UpstreamHiddenRetryLiveLab)

    def test_variant_is_rejected_for_unrelated_negative_mode(self) -> None:
        with self.assertRaises(ValueError):
            self.module._resolve_hidden_retry_variant(  # noqa: SLF001
                negative_mode="BypassFault",
                requested="upstream-extra-connect",
            )


if __name__ == "__main__":
    unittest.main()
