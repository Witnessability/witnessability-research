<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Algorithm, fixture and evidence provenance

## Existing algorithms and the standalone extraction

The public source baseline is
[`9ec68cff4981567705490b44ab5f76ffc0590cbb`](https://github.com/Witnessability/witnessability-research/commit/9ec68cff4981567705490b44ab5f76ffc0590cbb).
Its [`src/witnessability_research/finite.py`](https://github.com/Witnessability/witnessability-research/blob/9ec68cff4981567705490b44ab5f76ffc0590cbb/src/witnessability_research/finite.py)
has Git blob `e6a569b9087d0fcbd6b80050134b545448281cf8`.
The standalone component adapts this code within the same project:

| Standalone operation | Baseline source | Preserved criterion and changed boundary |
| --- | --- | --- |
| `evaluate-record` | `differences`, `compatible_criterion`, `_judgment`, `judge_criterion` | Exposure membership is disagreement confined to an allowed fault set. The candidate adds strict validation, context binding, resource accounting and a structured result. |
| `check-capability` | `structural_collision`, `structural_capability` | Opposite histories collide when an honest-record disagreement fits the union of one allowed fault set per history. Negative witness formatting is separate from search. |
| `verify-ambiguity` | `verify_certificate`, `pins` | Check the supplied witnesses' truth, support, faults and exposure membership. The candidate adds a strict envelope, version/policy context, duplicate rejection and resource charges; it does not search for a replacement witness. |

The original direct exposure enumeration and source-pinned replay remain in
the original package. This extraction is not an independently authored
implementation. [TRUST.md](../standalone/TRUST.md) lists the trusted code and
assumptions for each operation. Agreement of calculation paths can reveal
defects but can preserve a shared model or implementation mistake.

## Expected values, executed outputs and previous evidence

[Manual tiny controls](../standalone/fixtures/MANUAL-EXPECTATIONS.md) state
hand-derived expected compatible sets. They are expectations, not execution
reports or an independent oracle. Their history labels define possible worlds;
the selected run's hidden label must not be substituted for observation evidence.

The `standalone/fixtures/legacy-001/` fragments come from a preserved development
run. They are canonical serializations of selected values, not the original
parent artifact bytes. Their local `PROVENANCE.json` records parent hashes,
selection and source identity. Independently supplied fixture pins are test
trust anchors, not proof of the model-to-world relation. Semantic conversion
into `declared-model/1` does not reproduce the old receipt admission policy;
carrier rejections cannot silently become admitted factual results.

For any validation claim, retain the exact source/model/configuration identity,
selected finite class, command, interpreter/build environment, limits, exit
status, stdout/stderr and output hashes. Name what was measured and what was
derived. A limited sample, a fully enumerated sublanguage and an unexecuted
proposal have different scopes. Neither the historical 1125-case corpus nor a
later set is a general correctness proof merely because all cases agree.

Another run of the same code is reproduction. A separately written checker
must identify its derivation, code sharing and operation coverage; another
internal agent or process alone does not establish independent external review.
Broader checks require their own recorded evidence. The [bounded validation results](../validation/r02-06/RESULTS.md) identify
the actual measured classes and third-checker scope separately. The
disclosure preparation itself executes no new experiment.

## Prior work, scope and citation

[PRIOR-WORK.md](../experiments/endpoint-counter-001/docs/PRIOR-WORK.md) identifies
the inspected *Three Jobs, Not One* version and relevant agent-evidence-vectors
snapshots. Withdrawal/absence ambiguity, write-and-restore and detection through
prior external commitments are not claimed as discoveries here. The bounded
question is how an explicit event-to-observation relation changes a claim's
decidability when capture, binding and fault assumptions change. Historical
corpus results are their authors' reports unless separately reproduced.

This finite model does not by itself prove a general boundary theorem, implement
all WCC/WM, or establish WEXP/AAR interoperability. It does not borrow numerical
results or publication status from a manuscript. No cited author is listed as
a collaborator or endorser merely because their work is relevant.

[CITATION.cff](../CITATION.cff) identifies the confirmed project author and
repository. Cite the exact commit, component and any run used; no DOI, new
release date or paper citation is assigned. [CHANGELOG.md](../CHANGELOG.md)
separates the public baseline from unreleased changes. Any future export must
bind its claims to the actual exported bytes and include or accurately describe
the evidence it expects readers to inspect.
