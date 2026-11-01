"""Constructed model: event B, source record C, returned record R; R <= C <= B.
This is a decision-analysis prototype, not an Audit Store or AAR implementation.
Complete booleans are admitted premises, never inferred from self-declarations.
"""
import itertools,json
from pathlib import Path
H=[(b,c,r) for b,c,r in itertools.product([0,1],repeat=3) if r<=c<=b]
def solve(r,search_complete,capture_complete):
 hs=[h for h in H if h[2]==r and (not search_complete or h[1]==h[2]) and (not capture_complete or h[0]==h[1])]
 ts={h[0]==0 for h in hs}
 return dict(verdict='TRUE' if ts=={True} else 'FALSE' if ts=={False} else 'UNRESOLVED',histories=hs)
def main():
 cases=[]
 for r,s,c in itertools.product([0,1],repeat=3):
  result=solve(r,s,c)
  expected='FALSE' if r else 'TRUE' if s and c else 'UNRESOLVED'
  if result['verdict']!=expected:raise ValueError((r,s,c))
  cases.append(dict(returned_positive=r,search_complete=s,capture_complete=c,**result))
 # The same empty response survives any number of copies and signatures.
 ambiguity=solve(0,1,0)['histories']
 if (0,0,0) not in ambiguity or (1,0,0) not in ambiguity:raise ValueError('missing capture counterexample')
 ambiguity2=solve(0,0,1)['histories']
 if (0,0,0) not in ambiguity2 or (1,1,0) not in ambiguity2:raise ValueError('missing search counterexample')
 # Actual portfolios of logical premises, not failure domains.
 portfolios=[]
 for size in range(3):
  for subset in itertools.combinations(['search_complete','capture_complete'],size):
   if solve(0,'search_complete' in subset,'capture_complete' in subset)['verdict']=='TRUE':portfolios.append(list(subset))
 out=dict(histories=H,cases=cases,minimum_premise_portfolio=portfolios[0],limits='No false positive records in H; positive witness must be admitted and bound. No arbitrary faulty-domain tolerance, deployment or cryptographic validation established.')
 
 print(json.dumps(out))
if __name__=='__main__':main()
