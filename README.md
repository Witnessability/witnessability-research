# Witnessability Research

Two histories can leave the same endpoints and answer a factual question
differently. Start with value `0` and ask whether **no completed write occurred
to the fixed object between the fixed start and end fences**:

| History | Consumer's endpoint projection | Claim | Exact commit-count delta, if its premises hold |
| --- | --- | --- | --- |
| H0: no writes | initial `0`, final `0` | true | `0` |
| H1: `write1`, then `write0` | initial `0`, final `0` | false | `2` |

The endpoints alone are `UNRESOLVED` in this declared model. Adding the count
distinguishes this pair **only if** every completed write and its increment are
atomic, every such write is counted exactly once, other events are not counted,
the counter does not reset or wrap, and its report is faithful and bound to the
same object, run, epoch and interval. Fences order the commits; the protected
sequential model has no pending or concurrent writes. Same-value writes count.
Under these premises, endpoint `0→0` with count `0` supports `TRUE`, while
count `2` supports `FALSE`. These are analytical expectations, not a newly
executed verifier run. One missed increment can hide a single same-value write;
it does not hide both writes of H1. The
[protocol](experiments/endpoint-counter-001/docs/PROTOCOL.md) distinguishes these
fault variants explicitly.

This is equality of an endpoint **projection**, not equality of complete audit
records, commitments or archived bytes. The project studies explicit finite
models; it does not establish real capture completeness from a counter format.
Protocols and executions are development work, not preregistered main results.
The standalone additions remain a development candidate, not a released v0.2.

## Read a result in five questions

| Question | Answer for the endpoint-only `0→0` example |
| --- | --- |
| What is claimed? | No completed write in the declared event class and interval; this includes completed writes of the existing value. |
| What was observed? | Only the initial and final values under the fixed context. Intermediate actions and the selected history ID are withheld from the observation. |
| What connection is assumed? | The projection and its binding describe the intended interval; the declared histories and fault model cover the alternatives being analysed. Their applicability is external to the checker. |
| Which alternatives remain? | No writes and write-and-restore both explain the endpoints and have opposite claim truth. |
| What would change the conclusion? | A faithful, correctly bound exact count under the premises above separates the alternatives. Missing capture, reset, wrap, misbinding or shared control require their own analysis. No cheapest or minimal repair is claimed. |

The evaluator receives the declared possible histories and their truth map;
it does not receive the selected case's hidden history as evidence. A result
is conditional on that model, not a discovery that omitted real histories
are impossible.

## Two components

- [`endpoint-counter-001`](experiments/endpoint-counter-001/docs/PROTOCOL.md)
  enumerates 40 histories of up to three actions over `noop`, `write0` and
  `write1`, starting at zero. Eleven models include capture gaps, bypass,
  reset, wrap, phantom counts, faulty reports and shared control. Events are
  simulated; separate keys or local processes do not establish independent
  administrative domains. A public fixture-key HMAC checks bytes only.
- The [standalone finite checker](standalone/README.md) evaluates saved explicit
  models, checks supplied ambiguity witnesses and decides raw capability.
  Its minimal installation does not need the experiment or store simulator.
  It uses identity binding and the exact [contract](standalone/CONTRACT.md);
  `admitted-only` capability is unsupported.

`TRUE`, `FALSE`, `UNRESOLVED` and `OUTSIDE_MODEL` describe compatible histories
after completed analysis. Input/admission errors and unfinished computation
are separate. An ambiguity certificate supplies opposite-truth histories for
one record; an invalid certificate establishes no replacement verdict. A
decidable record does not imply capability over every record. See the
[glossary](docs/GLOSSARY.md) and [trust boundary](standalone/TRUST.md).

## Run locally

The original experiment uses Python 3.12 or later, Make and the Python standard
library. It makes no network requests:

```sh
make check
make run
make replay
```

`make run` creates `runs/development-local`; `make replay` recomputes its saved
records. Existing nonempty output directories are refused. Use the same fresh
directory for a further run and replay:

```sh
make run RUN_DIR=runs/development-second
make replay RUN_DIR=runs/development-second
```

