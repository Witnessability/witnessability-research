#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Directed hand-derived controls and six executed wrong semantic functions.

The expected values below are explicit mathematical examples, not majority
outputs or a claimed oracle. All unmutated A/B/C comparisons run before any
mutant. No production source is edited. See PROTOCOL.md for the bounded scope.
"""
import argparse
import copy
import hashlib
from itertools import product
import json
from pathlib import Path
import platform
import sys
import time

sys.dont_write_bytecode = True
from run_consistency import Comparison


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)


def raw_model(name, domains, truth, joint, faults, alphabets=None):
    """Build explicit data; no result or expected value is calculated here."""
    return {
        "name": name, "claim": "declared binary predicate on labelled histories",
        "binding": "identity", "histories": list(truth), "truth": dict(truth),
        "domains": list(domains),
        "alphabets": alphabets or [["0", "1"] for _ in domains],
        "joint": {h: [list(r) for r in rows] for h, rows in joint.items()},
        "faults": [list(f) for f in faults],
    }


def expectation(record, verdict, histories):
    return {"record": list(record), "verdict": verdict,
            "compatible_histories": list(histories)}


def witness(history, honest, fault=()):
    return {"history": history, "honest": list(honest), "fault": list(fault)}


def directed_cases():
    """Literal expectations with their hand-derived justification."""
    correlation = raw_model(
        "M1-preserve-joint-correlation", ("a", "b"),
        {"f": False, "t": True},
        {"f": ("00", "11"), "t": ("01", "10")}, ((),))
    graph = raw_model(
        "M2-nontransitive-confusability", ("a", "b", "c"),
        {"h0": True, "h1": True, "h2": False},
        {"h0": ("000",), "h1": ("001",), "h2": ("111",)},
        ((), ("a",), ("b",), ("c",)))
    two_faults = raw_model(
        "M3-do-not-flatten-fault-family", ("a", "b"),
        {"f": False, "t": True}, {"f": ("00",), "t": ("11",)},
        ((), ("a",), ("b",)))
    disjoint = raw_model(
        "M5-nonvacuous-record-decision", ("a",),
        {"f": False, "t": True}, {"f": ("0",), "t": ("1",)}, ((),),
        [["0", "1", "2"]])
    same_truth = raw_model(
        "M6-opposite-truth-required", ("a",),
        {"f": False, "g": False}, {"f": ("0",), "g": ("0",)}, ((),))
    shared_fault_case = copy.deepcopy(two_faults)
    shared_fault_case["name"] = "M4-two-separately-allowed-faults"
    return [
        {
            "id": "M1-cartesian-marginals",
            "mutant": "cartesianize_joint_support",
            "raw_model": correlation,
            "query": {"operation": "evaluate-record", "record": ["0", "0"]},
            "expected": {"verdict": "FALSE", "compatible_histories": ["f"]},
            "expected_capability": True,
            "record_expectations": [expectation("00", "FALSE", ("f",)),
                                    expectation("01", "TRUE", ("t",))],
            "manual_justification":
                "With no faults, {00,11} and {01,10} are disjoint honest joint "
                "supports. At 00 only f is possible. Each coordinate marginal "
                "of both supports is {0,1}; their Cartesian products invent "
                "the other parity and incorrectly make 00 ambiguous.",
        },
        {
            "id": "M2-components-are-not-record-fibres",
            "mutant": "component_as_record_compatibility",
            "raw_model": graph,
            "query": {"operation": "evaluate-record", "record": ["0", "0", "0"]},
            "expected": {"verdict": "TRUE", "compatible_histories": ["h0", "h1"]},
            "expected_capability": False,
            "record_expectations": [expectation("000", "TRUE", ("h0", "h1")),
                                    expectation("011", "UNRESOLVED", ("h1", "h2"))],
            "manual_justification":
                "Each exposure is the radius-one binary Hamming ball. Distances "
                "between 000/001, 001/111 and 000/111 are 1,2,3. Thus graph edges "
                "are h0-h1 and h1-h2, but not h0-h2. Record 000 has only true "
                "histories h0,h1. Record 011 is shared by h1 and false h2, so "
                "global capability is false. Transitive closure adds false h2 "
                "to the fibre at 000 even though h2 cannot expose that record.",
            "graph_expectation": {"edges": [["h0", "h1"], ["h1", "h2"]],
                                  "nonedges": [["h0", "h2"]]},
        },
        {
            "id": "M3-fault-family-not-its-union",
            "mutant": "flatten_fault_family",
            "raw_model": two_faults,
            "query": {"operation": "evaluate-record", "record": ["1", "1"]},
            "expected": {"verdict": "TRUE", "compatible_histories": ["t"]},
            "expected_capability": False,
            "record_expectations": [expectation("11", "TRUE", ("t",)),
                                    expectation("01", "UNRESOLVED", ("f", "t"))],
            "manual_justification":
                "Each history may change a or b, never both. From f=00, record "
                "11 requires the disallowed joint fault {a,b}; t=11 exposes "
                "it honestly. Replacing the declared family by its union "
                "permits changing both and invents compatibility with f.",
        },
        {
            "id": "M4-two-faults-not-one-shared-fault",
            "mutant": "same_fault_for_both_histories",
            "raw_model": shared_fault_case,
            "query": {"operation": "check-capability", "scope": "raw"},
            "expected": {"capability": False},
            "expected_capability": False,
            "record_expectations": [expectation("01", "UNRESOLVED", ("f", "t"))],
            "manual_witness": {
                "record": ["0", "1"],
                "witnesses": [witness("f", "00", ("b",)),
                              witness("t", "11", ("a",))],
                "expected_valid": True,
            },
            "manual_justification":
                "00 under fault {b} and 11 under fault {a} both expose 01. "
                "These are two alternative histories, so their allowed fault "
                "sets need not be identical. No single allowed fault contains "
                "the disagreement {a,b}; requiring one common fault therefore "
                "misses this real model collision and returns capability true.",
        },
        {
            "id": "M5-empty-compatibility-is-not-true",
            "mutant": "empty_compatibility_is_true",
            "raw_model": disjoint,
            "query": {"operation": "evaluate-record", "record": ["2"]},
            "expected": {"verdict": "OUTSIDE_MODEL", "compatible_histories": []},
            "expected_capability": True,
            "record_expectations": [expectation("0", "FALSE", ("f",)),
                                    expectation("1", "TRUE", ("t",)),
                                    expectation("2", "OUTSIDE_MODEL", ())],
            "manual_justification":
                "Atom 2 is in the declared alphabet but in neither fault-free "
                "exposure. The compatible set is empty. Universal truth over "
                "an empty set must not be returned as TRUE. The two actual "
                "exposures {0} and {1} are disjoint, so capability is true.",
        },
        {
            "id": "M6-ambiguity-needs-opposite-truth",
            "mutant": "verify_without_truth_obligation",
            "raw_model": same_truth,
            "query": {
                "operation": "verify-ambiguity", "record": ["0"],
                "witnesses": [witness("f", "0"), witness("g", "0")],
            },
            "expected": {"valid": False},
            "expected_capability": True,
            "record_expectations": [expectation("0", "FALSE", ("f", "g"))],
            "manual_justification":
                "The supplied distinct histories both honestly expose 0 and "
                "both have truth false. All membership obligations hold, but "
                "there is no true history. This is not an ambiguity witness. "
                "Ignoring the opposite-truth obligation incorrectly accepts it.",
        },
    ]


def positive_controls():
    return [
        {
            "id": "C1-all-true",
            "raw_model": raw_model("all-true", ("a",), {"u": True, "v": True},
                                   {"u": ("0",), "v": ("0",)}, ((),)),
            "expected_capability": True,
            "record_expectations": [expectation("0", "TRUE", ("u", "v")),
                                    expectation("1", "OUTSIDE_MODEL", ())],
            "manual_justification": "Both compatible histories are true; sharing "
                                    "an observation with the same truth is not a collision.",
        },
        {
            "id": "C2-all-false",
            "raw_model": raw_model("all-false", ("a",), {"u": False, "v": False},
                                   {"u": ("0",), "v": ("0",)}, ((),)),
            "expected_capability": True,
            "record_expectations": [expectation("0", "FALSE", ("u", "v")),
                                    expectation("1", "OUTSIDE_MODEL", ())],
            "manual_justification": "Both compatible histories are false; a constant "
                                    "claim is decidable on model exposures, not outside them.",
        },
        {
            "id": "C3-disjoint-opposite-truths",
            "raw_model": raw_model("disjoint", ("a",), {"f": False, "t": True},
                                   {"f": ("0",), "t": ("1",)}, ((),)),
            "expected_capability": True,
            "record_expectations": [expectation("0", "FALSE", ("f",)),
                                    expectation("1", "TRUE", ("t",))],
            "manual_justification": "With no faults, the two opposite-truth "
                                    "histories expose different records.",
        },
        {
            "id": "C4-mixed-with-valid-witness",
            "raw_model": raw_model("mixed", ("a",), {"f": False, "t": True},
                                   {"f": ("0",), "t": ("0", "1")}, ((),)),
            "expected_capability": False,
            "record_expectations": [expectation("0", "UNRESOLVED", ("f", "t")),
                                    expectation("1", "TRUE", ("t",))],
            "manual_witness": {
                "record": ["0"],
                "witnesses": [witness("f", "0"), witness("t", "0")],
                "expected_valid": True,
            },
            "manual_justification": "Record 0 is shared by false f and true t; "
                                    "record 1 is exposed only by true t.",
        },
    ]


# The following helpers serve ONLY the deliberately wrong functions and the
# directed graph display. They are not presented as another independent checker.
def exposures(raw, joint=None, faults=None):
    joint = raw["joint"] if joint is None else joint
    faults = raw["faults"] if faults is None else faults
    result = {}
    for h in raw["histories"]:
        rows = set()
        for honest in joint[h]:
            for fault in faults:
                choices = [raw["alphabets"][i] if d in fault else (honest[i],)
                           for i, d in enumerate(raw["domains"])]
                rows.update(product(*choices))
        result[h] = rows
    return result


def judgment(raw, compatible):
    if not compatible:
        verdict = "OUTSIDE_MODEL"
    else:
        truths = {raw["truth"][h] for h in compatible}
        verdict = "UNRESOLVED" if len(truths) == 2 else ("TRUE" if True in truths else "FALSE")
    return {"verdict": verdict, "compatible_histories": compatible}


def record_result(raw, record, exposed):
    compatible = [h for h in raw["histories"] if tuple(record) in exposed[h]]
    return judgment(raw, compatible)


def cartesianize_joint_support(raw, query):
    """WRONG: replace each joint honest support by its Cartesian marginals."""
    marginals = {}
    for h in raw["histories"]:
        choices = [sorted({r[i] for r in raw["joint"][h]})
                   for i in range(len(raw["domains"]))]
        marginals[h] = list(product(*choices))
    return record_result(raw, query["record"], exposures(raw, joint=marginals))


def component_as_record_compatibility(raw, query):
    """WRONG: expand a record's actual fibre through graph connectivity."""
    exposed = exposures(raw)
    reachable = {h for h in raw["histories"] if tuple(query["record"]) in exposed[h]}
    while True:
        expanded = reachable | {
            h for h in raw["histories"] if any(exposed[h] & exposed[k] for k in reachable)
        }
        if expanded == reachable:
            break
        reachable = expanded
    return judgment(raw, [h for h in raw["histories"] if h in reachable])


