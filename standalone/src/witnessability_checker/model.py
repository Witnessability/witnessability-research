"""Strict model ingestion and normalized data, derived from legacy FiniteModel.

No exposure enumeration, certificate construction or collision search lives here.
Every raw list and nested value is checked before conversion to tuple/frozenset.
"""

from dataclasses import dataclass, field
from types import MappingProxyType

from .common import ComputeLimit, InvalidInput, Unsupported, digest
from .validation import exact_keys, validate_json_value, validated_string

MODEL_KEYS = {"name", "claim", "histories", "truth", "domains", "alphabets",
              "joint", "faults", "binding"}


@dataclass(frozen=True)
class FiniteModel:
    name: str
    claim: str
    histories: tuple
    truth: object
    domains: tuple
    alphabets: tuple
    joint: object
    faults: tuple
    binding: str
    _budget: object = field(repr=False, compare=False)

    def to_dict(self):
        # Identical field values and array ordering to legacy to_dict(). Fault
        # names within each set are sorted; the fault-family order is retained.
        return {"name": self.name, "claim": self.claim, "binding": self.binding,
                "histories": list(self.histories), "truth": dict(self.truth),
                "domains": list(self.domains), "alphabets": [list(a) for a in self.alphabets],
                "joint": {h: [list(r) for r in self.joint[h]] for h in self.histories},
                "faults": [sorted(f) for f in self.faults]}

    @property
    def pin(self):
        return digest(self.to_dict(), self._budget)

    @property
    def claim_pin(self):
        return digest({"claim": self.claim, "truth": dict(self.truth)}, self._budget)


def _array(value, label, minimum, maximum, budget):
    budget.tick()
    if type(value) is not list:
        raise InvalidInput(label + " must be an array")
    if minimum == maximum and len(value) != minimum:
        raise InvalidInput(label + " has incorrect length")
    if len(value) < minimum:
        raise InvalidInput(label + " has too few elements")
    if len(value) > maximum:
        raise ComputeLimit(label + " exceeds its structural limit")
    return value


def _distinct_strings(value, label, minimum, maximum, budget, nonempty=False):
    _array(value, label, minimum, maximum, budget)
    seen = set()
    for item in value:
        budget.tick()
        validated_string(item, label + " element", nonempty=nonempty)
        if item in seen:
            raise InvalidInput(label + " contains duplicate elements")
        seen.add(item)
    return seen


def parse_model(raw, budget):
    # Also enforce JSON language for direct Python API callers, not only CLI.
    validate_json_value(raw, budget)
    exact_keys(raw, MODEL_KEYS, "model")
    for key in ("name", "claim", "binding"):
        validated_string(raw[key], key, nonempty=True)
    if raw["binding"] != "identity":
        raise Unsupported("only identity binding is implemented")
    histories = _distinct_strings(raw["histories"], "histories", 1, 400, budget, True)
    domains = _distinct_strings(raw["domains"], "domains", 1, 6, budget, True)
    exact_keys(raw["truth"], histories, "truth map")
    for value in raw["truth"].values():
        budget.tick()
        if type(value) is not bool:
            raise InvalidInput("truth-map values must be booleans, not integers")
    n_domains = len(raw["domains"])
    _array(raw["alphabets"], "alphabets", n_domains, n_domains, budget)
    alphabet_sets = []
    for alphabet in raw["alphabets"]:
        alphabet_sets.append(_distinct_strings(alphabet, "alphabet", 1, 64, budget))
    exact_keys(raw["joint"], histories, "joint supports")
    for support in raw["joint"].values():
        _array(support, "joint support", 1, 4096, budget)
        seen_records = set()
        for record in support:
            _array(record, "support record", n_domains, n_domains, budget)
            for i, atom in enumerate(record):
                budget.tick()
                validated_string(atom, "support atom")
                if atom not in alphabet_sets[i]:
                    raise InvalidInput("joint-support record is outside its alphabets")
            checked_record = tuple(record)
            if checked_record in seen_records:
                raise InvalidInput("duplicate joint-support record")
            seen_records.add(checked_record)
    _array(raw["faults"], "fault family", 1, 64, budget)
    fault_sets = []
    allowed = set()
    for fault in raw["faults"]:
        # Reject repeated members before converting to frozenset.
        members = _distinct_strings(fault, "fault set", 0, 6, budget, True)
        if not members <= domains:
            raise InvalidInput("fault set names an undeclared domain")
        checked_fault = frozenset(members)
        if checked_fault in allowed:
            raise InvalidInput("duplicate fault set")
        allowed.add(checked_fault)
        fault_sets.append(checked_fault)
    if frozenset() not in allowed:
        raise InvalidInput("fault family must include the empty set")
    for fault in fault_sets:
        for domain in fault:
            budget.tick()
            # All immediate subsets + finite induction is equivalent to full
            # downward closure; at most six removals per declared set.
            if fault - {domain} not in allowed:
                raise InvalidInput("fault family is not downward closed")
    return FiniteModel(
        name=raw["name"], claim=raw["claim"], histories=tuple(raw["histories"]),
        truth=MappingProxyType(dict(raw["truth"])), domains=tuple(raw["domains"]),
        alphabets=tuple(tuple(a) for a in raw["alphabets"]),
        joint=MappingProxyType({h: tuple(tuple(r) for r in raw["joint"][h])
                                for h in raw["histories"]}),
        faults=tuple(fault_sets), binding=raw["binding"], _budget=budget)


def validate_record(model, raw, budget):
    # Record atoms outside declared alphabets remain well-formed queries. The
    # complete membership criterion will return OUTSIDE_MODEL for them.
    _array(raw, "record", len(model.domains), len(model.domains), budget)
    for atom in raw:
        budget.tick()
        validated_string(atom, "record atom")
    return tuple(raw)
