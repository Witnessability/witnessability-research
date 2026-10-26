#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Bounded CI checks, including an offline-built isolated installation.

Requires installed pip/setuptools/wheel. Build-tool bootstrap is separate from
this script. No dependency download, build isolation, or remote publication.
The 64-model prefix per declared class is a smoke test, not the full R02-06 run.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='new directory for commands, logs and results')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).resolve().parents[1]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
                       PIP_DISABLE_PIP_VERSION_CHECK='1',
                       SOURCE_DATE_EPOCH='1792960536')
    environment.pop('PYTHONPATH', None)
    records = []
    summary = {'schema': 'standalone-ci-checks-1', 'status': 'incomplete',
               'python': sys.version, 'source': str(source),
               'network_bootstrap_in_this_script': False,
               'bounded_prefix_per_class': 64, 'full_r0206_run': False}

    def run(name, command, cwd, pythonpath=None):
        env = dict(environment)
        if pythonpath is not None:
            env['PYTHONPATH'] = str(pythonpath)
        started = time.monotonic()
        timed_out = False
        try:
            proc = subprocess.run(list(map(str, command)), cwd=cwd, env=env,
                                  capture_output=True, timeout=120)
            stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout, stderr, code = exc.stdout or b'', exc.stderr or b'', None
        for stream in ['stdout', 'stderr']:
            (output/(name+'.'+stream)).write_bytes(stdout if stream == 'stdout' else stderr)
        records.append({'name': name, 'argv': list(map(str, command)),
                        'cwd': str(cwd), 'pythonpath': env.get('PYTHONPATH'),
                        'exit_code': code, 'timed_out': timed_out,
                        'elapsed_seconds': time.monotonic()-started,
                        'stdout_sha256': sha(output/(name+'.stdout')),
                        'stderr_sha256': sha(output/(name+'.stderr'))})
        (output/'commands.json').write_text(json.dumps(records, indent=2)+'\n')
        if timed_out:
            raise RuntimeError(name+' exceeded the 120-second command limit')
        if code:
            raise RuntimeError(name+' failed:\n'+stderr.decode(errors='replace')[-4000:])
        return stdout

    def test_count(name, minimum):
        text = (output/(name+'.stderr')).read_text()
        matches = re.findall(r'^Ran ([0-9]+) tests? in ', text, flags=re.MULTILINE)
        if len(matches) != 1 or int(matches[0]) < minimum:
            raise RuntimeError(name+' did not execute its minimum expected test count')
        summary[name+'_count'] = int(matches[0])

    try:
        summary['build_tools'] = {name: importlib.metadata.version(name)
                                  for name in ['pip', 'setuptools', 'wheel']}
        run('standalone-tests', [sys.executable, '-m', 'unittest', 'discover',
            '-s', source/'standalone/tests', '-v'], source, source/'standalone/src')
        test_count('standalone-tests', 38)
        validation = source/'validation/r02-06'
        reference = validation/'third-checker'
        run('third-tests', [sys.executable, '-m', 'unittest', 'discover',
            '-s', reference, '-v'], source)
        test_count('third-tests', 20)
        run('directed-mutations', [sys.executable, validation/'run_mutations.py',
            '--source', source, '--reference', reference,
            '--output', output/'mutations.json'], source)
        run('bounded-prefix', [sys.executable, validation/'run_consistency.py',
            '--source', source, '--reference', reference, '--limit', '64',
            '--wall-seconds', '60', '--output', output/'prefix.json'], source)
        with tempfile.TemporaryDirectory(prefix='wresearch-ci-') as td:
            temp = Path(td)
            build_source = temp/'standalone'
            shutil.copytree(source/'standalone', build_source,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc',
                                                         'build', '*.egg-info'))
            run('build-wheel', [sys.executable, '-m', 'pip', 'wheel', '--no-index',
                '--no-deps', '--no-build-isolation', '--wheel-dir', temp/'wheels',
                build_source], temp)
            wheels = list((temp/'wheels').glob('*.whl'))
            if len(wheels) != 1:
                raise RuntimeError('expected exactly one wheel')
            wheel = wheels[0]
            summary['wheel_sha256'] = sha(wheel)
            run('venv', [sys.executable, '-m', 'venv', temp/'venv'], temp)
            python = temp/'venv/bin/python'
            run('install', [python, '-m', 'pip', 'install', '--no-index',
                '--no-deps', wheel], temp)
            outside = temp/'outside'; outside.mkdir()
            fixtures = source/'standalone/fixtures'
            common = ['--model', fixtures/'mixed.model.json',
                      '--policy', fixtures/'policy.json']
            for atom, verdict in enumerate(['UNRESOLVED', 'TRUE', 'FALSE', 'OUTSIDE_MODEL']):
                report = json.loads(run('evaluate-'+str(atom), [python, '-I', '-m',
                    'witnessability_checker', 'evaluate-record', *common,
                    '--record', fixtures/f'mixed.{atom}.record.json',
                    '--expected', fixtures/f'mixed.{atom}.expected.json'], outside))
                if report.get('status') != 'ok' or report['result']['verdict'] != verdict:
                    raise RuntimeError('installed record verdict mismatch')
            for witness in ['f', 'g']:
                report = json.loads(run('verify-'+witness, [python, '-I', '-m',
                    'witnessability_checker', 'verify-ambiguity', *common,
                    '--record', fixtures/'mixed.0.record.json',
                    '--expected', fixtures/'mixed.0.expected.json',
                    '--certificate', fixtures/f'mixed.0.{witness}.certificate.json'], outside))
                if report.get('status') != 'ok' or report['result']['valid'] is not True:
                    raise RuntimeError('installed witness check mismatch')
            for model, expected in [('mixed', False), ('separated', True)]:
                report = json.loads(run('capability-'+model, [python, '-I', '-m',
                    'witnessability_checker', 'check-capability',
                    '--model', fixtures/(model+'.model.json'),
                    '--policy', fixtures/'policy.json',
                    '--expected', fixtures/(model+'.capability.expected.json')], outside))
                if report.get('status') != 'ok' or report['result']['capability'] is not expected:
                    raise RuntimeError('installed capability mismatch')
            report = json.loads(run('console-entry-point', [temp/'venv/bin/witnessability-checker',
                'evaluate-record', *common, '--record', fixtures/'mixed.1.record.json',
                '--expected', fixtures/'mixed.1.expected.json'], outside))
            if report.get('status') != 'ok' or report['result']['verdict'] != 'TRUE':
                raise RuntimeError('installed console entry point mismatch')
            guard = '''import importlib.abc,json,sys
operation=sys.argv[1]
forbidden=['witnessability_research','witnessability_checker.legacy']
if operation=='verify-ambiguity':
 forbidden+=['witnessability_checker.analysis','witnessability_checker.capability_command']
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,name,path=None,target=None):
  if any(name==p or name.startswith(p+'.') for p in forbidden):
   raise RuntimeError('forbidden import '+name)
sys.meta_path.insert(0,Guard())
from witnessability_checker.cli import main
raise SystemExit(main(json.loads(sys.argv[2])))
'''
            for operation in ['evaluate-record', 'verify-ambiguity', 'check-capability']:
                command = [operation, *map(str, common), '--expected', str(fixtures/(
                    'mixed.capability.expected.json' if operation == 'check-capability'
                    else 'mixed.0.expected.json'))]
                if operation != 'check-capability':
                    command += ['--record', str(fixtures/'mixed.0.record.json')]
                if operation == 'verify-ambiguity':
                    command += ['--certificate', str(fixtures/'mixed.0.f.certificate.json')]
                run('imports-'+operation, [python, '-I', '-c', guard,
                    operation, json.dumps(command)], outside)
        summary['status'] = 'PASS'
        summary['commands_passed'] = len(records)
    except Exception as exc:
        summary['status'] = 'FAIL'
        summary['error'] = str(exc)
    finally:
        (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        print(json.dumps(summary, indent=2))
    return 0 if summary['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
