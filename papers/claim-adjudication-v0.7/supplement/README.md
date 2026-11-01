# Reproducibility supplement

This supplement contains the scientific code, retained data and bounded
verification results for the accompanying reader draft.

## Contents

- `code/`: supplied Python checkers and retained-data validator.
- `data/retained-study/`: complete retained file-study evidence and its
  original source file. The 149 files in `evidence/executed_case/`, including
  its 148-entry manifest, are unchanged. The separate
  `PACKAGE_MANIFEST.json` is a new manifest of this curated scientific subset;
  it is not the original larger archive manifest.
- `data/local_certificates.json`: local propositional certificates.
- `expected/`: retained expected scientific results. Four execution-specific
  metadata fields are omitted from the retained-data baseline, and its outer
  manifest count reflects the curated subset. Scientific observations and
  signature evidence remain unchanged.
- `native/`: retained Wolfram source/evaluated input and result records,
  original and corrected Lean source, and compilation diagnostics.
- `SOURCE-PINS.json`: exact SHA-256 inventory of data, checkers, expected
  results and native files. Hashes provide integrity checks, not attestation.
- `LITERATURE-STATUS.md`: source-comparison scope and remaining access gaps.
- `REPLAY-CHECK.json`: verification summary for two fresh runs, including a
  path containing spaces. Both matched the supplied expected scientific results.

## Reproduce the Python checks

Use Python 3.10 or newer with the dependency in `requirements.txt`.
The recorded checks used Python 3.12 and cryptography 50.0.2.
From this directory run:

```sh
python3 -B tools/reproduce.py --output fresh-results
```

The output directory must be new. Do not use `-O`, `-OO` or
`PYTHONOPTIMIZE`, because the supplied checkers use assertions. The wrapper
verifies the input inventory, copies study data to a temporary directory and
checks that supplied inputs remain unchanged. It executes six checks and
three expected-rejection controls, capturing output and exit status.

The finite checker covers 13,536 exhaustive binary configurations, 300 seeded
configurations and 252 portfolios. Other checks cover local resolution
certificates, a domain-permutation boundary example, 224 retained signatures
with signed-target mutations, the declared file-study projection, and anchors
in 26 model/group pairs and 116 budget cases. The three isolated negative
controls alter a signature, a signed payload and a manifest-covered file.
Every expected scientific result is compared; only elapsed time is omitted
for the finite checker. Retained-data comparisons omit validation time,
temporary package path and dependency versions. The outer manifest count is
checked against the curated subset. All other compared fields are unchanged.

## Interpretation limits

These are executions of supplied implementations and validation of retained
records. They are not an independently authored implementation, independent
human review or a proof of the full mathematical theorem.

The original file-producing study is not executed, and no private signing
keys are used. Retained bytes and valid signatures do not independently
establish historical operating-system events, writes, fsync calls, timestamps,
controller identity or independence of administrative domains. The six-domain
model is hypothetical; the one-host arrangement has one actual failure domain.

The Python resolution check covers two local propositional implications. It
does not verify the full first-order theorem or an arbitrary observation adapter.

The wrapper does not execute Wolfram or Lean. The native result records are
retained from 29 October 2026. Their original earlier runtime transcript was
unavailable. The Wolfram A.2 block checks Proposition 1 detection only; the
separate A.2 extension adds Theorem 1 adjudication checks. The original Lean
file fails with Lean 4.33.1; its one-line corrected copy checks only the
pointwise gluing lemma. The observation quotient and global decoder
equivalence remain outside that formalization. No full machine-checked proof
is claimed.

`VERIFICATION-DETAILS.md` gives the detailed replay provenance and scope summarized by the verification-coverage table in the manuscript.

## Additional reader checks

LEDGER-APPLICATION.md supplies commands for 28 projected ledger verdicts and eight constructed search/capture cases. FINITE-FAMILY.md supplies the exhaustive 5,625-model check. These are separate from the historical six-check wrapper above. Their code, data and expected results are covered by the package MANIFEST.json; SOURCE-PINS.json remains the unchanged historical 180-file inventory.
