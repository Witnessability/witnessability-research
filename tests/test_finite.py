import copy
from itertools import combinations, product
import unittest

from witnessability_research.finite import (
    CertificateError, ComputeLimit, FiniteModel, UnsupportedInput,
    compatible_criterion, compatible_direct, enumerate_exposure, judge_criterion,
    judge_direct, make_certificate, pins, structural_capability, structural_collision,
    powerset, verify_certificate)


def model(joint=None, truth=None, faults=((),), alphabets=(("0", "1"), ("0", "1"))):
    joint = joint or {"f": (("0", "0"),), "t": (("1", "1"),)}
    return FiniteModel("test", "binary-claim", tuple(joint), truth or {"f": False, "t": True},
                       ("a", "b"), alphabets, joint, faults)


class FiniteKernelTests(unittest.TestCase):
    def test_outside_model_is_not_vacuous_true(self):
        m = model()
        self.assertEqual(judge_direct(m, ("0", "1")), "OUTSIDE_MODEL")
        self.assertEqual(judge_criterion(m, ("0", "1")), "OUTSIDE_MODEL")
        self.assertEqual(judge_direct(m, ("unknown", "0")), "OUTSIDE_MODEL")
        with self.assertRaises(UnsupportedInput):
            judge_direct(m, ("0",))

    def test_constant_claim_and_empty_support(self):
        m = model(truth={"f": True, "t": True})
        self.assertTrue(structural_capability(m))
        self.assertEqual(judge_direct(m, ("0", "0")), "TRUE")
        self.assertEqual(judge_direct(m, ("0", "1")), "OUTSIDE_MODEL")
        with self.assertRaises(UnsupportedInput):
            FiniteModel("x", "c", (), {}, ("a",), (("0",),), {}, ((),))
        with self.assertRaises(UnsupportedInput):
            model(joint={"f": (), "t": (("1", "1"),)})

    def test_global_incability_does_not_prevent_record_true(self):
        m = model(joint={"f": (("0", "0"),), "t": (("0", "0"), ("1", "1"))})
        self.assertFalse(structural_capability(m))
        self.assertEqual(judge_direct(m, ("1", "1")), "TRUE")
        self.assertEqual(judge_direct(m, ("0", "0")), "UNRESOLVED")

    def test_joint_support_is_not_cartesian_marginals(self):
        m = model(joint={"f": (("0", "0"), ("1", "1")),
                         "t": (("0", "1"), ("1", "0"))})
        self.assertTrue(structural_capability(m))
        self.assertEqual(judge_direct(m, ("0", "0")), "FALSE")
        self.assertEqual(judge_direct(m, ("0", "1")), "TRUE")
        self.assertEqual(len(enumerate_exposure(m, "f")), 2)

    def test_exhaustive_two_domain_joint_supports_and_fault_families(self):
        records = tuple(product(("0", "1"), repeat=2))
        supports = tuple(s for size in range(1, 5) for s in combinations(records, size))
        families = (((),), ((), ("a",)), ((), ("b",)),
                    ((), ("a",), ("b",)), ((), ("a",), ("b",), ("a", "b")))
        checked = 0
        for left, right, faults in product(supports, supports, families):
            m = model(joint={"f": left, "t": right}, faults=faults)
            collision = enumerate_exposure(m, "f") & enumerate_exposure(m, "t")
            self.assertEqual(structural_capability(m), not collision)
            for r in records:
                self.assertEqual(compatible_direct(m, r), compatible_criterion(m, r))
                self.assertEqual(judge_direct(m, r), judge_criterion(m, r))
            if collision:
                r = sorted(collision)[0]
                c = make_certificate(m, r)
                self.assertTrue(verify_certificate(m, r, c, expected_pins=pins(m, r)))
            checked += 1
        self.assertEqual(checked, 1125)

    def test_two_alternative_fault_sets_can_jointly_cover_disagreement(self):
        m = model(faults=((), ("a",), ("b",)))
        self.assertFalse(structural_capability(m))
        collision = structural_collision(m)
        self.assertNotEqual(collision["faults"][0], collision["faults"][1])
        self.assertEqual(judge_direct(m, ("0", "0")), "FALSE")
        self.assertEqual(judge_direct(m, ("1", "0")), "UNRESOLVED")
        for record in (("0", "0"), ("0", "1"), ("1", "0"), ("1", "1")):
            self.assertEqual(compatible_direct(m, record), compatible_criterion(m, record))

    def test_fault_family_and_bounds_are_checked(self):
        with self.assertRaises(UnsupportedInput):
            model(faults=((), ("a", "b")))
        with self.assertRaises(UnsupportedInput):
            model(faults=(("a",),))
        with self.assertRaises(UnsupportedInput):
            model(truth={"f": 0, "t": 1})
        with self.assertRaises(ComputeLimit):
            enumerate_exposure(model(), "f", cap=0)
        with self.assertRaises(ComputeLimit):
            structural_collision(model(), cap=0)
        d = model().to_dict()
        d["binding"] = "non-identity"
        with self.assertRaises(UnsupportedInput):
            FiniteModel.from_dict(d)

    def test_certificate_requires_external_expected_pins(self):
        m = model(faults=((), ("a",), ("b",)))
        r = ("0", "1")
        c = make_certificate(m, r)
        p = pins(m, r)
        self.assertTrue(verify_certificate(m, r, c, expected_pins=p))
        with self.assertRaises(TypeError):
            verify_certificate(m, r, c)
        for key in ("model", "claim", "record"):
            bad = copy.deepcopy(c)
            bad["pins"][key] = "0" * 64
            with self.assertRaises(CertificateError):
                verify_certificate(m, r, bad, expected_pins=p)
        for field, value in (("history", "t"), ("honest", ["1", "0"]), ("fault", [])):
            bad = copy.deepcopy(c)
            bad["witnesses"][0][field] = value
            with self.assertRaises(CertificateError):
                verify_certificate(m, r, bad, expected_pins=p)
        with self.assertRaises(CertificateError):
            verify_certificate(m, ("1", "0"), c, expected_pins=p)
        changed_model = FiniteModel.from_dict(m.to_dict())
        changed_model.name = "different-model"
        with self.assertRaises(CertificateError):
            verify_certificate(changed_model, r, c, expected_pins=p)
        changed_claim = FiniteModel.from_dict(m.to_dict())
        changed_claim.claim = "different-claim"
        with self.assertRaises(CertificateError):
            verify_certificate(changed_claim, r, c, expected_pins=p)
        # Updating the embedded pins cannot override the caller's old expectation.
        replacement = copy.deepcopy(c)
        replacement["pins"] = pins(changed_claim, r)
        with self.assertRaises(CertificateError):
            verify_certificate(changed_claim, r, replacement, expected_pins=p)

    def test_certificate_verifier_does_not_expand_large_product(self):
        domains = tuple("abcdef")
        alphabet = tuple(str(n) for n in range(64))
        zero = ("0",) * 6
        one = ("1",) * 6
        m = FiniteModel("bounded-certificate", "claim", ("f", "t"),
                        {"f": False, "t": True}, domains, (alphabet,) * 6,
                        {"f": (zero,), "t": (one,)}, powerset(domains))
        c = {"schema": "finite-ambiguity-v1", "pins": pins(m, zero), "record": list(zero),
             "witnesses": [{"history": "f", "honest": list(zero), "fault": []},
                           {"history": "t", "honest": list(one), "fault": list(domains)}]}
        self.assertTrue(verify_certificate(m, zero, c, expected_pins=pins(m, zero)))


if __name__ == "__main__":
    unittest.main()
