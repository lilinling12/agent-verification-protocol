import unittest

from avp_ref import __version__
from avp_ref.runtime import ReferenceRuntime
from avp_ref.telemetry import NoopTelemetryBridge


class ReferenceRuntimeCapabilitiesTest(unittest.TestCase):
    def test_public_discovery_separates_claim_levels(self) -> None:
        capabilities = ReferenceRuntime().capabilities()

        self.assertEqual("avp", capabilities["protocol"])
        self.assertNotIn("version", capabilities)
        self.assertNotIn("profiles", capabilities)
        self.assertNotIn("features", capabilities)
        self.assertEqual("avp-reference", capabilities["implementation"]["name"])
        self.assertEqual(__version__, capabilities["implementation"]["version"])

        implementation_features = capabilities["implementation_features"]
        self.assertEqual(
            "avp.spec/v0.1",
            implementation_features["scenario_api_version"],
        )
        self.assertEqual(
            "avp.environment/v0.1",
            implementation_features["environment_adapter_spi"],
        )
        self.assertEqual(
            "avp.subject/v0.1",
            implementation_features["subject_adapter_spi"],
        )
        self.assertEqual("2026-07-28", implementation_features["mcp_protocol"])
        self.assertNotIn("oracle_profile", implementation_features)
        self.assertNotIn("evidence_profile", implementation_features)
        self.assertNotIn("isolation", implementation_features)

        instance_configuration = capabilities["instance_configuration"]
        self.assertEqual(
            "avp.oracle/v2",
            instance_configuration["oracle_runner_spi"],
        )
        self.assertIsNone(instance_configuration["telemetry_bridge"])

    def test_public_discovery_reflects_configured_telemetry_bridge(self) -> None:
        capabilities = ReferenceRuntime(NoopTelemetryBridge()).capabilities()

        self.assertEqual(
            "noop-telemetry",
            capabilities["instance_configuration"]["telemetry_bridge"],
        )


if __name__ == "__main__":
    unittest.main()
