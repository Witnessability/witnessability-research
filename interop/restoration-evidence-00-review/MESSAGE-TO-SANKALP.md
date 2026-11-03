# Restoration Evidence -00: technical message

Current approved public wording. Supersedes the preparation text in commit cc97bb27be610b8b0fe03a3ea58e40d6c09d7d31. Quoted correspondence and mail transport metadata are excluded.

Hi Sankalp,

Thank you for inviting checks of Restoration Evidence -00. Following Konrad's observation about the rule-3 boundary, I have prepared a proposed clarification and reproducible first-failure examples.

Against the v0.31.2 corpus pinned by Section 10, the checker matches all 57 verdicts and reasons. It checks document-defined closed sets under rule 2 and registry-defined sets under rule 3. Section 10 already settles the published approver-role case; the proposal makes that boundary explicit in Section 4.4.

Could the rule descriptions specify that:
- Rule 2 checks member, type and structural constraints, including document-defined closed sets, except for the particular conditions assigned to later rules.
- Rule 3 checks the accepted sets of the registry terms named in Section 4.3, using its pinned digest.
- Deferring a condition to a later rule does not defer type checks on present members or unrelated structural checks.

Three examples illustrate the proposed precedence:
1. Unknown independenceBasis plus missing producer: predicate-malformed.
2. Missing R1 authorityBasis on an authorized party: authority-basis-missing; a present numeric authorityBasis: predicate-malformed.
3. Missing R3 evidence slot plus an empty explanation and no approvers: evidence-slot-missing; a malformed present slot value instead makes rule 2 fail first.

The proposed text, checker, 22 additional boundary examples and offline replay script are here:
https://github.com/Witnessability/witnessability-research/tree/cc97bb27be610b8b0fe03a3ea58e40d6c09d7d31/interop/restoration-evidence-00-review

These examples express the proposed reading; agreement with this checker alone does not establish the intended semantics. The review retains the registry and corpus pinned by -00.

The checker was authored without using your checker, generator or Go reader. Expected corpus outcomes were exposed before implementation, so this is not a blind clean-room claim. The results cover unsigned records and bundles, not DSSE signatures, canonical JCS bytes, evidence truth or whether resumption is justified; they do not establish full draft conformance.

Would this wording capture the intended first-failure semantics?

Best,
Mikhail
