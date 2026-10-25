# Endpoint observations and a bounded commit-counter repair

Status: development protocol candidate, 25 October 2026.
This document proposes a small finite diagnostic experiment. It is not a
preregistration, a frozen main-run protocol, or a report of a completed main run.
Any execution under this candidate is a development run and must be labelled as
such. Publication does not imply endorsement or participation by any author of
the related work.

## 1. Question and intended contribution

For a precisely defined event class and observation interval, which observations
allow a consumer to decide whether no completed write occurred? When an added
counter resolves an ambiguous endpoint observation, which capture, binding and
failure assumptions do the work?

The contribution sought is an inspectable diagnostic artifact: explicit
opposite-claim histories, a bounded additional observation, remaining
counterexamples under weakened assumptions, and a reproducible accounting of
the changed observation classes. Endpoint equality after write-and-restore is a
demonstration case, not a novelty claim. The experiment does not propose a new
cryptographic mechanism or establish general collection completeness.

## 2. Claim, histories and observation boundary

Fix a target object, a run identifier, an epoch and two ordered interval fences
before evaluating a run. The claim is:

> No completed write in the declared event class occurred to the target object
> between the start and end fences.

A completed write is a state-transition event defined by the experimental
store's commit rule. It is not defined by the existence of a receipt, an attempted
invocation, or a successful signature check. A write of the current value still
counts if it completes under that rule. The commit rule and treatment of failed
attempts must be fixed in the machine-readable model.

The initial prototype uses a finite, sequential history space: initial value 0;
trace alphabet `noop`, `write0`, `write1`; every trace of lengths 0 through 3.
There are 1 + 3 + 9 + 27 = 40 histories. `noop` does not commit a write;
`write0` and `write1` each commit one, including a write of the current value.
The four all-noop histories satisfy the claim and the other 36 falsify it.
These are hand-derived model expectations agreed during development, not new
experimental findings. Concurrent writers and crashes are excluded from the
protected baseline unless represented explicitly. A claim about arbitrary
writes outside this event class is a different claim.

The baseline adapter exposes the target/run/epoch/fence binding and the initial
and final values. It omits the intermediate writes and their number. The
selected run's full history is retained for experimental truth and reproduction,
but its hidden actions, per-case history identifier and expected verdict are
not supplied to the evaluator as evidence. The evaluator does receive the
declared finite model, including its possible histories and claim-truth
assignment: these define which alternatives are compatible with the observed
record. The restriction concerns revealing which history actually generated
the case, not withholding the model needed to adjudicate it.
The public binding context is fixed across the alternatives; a trace identifier,
length-bearing fence or lookup key must not leak which history was selected.

The illustrative pair is H0, with no write, and H1, with a write to another value
followed by restoration of the initial value. Their endpoint projections are
equal; the claim is true in H0 and false in H1. This is equality of the declared
projection. It is not a claim that their complete AAR records, commitments,
signatures, event roots or all archived bytes are equal.

## 3. Additional observation and its assumptions

The additional semantic observation is a commit-counter interval delta bound to
the same object, run, epoch and fences. The proposed values for the illustrative
pair are zero and two. These values are hand-derived expectations, not a report
of a new verifier run.

Under the protected-counter model, every declared completed write increments
the relevant counter exactly once; no other event increments it. The counter
does not reset or wrap in the interval. Its relevant capture/reporting domain
is excluded from the allowed faults. Its binding is checked. These are explicit
premises of this model, not consequences of the receipt format.

Commit and counter update must be atomic in the experimental abstraction, or
the crash window between them must be modeled. Two sequential function calls
do not establish atomicity. The protocol must distinguish a completed write
without a count from a counted attempt that never commits.

Fences are ordered relative to the commit point. The sequential prototype may
use explicit start/end barriers with no outstanding operation. A later concurrent
experiment must specify how writes begun before a fence and completed after it
are assigned; wall-clock timestamps alone do not supply this ordering.

The first implementation may simulate the counter and its faults. If processes
are run on one host under one controller, they remain one actual control domain.
The protected-counter interpretation is then conditional. Separate processes,
keys or signatures are not measured administrative independence.

## 4. Declared model variants and controls

