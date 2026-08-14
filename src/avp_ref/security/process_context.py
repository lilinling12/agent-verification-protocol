"""Managed Subject child-process context for credential-boundary witnesses."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from avp_ref.isolation import build_sanitized_environment


@dataclass(frozen=True, slots=True)
class SubjectProcessContextResult:
    """Observed environment-presence facts from one managed Subject process."""

    environment_presence: Mapping[str, bool]


class ManagedSubjectProcessContext:
    """Launch a narrow Subject witness with explicit environment inheritance.

    This helper proves credential-context separation only. It does not claim
    network, tenant, filesystem, or hardened sandbox isolation.
    """

    def __init__(self, *, inherited_environment: tuple[str, ...] = ()) -> None:
        if len(inherited_environment) != len(set(inherited_environment)):
            raise ValueError("inherited environment names must be unique")
        if not all(isinstance(name, str) and name for name in inherited_environment):
            raise ValueError("inherited environment names must be non-empty strings")
        self._inherited_environment = tuple(inherited_environment)

    def probe_environment_presence(
        self,
        names: tuple[str, ...],
        *,
        timeout_seconds: float = 5.0,
    ) -> SubjectProcessContextResult:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        if not names or len(names) != len(set(names)):
            raise ValueError("probe names must be non-empty and unique")
        if not all(isinstance(name, str) and name for name in names):
            raise ValueError("probe names must be non-empty strings")

        script = (
            "import json, os, sys; "
            "names=json.loads(sys.argv[1]); "
            "print(json.dumps({name: name in os.environ for name in names}, sort_keys=True))"
        )
        environment = build_sanitized_environment(inherit=self._inherited_environment)
        with tempfile.TemporaryDirectory(prefix="avp-subject-context-") as workdir:
            completed = subprocess.run(
                [sys.executable, "-I", "-B", "-c", script, json.dumps(names)],
                cwd=Path(workdir),
                env=environment,
                shell=False,
                close_fds=True,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )

        if completed.returncode != 0:
            raise RuntimeError(
                "managed Subject process probe failed: "
                f"exit={completed.returncode} stderr={completed.stderr[:512]!r}"
            )
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("managed Subject process emitted invalid JSON") from exc
        if not isinstance(payload, dict) or set(payload) != set(names):
            raise RuntimeError("managed Subject process returned unexpected probe shape")
        if not all(isinstance(value, bool) for value in payload.values()):
            raise RuntimeError("managed Subject process returned non-boolean probe values")
        return SubjectProcessContextResult(dict(payload))
