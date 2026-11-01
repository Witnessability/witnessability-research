"""Reconstruct only the declared finite projection in D3 section 8.

No retained experimental data or signatures are consumed. This new arithmetic
cannot verify an original subprocess run, file effect or signature count.
"""
import hashlib
import itertools
import json
from pathlib import Path


def calculate():
    histories = list(itertools.product((0, 1), repeat=4))
    records = []
    for h in histories:
        ua, ub, xa, xb = h
        records.append({"history": h, "claim": bool(ua and xa),
                        "bound": ((ua, ub),) * 3 + ((xa, xb),) * 3,
                        "unbound": (ua + ub,) * 3 + (xa + xb,) * 3})
    tables = {}
    for projection in ("bound", "unbound"):
        classes = {}
        for row in records:
            classes.setdefault(row[projection], []).append(row)
        result = []
        for observation, members in sorted(classes.items()):
            values = {row["claim"] for row in members}
            result.append({"observation": observation,
                           "histories": [row["history"] for row in members],
                           "verdict": "UNRESOLVED" if len(values) == 2 else "TRUE" if True in values else "FALSE"})
        separate_margin = min(sum(a != b for a, b in zip(x[projection], y[projection]))
                              for x in records for y in records if x["claim"] != y["claim"])
        host_margin = min(int(x[projection] != y[projection])
                          for x in records for y in records if x["claim"] != y["claim"])
        tables[projection] = {
            "class_count": len(result), "classes": result,
            "counts": {v: sum(row["verdict"] == v for row in result) for v in ("FALSE", "TRUE", "UNRESOLVED")},
            "six_separate_domain_margin": separate_margin,
            "one_host_domain_margin": host_margin,
        }
    expected = {"bound": {"FALSE": 12, "TRUE": 4, "UNRESOLVED": 0},
                "unbound": {"FALSE": 5, "TRUE": 1, "UNRESOLVED": 3}}
    if any(tables[p]["counts"] != expected[p] for p in expected):
        raise ValueError("projection counts differ from manuscript")
    if (tables["bound"]["six_separate_domain_margin"], tables["bound"]["one_host_domain_margin"],
        tables["unbound"]["six_separate_domain_margin"], tables["unbound"]["one_host_domain_margin"]) != (3, 1, 0, 0):
        raise ValueError("projection margins differ")
    return {"schema": "d3-file-study-projection-recalculation/v1", "status": "PASS",
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "scope": "New finite arithmetic from the manuscript's declared histories and projections; not a replay of the original file study.",
            "history_count": len(histories), "projection_tables": tables,
            "historical_signatures_verified": 0, "new_file_effects_executed": 0,
            "historical_subprocess_invocations_verified": 0,
            "warning": "Original reports, public keys, requests, effect files, source script and digest manifest were not available to this calculation."}


if __name__ == "__main__":
    print(json.dumps(calculate(), indent=2) + "\n", end="")
