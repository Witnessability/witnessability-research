# Restoration Evidence -00: rule-order review

Reproduce the saved candidate, the default-mode correction and the proposed boundary controls:

```sh
python3 review.py
```

Python 3.12+ and its standard library are sufficient; tested on 3.12.14.
Read PROPOSED-TEXT.md and INTERPRETATIONS.md before interpreting results.
MESSAGE-TO-SANKALP.md is a proposed message, not evidence of sending.

The saved checker and archived results are unchanged. The command derives
proposed/checker.py with only three default changes and preserves explicit diagnostic mode.
All corpus inputs are pinned to probityai/agent-evidence-vectors v0.31.2.
Results are written to review-results/. The summary derives counts from executed checks.
The corpus and additional examples establish bounded agreement, not full conformance.

Freshness: reviewed upstream main 317df600f9a1503f32bcc2742b9f111036bdee32.
Its six profile/predicate documents and manifest match the saved versions.
PR #421 is merged but defers profile migration; #425 remained open.
No latest-version claim extends beyond these observations.

Third-party provenance and applicable terms are recorded in LICENSE-NOTICE.md.
This package contains no private correspondence or private repository links.
