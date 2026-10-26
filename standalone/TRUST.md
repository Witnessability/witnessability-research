# Trusted dependencies and evidence boundaries

This component reduces the dependency set of each operation. It does not make
the declared model, external pins or observed world trustworthy automatically.
It derives from `finite.py` at public base
`9ec68cff4981567705490b44ab5f76ffc0590cbb`; extraction and changed accounting are
recorded in the candidate's algorithm-origin record. Shared origin and helpers
remain shared: this is not an independently authored implementation.

## Operation-specific import boundary

| Operation | Project code required at runtime | Additional dependency |
|---|---|---|
| `verify-ambiguity` | Entry point/CLI, `common`, `validation`, `model`, `context`, `verify` | Exact witness membership checks only |
| `evaluate-record` | Entry point/CLI, `common`, `validation`, `model`, `context`, `analysis` | Full record-compatible-history criterion |
| `check-capability` | Entry point/CLI, `common`, `validation`, `model`, `context`, `analysis`, `capability_command` | Exact opposite-pair structural collision criterion and formatting its negative witness |
| Explicit legacy conversion | `legacy` plus shared parsing/model/context/pin helpers and supplied-certificate verification | Caller-trusted legacy pins; no generation |

`common` provides errors, work accounting and canonical hashing; `validation`
provides bounded JSON/type/shape checks; `model` provides validated representation,
normalization and model fields; `context` provides versions, policy and external
pin bindings. These helpers contain no finite-model search, experimental trace
construction or store simulation. `verify` must not import `analysis`, the old
`finite.py`, `experiment`, `store`, optimizers or research adapters. Importing a
module that contains search routines would violate this boundary even if that
search were not called. `capability_command` constructs a certificate from the
already found collision and belongs only to the capability path. The CLI loads
operation-specific modules lazily. The capability CLI does not independently
verify its own output; the separate verifier and tests check negative witnesses.

The minimal wheel includes the standalone component, including the analysis
module needed for the other two commands. Merely being installed is distinct
from being imported by certificate verification. It excludes the original
`witnessability_research` package, its old CLI, experiment and store modules.
The provisional distribution name is an installation choice, not a rename or
PyPI registration. The old package remains available separately for exact replay.

## Common trusted computing base

Every result depends on the running Python implementation and its standard
library, in particular JSON decoding/encoding, string/collection semantics,
hashlib/SHA-256, file I/O, exception handling and module loading. The CLI also
uses argument parsing and process output. Installation trusts the selected
wheel bytes, packaging metadata, installer and build tools used to create it.
No third-party runtime dependency is needed by the standalone operations.
The OS, filesystem and process environment must provide the files and code the
caller intended. An import-closure test is evidence about that tested execution,
not a general proof against a compromised interpreter or loader.

Validation and serialization are trusted code, not free preconditions.
Deterministic work accounting includes validation and certificate checks. It
does not establish a hard wall-clock deadline or protect against every host-level
resource failure. An unexpected error or incomplete budgeted computation is a
processing failure, never a mathematical answer.

## Assumptions outside the checker

| External assumption | What the checker can and cannot establish |
|---|---|
| Intended model and claim | Checks their representation and pins; does not prove the model describes the real system or that the truth map is factually correct |
| Complete declared alternatives | Analyses every relevant declared alternative; does not prove omitted real histories impossible |
| Honest supports and faults | Enforces the declared finite relation and downward-closed family; does not establish actual fault independence or capture reliability |
| Identity/binding interpretation | Supports identity binding only; does not infer real object/run/epoch/fence correspondence from labels |
| Trusted expected context | Detects substitution relative to supplied external pins; cannot make pins trustworthy if attacker-controlled alongside inputs |
| Code integrity | Logs/wheel hashes identify reviewed bytes; execution additionally trusts that those bytes are what the runtime loaded |
| Admission | Checks explicit acknowledgement under `declared-model/1`; does not authenticate a producer or validate a real receipt |
| Applicability | A caller must justify the event class, interval ordering, capture assumptions and observation projection for a concrete use |

A valid ambiguity certificate is a local mathematical counterexample under
those premises. `TRUE` is a completed conditional finite-model result. Neither
creates a WCC Support Assessment/Support Envelope, entails WEXP `accept`, proves
real capture completeness, or evaluates the whole Witnessability programme.

## Verification evidence and remaining assurance

The private candidate retains real command logs, environment versions, input and
output digests, wheel inventory, installed execution/import checks, regression
results and internal review. Consult those records for what actually ran and
for unavailable Python versions. Test expectations are preserved separately
from output. Repeating the same code in a clean environment demonstrates a
bounded reproduction property; internal review is not external scientific
validation. The 1125-case inherited consistency corpus is finite and limited,
not a general correctness proof or automatically an oracle.

Independent external reproduction, separately authored implementations and
expanded finite classes need their own identified evidence. They are distinct
from one another and from repeated runs of this extraction. Any additional
checker must state its derivation, shared code and operation coverage; its name
or execution in a different process is not evidence of independence.
Model-to-world validation, symbolic backends, observation optimization,
Coverage-002 and external comparison remain separate claims.

The [provenance guide](../docs/PROVENANCE.md) distinguishes expected controls
from executed outputs; the [glossary](../docs/GLOSSARY.md) separates neighbouring
contracts. Use the [challenge procedure](../CONTRIBUTING.md) to preserve disputed
expectations and their eventual disposition.
