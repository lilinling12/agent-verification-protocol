"""Validate repository governance files and pull-request metadata."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INTERNAL_BRANCH = re.compile(
    r"^(?:feat|fix|refactor|perf|test|docs|build|ci|chore|security|hotfix)/"
    r"[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?$"
)
RELEASE_BRANCH = re.compile(
    r"^release/v\d+\.\d+\.\d+(?:-(?:alpha|beta|rc)\.\d+)?$"
)
DEPENDABOT_BRANCH = re.compile(r"^dependabot/(?:pip|github_actions)/[A-Za-z0-9._+/-]+$")
PR_TITLE = re.compile(
    r"^(?:feat|fix|refactor|perf|test|docs|build|ci|chore|security|revert)"
    r"(?:\([a-z0-9._-]+\))?!?: [^\s].+$"
)
ACTION_REF = re.compile(r"^\s*-?\s*uses:\s*([^\s@]+)@([^\s#]+)", re.MULTILINE)
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")

REQUIRED_FILES = (
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "SECURITY.md",
    "repository-boundaries.json",
    "docs/ARCHITECTURE_BOUNDARIES.md",
    "docs/OPEN_SOURCE_ENGINEERING_STANDARD.md",
    "docs/BRANCHING.md",
    "docs/RELEASE_PROCESS.md",
    "docs/REPOSITORY_SETTINGS.md",
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/bug.yml",
    ".github/ISSUE_TEMPLATE/protocol-change.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
)

CODEOWNER_PROTECTED_PATHS = (
    "/.github/",
    "/GOVERNANCE.md",
    "/SECURITY.md",
    "/repository-boundaries.json",
    "/docs/ARCHITECTURE_BOUNDARIES.md",
    "/docs/OPEN_SOURCE_ENGINEERING_STANDARD.md",
    "/rfcs/",
    "/spec/",
    "/schemas/",
    "/conformance/",
)


def _fail(message: str) -> None:
    raise SystemExit(message)


def validate_metadata(branch: str, title: str, head_repo: str, repository: str) -> None:
    if not PR_TITLE.fullmatch(title):
        _fail(
            "PR title must use Conventional Commit form, for example "
            "'feat(runtime): add replay manifest'"
        )
    if head_repo == repository and not (
        INTERNAL_BRANCH.fullmatch(branch)
        or RELEASE_BRANCH.fullmatch(branch)
        or DEPENDABOT_BRANCH.fullmatch(branch)
    ):
        _fail(
            "Repository-owned branch name is invalid. See docs/BRANCHING.md. "
            f"Received: {branch!r}"
        )


def _load_yaml(path: Path):
    import yaml

    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _fail(f"invalid YAML: {path.relative_to(ROOT)}: {exc}")


def validate_issue_forms() -> None:
    for relative in (
        ".github/ISSUE_TEMPLATE/bug.yml",
        ".github/ISSUE_TEMPLATE/protocol-change.yml",
    ):
        path = ROOT / relative
        document = _load_yaml(path)
        if not isinstance(document, dict):
            _fail(f"issue form must be a mapping: {relative}")
        for key in ("name", "description", "body"):
            if key not in document:
                _fail(f"issue form missing {key!r}: {relative}")
        if not isinstance(document["body"], list) or not document["body"]:
            _fail(f"issue form body must be a non-empty list: {relative}")
        ids: set[str] = set()
        for index, item in enumerate(document["body"]):
            if not isinstance(item, dict) or "type" not in item or "attributes" not in item:
                _fail(f"malformed issue form item {index}: {relative}")
            if item["type"] != "markdown":
                item_id = item.get("id")
                if not isinstance(item_id, str) or not item_id:
                    _fail(f"interactive issue form item {index} needs an id: {relative}")
                if item_id in ids:
                    _fail(f"duplicate issue form id {item_id!r}: {relative}")
                ids.add(item_id)

    config = _load_yaml(ROOT / ".github/ISSUE_TEMPLATE/config.yml")
    if not isinstance(config, dict) or config.get("blank_issues_enabled") is not False:
        _fail("issue template config must explicitly disable blank issues")


def validate_codeowners() -> None:
    text = (ROOT / ".github/CODEOWNERS").read_text(encoding="utf-8")
    for protected_path in CODEOWNER_PROTECTED_PATHS:
        pattern = rf"^{re.escape(protected_path)}\s+@\S+"
        if not re.search(pattern, text, re.MULTILINE):
            _fail(f"CODEOWNERS must explicitly protect {protected_path}")


def validate_workflows() -> None:
    workflow_dir = ROOT / ".github/workflows"
    for path in sorted(workflow_dir.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        if "permissions:" not in text or "contents: read" not in text:
            _fail(f"workflow must declare minimum permissions: {path.relative_to(ROOT)}")
        for match in ACTION_REF.finditer(text):
            action, ref = match.groups()
            if action.startswith("./") or action.startswith("docker://"):
                continue
            if not FULL_SHA.fullmatch(ref):
                _fail(
                    f"third-party action must be pinned to a full commit SHA: "
                    f"{path.relative_to(ROOT)}: {action}@{ref}"
                )


def validate_repository() -> None:
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size == 0:
            _fail(f"required governance file missing or empty: {relative}")
    validate_issue_forms()
    validate_codeowners()
    validate_workflows()
    print("repository governance OK")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()

    if args.metadata_only:
        validate_metadata(
            os.environ.get("GOVERNANCE_HEAD_REF", ""),
            os.environ.get("GOVERNANCE_PR_TITLE", ""),
            os.environ.get("GOVERNANCE_HEAD_REPO", ""),
            os.environ.get("GOVERNANCE_REPOSITORY", ""),
        )
        print("pull-request metadata OK")
        return

    validate_repository()


if __name__ == "__main__":
    main()
