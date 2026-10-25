import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from witnessability_research.experiment import build_models, consume, generate, verify_run, write_run
from witnessability_research.finite import (UnsupportedInput, canonical, enumerate_exposure,
                                          judge_direct, structural_capability)
from witnessability_research.store import BINDING, admit_counter, counter_value, endpoint, histories, receipt, replay, variants


class ExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.traces, cls.models, cls.raw = build_models()
        cls.by_actions = {tuple(t["actions"]): t["history_id"] for t in cls.traces}

    def exposure(self, model_id, actions):
        return enumerate_exposure(self.models[model_id], self.by_actions[tuple(actions)])

    def test_ground_truth_and_same_value_write(self):
        self.assertEqual(len(histories()), 40)
        self.assertEqual(sum(t["store"]["committed_write_count"] == 0 for t in self.traces), 4)
        self.assertEqual(replay(("write0",))["committed_write_count"], 1)
        self.assertEqual(replay(("write1", "write0"))["committed_write_count"], 2)
        self.assertEqual(replay(("noop",))["committed_write_count"], 0)

    def test_counter_does_not_copy_ground_truth_count_or_ledger(self):
        actions = ("write0", "noop", "write1")
        state = replay(actions)
        poisoned = copy.deepcopy(state)
        poisoned["committed_write_count"] = 999
        poisoned["commits"] = []
        for model_id in self.models:
            self.assertEqual(variants(model_id, actions, state, 3),
                             variants(model_id, actions, poisoned, 3), model_id)
        self.assertEqual(counter_value(actions), 2)
        self.assertEqual(counter_value(actions, missed=(0,)), 1)
        self.assertEqual(counter_value(actions, reset_before=3), 0)
        self.assertEqual(state["committed_write_count"], 2)

    def test_baseline_aliases_zero_and_reverted_and_same_value_writes(self):
        zero = self.exposure("baseline", ())
        self.assertEqual(zero, self.exposure("baseline", ("write0",)))
        self.assertEqual(zero, self.exposure("baseline", ("write1", "write0")))
        r = next(iter(zero))
        self.assertEqual(judge_direct(self.models["baseline"], r), "UNRESOLVED")
        decoded = json.loads(r[0])
        self.assertEqual(set(decoded), {"binding", "initial", "final"})
        self.assertEqual(decoded["binding"], BINDING)
        self.assertNotIn("history_id", r[0])

    def test_atomic_counter_distinguishes_but_relies_on_its_assumptions(self):
        self.assertTrue(structural_capability(self.models["atomic"]))
        zero = next(iter(self.exposure("atomic", ())))
        write = next(iter(self.exposure("atomic", ("write0",))))
        self.assertNotEqual(zero, write)
        self.assertEqual(consume(self.models["atomic"], zero)["judgment"], "TRUE")
        self.assertEqual(consume(self.models["atomic"], write)["judgment"], "FALSE")
        # Valid MAC plus a false count is possible: the public fixture key is not authority.
        forged_zero = (endpoint(replay(("write0",))), receipt(0))
        self.assertEqual(admit_counter(forged_zero[1]), "ADMITTED")
        self.assertEqual(consume(self.models["atomic"], forged_zero)["judgment"], "TRUE")
        self.assertEqual(consume(self.models["compromised_issuer"], forged_zero)["judgment"], "UNRESOLVED")
        self.assertEqual(replay(("write0",))["committed_write_count"], 1)

    def test_crash_gap_single_write_restores_ambiguity(self):
        zero = self.exposure("crash_gap", ())
        one = self.exposure("crash_gap", ("write0",))
        two = self.exposure("crash_gap", ("write1", "write0"))
        self.assertTrue(zero & one)
        self.assertFalse(zero & two)
        r = next(iter(zero & one))
        self.assertEqual(consume(self.models["crash_gap"], r)["judgment"], "UNRESOLVED")

    def test_reset_bypass_wrap_overcount_and_shared_controls(self):
        for model_id in ("bypass", "reset", "compromised_issuer", "shared_control"):
            with self.subTest(model=model_id):
                self.assertTrue(self.exposure(model_id, ()) & self.exposure(model_id, ("write1", "write0")))
                self.assertFalse(structural_capability(self.models[model_id]))
        # The final reset boundary is required, including a sole same-value write.
        self.assertTrue(self.exposure("reset", ()) & self.exposure("reset", ("write0",)))
        self.assertTrue(self.exposure("wrap_mod2", ()) & self.exposure("wrap_mod2", ("write0", "write0")))
        self.assertFalse(self.exposure("wrap_mod2", ()) & self.exposure("wrap_mod2", ("write0",)))
        self.assertTrue(self.exposure("overcount", ()) & self.exposure("overcount", ("write0",)))
        self.assertEqual(replay(())["committed_write_count"], 0)
        # Common-control replacement can erase even a changed endpoint.
        self.assertTrue(self.exposure("shared_control", ()) & self.exposure("shared_control", ("write1",)))

    def test_invalid_carrier_and_binding_are_not_false_or_zero(self):
        m = self.models["atomic"]
        ep = endpoint(replay(()))
        for atom in ("not-json", canonical({"missing": True}), receipt(0).replace('"mac":"', '"mac":"bad')):
            result = consume(m, (ep, atom))
            self.assertEqual(result["admission"], "REJECTED_CARRIER")
            self.assertIsNone(result["judgment"])
        for field in BINDING:
            binding = dict(BINDING)
            binding[field] += "-other"
            result = consume(m, (ep, receipt(0, binding)))
            self.assertEqual(result["admission"], "REJECTED_BINDING")
            self.assertIsNone(result["judgment"])

    def test_endpoint_projection_conservation_under_unchanged_fault_assumptions(self):
        base = self.models["baseline"]
        for name, extended in self.models.items():
            if name in ("baseline", "shared_control"):
                continue
            for h in base.histories:
                self.assertEqual({r[:1] for r in enumerate_exposure(extended, h)},
                                 set(enumerate_exposure(base, h)), name)
        h = self.by_actions[()]
        self.assertNotEqual({r[:1] for r in enumerate_exposure(self.models["shared_control"], h)},
                            set(enumerate_exposure(base, h)))

    def test_derived_summary_and_separate_consumer_projection(self):
        data = generate()
        baseline = data["summary.json"]["models"]["baseline"]
        atomic = data["summary.json"]["models"]["atomic"]
        self.assertEqual(baseline["distinct_raw_records"], 2)
        self.assertEqual(baseline["judgment_counts_distinct_admitted_records"], {"FALSE": 1, "UNRESOLVED": 1})
        self.assertEqual(atomic["distinct_raw_records"], 7)
        self.assertEqual(atomic["judgment_counts_distinct_admitted_records"], {"FALSE": 6, "TRUE": 1})
        for row in data["consumer-projections.json"]:
            self.assertEqual(set(row), {"record_id", "model_id", "record"})
            self.assertNotIn("history_id", canonical(row["record"]))
            self.assertNotIn("committed_write_count", canonical(row["record"]))
        unresolved = {r["record_id"] for r in data["judgments.json"] if r["judgment"] == "UNRESOLVED"}
        self.assertEqual(unresolved, {r["record_id"] for r in data["certificates.json"]})

    def test_saved_run_roundtrip_and_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp) / "run"
            manifest = write_run(run, max_length=2)
            self.assertEqual(manifest["phase"], "development")
            self.assertEqual(verify_run(run)["status"], "VERIFIED_FINITE_RECOMPUTATION")
            with self.assertRaises(UnsupportedInput):
                write_run(run)
            original = (run / "summary.json").read_bytes()
            altered = json.loads(original)
            altered["models"]["atomic"]["true_histories"] += 1
            blob = (canonical(altered) + "\n").encode()
            (run / "summary.json").write_bytes(blob)
            with self.assertRaises(UnsupportedInput):
                verify_run(run)
            # Updating a digest cannot conceal a result that fails recomputation.
            manifest["artifacts_sha256"]["summary.json"] = hashlib.sha256(blob).hexdigest()
            (run / "manifest.json").write_text(canonical(manifest) + "\n")
            with self.assertRaises(UnsupportedInput):
                verify_run(run)


if __name__ == "__main__":
    unittest.main()