These root commands exercise the original experiment. The standalone install
and its three commands are documented [separately](standalone/README.md).
Report actual commands, interpreter, exit statuses and artifact identities;
examples and expected values are not execution logs.

The candidate workflow in `.github/workflows/check.yml` retains those legacy
checks and adds the standalone suite on Python 3.12 and 3.13. With pip,
setuptools and wheel already installed, run its offline test stage locally:

```sh
make check-standalone PYTHON=python3 CHECK_DIR=runs/checker-ci
```

The output directory must be new. The stage needs a POSIX environment with
working `venv`/ensurepip (the CI runner uses Ubuntu). It retains command logs,
SHA-256 values and a summary. It first checks the CI driver's zero-test and
timeout failure paths, then runs standalone and third-checker unit tests, four positive
controls and six directed mutations, then a **64-model prefix of each of three
declared classes**. This is a smoke subset; it does not repeat the full R02-06
run or establish its coverage. A copied source is built with `--no-index
--no-deps --no-build-isolation`; a fresh virtual environment then exercises all
three installed operations outside the source tree, including alternative
witnesses, the console entry point and guarded import boundaries. No experiment
package is installed. Unit-test count floors prevent empty discovery from
being treated as successful execution; adjust them explicitly if suites change.

CI separately bootstraps pip 26.2.2, setuptools 84.1.0 and wheel 0.48.0 from the
package index before that offline stage. Runtime downloads and this bootstrap
require network access; the workflow as a whole is not described as offline.
Neither the workflow nor the local script publishes anything. A committed
workflow definition is not evidence that hosted jobs have run or passed.

The original run's `source_pin` hashes its Python package files;
`protocol_pin` hashes the machine-readable experiment contract. Neither hashes
the whole repository or prose protocol. Retain the exact commit with a shared
run. Historical source-pinned replay and explicit conversion into the standalone
contract remain different operations. A future freeze cannot preregister already
observed results; repeating known finite counts is reproduction.

The [bounded R02-06 validation](validation/r02-06/RESULTS.md) records exactly
which larger finite classes were run and the limits of the third implementation.

## Scope, provenance and contributions

The [three C1 event-absence cases](interop/event-absence-c1-checker/README.md)
pair this Checker with the published Probity fixture under stated assumptions.
The package contains pinned synthetic inputs, a runner, full expected outputs
and recorded Checker outputs. From the repository root, reproduce it with:

```sh
python interop/event-absence-c1-checker/run.py --out runs/event-absence-c1
```

Use Python 3.12 or newer and a new output directory. This is a bounded
comparison; it does not establish general equivalence or execute Probity.

Recorded [bounded validation](validation/r02-06/RESULTS.md) is provided
with its exact finite classes and disclosure limits; it is not a general
correctness proof or external validation. This source projection includes
selected legacy fixture fragments, the three standalone operations and
the bounded validation code. Root commands can generate and replay a
fresh 001 run. The complete historical parent runs and private clean-build
evidence bundle are not included here, so replay of every historical
artifact is not claimed publicly reproducible from this source alone.

Read the [limitations](experiments/endpoint-counter-001/docs/LIMITATIONS.md),
[prior work](experiments/endpoint-counter-001/docs/PRIOR-WORK.md) and
[algorithm and evidence provenance](docs/PROVENANCE.md). Write-and-restore
ambiguity and prior external commitments are not claimed as new. Related-work
citations do not imply collaboration, adoption or endorsement.

The [contribution and challenge procedure](CONTRIBUTING.md) explains how to
report a counterexample without overwriting earlier expectations. Cite the exact
commit and component using [CITATION.cff](CITATION.cff); unreleased changes are
listed in [CHANGELOG.md](CHANGELOG.md). This repository does not amend
[Witnessability Core](https://github.com/Witnessability/witnessability-core)
or [Witnessability Model](https://github.com/Witnessability/witnessability-model).

Reuse follows [LICENSE.md](LICENSE.md) and the applicable file notices;
attribution is in [NOTICE](NOTICE). New documentation carries CC-BY-4.0 notices.
