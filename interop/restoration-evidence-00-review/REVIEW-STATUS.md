# Publication preparation review (retained pre-publication snapshot)

Two passes use the same implementation and reviewer; they are not independent replication.
Pass 1 reviews sources, rule ordering, corpus results and baseline preservation.
Pass 2 extracts the final archive, verifies hashes, runs the replay offline in a fresh
directory, compares outcomes and checks the minimal default-only patch.

Upstream main remains 317df600f9a1503f32bcc2742b9f111036bdee32.
PR #421 remains merged; #425 remains open. The observed discussion still contains
the original announcement and Konrad's reply, with no newer message returned.

The diagnostic mode retains 57 verdict matches and 56 reason matches.
Profile and corrected default both match all 57 verdicts and reasons.
The 30 original tests pass on both versions; all 22 boundary examples pass.

The private working archive is not a publication asset. This export omits private
correspondence, repository links, internal gate records and superseded interpretation
prose. It preserves original checker and archived result bytes, adds current
interpretations and explicit path-specific license notices.

Suggested destination: Witnessability/witnessability-research,
interop/restoration-evidence-00-review/. Destination main inspected:
5cd9b5933d26cbe8f0014479a631dd7dcd523afd.
This is a standalone review package. Original-prototype make check/run/replay
and repository CI were not run and are not claimed here.

At the preparation checkpoint, no branch, commit, PR, release or email had been created.
Publication still requires a final target/actor/request review and authorization.
Email additionally requires recipient, thread and attachment binding.

