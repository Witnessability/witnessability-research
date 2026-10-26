"""Exact finite analysis extracted from the original identity-binding kernel.

This module contains search/analysis and must not be imported by the certificate
verification path.  See ALGORITHM-ORIGINS.md in the private candidate evidence.
"""

from .common import InvalidInput
from .validation import validated_string


def _record(model, record, budget):
    if type(record) not in (tuple, list) or len(record) != len(model.domains):
        raise InvalidInput("record must contain one atom per domain")
    for atom in record:
        budget.tick()
        validated_string(atom, "record atom")
    return tuple(record)


def _differences(model, left, right, budget):
    budget.tick(1 + len(model.domains))
    return frozenset(domain for domain, a, b in zip(model.domains, left, right) if a != b)


def evaluate_record(model, record, budget):
    """Complete original compatible_criterion and _judgment for this record.

    The criterion is equivalent to exposure membership in the declared finite
    language.  No Cartesian replacement product is needed.  All histories are
    visited before a verdict is returned, including TRUE/FALSE/OUTSIDE_MODEL.
    """
    record = _record(model, record, budget)
    for i, atom in enumerate(record):
        budget.tick(1 + len(model.alphabets[i]))
        if atom not in model.alphabets[i]:
            # Exposure never leaves declared alphabets: this is a completed
            # exact exclusion of every history, not a vacuous positive result.
            return {"verdict": "OUTSIDE_MODEL", "compatible_histories": []}
    compatible = []
    for history in model.histories:
        budget.tick()
        found = False
        for honest in model.joint[history]:
            diff = _differences(model, record, honest, budget)
            for fault in model.faults:
                budget.tick(1 + len(model.domains))
                if diff <= fault:
                    found = True
                    break
            if found:
                break
        if found:
            compatible.append(history)
    budget.tick(1 + len(compatible))
    values = {model.truth[history] for history in compatible}
    if not values:
        verdict = "OUTSIDE_MODEL"
    elif len(values) == 2:
        verdict = "UNRESOLVED"
    else:
        verdict = "TRUE" if True in values else "FALSE"
    return {"verdict": verdict, "compatible_histories": compatible}


def check_capability(model, budget):
    """Original structural_collision criterion on the full raw domain.

    Positive result completes all opposite-history/support/fault comparisons.
    Negative result contains the first witnessed collision; its existence
    suffices to refute the global property, without completing the remaining
    comparisons.  The returned witness can be checked by the separate verifier.
    """
    for h0 in model.histories:
        budget.tick()
        if model.truth[h0]:
            continue
        for h1 in model.histories:
            budget.tick()
            if not model.truth[h1]:
                continue
            for a in model.joint[h0]:
                budget.tick()
                for b in model.joint[h1]:
                    diff = _differences(model, a, b, budget)
                    for f0 in model.faults:
                        budget.tick()
                        for f1 in model.faults:
                            budget.tick(1 + 2 * len(model.domains))
                            if diff <= f0 | f1:
                                budget.tick(1 + len(model.domains))
                                record = tuple(b[i] if domain in f0 else a[i]
                                               for i, domain in enumerate(model.domains))
                                collision = {"histories": [h0, h1], "record": list(record),
                                             "honest_records": [list(a), list(b)],
                                             "faults": [sorted(f0), sorted(f1)]}
                                return {"capability": False, "collision": collision}
    return {"capability": True, "collision": None}
