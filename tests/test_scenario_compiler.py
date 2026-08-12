import unittest

from avp_ref.reference import REFERENCE_TEMPLATE
from avp_ref.scenario import CompileOptions, ParameterResolutionError, ReferenceResolutionError, ScenarioCompiler


class ScenarioCompilerTest(unittest.TestCase):
    def test_same_seed_produces_same_digest(self):
        compiler = ScenarioCompiler()
        first = compiler.compile(REFERENCE_TEMPLATE, CompileOptions(root_seed=42))
        second = compiler.compile(REFERENCE_TEMPLATE, CompileOptions(root_seed=42))
        self.assertEqual(first.instance_digest, second.instance_digest)
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_different_seed_changes_instance_identity(self):
        compiler = ScenarioCompiler()
        self.assertNotEqual(compiler.compile(REFERENCE_TEMPLATE, CompileOptions(root_seed=1)).instance_digest, compiler.compile(REFERENCE_TEMPLATE, CompileOptions(root_seed=2)).instance_digest)

    def test_instance_is_deeply_immutable(self):
        instance = ScenarioCompiler().compile(REFERENCE_TEMPLATE)
        with self.assertRaises(TypeError):
            instance.document["metadata"]["name"] = "mutated"

    def test_subject_projection_hides_evaluator_extensions(self):
        projection = ScenarioCompiler().compile(REFERENCE_TEMPLATE).subject_projection()
        self.assertNotIn("extensions", projection)
        self.assertNotIn("success", projection)
        self.assertNotIn("invariants", projection)

    def test_unresolved_parameter_is_rejected(self):
        template = dict(REFERENCE_TEMPLATE)
        template["parameters"] = {"target": {"type": "string", "required": True}}
        template["task"] = {"instruction": "Refund ${target}"}
        with self.assertRaises(ParameterResolutionError):
            ScenarioCompiler().compile(template)

    def test_strict_references_reject_symbolic_resolution(self):
        with self.assertRaises(ReferenceResolutionError):
            ScenarioCompiler().compile(REFERENCE_TEMPLATE, CompileOptions(strict_references=True))


if __name__ == "__main__":
    unittest.main()
