import unittest

from avp_ref import __version__
from avp_ref.runtime import ReferenceRuntime


class ReferenceRuntimeCapabilitiesTest(unittest.TestCase):
    def test_public_discovery_does_not_self_assert_tck_profiles(self) -> None:
        capabilities = ReferenceRuntime().capabilities()

        self.assertNotIn("profiles", capabilities)
        self.assertEqual("avp-reference", capabilities["implementation"]["name"])
        self.assertEqual(__version__, capabilities["implementation"]["version"])
        self.assertIn("features", capabilities)


if __name__ == "__main__":
    unittest.main()
