"""Concrete Browser security/visibility evidence for AVP-BROWSER-019.

The Subject-facing object in this module deliberately contains only one
Scenario-authorized observation value. BrowserContext, Page, resource handles,
privileged lifecycle operations, evaluator-private authoritative state, and
artifact retrieval authority never cross that boundary.

Artifact identity and retrieval authority are also kept distinct. A SHA-256
identity can name retained bytes, but only an evaluator-owned opaque capability
created by this control authorizes retrieval. Redacted bytes are retained as a
separate Artifact identity.

This module is concrete reference implementation evidence. It does not define a
new portable Subject automation API or a second AVP security model.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from avp_ref.tck_adapter.browser_harness import BrowserVerificationError

from .backend import PlaywrightBrowserFixtureControl, PlaywrightBrowserResource


@dataclass(frozen=True, slots=True)
class BrowserSubjectObservation:
    """Exact Subject-visible Browser surface for the controlled security proof."""

    value: str


@dataclass(frozen=True, slots=True)
class BrowserArtifactLocator:
    """Artifact identity only; deliberately carries no retrieval authority."""

    digest: str


@dataclass(frozen=True, slots=True)
class BrowserArtifactAuthorization:
    """Opaque evaluator-owned retrieval authority distinct from Artifact identity."""

    _token: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class BrowserRetainedArtifact:
    """Evaluator-side retained Artifact record used by the security proof."""

    locator: BrowserArtifactLocator
    authorization: BrowserArtifactAuthorization = field(repr=False)


class PlaywrightBrowserSecurityControl:
    """Evaluator/Control operations for Browser visibility-separation evidence."""

    def __init__(self) -> None:
        self._fixture_control = PlaywrightBrowserFixtureControl()
        self._artifact_bytes: dict[str, bytes] = {}
        self._artifact_authorizations: dict[str, set[str]] = {}

    @staticmethod
    def _resource(sut: Any) -> PlaywrightBrowserResource:
        if not isinstance(sut, PlaywrightBrowserResource):
            raise TypeError("Playwright Browser security control received a foreign SUT")
        sut._ensure_live()
        return sut

    @staticmethod
    def _selected_origin(resource: PlaywrightBrowserResource, origin: str) -> None:
        if not isinstance(origin, str) or not origin:
            raise BrowserVerificationError("Browser security origin must be non-empty")
        resource._verifier.verify_canonical_origin(origin)
        if origin not in set(resource._fixture.manifest["localStorageOrigins"]):
            raise BrowserVerificationError(
                "Browser security origin is outside Manifest localStorage selection"
            )

    def seed_evaluator_private_state(
        self,
        sut: Any,
        *,
        origin: str,
        cookie: Mapping[str, Any],
        local_storage: Sequence[Mapping[str, str]],
    ) -> None:
        """Seed authoritative evaluator-private state through privileged control only."""

        resource = self._resource(sut)
        self._selected_origin(resource, origin)
        self._fixture_control.seed_cookie(resource, cookie)
        self._fixture_control.seed_local_storage(resource, origin, local_storage)

    def observe_subject_surface(
        self,
        sut: Any,
        *,
        subject_origin: str,
        path: str,
        expected_authorized_value: str,
    ) -> BrowserSubjectObservation:
        """Return only the explicitly authorized observation to the Subject boundary."""

        resource = self._resource(sut)
        self._selected_origin(resource, subject_origin)
        if not isinstance(path, str) or not path.startswith("/"):
            raise BrowserVerificationError("Subject observation path must be absolute")
        if not isinstance(expected_authorized_value, str) or not expected_authorized_value:
            raise BrowserVerificationError("authorized Subject value must be non-empty")

        page = resource._context.new_page()
        try:
            response = page.goto(subject_origin + path, wait_until="domcontentloaded")
            if response is None:
                raise BrowserVerificationError("Subject observation route returned no response")
            value = str(response.text())
            if value != expected_authorized_value:
                raise BrowserVerificationError(
                    "Subject-visible route did not return the exact authorized observation"
                )
            return BrowserSubjectObservation(value=value)
        finally:
            page.close()

    def observe_evaluator_private_state(
        self,
        sut: Any,
        *,
        origin: str,
        cookie_name: str,
        local_storage_key: str,
    ) -> tuple[str | None, str | None]:
        """Independently confirm private authoritative state on the evaluator side."""

        resource = self._resource(sut)
        self._selected_origin(resource, origin)
        if not cookie_name or not local_storage_key:
            raise BrowserVerificationError("private-state probe keys must be non-empty")

        page = resource._context.new_page()
        try:
            page.goto(origin + "/state", wait_until="domcontentloaded")
            storage_value = page.evaluate(
                "key => localStorage.getItem(key)",
                local_storage_key,
            )
        finally:
            page.close()

        cookies = resource._context.cookies([origin + "/"])
        matches = [cookie for cookie in cookies if cookie.get("name") == cookie_name]
        if len(matches) > 1:
            raise BrowserVerificationError("private cookie probe is ambiguous")
        cookie_value = None if not matches else str(matches[0].get("value"))
        return cookie_value, None if storage_value is None else str(storage_value)

    def retain_evaluator_artifact(self, content: bytes) -> BrowserRetainedArtifact:
        """Retain bytes with identity and separate evaluator retrieval authorization."""

        if not isinstance(content, bytes) or not content:
            raise BrowserVerificationError("retained Browser Artifact bytes must be non-empty")
        digest = "sha256:" + hashlib.sha256(content).hexdigest()
        token = secrets.token_urlsafe(32)
        self._artifact_bytes.setdefault(digest, bytes(content))
        self._artifact_authorizations.setdefault(digest, set()).add(token)
        return BrowserRetainedArtifact(
            locator=BrowserArtifactLocator(digest=digest),
            authorization=BrowserArtifactAuthorization(_token=token),
        )

    def retrieve_evaluator_artifact(
        self,
        locator: BrowserArtifactLocator,
        authorization: BrowserArtifactAuthorization,
    ) -> bytes:
        """Retrieve only when evaluator-owned capability matches the retained Artifact."""

        if not isinstance(locator, BrowserArtifactLocator):
            raise BrowserVerificationError("Artifact retrieval requires an Artifact locator")
        if not isinstance(authorization, BrowserArtifactAuthorization):
            raise BrowserVerificationError(
                "Artifact digest identity is not retrieval authorization"
            )
        accepted = self._artifact_authorizations.get(locator.digest, set())
        if not any(
            secrets.compare_digest(token, authorization._token)
            for token in accepted
        ):
            raise BrowserVerificationError("Artifact retrieval authorization is invalid")
        try:
            return self._artifact_bytes[locator.digest]
        except KeyError as exc:
            raise BrowserVerificationError("retained Browser Artifact is unavailable") from exc

    def retain_redacted_artifact(
        self,
        content: bytes,
        *,
        redacted_content: bytes,
    ) -> tuple[BrowserRetainedArtifact, BrowserRetainedArtifact]:
        """Retain unredacted/redacted bytes as distinct Artifacts with distinct identity."""

        if content == redacted_content:
            raise BrowserVerificationError(
                "redacted Browser Artifact bytes must differ from unredacted bytes"
            )
        unredacted = self.retain_evaluator_artifact(content)
        redacted = self.retain_evaluator_artifact(redacted_content)
        if unredacted.locator.digest == redacted.locator.digest:
            raise BrowserVerificationError(
                "redacted Browser Artifact reused unredacted Artifact identity"
            )
        return unredacted, redacted
