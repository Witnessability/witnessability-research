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
