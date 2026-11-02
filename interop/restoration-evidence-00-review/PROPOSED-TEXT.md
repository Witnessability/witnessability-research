# Proposed clarification of Restoration Evidence -00, Section 4.4

Status: proposal for author review; not an adopted interpretation or a published erratum.
Anchor: draft-gilda-audit-restoration-evidence-00.txt, SHA-256
0ae1b94c226cf85b006dfb34abf2180e9dcbda34ad30b9933067df37eafec745.
Retain rule numbers, reason codes, type URIs, and the Section 10 release pin.

Replace the descriptions of rules 2 and 3 in Table 1 with:

| Rule | Proposed description | Existing code |
| --- | --- | --- |
| 2 | The predicate satisfies its member, type, and structural constraints, including membership in closed sets defined by this document, except for the particular constraints assigned to later rules. | predicate-malformed |
| 3 | Each value drawn from a registry term named in Section 4.3 belongs to the set accepted for that member under the registry digest pinned there. | closed-vocabulary-violation |

Insert immediately after Table 1:

> For first-failure reporting, a reader MUST defer to a later rule only the particular condition that rule tests. Deferring a presence, cardinality, or conditional constraint does not defer type checks or other structural constraints on members that are present. A predicate that fails a non-deferred constraint MUST be rejected under rule 2 before rule 3 is evaluated. Membership in a document-defined closed set is checked under rule 2; membership in a registry-defined set named in Section 4.3 is checked under rule 3.

Suggested non-normative examples following this paragraph:

- An R3 approver role of `approver` fails rule 2; an unknown string in `independenceBasis` fails rule 3. If the latter record also lacks `producer`, rule 2 fails first.
- In R1, absence of an authorized party's `authorityBasis` reaches R1.6; a present non-string `authorityBasis` fails rule 2. An unknown registry value in `intentBinding` precedes the missing-basis failure.
- In R3, a missing evidence slot reaches R3.4, an empty `notAddressed` explanation reaches R3.5, and an empty approver list reaches R3.6. A missing `evidence` object or a non-string `notAddressed` fails rule 2.

The executable examples also cover R1.10, R2.7, R3.7, R3.8 and R4.4. They are proposed boundary controls, not upstream conformance vectors. Their expected reasons state the proposed reading explicitly; agreement with our checker alone is not independent validation of that reading.

Why this is needed: Section 4.4's broad description of rule 3 can be read as covering every closed set. Section 10 and the pinned manifest already settle the published role case and explain that R4/RB have no registry-defined values. The proposal makes this boundary explicit where rule order is specified. It does not establish a reference-reader defect.

PR #421 adds registry terms but explicitly defers profile/corpus migration. Its new registry must not be silently substituted for the digest pinned by -00. Such a migration is a separate versioning decision; this proposal does not attempt it.

