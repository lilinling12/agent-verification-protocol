"""Reference adapter and runner for the language-independent AVP TCK.

Nothing in this package is normative. The specification, requirement index,
and TCK resources remain authoritative over the Python implementation.
"""

from .loader import LoadedTCKCase, TCKRepository
from .models import TCKAdapterError, TCKCaseResult, TCKStatus
from .reference import ReferenceTCKAdapter
from .report import build_report
from .runner import TCKRunResult, TCKRunner
from .schema import load_report_schema, validate_report

__all__ = [
    "LoadedTCKCase",
    "ReferenceTCKAdapter",
    "TCKAdapterError",
    "TCKCaseResult",
    "TCKRepository",
    "TCKRunResult",
    "TCKRunner",
    "TCKStatus",
    "build_report",
    "load_report_schema",
    "validate_report",
]
