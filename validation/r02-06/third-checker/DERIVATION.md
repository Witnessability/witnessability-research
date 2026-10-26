# Derivation and proof sketch

Assume a prevalidated finite raw identity model. Let the coordinate alphabets be
`A_i` and let `U = product_i A_i`. Give each observation in `U` a distinct bit
position. For coordinate `i` and atom `x`, define the equality-mask set
`M(i,x) = {r in U : r_i = x}`.

For a declared honest record `a` and allowed fault set `F`, the implementation
forms the bitset corresponding to

`C(a,F) = intersection_{i outside F} M(i,a_i)`.

The intersection starts at all of `U`, so when every coordinate is faulty the
result is `U`. For any observation `r`, membership in this intersection means
exactly that `r` has the honest atom at every nonfaulty coordinate. Membership in
`U` already enforces an allowed alphabet atom at each faulty coordinate. Thus
`C(a,F)` is precisely the exposure contribution of this honest record and fault.

For each history `h`, the algorithm forms

`E_h = union_{a in joint[h], F in faults} C(a,F)`.

Every support record and fault is visited, so the cylinder lemma gives equality
between this union and the contract's exposure, in both directions. Bitwise
intersection and union preserve exactly these finite set operations.

The transpose step sets history bit `h` in row `r` exactly when the observation
bit `r` is in `E_h`. Consequently a row is exactly the compatible-history set.
An observation containing an out-of-alphabet atom is absent from `U` and its row
is empty, matching the contract. The four classifications follow by testing
whether the row is empty and whether it contains false and/or true history
bits. An empty set is not classified as `TRUE` or `FALSE`.

Let `T = union_{h:truth[h]} E_h` and
`N = union_{h:not truth[h]} E_h`. An observation lies in `T & N` exactly when it
has at least one true and one false compatible history. Thus `T & N` is empty
exactly when every opposite-truth history pair has disjoint exposure, proving
the capability result without iterating history pairs. If nonempty, select one
observation bit, then one compatible history of each truth value. Each selected
history's exposure is a union of its retained cylinders, so at least one of
those cylinders contains the selected bit. Retained honest/fault data for that
cylinder yields a valid ambiguity witness. This selection is done only for
collision production, not supplied-witness verification.

The supplied verifier checks each given witness's declared history and required
truth, honest-support membership, allowed fault membership, and that the record
has a declared alphabet atom on faulty coordinates and the honest atom on every
other coordinate. Those conditions are the cylinder definition above. Applying
them to the supplied false/true pair proves exactly that the common record is
ambiguous. Failure says this supplied pair is invalid in this narrow verifier;
it is not evidence of determinacy and does not trigger replacement search.

These arguments establish the algorithms under the stated mathematical and
prevalidation assumptions. They are a proof sketch, not a mechanized proof,
external audit or claim that Python execution or caller validation is flawless.
