# Third finite reference checker (private research)

This separately authored Python module implements a bounded mathematical
reference for raw identity models. It is part of the same internal agent effort;
it is not external independent validation, a strict public loader, or a full
implementation of the standalone contract.

## Interface

Place this directory on `sys.path` and import `third_checker`. Inputs are plain
Python dictionaries for the inner `model` object in `CONTRACT.md`, not its JSON
envelope. All functions use only Python's standard library.

```python
from third_checker import compile_model, evaluate_record, check_capability
from third_checker import verify_ambiguity, Limits, UnsupportedSlice

compiled = compile_model(model)
compiled.evaluate_record(["0", "1"])
# {"verdict": "UNRESOLVED", "compatible_histories": ["negative", "positive"]}
compiled.check_capability()
# {"capability": False, "collision": {...}}

evaluate_record(model, record)       # Compiles anew; same result shape.
check_capability(model)             # Compiles anew; same result shape.
verify_ambiguity(model, record, witnesses)  # {"valid": True} or {"valid": False}
```

`compatible_histories` follows the model's history order. A negative capability
result's `collision` has `histories` (false then true), `record`, `honest_records`
and `faults`. The collision uses the first ambiguous observation in the product
order induced by the alphabet arrays, the first compatible history of each truth
in model order, and its first covering cylinder. Matching a different checker's
first witness is neither required nor expected. Positive capability has null
`collision`. There is no certificate or pin envelope in these results.

`witnesses` is the supplied two-entry list, false history first, with each entry
exactly `{"history": ..., "honest": [...], "fault": [...]}`. To check a public
certificate mathematically, pass its already-validated record and witnesses;
the caller remains responsible for its envelope, pins and external context.
The verifier checks this supplied pair only. It neither calls `compile_model`
nor enumerates observations nor searches for replacement witnesses. A malformed
witness shape returns `{"valid": False}` in this narrow API; no claim is made
that this matches the public invalid-input/invalid-certificate distinction.
Malformed evaluation-record shape raises `ValueError`.

All top-level operations accept keyword arguments `scope="raw"` and
`limits=Limits(...)`. Other scopes and bindings raise `UnsupportedSlice`.
Compiled objects expose `.world_count`, `.cylinder_count`, and
`.relation_cells_bound`; treat compiled objects as immutable. Compilation owns
copies of all data needed for subsequent queries, so caller model edits do not
change an already-compiled result.

## Algorithm and declared bounds

Construct the entire Cartesian observation universe **once**. For each
coordinate and atom, construct a bit mask of universe observations having that
atom. An honest-record/fault cylinder is the intersection of equality masks on
nonfaulty coordinates; an empty intersection is the whole universe. Union these
cylinders per history, then transpose exposure membership into one history
bitset per observation. Union history exposures by truth value; their bitwise
intersection is exactly the ambiguous-observation set.

This algorithm does not enumerate a Cartesian substitution product for each
fault or compare pairs of honest records using disagreement unions. Capability
collision provenance is recovered from retained cylinder masks, while supplied
witness verification directly checks the declared honest record, fault set and
coordinate membership.

The supported slice is prevalidated raw identity models satisfying all three
configurable bounds:

| Count | Default bound | Exact preflight quantity |
|---|---:|---|
| Universe observations | 65,536 | Product of coordinate alphabet sizes |
| Cylinders | 100,000 | Number of allowed faults times total honest-support records |
| Potential relation cells | 1,000,000 | Universe size times history count |

Bounds are checked before universe construction, including for verification so
all entrypoints share this declared model slice. Exceeding a bound raises
`UnsupportedSlice`, with no mathematical verdict. The potential-cell bound is
conservative even when actual exposure membership is sparse. With `d`
coordinates, `U` universe observations, `C` cylinders and `H` histories,
construction performs `d*U` mask insertions, at most `d*C` big-integer
intersections, `C` cylinder unions and at most `H*U` relation-bit insertions.
These are count bounds, not exact time, byte-memory or OS resource limits.
Retained cylinder bitsets can use `O(C*U)` bits; callers must choose stricter
limits when that worst-case footprint is unsuitable.

## Trusted computing base and exclusions

The caller supplies models already validated against the public model contract,
including actual Boolean truth values, valid dimensions, distinct nonempty
history/domain identifiers, nonempty alphabets/supports/fault family, legal
atoms, valid fault names and downward closure. Only scope, binding, count bounds
and simple operation-record/witness checks are enforced here. Supplying an
invalid model may raise ordinary exceptions or produce meaningless output;
this module is not a safe admission boundary for untrusted input.

The TCB includes that caller/prevalidator, the model's applicability assumptions,
Python's tuple/dictionary/set/integer operations and this module. This checker
does not validate strict JSON/UTF-8, duplicate JSON keys, schema/semantics
versions, expected pins, canonical encoding, admission, cryptographic evidence,
carrier policies, public report construction or resource-budget/status parity.
No full contract, serialization, loader or admission parity is claimed. Bounded
agreement with another checker is evidence about the compared slice only.

## Local tests

Run `python -m unittest -v test_third_checker.py` from this directory. Tests are
small, newly authored examples derived from the mathematical contract. They
cover all record verdicts, complete compatible sets, coupling, whole-coordinate
faults, truth order, several valid and invalid supplied witnesses, direct
verification without compilation, unsupported slice boundaries and reusable
compiled state. The parent research harness supplies the larger differential
comparison; no large exhaustive suite is included here.
