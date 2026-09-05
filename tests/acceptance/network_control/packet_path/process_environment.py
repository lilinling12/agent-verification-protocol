"""Mechanism-local process environment boundary for packet-path evidence.

Trusted-main packet-path CLIs run with existing root authority and then create
Subject/evaluator worker processes. Those workers need the repository's test-only
``acceptance`` package, but they must not inherit arbitrary caller Python search
paths or GitHub Actions/runtime variables.

This module therefore retains only a small execution allowlist and binds
``PYTHONPATH`` to exactly the reviewed workspace ``tests`` directory. It is not a
generic process sandbox or portable AVP security abstraction.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import MutableMapping

from ..evidence_core import EvidenceMaterializationError

_ENVIRONMENT_ALLOWLIST = frozenset(
    {
        "HOME",
        "LANG",
        "LC_ALL",
        "PATH",
        "PYTHONIOENCODING",
        "PYTHONUTF8",
        "VIRTUAL_ENV",
    }
)


def sanitize_packet_path_process_environment(
    *,
    workspace: Path,
    environment: MutableMapping[str, str] | None = None,
) -> None:
    """Reduce process environment and bind worker imports to reviewed tests.

    ``PYTHONPATH`` is deliberately not caller-retained. The only admitted Python
    search root is ``<workspace>/tests`` so ``acceptance.network_control`` workers
    remain importable after ``sudo`` while arbitrary runner/user paths cannot
    cross the privileged Subject boundary.
    """

    root = Path(workspace).resolve()
    tests = root / "tests"
    acceptance = tests / "acceptance"
    if not root.is_dir() or not tests.is_dir() or not acceptance.is_dir():
        raise EvidenceMaterializationError(
            "packet-path process environment requires reviewed workspace tests/acceptance"
        )

    target = os.environ if environment is None else environment
    retained = {
        key: value
        for key, value in target.items()
        if key in _ENVIRONMENT_ALLOWLIST
    }
    retained["PYTHONPATH"] = str(tests)
    target.clear()
    target.update(retained)
