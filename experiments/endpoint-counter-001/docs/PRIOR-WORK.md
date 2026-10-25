# Related work and the bounded difference this experiment tests

Status: public-safe candidate, 25 October 2026. This is a focused comparison for
the endpoint/counter experiment, not an exhaustive literature or priority
review. Repository snapshots below pin source material; reported corpus runs
remain their authors' reports unless separately reproduced.

## Withdrawal and prior commitments

Sankalp Gilda's *Three Jobs, Not One*, version 6, Section 6.1, describes a
withdrawal obstruction: a producer can omit a claim and its contrary supporting
material so that the carried statement is indistinguishable from honest
absence. It also describes fixing consumer-required evidence classes before
the run and refusing an incomplete response. This experiment does not claim
either observation as new.

- [Public record](https://zenodo.org/records/21935891)
- [Version 6 PDF](https://zenodo.org/records/21935891/files/three-jobs-not-one-v6.pdf)

The proposed experiment asks a narrower operational question: what connects a
completed event to the additional observation, and what remains distinguishable
after capture, binding and shared-control assumptions are weakened? Declaring
a required counter does not itself establish that every event reached it.

## Existing no-anchor/anchor contrasts

The Proof-of-Control corpus proposed in
[agent-evidence-vectors PR #259](https://github.com/probityai/agent-evidence-vectors/pull/259)
is a close executable-artifact antecedent. At inspected head
`3e120f59554406039c07457d3e53dcccfdd0835d`, its README describes 171 cases tied to
specification commit `93d0e282fc177d5df741de4cdd6a0d0dacf1955a`. This pin records
the inspected proposal; it does not assert that this head is a released or
currently merged corpus.

- [README](https://github.com/probityai/agent-evidence-vectors/blob/3e120f59554406039c07457d3e53dcccfdd0835d/vectors-poc-evidence/README.md)
- [Manifest](https://github.com/probityai/agent-evidence-vectors/blob/3e120f59554406039c07457d3e53dcccfdd0835d/vectors-poc-evidence/CORPUS-MANIFEST.json)
- [Reference comparison](https://github.com/probityai/agent-evidence-vectors/blob/3e120f59554406039c07457d3e53dcccfdd0835d/vectors-poc-evidence/REFERENCE-RESULTS.json)

Its chain fixtures already include:

| Case | Declared expectation | Distinction |
|---|---|---|
| `CHN-N-history-rewritten-no-anchor` | accept | A coherently rewritten and re-signed chain is not distinguished by its carried records alone. |
| `CHN-N-history-rewritten-resigned` | reject: `history-rewritten` | A prior anchor exposes the rewrite. |
| `CHN-N-tail-truncated-no-anchor` | accept | The carried prefix alone does not establish the missing tail. |
| `CHN-N-tail-truncated-with-anchor` | reject: `truncation` | An anchor beyond the supplied prefix supplies an external comparison. |

The exact fixtures are under
[`package/poc_evidence_vectors/corpus/chain/`](https://github.com/probityai/agent-evidence-vectors/tree/3e120f59554406039c07457d3e53dcccfdd0835d/vectors-poc-evidence/package/poc_evidence_vectors/corpus/chain).
The fixture's `accept` is a result of that corpus's verification contract; it is
not a finding that the original world history occurred or that no record was
withheld.

Consequently, merely adding an anchor to detect rewrite or truncation is not
the intended contribution here. The new candidate keeps carrier integrity and
the world-event/capture relation separate, then tests how faults in that relation
affect a specific factual question. It has not established a strict extension
of the Proof-of-Control standard or a new security guarantee.

## Source coverage and contradictory clean reports

[PR #256](https://github.com/probityai/agent-evidence-vectors/pull/256), inspected
head `61ca173092a1a74a28b3944ca3a77b718f4a311e`, adds a scanner pair derived from
an external contribution. One record says that repositories were not opened
and nevertheless finishes with a clean claim; its twin reads the complete
declared set. The
[source-coverage README](https://github.com/probityai/agent-evidence-vectors/blob/61ca173092a1a74a28b3944ca3a77b718f4a311e/vectors-source-coverage/README.md)
explicitly limits what passing the synthetic cases establishes.

This is a relevant precedent for keeping explicit gaps, consumer requirements
and final claims consistent. Our missing-counter control must not silently
reinterpret absent evidence as a zero count. Neither test family proves
completeness of arbitrary real-world capture.

## Exact bytes, final-line handling and reasons

[PR #258](https://github.com/probityai/agent-evidence-vectors/pull/258), inspected
head `3c106867ab65528ca7d66686f0ccf9b585c3df5d`, adds a real 73-line stream and
a paired final-newline mutation. The
[anchor-stream README](https://github.com/probityai/agent-evidence-vectors/blob/3c106867ab65528ca7d66686f0ccf9b585c3df5d/vectors-anchor-stream/README.md)
also distinguishes the expected stop reason from an accidentally matching
verdict, pins platform observations, and avoids answer-bearing identifiers.

These are useful evaluation practices, not discoveries claimed by this
experiment. A decoder must see the declared observation rather than an expected
answer encoded in a filename. A parser rejection is not successful evaluation
of the later semantic property.

## Evaluation result origin and missingness

[PR #255](https://github.com/probityai/agent-evidence-vectors/pull/255), inspected
head `d00949bce9bd05507d06ee7e85dde4a4774aced8`, supplies cases for declared score
direction, evidence origin per item, separate producer/verifier fields, and
held-out true/false/unknown states. Its
[README](https://github.com/probityai/agent-evidence-vectors/blob/d00949bce9bd05507d06ee7e85dde4a4774aced8/packaging/agent_evidence_vectors/eval_result/README.md)
states that these are working fixture names and that the corpus does not
establish the truth of producer records.

The same distinction applies here: another party checking a receipt does not
change who observed or produced its content. Missingness is not falsity, and
two calculations sharing authorship and modeling choices are not independent
external validation.

## Relationship to Witnessability

The public
[Witnessability Conceptual Core 1.0](https://github.com/Witnessability/witnessability-core/blob/v1.0.0/release/1.0/assets/WITNESSABILITY-CORE-1.0.md)
and
[Witnessability Model 1.1 publication](https://github.com/Witnessability/witnessability-model/blob/e316d1200053ec9da6a3c30d3f7f2cf952b24e54/README.md)
provide the surrounding vocabulary of evidence boundaries and support for
claims. The present candidate is a finite experimental specialization. It does
not revise those publications, implement every part of them, or establish
conformance to a protocol.

No historical numerical result is inherited into the new experiment. Any
execution, mathematical proof, novelty assessment or independent reproduction
claimed for this candidate requires its own identified evidence.
