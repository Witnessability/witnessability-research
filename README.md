# Witnessability Research

Executable finite examples of which claims a consumer can decide from a
declared observation, and how that capability changes under explicit capture,
binding and fault assumptions. The protocols and executions here are
development work, not preregistered main results.

## Endpoint observations and a commit counter

The first experiment, [`endpoint-counter-001`](experiments/endpoint-counter-001/docs/PROTOCOL.md),
examines the claim that no completed write occurred in a fixed interval.
Identical initial and final values can describe both no write and a write
followed by restoration. A correctly bound exact commit counter distinguishes
those histories when every completed write and its increment are atomic.

The runner enumerates 40 histories of up to three actions over `noop`, `write0`
and `write1`, starting at zero. Same-value writes count. Eleven models compare
endpoint-only observations, exact capture, missing or misbound receipts,
capture gaps, bypass, reset, wrapping, phantom counts, a faulty issuer and
shared control. These are abstract events in a finite model, not physical store
writes or evidence of independent control in a deployment.

Two calculation paths check the same model. They are not independently authored
implementations. The kernel uses identity binding transformations and separates
`TRUE`, `FALSE`, `UNRESOLVED` and `OUTSIDE_MODEL` from carrier admission errors.
A test HMAC with a public fixture key checks bytes only; anyone can mint it.

See the [protocol](experiments/endpoint-counter-001/docs/PROTOCOL.md),
[prior work](experiments/endpoint-counter-001/docs/PRIOR-WORK.md) and
[limitations](experiments/endpoint-counter-001/docs/LIMITATIONS.md).
This repository does not amend [Witnessability Core](https://github.com/Witnessability/witnessability-core)
or [Witnessability Model](https://github.com/Witnessability/witnessability-model).

## Run locally

Python 3.12 or later and Make are sufficient. The experiment uses the Python
standard library and makes no network requests.

```sh
make check
make run
make replay
```

`make run` creates `runs/development-local`; `make replay` checks its saved
records by recomputation. Existing nonempty output directories are refused.
For a fresh run, use the same new `RUN_DIR` with both commands:

```sh
make run RUN_DIR=runs/development-second
make replay RUN_DIR=runs/development-second
```

Local development checks passed all 19 tests on CPython 3.12.14 and 3.13.16;
generation and recomputation also passed on both. These were local checks,
not a report of hosted CI or a physical experiment. The workflow in
`.github/workflows/check.yml` runs development checks on Python 3.12 and 3.13
and performs no publication actions.

The run's `source_pin` hashes the Python package files; `protocol_pin` hashes the
machine-readable experiment contract. Neither hashes the full repository or
the prose protocol. Retain the exact repository commit with a shared run.
Successful replay establishes consistency with the declared finite model and
source, not real-world collection completeness.

A later protocol freeze cannot preregister already observed development
outcomes. Repeating known finite counts is reproduction, not a new prediction.

## Contributing and reuse

Read [CONTRIBUTING.md](CONTRIBUTING.md). Software is Apache-2.0, documentation
is CC-BY-4.0, and newly authored synthetic data is CC0-1.0, with the exact path
map and exceptions in [LICENSE.md](LICENSE.md). Attribution is in [NOTICE](NOTICE).
No collaboration, coauthorship or endorsement by authors of cited work is implied.
