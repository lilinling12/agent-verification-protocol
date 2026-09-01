from __future__ import annotations

import hashlib
import secrets
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from avp_ref.environment.models import SnapshotRef
from avp_ref.tck_adapter.browser_harness import BrowserVerificationError
from avp_ref.tck_adapter.browser_tck_security import (
    BrowserSecurityArtifact,
    BrowserSecurityTCKEvaluator,
)
from avp_ref.tck_adapter.models import TCKAdapterError, TCKStatus

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "conformance/tck/cases/browser/AVP-TCK-BROWSER-SECURITY-001.yaml"


@dataclass
class _SUT:
    handle_id: str = "security-browser-1"
    private_cookie: str | None = None
    private_storage: str | None = None

    def snapshot(self) -> SnapshotRef:
        raise AssertionError("security evaluator must not invoke snapshot")

    def reset(self) -> None:
        raise AssertionError("security evaluator must not invoke reset")

    def restore(self, snapshot: SnapshotRef) -> None:
        del snapshot
        raise AssertionError("security evaluator must not invoke restore")

    def release(self) -> None:
        return


class _SecurityControl:
    def __init__(self) -> None:
        self._bytes: dict[str, bytes] = {}
        self._authorization: dict[str, str] = {}

    def seed_evaluator_private_state(
        self,
        sut: _SUT,
        *,
        cookie_value: str,
        local_storage_value: str,
    ) -> None:
        sut.private_cookie = cookie_value
        sut.private_storage = local_storage_value

    def observe_subject_surface(self, sut: _SUT) -> Mapping[str, Any]:
        del sut
        return {"value": "public-observation"}

    def observe_evaluator_private_state(self, sut: _SUT) -> Mapping[str, str]:
        if sut.private_cookie is None or sut.private_storage is None:
            raise BrowserVerificationError("private state was not seeded")
        return {
            "cookie": sut.private_cookie,
            "localStorage": sut.private_storage,
        }

    def retain_artifact(self, content: bytes) -> BrowserSecurityArtifact:
        digest = "sha256:" + hashlib.sha256(content).hexdigest()
        token = secrets.token_urlsafe(16)
        self._bytes[digest] = bytes(content)
        self._authorization[digest] = token
        return BrowserSecurityArtifact(
            identity=digest,
            locator=digest,
            authorization=token,
        )

    def retrieve_artifact(self, locator: object, authorization: object) -> bytes:
        if not isinstance(locator, str) or not isinstance(authorization, str):
            raise BrowserVerificationError("Artifact retrieval inputs are invalid")
        token = self._authorization.get(locator)
        if token is None or not secrets.compare_digest(token, authorization):
            raise BrowserVerificationError("Artifact retrieval authorization is invalid")
        return self._bytes[locator]

    def retain_redacted_artifacts(
        self,
        content: bytes,
        *,
        redacted_content: bytes,
    ) -> tuple[BrowserSecurityArtifact, BrowserSecurityArtifact]:
        if content == redacted_content:
            raise BrowserVerificationError("redacted bytes must differ")
        return self.retain_artifact(content), self.retain_artifact(redacted_content)


class _LeakingControl(_SecurityControl):
    def observe_subject_surface(self, sut: _SUT) -> Mapping[str, Any]:
        return {
            "value": "public-observation",
            "private": sut.private_cookie,
        }


class _DigestAuthorizesControl(_SecurityControl):
    def retrieve_artifact(self, locator: object, authorization: object) -> bytes:
        if locator == authorization and isinstance(locator, str) and locator in self._bytes:
            return self._bytes[locator]
        return super().retrieve_artifact(locator, authorization)


def _case() -> dict[str, Any]:
    return yaml.safe_load(CASE.read_text(encoding="utf-8"))


def _verify_private_authoritative(sut: _SUT) -> None:
    if sut.private_cookie is None or sut.private_storage is None:
        raise BrowserVerificationError(
            "evaluator-private state was omitted from authoritative memory state"
        )


def _evaluator(control: _SecurityControl) -> BrowserSecurityTCKEvaluator:
    return BrowserSecurityTCKEvaluator(
        sut=_SUT(),
        evidence_control=control,
        verify_private_state_authoritative=_verify_private_authoritative,
    )


class BrowserSecurityTCKEvaluatorTest(unittest.TestCase):
    def test_executes_visibility_and_artifact_authority_separation(self) -> None:
        result = _evaluator(_SecurityControl()).evaluate(_case())

        self.assertIs(TCKStatus.PASS, result.status, result.detail)

    def test_rejects_actual_subject_private_state_leak(self) -> None:
        result = _evaluator(_LeakingControl()).evaluate(_case())

        self.assertIs(TCKStatus.FAIL, result.status)
        self.assertIn("Subject-visible Browser surface", result.detail)

    def test_rejects_locator_used_as_retrieval_authority(self) -> None:
        result = _evaluator(_DigestAuthorizesControl()).evaluate(_case())

        self.assertIs(TCKStatus.FAIL, result.status)
        self.assertIn("retrieval authorization", result.detail)

    def test_rejects_privileged_control_vector_drift(self) -> None:
        case = _case()
        case["vector"]["privilegedControl"].pop()

        with self.assertRaisesRegex(TCKAdapterError, "privilegedControl changed"):
            _evaluator(_SecurityControl()).evaluate(case)

    def test_fails_if_private_state_is_not_authoritative(self) -> None:
        def reject_authoritative(sut: _SUT) -> None:
            del sut
            raise BrowserVerificationError("private state is not authoritative")

        evaluator = BrowserSecurityTCKEvaluator(
            sut=_SUT(),
            evidence_control=_SecurityControl(),
            verify_private_state_authoritative=reject_authoritative,
        )

        result = evaluator.evaluate(_case())

        self.assertIs(TCKStatus.FAIL, result.status)
        self.assertIn("not authoritative", result.detail)


if __name__ == "__main__":
    unittest.main()
