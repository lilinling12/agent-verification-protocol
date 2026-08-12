"""JSON line protocol helpers for Oracle workers."""

from __future__ import annotations

import json


PROTOCOL = "avp.oracle/v1"


def encode(message: dict) -> str:
    payload = dict(message)
    payload.setdefault("protocol", PROTOCOL)
    return json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"


def decode(line: str) -> dict:
    value = json.loads(line)
    if not isinstance(value, dict):
        raise ValueError("oracle response must be object")
    if value.get("protocol") != PROTOCOL:
        raise ValueError("unsupported oracle protocol")
    return value
