# Restoration Evidence -00: current status

Checkpoint: 2026-11-03. This status supersedes preparation-state descriptions;
REVIEW-STATUS.md remains an explicitly historical snapshot.

## Completed

The review was published at cc97bb27be610b8b0fe03a3ea58e40d6c09d7d31.
The technical message was sent to the draft author on 2026-11-03.
MESSAGE-TO-SANKALP.md now carries the approved wording, without quoted
correspondence or private mail identifiers. The prior wording remains in Git history.
Sending is not evidence of receipt, agreement or adoption.

The corrected default matches all 57 pinned verdicts and reasons. The 30
original controls and 22 proposed boundary examples pass. Original checker,
inputs and archived results remain unchanged. The original diagnostic mode
is retained for comparison and does not conform to Section 10 on one reason.
That implementation defect is separate from the proposed clarification.

## Source freshness

At upstream main ac4c9430d23822544de5875885dc9e239a477668, all ten retained
source files (six profile/predicate texts, three schemas and the manifest)
are byte-identical to this package's upstream snapshots.

PR https://github.com/probityai/agent-evidence-vectors/pull/425 remains open
at eb4bef6e7e4508d08362a12f55cb3366f5d7d816. Its restored digest-list signature
metadata does not amend the rule-2/rule-3 proposal. Signature correctness was
not cryptographically checked here. The review continues to use the registry
and corpus pinned by -00; newer release metadata does not replace those pins.

## Reproducibility and open work

The CI definition now runs review.py on Python 3.12 and 3.13 in a temporary
copy, preserving committed historical outputs. Workflow configuration alone
is not evidence that a hosted run passed; inspect the run for the exact commit.
Earlier green repository checks did not run this Restoration review.

The wording proposal still awaits author disposition. The additional examples
encode a proposed reading, not independently established intended semantics.
There is no claim of full conformance, blind clean-room authorship, DSSE or
JCS-byte validation, evidence truth, or justified resumption. A separate
implementation's reproduction remains open. No further message is scheduled.
