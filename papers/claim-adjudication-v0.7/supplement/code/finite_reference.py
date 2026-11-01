"""Finite reference routines for direct and structural comparisons."""
import itertools, random
from fractions import Fraction

# ---------- generic model ----------
def compose(a, b):  # (a∘b)(x) = a(b(x)), coordinatewise perms as tuples of tuples
    return tuple(tuple(ag[bg[x]] for x in range(len(bg))) for ag, bg in zip(a, b))

def closure(gens, m, ks):
    ident = tuple(tuple(range(k)) for k in ks)
    G = {ident}
    frontier = [ident]
    while frontier:
        new = []
        for g in frontier:
            for s in gens:
                h = compose(s, g)
                if h not in G:
                    G.add(h); new.append(h)
        frontier = new
    return sorted(G)

def act(g, r):
    return tuple(g[i][r[i]] for i in range(len(r)))

def orbit_rep(u, G):
    return min(act(g, u) for g in G)

def D(r, s):
    return frozenset(i for i in range(len(r)) if r[i] != s[i])

def ball(r, F, ks):
    axes = [range(ks[g]) if g in F else [r[g]] for g in range(len(r))]
    return [tuple(x) for x in itertools.product(*axes)]

def down_close(gens):
    out = set()
    for S in gens:
        S = tuple(sorted(S))
        for n in range(len(S) + 1):
            for sub in itertools.combinations(S, n):
                out.add(frozenset(sub))
    return sorted(out, key=lambda f: (len(f), sorted(f)))

def structural_adj_fail(p, J, G, Phi):
    for h0 in J:
        for h1 in J:
            if p[h0] == 0 and p[h1] == 1:
                for r0 in J[h0]:
                    for r1 in J[h1]:
                        for g in G:
                            d = D(r0, act(g, r1))
                            for F0 in Phi:
                                for F1 in Phi:
                                    if d <= (F0 | F1):
                                        return True
    return False

def direct_adj_fail(p, J, G, Phi, ks):
    E = {}
    for h in J:
        E[h] = set()
        for r in J[h]:
            for F in Phi:
                for u in ball(r, F, ks):
                    E[h].add(orbit_rep(u, G))
    for h0 in J:
        for h1 in J:
            if p[h0] == 0 and p[h1] == 1 and E[h0] & E[h1]:
                return True
    return False

def structural_undetected(p, J, G, Phi):
    for h0 in J:
        for h1 in J:
            if p[h0] != p[h1]:
                for r0 in J[h0]:
                    for r1 in J[h1]:
                        for g in G:
                            d = D(r0, act(g, r1))
                            if any(d <= F for F in Phi):
                                return True
    return False

def direct_undetected(p, J, G, Phi, ks):
    honest_orbits = {}
    for h in J:
        honest_orbits[h] = {orbit_rep(r, G) for r in J[h]}
    for h0 in J:
        opp = set().union(*[honest_orbits[h] for h in J if p[h] != p[h0]])
        for r0 in J[h0]:
            for F in Phi:
                for u in ball(r0, F, ks):
                    if orbit_rep(u, G) in opp:
                        return True
    return False

def random_model(rng):
    m = rng.randint(1, 4)
    ks = [rng.choice([2, 3]) for _ in range(m)]
    Y = [tuple(x) for x in itertools.product(*[range(k) for k in ks])]
    nh = rng.randint(2, 4)
    p = [0, 1] + [rng.randint(0, 1) for _ in range(nh - 2)]
    rng.shuffle(p)
    J = {h: rng.sample(Y, min(len(Y), rng.randint(1, 3))) for h in range(nh)}
    gens = []
    for _ in range(rng.randint(0, 2)):
        g = []
        for k in ks:
            perm = list(range(k))
            if rng.random() < 0.6:
                rng.shuffle(perm)
            g.append(tuple(perm))
        gens.append(tuple(g))
    G = closure(gens, m, ks)
    Phi = down_close([rng.sample(range(m), rng.randint(0, m)) for _ in range(rng.randint(1, 2))])
    return ks, p, J, G, Phi

def run_random(n, seed):
    rng = random.Random(seed)
    agree_adj = agree_det = 0
    nontrivial_G = 0; setvalued = 0
    for _ in range(n):
        ks, p, J, G, Phi = random_model(rng)
        if len(G) > 1: nontrivial_G += 1
        if any(len(v) > 1 for v in J.values()): setvalued += 1
        a = structural_adj_fail(p, J, G, Phi); b = direct_adj_fail(p, J, G, Phi, ks)
        c = structural_undetected(p, J, G, Phi); d = direct_undetected(p, J, G, Phi, ks)
        agree_adj += (a == b); agree_det += (c == d)
    print(f"random models: n={n}, Theorem1 struct==direct: {agree_adj}, Prop1 struct==direct: {agree_det}, "
          f"nontrivial Gamma in {nontrivial_G}, set-valued J in {setvalued}")

