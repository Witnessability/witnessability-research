<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Result vocabulary and contract boundaries

This is a reading guide, not an adapter, conformance claim or normative change
to any cited document. Similar words can answer different questions. A comparison
must match the exact proposition, scope, observation relation, binding, admitted
premises and processing outcome before defining a partial mapping.

## This finite checker

The [contract](../standalone/CONTRACT.md) names schema
`wresearch-checker-input-1`, semantics `finite-joint-identity-1` and admission
policy `declared-model/1`. Only raw scope and identity binding are implemented.

| Term | Meaning here |
| --- | --- |
| `TRUE` / `FALSE` | The compatible-history set is nonempty and all its histories respectively satisfy / falsify the declared claim. |
| `UNRESOLVED` | Compatible histories with both claim truth values exist. |
| `OUTSIDE_MODEL` | No declared history can expose the record. This identifies neither factual falsity nor which real premise failed. |
| Raw capability | Every opposite-truth pair has disjoint exposure in the declared model. It is a global property, unlike one record's verdict. |
| Valid ambiguity certificate | Two supplied opposite-truth histories expose the same record under allowed faults and the expected context. It establishes ambiguity for that record, not completeness of real-world capture. |
| Admission | A caller acknowledges applicability under `declared-model/1`. This checks neither signatures nor a producer's trustworthiness. |
| Processing failure | Invalid input, unsupported contract, pin mismatch, admission rejection, invalid certificate or incomplete computation. These are not claim verdicts. |

A record can be `TRUE` while raw capability is false. A model with raw
capability true can still receive an `OUTSIDE_MODEL` record. A failed supplied
certificate does not exclude another valid witness. Trusted expected pins
bind the intended inputs; they do not establish their truth or applicability.

## Neighbouring contracts: partial comparison only

| Versioned source | Vocabulary or object | What must not be inferred |
| --- | --- | --- |
| [WCC 1.0](https://github.com/Witnessability/witnessability-core/blob/v1.0.0/release/1.0/assets/WITNESSABILITY-CORE-1.0.md), W-I8 and §§2.7, 2.11–2.12, 7.2–7.4 | Minimum support outcomes include **supported**, **not supported**, **indeterminate**. A Support Assessment is profile-bound and includes its envelope, qualifications and other status dimensions; it is separate from a relying-party decision. | `not supported` does not mean false. A finite `TRUE` does not automatically create a WCC Support Assessment or Support Envelope. These WCC outcomes are not this checker's four-value executable contract. |
| [WEXP Core-02](https://datatracker.ietf.org/doc/draft-sergeev-wexp-core/02/), §§8.1–8.6 | `accept`, `downgrade`, `reject`, with supported claims, reasons and evaluation gaps reported separately. Acceptance requires the exact asserted claim to be supported and applicable counter-evidence not to block it. | No mechanical `accept→TRUE`, `downgrade→UNRESOLVED`, or `reject→FALSE/OUTSIDE_MODEL`. `asserted_claim_supported=true` can coexist with `downgrade` because of counter-evidence. |
| [WEXP Coverage-00](https://datatracker.ietf.org/doc/draft-sergeev-wexp-coverage/00/), §§7.3, 8, 13 | Evaluated claim outcomes are `supported`, `refuted`, `not-established`. Support alone and refutation alone yield the first two; both or neither yield `not-established`, with different diagnostics. A requested claim not evaluated has no outcome and carries a reason. | `not-established` is not automatically an opposite-history ambiguity witness. Not-evaluated, rejected input and exhausted resources are not refutation. The capture premise and exact derivation basis must be retained. |
| [Agent Audit Record corpus snapshot](https://github.com/probityai/agent-evidence-vectors/blob/0e761e646d08bdc6731dd53e975167fce46a74e6/vectors-agent-audit-record/README.md), AAR-00 plus five -01 rows | The pinned corpus scores `expected.verdict` under its record contract; examples include `valid`, `malformed`, `indeterminate`. Its N2 row permits `valid` or `indeterminate` via `readings`. This is not an exhaustive result-code list. | `valid` does not imply this experiment's no-write claim is `TRUE`. Equal endpoint projections do not imply equal full AAR records. A glossary does not add AAR fields, a counter carrier or an executable adapter. |
| [Proof-of-Control corpus snapshot](https://github.com/probityai/agent-evidence-vectors/blob/3e120f59554406039c07457d3e53dcccfdd0835d/vectors-poc-evidence/README.md) | Its chain controls distinguish acceptance of carried history without a prior anchor from rejection after comparison with an anchor. | Corpus `accept` is not confirmation that the original world history occurred or that nothing was withheld. This project's counter model is not a claimed extension of that standard. |

“Probity verdict” is too broad to identify a contract: name the corpus,
specification revision and snapshot. The snapshots above are citation pins,
not an assertion that these are the newest releases. They establish neither
shared governance nor agreement by their authors with this project's mappings.

An `OUTSIDE_MODEL` result must not be renamed a WCC undermining condition or
WEXP rejection without a justified contract-specific rule. A full comparison
would require explicit input transformation, preserved assumptions, expected
outcome derivation and treatment of failures. None is supplied by this glossary.