Each variant must define complete possible observations for every admissible
history. The addition of a fault changes this relation or its underlying
histories; it must not be introduced only as a label on unchanged expectations.

| Variant/control | Required distinction |
|---|---|
| Endpoint-only baseline | Equal endpoint values can conceal completed writes. |
| Protected, correctly bound counter | A faithful delta may remove that ambiguity within the declared model. |
| Missing counter observation | Absence is not delta zero; any conclusion must come from the remaining observations. |
| Wrong object/run/epoch/interval or replay | A valid carrier may fail the binding required for this claim. |
| Reset or wrap | Equal endpoint counter values need not imply zero events. |
| Completed write bypasses capture | A zero delta may coexist with a completed write in the same declared event class. |
| Commit-before-count crash | State can change while the reported count lags. |
| Count-before-commit failure | A count can record an attempt without the claimed completed event. |
| Arbitrary counter report or common producer/counter control | Authentication alone does not exclude a false report. |
| Authenticated but false receipt | If signatures are implemented, a faulty source may sign false semantic content with its legitimate key. |

The candidate uses model identifiers `baseline`, `atomic`, `missing_receipt`,
`bad_binding`, `crash_gap`, `bypass`, `reset`, `wrap_mod2`, `overcount`,
`compromised_issuer` and `shared_control`.

The initial operational cases are bounded explicitly: one missed counter
increment for the crash-gap case; an arbitrary subset of writes missed for the
bypass case; a reset case; a counter modulo two; and one possible phantom count
for an aborted attempt. An arbitrary-reporting issuer case allows every counter
value in the declared finite alphabet. A separate shared-control model permits
replacement of both endpoint and counter observation blocks under common
control, including their downward-closed subsets. It does not assert that the
two blocks are independently controlled domains.
The exact possible outputs belong in the machine-readable configuration.

Operational counter failures are represented as nondeterminism in the joint
support for a history. These models allow no further domain replacement beyond
the empty failure set. `shared_control` separately exercises arbitrary block
replacements; its allowed family is the powerset of the two blocks. This
distinction prevents the same failure from being counted twice or described as
an independently measured fault budget.

A single missed increment can make H0 and a single `write0` share a zero count
and unchanged endpoint. It need not hide the two completed writes in
`write1, write0`: one count can remain, still falsifying the no-write claim.
The bypass and arbitrary-report cases test broader loss. This difference must
remain visible rather than grouping every capture fault under the same verdict.

A bypass control must enact an event included in the fixed claim. An unrelated
filesystem mutation outside the experimental store is not automatically a
counterexample to a claim confined to that store's commits. If this alternative
is included, the broader event scope must be explicit.

Controls need not make every observation unresolved. For example, a changed
endpoint may already rule out a no-write history. Expected outcomes are derived
per observation from the complete compatible-history set, not assigned from a
control's name.

## 5. Diagnostic contract

For a declared model M and an admitted semantic observation r, let C_M(r) be the
set of histories capable of producing r. Return:

| Compatible histories | Factual verdict |
|---|---|
| Nonempty; all satisfy the claim | TRUE |
| Nonempty; all falsify the claim | FALSE |
| Both truth values occur | UNRESOLVED |
| None | OUTSIDE_MODEL |

OUTSIDE_MODEL does not establish that the factual claim is false or identify
which assumption failed. An input that cannot be parsed or admitted receives
an input/carrier error, separately from the factual verdict. A missing optional
observation can be a well-formed model value. A missing required carrier or bad
binding must not be converted into a factual FALSE or a zero counter.

In the candidate consumer, an absent required receipt or a binding-rejected
receipt produces a carrier/admission rejection and no factual judgment. There
is no automatic endpoint-only fallback in this first version. The raw finite
model can still analyze observations containing missing or misbound receipts;
its capability result includes such records and must be labelled as a
raw-model result, not capability restricted to carrier-admitted inputs. These
two interfaces must not be combined into one percentage or pass/fail value.

Record-level adjudication and prospective capability are separate outputs.
An assembly can fail to decide some admissible records while deciding the
particular record under examination. If enumeration does not finish, report
incomplete computation rather than a guessed semantic result.

