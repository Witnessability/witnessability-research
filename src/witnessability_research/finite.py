"""Explicit finite joint-support kernel, restricted to identity binding.

The enumeration and disagreement criteria are two algorithms in one codebase,
not independent implementations or a machine-checked proof.
"""

from dataclasses import dataclass
from itertools import combinations, product
import hashlib
import json


class UnsupportedInput(ValueError):
    """Input is malformed or outside the implemented language/bounds."""


class ComputeLimit(RuntimeError):
    """A finite computation exceeded the declared resource bound."""


class CertificateError(ValueError):
    """A certificate does not satisfy the caller's expected pins."""


def canonical(value):
    """Deterministic local JSON encoding; this is not RFC 8785 JCS."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def powerset(items):
    items = tuple(items)
    return tuple(frozenset(s) for n in range(len(items) + 1)
                 for s in combinations(items, n))


@dataclass
class FiniteModel:
    name: str
    claim: str
    histories: tuple
    truth: dict
    domains: tuple
    alphabets: tuple
    joint: dict
    faults: tuple
    binding: str = "identity"

    def __post_init__(self):
        self.histories = tuple(self.histories)
        self.domains = tuple(self.domains)
        self.alphabets = tuple(tuple(a) for a in self.alphabets)
        self.joint = {h: tuple(tuple(r) for r in rs) for h, rs in self.joint.items()}
        self.faults = tuple(frozenset(f) for f in self.faults)
        self.validate()

    def validate(self):
        if self.binding != "identity":
            raise UnsupportedInput("only identity binding is implemented")
        if not isinstance(self.name, str) or not self.name or not isinstance(self.claim, str) or not self.claim:
            raise UnsupportedInput("model and claim names must be nonempty strings")
        if not self.histories or len(self.histories) > 400:
            raise UnsupportedInput("history count must be in 1..400")
        if any(not isinstance(h, str) or not h for h in self.histories) or len(set(self.histories)) != len(self.histories):
            raise UnsupportedInput("history IDs must be distinct nonempty strings")
        if set(self.truth) != set(self.histories) or any(type(v) is not bool for v in self.truth.values()):
            raise UnsupportedInput("one binary truth value is required for each history")
        if not 1 <= len(self.domains) <= 6 or len(set(self.domains)) != len(self.domains):
            raise UnsupportedInput("1..6 distinct domains required")
        if any(not isinstance(d, str) or not d for d in self.domains):
            raise UnsupportedInput("domain names must be strings")
        if len(self.alphabets) != len(self.domains):
            raise UnsupportedInput("one alphabet per domain required")
        for alphabet in self.alphabets:
            if not 1 <= len(alphabet) <= 64 or len(set(alphabet)) != len(alphabet):
                raise UnsupportedInput("alphabet must contain 1..64 distinct atoms")
            if any(not isinstance(a, str) for a in alphabet):
                raise UnsupportedInput("coordinate atoms must be strings")
        if set(self.joint) != set(self.histories):
            raise UnsupportedInput("joint supports must cover exactly the histories")
        for records in self.joint.values():
            if not records or len(records) > 4096:
                raise UnsupportedInput("every joint support must be nonempty and bounded")
            if len(set(records)) != len(records):
                raise UnsupportedInput("duplicate joint-support record")
            for record in records:
                if len(record) != len(self.domains) or any(a not in self.alphabets[i] for i, a in enumerate(record)):
                    raise UnsupportedInput("joint-support record is outside its alphabets")
        allowed = set(self.faults)
        if len(allowed) != len(self.faults) or frozenset() not in allowed:
            raise UnsupportedInput("distinct fault sets including empty are required")
        for fault in allowed:
            if not fault <= set(self.domains) or not set(powerset(sorted(fault))) <= allowed:
                raise UnsupportedInput("fault sets must be explicit and downward closed")
        return self

    def to_dict(self):
        return {"name": self.name, "claim": self.claim, "binding": self.binding,
                "histories": list(self.histories), "truth": dict(self.truth),
                "domains": list(self.domains), "alphabets": [list(a) for a in self.alphabets],
                "joint": {h: [list(r) for r in self.joint[h]] for h in self.histories},
                "faults": [sorted(f) for f in self.faults]}

    @classmethod
    def from_dict(cls, data):
        try:
            return cls(**data)
        except (TypeError, KeyError) as exc:
            raise UnsupportedInput("invalid finite model serialization") from exc

    @property
    def pin(self):
        return digest(self.to_dict())

    @property
    def claim_pin(self):
        return digest({"claim": self.claim, "truth": self.truth})


def _record(model, record):
    if not isinstance(record, (tuple, list)) or len(record) != len(model.domains) or any(not isinstance(a, str) for a in record):
        raise UnsupportedInput("record must have exactly one string atom per domain")
    return tuple(record)


def differences(model, left, right):
    return frozenset(d for d, a, b in zip(model.domains, left, right) if a != b)


def enumerate_exposure(model, history, cap=100000):
    """Direct E(h): union of replacements of whole domain coordinates."""
    if history not in model.joint:
        raise UnsupportedInput("unknown history")
    exposed = set()
    work = 0
    for honest in model.joint[history]:
        for fault in model.faults:
            choices = [model.alphabets[i] if d in fault else (honest[i],)
                       for i, d in enumerate(model.domains)]
            for candidate in product(*choices):
                work += 1
                if work > cap:
                    raise ComputeLimit("exposure replacement cap exceeded")
                exposed.add(candidate)
    return frozenset(exposed)


def compatible_direct(model, record):
    record = _record(model, record)
    return tuple(h for h in model.histories if record in enumerate_exposure(model, h))


def compatible_criterion(model, record):
    record = _record(model, record)
    if any(atom not in model.alphabets[i] for i, atom in enumerate(record)):
        return ()
    return tuple(h for h in model.histories if any(
        differences(model, record, honest) <= fault
        for honest in model.joint[h] for fault in model.faults))


def _judgment(model, compatible):
    values = {model.truth[h] for h in compatible}
    if not values:
        return "OUTSIDE_MODEL"
    if len(values) == 2:
        return "UNRESOLVED"
    return "TRUE" if True in values else "FALSE"


def judge_direct(model, record):
    return _judgment(model, compatible_direct(model, record))


def judge_criterion(model, record):
    return _judgment(model, compatible_criterion(model, record))


def structural_collision(model, cap=2000000):
    """Opposite truths collide iff a disagreement fits F0 union F1."""
    work = 0
    for h0 in model.histories:
        if model.truth[h0]:
            continue
        for h1 in model.histories:
            if not model.truth[h1]:
                continue
            for a in model.joint[h0]:
                for b in model.joint[h1]:
                    diff = differences(model, a, b)
                    for f0 in model.faults:
                        for f1 in model.faults:
                            work += 1
                            if work > cap:
                                raise ComputeLimit("structural comparison cap exceeded")
                            if diff <= f0 | f1:
                                record = tuple(b[i] if d in f0 else a[i]
                                               for i, d in enumerate(model.domains))
                                return {"histories": [h0, h1], "record": list(record),
                                        "honest_records": [list(a), list(b)],
                                        "faults": [sorted(f0), sorted(f1)]}
    return None


def structural_capability(model):
    return structural_collision(model) is None


def pins(model, record):
    record = _record(model, record)
    return {"model": model.pin, "claim": model.claim_pin, "record": digest(list(record))}


def make_certificate(model, record):
    record = _record(model, record)
    if judge_direct(model, record) != "UNRESOLVED":
        raise CertificateError("ambiguity requires both truth values")
    witnesses = []
    for value in (False, True):
        found = None
        for h in model.histories:
            if model.truth[h] != value:
                continue
            for honest in model.joint[h]:
                for fault in model.faults:
                    if differences(model, record, honest) <= fault:
                        found = {"history": h, "honest": list(honest), "fault": sorted(fault)}
                        break
                if found is not None:
                    break
            if found is not None:
                break
        witnesses.append(found)
    return {"schema": "finite-ambiguity-v1", "pins": pins(model, record),
            "record": list(record), "witnesses": witnesses}


def verify_certificate(model, record, certificate, *, expected_pins):
    """Expected pins must come from the caller, not from the certificate."""
    try:
        record = _record(model, record)
        actual = pins(model, record)
        if expected_pins != actual or certificate["pins"] != actual:
            raise CertificateError("pin mismatch")
        if certificate["schema"] != "finite-ambiguity-v1" or certificate["record"] != list(record):
            raise CertificateError("certificate record/schema mismatch")
        witnesses = certificate["witnesses"]
        if len(witnesses) != 2:
            raise CertificateError("two witnesses required")
        for expected_truth, witness in zip((False, True), witnesses):
            history = witness["history"]
            honest = tuple(witness["honest"])
            fault = frozenset(witness["fault"])
            if history not in model.truth or model.truth[history] != expected_truth:
                raise CertificateError("wrong witness truth")
            if honest not in model.joint[history] or fault not in model.faults:
                raise CertificateError("witness not in declared joint support/fault family")
            # Independently check membership in this witness's replacement set.
            # Never materialize a product: even six 64-atom domains are enormous.
            choices = [model.alphabets[i] if d in fault else (honest[i],)
                       for i, d in enumerate(model.domains)]
            if not all(atom in choices[i] for i, atom in enumerate(record)):
                raise CertificateError("record not in witness exposure")
        return True
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, CertificateError):
            raise
        raise CertificateError("malformed certificate") from exc
