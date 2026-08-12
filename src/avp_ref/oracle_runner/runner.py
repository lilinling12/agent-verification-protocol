"""Oracle execution boundary."""

from __future__ import annotations

from typing import Protocol

from .models import OracleExecutionResult, OracleRequest


class OracleRunner(Protocol):
    """Executes Oracle evaluation behind an explicit trust boundary."""

    def evaluate(self, request: OracleRequest) -> OracleExecutionResult:
        ...