# ---------- Section 7.2 counts ----------
def sec72():
    H = list(itertools.product([0, 1], repeat=4))
    p = {h: h[0] & h[2] for h in H}
    obs = {}
    for h in H:
        key = (h[0] + h[1], h[2] + h[3])
        obs.setdefault(key, set()).add(p[h])
    classes = {"FALSE": 0, "TRUE": 0, "UNRESOLVED": 0}
    decisive_hist = 0
    for key, vals in obs.items():
        label = "UNRESOLVED" if len(vals) == 2 else ("TRUE" if 1 in vals else "FALSE")
        classes[label] += 1
    for h in H:
        key = (h[0] + h[1], h[2] + h[3])
        if len(obs[key]) == 1: decisive_hist += 1
    print("7.2 unordered observations:", len(obs), classes, "decisive histories:", decisive_hist)

# ---------- Section 7.3 / Table 2 margins ----------
def margin(p, J, G):
    best = None
    for h0 in J:
        for h1 in J:
            if p[h0] == 0 and p[h1] == 1:
                for r0 in J[h0]:
                    for r1 in J[h1]:
                        for g in G:
                            d = len(D(r0, act(g, r1)))
                            best = d if best is None else min(best, d)
    return best

def sec73():
    H = list(itertools.product([0, 1], repeat=4))
    p = {h: h[0] & h[2] for h in H}
    six = {h: [((h[0], h[1]),) * 3 + ((h[2], h[3]),) * 3] for h in H}
    ident6 = [tuple(tuple(range(1)) for _ in range(6))]  # identity on 'abstract' alphabet, handled via equality
    # use generic D with identity only
    print("7.3 six-domain checked margin:", margin(p, six, [None]) if False else
          min(len(D(r0, r1)) for h0 in H for h1 in H if p[h0] == 0 and p[h1] == 1 for r0 in six[h0] for r1 in six[h1]))
    two = {h: [((h[0], h[1], h[0], h[1], h[0], h[1]), (h[2], h[3], h[2], h[3], h[2], h[3]))] for h in H}
    print("7.3 shared-control margin:",
          min(len(D(r0, r1)) for h0 in H for h1 in H if p[h0] == 0 and p[h1] == 1 for r0 in two[h0] for r1 in two[h1]))
    # unit-cost portfolio at t=0 and t=1 in six-domain model (identity binding)
    diffsets = {D(r0, r1) for h0 in H for h1 in H if p[h0] == 0 and p[h1] == 1 for r0 in six[h0] for r1 in six[h1]}
    best = {}
    for n in range(1, 7):
        for S in itertools.combinations(range(6), n):
            S = set(S)
            for t in (0, 1):
                if all(len(d & S) >= 2 * t + 1 for d in diffsets):
                    best.setdefault(t, []).append(S)
    for t in (0, 1):
        mn = min(len(S) for S in best[t])
        print(f"7.3 portfolio t={t}: min size {mn}, optimal count {sum(1 for S in best[t] if len(S) == mn)}")

# ---------- Table 1 ----------
def tv(records_by_h, f, weights=None):
    # uniform over listed (h-index) items
    c1, c0 = {}, {}
    n1 = n0 = 0
    for rec, val in records_by_h:
        if val == 1: c1[rec] = c1.get(rec, 0) + 1; n1 += 1
        else: c0[rec] = c0.get(rec, 0) + 1; n0 += 1
    keys = set(c1) | set(c0)
    return sum(abs(Fraction(c1.get(k, 0), n1) - Fraction(c0.get(k, 0), n0)) for k in keys) / 2

