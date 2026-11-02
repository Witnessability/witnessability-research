"""Reproduce the saved candidate and proposed default-only fix. Python stdlib only."""
import copy, difflib, hashlib, importlib.util, io, json, pathlib, platform, subprocess, sys, unittest
ROOT = pathlib.Path(__file__).resolve().parent
BASE = ROOT / "baseline"
OUT = ROOT / "review-results"
OUT.mkdir(exist_ok=True)
def sha(data): return hashlib.sha256(data).hexdigest()
def dump(path, data): path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
original = (BASE / "checker.py").read_bytes()
assert sha(original) == "4e30922ac5a5044e7e0fb821e620321dcaa6cb748eeb6c2f3280d541be103afe"
modified = original.decode()
for before, after in [
    ('vocabulary_mode="draft"', 'vocabulary_mode="profile"'),
    ('mode="draft"):', 'mode="profile"):'),
    ('default="draft"', 'default="profile"'),
]:
    assert modified.count(before) == 1, before
    modified = modified.replace(before, after)
(ROOT / "proposed").mkdir(exist_ok=True)
(ROOT / "proposed/checker.py").write_text(modified)
(ROOT / "proposed/default-mode.patch").write_text("".join(difflib.unified_diff(
    original.decode().splitlines(True), modified.splitlines(True),
    fromfile="baseline/checker.py", tofile="proposed/checker.py")))
