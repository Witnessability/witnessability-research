#!/usr/bin/env python3
"""Check a counterexample to applying the theorem to domain permutations."""
from itertools import product
import json
from pathlib import Path
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    r0, r1 = (0, 0), (1, 1)
    family = [frozenset(), frozenset({0})]
    def ball(r, f):
        return {u for u in product((0, 1), repeat=2) if all(u[i] == r[i] for i in range(2) if i not in f)}
    def orbit(u):
        return min(u, tuple(reversed(u)))
    observations = [{orbit(u) for f in family for u in ball(r, f)} for r in (r0, r1)]
    intersection = observations[0] & observations[1]
    untransported_cover = any({i for i in range(2) if r0[i] != s[i]} <= f0 | f1
        for s in (r1, tuple(reversed(r1))) for f0 in family for f1 in family)
    assert intersection == {(0, 1)} and not untransported_cover
    # Correct extension transports the second failure set under the domain swap.
    transported = frozenset({1})
    assert frozenset({0, 1}) <= frozenset({0}) | transported
    result = {"domain_permutation_outside_theorem": {
        "r0": r0, "r1": r1, "fault_family": [[], [0]], "shared_observation": [0, 1],
        "untransported_criterion_would_wrongly_predict_separation": True,
        "correct_transport": "F0 union sigma(F1)", "theorem_applicable": False},
        "checked": True}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
