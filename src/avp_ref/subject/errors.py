"""Typed Subject Adapter failures.

Subject infrastructure failures are distinct from task-verdict failures. A
transport timeout, malformed protocol frame, or adapter budget exhaustion must
not be counted as an Agent task failure without explicit policy.
"""


class SubjectAdapterError(RuntimeError):
    """Base class for Subject Adapter failures."""


class SubjectTransportError(SubjectAdapterError):
    """The external subject endpoint could not be reached or returned HTTP failure."""


class SubjectTimeoutError(SubjectTransportError):
    """The subject invocation exceeded its configured transport deadline."""


class SubjectProtocolError(SubjectAdapterError):
    """The subject returned a response that violates avp.subject/v0.1."""


class SubjectExecutionError(SubjectAdapterError):
    """The subject explicitly reported execution failure."""


class SubjectBudgetExceeded(SubjectAdapterError):
    """The subject exceeded the evaluator-owned maximum interaction steps."""
