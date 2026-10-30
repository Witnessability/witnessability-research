# SPDX-License-Identifier: Apache-2.0
"""Run the three public C1 inputs against an exact public checker snapshot."""
import argparse, hashlib, json, subprocess, sys, datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent
CASES=('C1-01-covered-empty','C1-02-event-with-gap','C1-03-empty-with-gap')
def require(ok,message):
    if not ok: raise ValueError(message)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def safe(root,rel):
    p=(root/rel).resolve();require(p.is_relative_to(root.resolve()),'unsafe path');return p
def verify_files(root,items):
    require(len({x['path'] for x in items})==len(items),'duplicate paths')
    for x in items:
        raw=safe(root,x['path']).read_bytes()
        require(len(raw)==x['length'] and sha(raw)==x['sha256'],'pin mismatch: '+x['path'])
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--checker-root',type=Path,default=HERE.parents[1]);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    require(sys.version_info>=(3,12),'Python >=3.12 required')
    root=a.checker_root.resolve();out=a.out.resolve();require(not out.exists(),'output must be new')
    pin=read(HERE/'CHECKER-SOURCE-PIN.json');manifest=read(HERE/'INPUT-MANIFEST.json')
    verify_files(root,pin['files']);verify_files(HERE,manifest['files'])
    module_root=root/'standalone/src/witnessability_checker'
    require({x.relative_to(root).as_posix() for x in module_root.rglob('*.py')}=={x['path'] for x in pin['files']},'unexpected source module')
    exp_bytes=(HERE/'EXPECTED.json').read_bytes();require(sha(exp_bytes)==manifest['expected_sha256'],'expectation mismatch')
    expected=json.loads(exp_bytes);require(set(expected)==set(CASES),'case set mismatch')
    frozen={str(x):sha(x.read_bytes()) for x in [HERE/'CHECKER-SOURCE-PIN.json',HERE/'INPUT-MANIFEST.json',HERE/'EXPECTED.json',Path(__file__)]}
    out.mkdir(parents=True)
    summary={'source_commit':pin['commit'],'python':sys.version,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mode':'new execution of existing checker on three public synthetic inputs','cases':{},'pre_run_hashes':frozen,'probity_executed':False,'general_equivalence':False}
    (out/'PRE-RUN.json').write_text(json.dumps(summary,indent=2)+'\n')
    wrapper='import pathlib,sys,importlib\nsrc=pathlib.Path(sys.argv.pop(1)).resolve()\nsys.path.insert(0,str(src))\nm=importlib.import_module("witnessability_checker.cli")\ntry:\n m.main()\nfinally:\n origins={n:str(pathlib.Path(v.__file__).resolve()) for n,v in sys.modules.items() if n.startswith("witnessability_checker") and getattr(v,"__file__",None)}\n pathlib.Path("origins.json").write_text(__import__("json").dumps(origins,sort_keys=True)+"\\n")\n if any(not pathlib.Path(v).is_relative_to(src) for v in origins.values()): raise RuntimeError("foreign module")\n'
    # Preserve the CLI exit value: main() returns an integer on this source.
    wrapper=wrapper.replace(' m.main()',' raise SystemExit(m.main())')
    for case in CASES:
        d=out/case;d.mkdir();i=HERE/'inputs'
        argv=[sys.executable,'-I','-B','-X','pycache_prefix='+str(out/'unused-pycache'),'-c',wrapper,str(root/'standalone/src'),'evaluate-record','--model',str(i/'checker-model.json'),'--policy',str(i/'checker-policy.json'),'--expected',str(i/'expected-pins'/(case+'.json')),'--record',str(i/'records'/(case+'.json')),'--scope','raw','--max-work','2000000']
        (d/'command.json').write_text(json.dumps(argv,indent=2)+'\n')
        v=subprocess.run(argv,cwd=d,capture_output=True,timeout=60);(d/'stdout.json').write_bytes(v.stdout);(d/'stderr.txt').write_bytes(v.stderr)
        matched=v.returncode==0 and not v.stderr and json.loads(v.stdout)==expected[case]
        summary['cases'][case]={'exit_code':v.returncode,'stdout_sha256':sha(v.stdout),'stderr_sha256':sha(v.stderr),'full_expected_match':matched,'verdict':json.loads(v.stdout).get('result',{}).get('verdict') if v.returncode==0 else None}
    verify_files(root,pin['files']);verify_files(HERE,manifest['files'])
    for path,digest in frozen.items():require(sha(Path(path).read_bytes())==digest,'changed during run')
    summary['status']='PASS' if all(x['full_expected_match'] for x in summary['cases'].values()) else 'FAIL'
    summary['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(out/'RESULTS.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'status':summary['status'],'cases':len(summary['cases'])}));return 0 if summary['status']=='PASS' else 1
if __name__=='__main__':sys.exit(main())
