# Standalone finite checker: private candidate contract

This contract belongs to the first private implementation candidate based on
`Witnessability/witnessability-research` commit
`9ec68cff4981567705490b44ab5f76ffc0590cbb`. It defines a bounded, explicit finite
language with identity binding. It is not a ratified WCC/WM contract, a WEXP
profile, or a public release. Distribution and import names are provisional
installation identifiers; the existing `witnessability-research` package is not
renamed. The terminology handoff was a recommendation, not naming authority.

## Versions and files

| Identity | Candidate value | Meaning |
|---|---|---|
| `schema_version` | `wresearch-checker-input-1` | Envelope, fields, types and encoding contract below |
| `semantics_version` | `finite-joint-identity-1` | Explicit joint supports, whole-coordinate faults, binary claims, identity binding |
| Admission policy | `declared-model`, version `1` | Explicit acknowledgement of applicability assumptions; no carrier validation |
| Implementation | `0.2.0.dev1` | This implementation revision; not a semantic hash ingredient |

A model document contains exactly `schema_version`, `semantics_version` and
`model`. A record file is a JSON array. A policy file contains exactly:

```json
{"id":"declared-model","version":"1","acknowledged_assumptions":true}
```

All three commands require a separate expected-pins file. A certificate is a
separate input only to `verify-ambiguity`. Version strings are exact,
case-sensitive values. A correctly typed unknown schema, semantics, policy,
policy version, scope or binding is unsupported; malformed version fields are
invalid input. There is no implicit migration.

## Finite model and raw form

The `model` object has exactly these required fields, including `binding`:

| Field | Raw JSON type and constraints |
|---|---|
| `name`, `claim` | Nonempty strings |
| `binding` | String `identity` |
| `histories` | Array of 1–400 distinct nonempty history-ID strings |
| `truth` | Object with exactly the history IDs as keys; every value is a JSON Boolean |
| `domains` | Array of 1–6 distinct nonempty coordinate/domain strings |
| `alphabets` | One array per domain, each containing 1–64 distinct string atoms; empty-string atoms are permitted |
| `joint` | Object with exactly the history IDs; each value is an array of 1–4096 distinct records |
| `faults` | Array of 1–64 distinct arrays of distinct domain names, containing the empty array and closed downward |

Every support record is an array with exactly one string atom per domain and
each atom belongs to that domain's alphabet. A fault set is a subset of the
declared domains. Downward closure means every subset of each allowed fault is
also explicitly present. Repeated fault members are invalid even when conversion
to a set would remove them. Equivalent repeated fault sets with different member
orders are also invalid. Repeated history IDs, domains, alphabet atoms, support
records and JSON object keys are rejected before normalization.

An evaluation record has the same length and string types as a support record.
It may contain an atom outside its alphabet: this is well-formed record syntax
with no compatible history, hence `OUTSIDE_MODEL` after admission and completed
analysis. An out-of-alphabet atom in a model's support is invalid input.
History IDs are labels; the checker does not execute their names as traces.

## Finite semantics and operations

For history `h`, its exposure is the union, over honest joint-support records
`a` and allowed faults `F`, of records that equal `a` outside `F` and use the
declared alphabets inside `F`. Binding is the identity. For record `r`, the
compatible set contains exactly histories whose exposures contain `r`.

| Operation | Completed result | Required reasoning |
|---|---|---|
| `evaluate-record` | `TRUE` | Compatible set nonempty and every compatible history has truth `true` |
| `evaluate-record` | `FALSE` | Compatible set nonempty and every compatible history has truth `false` |
| `evaluate-record` | `UNRESOLVED` | Compatible histories contain both truth values |
| `evaluate-record` | `OUTSIDE_MODEL` | Compatible set empty; no factual falsity or failed premise is thereby identified |
| `verify-ambiguity` | Valid supplied ambiguity witness | The two supplied histories have opposite truth and both expose the supplied record |
| `check-capability` | Raw capability `true` | Every pair of opposite-truth histories has disjoint exposure |
| `check-capability` | Raw capability `false`, with collision | A pair of opposite-truth histories has a common record |

`evaluate-record` extracts the baseline's exact disagreement-membership
criterion and visits the declared alternatives needed to decide each history.
`check-capability` extracts its structural collision criterion: an opposite
pair's honest-record disagreement must fit the union of one allowed fault per
history. Finding one collision completes a negative capability decision;
capability `true` requires exhaustion of the exact comparison domain. These
are adapted existing algorithms, not independently authored implementations.

Only `--scope raw` is implemented. Any other scope, including `admitted-only`,
receives `unsupported`; no raw result is relabelled. Raw capability quantifies
over all model exposures, including observations an unrelated carrier policy
could reject. Capability does not assert that every syntactically valid record
has any compatible history. A record can be `TRUE` while raw capability is false.

The supported admission policy admits a record request only when the Boolean
acknowledgement is `true`. It means the caller accepts conditional analysis of
this declared model. It verifies no signature, HMAC, capture, physical effect,
administrative independence, historical fact or model completeness. A false
acknowledgement is `admission_rejected`, distinct from an unknown policy.
Raw capability remains an analysis of the raw model; policy identity is still
bound and reported, not used to remove records from the quantified domain.

