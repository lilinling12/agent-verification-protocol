"""Typed configuration and trust-boundary failures for Oracle runners."""


class OracleRunnerError(RuntimeError):
    """Base class for local Oracle runner configuration failures."""


class OracleConfigurationError(OracleRunnerError):
    """The requested Oracle package or runner configuration is invalid."""


class OracleSecurityError(OracleRunnerError):
    """A trust-boundary or sandbox policy check failed before evaluation."""


class OracleProtocolError(OracleRunnerError):
    """The Oracle worker protocol is malformed or inconsistent."""
