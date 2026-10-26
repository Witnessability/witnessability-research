#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Bounded differential harness; see PROTOCOL.md for exact scope and counts."""
import argparse
from collections import Counter
import hashlib
import importlib.util
from itertools import combinations, product
import json
from pathlib import Path
import platform
import signal
import sys
import time


COUNTS = {'legacy-2x2': 1125, 'singleton-3x3': 77824, 'joint-catalog-3x3': 32832}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def families(domains):
    subsets = tuple(frozenset(x) for n in range(len(domains) + 1)
                    for x in combinations(domains, n))
    result = []
    for mask in range(1 << len(subsets)):
        chosen = {s for i, s in enumerate(subsets) if mask & (1 << i)}
        if frozenset() not in chosen:
            continue
        if all(s - {d} in chosen for s in chosen for d in s):
            result.append([sorted(s) for s in subsets if s in chosen])
    expected = {2: 5, 3: 19}[len(domains)]
    if len(result) != expected:
        raise RuntimeError('fault-family enumeration count mismatch')
    return result


def raw_model(histories, domains, joint, truth, faults, name='bounded-r02-06'):
    return {'name': name, 'claim': 'binary claim on labelled histories',
            'binding': 'identity', 'histories': list(histories),
            'truth': dict(zip(histories, truth)), 'domains': list(domains),
            'alphabets': [['0', '1'] for _ in domains],
            'joint': {h: [list(r) for r in s] for h, s in zip(histories, joint)},
            'faults': faults}


def model_class(name):
    dimension = 2 if name == 'legacy-2x2' else 3
    domains = tuple('abc'[:dimension])
    records = tuple(product(('0', '1'), repeat=dimension))
    histories = ('f', 't') if dimension == 2 else ('h0', 'h1', 'h2')
    truths = ((False, True),) if dimension == 2 else tuple(product((False, True), repeat=3))
    if name == 'legacy-2x2':
        catalog = tuple(s for n in range(1, 5) for s in combinations(records, n))
    elif name == 'singleton-3x3':
        catalog = tuple((r,) for r in records)
    elif name == 'joint-catalog-3x3':
        pairs = []
        for r in records:
            opposite = tuple('1' if x == '0' else '0' for x in r)
            if r < opposite:
                pairs.append((r, opposite))
        catalog = tuple(pairs) + tuple(tuple(r for r in records if sum(map(int, r)) % 2 == p)
                                       for p in (0, 1))
        if len(catalog) != 6 or len(set(catalog)) != 6:
            raise RuntimeError('joint catalog mismatch')
    else:
        raise ValueError(name)
    all_fault_families = families(domains)
    for joint in product(catalog, repeat=len(histories)):
        for truth in truths:
            for fault in all_fault_families:
                yield raw_model(histories, domains, joint, truth, fault)


class Comparison:
    def __init__(self, source, reference):
        self.source = source
        self.reference = reference
        sys.path.insert(0, str(source / 'standalone/src'))
        self.old = load_module('_original_finite_r0206', source / 'src/witnessability_research/finite.py')
        self.third = load_module('_third_finite_r0206', reference / 'third_checker.py')
        from witnessability_checker import analysis, common, context, verify
        self.analysis, self.common, self.context, self.verify = analysis, common, context, verify
        self.policy = {'id': 'declared-model', 'version': '1', 'acknowledged_assumptions': True}

    def compare(self, raw):
        old = self.old.FiniteModel.from_dict(raw)
        document = {'schema_version': self.context.SCHEMA_VERSION,
                    'semantics_version': self.context.SEMANTICS_VERSION, 'model': raw}
        model = self.context.validate_document(document, self.common.Budget())
        relation = self.third.compile_model(raw)
        # Cache outputs of the actual original exposure routine; do not copy its algorithm.
        exposures = {h: self.old.enumerate_exposure(old, h) for h in old.histories}
        raw_capability = all(not (exposures[h] & exposures[k]) for h in old.histories
                             for k in old.histories if old.truth[h] != old.truth[k])
        criterion = self.analysis.check_capability(model, self.common.Budget())
        third_cap = relation.check_capability()
        if not (raw_capability == criterion['capability'] == third_cap['capability']):
            raise RuntimeError('capability disagreement')
        records = tuple(product(*raw['alphabets']))
        outside = ('__outside__',) + records[0][1:]
        outputs = []
        for record in records + (outside,):
            compatible = [h for h in old.histories if record in exposures[h]]
            direct = {'verdict': self.old._judgment(old, compatible),
                      'compatible_histories': compatible}
            actual = self.analysis.evaluate_record(model, record, self.common.Budget())
            other = relation.evaluate_record(record)
            if not (direct == actual == other):
                raise RuntimeError('record disagreement: ' + canonical({'record': record,
                                   'direct': direct, 'criterion': actual, 'third': other}))
            outputs.append({'record': list(record), **actual})
        certificates = 0
        if not raw_capability:
            for collision in (criterion['collision'], third_cap['collision']):
                record = collision['record']
                witnesses = [{'history': h, 'honest': a, 'fault': f} for h, a, f in
                             zip(collision['histories'], collision['honest_records'], collision['faults'])]
                expected = self.context.make_pins(document, model, self.policy, record, self.common.Budget())
                certificate = {'schema_version': self.context.SCHEMA_VERSION,
                               'semantics_version': self.context.SEMANTICS_VERSION,
                               'pins': expected, 'record': list(record), 'witnesses': witnesses}
                legacy_pins = self.old.pins(old, record)
                legacy_certificate = {'schema': 'finite-ambiguity-v1', 'pins': legacy_pins,
                                      'record': list(record), 'witnesses': witnesses}
                if not self.old.verify_certificate(old, record, legacy_certificate, expected_pins=legacy_pins):
                    raise RuntimeError('legacy rejected supplied collision')
                if not self.verify.verify_ambiguity(model, record, certificate,
                                                   expected_pins=expected, budget=self.common.Budget()):
                    raise RuntimeError('component rejected supplied collision')
                if not self.third.verify_ambiguity(raw, record, witnesses)['valid']:
                    raise RuntimeError('third checker rejected supplied collision')
                certificates += 1
        return {'records': outputs, 'capability': raw_capability,
                'certificate_objects_cross_verified': certificates,
                'witness_verifications': certificates * 3}


