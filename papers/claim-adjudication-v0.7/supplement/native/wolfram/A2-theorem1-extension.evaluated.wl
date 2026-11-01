(* NEW CODE written 2026-10-29 for this replay; not part of manuscript v0.5.
   Same seed and model generator as Appendix A.2, check extended with the two
   Theorem 1 adjudication checks (structural and direct), adapted from A.3 to
   the additive group action of A.2. *)
{$Version, AbsoluteTiming[(
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
check4[M_] := Module[{ks = M["ks"], p = M["p"], J = M["J"], grp = M["grp"], phi = M["phi"], nh, opp, oppH},
  nh = Length[p];
  opp = Select[Tuples[Range[nh], 2], p[[#[[1]]]] != p[[#[[2]]]] &];
  oppH[h0_] := Union @@ J[[Select[Range[nh], p[[#]] != p[[h0]] &]]];
  {AnyTrue[opp, Function[pr, AnyTrue[Tuples[{J[[pr[[1]]]], J[[pr[[2]]]], grp}],
       Function[x, With[{d = dis[x[[1]], act[x[[3]], x[[2]], ks]]}, AnyTrue[phi, SubsetQ[#, d] &]]]]]],
   AnyTrue[Range[nh], Function[h0, With[{oh = oppH[h0]}, AnyTrue[J[[h0]], Function[r0,
        AnyTrue[phi, Function[F, AnyTrue[ballK[r0, F, ks], IntersectingQ[orbit[#, grp, ks], oh] &]]]]]]]],
   AnyTrue[opp, Function[pr, AnyTrue[Tuples[{J[[pr[[1]]]], J[[pr[[2]]]], grp, phi, phi}],
       Function[x, SubsetQ[Union[x[[4]], x[[5]]], dis[x[[1]], act[x[[3]], x[[2]], ks]]]]]]],
   AnyTrue[opp, Function[pr, AnyTrue[Tuples[{J[[pr[[1]]]], J[[pr[[2]]]], phi, phi}],
       Function[x, IntersectingQ[ballK[x[[1]], x[[3]], ks],
         Union @@ (orbit[#, grp, ks] & /@ ballK[x[[2]], x[[4]], ks])]]]]]}];
models = Table[makeModel[], {300}];
res = check4 /@ models;
{Count[res, {a_, a_, _, _}], Count[res, {_, _, b_, b_}], Count[res, {a_, a_, b_, b_}], Counts[res], Hash[models, "SHA256", "HexString"]}
)]}
