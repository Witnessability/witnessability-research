<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# R02-06: bounded differential validation protocol

Protocol revision 1, prepared before the pilot and full runs on 2026-10-26.
The target is PC-WR-02-002, source tree
`57ab2f7494d14f74e711a3a75ea8f722e53a7ee5`, raw identity semantics
`finite-joint-identity-1`. This is internal consistency validation, not an
external implementation, authoritative oracle, capture validation or full 3x3.

## Frozen classes

All histories and coordinates are labelled; no symmetry quotient is used.
All atoms are strings. Fault families are all downward-closed subsets of the
coordinate powerset containing the empty set: 5 for two and 19 for three
coordinates. They are generated independently by testing closure of all
candidate families.

1. `legacy-2x2`: two histories, two binary coordinates, fixed false/true map;
   each support is any of the 15 nonempty subsets of the four records.
   Exactly 15^2 * 5 = **1,125 models**.
2. `singleton-3x3`: three histories, three binary coordinates, one honest
   record per history (8 choices independently), all eight truth maps, all
   19 families. Exactly 8^3 * 8 * 19 = **77,824 models**.
3. `joint-catalog-3x3`: three histories, three binary coordinates; each support
   independently selected from the same six-entry catalog: the four unordered
   antipodal pairs `{r, complement(r)}` and the even/odd parity supports (four
   records each). All eight truth maps and 19 families. Exactly 6^3 * 8 * 19 =
   **32,832 models**. This is exhaustive ONLY over this declared catalog;
   it does not cover all nondeterministic supports of size two or four.

Every model is evaluated at every in-alphabet record, plus one well-formed
out-of-alphabet record (`__outside__` in the first coordinate). Expected total:
**111,781 models; 1,001,529 record queries**. Every model has a capability check.
The legacy 2x2 set is retained as a separately reported class.

## Implementations and comparison

A: original `finite.py`: Cartesian exposure enumeration for record membership,
with its direct exposure intersection used for capability in the harness.
B: installed-component source algorithms: strict model parse, disagreement
membership and opposite-truth support/fault-union criterion.
C: separately authored internal reference checker: complete observation
universe, coordinate-value bit masks, intersections for honest coordinates and
unions of cylinders per history. Its author reads the public-facing contract,
which describes A/B algorithms, but no implementation sources or tests.
It is source-blind authoring, not theory-blind or external independent work.

Compare complete compatible-history lists, verdicts and raw capability. Do not
require identical selected collisions. For each negative capability, verify
both B's and C's supplied collisions with A, B and C witness checks. B uses
externally supplied expected pins constructed by the harness from the trusted
test input; this checks plumbing, not independent provenance of the model.
Certificate validation MUST NOT search for a replacement witness.

## Directed controls and mutations

Retain concrete controls for jointly useful channels, nontransitive collision
graphs, record TRUE while global capability is false, and common-control fault
families. Execute separately labelled deliberately wrong implementations:
vacuous TRUE for empty compatibility; Cartesianization of joint supports;
connected components used as a record's compatible set; merging the fault
family into one union; requiring a single fault to cover both histories;
accepting a witness without its opposite-truth obligation. For each mutation
save an input and expected/actual mismatch. Mutant results are not production
outputs, and expected values are not changed by majority vote.

## Resource policy and reporting

First run a deterministic 256-model prefix of each class as a pilot. Record
elapsed time and throughput, then choose and record the full-run wall budget.
Initial hard ceiling: 900 seconds per interpreter and 200,000 models per
invocation; each model uses the component's default 2,000,000-work budget per
operation. C has its own declared bounded-slice limits. A timeout/error yields
`incomplete` or `failed`, never PASS for the intended complete class.

Full execution is intended on Python 3.12.14. Repeat on 3.13.16 if measured
cost fits the ceiling. Publish hashes of source/protocol, deterministic model
stream and result stream, counts, command lines, runtime versions and actual
completion. Progress goes to stderr; summary JSON reports only completed
observations. No network is used during these validations.

The complete arbitrary-support 3x3 space (2,520,369,000 models for all truth
maps) is not run. Routine CI budget is decided from measured results; existing
CI is not silently replaced by an extended exhaustive job. Correctness outside
the declared classes, cross-language compatibility, admission-only semantics,
real evidence capture and external validation remain unestablished.
