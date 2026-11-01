#!/usr/bin/env python3
"""Small resolution certificate verifier for the local propositional lemmas.

This verifies clauses and resolution steps, not the translation of arbitrary
records/group actions into these local predicates or the complete theorem.
It is a same-preparer implementation, not an independent proof assistant.
"""
import argparse
import hashlib
import json
from pathlib import Path


def check(certificate):
    clauses = [frozenset(c) for c in certificate["premises"]]
    assert clauses and all(all(isinstance(x, int) and x != 0 for x in c) for c in clauses)
    assert all(not any(-x in c for x in c) for c in clauses)
    for step in certificate["steps"]:
        left, right, pivot = step["left"], step["right"], step["pivot"]
        assert isinstance(pivot, int) and pivot > 0
        assert 0 <= left < len(clauses) and 0 <= right < len(clauses)
        a, b = clauses[left], clauses[right]
        if pivot in a and -pivot in b:
            expected = (a - {pivot}) | (b - {-pivot})
        elif -pivot in a and pivot in b:
            expected = (a - {-pivot}) | (b - {pivot})
        else:
            raise AssertionError("No complementary pivot in the parent clauses.")
        assert not any(-x in expected for x in expected)
        assert frozenset(step["clause"]) == expected
        clauses.append(expected)
    assert clauses[-1] == frozenset()
    return len(certificate["steps"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--certificates", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    certificates = json.loads(args.certificates.read_text())
    checked, rejected = {}, 0
    for name, certificate in certificates.items():
        checked[name] = check(certificate)
        # Check that the verifier detects a false final resolvent.
        mutant = json.loads(json.dumps(certificate))
        mutant["steps"][-1]["clause"] = [99]
        try:
            check(mutant)
        except AssertionError:
            rejected += 1
        else:
            raise AssertionError("An invalid certificate was accepted.")
    # Exhaust every Boolean abstraction of cover and the blend's equality to y.
    blend_checks = 0
    for f0 in (False, True):
        for f1 in (False, True):
            for equal in (False, True):
                covered = f0 or f1 or equal
                uy = f0 or equal
                ux = (not f0) or equal
                assert (f0 or ux)
                assert (not covered) or (f1 or uy)
                blend_checks += 1
    result = {"checked_certificates": checked, "resolution_steps": sum(checked.values()),
              "invalid_certificate_rejections": rejected, "blend_boolean_cases": blend_checks,
              "scope": "two local propositional implications conditional on equality/transformation interpretation",
              "full_first_order_or_Lean_theorem_checked": False,
              "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
