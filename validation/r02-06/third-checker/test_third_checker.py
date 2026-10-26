"""Small specification-derived tests; no existing project tests were read."""

import copy
import unittest
from unittest.mock import patch

import third_checker as tc


def two_history_model(faults=None):
    return {
        "name": "two coordinate example",
        "claim": "selected history has true label",
        "binding": "identity",
        "histories": ["negative", "positive"],
        "truth": {"negative": False, "positive": True},
        "domains": ["left", "right"],
        "alphabets": [["0", "1"], ["0", "1"]],
        "joint": {"negative": [["0", "0"]],
                  "positive": [["1", "1"]]},
        "faults": faults if faults is not None else [[], ["left"], ["right"]],
    }


def collision_witnesses(collision):
    return [
        {"history": history, "honest": honest, "fault": fault}
        for history, honest, fault in zip(collision["histories"],
                                         collision["honest_records"],
                                         collision["faults"])
    ]


class ReferenceTests(unittest.TestCase):
    def test_all_four_record_outcomes_and_exact_compatible_sets(self):
        model = two_history_model()
        compiled = tc.compile_model(model)
        expected = {
            ("0", "0"): ("FALSE", ["negative"]),
            ("1", "1"): ("TRUE", ["positive"]),
            ("0", "1"): ("UNRESOLVED", ["negative", "positive"]),
            ("outside", "1"): ("OUTSIDE_MODEL", []),
        }
        for record, (verdict, compatible) in expected.items():
            with self.subTest(record=record):
                self.assertEqual(compiled.evaluate_record(record), {
                    "verdict": verdict, "compatible_histories": compatible
                })

    def test_negative_capability_returns_checkable_collision(self):
        model = two_history_model()
        result = tc.check_capability(model)
        self.assertFalse(result["capability"])
        collision = result["collision"]
        self.assertEqual(tc.verify_ambiguity(
            model, collision["record"], collision_witnesses(collision)
        ), {"valid": True})

    def test_disjoint_exposure_has_capability(self):
        self.assertEqual(tc.check_capability(two_history_model([[]])), {
            "capability": True, "collision": None
        })

    def test_capability_does_not_imply_universal_support(self):
        model = two_history_model([[]])
        self.assertTrue(tc.check_capability(model)["capability"])
        self.assertEqual(tc.evaluate_record(model, ["0", "1"])["verdict"],
                         "OUTSIDE_MODEL")

    def test_true_record_does_not_imply_capability(self):
        model = two_history_model()
        self.assertEqual(tc.evaluate_record(model, ["1", "1"])["verdict"],
                         "TRUE")
        self.assertFalse(tc.check_capability(model)["capability"])

    def test_joint_support_is_not_marginal_product(self):
        model = two_history_model([[]])
        model["joint"]["negative"] = [["0", "0"], ["1", "1"]]
        model["joint"]["positive"] = [["0", "1"]]
        self.assertEqual(tc.evaluate_record(model, ["1", "0"]), {
            "verdict": "OUTSIDE_MODEL", "compatible_histories": []
        })

    def test_empty_and_nonbinary_atoms(self):
        model = {
            "name": "nonbinary", "claim": "boolean", "binding": "identity",
            "histories": ["n", "p"], "truth": {"n": False, "p": True},
            "domains": ["single"], "alphabets": [["", "alpha", "β"]],
            "joint": {"n": [[""]], "p": [["β"]]},
            "faults": [[], ["single"]],
        }
        self.assertEqual(tc.evaluate_record(model, ["alpha"]), {
            "verdict": "UNRESOLVED", "compatible_histories": ["n", "p"]
        })

    def test_same_truth_overlap_is_capable(self):
        model = two_history_model()
        model["truth"]["negative"] = True
        self.assertTrue(tc.check_capability(model)["capability"])
        self.assertEqual(tc.evaluate_record(model, ["0", "1"]), {
            "verdict": "TRUE", "compatible_histories": ["negative", "positive"]
        })

    def test_history_order_preserved(self):
        model = two_history_model()
        model["histories"].reverse()
        self.assertEqual(tc.evaluate_record(model, ["0", "1"])
                         ["compatible_histories"], ["positive", "negative"])
        collision = tc.check_capability(model)["collision"]
        self.assertEqual(collision["histories"], ["negative", "positive"])

    def test_nonfirst_valid_supplied_witness_accepted(self):
        model = two_history_model()
        model["joint"]["negative"].append(["1", "0"])
        model["joint"]["positive"].append(["0", "1"])
        witnesses = [
            {"history": "negative", "honest": ["1", "0"], "fault": ["left"]},
            {"history": "positive", "honest": ["0", "1"], "fault": ["right"]},
        ]
        self.assertEqual(tc.verify_ambiguity(model, ["0", "0"], witnesses),
                         {"valid": True})

    def test_verify_never_calls_compiler_or_universe_enumerator(self):
        model = two_history_model()
        witnesses = [
            {"history": "negative", "honest": ["0", "0"], "fault": ["right"]},
            {"history": "positive", "honest": ["1", "1"], "fault": ["left"]},
        ]
        with patch.object(tc, "compile_model", side_effect=AssertionError), \
             patch.object(tc, "product", side_effect=AssertionError):
            self.assertEqual(tc.verify_ambiguity(model, ["0", "1"], witnesses),
                             {"valid": True})

    def test_witness_mutations_rejected_without_replacement(self):
        model = two_history_model()
        collision = tc.check_capability(model)["collision"]
        original = collision_witnesses(collision)
        mutations = []
        wrong_history = copy.deepcopy(original)
        wrong_history[0]["history"] = "missing"
        mutations.append(wrong_history)
        mutations.append(list(reversed(original)))
        wrong_honest = copy.deepcopy(original)
        wrong_honest[0]["honest"] = ["1", "1"]
        mutations.append(wrong_honest)
        wrong_fault = copy.deepcopy(original)
        wrong_fault[0]["fault"] = []
        mutations.append(wrong_fault)
        duplicate_fault = copy.deepcopy(original)
        duplicate_fault[0]["fault"] *= 2
        mutations.append(duplicate_fault)
        mutations.append(original[:1])
        for witnesses in mutations:
            with self.subTest(witnesses=witnesses):
                self.assertEqual(tc.verify_ambiguity(
                    model, collision["record"], witnesses), {"valid": False})

    def test_fault_order_is_set_semantics(self):
        model = two_history_model([[], ["left"], ["right"], ["left", "right"]])
        witnesses = [
            {"history": "negative", "honest": ["0", "0"],
             "fault": ["right", "left"]},
            {"history": "positive", "honest": ["1", "1"],
             "fault": ["left", "right"]},
        ]
        self.assertEqual(tc.verify_ambiguity(model, ["0", "1"], witnesses),
                         {"valid": True})
        self.assertEqual(tc.verify_ambiguity(model, ["bad", "1"], witnesses),
                         {"valid": False})

    def test_undeclared_fault_rejected(self):
        model = two_history_model()
        witnesses = [
            {"history": "negative", "honest": ["0", "0"],
             "fault": ["left", "right"]},
            {"history": "positive", "honest": ["1", "1"], "fault": []},
        ]
        self.assertEqual(tc.verify_ambiguity(model, ["1", "1"], witnesses),
                         {"valid": False})

    def test_compiled_object_owns_a_snapshot_and_returns_fresh_results(self):
        model = two_history_model()
        compiled = tc.compile_model(model)
        result = compiled.check_capability()
        result["collision"]["honest_records"][0][0] = "mutated"
        model["joint"]["negative"][0][0] = "changed"
        self.assertEqual(compiled.evaluate_record(["0", "0"])["verdict"],
                         "FALSE")
        self.assertNotEqual(compiled.check_capability()["collision"]
                            ["honest_records"][0][0], "mutated")

    def test_bad_record_shape_raises(self):
        model = two_history_model()
        for record in (["0"], ["0", 1], "00"):
            with self.subTest(record=record), self.assertRaises(ValueError):
                tc.evaluate_record(model, record)

    def test_nonraw_and_nonidentity_are_unsupported(self):
        model = two_history_model()
        for operation, arguments in (
            (tc.compile_model, (model,)),
            (tc.evaluate_record, (model, ["0", "0"])),
            (tc.check_capability, (model,)),
            (tc.verify_ambiguity, (model, ["0", "0"], [])),
        ):
            with self.subTest(operation=operation.__name__), \
                 self.assertRaises(tc.UnsupportedSlice):
                operation(*arguments, scope="admitted-only")
        model["binding"] = "other"
        with self.assertRaises(tc.UnsupportedSlice):
            tc.compile_model(model)

    def test_all_declared_boundaries_reject_explicitly(self):
        model = two_history_model()
        for limits in (tc.Limits(max_worlds=3),
                       tc.Limits(max_cylinders=5),
                       tc.Limits(max_relation_cells=7)):
            with self.subTest(limits=limits), self.assertRaises(tc.UnsupportedSlice):
                tc.compile_model(model, limits=limits)

    def test_exact_limits_and_accounting(self):
        compiled = tc.compile_model(two_history_model(), limits=tc.Limits(
            max_worlds=4, max_cylinders=6, max_relation_cells=8
        ))
        self.assertEqual((compiled.world_count, compiled.cylinder_count,
                          compiled.relation_cells_bound), (4, 6, 8))

    def test_entrypoints_agree_with_compiled_methods(self):
        model = two_history_model()
        compiled = tc.compile_model(model)
        self.assertEqual(tc.evaluate_record(model, ["0", "1"]),
                         compiled.evaluate_record(["0", "1"]))
        self.assertEqual(tc.check_capability(model), compiled.check_capability())


if __name__ == "__main__":
    unittest.main(verbosity=2)
