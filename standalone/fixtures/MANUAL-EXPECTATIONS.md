# Tiny controls fixed before semantic implementation runs

Prepared 2026-10-26. These are hand-derived expectations, not measured outputs,
not a new preregistered experiment, and not an independent oracle.

All controls use identity binding and explicit finite support. Policy
`declared-model` version `1` only acknowledges the declared assumptions. It
makes no assertion about actual capture or signatures. No tests have been
run to produce the expectations below.

## mixed (one coordinate x; no faults)

Alphabet x = {0,1,2,3}. Histories f and g are false; t is true.
Honest joint supports: f={0}, g={0,2}, t={0,1}. Only empty fault allowed.
Thus exposure equals the stated honest support.

| Record | Compatible histories | Expected record verdict | Reason |
|---|---|---|---|
| 0 | f,g,t | UNRESOLVED | Both truth values remain |
| 1 | t | TRUE | Nonempty and only true |
| 2 | g | FALSE | Nonempty and only false |
| 3 | none | OUTSIDE_MODEL | Empty compatible set |
| outside | none | OUTSIDE_MODEL | Atom is outside every support/alphabet |

Raw capability is false: record 0 belongs to f and t with opposite truth.
Record 1 is nevertheless TRUE, so global failure does not force every record
verdict to be unresolved. A certificate at 0 using f/t is valid. A distinct
certificate at 0 using g/t is equally valid, though f precedes g in the input.
Changing the first witness to t makes that certificate invalid and establishes
no record verdict. The unchanged input still has the valid f/t certificate.

## separated (one coordinate x; no faults)

Alphabet x = {0,1,2}. False history f has honest support {0}; true t has {1}.
The two exposures are disjoint. Raw capability is true. Record 2 remains
OUTSIDE_MODEL; global capability does not make all syntactic records inhabited.

## alternative-faults (two coordinates a,b)

Both alphabets = {0,1}. False f has only honest 00 and true t only honest 11.
Allowed faults are {}, {a}, {b}; the family is downward closed. Record 10
comes from f by fault {a} and from t by fault {b}; it is UNRESOLVED and raw
capability is false. Each supplied honest observation is in its joint support.

## Processing expectations (not mathematical verdicts)

- A mismatched externally supplied model, claim, record, policy or context pin
  rejects processing, including a fully self-consistent substituted model,
  record and certificate with the original external expected context.
- `acknowledged_assumptions=false` is admission rejection, distinct from an
  unknown policy/version and distinct from malformed input.
- Unknown schema/semantics and admitted-only capability are unsupported.
- Malformed types, duplicated JSON keys/elements and non-downward-closed fault
  families are invalid input. Quota exhaustion is ComputeLimit.
- An invalid supplied certificate produces no claim verdict or capability
  determination. Verification may accept another valid certificate later.

The original 1125 two-coordinate combinations are retained as a bounded
consistency/regression comparison to the pinned old implementation. Agreement
is not an independent implementation or general correctness proof.
