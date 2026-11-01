H = Tuples[{0, 1}, 6];                       (* (uA,uB,xA,xB,m1,m2); m1, m2 uniform masks *)
p[h_] := h[[1]] h[[3]]; s1[h_] := h[[2]]; s2[h_] := h[[1]];
designs = <|"bound" -> {({#[[1]], #[[2]]} &), ({#[[3]], #[[4]]} &)},
   "scoped" -> {(#[[1]] &), (#[[3]] &)},
   "xor" -> {(Mod[#[[1]] + #[[5]], 2] &), (#[[5]] &), (Mod[#[[3]] + #[[6]], 2] &), (#[[6]] &)}|>;
rec[d_, h_, C_] := Table[d[[c]][h], {c, C}];
decides[d_, C_, f_] := AllTrue[Values[GroupBy[H, rec[d, #, C] &]], Length[Union[f /@ #]] == 1 &];
tv[d_, C_, f_] := Module[{k1 = rec[d, #, C] & /@ Select[H, f[#] == 1 &], k0 = rec[d, #, C] & /@ Select[H, f[#] == 0 &], c1, c0, cs},
   c1 = Counts[k1]/Length[k1]; c0 = Counts[k0]/Length[k0]; cs = Union[Keys[c1], Keys[c0]];
   Total[Abs[Lookup[c1, Key /@ cs, 0] - Lookup[c0, Key /@ cs, 0]]]/2];
Table[With[{d = designs[k]}, {k, Table[{C, decides[d, C, p], tv[d, C, p], tv[d, C, s1], tv[d, C, s2]},
    {C, Rest[Subsets[Range[Length[d]]]]}]}], {k, Keys[designs]}]
