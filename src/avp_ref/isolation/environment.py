"""Explicit child-process environment construction for reference isolation seams."""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping

_PLATFORM_PASSTHROUGH = ("SYSTEMROOT", "WINDIR", "LANG", "LC_ALL")


def build_sanitized_environment(
    *,
    explicit: Mapping[str, str] | None = None,
    inherit: Iterable[str] = (),
) -> dict[str, str]:
    """Build a child environment without inheriting the parent by default.

    Only a minimal platform compatibility set, explicitly named inherited
    variables, and explicit values are present. Callers remain responsible for
    deciding which names are safe for their trust boundary.
    """

    result: dict[str, str] = {}
    for name in _PLATFORM_PASSTHROUGH:
        value = os.environ.get(name)
        if value is not None:
            result[name] = value

    for raw_name in inherit:
        if not isinstance(raw_name, str) or not raw_name:
            raise ValueError("inherited environment names must be non-empty strings")
        value = os.environ.get(raw_name)
        if value is not None:
            result[raw_name] = value

    for raw_name, raw_value in (explicit or {}).items():
        if not isinstance(raw_name, str) or not raw_name:
            raise ValueError("explicit environment names must be non-empty strings")
        if not isinstance(raw_value, str):
            raise TypeError("explicit environment values must be strings")
        result[raw_name] = raw_value

    return result
