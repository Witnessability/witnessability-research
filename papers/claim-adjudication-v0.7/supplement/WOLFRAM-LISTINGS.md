## Appendix A. Finite Wolfram Language checks

The five code blocks below give finite checks for the stated models. A.1 and A.3 compare detection and adjudication; printed A.2 compares detection only; A.4 concerns Table 1. A separate supplementary A.2 extension adds adjudication checks. Records are lists of integers, and each block specifies its transformation representation. Exact replay provenance and retained source differences are documented in the supplement.

A.1 Exhaustive family (13,536 configurations; Proposition 1 and Theorem 1, structural against direct, both against the threshold).

```mathematica
dis[r_, s_] := Flatten[Position[MapThread[Unequal, {r, s}], True]];
ball[r_, F_] := Tuples[Table[If[MemberQ[F, g], {0, 1}, {r[[g]]}], {g, Length[r]}]];
phiT[m_, t_] := Select[Subsets[Range[m]], Length[#] <= t &];
opp[p_] := Select[Tuples[Range[3], 2], p[[#[[1]]]] != p[[#[[2]]]] &];
undetStruct[R_, p_, phi_] := AnyTrue[opp[p], Function[pr, AnyTrue[phi, SubsetQ[#, dis[R[[pr[[1]]]], R[[pr[[2]]]]]] &]]];
undetDirect[R_, p_, phi_] := AnyTrue[Range[3], Function[h0,
   With[{others = R[[Select[Range[3], p[[#]] != p[[h0]] &]]]},
    AnyTrue[phi, Function[F, AnyTrue[ball[R[[h0]], F], MemberQ[others, #] &]]]]]];
adjStructFail[R_, p_, phi_] := AnyTrue[opp[p], Function[pr, AnyTrue[Tuples[phi, 2], SubsetQ[Union @@ #, dis[R[[pr[[1]]]], R[[pr[[2]]]]]] &]]];
adjDirectFail[R_, p_, phi_] := AnyTrue[opp[p], Function[pr, AnyTrue[Tuples[phi, 2],
     Function[ff, IntersectingQ[ball[R[[pr[[1]]]], ff[[1]]], ball[R[[pr[[2]]]], ff[[2]]]]]]]];
delta[R_, p_] := Min[Length[dis[R[[#[[1]]]], R[[#[[2]]]]]] & /@ opp[p]];
claims = Select[Tuples[{0, 1}, 3], Length[Union[#]] == 2 &];
res = Flatten[Table[Module[{phi = phiT[m, t], d = delta[R, p]},
     {m, undetStruct[R, p, phi], undetDirect[R, p, phi], d <= t,
      adjStructFail[R, p, phi], adjDirectFail[R, p, phi], d <= 2 t}],
    {m, 1, 3}, {R, Tuples[Tuples[{0, 1}, m], 3]}, {p, claims}, {t, 0, m}], 3];
{Length[res], Count[res, {_, a_, a_, a_, _, _, _}], Count[res, {_, _, _, _, a_, a_, a_}]}
(* expected: {13536, 13536, 13536} *)
```

A.2 General seeded batch (300 models, seed 20261013). Proposition 1, structural against direct.

```mathematica
SeedRandom[20261013, Method -> "MersenneTwister"];
dis[r_, s_] := Flatten[Position[MapThread[Unequal, {r, s}], True]];
ballK[r_, F_, ks_] := Tuples[Table[If[MemberQ[F, g], Range[0, ks[[g]] - 1], {r[[g]]}], {g, Length[r]}]];
act[g_, r_, ks_] := Mod[r + g, ks];
orbit[u_, grp_, ks_] := Union[act[#, u, ks] & /@ grp];
downClose[gens_] := Union[Flatten[Subsets /@ gens, 1]];
makeModel[] := Module[{m, ks, nh, p, Y, J, S, grpType, grp, phi, gens},
  m = RandomInteger[{1, 4}]; ks = RandomChoice[{2, 3}, m]; nh = RandomInteger[{3, 4}];
  p = RandomSample[Join[{0, 1}, RandomChoice[{0, 1}, nh - 2]]];
  Y = Tuples[Range[0, # - 1] & /@ ks];
  J = Table[RandomSample[Y, Min[Length[Y], RandomInteger[{1, 3}]]], {nh}];
  grpType = RandomChoice[{"identity", "diagonal", "product"}];
  S = RandomSample[Range[m], RandomInteger[{1, m}]];
  grp = Switch[grpType, "identity", {ConstantArray[0, m]},
    "diagonal", Union[Table[Table[If[MemberQ[S, g], s, 0], {g, m}], {s, 0, LCM @@ ks[[S]] - 1}]],
    "product", Tuples[Table[If[MemberQ[S, g], Range[0, ks[[g]] - 1], {0}], {g, m}]]];
  gens = Table[RandomSample[Range[m], RandomInteger[{0, m}]], {RandomInteger[{1, 3}]}];
  phi = downClose[gens];
  <|"ks" -> ks, "p" -> p, "J" -> J, "grp" -> grp, "phi" -> phi|>];
check[M_] := Module[{ks = M["ks"], p = M["p"], J = M["J"], grp = M["grp"], phi = M["phi"], nh, opp, oppH},
  nh = Length[p];
  opp = Select[Tuples[Range[nh], 2], p[[#[[1]]]] != p[[#[[2]]]] &];
  oppH[h0_] := Union @@ J[[Select[Range[nh], p[[#]] != p[[h0]] &]]];
  {AnyTrue[opp, Function[pr, AnyTrue[Tuples[{J[[pr[[1]]]], J[[pr[[2]]]], grp}],
       Function[x, With[{d = dis[x[[1]], act[x[[3]], x[[2]], ks]]}, AnyTrue[phi, SubsetQ[#, d] &]]]]]],
   AnyTrue[Range[nh], Function[h0, With[{oh = oppH[h0]}, AnyTrue[J[[h0]], Function[r0,
        AnyTrue[phi, Function[F, AnyTrue[ballK[r0, F, ks], IntersectingQ[orbit[#, grp, ks], oh] &]]]]]]]]}];
res = check /@ Table[makeModel[], {300}];
Count[res, {a_, a_}]   (* expected: 300 *)
```

