"""Application-layer runner for executing AVP TCK profiles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Protocol

from avp_ref.runtime import ReferenceRuntime

from .loader import TCKRepository
from .models import TCKAdapterError, TCKCaseResult
from .reference_composite import ReferenceConformanceAdapter
from .report import build_report
from .schema import validate_report


class TCKCaseAdapter(Protocol):
    """Minimal implementation adapter contract consumed by TCKRunner."""

    @property
    def supported_case_ids(self) -> frozenset[str]: ...

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult: ...


@dataclass(frozen=True, slots=True)
class TCKRunResult:
    """Validated report and the richer in-process case diagnostics."""

    report: Mapping[str, Any]
    case_results: tuple[TCKCaseResult, ...]

    @property
    def conformant(self) -> bool:
        return self.report["summary"]["failed"] == 0


class TCKRunner:
    """Execute selected TCK cases and fail closed on contract errors."""

    def __init__(
        self,
        repository: TCKRepository,
        *,
        adapter: TCKCaseAdapter,
        implementation: Mapping[str, object],
        capabilities: Iterable[str] = (),
    ) -> None:
        capability_values = tuple(capabilities)
        if not all(isinstance(item, str) and item for item in capability_values):
            raise TCKAdapterError("declared capabilities must be non-empty strings")
        self._repository = repository
        self._adapter = adapter
        self._implementation = dict(implementation)
        self._capabilities = frozenset(capability_values)
        for field in ("name", "version"):
            if not isinstance(self._implementation.get(field), str) or not self._implementation[field]:
                raise TCKAdapterError(
                    f"implementation.{field} must be a non-empty string"
                )

    @classmethod
    def for_reference(
        cls,
        repository: TCKRepository,
        *,
        capabilities: Iterable[str] = (),
    ) -> "TCKRunner":
        """Create a runner targeting the Python reference implementation."""

        capability_set = frozenset(capabilities)
        runtime_capabilities = ReferenceRuntime().capabilities()
        implementation = runtime_capabilities.get("implementation")
        if not isinstance(implementation, Mapping):
            raise TCKAdapterError(
                "reference runtime does not expose implementation identity"
            )
        return cls(
            repository,
            adapter=ReferenceConformanceAdapter(capabilities=capability_set),
            implementation=implementation,
            capabilities=capability_set,
        )

    def run(
        self,
        *,
        profile: str = "avp-core-v0.1",
        selected_case_ids: Iterable[str] | None = None,
    ) -> TCKRunResult:
        """Execute a complete profile or a deterministic selected subset."""

        profile_document = self._repository.load_profile(profile)
        metadata = profile_document.get("metadata")
        if not isinstance(metadata, Mapping) or not isinstance(
            metadata.get("version"), str
        ):
            raise TCKAdapterError(
                f"profile {profile!r} is missing metadata.version"
            )
        cases = self._repository.load_cases(
            profile,
            selected_case_ids=selected_case_ids,
        )
        unsupported = {
            item.case_id for item in cases
        } - self._adapter.supported_case_ids
        if unsupported:
            raise TCKAdapterError(
                "implementation adapter does not support registered TCK cases: "
                f"{sorted(unsupported)}"
            )

        results: list[TCKCaseResult] = []
        for loaded in cases:
            result = self._adapter.evaluate(loaded.document)
            if result.case_id != loaded.case_id:
                raise TCKAdapterError(
                    "adapter result identity mismatch: "
                    f"expected {loaded.case_id}, got {result.case_id}"
                )
            results.append(result)

        report = build_report(
            self._repository,
            profile=profile,
            profile_version=metadata["version"],
            implementation=self._implementation,
            capabilities=self._capabilities,
            results=results,
        )
        validate_report(report, self._repository, expected_profile=profile)
        return TCKRunResult(
            report=report,
            case_results=tuple(results),
        )
