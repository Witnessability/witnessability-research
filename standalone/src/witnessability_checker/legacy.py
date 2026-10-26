"""Explicit conversion of pinned legacy finite models and ambiguity witnesses.

This module does not import the experiment, store or search/construction code.
It does not migrate the experiment's carrier/admission policy. The caller must
supply trusted legacy pins and explicitly select the new declared-model policy.
Derived new context pins are conversion outputs, not independent trust anchors.
"""

import re

from .common import InvalidInput, PinMismatch, Unsupported, digest
from .context import (SCHEMA_VERSION, SEMANTICS_VERSION, make_pins,
                      validate_document, validate_policy)
from .model import parse_model, validate_record
from .validation import exact_keys
from .verify import verify_ambiguity


def _check_legacy_pins(expected, actual, budget):
    exact_keys(expected, set(actual), "expected legacy pins")
    for key, value in expected.items():
        budget.tick()
        if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise InvalidInput("expected legacy pins must be lowercase SHA-256")
    if expected != actual:
        raise PinMismatch("legacy model/claim/record differs from external expected pins")


def import_model(raw_model, *, expected_legacy_pins, budget):
    """Wrap a strict legacy model, preserving its original semantic hashes.

Required external pins are exactly ``model`` and ``claim``. ``model`` hashes
the old FiniteModel.to_dict() representation using the unchanged local JSON
encoder; ``claim`` hashes {claim, truth}. No old run or carrier is evaluated.
    """
    model = parse_model(raw_model, budget)
    _check_legacy_pins(expected_legacy_pins,
                       {"model": model.pin, "claim": model.claim_pin}, budget)
    budget.tick()
    return {"schema_version": SCHEMA_VERSION,
            "semantics_version": SEMANTICS_VERSION, "model": model.to_dict()}


def import_certificate(document, record, legacy_certificate, policy, *,
                       expected_legacy_pins, budget):
    """Validate and convert a legacy ``finite-ambiguity-v1`` certificate.

The old envelope and pins are checked first. The witnesses are then checked
under the explicit new context without searching for a replacement witness.
The returned certificate has a *new* schema and new policy/context pins; its
model/claim/record hashes retain their old values. This is not source replay.
    """
    model = validate_document(document, budget)
    record = validate_record(model, record, budget)
    policy = validate_policy(policy, budget)
    actual_legacy = {"model": model.pin, "claim": model.claim_pin,
                     "record": digest(list(record), budget)}
    _check_legacy_pins(expected_legacy_pins, actual_legacy, budget)
    exact_keys(legacy_certificate, {"schema", "pins", "record", "witnesses"},
               "legacy certificate")
    if type(legacy_certificate["schema"]) is not str:
        raise InvalidInput("legacy certificate schema must be a string")
    if legacy_certificate["schema"] != "finite-ambiguity-v1":
        raise Unsupported("unsupported legacy certificate schema")
    _check_legacy_pins(legacy_certificate["pins"], actual_legacy, budget)
    new_pins = make_pins(document, model, policy, record)
    converted = {"schema_version": SCHEMA_VERSION,
                 "semantics_version": SEMANTICS_VERSION,
                 "pins": new_pins, "record": legacy_certificate["record"],
                 "witnesses": legacy_certificate["witnesses"]}
    verify_ambiguity(model, record, converted,
                     expected_pins=new_pins, budget=budget)
    return converted
