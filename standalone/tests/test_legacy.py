"""Legacy conversion controls from a previously saved 001 development run."""

import copy
import json
from pathlib import Path
import unittest

from witnessability_checker.common import Budget, InvalidInput, PinMismatch, Unsupported
from witnessability_checker.context import make_pins, validate_document
from witnessability_checker.legacy import import_model, import_certificate
from witnessability_checker.verify import verify_ambiguity
from witnessability_checker.analysis import evaluate_record, check_capability

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "legacy-001"
POLICY = {"id": "declared-model", "version": "1", "acknowledged_assumptions": True}


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class LegacyConversionTests(unittest.TestCase):
    def document(self, name, budget):
        return import_model(load("model-" + name + ".json"),
                            expected_legacy_pins=load("expected-model-" + name + ".json"),
                            budget=budget)

    def test_model_conversion_preserves_pinned_semantics_and_results(self):
        for name, capability in (("baseline", False), ("atomic", True)):
            budget = Budget()
            doc = self.document(name, budget)
            model = validate_document(doc, budget)
            self.assertEqual(doc["model"], load("model-" + name + ".json"))
            expected = load("expected-model-" + name + ".json")
            self.assertEqual(model.pin, expected["model"])
            self.assertEqual(model.claim_pin, expected["claim"])
            self.assertEqual(check_capability(model, budget)["capability"], capability)
        for model_id, record_id, verdict in (("baseline", "r0000", "UNRESOLVED"),
                                             ("atomic", "r0002", "TRUE"),
                                             ("atomic", "r0000", "FALSE")):
            budget = Budget()
            model = validate_document(self.document(model_id, budget), budget)
            record = load("record-" + model_id + "-" + record_id + ".json")
            self.assertEqual(evaluate_record(model, record, budget)["verdict"], verdict)

    def test_explicit_certificate_conversion_keeps_old_pins_adds_context(self):
        budget = Budget()
        doc = self.document("baseline", budget)
        old = load("certificate-baseline-r0000.json")
        untouched = copy.deepcopy(old)
        record = load("record-baseline-r0000.json")
        old_pins = load("expected-certificate-baseline-r0000.json")
        new = import_certificate(doc, record, old, POLICY,
                                 expected_legacy_pins=old_pins, budget=budget)
        self.assertNotIn("schema", new)
        self.assertIn("schema_version", new)
        self.assertEqual({k: new["pins"][k] for k in old_pins}, old_pins)
        self.assertEqual(new["witnesses"], old["witnesses"])
        self.assertEqual(old, untouched)
        model = validate_document(doc, budget)
        expected = make_pins(doc, model, POLICY, record)
        self.assertTrue(verify_ambiguity(model, record, new,
                                        expected_pins=expected, budget=budget))

    def test_legacy_external_pins_cannot_be_replaced_from_certificate(self):
        budget = Budget()
        doc = self.document("baseline", budget)
        old = load("certificate-baseline-r0000.json")
        expected = load("expected-certificate-baseline-r0000.json")
        expected["record"] = "0" * 64
        with self.assertRaises(PinMismatch):
            import_certificate(doc, old["record"], old, POLICY,
                               expected_legacy_pins=expected, budget=budget)
        raw = load("model-baseline.json")
        raw["name"] += "-replacement"
        with self.assertRaises(PinMismatch):
            import_model(raw, expected_legacy_pins=load("expected-model-baseline.json"),
                         budget=Budget())

    def test_legacy_unknown_schema_and_extra_fields_are_not_relabelled(self):
        for malformed, expected_error in (({"schema": "other"}, Unsupported),
                                            ({"extra": 1}, InvalidInput)):
            budget = Budget()
            doc = self.document("baseline", budget)
            old = load("certificate-baseline-r0000.json")
            old.update(malformed)
            with self.assertRaises(expected_error):
                import_certificate(doc, old["record"], old, POLICY,
                                   expected_legacy_pins=load("expected-certificate-baseline-r0000.json"),
                                   budget=budget)


if __name__ == "__main__":
    unittest.main()
