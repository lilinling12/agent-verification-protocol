"""Deterministic Subject worker invocation for the packet-path evidence lab.

Subject workers cross a deliberate privilege boundary: the evaluator enters the
Subject namespace and ``setpriv`` drops uid/gid and all Linux capabilities before
Python starts. Importing the test-only ``acceptance`` package must therefore not
depend on inherited ``PYTHONPATH`` behavior across that boundary.

This module keeps that binding mechanism-local. It does not provide a generic
process launcher, backend SPI, or provider abstraction.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ..evidence_core import EvidenceMaterializationError

_WORKER_MODULE = "acceptance.network_control.packet_path.worker"
_BOOTSTRAP = (
    "import runpy,sys;"
    "tests_root=sys.argv[1];"
    "module=sys.argv[2];"
    "sys.path.insert(0,tests_root);"
    "sys.argv=[module,*sys.argv[3:]];"
    "runpy.run_module(module,run_name='__main__')"
)


def subject_worker_argv(
    *,
    python_executable: str,
    tests_root: Path,
    worker_args: Sequence[str],
) -> tuple[str, ...]:
    """Build isolated Python argv for one reviewed packet-path Subject worker.

    ``-I`` intentionally ignores caller ``PYTHONPATH`` and user-site state. The
    bootstrap then inserts exactly the reviewed repository ``tests`` directory
    before executing the fixed packet-path worker module. The returned argv still
    requires ``PacketPathController.subject_command`` to apply namespace entry,
    uid/gid drop, capability removal, and no-new-privs.
    """

    if not isinstance(python_executable, str) or not python_executable:
        raise EvidenceMaterializationError(
            "packet-path Subject worker Python executable is required"
        )
    root = Path(tests_root).resolve()
    worker = root / "acceptance" / "network_control" / "packet_path" / "worker.py"
    if not root.is_dir() or not worker.is_file():
        raise EvidenceMaterializationError(
            "packet-path Subject worker requires reviewed tests/acceptance worker"
        )
    args = tuple(worker_args)
    if not args or any(not isinstance(item, str) or not item for item in args):
        raise EvidenceMaterializationError(
            "packet-path Subject worker arguments must be non-empty strings"
        )
    return (
        python_executable,
        "-I",
        "-c",
        _BOOTSTRAP,
        str(root),
        _WORKER_MODULE,
        *args,
    )