old = module("old_checker", BASE / "checker.py")
new = module("new_checker", ROOT / "proposed/checker.py")
sys.modules["checker"] = old
fixtures = module("fixtures", BASE / "test_checker.py")
unit_results = {}
for label, checker in [("baseline", old), ("proposed", new)]:
    sys.modules["checker"] = checker
    tests = module("tests_" + label, BASE / "test_checker.py")
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    (OUT / (label + "-unit-tests.txt")).write_text(stream.getvalue())
    unit_results[label] = {"run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors)}
    assert result.wasSuccessful()
manifest = json.loads((BASE / "MANIFEST.upstream.json").read_text())
inputs = json.loads((BASE / "corpus-inputs.json").read_text())
archived = json.loads((BASE / "results/final/REPLAY-RESULT.json").read_text())
archive_index = {(x["mode"], x["id"]): x["actual"] for x in archived["results"]}
verified = set()
rows = []
for v in manifest["vectors"]:
    data = []
    for name, expected_hash in sorted(v["files"].items()):
        path = "vectors-restart-records/" + v["path"] + "/" + name
        value = inputs[path].encode()
        assert sha(value) == expected_hash, path
        verified.add(path)
        data.append(value)
    for label, checker, mode in [("baseline-draft", old, "draft"), ("baseline-profile", old, "profile"), ("proposed-default", new, None)]:
        kwargs = {} if mode is None else {"mode": mode}
        if v["shape"] == "record":
            actual = (checker.Reader() if mode is None else checker.Reader(mode)).record(data[0])
        else:
            actual = checker.bundle(data, **kwargs)
        if label.startswith("baseline"):
            assert actual == archive_index[(mode, v["id"])], (mode, v["id"])
        rows.append({"id": v["id"], "variant": label, "actual": actual, "expected": v["expected"],
                     "verdict_match": actual["verdict"] == v["expected"]["verdict"],
                     "reason_match": actual["reason"] == v["expected"]["reason"]})
assert len(verified) == 75
dump(OUT / "corpus-replay.json", rows)
cases = []
def add(name, record, expected, rule, diagnostic=None):
    cases.append((name, record, expected, rule, diagnostic or expected))
def r3(): return fixtures.r3(fixtures.r2(fixtures.r1()))
s=r3(); s["predicate"]["approvers"][0]["roles"]=["approver"]
add("document-role",s,"predicate-malformed","2","closed-vocabulary-violation")
s=fixtures.rb(); s["predicate"]["sink"]["kind"]="unregistered"
add("document-sink",s,"predicate-malformed","2","closed-vocabulary-violation")
s=fixtures.r4(); s["predicate"]["parties"][0]["authorityBasis"]="unregistered"
add("document-authority",s,"predicate-malformed","2","closed-vocabulary-violation")
s=r3(); s["predicate"]["approvers"][0]["independenceBasis"]="unregistered"
add("registry-independence",s,"closed-vocabulary-violation","3")
s=copy.deepcopy(s); del s["predicate"]["producer"]
add("shape-before-registry",s,"predicate-malformed","2")
s=fixtures.r1(); del s["predicate"]["parties"][0]["authorityBasis"]
add("authority-absent",s,"authority-basis-missing","R1.6")
s=copy.deepcopy(s); s["predicate"]["intentBinding"]="unregistered"
add("registry-before-authority-absence",s,"closed-vocabulary-violation","3")
s=fixtures.r1(); s["predicate"]["parties"][0]["authorityBasis"]=42
add("authority-wrong-type",s,"predicate-malformed","2")
s=fixtures.r1(); s["predicate"]["action"]["inducedEffects"]={"declared":"none_observed"}
add("observation-absent",s,"induced-effects-unobserved","R1.10")
s=copy.deepcopy(s); s["predicate"]["action"]["inducedEffects"]["observation"]={"sha256":"bad"}
add("observation-malformed",s,"predicate-malformed","2")
s=r3(); del s["predicate"]["evidence"]["persistence"]
add("slot-absent",s,"evidence-slot-missing","R3.4")
s=copy.deepcopy(s); s["predicate"]["evidence"]["rootCause"]={"notAddressed":""}; s["predicate"]["approvers"]=[]
add("slot-before-explanation-and-approver",s,"evidence-slot-missing","R3.4")
s=r3(); s["predicate"]["evidence"]["rootCause"]={"notAddressed":""}; s["predicate"]["approvers"]=[]
add("explanation-before-approver",s,"evidence-slot-unexplained","R3.5")
s=r3(); del s["predicate"]["evidence"]
add("evidence-container-absent",s,"predicate-malformed","2")
s=r3(); s["predicate"]["approvers"]=[]
add("approvers-empty",s,"no-approver","R3.6")
s=copy.deepcopy(s); s["predicate"]["setSufficiency"]="unregistered"
add("registry-before-empty-approvers",s,"closed-vocabulary-violation","3")
s=r3(); del s["predicate"]["restoration"]["restoredScope"]
add("staged-scope-absent",s,"partial-without-scope","R3.7")
s=copy.deepcopy(s); s["predicate"]["restoration"]["restoredScope"]=[]
add("scope-wrong-type",s,"predicate-malformed","2")
s=fixtures.r4(); del s["predicate"]["parties"][0]["authorityBasis"]; s["predicate"]["parties"][1]["organization"]="one"
add("authority-before-single-organization",s,"authority-basis-missing","R4.4")
s=fixtures.r2(fixtures.r1()); s["predicate"]["coverage"]["claim"]="issued_after_only"
add("coverage-time-absent",s,"coverage-claim-incomplete","R2.7")
s=r3(); s["predicate"]["restoration"]["decision"]="resume_full"
add("full-with-scope",s,"full-with-scope","R3.8")
s=r3(); del s["predicate"]["evidence"]["persistence"]; s["predicate"]["evidence"]["rootCause"]={"notAddressed":42}
add("slot-missing-and-value-wrong-type",s,"predicate-malformed","2")
(ROOT / "examples").mkdir(exist_ok=True)
observations=[]
for name, record, expected, rule, diagnostic in cases:
    raw=fixtures.raw(record)
    path=ROOT / "examples" / (name+".json")
    path.write_bytes(raw)
    actual=new.Reader().record(raw)
    literal=old.Reader("draft").record(raw)
    assert actual == {"verdict":"reject","reason":expected}, (name,actual,expected)
    assert literal["reason"] == diagnostic, (name,literal,diagnostic)
    observations.append({"id":name,"path":str(path.relative_to(ROOT)),"sha256":sha(raw),"rule":rule,
        "expected":expected,"observed":actual,"draft_diagnostic":literal,
        "invariant":"First failing rule is retained; only its named condition is deferred.",
        "failure_condition":"Returned reason differs from expected; input bytes are pinned."})
dump(OUT / "boundary-examples.json",observations)
negative=[]
for label, checker, path in [("baseline",old,BASE/"checker.py"),("proposed",new,ROOT/"proposed/checker.py")]:
    example=ROOT/"examples/document-role.json"
    record=json.loads(example.read_text())
    a=fixtures.r1(); b=fixtures.r2(a); record["predicate"]["predecessors"]=[fixtures.ref(b)]
    cli=subprocess.run([sys.executable,str(path),"--record",str(example)],capture_output=True,text=True)
    results={"reader":checker.Reader().record(example.read_bytes()),"bundle":checker.bundle([fixtures.raw(x) for x in (a,b,record)]),
             "cli":json.loads(cli.stdout),"cli_exit":cli.returncode}
    expected="closed-vocabulary-violation" if label=="baseline" else "predicate-malformed"
    assert cli.returncode==1
    assert all(results[k]["reason"]==expected for k in ("reader","bundle","cli"))
    negative.append({"variant":label,"passes_intended_default":label=="proposed","observed":results})
dump(OUT/"default-negative-controls.json",negative)
fresh=[]
sources=json.loads((BASE/"SOURCES.json").read_text())
for source in sources["sources"]:
    p=ROOT/"upstream"/source["path"]
    if p.exists():
        digest=sha(p.read_bytes())
        fresh.append({"path":source["path"],"sha256":digest,"unchanged":digest==source["sha256"]})
assert all(x["unchanged"] for x in fresh)
assert (ROOT/"upstream/corpora/vectors-restart-records/MANIFEST.json").read_bytes()==(BASE/"MANIFEST.upstream.json").read_bytes()
summary={"python":sys.version,"platform":platform.platform(),"external_dependencies":[],
    "baseline_sha256":sha(original),"proposed_sha256":sha(modified.encode()),
    "verified_input_files":len(verified),"baseline_rows_identical_to_archived":114,
    "original_unit_tests":unit_results,"new_boundary_examples":len(cases),
    "default_negative_controls":"Baseline fails intended reason on Reader, bundle and CLI; proposed passes.",
    "fresh_sources":fresh,"current_manifest_byte_identical":True,
    "corpus":{label:{"count":len([r for r in rows if r["variant"]==label]),
        "verdict_matches":sum(r["verdict_match"] for r in rows if r["variant"]==label),
        "reason_matches":sum(r["reason_match"] for r in rows if r["variant"]==label)}
        for label in ("baseline-draft","baseline-profile","proposed-default")}}
dump(OUT/"SUMMARY.json",summary)
print(json.dumps(summary,indent=2))

