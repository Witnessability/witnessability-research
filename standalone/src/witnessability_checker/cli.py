"""Offline operations on a caller-pinned declared finite model."""

import argparse
import json
from pathlib import Path
import sys

from .common import (AdmissionRejected, Budget, ComputeLimit, InvalidCertificate,
                     InvalidInput, MAX_WORK, PinMismatch, Unsupported)
from .context import (IMPLEMENTATION_VERSION, SCHEMA_VERSION, SEMANTICS_VERSION,
                      make_pins, validate_document, validate_expected, validate_policy)
from .model import validate_record
from .validation import (MAX_JSON_BYTES, MAX_JSON_DEPTH, MAX_JSON_NODES,
                         MAX_STRING_LENGTH, loads_strict)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise InvalidInput(message)


def _read(path, budget):
    try:
        with Path(path).open("rb") as stream:
            data = stream.read(MAX_JSON_BYTES + 1)
    except (OSError, ValueError) as exc:
        raise InvalidInput("cannot read an input file") from exc
    return loads_strict(data, budget)


def _parser():
    parser = Parser(description=__doc__)
    subs = parser.add_subparsers(dest="operation", required=True)
    for name in ("evaluate-record", "verify-ambiguity", "check-capability"):
        sub = subs.add_parser(name)
        for flag in ("model", "policy", "expected"):
            sub.add_argument("--" + flag, required=True)
        if name != "check-capability":
            sub.add_argument("--record", required=True)
        if name == "verify-ambiguity":
            sub.add_argument("--certificate", required=True)
        sub.add_argument("--scope", default="raw")
        sub.add_argument("--max-work", type=int, default=MAX_WORK)
    return parser


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    report = {
        "operation": None, "scope": None,
        "versions": {"schema_version": SCHEMA_VERSION,
                     "semantics_version": SEMANTICS_VERSION,
                     "admission_policy_version": None,
                     "implementation_version": IMPLEMENTATION_VERSION},
        "pins": None, "expected_pins": None, "method": None,
        "admission": {"status": "not_checked"}, "completion": "not_completed",
        "limits": {"max_work": MAX_WORK, "max_json_bytes_per_file": MAX_JSON_BYTES,
                   "max_json_depth": MAX_JSON_DEPTH, "max_json_nodes_per_value": MAX_JSON_NODES,
                   "max_string_codepoints": MAX_STRING_LENGTH},
        "work": 0, "status": None, "result": None,
    }
    budget = None
    code = 0
    try:
        args = _parser().parse_args(argv)
        report["operation"] = args.operation
        report["scope"] = args.scope
        report["limits"]["max_work"] = args.max_work
        budget = Budget(args.max_work)
        if args.scope != "raw":
            raise Unsupported("only the raw capability/observation scope is implemented")
        doc = _read(args.model, budget)
        model = validate_document(doc, budget)
        policy = validate_policy(_read(args.policy, budget), budget)
        report["versions"]["admission_policy_version"] = policy["version"]
        has_record = args.operation != "check-capability"
        record = validate_record(model, _read(args.record, budget), budget) if has_record else None
        expected = validate_expected(_read(args.expected, budget), has_record, budget)
        actual = make_pins(doc, model, policy, record, budget=budget)
        report["pins"] = actual
        report["expected_pins"] = expected
        if expected != actual:
            raise PinMismatch("request does not match external expected pins")
        if has_record:
            report["admission"] = {"id": policy["id"], "version": policy["version"],
                                   "status": "accepted" if policy["acknowledged_assumptions"] else "rejected"}
            if not policy["acknowledged_assumptions"]:
                raise AdmissionRejected("declared-model assumptions were not acknowledged")
        else:
            report["admission"] = {"id": policy["id"], "version": policy["version"],
                                   "status": "not_applicable_raw_scope"}
        if args.operation == "verify-ambiguity":
            # Deliberately do not import analysis or a constructor on this path.
            from .verify import verify_ambiguity
            report["method"] = "supplied-witness-exposure-membership"
            certificate = _read(args.certificate, budget)
            verify_ambiguity(model, record, certificate, expected_pins=expected, budget=budget)
            report["result"] = {"valid": True, "record_verdict": "UNRESOLVED",
                                "raw_capability": False}
        elif args.operation == "evaluate-record":
            from .analysis import evaluate_record
            report["method"] = "complete-compatible-disagreement-criterion"
            report["result"] = evaluate_record(model, record, budget)
        else:
            from .capability_command import build_result
            report["method"] = "exact-opposite-truth-disagreement-union-criterion"
            report["result"] = build_result(doc, model, policy, budget)
        report["status"] = "ok"
        report["completion"] = "completed"
    except (InvalidInput, Unsupported, PinMismatch, AdmissionRejected,
            InvalidCertificate, ComputeLimit) as exc:
        types = {InvalidInput: (2, "invalid_input"), Unsupported: (3, "unsupported"),
                 PinMismatch: (4, "pin_mismatch"), AdmissionRejected: (5, "admission_rejected"),
                 InvalidCertificate: (6, "invalid_certificate"), ComputeLimit: (7, "compute_limit")}
        code, report["status"] = types[type(exc)]
        report["error"] = str(exc)
        report["result"] = None
    except Exception:
        code, report["status"] = 8, "compute_error"
        report["error"] = "unexpected computation failure; no mathematical conclusion"
        report["result"] = None
    if budget is not None:
        report["work"] = budget.used
    if code:
        print(report["status"] + ": " + report["error"], file=sys.stderr)
    print(json.dumps(report, sort_keys=True, ensure_ascii=True, allow_nan=False))
    return code
