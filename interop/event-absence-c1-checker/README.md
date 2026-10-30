<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Checker side of the three C1 event-absence cases

This package runs the standalone finite Research Checker on the three synthetic inputs published by Sankalp Gilda in [event-absence-c1-sergeev](https://github.com/probityai/agent-evidence-vectors/tree/1044438a97b199bc3c3d887965138b19378f4140/interop/event-absence-c1-sergeev). Mikhail Sergeev authored the inputs and their interpretation. This is a bounded comparison, not an independent implementation of Probity or a general equivalence result.

## Reproduce

Use Python 3.12 or newer (the recorded run used CPython 3.12.14), Git and this package. No Python packages or private repositories are required.

From the root of a checkout containing this package, run:

```sh
python interop/event-absence-c1-checker/run.py --out runs/event-absence-c1
```

The runner checks the current source files against the pinned Checker modules
at `4a37199f2a59b7ecd97055cfc1af5cb787a76265`; unrelated repository additions do
not change that source pin. CI runs this command on Python 3.12 and 3.13.

Alternatively, with the package copied separately, acquire the pinned engine:

```sh
git clone https://github.com/Witnessability/witnessability-research.git checker
git -C checker checkout --detach 4a37199f2a59b7ecd97055cfc1af5cb787a76265
python run.py --checker-root checker --out results-new
```

Run these commands from this package directory. The output directory must not exist. The runner checks all 11 source modules and all 12 input/metadata files by length and SHA-256, checks the exact case set, invokes the actual CLI in isolated Python subprocesses, retains full output and exit codes, and compares each complete JSON object with `EXPECTED.json`. It never converts an execution error into a claim verdict. The source files are unchanged public code at the pinned commit. Checkout identity alone is not the source gate; the module hashes are checked before and after execution.

| Case | Checker result | Compatible histories | Published Probity PEER decision / reason |
| --- | --- | --- | --- |
| covered-empty | TRUE | N | supported / absence_within_covered_scope |
| event-with-gap | FALSE | W10 | contradicted / event_observed |
| empty-with-gap | UNRESOLVED | N, W30 | not_established / observation_coverage_unestablished |

[Recorded outputs](results/RESULTS.json) come from a new 30 October run in an isolated checkout. All three complete stdout files matched both the prior expectations and a first new run byte for byte. The expected objects were already known; this is reproduction, not a blinded or preregistered experiment. This runner executes only the Research Checker. The Probity column comes from the [partner's pinned EXPECTED.json](https://github.com/probityai/agent-evidence-vectors/blob/1044438a97b199bc3c3d887965138b19378f4140/interop/event-absence-c1-sergeev/EXPECTED.json), not a new Probity invocation here.

## Scope

The claim is absence of a completed write in the chosen invocation and interval. Capture, attribution, event truth, visibility and completeness are declared premises. Synthetic `independent` labels do not authenticate identity or custody. The chosen finite histories are not claimed exhaustive of the real world.

The correspondence is limited to these three inputs under Probity's PEER requirement. Under EXTERNAL, the partner's first case changes to `not_established / witness_scope_below_required`. That authority-policy gate is not modeled by this Checker input and must not be translated into UNRESOLVED. The third case is unresolved because both N and W30 remain compatible, not merely because another system returns `not_established`.

No WEXP conformance, general semantic equivalence, production guarantee, review of D3, coauthorship or endorsement is established. The implementation is the existing `0.2.0.dev1` development candidate, not a new release.

Reuse and attribution follow [LICENSE-NOTICE.md](LICENSE-NOTICE.md).
