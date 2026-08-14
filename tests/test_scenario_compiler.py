import copy
import unittest

from avp_ref.reference import REFERENCE_TEMPLATE
from avp_ref.scenario import (
    CompileOptions,
    ParameterResolutionError,
    ReferenceResolutionError,
    ScenarioCompiler,
    ScenarioIdentityError,
    ScenarioInstance,
    scenario_instance_digest,
    validate_instance,
    verify_scenario_instance_identity,
)


class ScenarioCompilerTest(unittest.TestCase):
    def test_same_inputs_produce_same_digest(self):
        compiler = ScenarioCompiler()
        first = compiler.compile(REFERENCE_TEMPLATE, CompileOptions(root_seed=42))
        second = compiler.compile(REFERENCE_TEMPLATE, CompileOptions(root_seed=42))
        self.assertEqual(first.instance_digest, second.instance_digest)
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_non_semantic_seed_provenance_does_not_change_identity(self):
        compiler = ScenarioCompiler()
        first = compiler.compile(REFERENCE_TEMPLATE, CompileOptions(root_seed=1))
        second = compiler.compile(REFERENCE_TEMPLATE, CompileOptions(root_seed=2))
        self.assertEqual(first.instance_digest, second.instance_digest)
        self.assertNotEqual(first.to_dict()["provenance"], second.to_dict()["provenance"])

    def test_materialized_semantic_change_changes_identity(self):
        template = copy.deepcopy(REFERENCE_TEMPLATE)
        template["parameters"] = {"target": {"type": "string", "required": True}}
        template["task"] = {"instruction": "Refund ${target}."}
        compiler = ScenarioCompiler()
        first = compiler.compile(
            template,
            CompileOptions(parameter_overrides={"target": "ord_1"}),
        )
        second = compiler.compile(
            template,
            CompileOptions(parameter_overrides={"target": "ord_2"}),
        )
        self.assertNotEqual(first.instance_digest, second.instance_digest)

    def test_provenance_is_excluded_from_identity_preimage(self):
        instance = ScenarioCompiler().compile(REFERENCE_TEMPLATE)
        document = instance.to_dict()
        document["provenance"]["compiler"]["version"] = "other-implementation"
        self.assertEqual(instance.instance_digest, scenario_instance_digest(document))

    def test_serialized_instance_is_schema_valid(self):
        instance = ScenarioCompiler().compile(REFERENCE_TEMPLATE)
        document = instance.to_dict()
        validate_instance(document)
        verify_scenario_instance_identity(document)
        self.assertEqual(document["instanceDigest"], instance.instance_digest)
        self.assertNotIn("instance_digest", document)
        self.assertNotIn("compilation", document)

    def test_declared_digest_tampering_fails_closed(self):
        instance = ScenarioCompiler().compile(REFERENCE_TEMPLATE)
        document = instance.to_dict()
        document["instanceDigest"] = "sha256:" + "0" * 64
        with self.assertRaises(ScenarioIdentityError):
            verify_scenario_instance_identity(document)
        with self.assertRaises(ScenarioIdentityError):
            ScenarioInstance(
                template_digest=instance.template_digest,
                instance_digest=instance.instance_digest,
                document=document,
            )

    def test_manual_instance_construction_detaches_mutable_input(self):
        compiled = ScenarioCompiler().compile(REFERENCE_TEMPLATE)
        document = compiled.to_dict()
        reconstructed = ScenarioInstance(
            template_digest=compiled.template_digest,
            instance_digest=compiled.instance_digest,
            document=document,
        )
        document["task"]["instruction"] = "tampered after construction"
        self.assertNotEqual(document["task"]["instruction"], reconstructed.document["task"]["instruction"])
        with self.assertRaises(TypeError):
            reconstructed.document["task"]["instruction"] = "mutate frozen instance"

    def test_identity_rejects_non_string_object_member_names(self):
        document = ScenarioCompiler().compile(REFERENCE_TEMPLATE).to_dict()
        document[1] = "non-json-member-name"
        with self.assertRaises(ScenarioIdentityError):
            scenario_instance_digest(document)

    def test_reference_bindings_are_identity_bound(self):
        instance = ScenarioCompiler().compile(REFERENCE_TEMPLATE)
        document = instance.to_dict()
        bindings = document["referenceBindings"]
        self.assertTrue(bindings)
        changed = copy.deepcopy(document)
        changed["referenceBindings"][0]["identity"] = "sha256:" + "0" * 64
        self.assertNotEqual(instance.instance_digest, scenario_instance_digest(changed))

    def test_instance_is_deeply_immutable(self):
        instance = ScenarioCompiler().compile(REFERENCE_TEMPLATE)
        with self.assertRaises(TypeError):
            instance.document["metadata"]["name"] = "mutated"

    def test_subject_projection_hides_evaluator_extensions(self):
        projection = ScenarioCompiler().compile(REFERENCE_TEMPLATE).subject_projection()
        self.assertNotIn("extensions", projection)
        self.assertNotIn("success", projection)
        self.assertNotIn("invariants", projection)
        self.assertNotIn("provenance", projection)
        self.assertNotIn("referenceBindings", projection)

    def test_unresolved_parameter_is_rejected(self):
        template = copy.deepcopy(REFERENCE_TEMPLATE)
        template["parameters"] = {"target": {"type": "string", "required": True}}
        template["task"] = {"instruction": "Refund ${target}"}
        with self.assertRaises(ParameterResolutionError):
            ScenarioCompiler().compile(template)

    def test_strict_references_reject_symbolic_resolution(self):
        with self.assertRaises(ReferenceResolutionError):
            ScenarioCompiler().compile(
                REFERENCE_TEMPLATE,
                CompileOptions(strict_references=True),
            )


if __name__ == "__main__":
    unittest.main()
