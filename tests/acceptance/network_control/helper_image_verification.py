"""Concrete helper-image verification for Network Control live execution.

This module is project-local execution plumbing. It deliberately does not define
portable AVP semantics or a provider abstraction. The reviewed helper is already
addressed by an immutable platform-manifest digest; successful Docker pull of
that exact reference is therefore the content-identity boundary. Local inspect
then proves that the materialized image is usable on the reviewed platform.

``RepoDigests`` is intentionally not used as a second identity oracle. Docker may
normalize official-image repository names and may expose repository/index digest
metadata that is not byte-for-byte equal to the fully-qualified platform-digest
reference used for the pull. Treating that display metadata as authoritative
caused TEL-RB-003 run 33824673863 to reject the exact reviewed helper before any
capture canary executed.
"""

from __future__ import annotations

import json
from typing import Protocol

from .toxiproxy_binding import ToxiproxyPrerequisiteError


class _DockerControl(Protocol):
    def run(self, *args: str, allow_failure: bool = False) -> str: ...


class _ExactHelperArtifact(Protocol):
    platform: str
    image_ref: str


def prepare_exact_helper_image(
    docker: _DockerControl,
    artifact: _ExactHelperArtifact,
) -> dict[str, object]:
    """Pull one immutable helper ref and verify its local platform materialization.

    The pull reference must already contain the reviewed exact digest. Docker
    resolves that immutable reference or fails the operation; no mutable tag is
    admitted here. The subsequent inspect is performed against the same exact
    reference and fails closed on malformed identity/platform metadata.
    """

    if "@sha256:" not in artifact.image_ref:
        raise ToxiproxyPrerequisiteError("helper image reference is not digest pinned")
    if artifact.platform != "linux/amd64":
        raise ToxiproxyPrerequisiteError(
            f"reviewed helper platform is unsupported: {artifact.platform!r}"
        )

    docker.run("pull", "--platform", artifact.platform, artifact.image_ref)
    raw = docker.run(
        "image",
        "inspect",
        artifact.image_ref,
        "--format",
        "{{json .}}",
    )
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ToxiproxyPrerequisiteError("helper image inspect is invalid JSON") from exc
    if not isinstance(document, dict):
        raise ToxiproxyPrerequisiteError("helper image inspect is not an object")

    image_id = document.get("Id")
    os_type = document.get("Os")
    architecture = document.get("Architecture")
    if not isinstance(image_id, str) or not image_id.startswith("sha256:"):
        raise ToxiproxyPrerequisiteError("helper image local content ID is unavailable")
    if os_type != "linux" or architecture not in {"amd64", "x86_64"}:
        raise ToxiproxyPrerequisiteError(
            "helper image platform mismatch: "
            f"expected linux/amd64, got {os_type!r}/{architecture!r}"
        )
    return document
