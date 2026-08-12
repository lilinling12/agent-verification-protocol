"""Reference implementation adapter for the language-independent AVP TCK.

This package is intentionally non-normative. It translates TCK vectors into
observations of the Python reference implementation and reports the result
without changing TCK expectations to match implementation behavior.
"""

from .reference import ReferenceTCKAdapter, TCKAdapterError, TCKCaseResult, TCKStatus

__all__ = ["ReferenceTCKAdapter", "TCKAdapterError", "TCKCaseResult", "TCKStatus"]
