# Exhaustive small-group family

There are exactly two histories with opposite truth values and two binary domain alphabets. The four raw records have 15 nonempty subsets; all 15 squared ordered pairs of honest supports are included. All five subgroups of the coordinatewise group C2 x C2 and all five nonempty downward-closed fault families on two domains are included. This gives 5,625 models.

The enumeration compares the structural criterion of Theorem 1 with direct intersections of corrupted observation orbits and Proposition 1 with direct reachability of honest opposite-claim orbits. It covers 4,500 models with nontrivial groups, 5,225 with at least one set-valued support and 2,250 with noncardinal fault families.

From the supplement directory, using Python 3 without optimization:
```sh
python3 -I -B code/exhaustive_small_groups.py > exhaustive-replay.json
```

Compare with expected/exhaustive-small-groups.json; the Python version field may differ. The recorded driver/source hashes refer to the exact supplied reader files. The finite reference routines and enumerating driver are supplied implementations, not an independent implementation or a proof. The reader copy replaces an introductory provenance assertion with a neutral description; the numerical routines are preserved.