def table1():
    H = list(itertools.product([0, 1], repeat=6))  # uA uB xA xB m1 m2
    p = lambda h: h[0] & h[2]; s1 = lambda h: h[1]; s2 = lambda h: h[0]
    designs = {
        "bound": [lambda h: (h[0], h[1]), lambda h: (h[2], h[3])],
        "scoped": [lambda h: h[0], lambda h: h[2]],
        "xor": [lambda h: h[0] ^ h[4], lambda h: h[4], lambda h: h[2] ^ h[5], lambda h: h[5]],
    }
    for name, d in designs.items():
        m = len(d)
        decides = {}
        for n in range(1, m + 1):
            for C in itertools.combinations(range(m), n):
                groups = {}
                for h in H:
                    groups.setdefault(tuple(d[c](h) for c in C), set()).add(p(h))
                decides[C] = all(len(v) == 1 for v in groups.values())
        smallest = min(len(C) for C, v in decides.items() if v)
        # exact concealment from singletons (Definition 2): every observation compatible with both p values
        conc = []
        for c in range(m):
            groups = {}
            for h in H:
                groups.setdefault(d[c](h), set()).add(p(h))
            conc.append(all(len(v) == 2 for v in groups.values()))
        tvs = {c: (tv([(d[c](h), p(h)) for h in H], p), tv([(d[c](h), s1(h)) for h in H], s1), tv([(d[c](h), s2(h)) for h in H], s2)) for c in range(m)}
        # margin at identity binding, J(h) = all mask choices
        J = {}
        for h in H:
            J.setdefault(h[:4], []).append(tuple(d[c](h) for c in range(m)))
        mg = min(len(D(r0, r1)) for h0 in J for h1 in J if (h0[0] & h0[2]) == 0 and (h1[0] & h1[2]) == 1 for r0 in J[h0] for r1 in J[h1])
        print(f"Table1 {name}: domains={m} margin={mg} smallest deciding coalition={smallest} "
              f"exactly-concealed-from-singletons={conc} TV(p,s1,s2) per custodian={[tuple(str(x) for x in tvs[c]) for c in range(m)]}")
    # Shamir over GF(5), 4 custodians, threshold 2
    Hs = [(a, b, c, d, r1, r2) for a in (0, 1) for b in (0, 1) for c in (0, 1) for d in (0, 1) for r1 in range(5) for r2 in range(5)]
    share = lambda h, i: ((h[0] + h[4] * i) % 5, (h[2] + h[5] * i) % 5)
    rec = lambda h, C: tuple(share(h, i) for i in C)
    J = {}
    for h in Hs:
        J.setdefault(h[:4], []).append(rec(h, (1, 2, 3, 4)))
    mg = min(len(D(r0, r1)) for h0 in J for h1 in J if (h0[0] & h0[2]) == 0 and (h1[0] & h1[2]) == 1 for r0 in J[h0] for r1 in J[h1])
    ks = [25] * 4
    # encode shares as ints 0..24 for ball enumeration
    enc = lambda s: s[0] * 5 + s[1]
    Jn = {h: [tuple(enc(x) for x in r) for r in rs] for h, rs in J.items()}
    pS = {h: h[0] & h[2] for h in Jn}
    G = [tuple(tuple(range(25)) for _ in range(4))]
    Phi1 = down_close([[0], [1], [2], [3]])
    exact_t1 = not direct_adj_fail(pS, Jn, G, Phi1, ks)
    decide = {}
    for n in range(1, 5):
        for C in itertools.combinations((1, 2, 3, 4), n):
            groups = {}
            for h in Hs:
                groups.setdefault(rec(h, C), set()).add(h[0] & h[2])
            decide[C] = all(len(v) == 1 for v in groups.values())
    print(f"Table1 shamir: margin={mg} exact at t=1 (direct enumeration)={exact_t1} "
          f"smallest deciding={min(len(C) for C, v in decide.items() if v)} "
          f"#deciding coalitions size>=2={sum(1 for C, v in decide.items() if v and len(C) >= 2)} "
          f"single custodian TV(p)={tv([(share(h, 1), h[0] & h[2]) for h in Hs], None)}")
    # (4): k + 2t <= m
    print("Table1 shamir (4): k=2,t=1,m=4 ->", 2 + 2 <= 4)

# ---------- Section 5.2 / 7.5 anchor family ----------
def anchors():
    for n, k in [(2, 1), (1, 2), (3, 3), (2, 2), (4, 1)]:
        m = n + k
        r0 = tuple([0] * m); r1 = tuple([1] * n + [0] * k)
        flip = tuple((1, 0) for _ in range(m)); ident = tuple((0, 1) for _ in range(m))
        diag = [ident, flip]
        prod = closure([tuple((1, 0) if i == j else (0, 1) for i in range(m)) for j in range(m)], m, [2] * m)
        dm = min(len(D(r0, act(g, r1))) for g in diag); pm = min(len(D(r0, act(g, r1))) for g in prod)
        print(f"anchor n={n} k={k}: diagonal margin={dm} (min(n,k)={min(n, k)}), product margin={pm}, largest t={(dm - 1) // 2}")
    # 7.5 orbits under common flip
    m = 3; flip = tuple((1, 0) for _ in range(m)); ident = tuple((0, 1) for _ in range(m))
    orbs = {}
    for u in itertools.product((0, 1), repeat=3):
        orbs.setdefault(orbit_rep(u, [ident, flip]), set()).add(u)
    print("7.5 common-flip orbits:", sorted(orbs.values(), key=lambda s: min(s)))

# ---------- Section 9 boundary test ----------
def sec9():
    r0, r1 = (0, 0), (1, 1)
    Phi = [frozenset(), frozenset({0})]
    ks = [2, 2]
    # observations quotient by domain swap (NOT coordinatewise)
    swap_rep = lambda u: min(u, (u[1], u[0]))
    E0 = {swap_rep(u) for F in Phi for u in ball(r0, F, ks)}
    E1 = {swap_rep(u) for F in Phi for u in ball(r1, F, ks)}
    print("Sec 9: shared observations under domain swap:", E0 & E1,
          "| untransported D(r0,r1)=", set(D(r0, r1)), "covered by F0∪F1={0}?", D(r0, r1) <= frozenset({0}))

def config_count():
    print("7.4 config count:", [2 ** (3 * m) * 6 * (m + 1) for m in (1, 2, 3)], sum(2 ** (3 * m) * 6 * (m + 1) for m in (1, 2, 3)))

if __name__ == "__main__":
    sec72(); sec73(); table1(); anchors(); sec9(); config_count()
    run_random(1500, 20261101)
