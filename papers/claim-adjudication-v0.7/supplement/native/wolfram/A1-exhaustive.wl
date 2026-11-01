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
