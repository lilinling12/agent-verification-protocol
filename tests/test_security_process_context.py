from __future__ import annotations

import os
import unittest
from contextlib import contextmanager
from typing import Iterator

from avp_ref.security import ManagedSubjectProcessContext


@contextmanager
def _environment(name: str, value: str) -> Iterator[None]:
    previous = os.environ.get(name)
    os.environ[name] = value
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = previous


class ManagedSubjectProcessContextTest(unittest.TestCase):
    def test_evaluator_secret_is_not_inherited_by_default(self) -> None:
        secret = "AVP_TEST_EVALUATOR_SECRET"
        with _environment(secret, "must-not-cross-boundary"):
            result = ManagedSubjectProcessContext().probe_environment_presence((secret,))

        self.assertFalse(result.environment_presence[secret])

    def test_allowlisted_public_context_is_inherited(self) -> None:
        public = "AVP_TEST_PUBLIC_CONTEXT"
        with _environment(public, "safe-to-cross-boundary"):
            result = ManagedSubjectProcessContext(
                inherited_environment=(public,)
            ).probe_environment_presence((public,))

        self.assertTrue(result.environment_presence[public])

    def test_explicitly_allowlisted_name_is_observable(self) -> None:
        secret = "AVP_TEST_EXPLICIT_SECRET"
        with _environment(secret, "deliberately-allowlisted"):
            result = ManagedSubjectProcessContext(
                inherited_environment=(secret,)
            ).probe_environment_presence((secret,))

        self.assertTrue(result.environment_presence[secret])

    def test_duplicate_allowlist_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ManagedSubjectProcessContext(
                inherited_environment=("AVP_DUPLICATE", "AVP_DUPLICATE")
            )


if __name__ == "__main__":
    unittest.main()
