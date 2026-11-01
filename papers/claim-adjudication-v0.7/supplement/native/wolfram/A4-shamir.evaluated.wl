{$Version, AbsoluteTiming[(
H = Flatten[Table[{a, b, c, d, r1, r2}, {a, 0, 1}, {b, 0, 1}, {c, 0, 1}, {d, 0, 1}, {r1, 0, 4}, {r2, 0, 4}], 5];
p[h_] := h[[1]] h[[3]]; s1[h_] := h[[2]]; s2[h_] := h[[1]];
share[h_, i_] := {Mod[h[[1]] + h[[5]] i, 5], Mod[h[[3]] + h[[6]] i, 5]};   (* custodian i = 1..4 *)
rec[h_, C_] := Table[share[h, i], {i, C}];
decides[C_, f_] := AllTrue[Values[GroupBy[H, rec[#, C] &]], Length[Union[f /@ #]] == 1 &];
honest = GroupBy[H, p]; alph = Tuples[Range[0, 4], 2];
obsT1[h_] := Union[Flatten[Table[ReplacePart[rec[h, Range[4]], g -> v], {g, 4}, {v, alph}], 1], {rec[h, Range[4]]}];
{Min[Flatten[Outer[Count[MapThread[Unequal, {rec[#1, Range[4]], rec[#2, Range[4]]}], True] &, honest[0], honest[1], 1]]],
 Intersection[Union[Flatten[obsT1 /@ honest[0], 1]], Union[Flatten[obsT1 /@ honest[1], 1]]] == {},
 Count[Select[Rest[Subsets[Range[4]]], Length[#] >= 2 &], C_ /; decides[C, p]],
 decides[Range[4], s1], decides[Range[4], s2]}
(* expected: {3, True, 11, False, True} *)
)]}
