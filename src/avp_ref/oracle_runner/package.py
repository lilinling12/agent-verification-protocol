"""Oracle package identity and deterministic input selection helpers."""

from __future__ import annotations

import hashlib
import importlib.util
import re
from pathlib import Path
from typing import Mapping

from .errors import OracleConfigurationError
from .models import OraclePackage

_ENTRYPOINT = re.compile(r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z_]\w*$")


def parse_entrypoint(entrypoint: str) -> tuple[str, str]:
    if not _ENTRYPOINT.fullmatch(entrypoint):
        raise OracleConfigurationError(f"invalid Oracle entrypoint: {entrypoint!r}")
    module_name, callable_name = entrypoint.split(":", 1)
    return module_name, callable_name


def module_code_digest(entrypoint: str) -> str:
    """Hash the complete source module without importing/evaluating its code."""

    module_name, _ = parse_entrypoint(entrypoint)
    spec = importlib.util.find_spec(module_name)
    if spec is None or spec.origin is None:
        raise OracleConfigurationError(f"Oracle module cannot be resolved: {module_name}")
    source = Path(spec.origin)
    if not source.is_file():
        raise OracleConfigurationError(f"Oracle module has no hashable source file: {module_name}")
    return "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()


def build_oracle_package(
    *,
    oracle_id: str,
    version: str,
    entrypoint: str,
    projections: tuple[str, ...],
    input_pointers: Mapping[str, str] | None = None,
) -> OraclePackage:
    return OraclePackage(
        oracle_id=oracle_id,
        version=version,
        entrypoint=entrypoint,
        code_digest=module_code_digest(entrypoint),
        projections=projections,
        input_pointers=input_pointers or {},
    )


def resolve_json_pointer(document: object, pointer: str) -> object:
    """Resolve an RFC 6901 pointer without adding a general expression engine."""

    if not pointer.startswith("/"):
        raise OracleConfigurationError(f"Oracle input pointer must start with '/': {pointer!r}")
    current = document
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping):
            if token not in current:
                raise OracleConfigurationError(f"Oracle input pointer does not resolve: {pointer}")
            current = current[token]
            continue
        if isinstance(current, (list, tuple)):
            try:
                index = int(token)
                current = current[index]
            except (ValueError, IndexError) as exc:
                raise OracleConfigurationError(f"Oracle array input pointer does not resolve: {pointer}") from exc
            continue
        raise OracleConfigurationError(f"Oracle input pointer traverses a scalar: {pointer}")
    return current
