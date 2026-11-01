#!/usr/bin/env python3
"""Finite D3 anchor calculations; no native engine, external input, or network.

Each model has H={0,1}, p(h)=h, and one honest record per history.
Records are bit tuples; failure blocks partition bit positions. Full product
binding permits every coordinate XOR, while diagonal binding permits identity
and complement of all bits. These are bijections inside each failure block.

The direct path enumerates replacement values for every allowed failed block,
then quotients all resulting records into group orbits. The structural path
only tests honest-record disagreement sets against unions of failure sets.
They share model data and group actions, not their decision procedures.
"""

import argparse
import hashlib
import itertools
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def powerset(items, max_size):
    for size in range(max_size + 1):
        for chosen in itertools.combinations(items, size):
            yield frozenset(chosen)


def xor(record, mask):
    return tuple(a ^ b for a, b in zip(record, mask))


def group(width, kind):
    if kind == "product":
        return tuple(itertools.product((0, 1), repeat=width))
    if kind == "diagonal":
        return ((0,) * width, (1,) * width)
    raise ValueError("unknown binding group")


def orbit(record, transforms):
    return frozenset(xor(record, mask) for mask in transforms)


def quotient_key(record, transforms):
    return min(orbit(record, transforms))


def model(n_data, n_anchors, shared_anchors=False):
    width = n_data + n_anchors
    blocks = tuple((i,) for i in range(width))
    if shared_anchors:
        require(n_anchors > 0, "shared anchor model needs an anchor")
        blocks = tuple((i,) for i in range(n_data)) + (tuple(range(n_data, width)),)
    require(sorted(i for block in blocks for i in block) == list(range(width)), "block partition")
    return {
        "n_data": n_data,
        "n_anchors": n_anchors,
        "bit_width": width,
        "blocks": blocks,
        "honest": ((0,) * width, (1,) * n_data + (0,) * n_anchors),
    }


def exposed_records(honest, blocks, transforms, failures):
    """Directly realize every replacement; keep one explanation per orbit."""
    exposed = {}
    for failed in failures:
        positions = tuple(i for domain in sorted(failed) for i in blocks[domain])
        for replacements in itertools.product((0, 1), repeat=len(positions)):
            raw = list(honest)
            for i, bit in zip(positions, replacements):
                raw[i] = bit
            raw = tuple(raw)
            key = quotient_key(raw, transforms)
            exposed.setdefault(key, {"faults": sorted(failed), "raw": raw})
    return exposed


def direct(honest, blocks, transforms, failures):
    exposed = [exposed_records(r, blocks, transforms, failures) for r in honest]
    common = sorted(set(exposed[0]).intersection(exposed[1]))
    witness = None
    if common:
        key = common[0]
        witness = {"orbit_representative": key, "h0": exposed[0][key], "h1": exposed[1][key]}
    return {"exact": not common, "orbit_counts_by_history": [len(e) for e in exposed],
            "shared_orbit_count": len(common), "obstruction": witness}


def disagreements(left, right, blocks):
    return frozenset(g for g, block in enumerate(blocks)
                     if any(left[i] != right[i] for i in block))


def structural(honest, blocks, transforms, failures):
    """Theorem 1 specialization, using F0 union F1 rather than a threshold."""
    for mask in transforms:
        difference = disagreements(honest[0], xor(honest[1], mask), blocks)
        for f0 in failures:
            for f1 in failures:
                if difference.issubset(f0.union(f1)):
                    return {"exact": False, "obstruction": {
                        "h0": 0, "h1": 1, "r0": honest[0], "r1": honest[1],
                        "xor_mask": mask, "disagreement_domains": sorted(difference),
                        "F0": sorted(f0), "F1": sorted(f1)}}
    return {"exact": True, "obstruction": None}


