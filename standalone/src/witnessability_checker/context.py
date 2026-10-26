"""Versioned model/policy context and caller-supplied expected pin checks."""

from .common import InvalidInput, Unsupported, digest
from .model import parse_model
from .validation import exact_keys, validate_json_value, validated_string

SCHEMA_VERSION = "wresearch-checker-input-1"
SEMANTICS_VERSION = "finite-joint-identity-1"
IMPLEMENTATION_VERSION = "0.2.0.dev1"
ADMISSION_POLICY_ID = "declared-model"
ADMISSION_POLICY_VERSION = "1"


def validate_versions(raw):
    for key, supported in (("schema_version", SCHEMA_VERSION),
                           ("semantics_version", SEMANTICS_VERSION)):
        validated_string(raw[key], key, nonempty=True)
        if raw[key] != supported:
            raise Unsupported("unsupported " + key)


def validate_document(raw, budget):
    exact_keys(raw, {"schema_version", "semantics_version", "model"}, "model document")
    validate_versions(raw)
    budget.tick(2)
    return parse_model(raw["model"], budget)


def validate_policy(raw, budget):
    validate_json_value(raw, budget)
    exact_keys(raw, {"id", "version", "acknowledged_assumptions"}, "admission policy")
    validated_string(raw["id"], "policy id", nonempty=True)
    validated_string(raw["version"], "policy version", nonempty=True)
    if type(raw["acknowledged_assumptions"]) is not bool:
        raise InvalidInput("acknowledged_assumptions must be a boolean")
    if raw["id"] != ADMISSION_POLICY_ID or raw["version"] != ADMISSION_POLICY_VERSION:
        raise Unsupported("unsupported admission policy or version")
    # False is a supported policy's rejection, handled separately by caller.
    return dict(raw)


def validate_expected(raw, record_required, budget):
    if type(record_required) is not bool:
        raise InvalidInput("record_required must be a boolean")
    keys = {"model", "claim", "policy", "context"}
    if record_required:
        keys.add("record")
    exact_keys(raw, keys, "expected pins")
    for value in raw.values():
        budget.tick()
        if type(value) is not str or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise InvalidInput("pins must be lowercase SHA-256 hexadecimal strings")
    return dict(raw)


def make_pins(document, model, policy, record=None, budget=None):
    """Construct hashes; this does not establish their external trustworthiness.

    Model, policy and document must already have passed their strict validators.
    Model/claim/record hashes retain legacy meaning. New policy/context hashes
    bind schema and semantics identities without including implementation name.
    """
    if budget is None:
        budget = model._budget
    result = {"model": digest(model.to_dict(), budget),
              "claim": digest({"claim": model.claim, "truth": dict(model.truth)}, budget),
              "policy": digest(policy, budget)}
    result["context"] = digest({"schema_version": document["schema_version"],
                                "semantics_version": document["semantics_version"],
                                "model": result["model"], "claim": result["claim"],
                                "policy": result["policy"]}, budget)
    if record is not None:
        result["record"] = digest(list(record), budget)
    return result
