#!/usr/bin/env python3
"""Finite model checks for Witnessability manuscript v0.3.

Python standard library only. The direct checker enumerates admissible records.
The structural checker implements the proved separation criterion. Agreement
is finite consistency evidence, not a proof assistant or independent review.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
from pathlib import Path
import argparse
import hashlib
import json
import random
import time


@dataclass(frozen=True)
class Model:
    alphabets: tuple[int, ...]
    truths: tuple[int, ...]
    supports: tuple[tuple[tuple[int, ...], ...], ...]
    group: tuple[tuple[tuple[int, ...], ...], ...]
    faults: tuple[frozenset[int], ...]


def identity(alphabets):
    return tuple(tuple(range(k)) for k in alphabets)


def apply_action(action, record):
    return tuple(mapping[value] for mapping, value in zip(action, record))


def inverse_action(action):
    result = []
    for mapping in action:
        inverse = [0] * len(mapping)
        for i, j in enumerate(mapping):
            inverse[j] = i
        result.append(tuple(inverse))
    return tuple(result)


def canonical(model, record):
    return min(apply_action(action, record) for action in model.group)


def subsets(values):
    values = tuple(values)
    return [frozenset(c) for size in range(len(values) + 1)
            for c in combinations(values, size)]


def budget_faults(m, t):
    return tuple(s for s in subsets(range(m)) if len(s) <= t)


def validate(model, check_closure=True):
    m = len(model.alphabets)
    assert m > 0 and all(k > 0 for k in model.alphabets)
    assert len(model.truths) == len(model.supports) > 0
    assert set(model.truths) <= {0, 1}
    for support in model.supports:
        assert support
        for record in support:
            assert len(record) == m
            assert all(0 <= v < k for v, k in zip(record, model.alphabets))
    actions = set(model.group)
    assert identity(model.alphabets) in actions
    for action in actions:
        assert len(action) == m
        assert all(tuple(sorted(mapping)) == tuple(range(k))
                   for mapping, k in zip(action, model.alphabets))
        assert inverse_action(action) in actions
    if check_closure:
        for a in actions:
            for b in actions:
                composed = tuple(tuple(x[y[i]] for i in range(len(x)))
                                 for x, y in zip(a, b))
                assert composed in actions
    assert frozenset() in model.faults
    family = set(model.faults)
    for fault in family:
        assert fault <= set(range(m))
        assert all(s in family for s in subsets(fault))


def corrupted_records(model, honest_record, fault):
    choices = [range(k) if g in fault else (honest_record[g],)
               for g, k in enumerate(model.alphabets)]
    return product(*choices)


def direct_check(model):
    """Enumerate possible observations and their compatible histories."""
    labels = {}
    for history, (truth, support) in enumerate(zip(model.truths, model.supports)):
        for honest in support:
            for fault in model.faults:
                for raw in corrupted_records(model, honest, fault):
                    observation = canonical(model, raw)
                    labels.setdefault(observation, {}).setdefault(truth, set()).add(history)
    ambiguous = [record for record, label in labels.items() if len(label) > 1]
    counts = {"false": 0, "true": 0, "unresolved": len(ambiguous)}
    for label in labels.values():
        if len(label) == 1:
            counts["true" if 1 in label else "false"] += 1
    return {
        "exact": not ambiguous,
        "possible_observations": len(labels),
        "record_verdict_counts": counts,
        "labels": labels,
    }


def structural_check(model, certificate=False):
    """Test all opposite-claim supports, actions, and two failure sets."""
    cover_witnesses = {}
    for f0 in model.faults:
        for f1 in model.faults:
            cover_witnesses.setdefault(f0 | f1, (f0, f1))
    for h0, truth0 in enumerate(model.truths):
        if truth0 != 0:
            continue
        for h1, truth1 in enumerate(model.truths):
            if truth1 != 1:
                continue
            for r0 in model.supports[h0]:
                for r1 in model.supports[h1]:
                    for action in model.group:
                        transformed = apply_action(action, r1)
                        differences = frozenset(g for g, (a, b)
                                                in enumerate(zip(r0, transformed)) if a != b)
                        for cover, (f0, f1) in cover_witnesses.items():
                            if differences <= cover:
                                result = {"exact": False}
                                if certificate:
                                    raw0 = tuple(r0[g] if g not in f0 else transformed[g]
                                                 for g in range(len(r0)))
                                    raw1 = apply_action(inverse_action(action), raw0)
                                    assert all(raw0[g] == r0[g] for g in range(len(r0)) if g not in f0)
                                    assert all(raw1[g] == r1[g] for g in range(len(r1)) if g not in f1)
                                    assert canonical(model, raw0) == canonical(model, raw1)
                                    result["obstruction"] = {
                                        "history_false_index": h0, "history_true_index": h1,
                                        "honest_false_record": r0, "honest_true_record": r1,
                                        "action": action, "differing_domains": sorted(differences),
                                        "false_history_faults": sorted(f0),
                                        "true_history_faults": sorted(f1),
                                        "false_history_raw_record": raw0,
                                        "true_history_raw_record": raw1,
                                        "shared_observation": canonical(model, raw0),
                                    }
                                return result
    return {"exact": True}


def separation_margin(model):
    distances = [sum(a != b for a, b in zip(r0, apply_action(action, r1)))
                 for h0 in range(len(model.truths)) if model.truths[h0] == 0
                 for h1 in range(len(model.truths)) if model.truths[h1] == 1
                 for r0 in model.supports[h0] for r1 in model.supports[h1]
                 for action in model.group]
    return min(distances) if distances else None


def summary(model):
    validate(model)
    direct = direct_check(model)
    structural = structural_check(model, certificate=True)
    assert direct["exact"] == structural["exact"]
    return {
        "history_count": len(model.truths), "domain_count": len(model.alphabets),
        "group_size": len(model.group), "fault_sets": [sorted(f) for f in model.faults],
        "exact": structural["exact"], "separation_margin": separation_margin(model),
        "possible_observations": direct["possible_observations"],
        "record_verdict_counts": direct["record_verdict_counts"],
        **({"obstruction": structural["obstruction"]} if "obstruction" in structural else {}),
    }


def pair_permutation_group(m, unbound):
    local_identity = (0, 1, 2, 3)
    local_swap = (0, 2, 1, 3)
    if not unbound:
        return (tuple(local_identity for _ in range(m)),)
    return tuple(product((local_identity, local_swap), repeat=m))


def transaction_model(copies=1, unbound=False, shared_domains=False, t=0):
    histories = tuple(product((0, 1), repeat=4))  # u_A, u_B, x_A, x_B
    truths = tuple(u_a & x_a for u_a, u_b, x_a, x_b in histories)
    if shared_domains:
        assert not unbound
        k = 4 ** copies
        alphabets = (k, k)
        def repeated_pair_code(a, b):
            pair = 2 * a + b
            return sum(pair * (4 ** i) for i in range(copies))
        records = tuple((repeated_pair_code(u_a, u_b), repeated_pair_code(x_a, x_b))
                        for u_a, u_b, x_a, x_b in histories)
        group = (identity(alphabets),)
    else:
        m = 2 * copies
        alphabets = (4,) * m
        records = tuple((2 * u_a + u_b,) * copies + (2 * x_a + x_b,) * copies
                        for u_a, u_b, x_a, x_b in histories)
        group = pair_permutation_group(m, unbound)
    return Model(alphabets, truths, tuple((record,) for record in records),
                 group, budget_faults(len(alphabets), t)), histories


def transaction_examples():
    configurations = {
        "bound_two_domains_t0": (1, False, False, 0),
        "bound_two_domains_t1": (1, False, False, 1),
        "bound_six_domains_t1": (3, False, False, 1),
        "bound_six_reports_two_domains_t1": (3, False, True, 1),
        "unbound_two_domains_t0": (1, True, False, 0),
        "unbound_six_domains_t0": (3, True, False, 0),
        "unbound_six_domains_t1": (3, True, False, 1),
    }
    results = {}
    for name, args in configurations.items():
        model, histories = transaction_model(*args)
        results[name] = summary(model)
        results[name]["histories"] = histories
    bound, _ = transaction_model()
    unbound, _ = transaction_model(unbound=True)
    result = direct_check(unbound)
    decisive_histories = sum(
        len(result["labels"][canonical(unbound, support[0])]) == 1
        for support in unbound.supports)
    results["unbound_two_domains_t0"]["decisive_histories"] = decisive_histories
    # Explicit same bag, different transaction binding.
    false_h = (1, 0, 0, 1)
    true_h = (1, 0, 1, 0)
    assert (false_h[0] & false_h[2]) == 0 and (true_h[0] & true_h[2]) == 1
    raw_false = (2 * false_h[0] + false_h[1], 2 * false_h[2] + false_h[3])
    raw_true = (2 * true_h[0] + true_h[1], 2 * true_h[2] + true_h[3])
    assert canonical(unbound, raw_false) == canonical(unbound, raw_true)
    results["explicit_binding_obstruction"] = {
        "false_history": false_h, "true_history": true_h,
        "false_raw_record": raw_false, "true_raw_record": raw_true,
        "shared_observation": canonical(unbound, raw_false),
    }
    assert results["bound_two_domains_t0"]["exact"]
    assert not results["bound_two_domains_t1"]["exact"]
    assert results["bound_six_domains_t1"]["exact"]
    assert not results["bound_six_reports_two_domains_t1"]["exact"]
    assert not results["unbound_six_domains_t0"]["exact"]
    assert results["unbound_two_domains_t0"]["possible_observations"] == 9
    assert decisive_histories == 8
    return results


def exhaustive_binary_checks():
    counts = {}
    for m in range(1, 4):
        count = 0
        alphabets = (2,) * m
        group = (identity(alphabets),)
        for flat in product((0, 1), repeat=3 * m):
            supports = tuple((tuple(flat[h * m:(h + 1) * m]),) for h in range(3))
            for truths in product((0, 1), repeat=3):
                if len(set(truths)) == 1:
                    continue
                for t in range(m + 1):
                    model = Model(alphabets, truths, supports, group, budget_faults(m, t))
                    assert direct_check(model)["exact"] == structural_check(model)["exact"]
                    assert structural_check(model)["exact"] == (separation_margin(model) > 2 * t)
                    count += 1
        counts[str(m)] = count
    return counts


def randomized_checks(n=300, seed=20261013):
    rng = random.Random(seed)
    for _ in range(n):
        m = rng.randint(1, 4)
        k = rng.choice((2, 3))
        alphabets = (k,) * m
        records = tuple(product(range(k), repeat=m))
        supports = tuple(tuple(rng.sample(records, rng.randint(1, min(3, len(records)))))
                         for _ in range(4))
        truths = (0, 0, 1, 1)
        kind = rng.randint(0, 2)
        if kind == 0:
            group = (identity(alphabets),)
        elif kind == 1:
            group = tuple(tuple(tuple((x + a) % k for x in range(k)) for _ in range(m))
                          for a in range(k))
        else:
            group = tuple(tuple(tuple((x + a) % k for x in range(k)) for a in shifts)
                          for shifts in product(range(k), repeat=m))
        maximal = [frozenset(g for g in range(m) if rng.getrandbits(1)) for _ in range(2)]
        family = set().union(*(set(subsets(f)) for f in maximal))
        faults = tuple(sorted(family, key=lambda f: (len(f), tuple(sorted(f)))))
        model = Model(alphabets, truths, supports, group, faults)
        validate(model)
        direct = direct_check(model)
        structural = structural_check(model, certificate=True)
        assert direct["exact"] == structural["exact"]
        if not structural["exact"]:
            obs = tuple(structural["obstruction"]["shared_observation"])
            assert set(direct["labels"][obs]) == {0, 1}
    return {"configurations": n, "seed": seed, "status": "PASS"}


def targeted_checks():
    alphabets = (2, 2)
    correlated = Model(alphabets, (0, 1), (((0, 0), (1, 1)), ((0, 1), (1, 0))),
                       (identity(alphabets),), budget_faults(2, 0))
    all_records = tuple(product((0, 1), repeat=2))
    cartesian = Model(alphabets, (0, 1), (all_records, all_records),
                      (identity(alphabets),), budget_faults(2, 0))
    protected = Model((2, 2, 2), (0, 1), (((0, 0, 0),), ((0, 0, 1),)),
                      (identity((2, 2, 2)),),
                      (frozenset(), frozenset({0}), frozenset({1})))
    results = {"correlated_honest_support": summary(correlated),
               "cartesian_overapproximation": summary(cartesian),
               "protected_domain_asymmetric_family": summary(protected)}
    assert results["correlated_honest_support"]["exact"]
    assert not results["cartesian_overapproximation"]["exact"]
    assert results["protected_domain_asymmetric_family"]["exact"]
    assert results["protected_domain_asymmetric_family"]["separation_margin"] == 1
    return results


def project_model(model, selected, t):
    selected = tuple(sorted(selected))
    alphabets = tuple(model.alphabets[g] for g in selected)
    supports = tuple(tuple(sorted(set(tuple(r[g] for g in selected) for r in support)))
                     for support in model.supports)
    group = tuple(sorted(set(tuple(action[g] for g in selected) for action in model.group)))
    return Model(alphabets, model.truths, supports, group, budget_faults(len(selected), t))


def portfolio_checks():
    results = {}
    for unbound in (False, True):
        full, _ = transaction_model(copies=3, unbound=unbound)
        for t in (0, 1):
            feasible = []
            checked = 0
            for selected in subsets(range(6)):
                if not selected:  # Nonconstant claim cannot be decided with no observation.
                    continue
                model = project_model(full, selected, t)
                validate(model, check_closure=False)
                exact = structural_check(model)["exact"]
                # Separately evaluate the multicover inequalities on full supports.
                multicover = all(
                    sum(r0[g] != apply_action(action, r1)[g] for g in selected) >= 2 * t + 1
                    for h0 in range(16) if full.truths[h0] == 0
                    for h1 in range(16) if full.truths[h1] == 1
                    for r0 in full.supports[h0] for r1 in full.supports[h1]
                    for action in full.group)
                assert exact == multicover
                assert exact == direct_check(model)["exact"]
                checked += 1
                if exact:
                    feasible.append(tuple(sorted(selected)))
            minimum = min(map(len, feasible)) if feasible else None
            optimal = [s for s in feasible if len(s) == minimum]
            results[("unbound" if unbound else "bound") + f"_t{t}"] = {
                "portfolios_checked": checked, "minimum_unit_cost": minimum,
                "optimal_portfolios": optimal,
            }
    assert results["bound_t0"]["minimum_unit_cost"] == 2
    assert len(results["bound_t0"]["optimal_portfolios"]) == 9
    assert results["bound_t1"]["minimum_unit_cost"] == 6
    assert results["unbound_t0"]["minimum_unit_cost"] is None
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("evidence"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    exhaustive = exhaustive_binary_checks()
    random_results = randomized_checks()
    results = {
        "manuscript_version": "0.3",
        "method": "structural criterion versus exhaustive record enumeration",
        "exhaustive_binary_configurations_by_domains": exhaustive,
        "exhaustive_binary_configurations_total": sum(exhaustive.values()),
        "randomized": random_results,
        "targeted": targeted_checks(),
        "transactions": transaction_examples(),
        "portfolios": portfolio_checks(),
        "status": "PASS",
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "assurance_boundary": "Finite executed checks on one host; not independent review or a machine-checked proof.",
    }
    (args.output / "verification_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: results[k] for k in (
        "status", "exhaustive_binary_configurations_total", "randomized", "elapsed_seconds")}, indent=2))
    for name, value in results["transactions"].items():
        if "exact" in value:
            print(name, "exact=", value["exact"], "delta=", value["separation_margin"],
                  "records=", value["possible_observations"])


if __name__ == "__main__":
    main()
