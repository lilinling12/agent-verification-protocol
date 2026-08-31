"""Evaluator-only Playwright control for positive Browser settlement evidence.

This module deliberately does not define settlement semantics. The provider-neutral
``BrowserSettlementLedger`` remains the authority for admission closure, accepted
profile-relevant work, and terminal outcomes. This control only creates and observes
one concrete delayed selected-state mutation in a real Playwright Browser resource.

Provider network-idle can be observed as negative evidence, but it is never exposed
as a settlement predicate and never marks a mutation terminal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from avp_ref.tck_adapter.browser_harness import (
    BrowserHarnessError,
    BrowserVerificationError,
    decode_dom_string_code_units,
)

from .backend import PlaywrightBrowserResource


@dataclass(slots=True)
class _MutationSession:
    resource_handle_id: str
    page: Any


class PlaywrightBrowserMutationControl:
    """Privileged evaluator control for explicit real-browser mutation terminals."""

    def __init__(self) -> None:
        self._sessions: dict[tuple[str, str], _MutationSession] = {}

    @staticmethod
    def _resource(sut: Any) -> PlaywrightBrowserResource:
        if not isinstance(sut, PlaywrightBrowserResource):
            raise TypeError("Playwright mutation control received a foreign Browser SUT")
        sut._ensure_live()
        return sut

    @staticmethod
    def _mutation_key(
        resource: PlaywrightBrowserResource,
        mutation_id: str,
    ) -> tuple[str, str]:
        if not isinstance(mutation_id, str) or not mutation_id:
            raise BrowserVerificationError("mutation id must be a non-empty string")
        return resource.handle_id, mutation_id

    @staticmethod
    def _entry_payload(entry: Mapping[str, str]) -> dict[str, list[int]]:
        if set(entry) != {"key", "value"}:
            raise BrowserVerificationError("delayed mutation entry shape must be key/value")
        return {
            "key": list(decode_dom_string_code_units(entry["key"])),
            "value": list(decode_dom_string_code_units(entry["value"])),
        }

    def start_delayed_local_storage_mutation(
        self,
        sut: Any,
        *,
        mutation_id: str,
        origin: str,
        entry: Mapping[str, str],
        delay_ms: int,
    ) -> None:
        """Start one accepted mutation whose terminal predicate is browser-observable.

        The caller must register ``mutation_id`` with ``BrowserSettlementLedger``
        before invoking this method. The control intentionally does not receive or
        mutate the ledger, preventing provider mechanics from self-certifying
        settlement.
        """

        resource = self._resource(sut)
        key = self._mutation_key(resource, mutation_id)
        if key in self._sessions:
            raise BrowserVerificationError(
                f"duplicate Browser mutation id: {mutation_id}"
            )
        if origin not in set(resource._fixture.manifest["localStorageOrigins"]):
            raise BrowserVerificationError(
                "delayed mutation origin is outside Manifest selection"
            )
        if (
            isinstance(delay_ms, bool)
            or not isinstance(delay_ms, int)
            or not 1 <= delay_ms <= 10_000
        ):
            raise BrowserVerificationError(
                "delayed mutation delay_ms must be an integer in [1, 10000]"
            )

        payload = self._entry_payload(entry)
        page = resource._context.new_page()
        try:
            page.goto(origin + "/", wait_until="domcontentloaded")
            page.evaluate(
                """
                ([payload, delayMs]) => {
                  const text = units => String.fromCharCode(...units);
                  window.__avpMutationTerminal = false;
                  setTimeout(() => {
                    localStorage.setItem(text(payload.key), text(payload.value));
                    window.__avpMutationTerminal = true;
                  }, delayMs);
                }
                """,
                [payload, delay_ms],
            )
        except Exception:
            page.close()
            raise
        self._sessions[key] = _MutationSession(
            resource_handle_id=resource.handle_id,
            page=page,
        )

    def observe_network_idle_before_terminal(
        self,
        sut: Any,
        mutation_id: str,
    ) -> bool:
        """Return whether provider network-idle occurred while work was unresolved.

        This method exists only to prove that network-idle is insufficient. Its
        return value must never be used as a positive settlement witness.
        """

        session = self._session(sut, mutation_id)
        session.page.wait_for_load_state("networkidle")
        return not bool(
            session.page.evaluate("window.__avpMutationTerminal === true")
        )

    def is_terminal(self, sut: Any, mutation_id: str) -> bool:
        session = self._session(sut, mutation_id)
        return bool(session.page.evaluate("window.__avpMutationTerminal === true"))

    def wait_for_terminal(self, sut: Any, mutation_id: str) -> None:
        """Wait only on the explicit mutation terminal predicate."""

        session = self._session(sut, mutation_id)
        session.page.wait_for_function("window.__avpMutationTerminal === true")
        if not self.is_terminal(sut, mutation_id):
            raise BrowserVerificationError(
                "explicit Browser mutation terminal was not established"
            )

    def release_mutation(self, sut: Any, mutation_id: str) -> None:
        resource = self._resource(sut)
        key = self._mutation_key(resource, mutation_id)
        session = self._sessions.pop(key, None)
        if session is None:
            return
        session.page.close()

    def close(self) -> None:
        sessions = tuple(self._sessions.values())
        self._sessions.clear()
        for session in sessions:
            session.page.close()

    def _session(self, sut: Any, mutation_id: str) -> _MutationSession:
        resource = self._resource(sut)
        key = self._mutation_key(resource, mutation_id)
        try:
            session = self._sessions[key]
        except KeyError as exc:
            raise BrowserHarnessError(
                f"unknown Browser mutation id: {mutation_id}"
            ) from exc
        if session.resource_handle_id != resource.handle_id:
            raise BrowserVerificationError("Browser mutation belongs to another resource")
        return session
