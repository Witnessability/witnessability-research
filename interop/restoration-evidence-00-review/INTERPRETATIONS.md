# Interpretation and assurance boundaries

This supersedes the historical wording that treated two modes as potentially conforming.
Section 10 requires the manifest's verdict and reason. The profile interpretation is the
default in proposed/checker.py; explicit draft mode is diagnostic and fails one required reason.

Rule 2 checks document-defined closed sets and structural constraints. Rule 3 checks
registry-defined sets. Only the specific condition assigned to a later rule is deferred.
The proposed text asks the author to confirm this staging explicitly.

The checker is an unsigned research candidate, not a complete -00 implementation.
It does not verify DSSE, signer authority, JCS bytes, evidence truth, or admission safety.
It accepts only whole-second uppercase-Z timestamps, rejects leap seconds, floats,
unsafe integers, duplicate decoded keys and nesting beyond 128. These are bounded
implementation choices, not demonstrated full inherited AUDIT-RECORD conformance.
Bundle B1 ties use input order; the CLI sorts filenames. B2 counts carried occurrences.
B5 uses a common incident identity intersection, not transitive pairwise overlap.
B7 tests restored credential membership in a sweep population, not successful revocation.
One R3 and predecessor closure have local input-error codes after B7.
Unknown registries return local unsupported. No universal JSON Schema engine was run.
The graph cycle tests do not create hash-valid cyclic bundles.

Expected corpus outcomes were exposed before implementation. No author checker,
generator or Go implementation was used. This is not a blind clean-room claim.
The two review passes use the same authored implementation; they are not independent
implementations or independent human reviews.
