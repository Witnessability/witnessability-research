"""Enumerate Definition 2 and decision for every coalition in Table 1.

All four arrangements have identity binding. Randomizers are enumerated as
honest support choices, not disclosed to the observer except by its shares.
Run with Python 3: python3 -B code/check_coalition_concealment.py
"""
from itertools import product, combinations
from collections import defaultdict
import json

def rows(kind):
    for ua, ub, xa, xb in product((0,1),repeat=4):
        p=ua & xa
        if kind=='bound': yield ((ua,ub),(xa,xb)),p
        elif kind=='scoped': yield (ua,xa),p
        elif kind=='xor':
            for a,b in product((0,1),repeat=2): yield (ua^a,a,xa^b,b),p
        else:
            for a,b in product(range(5),repeat=2):
                yield tuple(((ua+a*x)%5,(xa+b*x)%5) for x in range(1,5)),p

def check(kind):
    records=list(rows(kind)); m=len(records[0][0]); results=[]
    for size in range(m+1):
        for coalition in combinations(range(m),size):
            observations=defaultdict(set)
            for record,p in records: observations[tuple(record[i] for i in coalition)].add(p)
            decides=all(len(v)==1 for v in observations.values())
            conceals=all(v=={0,1} for v in observations.values())
            witness=next(({'observation':o,'claim_values':sorted(v)} for o,v in observations.items() if len(v)==1),None)
            results.append({'coalition':coalition,'observations':len(observations),'decides':decides,'conceals':conceals,'nonconcealment_witness':witness})
    margin=min(sum(a!=b for a,b in zip(r,s)) for r,p in records for s,q in records if p!=q)
    return {'arrangement':kind,'history_support_pairs':len(records),'coalitions':results,'margin':margin,'smallest_deciding_coalition':min(len(r['coalition']) for r in results if r['decides']),'every_singleton_concealed':all(r['conceals'] for r in results if len(r['coalition'])==1),'max_q_every_coalition_up_to_q_concealed':max(q for q in range(m+1) if all(r['conceals'] for r in results if len(r['coalition'])<=q))}

if __name__=='__main__':
    result=[check(k) for k in ('bound','scoped','xor','shamir')]
    assert [r['smallest_deciding_coalition'] for r in result]==[2,2,4,2]
    assert [r['every_singleton_concealed'] for r in result]==[False,False,True,True]
    assert [r['margin'] for r in result]==[1,1,1,3]
    assert [r['max_q_every_coalition_up_to_q_concealed'] for r in result]==[0,0,1,1]
    print(json.dumps({'status':'PASS','binding':'identity in all four arrangements','scope':'All honest observations of every coalition; no faulted concealment or deployment claim','results':result},indent=2))
