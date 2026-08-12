"""Fail-closed loader for language-independent AVP TCK resources."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from avp_ref.canonical import digest

from .reference import TCKAdapterError


@dataclass(frozen=True, slots=True)
class LoadedTCKCase:
    """One registry-bound TCK case and its parsed document."""

    case_id: str
    path: str
    profile: str
    applicability: str
    when: str | None
    requirements: tuple[str, ...]
    document: Mapping[str, Any]


class TCKRepository:
    """Load TCK resources from a checked-out AVP repository.

    Registry paths are repository-relative and are constrained to the
    ``conformance/tck/cases`` subtree to prevent path traversal or accidental
    execution of unrelated YAML files.
    """

    def __init__(self, repository_root: Path) -> None:
        self.repository_root = repository_root.resolve()
        self.tck_root = self.repository_root / "conformance" / "tck"
        self.case_root = (self.tck_root / "cases").resolve()
        self.registry_path = self.tck_root / "registry.yaml"
        self._registry = self._load_mapping(self.registry_path)
        self._validate_resource(self._registry, kind="TCKRegistry")

    @classmethod
    def discover(cls, start: Path | None = None) -> "TCKRepository":
        """Find the nearest checkout containing the TCK registry."""

        current = (start or Path.cwd()).resolve()
        candidates = (current, *current.parents)
        for candidate in candidates:
            if (candidate / "conformance" / "tck" / "registry.yaml").is_file():
                return cls(candidate)
        raise TCKAdapterError(
            "cannot locate conformance/tck/registry.yaml; pass an explicit repository root"
        )

    @property
    def version(self) -> str:
        metadata = self._registry.get("metadata")
        if not isinstance(metadata, Mapping) or not isinstance(metadata.get("version"), str):
            raise TCKAdapterError("TCK registry metadata.version is missing")
        return metadata["version"]

    @property
    def registry_digest(self) -> str:
        """Return deterministic identity of the parsed registry document."""

        return digest(self._registry)

    def load_profile(self, profile: str) -> Mapping[str, Any]:
        if not profile or "/" in profile or "\\" in profile or profile in {".", ".."}:
            raise TCKAdapterError(f"invalid TCK profile name: {profile!r}")
        path = self.tck_root / "profiles" / f"{profile}.yaml"
        document = self._load_mapping(path)
        self._validate_resource(document, kind="ConformanceProfile")
        metadata = document.get("metadata")
        if not isinstance(metadata, Mapping) or metadata.get("name") != profile:
            raise TCKAdapterError(f"profile identity mismatch in {path}")
        return document

    def load_cases(
        self,
        profile: str,
        *,
        selected_case_ids: Iterable[str] | None = None,
    ) -> tuple[LoadedTCKCase, ...]:
        """Load registry cases for a profile in deterministic registry order."""

        requested = set(selected_case_ids or ())
        seen: set[str] = set()
        loaded: list[LoadedTCKCase] = []
        entries = self._registry.get("cases")
        if not isinstance(entries, list) or not entries:
            raise TCKAdapterError("TCK registry cases must be a non-empty list")

        for entry in entries:
            if not isinstance(entry, Mapping):
                raise TCKAdapterError("TCK registry case entry must be a mapping")
            case_id = entry.get("id")
            if not isinstance(case_id, str) or not case_id:
                raise TCKAdapterError("TCK registry case id must be a non-empty string")
            if case_id in seen:
                raise TCKAdapterError(f"duplicate TCK registry case id: {case_id}")
            seen.add(case_id)
            if entry.get("profile") != profile:
                continue
            if requested and case_id not in requested:
                continue

            path_value = entry.get("path")
            if not isinstance(path_value, str):
                raise TCKAdapterError(f"{case_id} registry path must be a string")
            path = self._resolve_case_path(path_value)
            document = self._load_mapping(path)
            self._validate_resource(document, kind="ConformanceCase")
            metadata = document.get("metadata")
            if not isinstance(metadata, Mapping) or metadata.get("id") != case_id:
                raise TCKAdapterError(f"{case_id} case identity does not match registry")
            if document.get("profile") != profile:
                raise TCKAdapterError(f"{case_id} case profile does not match registry")

            requirements = self._string_tuple(entry.get("requirements"), f"{case_id} requirements")
            document_requirements = self._string_tuple(
                document.get("requirements"), f"{case_id} document requirements"
            )
            if requirements != document_requirements:
                raise TCKAdapterError(f"{case_id} requirement mapping differs from registry")
            applicability = entry.get("applicability")
            if applicability not in {"mandatory", "conditional", "mixed"}:
                raise TCKAdapterError(f"{case_id} has invalid applicability {applicability!r}")
            if document.get("applicability") != applicability:
                raise TCKAdapterError(f"{case_id} applicability differs from registry")
            when = entry.get("when")
            if when is not None and not isinstance(when, str):
                raise TCKAdapterError(f"{case_id} condition must be a string")
            if applicability == "conditional" and document.get("when") != when:
                raise TCKAdapterError(f"{case_id} condition differs from registry")

            loaded.append(
                LoadedTCKCase(
                    case_id=case_id,
                    path=path_value,
                    profile=profile,
                    applicability=applicability,
                    when=when,
                    requirements=requirements,
                    document=document,
                )
            )

        if requested:
            missing = requested - {item.case_id for item in loaded}
            if missing:
                raise TCKAdapterError(
                    f"requested TCK cases are not registered for {profile}: {sorted(missing)}"
                )
        if not loaded:
            raise TCKAdapterError(f"no TCK cases registered for profile {profile}")
        return tuple(loaded)

    def _resolve_case_path(self, value: str) -> Path:
        path = (self.repository_root / value).resolve()
        try:
            path.relative_to(self.case_root)
        except ValueError as exc:
            raise TCKAdapterError(f"TCK case path escapes case root: {value}") from exc
        if path.suffix != ".yaml":
            raise TCKAdapterError(f"TCK case path must end in .yaml: {value}")
        return path

    @staticmethod
    def _string_tuple(value: Any, context: str) -> tuple[str, ...]:
        if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
            raise TCKAdapterError(f"{context} must be a non-empty string list")
        if len(value) != len(set(value)):
            raise TCKAdapterError(f"{context} contains duplicates")
        return tuple(value)

    @staticmethod
    def _load_mapping(path: Path) -> Mapping[str, Any]:
        try:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise TCKAdapterError(f"cannot load TCK resource {path}: {exc}") from exc
        if not isinstance(value, Mapping):
            raise TCKAdapterError(f"TCK resource must contain a mapping: {path}")
        return value

    @staticmethod
    def _validate_resource(document: Mapping[str, Any], *, kind: str) -> None:
        if document.get("apiVersion") != "avp.tck/v0.1" or document.get("kind") != kind:
            raise TCKAdapterError(
                f"expected avp.tck/v0.1 {kind}, got "
                f"{document.get('apiVersion')!r} {document.get('kind')!r}"
            )