A.3 Separated seeded batch (300 models, seed 20261014) and the benchmark of Section 7; Proposition 1 and Theorem 1, structural against direct. Transformations are per-coordinate permutation tables.

```mathematica
SeedRandom[20261014, Method -> "MersenneTwister"];
dis[r_, s_] := Flatten[Position[MapThread[Unequal, {r, s}], True]];
ballK[r_, F_, ks_] := Tuples[Table[If[MemberQ[F, g], Range[0, ks[[g]] - 1], {r[[g]]}], {g, Length[r]}]];
act[g_, r_] := MapThread[#1[[#2 + 1]] &, {g, r}];
orbit[u_, grp_] := Union[act[#, u] & /@ grp];
downClose[gens_] := Union[Flatten[Subsets /@ gens, 1]];
idPerm[k_] := Range[0, k - 1]; cyc[k_, s_] := Mod[Range[0, k - 1] + s, k];
check[ks_, p_, J_, grp_, phi_] := Module[{nh = Length[p], opp, oppH},
  opp = Select[Tuples[Range[nh], 2], p[[#[[1]]]] != p[[#[[2]]]] &];
  oppH[h0_] := Union @@ J[[Select[Range[nh], p[[#]] != p[[h0]] &]]];
  {AnyTrue[opp, Function[pr, AnyTrue[Tuples[{J[[pr[[1]]]], J[[pr[[2]]]], grp}],
       Function[x, With[{d = dis[x[[1]], act[x[[3]], x[[2]]]]}, AnyTrue[phi, SubsetQ[#, d] &]]]]]],
   AnyTrue[Range[nh], Function[h0, With[{oh = oppH[h0]}, AnyTrue[J[[h0]], Function[r0,
        AnyTrue[phi, Function[F, AnyTrue[ballK[r0, F, ks], IntersectingQ[orbit[#, grp], oh] &]]]]]]]],
   AnyTrue[opp, Function[pr, AnyTrue[Tuples[{J[[pr[[1]]]], J[[pr[[2]]]], grp, phi, phi}],
       Function[x, SubsetQ[Union[x[[4]], x[[5]]], dis[x[[1]], act[x[[3]], x[[2]]]]]]]]],
   AnyTrue[opp, Function[pr, AnyTrue[Tuples[{J[[pr[[1]]]], J[[pr[[2]]]], phi, phi}],
       Function[x, IntersectingQ[ballK[x[[1]], x[[3]], ks],
         Union @@ (orbit[#, grp] & /@ ballK[x[[2]], x[[4]], ks])]]]]]}];
sep = Table[Module[{m = RandomInteger[{3, 5}], ks, nh, p, Y, J, S, grp, phi},
    ks = RandomChoice[{2, 3}, m]; nh = RandomInteger[{2, 4}];
    p = RandomSample[Join[{0, 1}, RandomChoice[{0, 1}, nh - 2]]];
    Y = Tuples[Range[0, # - 1] & /@ ks];
    J = Table[RandomSample[Y, RandomInteger[{1, 2}]], {nh}];
    S = RandomSample[Range[m], RandomInteger[{0, 1}]];
    grp = Tuples[Table[If[MemberQ[S, g], Table[cyc[ks[[g]], s], {s, 0, ks[[g]] - 1}], {idPerm[ks[[g]]]}], {g, m}]];
    phi = downClose[Table[RandomSample[Range[m], RandomInteger[{0, 2}]], {RandomInteger[{1, 2}]}]];
    check[ks, p, J, grp, phi]], {300}];
H = Tuples[{0, 1}, 4]; pB = (#[[1]] #[[3]]) & /@ H;
enc[a_, b_] := 2 a + b; swap = {0, 2, 1, 3};
phiT[m_, t_] := Select[Subsets[Range[m]], Length[#] <= t &];
sixJ = ({Join[Table[enc[#[[1]], #[[2]]], 3], Table[enc[#[[3]], #[[4]]], 3]]} &) /@ H;
tri[v_] := 21 v; twoJ = ({{tri[enc[#[[1]], #[[2]]]], tri[enc[#[[3]], #[[4]]]]}} &) /@ H;
bench = Join[
   Table[{"six domains, checked", t, check[Table[4, 6], pB, sixJ, {Table[idPerm[4], 6]}, phiT[6, t]]}, {t, 0, 3}],
   Table[{"shared control, checked", t, check[{64, 64}, pB, twoJ, {{idPerm[64], idPerm[64]}}, phiT[2, t]]}, {t, 0, 1}],
   {{"six domains, unbound", 0, check[Table[4, 6], pB, sixJ, Tuples[Table[{idPerm[4], swap}, 6]], phiT[6, 0]]}}];
{Count[sep, {a_, a_, b_, b_}], bench}
(* expected: 300; benchmark rows give {undetected, undetected, adj-fail, adj-fail}:
   six checked t=0,1 all False; t=2 {False,False,True,True}; t=3 all True;
   shared t=0 all False, t=1 all True; unbound t=0 all True *)
```

A.4 Two-sided analysis of Section 5.4 (Table 1). The first block covers the three arrangements without fault tolerance; the second covers the Shamir arrangement, including the direct check under one arbitrary failure.

```mathematica
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
```

```mathematica
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
```

