"""Command reports and import boundaries; packaging itself is checked separately."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from witnessability_checker import cli
from witnessability_checker.common import Budget
from witnessability_checker.context import make_pins, validate_document

FIXTURES=Path(__file__).resolve().parents[1]/'fixtures'
SOURCE=Path(__file__).resolve().parents[1]/'src'


def fixture(name): return str(FIXTURES/name)


def args(operation='evaluate-record', atom='0', name='mixed'):
    result=[operation,'--model',fixture(name+'.model.json'),
            '--policy',fixture('policy.json')]
    if operation=='check-capability':
        result += ['--expected',fixture(name+'.capability.expected.json')]
    else:
        result += ['--expected',fixture(name+'.'+atom+'.expected.json'),
                   '--record',fixture(name+'.'+atom+'.record.json')]
    if operation=='verify-ambiguity':
        result += ['--certificate',fixture('mixed.0.f.certificate.json')]
    return result


def invoke(arguments):
    stdout,stderr=io.StringIO(),io.StringIO()
    with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
        code=cli.main(arguments)
    output=stdout.getvalue()
    report=json.loads(output)
    return code,report,stderr.getvalue(),output


class CLIContract(unittest.TestCase):
    def test_all_three_commands_and_report_fields(self):
        for operation in ('evaluate-record','verify-ambiguity','check-capability'):
            with self.subTest(operation=operation):
                code,r,err,out=invoke(args(operation))
                self.assertEqual(code,0);self.assertEqual(err,'')
                self.assertEqual(r['status'],'ok');self.assertEqual(r['completion'],'completed')
                self.assertEqual(r['operation'],operation);self.assertEqual(r['scope'],'raw')
                for field in ('versions','pins','expected_pins','method','admission','limits','work','result'):
                    self.assertIn(field,r)
                self.assertGreater(r['work'],0)
                self.assertEqual(r['pins'],r['expected_pins'])
                self.assertEqual(len(out.strip().splitlines()),1)
        for atom,verdict in [('0','UNRESOLVED'),('1','TRUE'),('2','FALSE'),('3','OUTSIDE_MODEL')]:
            code,r,err,_=invoke(args(atom=atom));self.assertEqual(code,0)
            self.assertEqual(r['result']['verdict'],verdict)

    def test_capability_returns_supplied_verifiable_certificate(self):
        code,r,_,_=invoke(args('check-capability'))
        self.assertEqual(code,0);self.assertFalse(r['result']['capability'])
        cert=r['result']['certificate']
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            for name,value in [('cert.json',cert),('record.json',cert['record'])]:
                (folder/name).write_text(json.dumps(value))
            # Caller derives expected record binding from independently selected
            # model/policy and the advertised counterexample, not cert['pins'].
            doc=json.loads(Path(fixture('mixed.model.json')).read_text())
            policy=json.loads(Path(fixture('policy.json')).read_text())
            model=validate_document(doc,Budget())
            external=make_pins(doc,model,policy,cert['record'])
            (folder/'external.json').write_text(json.dumps(external))
            argv=args('verify-ambiguity')
            for flag,name in [('--certificate','cert.json'),('--record','record.json'),('--expected','external.json')]:
                argv[argv.index(flag)+1]=str(folder/name)
            code,r,_,_=invoke(argv)
            self.assertEqual(code,0);self.assertTrue(r['result']['valid'])

    def test_error_statuses_never_become_mathematical_verdicts(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            def changed(flag,filename,value,operation='evaluate-record'):
                (folder/filename).write_text(json.dumps(value))
                argv=args(operation);argv[argv.index(flag)+1]=str(folder/filename)
                return argv
            policy=json.loads(Path(fixture('policy.json')).read_text())
            unknown=dict(policy,id='unknown')
            wrong_expected=json.loads(Path(fixture('mixed.0.expected.json')).read_text())
            wrong_expected['model']='0'*64
            bad_cert=json.loads(Path(fixture('mixed.0.f.certificate.json')).read_text())
            bad_cert['witnesses'][0]['history']='t'
            cases=[(2,'invalid_input',changed('--record','bad-record.json',[True])),
                   (3,'unsupported',changed('--policy','unknown-policy.json',unknown)),
                   (4,'pin_mismatch',changed('--expected','wrong-pins.json',wrong_expected)),
                   (6,'invalid_certificate',changed('--certificate','bad-cert.json',bad_cert,'verify-ambiguity')),
                   (7,'compute_limit',args()+['--max-work','1']),
                   (3,'unsupported',args('check-capability')+['--scope','admitted-only']),
                   (2,'invalid_input',args()+['--max-work','true']),
                   (2,'invalid_input',args()+['--max-work','0'])]
            # Unsupported does not consume an old context as if it were raw.
            for code,status,argv in cases:
                with self.subTest(status=status,argv=argv):
                    actual,r,err,out=invoke(argv)
                    self.assertEqual(actual,code);self.assertEqual(r['status'],status)
                    self.assertIsNone(r['result']);self.assertEqual(r['completion'],'not_completed')
                    self.assertTrue(err);self.assertEqual(len(out.strip().splitlines()),1)
            # Known policy with correctly rebound expected pins is rejected by
            # admission, not by pin mismatch; the two stages are different.
            rejected=dict(policy,acknowledged_assumptions=False)
            doc=json.loads(Path(fixture('mixed.model.json')).read_text())
            model=validate_document(doc,Budget())
            argv=changed('--policy','reject.json',rejected)
            (folder/'reject-pins.json').write_text(json.dumps(make_pins(doc,model,rejected,['0'])))
            argv[argv.index('--expected')+1]=str(folder/'reject-pins.json')
            code,r,err,_=invoke(argv)
            self.assertEqual(code,5);self.assertEqual(r['status'],'admission_rejected')
            self.assertEqual(r['admission']['status'],'rejected');self.assertIsNone(r['result'])
            # Same policy is bound but not an admitted-only restriction on raw capability.
            argv=args('check-capability');argv[argv.index('--policy')+1]=str(folder/'reject.json')
            (folder/'raw-pins.json').write_text(json.dumps(make_pins(doc,model,rejected)))
            argv[argv.index('--expected')+1]=str(folder/'raw-pins.json')
            code,r,err,_=invoke(argv)
            self.assertEqual(code,0);self.assertEqual(r['admission']['status'],'not_applicable_raw_scope')
            self.assertFalse(r['result']['capability'])

    def test_unexpected_computation_error_is_not_a_verdict(self):
        with patch('witnessability_checker.analysis.evaluate_record',side_effect=RuntimeError('injected failure')):
            code,r,err,_=invoke(args())
        self.assertEqual(code,8);self.assertEqual(r['status'],'compute_error')
        self.assertIsNone(r['result']);self.assertEqual(r['completion'],'not_completed')
        self.assertNotIn('injected failure',err)

    def test_bad_certificate_json_does_not_infer_determinacy(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'dup.json';path.write_text('{"a":1,"a":2}')
            argv=args('verify-ambiguity');argv[argv.index('--certificate')+1]=str(path)
            code,r,_,_=invoke(argv)
            self.assertEqual(code,2);self.assertIsNone(r['result'])
        code,r,_,_=invoke(args('verify-ambiguity'))
        self.assertEqual(code,0);self.assertEqual(r['result']['record_verdict'],'UNRESOLVED')


GUARD = r'''
import importlib.abc,json,pathlib,sys
forbidden=('witnessability_research', 'witnessability_checker.analysis',
           'witnessability_checker.legacy', 'witnessability_checker.capability_command',
           'experiment', 'store')
class RejectForbidden(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if any(fullname==n or fullname.startswith(n+'.') for n in forbidden):
            raise RuntimeError('FORBIDDEN_IMPORT:'+fullname)
sys.meta_path.insert(0,RejectForbidden())
from witnessability_checker.cli import main
code=main(json.loads(sys.argv[1]))
closure=sorted(n for n in sys.modules if n.startswith('witnessability_'))
pathlib.Path(sys.argv[2]).write_text(json.dumps(closure))
assert not any(n in closure for n in forbidden),closure
raise SystemExit(code)
'''


class ImportBoundaryControls(unittest.TestCase):
    def guarded(self,source,arguments,work):
        env=os.environ.copy();env['PYTHONPATH']=str(source)
        closure=Path(work)/'closure.json'
        result=subprocess.run([sys.executable,'-c',GUARD,json.dumps(arguments),str(closure)],
                              cwd=work,env=env,text=True,capture_output=True)
        modules=json.loads(closure.read_text()) if closure.exists() else []
        return result,modules

    def test_verification_import_closure_excludes_search_and_generator(self):
        with tempfile.TemporaryDirectory() as td:
            result,modules=self.guarded(SOURCE,args('verify-ambiguity'),td)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertTrue(json.loads(result.stdout)['result']['valid'])
            self.assertIn('witnessability_checker.verify',modules)
            self.assertNotIn('witnessability_checker.analysis',modules)
            self.assertNotIn('witnessability_checker.capability_command',modules)
            self.assertNotIn('witnessability_research',modules)

    def test_each_operation_imports_only_its_allowed_analysis_modules(self):
        for operation in ('evaluate-record', 'check-capability'):
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as td:
                env = os.environ.copy(); env['PYTHONPATH'] = str(SOURCE)
                allowed_guard = GUARD.replace("'witnessability_checker.analysis',", '')
                if operation == 'check-capability':
                    allowed_guard = allowed_guard.replace("'witnessability_checker.capability_command',", '')
                closure = Path(td)/'closure.json'
                result = subprocess.run([sys.executable, '-c', allowed_guard,
                    json.dumps(args(operation)), str(closure)], cwd=td, env=env,
                    text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                modules = json.loads(closure.read_text())
                self.assertIn('witnessability_checker.analysis', modules)
                self.assertNotIn('witnessability_checker.verify', modules)
                self.assertNotIn('witnessability_checker.legacy', modules)
                self.assertNotIn('witnessability_research', modules)
                if operation == 'check-capability':
                    self.assertIn('witnessability_checker.capability_command', modules)
                else:
                    self.assertNotIn('witnessability_checker.capability_command', modules)

    def test_missing_and_poisoned_generator_leave_result_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);src=root/'src';src.mkdir()
            shutil.copytree(SOURCE/'witnessability_checker',src/'witnessability_checker',
                            ignore=shutil.ignore_patterns('__pycache__'))
            before,mods=self.guarded(src,args('verify-ambiguity'),td)
            # An importable poison generator/old CLI must remain untouched.
            poison=src/'witnessability_research';poison.mkdir()
            (poison/'__init__.py').write_text('raise RuntimeError("poison generator imported")\n')
            for filename in ('experiment.py','store.py','cli.py','finite.py'):
                (poison/filename).write_text('raise RuntimeError("poison generator imported")\n')
            after,mods2=self.guarded(src,args('verify-ambiguity'),td)
            self.assertEqual(before.returncode,0,before.stderr)
            self.assertEqual(after.returncode,0,after.stderr)
            self.assertEqual(before.stdout,after.stdout);self.assertEqual(mods,mods2)

    def test_forbidden_search_call_mutation_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);src=root/'src';src.mkdir()
            shutil.copytree(SOURCE/'witnessability_checker',src/'witnessability_checker',
                            ignore=shutil.ignore_patterns('__pycache__'))
            verifier=src/'witnessability_checker/verify.py'
            # Controlled mutation of a disposable copy, never production source.
            mutated = verifier.read_text().replace(
                '    budget.tick()\n    if type(record)',
                '    budget.tick()\n    check_capability(model, budget)\n    if type(record)', 1)
            verifier.write_text('from .analysis import check_capability\n' + mutated)
            result,modules=self.guarded(src,args('verify-ambiguity'),td)
            self.assertEqual(result.returncode,8,result.stderr)
            report=json.loads(result.stdout)
            self.assertEqual(report['status'],'compute_error');self.assertIsNone(report['result'])


if __name__=='__main__':unittest.main()
