"""Reference adapter for the AVP Scenario v0.1 conformance profile."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

from avp_ref.reference import REFERENCE_TEMPLATE
from avp_ref.scenario import (
    CompileOptions,
    ReferenceResolutionError,
    ScenarioCompileError,
    ScenarioCompiler,
    StaticReferenceResolver,
    scenario_instance_digest,
)

from .models import TCKAdapterError, TCKCaseResult, TCKStatus


class ReferenceScenarioTCKAdapter:
    """Execute language-neutral Scenario vectors against the reference compiler."""

    _MATERIALIZATION = "AVP-TCK-SCENARIO-MATERIALIZATION-001"
    _UNRESOLVED = "AVP-TCK-SCENARIO-UNRESOLVED-001"
    _IDENTITY = "AVP-TCK-SCENARIO-IDENTITY-001"
    _IMMUTABILITY = "AVP-TCK-SCENARIO-IMMUTABILITY-001"
    _PROJECTION = "AVP-TCK-SCENARIO-PROJECTION-001"
    _REFERENCE = "AVP-TCK-SCENARIO-REFERENCE-001"

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return frozenset(
            {
                self._MATERIALIZATION,
                self._UNRESOLVED,
                self._IDENTITY,
                self._IMMUTABILITY,
                self._PROJECTION,
                self._REFERENCE,
            }
        )

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        evaluators = {
            self._MATERIALIZATION: self._materialization,
            self._UNRESOLVED: self._unresolved,
            self._IDENTITY: self._identity,
            self._IMMUTABILITY: self._immutability,
            self._PROJECTION: self._projection,
            self._REFERENCE: self._reference,
        }
        evaluator = evaluators.get(case_id)
        if evaluator is None:
            raise TCKAdapterError(f"unsupported reference Scenario TCK case: {case_id}")
        passed, detail = evaluator(vector)
        return TCKCaseResult(
            case_id,
            TCKStatus.PASS if passed else TCKStatus.FAIL,
            detail,
        )

    @staticmethod
    def _materialization(vector: Mapping[str, Any]) -> tuple[bool, str]:
        template = ReferenceScenarioTCKAdapter._mapping(vector.get("template"), "template")
        inputs = ReferenceScenarioTCKAdapter._mapping(
            vector.get("compilationInputs", {}), "compilationInputs"
        )
        overrides = ReferenceScenarioTCKAdapter._mapping(
            inputs.get("parameterOverrides", {}), "parameterOverrides"
        )
        repetitions = int(vector.get("repetitions", 2))
        if repetitions < 2:
            raise TCKAdapterError("Scenario materialization repetitions must be >= 2")
        compiler = ScenarioCompiler()
        instances = tuple(
            compiler.compile(template, CompileOptions(parameter_overrides=overrides))
            for _ in range(repetitions)
        )
        documents = [instance.to_dict() for instance in instances]
        unresolved = any(
            key in document for document in documents for key in ("parameters", "seeds", "generators")
        )
        passed = (
            all(document.get("kind") == "ScenarioInstance" for document in documents)
            and not unresolved
            and all(document == documents[0] for document in documents[1:])
            and all(instance.instance_digest == instances[0].instance_digest for instance in instances[1:])
        )
        return passed, (
            "ScenarioTemplate materializes deterministically into one resolved ScenarioInstance identity"
            if passed
            else "Scenario materialization is unresolved or non-deterministic"
        )

    @staticmethod
    def _unresolved(vector: Mapping[str, Any]) -> tuple[bool, str]:
        template = ReferenceScenarioTCKAdapter._mapping(vector.get("template"), "template")
        try:
            ScenarioCompiler().compile(template)
        except ScenarioCompileError:
            return True, "unresolved required input fails before any Episode or task verdict exists"
        return False, "compiler accepted an unresolved required execution input"

    @staticmethod
    def _identity(vector: Mapping[str, Any]) -> tuple[bool, str]:
        instance = copy.deepcopy(dict(ReferenceScenarioTCKAdapter._mapping(vector.get("instance"), "instance")))
        base = scenario_instance_digest(instance)

        reordered = dict(reversed(list(instance.items())))
        order_independent = scenario_instance_digest(reordered) == base

        provenance_changed = copy.deepcopy(instance)
        provenance_changed["provenance"] = {"compiler": "implementation-b"}
        provenance_independent = scenario_instance_digest(provenance_changed) == base

        semantic_changed = copy.deepcopy(instance)
        semantic_changed["task"]["instruction"] = "Return CHANGED"
        semantic_sensitive = scenario_instance_digest(semantic_changed) != base

        format_valid = base.startswith("sha256:") and len(base.removeprefix("sha256:")) == 64
        passed = order_independent and provenance_independent and semantic_sensitive and format_valid
        return passed, (
            "RFC 8785 ScenarioInstance identity is order/provenance independent and semantic-content sensitive"
            if passed
            else "ScenarioInstance identity violates the v0.1 canonical preimage contract"
        )

    @staticmethod
    def _immutability(vector: Mapping[str, Any]) -> tuple[bool, str]:
        instance = ScenarioCompiler().compile(REFERENCE_TEMPLATE)
        original_digest = instance.instance_digest
        original_instruction = instance.document["task"]["instruction"]
        rejected = False
        try:
            instance.document["task"]["instruction"] = vector.get("mutationValue")
        except TypeError:
            rejected = True

        detached = instance.to_dict()
        detached["task"]["instruction"] = vector.get("mutationValue")
        detached_only = instance.document["task"]["instruction"] == original_instruction
        passed = rejected and detached_only and instance.instance_digest == original_digest
        return passed, (
            "identity-bound ScenarioInstance semantics are immutable and detached copies cannot mutate the instance"
            if passed
            else "ScenarioInstance semantic mutation affected the live compiled instance"
        )

    @staticmethod
    def _projection(vector: Mapping[str, Any]) -> tuple[bool, str]:
        actor_id = str(vector.get("actorId", "subject"))
        capability = str(vector.get("publicCapability", ""))
        sentinel = str(vector.get("hiddenSentinel", ""))
        hidden_fields = tuple(str(item) for item in vector.get("hiddenFields", ()))

        template = copy.deepcopy(REFERENCE_TEMPLATE)
        template["capabilities"] = {
            actor_id: {"include": [capability]},
            "evaluator": {"include": ["mcp://control/hidden"]},
        }
        template["success"] = {"sentinel": sentinel}
        template["faults"] = {"future": {"sentinel": sentinel}}
        template["security"] = {"sentinel": sentinel}
        template["graders"] = [{"sentinel": sentinel}]
        template["contamination"] = {"sentinel": sentinel}
        template["validity"] = {"sentinel": sentinel}
        template["extensions"] = {"sentinel": sentinel}

        projection = ScenarioCompiler().compile(template).subject_projection(actor_id)
        projection_text = repr(projection)
        capabilities = projection.get("capabilities", {})
        actor_capabilities = capabilities.get(actor_id, {}) if isinstance(capabilities, Mapping) else {}
        includes = actor_capabilities.get("include", ()) if isinstance(actor_capabilities, Mapping) else ()
        passed = (
            capability in includes
            and "evaluator" not in capabilities
            and sentinel not in projection_text
            and all(field not in projection for field in hidden_fields)
        )
        return passed, (
            "Subject projection contains declared Subject capability and excludes evaluator-only material"
            if passed
            else "Subject projection leaked hidden material or mis-projected actor capabilities"
        )

    @staticmethod
    def _reference(vector: Mapping[str, Any]) -> tuple[bool, str]:
        reference = str(vector.get("reference", ""))
        resolved = ReferenceScenarioTCKAdapter._mapping(
            vector.get("resolvedIdentity"), "resolvedIdentity"
        )
        identity = str(resolved.get("identity", ""))
        template = copy.deepcopy(REFERENCE_TEMPLATE)
        template["task"] = {
            "instruction": "Use the declared fixture.",
            "artifacts": [reference],
        }
        resolver = StaticReferenceResolver(records={reference: {"digest": identity}})
        bound = ScenarioCompiler(resolver=resolver).compile(
            template, CompileOptions(strict_references=True)
        )
        document = bound.to_dict()
        bindings = document.get("referenceBindings", ())
        binding_ok = any(
            isinstance(item, Mapping)
            and item.get("reference") == reference
            and item.get("identity") == identity
            and item.get("identityType") == "content"
            for item in bindings
        )

        changed = copy.deepcopy(document)
        changed["referenceBindings"][0]["identity"] = "sha256:" + "2" * 64
        identity_sensitive = scenario_instance_digest(changed) != bound.instance_digest

        strict_failed = False
        try:
            ScenarioCompiler().compile(template, CompileOptions(strict_references=True))
        except ReferenceResolutionError:
            strict_failed = True

        passed = binding_ok and identity_sensitive and strict_failed
        return passed, (
            "strict external reference identity is bound into ScenarioInstance and missing content identity fails closed"
            if passed
            else "reference identity binding or strict fail-closed behavior is incorrect"
        )

    @staticmethod
    def _case_id(case: Mapping[str, Any]) -> str:
        metadata = case.get("metadata")
        case_id = metadata.get("id") if isinstance(metadata, Mapping) else None
        if not isinstance(case_id, str) or not case_id:
            raise TCKAdapterError("Scenario TCK case metadata.id is missing")
        return case_id

    @staticmethod
    def _vector(case: Mapping[str, Any], case_id: str) -> Mapping[str, Any]:
        vector = case.get("vector")
        if not isinstance(vector, Mapping):
            raise TCKAdapterError(f"{case_id} vector must be an object")
        return vector

    @staticmethod
    def _mapping(value: Any, name: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise TCKAdapterError(f"Scenario TCK {name} must be an object")
        return value
