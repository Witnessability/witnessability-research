"""Bounded truth-table reference for trusted, prevalidated raw identity models.

This module is an internal, separately authored implementation, not independent
external validation. See README.md and PROVENANCE.md for scope and exclusions.
"""

from dataclasses import dataclass
from itertools import product
from math import prod


class UnsupportedSlice(ValueError):
    """The requested semantics or enumeration size is outside this checker."""


@dataclass(frozen=True)
class Limits:
    max_worlds: int = 65_536
    max_cylinders: int = 100_000
    max_relation_cells: int = 1_000_000


DEFAULT_LIMITS = Limits()


def _slice(model, scope, limits):
    """Eligibility only: this is deliberately not a strict input loader."""
    if scope != "raw":
        raise UnsupportedSlice("only raw scope is supported")
    if model["binding"] != "identity":
        raise UnsupportedSlice("only identity binding is supported")
    if min(limits.max_worlds, limits.max_cylinders,
           limits.max_relation_cells) < 1:
        raise ValueError("limits must be positive")
    domains = model["domains"]
    alphabets = model["alphabets"]
    worlds = prod(len(alphabet) for alphabet in alphabets)
    cylinders = len(model["faults"]) * sum(
        len(model["joint"][history]) for history in model["histories"]
    )
    if worlds > limits.max_worlds:
        raise UnsupportedSlice(
            f"alphabet product {worlds} exceeds max_worlds {limits.max_worlds}"
        )
    if cylinders > limits.max_cylinders:
        raise UnsupportedSlice(
            f"cylinder count {cylinders} exceeds "
            f"max_cylinders {limits.max_cylinders}"
        )
    cells = worlds * len(model["histories"])
    if cells > limits.max_relation_cells:
        raise UnsupportedSlice(
            f"potential relation cells {cells} exceed "
            f"max_relation_cells {limits.max_relation_cells}"
        )
    return worlds, cylinders, cells


def _record_tuple(model, record):
    if not isinstance(record, (list, tuple)):
        raise ValueError("record must be a list or tuple of strings")
    if len(record) != len(model["domains"]) or any(
        not isinstance(atom, str) for atom in record
    ):
        raise ValueError("record shape must match the model coordinates")
    return tuple(record)


def _copy_witness(witness):
    return {
        "history": witness["history"],
        "honest": list(witness["honest"]),
        "fault": list(witness["fault"]),
    }


class Relation:
    """A completed observation-to-history truth table and exposure provenance.

    Construct with compile_model(). Reuse is safe while treating this object
    as immutable. The input model is not retained or modified.
    """

    def __init__(self, histories, domains, universe, world_index, rows,
                 cylinders, true_bits, false_worlds, true_worlds,
                 cylinder_count, relation_cells):
        self.histories = tuple(histories)
        self.domains = tuple(domains)
        self._rows = rows
        self._universe = universe
        self._world_index = world_index
        self._cylinders = cylinders
        self._true_bits = true_bits
        self._false_bits = ((1 << len(histories)) - 1) ^ true_bits
        self._ambiguous_worlds = false_worlds & true_worlds
        self.world_count = len(universe)
        self.cylinder_count = cylinder_count
        self.relation_cells_bound = relation_cells

    def evaluate_record(self, record):
        observed = _record_tuple({"domains": self.domains}, record)
        index = self._world_index.get(observed)
        bits = 0 if index is None else self._rows[index]
        if bits == 0:
            verdict = "OUTSIDE_MODEL"
        elif bits & self._true_bits and bits & self._false_bits:
            verdict = "UNRESOLVED"
        elif bits & self._true_bits:
            verdict = "TRUE"
        else:
            verdict = "FALSE"
        return {
            "verdict": verdict,
            "compatible_histories": [
                history for index, history in enumerate(self.histories)
                if bits & (1 << index)
            ],
        }

    def check_capability(self):
        if not self._ambiguous_worlds:
            return {"capability": True, "collision": None}
        world_bit = self._ambiguous_worlds & -self._ambiguous_worlds
        world_index = world_bit.bit_length() - 1
        bits = self._rows[world_index]
        witnesses = []
        for truth_bits in (self._false_bits, self._true_bits):
            candidates = bits & truth_bits
            history_index = (candidates & -candidates).bit_length() - 1
            for cylinder, witness in self._cylinders[history_index]:
                if cylinder & world_bit:
                    witnesses.append(_copy_witness(witness))
                    break
        return {
            "capability": False,
            "collision": {
                "histories": [w["history"] for w in witnesses],
                "record": list(self._universe[world_index]),
                "honest_records": [w["honest"] for w in witnesses],
                "faults": [w["fault"] for w in witnesses],
            },
        }


