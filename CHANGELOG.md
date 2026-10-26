<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Changelog

## Unreleased development candidate

- Extract the existing finite criteria into a separate installation target
  with `evaluate-record`, `verify-ambiguity` and raw `check-capability`.
  Strict input validation, external version/policy context and bounded
  processing are documented in [the contract](standalone/CONTRACT.md).
  This is an adaptation of the project's existing algorithms, not an
  independently authored implementation or a completed v0.2 release.
- Preserve the original package and source-pinned replay. Legacy conversion
  is explicit; new expected context is not trusted merely because it was
  computed from an input. The development follow-up replaced optimization-
  removable assertions in replay-evidence helpers with explicit checks and
  corrected the standalone README's virtual-environment command paths.
- Add an endpoint/counter explanation with its assumptions, a
  [contract glossary](docs/GLOSSARY.md), [provenance](docs/PROVENANCE.md),
  citation metadata and a [challenge procedure](CONTRIBUTING.md).

- Add the [bounded R02-06 validation](validation/r02-06/RESULTS.md), including
  a separately authored internal bit-mask reference, declared 3x3 sublanguages
  and directed test-only mutations. This does not replace the installed checker.
- Extend the development CI definition on Python 3.12/3.13 with standalone and
  third-checker tests, directed mutations, a bounded smoke prefix and an offline
  isolated installation check. The existing experiment checks remain. Build-tool
  bootstrap is separate; hosted CI success is not implied by this definition.

These entries describe development changes. They assign no release date, DOI,
new package name, external review or collaboration status. Validation claims
must refer to the exact candidate's recorded commands and artifacts; the linked
R02-06 report gives the actual bounded runs and their provenance.

## Public baseline used by this candidate

Commit [`9ec68cff4981567705490b44ab5f76ffc0590cbb`](https://github.com/Witnessability/witnessability-research/commit/9ec68cff4981567705490b44ab5f76ffc0590cbb)
contains the original endpoint-counter development runner and finite model
code. The root package declares version `0.1.0`; the standalone candidate
declares `0.2.0.dev1`. These package metadata values do not imply corresponding
repository releases. Baseline files and historical run identities remain
available for exact replay; changed expectations require a new visible version.
