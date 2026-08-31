"""Provider-neutral BPR-010 canonical collection ordering evidence for AEP-0011.

This Alpha 3 evidence runner intentionally does not launch a browser and does not
consume Playwright/WebDriver enumeration order. It proves the protocol-owned
property introduced by BPR-010: permutations of the same logical Browser
Manifest/Image collections canonicalize to one accepted object and one digest,
while a deliberately broken provider-order-preserving path does not.

The fixture uses only ASCII strings, booleans, null, and integers chosen so that
Python's compact, key-sorted JSON bytes coincide with RFC 8785 JCS for this
restricted evidence vector. This helper is not a production JCS implementation
and is not Browser runtime or TCK authority.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

_FIXTURE_REVISION = "browser-canonical-ordering-evidence-v0.1"


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_id: str
    status: str
    details: dict[str, Any]


def _ascii_key(value: str) -> bytes:
    raw = value.encode("utf-8")
    if any(byte > 0x7F for byte in raw):
        raise ValueError("BPR-010 evidence fixture intentionally uses ASCII canonical text")
    return raw


def _cookie_identity_key(cookie: dict[str, Any]) -> tuple[bytes, bytes, int, bytes]:
    return (
        _ascii_key(cookie["name"]),
        _ascii_key(cookie["domain"]),
        1 if cookie["hostOnly"] else 0,
        _ascii_key(cookie["path"]),
    )


def _utf16_units_key(entry: dict[str, Any]) -> tuple[int, ...]:
    return tuple(int(unit) for unit in entry["keyUnits"])


def _canonical_manifest(origin_selection: Iterable[str], cookie_selection: Iterable[str]) -> dict[str, Any]:
    origins = list(origin_selection)
    domains = list(cookie_selection)
    if len(origins) != len(set(origins)) or len(domains) != len(set(domains)):
        raise ValueError("selection lists must be duplicate-free before identity is accepted")
    return {
        "capabilityId": "state.browser",
        "profile": "avp-browser-unpartitioned-cookie-localstorage-v0.1",
        "revision": "0.1",
        "representationRevision": "browser-v0.1-canonical-order-v1",
        "localStorageOrigins": sorted(origins, key=_ascii_key),
        "cookieDomains": sorted(domains, key=_ascii_key),
    }


def _canonical_image(
    manifest_digest: str,
    origins: Sequence[dict[str, Any]],
    cookies: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    canonical_origins = []
    seen_origins: set[str] = set()
    for origin in origins:
        origin_text = str(origin["origin"])
        if origin_text in seen_origins:
            raise ValueError("duplicate BrowserStateImage origin identity")
        seen_origins.add(origin_text)
        entries = [dict(item) for item in origin["localStorage"]]
        canonical_origins.append(
            {
                "origin": origin_text,
                "localStorage": sorted(entries, key=_utf16_units_key),
            }
        )
    canonical_origins.sort(key=lambda item: _ascii_key(item["origin"]))

    canonical_cookies = [dict(cookie) for cookie in cookies]
    identities = [_cookie_identity_key(cookie) for cookie in canonical_cookies]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate BrowserStateImage cookie identity")
    canonical_cookies.sort(key=_cookie_identity_key)

    return {
        "manifestDigest": manifest_digest,
        "origins": canonical_origins,
        "cookies": canonical_cookies,
    }


def _restricted_jcs_bytes(value: Any) -> bytes:
    """Canonical bytes for this ASCII-only evidence vector, not a generic JCS API."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_restricted_jcs_bytes(value)).hexdigest()


def _manifest_case() -> CaseResult:
    origins = (
        "https://z.example",
        "http://a.example:8080",
        "https://a.example",
    )
    domains = ("z.example", "a.example", "sub.a.example")
    expected_origins = ["http://a.example:8080", "https://a.example", "https://z.example"]
    expected_domains = ["a.example", "sub.a.example", "z.example"]

    canonical_digests: set[str] = set()
    broken_digests: set[str] = set()
    permutation_count = 0
    for origin_order in itertools.permutations(origins):
        for domain_order in itertools.permutations(domains):
            permutation_count += 1
            canonical = _canonical_manifest(origin_order, domain_order)
            if canonical["localStorageOrigins"] != expected_origins:
                raise AssertionError("origin selection comparator drifted from protocol vector")
            if canonical["cookieDomains"] != expected_domains:
                raise AssertionError("cookie-domain selection comparator drifted from protocol vector")
            canonical_digests.add(_digest(canonical))

            broken = {
                **canonical,
                "localStorageOrigins": list(origin_order),
                "cookieDomains": list(domain_order),
            }
            broken_digests.add(_digest(broken))

    if len(canonical_digests) != 1:
        raise AssertionError(f"canonical Manifest identity varied across permutations: {canonical_digests}")
    if len(broken_digests) <= 1:
        raise AssertionError("provider-order-preserving negative control unexpectedly produced one digest")

    return CaseResult(
        case_id="BAE-013-MANIFEST",
        status="pass",
        details={
            "permutationsExercised": permutation_count,
            "canonicalDigest": next(iter(canonical_digests)),
            "providerOrderNegativeDigestCount": len(broken_digests),
            "expectedOriginOrder": expected_origins,
            "expectedCookieDomainOrder": expected_domains,
            "inputOrderHasSemanticMeaning": False,
        },
    )


