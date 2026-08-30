"""Shared support for non-normative Browser acceptance evidence.

This module deliberately contains only evidence-runner mechanics and exact value
helpers needed by the acceptance tests.  It is not packaged with ``avp_ref`` and
must not be imported by the portable TCK.
"""

from __future__ import annotations

import base64
import json
import threading
from collections.abc import Iterable, Sequence
from contextlib import AbstractContextManager
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Final
from urllib.parse import urlsplit


_EVIDENCE_HOSTS: Final[tuple[str, ...]] = (
    "avp.test",
    "sub.avp.test",
    "other.test",
)


class EvidenceHTTPServer(AbstractContextManager["EvidenceHTTPServer"]):
    """Serve deterministic local pages used by browser evidence cases.

    The server never reaches the public Internet.  Hostnames are expected to be
    mapped to 127.0.0.1 by the dedicated evidence workflow so cookie-domain and
    tuple-origin behavior can be exercised with stable synthetic names.
    """

    def __init__(self) -> None:
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _EvidenceRequestHandler)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="avp-browser-evidence-http",
            daemon=True,
        )

    @property
    def port(self) -> int:
        return int(self._server.server_port)

    def url(self, host: str, path: str = "/") -> str:
        """Return one stable local evidence URL for a configured synthetic host."""

        if host not in _EVIDENCE_HOSTS:
            raise ValueError(f"unsupported evidence host: {host}")
        if not path.startswith("/"):
            raise ValueError("evidence path must be absolute")
        return f"http://{host}:{self.port}{path}"

    def __enter__(self) -> "EvidenceHTTPServer":
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


class _EvidenceRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        path = urlsplit(self.path).path
        if path == "/cookie/seed":
            self._send_cookie_seed()
            return
        if path == "/cookie/echo":
            self._send_json(
                {
                    "cookie": self.headers.get("Cookie", ""),
                    "host": self.headers.get("Host", ""),
                }
            )
            return
        if path == "/storage":
            self._send_html("<!doctype html><meta charset='utf-8'><title>AVP storage evidence</title>")
            return
        self._send_text(HTTPStatus.NOT_FOUND, "not found")

    def log_message(self, format: str, *args: object) -> None:
        # Evidence output is emitted explicitly by the unittest runner.  Suppress
        # per-request access logs so CI diagnostics stay focused on failed cases.
        del format, args

    def _send_cookie_seed(self) -> None:
        body = b"cookies seeded"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Set-Cookie", "avp_host_only=host; Path=/")
        self.send_header("Set-Cookie", "avp_domain=domain; Domain=avp.test; Path=/")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, document: object) -> None:
        body = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, status: HTTPStatus, text: str) -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def parse_cookie_header(header: str) -> dict[str, str]:
    """Parse the simple synthetic Cookie header emitted by the local fixture."""

    result: dict[str, str] = {}
    for field in header.split(";"):
        field = field.strip()
        if not field:
            continue
        name, separator, value = field.partition("=")
        if not separator:
            raise ValueError(f"malformed synthetic Cookie field: {field!r}")
        result[name] = value
    return result


def encode_domstring_code_units(code_units: Sequence[int]) -> str:
    """Encode exact unsigned UTF-16 code units per the AEP-0011 Proposed rule."""

    raw = bytearray()
    for unit in code_units:
        if isinstance(unit, bool) or not isinstance(unit, int) or not 0 <= unit <= 0xFFFF:
            raise ValueError(f"invalid UTF-16 code unit: {unit!r}")
        raw.extend(unit.to_bytes(2, byteorder="big", signed=False))
    return base64.urlsafe_b64encode(bytes(raw)).rstrip(b"=").decode("ascii")


def decode_domstring_code_units(encoded: str) -> tuple[int, ...]:
    """Decode the AEP-0011 evidence representation back to exact code units."""

    if not encoded.isascii():
        raise ValueError("DOMString evidence encoding must be ASCII")
    padding = "=" * ((4 - len(encoded) % 4) % 4)
    try:
        raw = base64.b64decode(
            encoded + padding,
            altchars=b"-_",
            validate=True,
        )
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid unpadded base64url DOMString encoding") from exc
    if len(raw) % 2:
        raise ValueError("DOMString evidence bytes must contain whole UTF-16 code units")
    return tuple(int.from_bytes(raw[index : index + 2], "big") for index in range(0, len(raw), 2))


def canonical_domstring_order(values: Iterable[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    """Order DOMString code-unit sequences lexicographically, shorter prefix first."""

    return tuple(sorted(tuple(value) for value in values))