def compile_model(model, *, scope="raw", limits=DEFAULT_LIMITS):
    """Compile cylinders from coordinate masks over one full observation universe.

    Faulty coordinates contribute no equality mask. Nonfaulty coordinates
    intersect their masks; cylinders union to exposures. The exposure relation
    is transposed into one history-bitset row per observation. No fault-specific
    Cartesian substitutions or honest-record pair comparisons are performed.
    """
    worlds, cylinder_count, relation_cells = _slice(model, scope, limits)
    domains = tuple(model["domains"])
    alphabets = tuple(tuple(alphabet) for alphabet in model["alphabets"])
    universe = tuple(product(*alphabets))
    world_index = {observed: index for index, observed in enumerate(universe)}
    atom_masks = [{atom: 0 for atom in alphabet} for alphabet in alphabets]
    for index, observed in enumerate(universe):
        bit = 1 << index
        for position, atom in enumerate(observed):
            atom_masks[position][atom] |= bit
    all_worlds = (1 << worlds) - 1
    rows = [0] * worlds
    cylinders = []
    true_bits = 0
    false_worlds = 0
    true_worlds = 0
    for index, history in enumerate(model["histories"]):
        truth = model["truth"][history]
        bit = 1 << index
        if truth:
            true_bits |= bit
        history_worlds = 0
        history_cylinders = []
        for honest in model["joint"][history]:
            for fault in model["faults"]:
                fault_set = frozenset(fault)
                cylinder = all_worlds
                for position, domain in enumerate(domains):
                    if domain not in fault_set:
                        cylinder &= atom_masks[position][honest[position]]
                witness = {
                    "history": history,
                    "honest": tuple(honest),
                    "fault": tuple(fault),
                }
                history_cylinders.append((cylinder, witness))
                history_worlds |= cylinder
        cylinders.append(tuple(history_cylinders))
        if truth:
            true_worlds |= history_worlds
        else:
            false_worlds |= history_worlds
        remaining = history_worlds
        while remaining:
            world_bit = remaining & -remaining
            rows[world_bit.bit_length() - 1] |= bit
            remaining ^= world_bit
    return Relation(model["histories"], domains, universe, world_index, rows,
                    cylinders, true_bits, false_worlds, true_worlds,
                    cylinder_count, relation_cells)


def evaluate_record(model, record, *, scope="raw", limits=DEFAULT_LIMITS):
    """Return exactly verdict and compatible_histories after table completion."""
    _record_tuple(model, record)
    return compile_model(model, scope=scope, limits=limits).evaluate_record(record)


def check_capability(model, *, scope="raw", limits=DEFAULT_LIMITS):
    """Return capability and, if false, an unpinned collision witness."""
    return compile_model(model, scope=scope, limits=limits).check_capability()


def verify_ambiguity(model, record, witnesses, *, scope="raw",
                     limits=DEFAULT_LIMITS):
    """Check the supplied false/true witnesses without generating or searching.

    Returns {'valid': bool}. Invalid shape is also False in this intentionally
    narrow API; this does not reproduce the public processing-status taxonomy.
    No pin, policy, schema, or certificate-envelope checks occur here.
    """
    _slice(model, scope, limits)
    try:
        observed = _record_tuple(model, record)
    except ValueError:
        return {"valid": False}
    if not isinstance(witnesses, (list, tuple)) or len(witnesses) != 2:
        return {"valid": False}
    domains = tuple(model["domains"])
    for expected_truth, witness in zip((False, True), witnesses):
        if not isinstance(witness, dict) or set(witness) != {
            "history", "honest", "fault"
        }:
            return {"valid": False}
        history = witness["history"]
        if not isinstance(history, str) or history not in model["truth"]:
            return {"valid": False}
        if model["truth"][history] is not expected_truth:
            return {"valid": False}
        try:
            honest = _record_tuple(model, witness["honest"])
        except ValueError:
            return {"valid": False}
        if honest not in (tuple(row) for row in model["joint"][history]):
            return {"valid": False}
        fault = witness["fault"]
        if not isinstance(fault, (list, tuple)) or any(
            not isinstance(domain, str) for domain in fault
        ):
            return {"valid": False}
        fault_set = frozenset(fault)
        if len(fault_set) != len(fault) or not fault_set.issubset(domains):
            return {"valid": False}
        if fault_set not in (frozenset(allowed) for allowed in model["faults"]):
            return {"valid": False}
        for index, domain in enumerate(domains):
            allowed_atoms = (model["alphabets"][index] if domain in fault_set
                             else (honest[index],))
            if observed[index] not in allowed_atoms:
                return {"valid": False}
    return {"valid": True}
