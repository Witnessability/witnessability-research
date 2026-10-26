# Standalone finite checker — private candidate

This separate installation target exposes three operations on saved explicit
finite models: `evaluate-record`, `verify-ambiguity`, and `check-capability`.
It retains the baseline's identity-binding semantics and adds strict input,
versioned external context and bounded processing. The existing
`witnessability-research` package and its source-pinned replay are unchanged.

The distribution `witnessability-research-checker`, import package
`witnessability_checker`, and executable `witnessability-checker` are provisional
candidate identifiers. No public rename, package registration or release is
implied. The technical description “finite adjudication kernel” does not make
this an implementation of all WCC/WM.

## Small example

The saved `mixed` control has one coordinate and three histories. False history
`f` can produce `0`; false `g` can produce `0` or `2`; true `t` can produce `0`
or `1`. There are no allowed faults except the empty set. Record `0` is
ambiguous because `f` and `t` have opposite truth. A different witness using
`g` and `t` is equally valid. Record `1` is `TRUE`, even though raw capability
is false because of the ambiguity at `0`. Record `2` is `FALSE`, and record
`3` is `OUTSIDE_MODEL` because no history can produce it.

These are hand-derived expectations in `fixtures/MANUAL-EXPECTATIONS.md`.
Execution results belong in the private candidate's verification records;
expected values are not measurements. To change ambiguity at `0`, one must
change the declared observation relation or admissible alternatives with an
explicit justification. Renaming a field, adding a digest, or changing admission
without declaring a different scope does not resolve raw ambiguity.

## Install and run

Use Python 3.12 or later. Build/install this directory as its own project, not
the repository root. With prepared build dependencies, an offline local build
can use:

```sh
python -m pip wheel --no-deps --no-build-isolation ./standalone -w /tmp/checker-wheels
python -m venv /tmp/checker-env
/tmp/checker-env/bin/python -m pip install --no-index --no-deps /tmp/checker-wheels/witnessability_research_checker-0.2.0.dev1-py3-none-any.whl
```

The exact wheel name and actual build versions are retained with the candidate.
Run installed commands outside the source tree with `PYTHONPATH` unset:

```sh
/tmp/checker-env/bin/witnessability-checker evaluate-record --model MODEL.json --record RECORD.json --policy POLICY.json --expected EXPECTED.json
/tmp/checker-env/bin/witnessability-checker verify-ambiguity --model MODEL.json --record RECORD.json --certificate CERTIFICATE.json --policy POLICY.json --expected EXPECTED.json
/tmp/checker-env/bin/witnessability-checker check-capability --model MODEL.json --policy POLICY.json --expected MODEL-EXPECTED.json --scope raw
```

The environment's Python accepts the same arguments through the module entry point:

```sh
/tmp/checker-env/bin/python -m witnessability_checker evaluate-record --model MODEL.json --record RECORD.json --policy POLICY.json --expected EXPECTED.json
```

The external
expected-pins file is mandatory; the certificate is never its trust source.
The first two commands need a record pin, while capability's expected context
does not contain one. Only raw capability is supported; admitted-only scope
gets a separate unsupported outcome.

Read [CONTRACT.md](CONTRACT.md) for exact schemas, pins, versions, errors and
limits, and [TRUST.md](TRUST.md) for per-operation dependencies and external
assumptions. `verify-ambiguity` checks the supplied witness without importing
the search module or regenerating an experiment. A failed witness does not
establish a record verdict.

## Admission, legacy input and limits

The explicit `declared-model/1` policy asks the caller to acknowledge applicability
of the declared assumptions. It authenticates nothing and does not import 001's
store/HMAC policy. A rejected carrier in the old experiment is not silently
turned into an admitted carrier here; a raw mathematical analysis has a different
admission contract. Legacy conversion is explicit and preserves the old model,
claim and record pins while adding new version/policy bindings.

The minimal wheel does not install experiment/store simulation. Old exact replay
uses an immutable checkout of public base
`9ec68cff4981567705490b44ab5f76ffc0590cbb` and its original `run`/`verify-run`
CLI. All files under the old `src/witnessability_research/` remain untouched so
their source-pinned replay path is preserved.

This component implements the bounded contract above. A validation package must
name its selected finite classes, completed checks and remaining work; neither
full 3×3 coverage nor independent implementation follows from installing it.
Coverage-002, external comparison, optimization, symbolic backends and WCC/WM
manuscript changes are separate work. Analysis of finite inputs does not establish
real event capture, collection completeness or superiority over another tool.

See the [result glossary](../docs/GLOSSARY.md),
[algorithm and evidence provenance](../docs/PROVENANCE.md), and
[contribution/challenge procedure](../CONTRIBUTING.md). The current component
remains a development candidate; its package version does not announce a
public release or completion of the full v0.2 plan.
