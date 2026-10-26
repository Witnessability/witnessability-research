"""Check a supplied ambiguity witness without constructing or searching for one.

Derived from witnessability_research.finite.verify_certificate at public commit
9ec68cff4981567705490b44ab5f76ffc0590cbb (lines 242--272).  This extraction keeps
the same exposure-membership criterion; it is not an independent implementation.
The caller supplies a strictly parsed model and trusted external expected pins.
The CLI also binds the actual policy to those pins before invoking this module.
"""

from .common import InvalidCertificate, InvalidInput, PinMismatch, Unsupported, digest
from .context import SCHEMA_VERSION, SEMANTICS_VERSION, validate_expected
from .validation import exact_keys, validated_string


def _array(value, label, *, length=None, maximum=None):
    if type(value) is not list:
        raise InvalidInput(f"{label} must be an array")
    if length is not None and len(value) != length:
        raise InvalidInput(f"{label} must contain exactly {length} elements")
    if maximum is not None and len(value) > maximum:
        raise InvalidInput(f"{label} exceeds its structural limit")
    return value


def _record(value, dimensions, label, budget):
    _array(value, label, length=dimensions)
    for atom in value:
        budget.tick()
        validated_string(atom, label)
    return tuple(value)


def verify_ambiguity(model, record, certificate, *, expected_pins, budget):
    """Validate this witness only; failure implies no record-level verdict.

    ``expected_pins`` must originate outside the certificate.  This function
    verifies the model, claim, record and semantic-context binding.  Its policy
    digest is a trusted caller input: policy acknowledgement/admission belongs
    to the caller (the CLI checks the actual policy bytes before this call).

    Witness order is part of schema 1: false, then true.  Every admissible
    witness in that schema is accepted, not only the first enumeration result.
    """
    budget.tick()
    if type(record) not in (tuple, list):
        raise InvalidInput("record must be a sequence of coordinate atoms")
    record = _record(list(record), len(model.domains), "record", budget)
    exact_keys(certificate, {"schema_version", "semantics_version", "pins",
                             "record", "witnesses"}, "certificate")
    for field, supported in (("schema_version", SCHEMA_VERSION),
                             ("semantics_version", SEMANTICS_VERSION)):
        validated_string(certificate[field], f"certificate.{field}", nonempty=True)
        if certificate[field] != supported:
            raise Unsupported(f"unsupported certificate {field}")
    expected = validate_expected(expected_pins, True, budget)
    embedded = validate_expected(certificate["pins"], True, budget)
    # Charge the current operation's budget, including when a Python caller
    # parsed this immutable model earlier with a different budget instance.
    model_pin = digest(model.to_dict(), budget=budget)
    claim_pin = digest({"claim": model.claim, "truth": dict(model.truth)}, budget=budget)
    actual = {"model": model_pin, "claim": claim_pin,
              "record": digest(list(record), budget=budget),
              "policy": expected["policy"]}
    actual["context"] = digest({"schema_version": SCHEMA_VERSION,
                                "semantics_version": SEMANTICS_VERSION,
                                "model": model_pin, "claim": claim_pin,
                                "policy": expected["policy"]}, budget=budget)
    if expected != actual or embedded != actual:
        raise PinMismatch("certificate or external context pin mismatch")

    certified_record = _record(certificate["record"], len(model.domains),
                               "certificate.record", budget)
    if certified_record != record:
        raise InvalidCertificate("certificate record differs from supplied record")
    witnesses = _array(certificate["witnesses"], "certificate.witnesses", length=2)
    for expected_truth, witness in zip((False, True), witnesses):
        budget.tick()
        exact_keys(witness, {"history", "honest", "fault"}, "witness")
        history = validated_string(witness["history"], "witness.history", nonempty=True)
        honest = _record(witness["honest"], len(model.domains), "witness.honest", budget)
        raw_fault = _array(witness["fault"], "witness.fault", maximum=len(model.domains))
        for domain in raw_fault:
            budget.tick()
            validated_string(domain, "witness.fault element", nonempty=True)
        if len(set(raw_fault)) != len(raw_fault):
            raise InvalidInput("duplicate witness fault-domain identifier")
        fault = frozenset(raw_fault)
        if history not in model.truth or model.truth[history] is not expected_truth:
            raise InvalidCertificate("wrong witness history or truth")

        # Explicitly charge each inspected declared support/fault set; these
        # membership checks never search for a different witness.
        honest_present = False
        for declared in model.joint[history]:
            budget.tick(1 + len(model.domains))
            if honest == declared:
                honest_present = True
                break
        fault_present = False
        for declared in model.faults:
            budget.tick(1 + len(model.domains))
            if fault == declared:
                fault_present = True
                break
        if not honest_present or not fault_present:
            raise InvalidCertificate("witness not in declared support/fault family")

        # Original finite.py lines 264--267: membership in the supplied
        # witness's replacement set, without materializing any product.
        for i, domain in enumerate(model.domains):
            choices = model.alphabets[i] if domain in fault else (honest[i],)
            budget.tick(1 + len(choices))
            if record[i] not in choices:
                raise InvalidCertificate("record not in witness exposure")
    return True
