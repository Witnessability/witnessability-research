Subject: Re: Restoration Evidence -00: clarification of rules 2/3 and first-failure precedence

Hi Sankalp,

Following Konrad's report on the rule-3 boundary, I continued an independently authored checker against Restoration Evidence -00 and vectors v0.31.2. I have also reviewed PR #421: it adds the vocabulary terms but explicitly leaves profile/corpus migration to a follow-up. At main commit 317df600f9a1503f32bcc2742b9f111036bdee32, the six pinned profile/predicate documents and the 57-member manifest remain byte-identical to our saved sources.

With document-defined closed sets checked under rule 2 and the Section 4.3 registry terms under rule 3, all 57 cases match both verdict and reason. A diagnostic interpretation that routes every unknown closed string to rule 3 differs on one reason: re-enable-decision-predicate-malformed, where an approver role is changed to "approver". Section 10 requires the manifest's predicate-malformed result, so I am not suggesting that both interpretations conform to -00.

Our earlier candidate defaulted to that diagnostic mode. A local three-default correction now selects the corpus-compatible interpretation for the Reader, bundle API and CLI. The original results are retained. This is our default-selection defect, separate from the specification clarification below.

Could Section 4.4 explicitly define these boundaries?

- Rule 2: member, type and structural constraints, including document-defined closed sets, except for the particular constraints assigned to later rules.
- Rule 3: membership in the accepted sets of the registry terms named in Section 4.3, using the pinned digest.
- A later rule defers only its named condition; it does not defer type checks on a present member or unrelated structural checks.

Three useful first-failure controls are:

1. Unknown independenceBasis plus missing producer: predicate-malformed, not closed-vocabulary-violation.
2. Missing R1 authorityBasis on an authorized party: authority-basis-missing; a present numeric authorityBasis: predicate-malformed.
3. Missing R3 evidence slot plus empty explanation and no approvers: evidence-slot-missing; a malformed present slot value instead makes rule 2 fail first.

I prepared 22 reproducible boundary examples, a minimal proposed wording change, and an offline replay script. All 30 existing local controls pass with either default; the proposed default matches 57/57 corpus reasons. The examples extend precedence coverage but do not establish full conformance.

The original author checker, generator and Go reader were not used. Expected corpus outcomes were exposed before implementation, so this is not a blind clean-room claim. These checks cover unsigned record/bundle validation, not DSSE signatures, evidence truth, or whether resumption is justified.

Would the proposed wording capture the intended first-failure semantics for this pinned revision?

References:
- Draft: https://datatracker.ietf.org/doc/draft-gilda-audit-restoration-evidence/
- Pinned corpus: https://github.com/probityai/agent-evidence-vectors/tree/v0.31.2/vectors-restart-records
- Vocabulary PR: https://github.com/probityai/agent-evidence-vectors/pull/421
- Konrad's earlier observation: https://mailarchive.ietf.org/arch/msg/audit/1q5UhminBiyvWvqcr1xBs0KgobQ/