def run(args):
    started = time.monotonic()
    model_digest, result_digest = hashlib.sha256(), hashlib.sha256()
    output = {'schema': 'r0206-bounded-consistency-run-1', 'status': 'running',
              'python': platform.python_version(), 'implementation': platform.python_implementation(),
              'command': sys.argv, 'pilot_prefix_per_class': args.limit,
              'wall_seconds_limit': args.wall_seconds, 'classes': [],
              'third_checker_independence': 'separately authored internal, source-blind; contract disclosed algorithms',
              'claim_scope': 'bounded mathematical consistency, not complete external contract or real capture'}
    current = None
    active = None
    count = 0
    stats = Counter()
    timer_installed = False
    previous_handler = None
    try:
        if not hasattr(signal, 'setitimer'):
            raise RuntimeError('this bounded runner requires POSIX setitimer')
        def deadline(signum, frame):
            raise TimeoutError('declared wall budget exhausted')
        previous_handler = signal.signal(signal.SIGALRM, deadline)
        signal.setitimer(signal.ITIMER_REAL, args.wall_seconds)
        timer_installed = True
        source_files = [Path(__file__), Path(__file__).with_name('PROTOCOL.md'),
                        args.reference / 'third_checker.py',
                        args.reference / 'PROVENANCE.md',
                        args.reference / 'DERIVATION.md',
                        args.source / 'src/witnessability_research/finite.py']
        source_files += sorted((args.source / 'standalone/src/witnessability_checker').glob('*.py'))
        output['source_files'] = [{'path': str(p.resolve()), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                                  for p in source_files]
        comparator = Comparison(args.source.resolve(), args.reference.resolve())
        for name in args.classes:
            count = 0
            stats = Counter()
            class_start = time.monotonic()
            active = name
            index = -1  # Deadline can fire while constructing the first generator item.
            for index, current in enumerate(model_class(name)):
                if args.limit and index >= args.limit:
                    break
                if time.monotonic() - started > args.wall_seconds:
                    raise TimeoutError('declared wall budget exhausted')
                if sum(x['models'] for x in output['classes']) + count >= 200000:
                    raise TimeoutError('model-count budget exhausted')
                actual = comparator.compare(current)
                model_digest.update((canonical({'class': name, 'index': index, 'model': current}) + '\n').encode())
                result_digest.update((canonical({'class': name, 'index': index, 'result': actual}) + '\n').encode())
                stats['record_queries'] += len(actual['records'])
                stats['capability_true' if actual['capability'] else 'capability_false'] += 1
                stats['certificate_objects_cross_verified'] += actual['certificate_objects_cross_verified']
                stats['witness_verifications'] += actual['witness_verifications']
                for item in actual['records']:
                    stats['verdict_' + item['verdict']] += 1
                count += 1
                if count % 4096 == 0:
                    print(f'{name}: {count} models; elapsed {time.monotonic()-started:.1f}s', file=sys.stderr, flush=True)
            expected = min(COUNTS[name], args.limit) if args.limit else COUNTS[name]
            if count != expected:
                raise RuntimeError('model count mismatch')
            output['classes'].append({'id': name, 'models': count, 'full_class_size': COUNTS[name],
                                      'exhaustive_for_declared_class': count == COUNTS[name],
                                      'elapsed_seconds': time.monotonic() - class_start, **dict(stats)})
            active = None
        for item in output['source_files']:
            if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest() != item['sha256']:
                raise RuntimeError('source changed during execution: ' + item['path'])
        output['status'] = 'pilot_pass' if args.limit else 'pass'
    except Exception as exc:
        output['status'] = 'incomplete' if isinstance(exc, TimeoutError) else 'failed'
        output['error'] = f'{type(exc).__name__}: {exc}'
        output['current_model'] = current
        output['interrupted_streams_are_not_complete_class_evidence'] = True
        if active is not None:
            output['partial_class'] = {'id': active, 'completed_models': count,
                                       'current_zero_based_index': index,
                                       'full_class_size': COUNTS[active], **dict(stats)}
    finally:
        if timer_installed:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous_handler)
    output['elapsed_seconds'] = time.monotonic() - started
    output['model_stream_sha256'] = model_digest.hexdigest()
    output['result_stream_sha256'] = result_digest.hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: output[k] for k in ('status', 'elapsed_seconds', 'model_stream_sha256', 'result_stream_sha256')}, indent=2))
    return 0 if output['status'] in ('pass', 'pilot_pass') else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--classes', nargs='+', choices=tuple(COUNTS), default=list(COUNTS))
    parser.add_argument('--limit', type=int, default=0, help='pilot prefix per class; 0 means full declared class')
    parser.add_argument('--wall-seconds', type=float, default=900)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not 0 <= args.limit <= 200000 or not 0 < args.wall_seconds <= 900:
        parser.error('limit must be 0..200000; wall-seconds must be >0 and <=900')
    return run(args)


if __name__ == '__main__':
    raise SystemExit(main())