def flatten_fault_family(raw, query):
    """WRONG: make all domains occurring in any allowed fault jointly faulty."""
    union = sorted({d for fault in raw["faults"] for d in fault})
    # For exposure, this one maximal set is equivalent to admitting every
    # subset of its union. The original raw model itself is not changed.
    return record_result(raw, query["record"], exposures(raw, faults=[union]))


def same_fault_for_both_histories(raw, query):
    """WRONG: require one F instead of separately allowed F0 and F1."""
    for h0 in raw["histories"]:
        for h1 in raw["histories"]:
            if raw["truth"][h0] == raw["truth"][h1]:
                continue
            for a in raw["joint"][h0]:
                for b in raw["joint"][h1]:
                    differences = {d for d, x, y in zip(raw["domains"], a, b) if x != y}
                    if any(differences <= set(fault) for fault in raw["faults"]):
                        return {"capability": False}
    return {"capability": True}


def empty_compatibility_is_true(raw, query):
    """WRONG: return vacuous TRUE before checking nonempty compatibility."""
    exposed = exposures(raw)
    compatible = [h for h in raw["histories"] if tuple(query["record"]) in exposed[h]]
    if all(raw["truth"][h] for h in compatible):
        return {"verdict": "TRUE", "compatible_histories": compatible}
    return judgment(raw, compatible)