## Ambiguity certificate

A certificate contains exactly these fields:

```json
{
  "schema_version": "wresearch-checker-input-1",
  "semantics_version": "finite-joint-identity-1",
  "pins": {"model":"<sha256>","claim":"<sha256>","record":"<sha256>","policy":"<sha256>","context":"<sha256>"},
  "record": ["<one atom per domain>"],
  "witnesses": [
    {"history":"<false-history>","honest":["<atoms>"],"fault":[]},
    {"history":"<true-history>","honest":["<atoms>"],"fault":[]}
  ]
}
```

There must be exactly two witnesses, ordered false then true. Every witness
contains exactly `history`, `honest` and `fault`. Its honest record must belong
to that history's joint support, its fault to the allowed family, and the common
record to that witness's exposure. Any pair satisfying these rules is accepted;
the old generator's first-found choice is not required. A malformed certificate
has an input-processing error; a well-formed witness violating these semantic
conditions is `invalid_certificate`. Neither outcome establishes determinacy.

A valid certificate establishes `UNRESOLVED` for this record and refutes raw
capability within the declared model. It does not certify a `TRUE`, `FALSE`,
`OUTSIDE_MODEL` or capability-true result. Those results require their completed
exact analyses. This restriction says nothing about other possible proof systems.
The verifier checks the supplied certificate without searching for a replacement.

## Canonical encoding and pins

The canonical function is the unchanged local Python encoder:

```python
json.dumps(value, sort_keys=True, separators=(",", ":"),
           ensure_ascii=True, allow_nan=False)
```

`H(x)` is SHA-256 of the UTF-8 bytes of that string, with no trailing newline,
written as 64 lowercase hexadecimal digits. This is **not RFC 8785 JCS**.
No Unicode normalization occurs. Composed and decomposed strings remain distinct.
Dictionary keys are sorted by Python's string ordering; arrays retain order.
Fault members are sorted in `model.to_dict()`, matching the old implementation;
the order of the fault-family array is retained. Equivalent reorderings can
therefore change some pins. Cross-language compatibility has not been established.

| Pin | Exact hashed value |
|---|---|
| `model` | Legacy-normalized `model.to_dict()`; same semantic data and encoding as baseline |
| `claim` | `{"claim": model.claim, "truth": model.truth}` |
| `record` | JSON array of the record atoms |
| `policy` | Entire validated policy object, including ID, version and acknowledgement |
| `context` | `{"schema_version": S, "semantics_version": V, "model": model_pin, "claim": claim_pin, "policy": policy_pin}` |

Record operations require exactly `model`, `claim`, `record`, `policy` and
`context` in the external expected file. Capability requires exactly `model`,
`claim`, `policy` and `context`; its request contains no record. The context pin
binds schema, semantics and admission policy while preserving the old model,
claim and record pins. Implementation version and marketing names are excluded.

Expected pins must be trusted by the caller independently of the submitted
certificate and candidate inputs. The CLI recomputes actual pins, compares them
to that external expectation, and then checks a certificate against the same
context. Replacing all input objects and their embedded pins consistently does
not pass under the old expected context. Computing new expected pins from an
untrusted replacement establishes only self-consistency. Hashes do not prove
the truth, provenance or applicability of their preimages.

The negative capability output contains a certificate and its record pin for
the returned collision. A later caller verifies the relation of that record to
the trusted model/context and supplies its own expected record context to
`verify-ambiguity`; it must not treat returned pins alone as independent trust.

## JSON boundary and resources

Input files contain one complete strict UTF-8 JSON value. A UTF-8 BOM, invalid
UTF-8, lone surrogate code points, duplicated keys at any depth, NaN, Infinity,
floating-point syntax, invalid syntax and trailing non-whitespace are invalid.
Whitespace following the value is permitted. Strings retain their code points;
JSON escape spelling does not alter their value. Integers, where structurally
allowed, must be signed 64-bit values. JSON Booleans do not count as integers.
The model's truth map requires actual Booleans, never `0` or `1`.

Each JSON file is limited to 2 MiB, 32 container nesting levels, 200,000 parsed
value/container nodes and 4,096 code points per string. Object keys are validated
and charged separately from the node count. Model structural upper bounds are
listed above. Exceeding a declared resource bound reports `compute_limit`;
malformed structure reports `invalid_input`. Fixed-shape mismatches, including
wrong record length, wrong witness count or more fault entries in a witness
than model dimensions, are malformed input. These bounds apply before expensive
model normalization. Certificate parsing and witness validation also consume budget.

`--max-work` is an integer from 1 through 2,000,000, default 2,000,000. One
shared deterministic work counter covers file decoding/preflight, parsed nodes
and strings, model validation, hashing and the selected operation. Work units
are implementation accounting units, not time or cryptographic cost estimates.
The counter is not an OS sandbox, wall-clock deadline or exact peak-memory cap.
Fixed input bounds additionally limit pre-budget parser allocation. A stopped
or failed computation produces no mathematical result.

