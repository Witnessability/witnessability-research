<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Bounded R02-06 results (development candidate)

The linked JSON files are explicitly labelled disclosure projections of
the recorded runs. Raw metadata hashes, removed fields and path mappings
are retained in each projection; original commands and private locators
are omitted. Numeric results and stream digests are unchanged. These are
not raw logs or new executions. The commands below are reproduction
examples, not substituted historical transcripts.

The [protocol](PROTOCOL.md) fixed the classes before the pilot and full runs.
All three paths agreed on full compatible-history sets, record verdicts and raw
capability. The original exposure routine is cached by the harness; the
standalone component is source-imported for these mathematical comparisons.
This is not a wheel/CLI comparison or external independent implementation.

| Declared class | Models | Record queries per interpreter |
|---|---:|---:|
| Original 2x2 support class | 1,125 | 5,625 |
| 3x3 singleton supports, all truth maps/fault families | 77,824 | 700,416 |
| 3x3 six-support catalog, all truth maps/fault families | 32,832 | 295,488 |
| Total | 111,781 | 1,001,529 |

Recorded runs: [Python 3.12.14](results/full-python312.json), 75.333 seconds;
[Python 3.13.16](results/full-python313.json), 77.538 seconds. Both PASS.
Each run cross-verified 142,646 supplied certificate objects (two per negative
capability, not necessarily distinct) using all three witness checks: 427,938
verification calls. The model and result stream hashes match across runtimes.
Per-operation parse/work budgets remain active; a failure yields no verdict.

These counts are conditional on labelled finite histories, the declared joint
supports, identity binding and fault families. They do not establish real
capture, a full arbitrary-support 3x3 result, admission-only semantics, complete
AAR/WEXP implementation, external participation or general correctness.
The third implementation is separately authored inside the same agent system;
its design direction and shared contract are disclosed in
[PROVENANCE](third-checker/PROVENANCE.md). No authoritative oracle is claimed.

Run from the source root, with a fresh output path (Python 3.12+, POSIX for the
bounded harness deadline; standard library only):

```sh
python -m unittest discover -s validation/r02-06/third-checker -v
python validation/r02-06/run_mutations.py --source . --reference validation/r02-06/third-checker --output /tmp/r0206-mutations.json
python validation/r02-06/run_consistency.py --source . --reference validation/r02-06/third-checker --wall-seconds 600 --output /tmp/r0206-full.json
```

The six deliberately wrong functions and their literal expectations are in
`run_mutations.py`; they are test-only mutations, never production revisions.
The development workflow retains the original experiment checks and adds
standalone tests, directed controls and a bounded smoke prefix. The full
R02-06 run remains an explicit extended validation with its measured budget;
the CI smoke prefix does not reproduce the full recorded run. The linked [3.12 mutation summary](results/mutations-python312.json) and
[3.13 mutation summary](results/mutations-python313.json) preserve the
recorded results and point to unchanged case bytes. Raw original metadata
and clean installation/replay evidence remain in the private preparation
archive; this source projection does not claim to publish that full archive.