The first implementation is a narrow finite diagnostic kernel. It accepts
explicit finite domains and alphabets, nonempty joint honest supports, binary
history claims and downward-closed failure families containing the empty set.
The binding-transformation group is the identity. Direct enumeration constructs
the possible observations; the structural path checks whether an opposite-claim
honest-record disagreement set can be contained in the union of one allowed
failure set from each alternative history. It does not implement the full
general method with uncertain coordinate transformations. Binding-error controls
are explicit observation/capture variants, not a proved nontrivial group action.

## 6. Evaluation and acceptance checks

Before a main run, freeze a machine-readable configuration with the exact finite
world enumeration, model variants, observation adapters, expected distinctions,
software/dependency pins and reproduction command. Independently derive the
small hand-checkable expectations before generating the main-run result files.
The evaluator must not read the selected case's expected outcome or hidden
history identifier as evidence; the declared model's histories and truth map
remain legitimate inputs.

Use two calculation paths: direct compatible-history enumeration and a
separate pair-separation calculation for the implemented finite class. Neither
path delegates its decision to the other. Both may share the declared model
and authorship; agreement is a consistency check, not an independently authored
implementation or external scientific review.

Two small analytical checks must hold in the fault-free models. The endpoint
adapter has two observation classes: final value 0 is UNRESOLVED and final value
1 is FALSE. With the exact counter, there are seven attainable endpoint/count
classes: count zero with final 0 is TRUE; each count from 1 through 3 can have
either final value and is FALSE. These are model-derived expectations, not
probabilities, and do not apply unchanged to the faulty-domain models.

For each UNRESOLVED result retain two admitted histories with opposite claim
values and the same observation. The certificate checker must receive the
expected model, claim and observation identities from the verification request,
not accept self-consistent replacement identities supplied only by a certificate.
TRUE, FALSE and OUTSIDE_MODEL require complete enumeration or another declared
method of excluding the missing truth value(s).

Check all attainable observations in the finite models, not only H0/H1. A repair
of that pair does not establish global sufficiency. An added observation must
preserve the old observation possibilities under projection; if it instead
removes histories through a stronger architecture assumption, record that
assumption change separately.

Required development checks include:

- the H0/H1 baseline equality and opposite claim values;
- the protected-counter distinction and each fault control's compatible set;
- agreement of the two calculation paths on the supported finite class;
- rejection of altered certificate histories, model/claim/record identities
  and unauthorized transformations;
- separation of carrier failure, UNRESOLVED and OUTSIDE_MODEL;
- an always-accept, always-reject or endpoint-only naive rule failing at least
  one applicable contrast; a failure for the right reason, not merely any error;
- reproduction from pinned inputs without a private repository or a live network
  lookup determining the semantic result.

Report finite counts of decisive and unresolved observation classes, remaining
counterexamples, and resource use actually measured. These counts are not
deployment failure probabilities. If an observation catalog is added, claims of
minimality or minimum cost are limited to its explicit choices and costs;
checking one successful addition establishes neither.

## 7. Evidence packaging and future freeze

Retain source/model/configuration identities, interpreter and dependency
versions, exact commands, stdout/stderr, exit status, raw simulated or executed
records, projected observations, factual verdicts and obstruction certificates.
Keep experimental truth and evaluator inputs separately identifiable. Label
simulated events, executed effects and expected arithmetic distinctly.
The first candidate represents abstract committed-write events; it does not
execute physical store writes. If a development control uses HMAC with a public
test key, label it as such: every reader can generate a valid test MAC. It tests
MAC verification versus semantic truth, not public-key signatures, identity,
PKI or adversarial authentication of an independent observer.

Preparation results may guide corrections to this protocol. That exposure must
remain visible. A later freeze cannot retrospectively turn development runs
into preregistered or held-out tests. Any new main run must identify its frozen
protocol and disclose which cases and results were already inspected.
Repeating already checked finite counts under that freeze is a reproduction
check, not confirmation of a newly made prediction about unseen results.

Changes to the claim/event scope, finite bounds, fault variants or carrier
assumptions require a visible protocol revision before their results are
interpreted. Related-work citations acknowledge antecedents and artifacts;
they do not assert collaboration, endorsement or adoption.
