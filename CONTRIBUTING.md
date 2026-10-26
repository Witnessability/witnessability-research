# Contributing and challenging a result

Contributions should state which scientific claim or reproducibility property
they improve. The research protocol remains a development candidate.
Review the path-specific terms in [LICENSE.md](LICENSE.md). Submit original
contributions under the applicable project license, and identify any third-party
material and its separate terms before proposing its inclusion.

For a proposed experiment or correction, identify the claim, admissible
histories, observation boundary, binding assumptions and allowed faults. Supply
a small counterexample or the exact command and input identity needed to
reproduce the change. Separate a record's verdict from capability over all
records and separate carrier validity from factual support.

Run `make check`, `make run` and `make replay` for changes to the original
executable prototype. For standalone changes, also exercise the affected
operations and their contract tests using the [standalone instructions](standalone/README.md).
State the interpreter version, exact commands and skipped checks. Do not
describe development execution as a preregistered main run or same-authored
calculation paths as independent implementations.

## Report a challenge through the existing issue or pull-request route

Use an [issue](https://github.com/Witnessability/witnessability-research/issues)
for a disputed expectation, model premise or result. A proposed correction may
use a pull request linked to that issue. These routes do not require a new
review service or an agreement with an external project.

Include enough information to distinguish the following:

| Item | Required distinction |
| --- | --- |
| Target | Repository commit, component and case/run identifier; preserve the original bytes or their hashes. |
| Claim and context | Exact proposition, event class, scope and interval; model, observation projection, binding and allowed faults. |
| Contract | Schema, semantics, admission policy, raw/admitted scope and expected pins from their declared source. |
| Disagreement | Original expectation, proposed expectation and why they differ. Mark a hand-derived control separately from actual output. |
| Reproduction | Minimal input/counterexample; exact command, runtime, exit status and relevant output. If no run occurred, say so. |
| Consequence | Implementation defect, changed premise, unsupported translation, documentation defect or an unresolved interpretation. |

An alternative valid ambiguity witness is welcome. A rejected witness alone
does not refute another witness or establish `TRUE`, `FALSE` or capability.
Likewise, admission rejection and resource exhaustion are not claim refutations.
For cross-project comparisons, identify both versioned contracts before comparing
their words; the [glossary](docs/GLOSSARY.md) supplies no automatic translation.

## Record disposition and authority

The maintainer handling a challenge records a disposition in the issue or linked
review: **open**, **reproduced**, **correction accepted**, **not reproduced with
the stated inputs**, or **unresolved/disputed**. These are human review labels,
not additional checker verdicts. Record the resolver, reviewed versions, reason,
supporting evidence and any remaining disagreement. Closing an issue does not
by itself establish scientific consensus.

Project maintainers decide changes to this repository within their permissions.
They do not determine another project's semantics, amend WCC/WEXP by implication,
or speak for cited authors. A cross-project question can remain open when the
relevant authority or comparison fragment has not been established. No shared
governance, response deadline or outside participation is presumed.

Keep the original expectation and dissent visible in the discussion and version
history. An accepted correction receives a new commit and a changelog entry
linking the old case/version, reason and replacement. Do not overwrite released
result artifacts, move an existing release identifier to changed bytes, or
silently rescore an old release. If new evidence changes an interpretation,
record the superseding assessment while retaining what the original version
expected. Protocol amendments after a freeze must explain their inference impact.

Never submit private correspondence, credentials, private manuscripts, or
unapproved third-party material. Cite public prior work and distinguish its
reported results from results independently reproduced here. A public issue
is not permission to republish another person's material.
