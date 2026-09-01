"""Evaluator-only Playwright proof for material IndexedDB excluded state.

IndexedDB is outside the Browser v0.1 selected representation. This concrete
control proves material interference only when a controlled IndexedDB record
changes an application-like browser decision while the canonical selected
cookie/localStorage digest remains unchanged.

Observation is deliberately side-effect free when the database is absent:
``indexedDB.databases()`` is consulted before ``indexedDB.open()`` so the proof
does not manufacture the residue it is trying to detect.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from avp_ref.tck_adapter.browser_harness import (
    BrowserVerificationError,
    canonical_state_image_digest,
)

from .backend import PlaywrightBrowserResource, _project_selected_state


@dataclass(frozen=True, slots=True)
class IndexedDBObservation:
    """Concrete observation of controlled IndexedDB state and dependent behavior."""

    database_exists: bool
    stored_value: str | None
    behavior_result: str


@dataclass(frozen=True, slots=True)
class IndexedDBInterferenceEvidence:
    """Evidence that IndexedDB changed behavior without changing selected state."""

    resource_handle_id: str
    origin: str
    surface: str
    database_name: str
    store_name: str
    selected_digest_before: str
    selected_digest_after: str
    baseline: IndexedDBObservation
    residual: IndexedDBObservation


class PlaywrightBrowserIndexedDBControl:
    """Privileged evaluator control for one real IndexedDB interference proof."""

    _SURFACE = "indexeddb"

    @staticmethod
    def _resource(sut: Any) -> PlaywrightBrowserResource:
        if not isinstance(sut, PlaywrightBrowserResource):
            raise TypeError("Playwright IndexedDB control received a foreign Browser SUT")
        sut._ensure_live()
        return sut

    @staticmethod
    def _require_selected_origin(resource: PlaywrightBrowserResource, origin: str) -> None:
        if not isinstance(origin, str) or not origin:
            raise BrowserVerificationError("IndexedDB proof origin must be a non-empty string")
        resource._verifier.verify_canonical_origin(origin)
        if origin not in set(resource._fixture.manifest["localStorageOrigins"]):
            raise BrowserVerificationError(
                "IndexedDB proof origin is outside Manifest localStorage selection"
            )

    @staticmethod
    def _require_nonempty(value: str, field: str) -> None:
        if not isinstance(value, str) or not value:
            raise BrowserVerificationError(f"{field} must be a non-empty string")

    @staticmethod
    def _selected_digest(resource: PlaywrightBrowserResource) -> str:
        image = _project_selected_state(resource, resource._fixture)
        return canonical_state_image_digest(
            image,
            resource._fixture.manifest,
            resource._verifier,
        )

    def observe(
        self,
        sut: Any,
        *,
        origin: str,
        database_name: str,
        store_name: str,
        key: str,
        clean_behavior: str,
        residual_behavior: str,
    ) -> IndexedDBObservation:
        """Observe controlled IndexedDB behavior without creating a missing database."""

        resource = self._resource(sut)
        self._require_selected_origin(resource, origin)
        for field, value in (
            ("database_name", database_name),
            ("store_name", store_name),
            ("key", key),
            ("clean_behavior", clean_behavior),
            ("residual_behavior", residual_behavior),
        ):
            self._require_nonempty(value, field)
        if clean_behavior == residual_behavior:
            raise BrowserVerificationError(
                "IndexedDB behavior proof requires distinct clean and residual outcomes"
            )

        page = resource._context.new_page()
        try:
            page.goto(origin + "/state", wait_until="domcontentloaded")
            result = page.evaluate(
                """async ([dbName, storeName, key, cleanBehavior, residualBehavior]) => {
                  if (typeof indexedDB.databases !== 'function') {
                    throw new Error('indexedDB.databases() is required for side-effect-free observation');
                  }
                  const databases = await indexedDB.databases();
                  const exists = databases.some(database => database.name === dbName);
                  if (!exists) {
                    return {
                      databaseExists: false,
                      storedValue: null,
                      behaviorResult: cleanBehavior,
                    };
                  }

                  const value = await new Promise((resolve, reject) => {
                    const request = indexedDB.open(dbName);
                    request.onerror = () => reject(request.error);
                    request.onsuccess = () => {
                      const db = request.result;
                      if (!db.objectStoreNames.contains(storeName)) {
                        db.close();
                        resolve(null);
                        return;
                      }
                      const tx = db.transaction(storeName, 'readonly');
                      const get = tx.objectStore(storeName).get(key);
                      get.onsuccess = () => {
                        const stored = get.result ?? null;
                        db.close();
                        resolve(stored);
                      };
                      get.onerror = () => {
                        db.close();
                        reject(get.error);
                      };
                    };
                  });
                  return {
                    databaseExists: true,
                    storedValue: value === null ? null : String(value),
                    behaviorResult: value === null ? cleanBehavior : residualBehavior,
                  };
                }""",
                [database_name, store_name, key, clean_behavior, residual_behavior],
            )
        finally:
            page.close()

        if not isinstance(result, dict):
            raise BrowserVerificationError("IndexedDB observation is malformed")
        database_exists = result.get("databaseExists")
        stored_value = result.get("storedValue")
        behavior_result = result.get("behaviorResult")
        if not isinstance(database_exists, bool):
            raise BrowserVerificationError("IndexedDB existence observation is malformed")
        if stored_value is not None and not isinstance(stored_value, str):
            raise BrowserVerificationError("IndexedDB stored value observation is malformed")
        if not isinstance(behavior_result, str) or not behavior_result:
            raise BrowserVerificationError("IndexedDB behavior observation is malformed")
        return IndexedDBObservation(
            database_exists=database_exists,
            stored_value=stored_value,
            behavior_result=behavior_result,
        )

    def prove_interference(
        self,
        sut: Any,
        *,
        origin: str,
        database_name: str,
        store_name: str,
        key: str,
        stored_value: str,
        clean_behavior: str,
        residual_behavior: str,
    ) -> IndexedDBInterferenceEvidence:
        """Seed one controlled record and prove behavior changes with selected state equal."""

        resource = self._resource(sut)
        self._require_selected_origin(resource, origin)
        for field, value in (
            ("database_name", database_name),
            ("store_name", store_name),
            ("key", key),
            ("stored_value", stored_value),
            ("clean_behavior", clean_behavior),
            ("residual_behavior", residual_behavior),
        ):
            self._require_nonempty(value, field)
        if clean_behavior == residual_behavior:
            raise BrowserVerificationError(
                "IndexedDB behavior proof requires distinct clean and residual outcomes"
            )

        selected_before = self._selected_digest(resource)
        baseline = self.observe(
            resource,
            origin=origin,
            database_name=database_name,
            store_name=store_name,
            key=key,
            clean_behavior=clean_behavior,
            residual_behavior=residual_behavior,
        )
        if baseline.database_exists or baseline.stored_value is not None:
            raise BrowserVerificationError(
                "IndexedDB interference proof requires a clean isolated Browser resource"
            )
        if baseline.behavior_result != clean_behavior:
            raise BrowserVerificationError(
                "IndexedDB clean behavior did not match the expected baseline"
            )

        page = resource._context.new_page()
        try:
            page.goto(origin + "/state", wait_until="domcontentloaded")
            seeded = page.evaluate(
                """([dbName, storeName, key, value]) => new Promise((resolve, reject) => {
                  const request = indexedDB.open(dbName, 1);
                  request.onupgradeneeded = () => {
                    if (!request.result.objectStoreNames.contains(storeName)) {
                      request.result.createObjectStore(storeName);
                    }
                  };
                  request.onerror = () => reject(request.error);
                  request.onsuccess = () => {
                    const db = request.result;
                    const tx = db.transaction(storeName, 'readwrite');
                    tx.objectStore(storeName).put(value, key);
                    tx.oncomplete = () => { db.close(); resolve(true); };
                    tx.onerror = () => { db.close(); reject(tx.error); };
                    tx.onabort = () => { db.close(); reject(tx.error); };
                  };
                })""",
                [database_name, store_name, key, stored_value],
            )
            if seeded is not True:
                raise BrowserVerificationError("controlled IndexedDB write did not complete")
        finally:
            page.close()

        residual = self.observe(
            resource,
            origin=origin,
            database_name=database_name,
            store_name=store_name,
            key=key,
            clean_behavior=clean_behavior,
            residual_behavior=residual_behavior,
        )
        selected_after = self._selected_digest(resource)

        if selected_after != selected_before:
            raise BrowserVerificationError(
                "IndexedDB setup changed selected Browser authoritative state"
            )
        if not residual.database_exists:
            raise BrowserVerificationError("controlled IndexedDB database is not observable")
        if residual.stored_value != stored_value:
            raise BrowserVerificationError(
                "controlled IndexedDB record is not observed losslessly"
            )
        if residual.behavior_result != residual_behavior:
            raise BrowserVerificationError(
                "IndexedDB residue did not produce the expected behavior change"
            )
        if residual.behavior_result == baseline.behavior_result:
            raise BrowserVerificationError(
                "IndexedDB-dependent behavior remained equivalent to the clean baseline"
            )

        resource._excluded_state_interfering = True
        return IndexedDBInterferenceEvidence(
            resource_handle_id=resource.handle_id,
            origin=origin,
            surface=self._SURFACE,
            database_name=database_name,
            store_name=store_name,
            selected_digest_before=selected_before,
            selected_digest_after=selected_after,
            baseline=baseline,
            residual=residual,
        )
