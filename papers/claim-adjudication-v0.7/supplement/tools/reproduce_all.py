#!/usr/bin/env python3
"""Run the historical checks and the four later finite checks."""
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if sys.flags.optimize or os.environ.get('PYTHONOPTIMIZE'):
        raise ValueError('Assertions must be enabled')
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output.exists() or output.is_relative_to(root):
        raise ValueError('Choose a new output directory outside the supplement')
    output.mkdir(parents=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([sys.executable, '-B', str(root/'tools/reproduce.py'),
                    '--output', str(output/'historical')], check=True, env=env)
    results = {}
    for name, filename in [('coalition-concealment','check_coalition_concealment.py'),
                           ('ledger-projection','replay_ledger.py'),
                           ('search-capture','search_capture.py'),
                           ('exhaustive-small-groups','exhaustive_small_groups.py')]:
        done = subprocess.run([sys.executable, '-B', str(root/'code'/filename)],
                              capture_output=True, check=True, timeout=180, env=env)
        (output/(name+'.json')).write_bytes(done.stdout)
        (output/(name+'.stderr.txt')).write_bytes(done.stderr)
        actual = json.loads(done.stdout)
        expected = json.loads((root/'expected'/(name+'.json')).read_text())
        omitted = ['python'] if name == 'exhaustive-small-groups' else []
        for field in omitted:
            actual.pop(field, None); expected.pop(field, None)
        if actual != expected:
            raise ValueError('Expected JSON mismatch: '+name)
        results[name] = dict(equal=True, omitted_fields=omitted,
                            output_sha256=hashlib.sha256(done.stdout).hexdigest())
    summary = dict(status='PASS', additional_checks=results,
                   historical_summary='historical/SUMMARY.json',
                   scope='Supplied Python implementations and retained records; no native engine or original file experiment rerun.')
    (output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__ == '__main__':
    main()
