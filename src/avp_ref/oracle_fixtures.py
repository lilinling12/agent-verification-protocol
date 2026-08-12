"""Conformance-only Oracle entrypoints used to exercise isolation failures."""

from __future__ import annotations

import os
import time

from avp_ref.models import VerificationResult
from avp_ref.oracle_runner import OracleEvaluationContext, OracleEvaluationOutput


def timeout_oracle(context: OracleEvaluationContext) -> OracleEvaluationOutput:
    time.sleep(30)
    return OracleEvaluationOutput(())


def environment_probe_oracle(context: OracleEvaluationContext) -> OracleEvaluationOutput:
    secret_name = str(context.inputs.get("secret_name", "AVP_TEST_PARENT_SECRET"))
    inherited = secret_name in os.environ
    result = VerificationResult(
        "oracle.parent_secret_not_inherited",
        "security.isolation",
        "FAIL" if inherited else "PASS",
        "critical",
        "oracle_isolation_probe",
        "oracle-env-probe@0.1.0",
    )
    return OracleEvaluationOutput((result,))


def context_surface_oracle(context: OracleEvaluationContext) -> OracleEvaluationOutput:
    forbidden = ("agent_report", "events", "telemetry", "agent_system", "environment")
    leaked = any(hasattr(context, name) for name in forbidden)
    return OracleEvaluationOutput((VerificationResult(
        "oracle.context_surface",
        "security.isolation",
        "FAIL" if leaked else "PASS",
        "critical",
        "oracle_context_probe",
        "oracle-context-probe@0.1.0",
    ),))
