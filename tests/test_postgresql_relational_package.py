from __future__ import annotations

import subprocess
import sys
import unittest

from avp_ref.tck_adapter.postgresql_relational import (
    PostgreSQLRelationalBackendHarness as PackagedHarness,
)
from avp_ref.tck_adapter.postgresql_relational import (
    PostgreSQLRelationalResource as PackagedResource,
)
from avp_ref.tck_adapter.postgresql_relational_harness import (
    PostgreSQLRelationalBackendHarness as CompatibilityHarness,
)
from avp_ref.tck_adapter.postgresql_relational_harness import (
    PostgreSQLRelationalResource as CompatibilityResource,
)


class PostgreSQLRelationalPackageTest(unittest.TestCase):
    """Lock the non-normative package and optional-dependency compatibility seam."""

    def test_legacy_facade_exports_packaged_classes(self) -> None:
        self.assertIs(PackagedHarness, CompatibilityHarness)
        self.assertIs(PackagedResource, CompatibilityResource)

    def test_import_does_not_eagerly_load_optional_psycopg_driver(self) -> None:
        script = (
            "import sys; "
            "import avp_ref.tck_adapter.postgresql_relational_harness; "
            "assert 'psycopg' not in sys.modules"
        )

        completed = subprocess.run(
            [sys.executable, "-c", script],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)


if __name__ == "__main__":
    unittest.main()