def verify_without_truth_obligation(raw, query):
    """WRONG: check the supplied witnesses' membership, but ignore truth."""
    record = tuple(query["record"])
    witnesses = query["witnesses"]
    if len(witnesses) != 2:
        return {"valid": False}
    for item in witnesses:
        h, honest, fault = item["history"], item["honest"], item["fault"]
        if h not in raw["histories"] or list(honest) not in raw["joint"][h]:
            return {"valid": False}
        if set(fault) not in [set(f) for f in raw["faults"]]:
            return {"valid": False}
        choices = [raw["alphabets"][i] if d in fault else (honest[i],)
                   for i, d in enumerate(raw["domains"])]
        if not all(atom in choices[i] for i, atom in enumerate(record)):
            return {"valid": False}
    return {"valid": True}


MUTANTS = {f.__name__: f for f in (
    cartesianize_joint_support, component_as_record_compatibility,
    flatten_fault_family, same_fault_for_both_histories,
    empty_compatibility_is_true, verify_without_truth_obligation)}


def verify_all(comparator, raw, record, witnesses):
    """Normalize only the expected semantic invalid-witness exceptions."""
    old = comparator.old.FiniteModel.from_dict(raw)
    document = {"schema_version": comparator.context.SCHEMA_VERSION,
                "semantics_version": comparator.context.SEMANTICS_VERSION, "model": raw}
    model = comparator.context.validate_document(document, comparator.common.Budget())
    old_pins = comparator.old.pins(old, record)
    legacy = {"schema": "finite-ambiguity-v1", "pins": old_pins,
              "record": list(record), "witnesses": copy.deepcopy(witnesses)}
    result = {}
    try:
        valid = comparator.old.verify_certificate(old, record, legacy, expected_pins=old_pins)
        result["A"] = {"valid": valid}
    except comparator.old.CertificateError as exc:
        result["A"] = {"valid": False, "rejection": type(exc).__name__, "message": str(exc)}
    expected = comparator.context.make_pins(
        document, model, comparator.policy, record, comparator.common.Budget())
    certificate = {"schema_version": document["schema_version"],
                   "semantics_version": document["semantics_version"],
                   "pins": expected, "record": list(record),
                   "witnesses": copy.deepcopy(witnesses)}
    try:
        valid = comparator.verify.verify_ambiguity(
            model, record, certificate, expected_pins=expected, budget=comparator.common.Budget())
        result["B"] = {"valid": valid}
    except comparator.common.InvalidCertificate as exc:
        result["B"] = {"valid": False, "rejection": type(exc).__name__, "message": str(exc)}
    result["C"] = comparator.third.verify_ambiguity(raw, record, witnesses)
    return result


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def check_unmutated(comparator, item):
    raw = item["raw_model"]
    actual = comparator.compare(raw)
    require(actual["capability"] is item["expected_capability"],
            item["id"] + ": all implementations disagree with manual capability expectation")
    for expected in item["record_expectations"]:
        matches = [r for r in actual["records"] if r["record"] == expected["record"]]
        require(matches == [expected],
                item["id"] + ": manual record expectation mismatch: " + canonical(matches))
    result = {"comparison": actual}
    if "manual_witness" in item:
        w = item["manual_witness"]
        verified = verify_all(comparator, raw, w["record"], w["witnesses"])
        require(all(v["valid"] is w["expected_valid"] for v in verified.values()),
                item["id"] + ": manual witness expectation mismatch")
        result["manual_witness_checks"] = verified
    if item.get("query", {}).get("operation") == "verify-ambiguity":
        q = item["query"]
        verified = verify_all(comparator, raw, q["record"], q["witnesses"])
        require(all(v["valid"] is item["expected"]["valid"] for v in verified.values()),
                item["id"] + ": manual certificate expectation mismatch")
        result["query_witness_checks"] = verified
    if "graph_expectation" in item:
        # Display graph from A's actual exposure routine, not the mutant helper.
        old = comparator.old.FiniteModel.from_dict(raw)
        ex = {h: comparator.old.enumerate_exposure(old, h) for h in old.histories}
        edges = [[h, k] for i, h in enumerate(old.histories)
                 for k in old.histories[i + 1:] if ex[h] & ex[k]]
        require(edges == item["graph_expectation"]["edges"],
                item["id"] + ": manual nontransitive graph expectation mismatch")
        result["actual_collision_graph_edges"] = edges
    return result


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def source_pins(source, reference):
    files = [Path(__file__), Path(__file__).with_name("run_consistency.py"),
             Path(__file__).with_name("PROTOCOL.md"), reference / "third_checker.py",
             source / "src/witnessability_research/finite.py"]
    files += sorted((source / "standalone/src/witnessability_checker").glob("*.py"))
    return [{"path": str(p.resolve()), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in files]


def run(args):
    source, reference, output = args.source.resolve(), args.reference.resolve(), args.output.resolve()
    case_dir = output.with_name(output.stem + "-cases")
    if output.exists() or case_dir.exists():
        raise RuntimeError("refusing to overwrite an existing result or case directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir()
    before = source_pins(source, reference)
    start = time.monotonic()
    report = {
        "schema": "r0206-directed-mutations-1", "status": "running",
        "python": platform.python_version(), "implementation": platform.python_implementation(),
        "command": sys.argv, "source": str(source), "reference": str(reference),
        "source_files": before, "controls": [], "mutations": [],
        "expected_basis": "literal hand-derived expectations fixed in this script, not majority vote",
        "scope": "internal bounded mathematical controls and deliberately wrong functions; "
                 "not authoritative oracle, external validation or real capture",
        "production_source_modified": False,
    }
    pending = []
    try:
        comparator = Comparison(source, reference)
        # Finish all baseline comparisons before executing any wrong function.
        for kind, items in (("control", positive_controls()), ("mutation", directed_cases())):
            for item in items:
                baseline = check_unmutated(comparator, item)
                row = {**item, "kind": kind, "unmutated": baseline,
                       "unmutated_matches_manual_expectations": True}
                pending.append(row)
        report["unmutated_models_checked"] = len(pending)
        report["unmutated_record_queries"] = sum(
            len(row["unmutated"]["comparison"]["records"]) for row in pending)
        for row in pending:
            if row["kind"] == "mutation":
                original = canonical(row["raw_model"])
                wrong = MUTANTS[row["mutant"]](row["raw_model"], row["query"])
                require(canonical(row["raw_model"]) == original, "mutant changed its input model")
                row["actual_mutant_result"] = wrong
                row["mutation_detected"] = wrong != row["expected"]
                path = case_dir / (row["id"] + ".json")
                write_json(path, row)
                report["mutations"].append({
                    "id": row["id"], "file": str(path), "expected": row["expected"],
                    "actual": wrong, "detected": row["mutation_detected"]})
                require(row["mutation_detected"], row["id"] + ": mutant survived declared control")
            else:
                path = case_dir / (row["id"] + ".json")
                write_json(path, row)
                report["controls"].append({"id": row["id"], "file": str(path), "passed": True})
        require(len(report["mutations"]) == 6, "expected exactly six executed mutants")
        require(source_pins(source, reference) == before, "source changed during directed checks")
        report["status"] = "pass"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = type(exc).__name__ + ": " + str(exc)
        if "item" in locals():
            report["current_case"] = item
    report["elapsed_seconds"] = time.monotonic() - start
    report["case_files"] = [
        {"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in sorted(case_dir.glob("*.json"))]
    write_json(output, report)
    print(json.dumps({"status": report["status"], "controls": len(report["controls"]),
                      "mutants_executed": len(report["mutations"]),
                      "mutants_detected": sum(m["detected"] for m in report["mutations"]),
                      "elapsed_seconds": report["elapsed_seconds"],
                      "output": str(output)}, indent=2))
    return 0 if report["status"] == "pass" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
