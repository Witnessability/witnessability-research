"""Capability analysis and negative-certificate construction, loaded on demand.

The verifier's import closure must never include this module.  Construction
wraps the original structural-collision witness; it does not perform a second
search and it does not assert that a positive capability has a pair certificate.
"""

from .analysis import check_capability
from .context import SCHEMA_VERSION, SEMANTICS_VERSION, make_pins


def build_result(document, model, policy, budget):
    result = check_capability(model, budget)
    collision = result["collision"]
    if collision is None:
        result["certificate"] = None
        return result
    record = collision["record"]
    pins = make_pins(document, model, policy, record, budget=budget)
    budget.tick(1 + 2 * len(model.domains))
    result["certificate"] = {
        "schema_version": SCHEMA_VERSION, "semantics_version": SEMANTICS_VERSION,
        "pins": pins, "record": record,
        "witnesses": [{"history": history, "honest": honest, "fault": fault}
                      for history, honest, fault in zip(collision["histories"],
                                                        collision["honest_records"],
                                                        collision["faults"])],
    }
    return result
