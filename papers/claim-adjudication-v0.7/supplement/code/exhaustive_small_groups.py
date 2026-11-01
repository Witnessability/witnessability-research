"""Exhaust all two-binary-domain models with two opposite histories.
Uses finite_reference.py; this is not an independently authored verification.
"""
import importlib.util,itertools,json,hashlib,platform
from pathlib import Path
root=Path(__file__).parent
source=root/'finite_reference.py'
spec=importlib.util.spec_from_file_location('reviewer',source)
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
Y=list(itertools.product(range(2),repeat=2))
def subsets(items):
 return [tuple(x for i,x in enumerate(items) if mask>>i&1) for mask in range(1<<len(items))]
supports=subsets(Y)[1:]
groups=[S for S in subsets(Y) if (0,0) in S and all(tuple(x^y for x,y in zip(a,b)) in S for a in S for b in S)]
domains=[frozenset(s) for s in subsets(range(2))]
faults=[S for S in subsets(domains) if S and all(T in S for F in S for T in domains if T<=F)]
assert len(supports)==15 and len(groups)==5 and len(faults)==5
n=nontrivial=setvalued=noncardinal=0
outcomes={'adj_fail':0,'undetected':0}
cardinal=[set(F for F in domains if len(F)<=t) for t in range(3)]
for J0,J1,flips,Phi in itertools.product(supports,supports,groups,faults):
 G=[tuple((b,1-b) for b in flip) for flip in flips]
 J={0:J0,1:J1};p={0:0,1:1}
 a=c.structural_adj_fail(p,J,G,Phi);b=c.direct_adj_fail(p,J,G,Phi,[2,2])
 d=c.structural_undetected(p,J,G,Phi);e=c.direct_undetected(p,J,G,Phi,[2,2])
 assert a==b and d==e,(J,flips,Phi)
 n+=1;nontrivial+=len(G)>1;setvalued+=len(J0)>1 or len(J1)>1;noncardinal+=set(Phi) not in cardinal
 outcomes['adj_fail']+=a;outcomes['undetected']+=d
assert n==5625
result=dict(models=n,theorem1_matches=n,proposition1_matches=n,nontrivial_groups=nontrivial,setvalued_supports=setvalued,noncardinal_fault_families=noncardinal,outcomes=outcomes,python=platform.python_version(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='All 15^2 nonempty support pairs, 5 subgroups of C2 x C2, 5 nonempty downward-closed fault families; exactly two histories with opposite truth values; two binary coordinates.',limit='Finite exhaustive coverage, not a proof or independent implementation.')

print(json.dumps(result))