def evaluate(spec, kind):
    blocks, honest = spec["blocks"], spec["honest"]
    transforms = group(spec["bit_width"], kind)
    alphabet = tuple(itertools.product((0, 1), repeat=spec["bit_width"]))
    # Basic action/orbit checks do not invoke either decision procedure.
    transform_set = set(transforms)
    require((0,) * spec["bit_width"] in transform_set, "missing identity")
    require(all(xor(a, b) in transform_set for a in transforms for b in transforms), "not a group")
    partition = {quotient_key(record, transforms) for record in alphabet}
    require(all(quotient_key(xor(record, mask), transforms) == quotient_key(record, transforms)
                for record in alphabet for mask in transforms), "orbit projection not invariant")
    margin = min(len(disagreements(honest[0], xor(honest[1], mask), blocks))
                 for mask in transforms)
    budgets = []
    for t in range(len(blocks) + 1):
        failures = tuple(powerset(range(len(blocks)), t))
        d = direct(honest, blocks, transforms, failures)
        s = structural(honest, blocks, transforms, failures)
        require(d["exact"] == s["exact"], "direct and structural disagree")
        require(d["exact"] == (margin > 2 * t), "cardinality threshold disagrees")
        budgets.append({"t": t, "allowed_failure_set_count": len(failures),
                        "direct": d, "structural": s, "threshold_exact": margin > 2 * t})
    return {**spec, "binding": kind, "group_size": len(transforms),
            "raw_record_count": len(alphabet), "orbit_count": len(partition),
            "honest_orbits": [sorted(orbit(r, transforms)) for r in honest],
            "domain_margin": margin, "budgets": budgets}


def run():
    separate = []
    for n_data in range(1, 4):
        for n_anchors in range(4):
            spec = model(n_data, n_anchors)
            for kind in ("product", "diagonal"):
                result = evaluate(spec, kind)
                expected_margin = 0 if kind == "product" else min(n_data, n_anchors)
                require(result["domain_margin"] == expected_margin, "anchor margin formula disagrees")
                separate.append(result)
    shared = [evaluate(model(2, 2, shared_anchors=True), kind) for kind in ("product", "diagonal")]
    require(shared[1]["domain_margin"] == 1, "shared anchors should form one distinguishing block")
    unshared = next(r for r in separate if (r["n_data"], r["n_anchors"], r["binding"]) == (2, 2, "diagonal"))
    require(unshared["domain_margin"] == 2, "separate-anchor model margin")
    three = [r for r in separate if (r["n_data"], r["n_anchors"]) == (2, 1)]
    # Explicit boundaries catch the overclaims this example is intended to fix.
    anchor_count_counterexample = next(r for r in separate
                                      if (r["n_data"], r["n_anchors"], r["binding"]) == (1, 3, "diagonal"))
    require(anchor_count_counterexample["domain_margin"] != anchor_count_counterexample["n_anchors"],
            "counterexample does not refute margin equals anchor count")
    no_anchor = next(r for r in separate if (r["n_data"], r["n_anchors"], r["binding"]) == (3, 0, "diagonal"))
    require(not no_anchor["budgets"][0]["direct"]["exact"], "no anchor should leave global ambiguity")
    one_anchor = next(r for r in three if r["binding"] == "diagonal")
    require(one_anchor["budgets"][0]["direct"]["exact"], "one anchor should separate at t=0")
    require(not one_anchor["budgets"][1]["direct"]["exact"], "one anchor must not imply t=1 tolerance")
    all_cases = separate + shared
    return {
        "schema": "d3-anchor-enumeration/v1", "status": "PASS",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Authored finite binary models, singleton honest supports, XOR product/diagonal actions, arbitrary replacement by declared failure blocks.",
        "separate_domain_model_group_pairs": len(separate),
        "shared_domain_model_group_pairs": len(shared),
        "cardinality_budget_comparisons": sum(len(r["budgets"]) for r in all_cases),
        "all_direct_structural_threshold_agree": True,
        "separate_domain_models": separate,
        "shared_anchor_models": shared,
        "three_coordinate_example": three,
        "anchor_count_only_counterexample": {
            "n_data": 1, "n_anchors": 3, "binding": "diagonal", "domain_margin": 1,
            "claimed_anchor_count_margin": 3, "claim_holds": False},
        "new_native_engine_calls": 0,
        "limits": [
            "Finite consistency check; not a proof of the general D3 theorem.",
            "Model decomposition into failure blocks is declared, not inferred from physical independence.",
            "Product-to-diagonal comparisons keep H, J, alphabets and failure blocks fixed; adding anchors changes the model.",
            "Direct and structural implementations share model conventions and one author; no independent validation claimed.",
            "No C2, Probity, Research Checker, Core, Coverage, or PostgreSQL execution."
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(run(), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