def _image_case() -> CaseResult:
    origin_a = {
        "origin": "https://a.example",
        "localStorage": [
            {"keyUnits": [97], "value": "lower-a"},
            {"keyUnits": [65], "value": "upper-a"},
            {"keyUnits": [65, 0], "value": "upper-a-nul"},
        ],
    }
    origin_z = {
        "origin": "https://z.example",
        "localStorage": [
            {"keyUnits": [122], "value": "z"},
            {"keyUnits": [1], "value": "control"},
        ],
    }
    cookies = (
        {"name": "sid", "domain": "a.example", "hostOnly": True, "path": "/", "value": "host"},
        {"name": "sid", "domain": "a.example", "hostOnly": False, "path": "/", "value": "domain"},
        {"name": "sid", "domain": "a.example", "hostOnly": False, "path": "/admin", "value": "admin"},
        {"name": "alpha", "domain": "z.example", "hostOnly": True, "path": "/", "value": "z"},
    )

    expected_cookie_identities = [
        ["alpha", "z.example", True, "/"],
        ["sid", "a.example", False, "/"],
        ["sid", "a.example", False, "/admin"],
        ["sid", "a.example", True, "/"],
    ]
    expected_origin_order = ["https://a.example", "https://z.example"]
    expected_a_keys = [[65], [65, 0], [97]]

    manifest_digest = "0" * 64
    canonical_digests: set[str] = set()
    broken_digests: set[str] = set()
    permutation_count = 0

    for cookie_order in itertools.permutations(cookies):
        for origin_order in ((origin_a, origin_z), (origin_z, origin_a)):
            for reverse_entries in (False, True):
                permutation_count += 1
                permuted_origins = []
                for origin in origin_order:
                    local = list(origin["localStorage"])
                    if reverse_entries:
                        local.reverse()
                    permuted_origins.append({"origin": origin["origin"], "localStorage": local})

                canonical = _canonical_image(manifest_digest, permuted_origins, cookie_order)
                cookie_ids = [
                    [item["name"], item["domain"], item["hostOnly"], item["path"]]
                    for item in canonical["cookies"]
                ]
                if cookie_ids != expected_cookie_identities:
                    raise AssertionError(f"cookie identity comparator drifted: {cookie_ids}")
                if [item["origin"] for item in canonical["origins"]] != expected_origin_order:
                    raise AssertionError("origin image comparator drifted from protocol vector")
                if [item["keyUnits"] for item in canonical["origins"][0]["localStorage"]] != expected_a_keys:
                    raise AssertionError("localStorage UTF-16 key comparator drifted")
                canonical_digests.add(_digest(canonical))

                broken = {
                    "manifestDigest": manifest_digest,
                    "origins": permuted_origins,
                    "cookies": list(cookie_order),
                }
                broken_digests.add(_digest(broken))

    if len(canonical_digests) != 1:
        raise AssertionError(f"canonical Image identity varied across permutations: {canonical_digests}")
    if len(broken_digests) <= 1:
        raise AssertionError("provider-order-preserving image negative control unexpectedly produced one digest")

    return CaseResult(
        case_id="BAE-013-IMAGE",
        status="pass",
        details={
            "permutationsExercised": permutation_count,
            "canonicalDigest": next(iter(canonical_digests)),
            "providerOrderNegativeDigestCount": len(broken_digests),
            "expectedOriginOrder": expected_origin_order,
            "expectedCookieIdentityOrder": expected_cookie_identities,
            "expectedFirstOriginLocalStorageKeyUnits": expected_a_keys,
            "browserOrProviderEnumerationUsedAsOracle": False,
        },
    )


def _duplicate_case() -> CaseResult:
    manifest_duplicate_rejected = False
    image_origin_duplicate_rejected = False
    image_cookie_duplicate_rejected = False

    try:
        _canonical_manifest(("https://a.example", "https://a.example"), ("a.example",))
    except ValueError:
        manifest_duplicate_rejected = True

    try:
        _canonical_image(
            "0" * 64,
            (
                {"origin": "https://a.example", "localStorage": []},
                {"origin": "https://a.example", "localStorage": []},
            ),
            (),
        )
    except ValueError:
        image_origin_duplicate_rejected = True

    duplicate_cookie = {"name": "sid", "domain": "a.example", "hostOnly": True, "path": "/", "value": "1"}
    try:
        _canonical_image("0" * 64, (), (duplicate_cookie, dict(duplicate_cookie)))
    except ValueError:
        image_cookie_duplicate_rejected = True

    if not all((manifest_duplicate_rejected, image_origin_duplicate_rejected, image_cookie_duplicate_rejected)):
        raise AssertionError("one or more duplicate-identity negative controls did not fail closed")

    return CaseResult(
        case_id="BAE-013-DUPLICATES",
        status="pass",
        details={
            "manifestDuplicateSelectionRejected": True,
            "imageDuplicateOriginRejected": True,
            "imageDuplicateCookieIdentityRejected": True,
        },
    )


def run(output: Path) -> int:
    cases: list[CaseResult] = []
    for case in (_manifest_case, _image_case, _duplicate_case):
        try:
            cases.append(case())
        except Exception as exc:
            cases.append(
                CaseResult(
                    case_id=case.__name__.strip("_").upper(),
                    status="fail",
                    details={"errorType": type(exc).__name__, "error": str(exc)},
                )
            )

    document = {
        "schema": "avp-browser-canonical-ordering-evidence-v0.1",
        "fixtureRevision": _FIXTURE_REVISION,
        "repositorySha": os.environ.get("GITHUB_SHA"),
        "authority": "non-normative-provider-neutral-acceptance-evidence",
        "serializationScope": "ASCII-only fixture where compact sorted-key JSON equals JCS; not a generic JCS implementation",
        "cases": [asdict(case) for case in cases],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")

    failures = [case.case_id for case in cases if case.status == "fail"]
    print(json.dumps({"cases": {case.case_id: case.status for case in cases}, "failures": failures}, indent=2))
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("browser-evidence/browser-canonical-ordering-evidence.json"),
    )
    args = parser.parse_args()
    return run(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
