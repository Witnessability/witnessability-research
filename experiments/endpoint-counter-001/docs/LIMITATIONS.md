# Limits and interpretation of results

Status: development protocol candidate, 25 October 2026. This file bounds the claims that
may be made about the proposed endpoint/counter experiment and its development
runs. It does not report a completed main run.

## What a successful finite run can show

A successful run can show that two implemented calculation paths agree on the
enumerated model, that particular observations admit explicit opposite-claim
histories, and that a specified added observation separates the declared
alternatives under stated premises. It can also expose remaining ambiguities,
adapter defects or mismatches between intended and implemented semantics.

These are useful, bounded results even when a proposed repair fails. A repair
that succeeds only after removing a failure possibility must identify that
stronger premise; it has not recovered information from the old record.

## Model and claim limits

- The history space is finite and selected by the experiment. Exhaustive
  enumeration within it is not proof that every relevant real history was
  modeled. Omitted channels can turn apparent decisiveness into false certainty.
- The claim concerns the specified completed-write event class and interval.
  Attempted invocation, final value, durable storage, safe behavior and absence
  of every other action are different claims.
- Equal endpoint projections do not imply equal complete AAR records or event
  commitments. Retained raw records may contain distinctions the adapter does
  not expose.
- A protected counter counts completed writes faithfully by assumption or by
  an explicitly bounded implementation argument. Signature validity does not
  establish that property. Reset, wrap, missing observations, misbinding, bypass
  and commit/count crash windows require their own histories and supports.
- An additional observation can resolve a particular pair without resolving
  every record in the model. Record-level verdict and prospective capability
  must be reported separately.
- OUTSIDE_MODEL is not factual FALSE. Invalid input is not UNRESOLVED. Incomplete
  computation is not a completed negative search. These distinctions must remain
  visible in reports and aggregate counts.

## Implementation and independence limits

The candidate implements explicit finite joint supports and failure families
with identity binding transformations. It does not implement general uncertain
coordinate bindings or adaptive observation planning. No Lean proof, verified Python runtime, or
end-to-end bytes-to-world refinement is implied by running its tests.

The two calculation paths share the declared model and this preparation's
authorship. They can catch implementation disagreements but can share a modeling
mistake. Running them in separate processes or by another person is not an
independently authored implementation.

The evaluator requires the declared possible histories and their claim-truth
assignment. Keeping the selected case's hidden history and expected verdict out
of its evidence input prevents case-answer leakage; it does not mean that the
evaluator operates without a model or without that model's truth assignment.

Simulated events and injected faults are not executed production effects. If a
local store or signed receipt is later implemented, that execution must be
identified separately. Multiple local processes, keys or signatures under one
controller do not establish separately controlled failure domains. An authentic
report may still be false when its legitimate writer is faulty.

Any development HMAC control uses a public test key and is not a public-key
signature or a demonstration of trustworthy observer identity. A valid MAC made
with that known key shows only that the tested verification algorithm accepts
the bytes under the key; it cannot establish that the reported event occurred.

A copied or borrowed runner establishes only its declared execution and artifact
properties. It does not inherit a proof of the claim under examination. A hash
binds bytes, not their truth or the legitimacy of the observation assumptions.

## Statistical and operational limits

Observation-class counts are finite model counts, not empirical reliability
rates or deployment probabilities. The configuration does not supply an event
distribution merely by enumerating histories. Runtime and artifact-size figures,
when measured, describe the stated environment and finite case family.

The initial sequential abstraction does not establish behavior under concurrent
writes, ambiguous ordering, crashes, recovery, adversarial scheduling or
long-running counter overflow. Controls can expose examples of these failures;
they do not automatically constitute a complete model of them.

Any minimum-cost or minimal-observation result is limited to the declared finite
catalog and its costs. A successful counter addition is not proof that counters
are the cheapest or best architecture. Additional observation can have privacy,
administrative and operational costs not represented in a first prototype.

## Publication and novelty limits

Development executions are not preregistered main runs or held-out tests. Their
results may inform the protocol; that exposure must be disclosed. A subsequent
freeze does not retroactively remove it.
Re-running finite cases whose outcomes were already inspected establishes
reproduction of those results, not success on an unseen prediction.

The write-and-restore ambiguity, limits of self-carried signed history, and use
of prior external commitments are not claimed as new. The closest reviewed
artifacts are recorded in [PRIOR-WORK.md](PRIOR-WORK.md). The candidate seeks a
reproducible comparison of claim-specific capture assumptions and faults, not
mathematical priority or a certification of completeness.

This experiment does not establish AAR/WEXP interoperability, protocol
conformance, standards-body adoption, security certification, author endorsement
or a collaboration agreement. Any later public text must bind its claims to an
identified run and retain unresolved limitations rather than borrowing success
from another corpus or manuscript.
