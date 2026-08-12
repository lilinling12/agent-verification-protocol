"""Oracle execution boundary."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import OracleExecutionResult, OracleRequest, OracleRunnerDescription


@runtime_checkable
class OracleRunner(Protocol):
    """Execute Oracle code behind an explicit evaluator trust boundary."""

    def describe(self) -> OracleRunnerDescription: ...

    def evaluate(self, request: OracleRequest) -> OracleExecutionResult: ...
