import os
import unittest
from contextlib import contextmanager
from dataclasses import replace

from avp_ref import __version__
from avp_ref.canonical import digest
from avp_ref.oracle import (
    broken_oracle_package,
    environment_probe_oracle_package,
    invalid_output_oracle_package,
    noisy_oracle_package,
    slow_oracle_package,
)
from avp_ref.oracle_runner import (
    OracleEvaluationContext,
    OracleExecutionStatus,
    OracleRequest,
    OracleSandboxPolicy,
    ProjectionSnapshot,
    SubprocessOracleRunner,
)
from avp_ref.oracle_runner.protocol import PROTOCOL_VERSION


@contextmanager
def _environment(name: str, value: str):
    previous = os.environ.get(name)
    os.environ[name] = value
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = previous


def _context() -> OracleEvaluationContext:
    data: list[object] = []
    projection = ProjectionSnapshot("commerce.refunds", data, digest(data))
    return OracleEvaluationContext(
        episode_id="ep_oracle_test",
        scenario_instance_digest="sha256:" + "1" * 64,
        manifest_digest="sha256:" + "2" * 64,
        inputs={},
        projections={"commerce.refunds": projection},
    )


def _runner(**overrides) -> SubprocessOracleRunner:
    policy = OracleSandboxPolicy(
        timeout_seconds=overrides.pop("timeout_seconds", 2.0),
        cpu_seconds=overrides.pop("cpu_seconds", 1),
        memory_bytes=overrides.pop("memory_bytes", 256 * 1024 * 1024),
        max_file_bytes=overrides.pop("max_file_bytes", 4096),
        max_open_files=overrides.pop("max_open_files", 64),
        max_request_bytes=overrides.pop("max_request_bytes", 1024 * 1024),
        max_response_bytes=overrides.pop("max_response_bytes", 4096),
        enforce_resource_limits=overrides.pop("enforce_resource_limits", os.name == "posix"),
        **overrides,
    )
    return SubprocessOracleRunner(policy)


def _execute(runner: SubprocessOracleRunner, package):
    return runner.evaluate(OracleRequest("oracle_req_test", package, _context()))


class OracleIsolationTest(unittest.TestCase):
    def test_runner_identity_binds_worker_code_and_allowlist(self):
        description = _runner().describe()
        self.assertTrue(description.worker_code_digest.startswith("sha256:"))
        self.assertEqual(("avp_ref.",), description.allowed_module_prefixes)
        self.assertTrue(description.identity_digest.startswith("sha256:"))

    def test_runner_release_identity_matches_distribution_without_relabeling_protocol(self):
        description = _runner().describe()
        self.assertEqual(__version__, description.version)
        self.assertEqual(PROTOCOL_VERSION, description.protocol_version)

        stale_release_identity = replace(description, version="0.2.0-alpha.8")
        self.assertNotEqual(description.identity_digest, stale_release_identity.identity_digest)

    def test_oracle_crash_is_classified_and_artifacted(self):
        execution = _execute(_runner(), broken_oracle_package())
        self.assertIs(OracleExecutionStatus.CRASHED, execution.status)
        self.assertIs(OracleExecutionStatus.CRASHED, execution.artifact.status)
        self.assertIsNotNone(execution.artifact.exit_code)

    def test_invalid_oracle_output_is_protocol_error(self):
        execution = _execute(_runner(), invalid_output_oracle_package())
        self.assertIs(OracleExecutionStatus.PROTOCOL_ERROR, execution.status)
        self.assertIs(OracleExecutionStatus.PROTOCOL_ERROR, execution.artifact.status)

    def test_timeout_kills_worker_and_preserves_artifact(self):
        execution = _execute(_runner(timeout_seconds=0.1), slow_oracle_package())
        self.assertIs(OracleExecutionStatus.TIMEOUT, execution.status)
        self.assertGreaterEqual(execution.artifact.duration_ms, 50)

    def test_code_digest_tampering_is_security_violation(self):
        package = replace(broken_oracle_package(), code_digest="sha256:" + "0" * 64)
        execution = _execute(_runner(), package)
        self.assertIs(OracleExecutionStatus.SECURITY_VIOLATION, execution.status)
        self.assertEqual(package.code_digest, execution.artifact.oracle_code_digest)

    def test_parent_secret_is_not_inherited_by_default(self):
        with _environment("AVP_TEST_SECRET", "must-not-cross-boundary"):
            execution = _execute(_runner(), environment_probe_oracle_package())
        self.assertIs(OracleExecutionStatus.SUCCESS, execution.status)
        self.assertEqual("PASS", execution.results[0].verdict)

    def test_excessive_stdout_is_security_violation_with_artifact(self):
        execution = _execute(
            _runner(max_response_bytes=512, max_file_bytes=4096),
            noisy_oracle_package(),
        )
        self.assertIs(OracleExecutionStatus.SECURITY_VIOLATION, execution.status)
        self.assertTrue(execution.artifact.stdout_digest.startswith("sha256:"))
        self.assertTrue(execution.artifact.stderr_digest.startswith("sha256:"))

    def test_context_surface_contains_no_live_runtime_handles(self):
        context = _context().to_dict()
        self.assertEqual(
            {"episode_id", "scenario_instance_digest", "manifest_digest", "inputs", "projections"},
            set(context),
        )
        forbidden = {"runtime", "environment_handle", "agent_report", "prompt", "tool_history"}
        self.assertTrue(forbidden.isdisjoint(context))


if __name__ == "__main__":
    unittest.main()
