"""Replay finite ledger projections, without raw-data admission or signature checks."""
from pathlib import Path
import itertools,json
root=Path(__file__).resolve().parent.parent
data=json.loads((root/'data/ledger-projection.json').read_text())
out=[]
for row in data['cases']:
 if row['gate']!='admitted':continue
 m=data['models'][row['model']]
 if m['binding']!='identity' or m['faults']!=[[]]:raise ValueError('unsupported model')
 compatible=[h for h in m['histories'] if row['record'] in m['joint'][h]]
 ts={m['truth'][h] for h in compatible}
 verdict='TRUE' if ts=={True} else 'FALSE' if ts=={False} else 'UNRESOLVED' if ts else 'OUTSIDE_MODEL'
 if verdict!=row['verdict'] or compatible!=row['compatible']:raise ValueError(row['id'])
 out.append(dict(id=row['id'],verdict=verdict,compatible=compatible))
margins={}
for name,m in data['models'].items():
 margins[name]=min(sum(a!=b for a,b in zip(r,s)) for h,k in itertools.product(m['histories'],repeat=2) if m['truth'][h] and not m['truth'][k] for r in m['joint'][h] for s in m['joint'][k])
print(json.dumps(dict(matches=len(out),cases=out,margins=margins,excluded_admission_refusals=3),indent=2))