## CLI and processing outcomes

```text
witnessability-checker evaluate-record --model MODEL.json --record RECORD.json --policy POLICY.json --expected EXPECTED.json [--scope raw] [--max-work N]
witnessability-checker verify-ambiguity --model MODEL.json --record RECORD.json --certificate CERTIFICATE.json --policy POLICY.json --expected EXPECTED.json [--scope raw] [--max-work N]
witnessability-checker check-capability --model MODEL.json --policy POLICY.json --expected EXPECTED.json [--scope raw] [--max-work N]
```

The same interface is available as `python -m witnessability_checker`. Normal
requests emit one JSON report on stdout. Errors emit a report plus a concise
diagnostic on stderr. A nonzero processing outcome never uses a mathematical
verdict as its error code. CLI help is the ordinary usage display.

| Exit | Processing status | Meaning |
|---|---|---|
| 0 | ok | Requested analysis or supplied-certificate verification completed |
| 2 | invalid_input | Malformed input or CLI usage |
| 3 | unsupported | Well-formed but unsupported mandatory version, policy, scope or binding |
| 4 | pin_mismatch | Input/certificate does not match external expected context |
| 5 | admission_rejected | Supported policy declines record request |
| 6 | invalid_certificate | Supplied well-formed witness fails its semantic obligations |
| 7 | compute_limit | Declared structural/work resource limit prevents completion |
| 8 | compute_error | Unexpected computation failure; no semantic answer |

The report has the following required fields. An error additionally has `error`,
a diagnostic string. Object-key order is serialization detail; stdout uses
sorted JSON keys and a final newline.

| Report field | Value |
|---|---|
| `operation`, `scope` | Parsed request values, or null if argument parsing did not finish |
| `versions` | Object with `schema_version`, `semantics_version`, `admission_policy_version`, `implementation_version`; schema/semantics identify the supported contract, policy version is null until validated |
| `pins`, `expected_pins` | Recomputed and externally supplied pin objects after validation, or null before that stage |
| `method` | `complete-compatible-disagreement-criterion`, `supplied-witness-exposure-membership`, or `exact-opposite-truth-disagreement-union-criterion`; null until operation selected |
| `admission` | Initially `{"status":"not_checked"}`; after pin checks includes `id`, `version` and status `accepted`, `rejected` or `not_applicable_raw_scope` |
| `completion` | `completed` on status `ok`, otherwise `not_completed` |
| `limits` | `max_work`, `max_json_bytes_per_file`, `max_json_depth`, `max_json_nodes_per_value`, `max_string_codepoints` |
| `work` | Actual deterministic units charged, including a charge that exceeded the limit |
| `status` | Processing status from the exit table |
| `result` | Operation-specific object on success, null on every processing error |

The evaluation result is exactly `{"verdict": V, "compatible_histories": [...]}`.
Verification succeeds with `{"valid": true, "record_verdict": "UNRESOLVED",
"raw_capability": false}`. Capability returns `capability`, `collision` and
`certificate`: the latter two are null for capability true. A negative collision
contains `histories` (false then true), `record`, `honest_records` and `faults`;
its certificate has the schema above. No partial mathematical result survives
a subsequent budget/error failure in reporting/construction.

Errors retain only information already established. An error report's supported
schema/semantics fields do not imply that an unknown requested version was
accepted. Pin matching precedes record admission; a mismatch therefore prevents
an admission result. `FALSE` and capability `false` are successful completed
decisions, not nonzero exits. An invalid certificate never produces a substitute
record verdict.

## Legacy mapping

Legacy finite-model data is validated before wrapping in the new model envelope.
Its `model`, `claim` and `record` pins retain their original meanings. The new
schema/semantics/policy context is an explicit added binding, not a reinterpretation
of the old pin as a new version-aware digest. A legacy `finite-ambiguity-v1`
certificate must be explicitly converted: verify caller-supplied legacy pins,
retain record and witness data, and add the new envelope and policy/context pins.
Changing only the `schema` label is not conversion. The importer never generates
another witness or invokes the experiment/store modules.

The conversion APIs are:

```python
import_model(raw_model, *, expected_legacy_pins, budget)
import_certificate(document, record, legacy_certificate, policy,
                   *, expected_legacy_pins, budget)
```

The former requires external legacy pins exactly `model` and `claim`; the latter
also requires `record`. Conversion validates the old envelope and embedded pins
against these independent expected values, then verifies the retained witness
under the new version/policy context. Its new context pins are conversion outputs
that need caller review/trust; they do not inherit independent authority merely
because the old certificate carried hashes. No import command is silently run
by the three main operations.

The standalone policy does not reproduce 001's receipt/HMAC admission. A raw
legacy observation may be studied under `declared-model` even if the old consumer
rejected its carrier; that is a different admission contract and must be reported
as such. Source-pinned replay remains a separate operation using the unchanged
baseline CLI and the original manifests. New standalone files are outside the
old source-pinned package directory. Old source hashes are never weakened or
rewritten to fit changed code.
