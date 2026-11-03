# RB receiver: positive witness with incomplete observation

Candidate addition for `Witnessability/witnessability-research`, path
`interop/restoration-rb-receiver-001/`. Not published or approved.

Run from this directory with Python 3.11+ and no external dependencies:

```sh
python3 -E -s -B run.py
python3 -E -s -B -O run.py
```

The script checks pinned source hashes, the 57-case corpus manifest and its
75 carried JSON files, then writes seven receiver readings and two finite
ambiguity controls under `results/`. Re-running replaces these local generated
outputs. It does not access the network or execute the capture harness.

The minimal case is `results/02-partial-positive/`: an original RB Statement
declares `not_established` with integer counts (2 initial attempts and 2
post-revocation commits); a partial local observation carries one initial
attempt, starting at 0, revocation at 1, commit at 2, finish at 3. Its exact
boundary is successful fsync return for first.txt, not directory durability.
The receiver retains the producer result and derives a positive observation
without deriving an exact count vector. Declared count 2 is not independently
established by this observation.

The finite oracle has no VATE imports. It compares histories [visible event]
and [visible event, hidden event], with identical visible projection. Both
have a positive event, but total counts are 1 and 2. These two histories refute
uniqueness of the count under the admitted observation model; positivity for
arbitrary extensions additionally follows because adding events cannot erase
the already admitted witness. This is a conditional argument, not a claim that
the finite model enumerates every real history. Producer count declarations
are not admitted as factual premises of this oracle.

| Reading | Expected boundary |
| --- | --- |
| 01 no observation | No local observation assessment |
| 02 partial positive | Original unknown result; positive witness; null derived counts |
| 03 partial empty | No positive witness found; no inference of zero |
| 04 unknown result + zero count | Record passes; local witness contradicts numeric zero |
| 05 commit equals revocation time | No definite post-revocation witness |
| 06 receiver selects another sink | Observation agrees with Statement but receiver binding fails |
| 07 wrong Statement digest | Observation binding fails; no positive finding admitted |

This does not duplicate the 57 record/bundle vectors: those carry no receiver
observation input or expected receiver-observation result. The corpus member
provides a valid carrier template, not the new expected semantics. Sato already
tests partial positives and zero contradictions; this package claims an
independent cross-boundary control and explicit compatible-history witness,
not discovery of that behavior or a defect in his reader.

## Source identities and independence

- VATE: `eaa47be4bd1f640f390ecd8b31111277c0e0e9e0`; eight unchanged files,
  with Git blob identities in `VENDOR-PINS.json`.
- Witnessability research baseline: `cc97bb27be610b8b0fe03a3ea58e40d6c09d7d31`.
- Agent-evidence-vectors: `1177028f6276f439768ab7d02fb734054832612c`, v0.31.2.
- Restoration Evidence -00 archived text SHA-256:
  `0ae1b94c226cf85b006dfb34abf2180e9dcbda34ad30b9933067df37eafec745`.
  The IETF endpoint was unavailable during this review. The text was recovered
  from the retained review archive; its hash matches both recorded source pins.

`run.py` calls the unchanged VATE reader as the implementation under test.
`finite_oracle.py` computes a different, finite observation-model predicate.
These are not two independent implementations of Restoration Evidence. The
oracle and adapter were prepared together; no independent author review is
claimed. The 57 members were inventoried and their hashes checked, not rerun
through a new full Restoration Evidence verifier in this package.

Validation: Python 3.12.14; seven readings pass in normal and optimized mode;
46 upstream receiver tests pass. The live fsync/OpenSSL capture, Inbox path,
DSSE signatures, issuer authority, clock authenticity, observation completeness,
evidence sufficiency and restart policy were not evaluated. Passing tests do
not establish safety or correctness of a restoration decision.
