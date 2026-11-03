"""Offline receiver-boundary control; run with Python 3.11+ (stdlib only)."""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import sys
from finite_oracle import evaluate

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'vendor/vate'))
import rb_receiving as rb

def raw(v):
    return (json.dumps(v, sort_keys=True, separators=(',', ':')) + '\n').encode()

def check(ok, label):
    if not ok:
        raise RuntimeError(label)

def fixture():
    # Reuse only a well-formed producer record; the receiver evidence is new.
    corpus = json.loads((ROOT/'sources/corpus-inputs.json').read_text())
    s = json.loads(corpus['vectors-restart-records/cases/revocation-boundary-accept-not-established/statement.json'])
    p = s['predicate']
    p['incident']['id'] = 'rb-positive-partial-independent-001'
    p['sink'] = {'id':'urn:rb-control:first-file','kind':'filesystem',
                 'commitBoundary':'successful fsync return for first.txt; no directory durability claim'}
    p['window'] = {'start':time(0), 'end':time(5)}
    p['revocation'] = {'credential':'urn:rb-control:credential', 'effectiveAt':time(1),
                       'timeSource':'urn:rb-control:synthetic-clock'}
    p['issuedAt'] = time(6)
    p['observer'] = {'id':'urn:rb-control:observer','vantage':'sink_side'}
    p['counts'] = dict(attempts=2,inFlightAtRevocation=2,postRevocationCommits=2,
                       replaysAttempted=0,replaysCommitted=0)
    p['result'] = 'not_established'
    p['exclusions'] = []
    plan = raw({'sink':p['sink'],'window':p['window']})
    s['subject'] = [{'digest':{'sha256':hashlib.sha256(plan).hexdigest()}}]
    context = {k:deepcopy(p[k]) for k in ('incident','producer','sink','observer','revocation','window')}
    context.update(test_plan_sha256=hashlib.sha256(plan).hexdigest(),registry_sha256=p['registryDigest']['sha256'])
    selection = {'profile':'vate-local-rb-selection-v1','receiver_id':'urn:rb-control:receiver','expected':context}
    observation = {'profile':'vate-local-rb-observation-v1','statement_sha256':hashlib.sha256(raw(s)).hexdigest(),
       'context':deepcopy(context),'collection':'partial','exclusions':[],
       'attempts':[{'id':'visible-1','kind':'initial','replay_of':None,'started_at':time(0),
                    'finished_at':time(3),'commit_state':'committed','committed_at':time(2)}]}
    return s,selection,plan,observation

def time(n):
    return '2026-11-03T00:00:%02dZ' % n

def run():
    for name, expected in json.loads((ROOT/'SOURCE-HASHES.json').read_text()).items():
        check(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected, 'source changed: '+name)
    s,sel,plan,o = fixture()
    manifest=json.loads((ROOT/'sources/MANIFEST.upstream.json').read_text())
    corpus=json.loads((ROOT/'sources/corpus-inputs.json').read_text())
    check(len(manifest['vectors'])==57,'unexpected corpus membership')
    for vector in manifest['vectors']:
        for filename,expected in vector['files'].items():
            source=corpus['vectors-restart-records/'+vector['path']+'/'+filename].encode()
            check(hashlib.sha256(source).hexdigest()==expected,'corpus member hash')
            check(json.loads(source)!=s,'new statement duplicates corpus member')
    check(all('observation.json' not in v['files'] for v in manifest['vectors']), 'receiver observation already in corpus')
    results = {}
    out = ROOT/'results';out.mkdir(exist_ok=True)
    def assess(name, statement=s, selection=sel, observation=o):
        data={'statement':raw(statement),'selection':raw(selection),'test_plan':plan,
              'observation':None if observation is None else raw(observation)}
        before=deepcopy(data)
        report=rb.assess(**data)
        check(data==before,'input mutation')
        folder=out/name;folder.mkdir(exist_ok=True)
        for key,b in data.items():
            if b is not None:(folder/(key+'.json')).write_bytes(b)
        (folder/'report.json').write_bytes(raw(report))
        for key in ('signature_verification','issuer_authority','evidence_sufficiency','permission_to_resume'):
            check(report[key]['status']=='not_assessed',name+': inflated '+key)
        results[name]=report
        return report
    absent=assess('01-no-observation',observation=None)
    positive=assess('02-partial-positive')
    oc=positive['observation_check']
    check(positive['record_check']['status']=='passed','RB syntax')
    check(positive['declared']['result']=='not_established','producer result rewritten')
    check(oc['observed_positive'] is True and oc['derived_counts'] is None and
          oc['derived_result']=='post_revocation_commit_observed' and oc['status']=='not_established','positive lost or count invented')
    check(absent['inputs']['statement']==positive['inputs']['statement'],'successive readings changed statement')
    empty=deepcopy(o);empty['attempts']=[]
    e=assess('03-partial-empty',observation=empty)['observation_check']
    check(e['observed_positive'] is False and e['derived_result']=='not_established' and e['derived_counts'] is None,'absence promoted')
    zero=deepcopy(s);zero['predicate']['counts']['postRevocationCommits']=0
    zo=deepcopy(o);zo['statement_sha256']=hashlib.sha256(raw(zero)).hexdigest()
    z=assess('04-unknown-result-zero-count',statement=zero,observation=zo)
    check(z['record_check']['status']=='passed' and z['declared']['result']=='not_established' and
          z['observation_check']['status']=='contradiction','unknown result hid false zero')
    tied=deepcopy(o);tied['attempts'][0]['committed_at']=time(1)
    t=assess('05-time-tie',observation=tied)['observation_check']
    check(t['observed_positive'] is False and t['derived_result']=='not_established','tie promoted to after')
    wrong=deepcopy(sel);wrong['expected']['sink']['id']='urn:rb-control:other-sink'
    w=assess('06-wrong-receiver-target',selection=wrong)
    check(w['receiver_binding']['status']=='mismatch' and w['observation_check']['observed_positive'] is True,'binding dimensions collapsed')
    unbound=deepcopy(o);unbound['statement_sha256']='0'*64
    u=assess('07-unbound-observation',observation=unbound)['observation_check']
    check(u['status']=='mismatch' and u['observed_positive'] is None,'unbound event admitted')
    a={'id':'visible-1','start':0,'finish':3,'commit':2}
    b={'id':'hidden-2','start':0,'finish':4,'commit':3}
    histories=[[a],[a,b]]
    oracle=evaluate(histories, {'visible-1'})
    check(oracle['positive_in_every_history'] and not oracle['exact_count_established'] and
          oracle['compatible_counts']==[1,2], 'finite witness failure')
    empty_oracle=evaluate([[],[b]],set())
    check(not empty_oracle['positive_in_every_history'] and not empty_oracle['zero_in_every_history'],'empty ambiguity lost')
    (out/'histories.json').write_bytes(raw({'positive':histories,'empty':[[],[b]]}))
    summary={'status':'PASS','receiver_readings':len(results),'reviewed_corpus_cases':57,'finite_oracle':oracle,'empty_oracle':empty_oracle,
       'source_statement_sha256':hashlib.sha256(raw(s)).hexdigest(),
       'limits':'Synthetic assertion-level replay, not live fsync, independent time, DSSE verification, completeness proof or restart approval.'}
    (out/'SUMMARY.json').write_bytes(raw(summary));print(json.dumps(summary,indent=2))

if __name__=='__main__':run()
