"""Subject Adapter SPI for executing Agents under AVP verification."""

from .adapter import SubjectAdapter, SubjectToolGateway
from .errors import (
    SubjectAdapterError,
    SubjectBudgetExceeded,
    SubjectExecutionError,
    SubjectProtocolError,
    SubjectTimeoutError,
    SubjectTransportError,
)
from .http import HTTPSubjectAdapter
from .in_process import InProcessSubjectAdapter
from .models import (
    SubjectDescription,
    SubjectHandle,
    SubjectInvocation,
    SubjectResult,
    SubjectStatus,
    ToolCall,
)

__all__ = [
    "HTTPSubjectAdapter",
    "InProcessSubjectAdapter",
    "SubjectAdapter",
    "SubjectAdapterError",
    "SubjectBudgetExceeded",
    "SubjectDescription",
    "SubjectExecutionError",
    "SubjectHandle",
    "SubjectInvocation",
    "SubjectProtocolError",
    "SubjectResult",
    "SubjectStatus",
    "SubjectTimeoutError",
    "SubjectToolGateway",
    "SubjectTransportError",
    "ToolCall",
]
