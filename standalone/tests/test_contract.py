"""Contract controls fixed in fixtures/MANUAL-EXPECTATIONS.md before runs.

The old implementation is used only for bounded differential regression tests;
it is not imported by the minimal installed component.
"""
import copy
import importlib.util
from itertools import combinations, product
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from witnessability_checker.common import (Budget, ComputeLimit, InvalidInput,
    InvalidCertificate, PinMismatch, Unsupported, canonical, digest)
from witnessability_checker.context import (SCHEMA_VERSION, SEMANTICS_VERSION,
    make_pins, validate_document, validate_expected, validate_policy)
from witnessability_checker.model import parse_model, validate_record
from witnessability_checker.validation import loads_strict
from witnessability_checker.analysis import evaluate_record, check_capability
from witnessability_checker.verify import verify_ambiguity

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures'
POLICY = {'id': 'declared-model', 'version': '1', 'acknowledged_assumptions': True}


def document(name='mixed'):
    return json.loads((FIXTURES / (name + '.model.json')).read_text())


def model_and_pins(name='mixed', record=None):
    doc = document(name)
    model = validate_document(doc, Budget())
    return doc, model, make_pins(doc, model, POLICY, record)


def certificate(model, record, pin_context, first='f'):
    return {'schema_version': SCHEMA_VERSION,
            'semantics_version': SEMANTICS_VERSION,
            'pins': copy.deepcopy(pin_context), 'record': list(record),
            'witnesses': [{'history': first, 'honest': ['0'], 'fault': []},
                          {'history': 't', 'honest': ['0'], 'fault': []}]}


def collision_certificate(doc, model, collision):
    r = collision['record']
    expected = make_pins(doc, model, POLICY, r)
    cert = {'schema_version': SCHEMA_VERSION, 'semantics_version': SEMANTICS_VERSION,
            'pins': expected, 'record': r, 'witnesses': [
                {'history': h, 'honest': honest, 'fault': fault}
                for h, honest, fault in zip(collision['histories'],
                    collision['honest_records'], collision['faults'])]}
    return r, expected, cert


class TinySemanticControls(unittest.TestCase):
    def test_all_four_record_outcomes_and_no_vacuous_true(self):
        _, m, _ = model_and_pins()
        expected = {'0': ('UNRESOLVED', ['f', 'g', 't']),
                    '1': ('TRUE', ['t']), '2': ('FALSE', ['g']),
                    '3': ('OUTSIDE_MODEL', []), 'outside': ('OUTSIDE_MODEL', [])}
        for atom, (verdict, compatible) in expected.items():
            with self.subTest(atom=atom):
                result = evaluate_record(m, [atom], Budget())
                self.assertEqual(result['verdict'], verdict)
                self.assertEqual(list(result['compatible_histories']), compatible)

    def test_record_true_with_global_capability_false(self):
        _, m, _ = model_and_pins()
        self.assertFalse(check_capability(m, Budget())['capability'])
        self.assertEqual(evaluate_record(m, ['1'], Budget())['verdict'], 'TRUE')

    def test_positive_capability_and_outside_record_are_separate(self):
        _, m, _ = model_and_pins('separated')
        result = check_capability(m, Budget())
        self.assertTrue(result['capability'])
        self.assertIsNone(result['collision'])
        self.assertEqual(evaluate_record(m, ['2'], Budget())['verdict'], 'OUTSIDE_MODEL')

    def test_negative_capability_witness_is_verified(self):
        for name in ('mixed', 'alternative-faults'):
            with self.subTest(model=name):
                doc, m, _ = model_and_pins(name)
                result = check_capability(m, Budget())
                self.assertFalse(result['capability'])
                r, expected, cert = collision_certificate(doc, m, result['collision'])
                self.assertTrue(verify_ambiguity(m, r, cert,
                    expected_pins=expected, budget=Budget()))
                self.assertEqual(evaluate_record(m, r, Budget())['verdict'], 'UNRESOLVED')

    def test_alternative_valid_witness_is_not_generator_order(self):
        _, m, expected = model_and_pins(record=['0'])
        for false_history in ('f', 'g'):
            self.assertTrue(verify_ambiguity(m, ['0'], certificate(m, ['0'], expected, false_history),
                expected_pins=expected, budget=Budget()))

    def test_invalid_witness_does_not_establish_determinacy(self):
        _, m, expected = model_and_pins(record=['0'])
        bad = certificate(m, ['0'], expected, first='t')
        with self.assertRaises(InvalidCertificate):
            verify_ambiguity(m, ['0'], bad, expected_pins=expected, budget=Budget())
        self.assertEqual(evaluate_record(m, ['0'], Budget())['verdict'], 'UNRESOLVED')
        self.assertTrue(verify_ambiguity(m, ['0'], certificate(m, ['0'], expected),
            expected_pins=expected, budget=Budget()))

    def test_fresh_verification_budget_pays_for_model_hashing(self):
        doc = document()
        parse_budget = Budget()
        m = validate_document(doc, parse_budget)
        expected = make_pins(doc, m, POLICY, ['0'])
        cert = certificate(m, ['0'], expected)
        previous = parse_budget.used
        operation_budget = Budget()
        self.assertTrue(verify_ambiguity(m, ['0'], cert, expected_pins=expected,
                                        budget=operation_budget))
        self.assertEqual(parse_budget.used, previous)
        self.assertGreaterEqual(operation_budget.used,
            (len(canonical(m.to_dict()).encode('utf-8')) + 63) // 64)
        with self.assertRaises(ComputeLimit):
            verify_ambiguity(m, ['0'], cert, expected_pins=expected,
                             budget=Budget(20))
        self.assertEqual(parse_budget.used, previous)

    def test_certificate_versions_and_semantic_failures(self):
        _, m, expected = model_and_pins(record=['0'])
        for key in ('schema_version', 'semantics_version'):
            cert = certificate(m, ['0'], expected)
            cert[key] = 'unknown'
            with self.assertRaises(Unsupported):
                verify_ambiguity(m, ['0'], cert, expected_pins=expected, budget=Budget())
        for field, value in (('history', 'missing'), ('honest', ['2']), ('fault', ['x'])):
            cert = certificate(m, ['0'], expected)
            cert['witnesses'][0][field] = value
            with self.subTest(field=field), self.assertRaises(InvalidCertificate):
                verify_ambiguity(m, ['0'], cert, expected_pins=expected, budget=Budget())

    def test_opposite_faults_and_joint_support(self):
        _, m, _ = model_and_pins('alternative-faults')
        self.assertEqual(evaluate_record(m, ['1','0'], Budget())['verdict'], 'UNRESOLVED')
        d = document('alternative-faults')['model']
        d['faults'] = [[]]
        d['joint'] = {'f': [['0','0'], ['1','1']], 't': [['0','1'], ['1','0']]}
        m = parse_model(d, Budget())
        self.assertTrue(check_capability(m, Budget())['capability'])
        self.assertEqual(evaluate_record(m, ['0','1'], Budget())['verdict'], 'TRUE')

    def test_constant_claim_still_requires_nonempty_compatibility(self):
        d = document('separated')['model']
        d['truth'] = {'f': True, 't': True}
        m = parse_model(d, Budget())
        self.assertTrue(check_capability(m, Budget())['capability'])
        self.assertEqual(evaluate_record(m, ['0'], Budget())['verdict'], 'TRUE')
        self.assertEqual(evaluate_record(m, ['2'], Budget())['verdict'], 'OUTSIDE_MODEL')


class ExternalPinControls(unittest.TestCase):
    def test_every_external_and_embedded_pin_is_checked(self):
        _, m, expected = model_and_pins(record=['0'])
        good = certificate(m, ['0'], expected)
        self.assertEqual(set(expected), {'model','claim','record','policy','context'})
        for key in expected:
            for location in ('external', 'embedded'):
                with self.subTest(key=key, location=location):
                    ex, cert = copy.deepcopy(expected), copy.deepcopy(good)
                    if location == 'external': ex[key] = '0' * 64
                    else: cert['pins'][key] = '0' * 64
                    with self.assertRaises(PinMismatch):
                        verify_ambiguity(m, ['0'], cert, expected_pins=ex, budget=Budget())

    def test_self_consistent_substitution_cannot_repin_external_context(self):
        _, old_model, original = model_and_pins(record=['0'])
        replacement = document()
        replacement['model']['name'] = 'substituted-name'
        replacement['model']['claim'] = 'different proposition'
        replacement['model']['alphabets'][0][0] = '4'
        for support in replacement['model']['joint'].values():
            for row in support:
                if row[0] == '0': row[0] = '4'
        m = validate_document(replacement, Budget())
        fresh = make_pins(replacement, m, POLICY, ['4'])
        cert = certificate(m, ['4'], fresh)
        for w in cert['witnesses']: w['honest'] = ['4']
        self.assertTrue(verify_ambiguity(m, ['4'], cert, expected_pins=fresh, budget=Budget()))
        with self.assertRaises(PinMismatch):
            verify_ambiguity(m, ['4'], cert, expected_pins=original, budget=Budget())

    def test_version_and_policy_identity_are_bound_in_context(self):
        doc, m, original = model_and_pins(record=['0'])
        for field in ('schema_version','semantics_version'):
            d = copy.deepcopy(doc); d[field] += '-changed'
            with self.assertRaises(Unsupported): validate_document(d, Budget())
        policy = dict(POLICY, acknowledged_assumptions=False)
        changed = make_pins(doc, m, policy, ['0'])
        self.assertNotEqual(changed['policy'], original['policy'])
        self.assertNotEqual(changed['context'], original['context'])
        for field in ('model','claim','record'):
            self.assertEqual(changed[field], original[field])
        self.assertEqual(set(make_pins(doc, m, POLICY)), {'model','claim','policy','context'})

    def test_legacy_canonical_encoder_and_pins_unchanged(self):
        doc, m, pins = model_and_pins(record=['0'])
        value = {'é':'😀', 'false': False, 'list': ['a', 3]}
        self.assertEqual(canonical(value), json.dumps(value, sort_keys=True,
            separators=(',', ':'), ensure_ascii=True, allow_nan=False))
        self.assertEqual(pins['model'], digest(m.to_dict()))
        self.assertEqual(pins['claim'], digest({'claim':m.claim,'truth':dict(m.truth)}))
        self.assertEqual(pins['record'], digest(['0']))


class StrictInputControls(unittest.TestCase):
    def test_duplicate_keys_at_multiple_depths(self):
        for data in (b'{"a":1,"a":2}', b'{"a":{"b":1,"b":2}}',
                     b'[{"a":[{"b":true,"b":false}]}]'):
            with self.subTest(data=data), self.assertRaises(InvalidInput):
                loads_strict(data, Budget())

    def test_json_utf8_numbers_trailing_and_depth(self):
        rejected = [b'{} {}', b'NaN', b'Infinity', b'-Infinity', b'1.5', b'1e3',
                    b'"\xff"', b'\xef\xbb\xbf{}', b'"\\ud800"', b'"\\udfff"',
                    b'1' * 5000, b'[' * 40 + b'0' + b']' * 40]
        for data in rejected:
            with self.subTest(data=data[:60]), self.assertRaises((InvalidInput, ComputeLimit)):
                loads_strict(data, Budget())
        self.assertEqual(loads_strict(b'"\\ud83d\\ude00"', Budget()), '😀')
        self.assertEqual(loads_strict('"привет"'.encode(), Budget()), 'привет')

    def test_no_unicode_normalization_or_string_coercion(self):
        nfc = document(); nfd = document()
        nfc['model']['name'] = '\u00e9'
        nfd['model']['name'] = 'e\u0301'
        a, b = validate_document(nfc, Budget()), validate_document(nfd, Budget())
        self.assertNotEqual(a.pin, b.pin)
        for bad in (0, 1, True, None, {}, []):
            d = document()['model']; d['name'] = bad
            with self.subTest(value=bad), self.assertRaises(InvalidInput):
                parse_model(d, Budget())

    def test_nested_model_types_and_fields(self):
        mutations = [
            lambda d: d.update(extra='x'),
            lambda d: d.pop('binding'),
            lambda d: d.update(histories='fgt'),
            lambda d: d['truth'].update(f=0),
            lambda d: d['truth'].pop('g'),
            lambda d: d['truth'].update(extra=True),
            lambda d: d.update(domains=[True]),
            lambda d: d.update(alphabets=['0123']),
            lambda d: d.update(alphabets=[[0,1,2,3]]),
            lambda d: d.update(joint=[]),
            lambda d: d['joint'].update(f=[]),
            lambda d: d['joint'].update(f=[['0','1']]),
            lambda d: d['joint'].update(f=[['unknown']]),
            lambda d: d['joint'].update(f=['0']),
            lambda d: d['joint'].pop('g'),
            lambda d: d.update(faults='x'),
            lambda d: d.update(faults=[[True]]),
        ]
        for i, change in enumerate(mutations):
            d = document()['model']; change(d)
            with self.subTest(mutation=i), self.assertRaises(InvalidInput):
                parse_model(d, Budget())
        d = document()['model']; d['binding'] = 'permutation'
        with self.assertRaises(Unsupported): parse_model(d, Budget())

    def test_no_silent_set_or_frozenset_deduplication(self):
        mutations = [
            lambda d: d['histories'].append('f'),
            lambda d: d['domains'].append('x'),
            lambda d: d['alphabets'][0].append('0'),
            lambda d: d['joint']['f'].append(['0']),
            lambda d: d['faults'].append([]),
        ]
        for i, change in enumerate(mutations):
            d = document()['model']; change(d)
            with self.subTest(mutation=i), self.assertRaises(InvalidInput):
                parse_model(d, Budget())

    def test_duplicate_domains_inside_fault_are_not_normalized(self):
        d = document('alternative-faults')['model']
        d['faults'].append(['a','a'])
        with self.assertRaises(InvalidInput): parse_model(d, Budget())

    def test_faults_empty_subset_downward_closure(self):
        for family in ([['a']], [[], ['a','b']], [[], ['unknown']]):
            d = document('alternative-faults')['model']; d['faults'] = family
            with self.subTest(faults=family), self.assertRaises(InvalidInput):
                parse_model(d, Budget())

    def test_document_policy_expected_and_record_shapes(self):
        for key in ('schema_version','semantics_version','model'):
            d=document(); del d[key]
            with self.assertRaises(InvalidInput): validate_document(d, Budget())
        d=document(); d['extra']=True
        with self.assertRaises(InvalidInput): validate_document(d, Budget())
        for key in ('id','version'):
            d=dict(POLICY); d[key]='unknown'
            with self.assertRaises(Unsupported): validate_policy(d, Budget())
        for bad in (0,1,'true',None,[]):
            d=dict(POLICY, acknowledged_assumptions=bad)
            with self.assertRaises(InvalidInput): validate_policy(d, Budget())
        self.assertEqual(validate_policy(dict(POLICY,acknowledged_assumptions=False),Budget())['acknowledged_assumptions'],False)
        _,m,expected=model_and_pins(record=['0'])
        for bad in ({},dict(expected,extra='0'*64),dict(expected,model=True),dict(expected,model='abc'),dict(expected,model='A'*64)):
            with self.assertRaises(InvalidInput): validate_expected(bad,True,Budget())
        for bad in ('0',[],['0','1'],[True],[0],None):
            with self.assertRaises(InvalidInput): validate_record(m,bad,Budget())

    def test_certificate_nested_shape_and_duplicate_fault_elements(self):
        _,m,expected=model_and_pins(record=['0'])
        mutations=[lambda c:c.update(extra=True), lambda c:c['pins'].update(extra='0'*64),
          lambda c:c['witnesses'][0].update(extra=True),
          lambda c:c['witnesses'][0].update(honest='0'),
          lambda c:c['witnesses'][0].update(fault=['x','x']),
          lambda c:c['witnesses'][0].update(history=True)]
        for i,change in enumerate(mutations):
            c=certificate(m,['0'],expected);change(c)
            with self.subTest(mutation=i),self.assertRaises(InvalidInput):
                verify_ambiguity(m,['0'],c,expected_pins=expected,budget=Budget())

    def test_validation_and_algorithms_consume_budgets(self):
        _,m,expected=model_and_pins(record=['0'])
        operations=[lambda:loads_strict(b'{"several":[1,2,3]}',Budget(1)),
                    lambda:parse_model(document()['model'],Budget(1)),
                    lambda:evaluate_record(m,['0'],Budget(1)),
                    lambda:check_capability(m,Budget(1)),
                    lambda:verify_ambiguity(m,['0'],certificate(m,['0'],expected),expected_pins=expected,budget=Budget(1))]
        for i,operation in enumerate(operations):
            with self.subTest(operation=i),self.assertRaises(ComputeLimit):operation()
        with self.assertRaises((InvalidInput,ComputeLimit)):
            loads_strict(b' ' * (2*1024*1024+1),Budget())
        for bad in (True,False,0,-1,2.5,'10'):
            with self.subTest(budget=bad),self.assertRaises(InvalidInput):Budget(bad)


class BoundedLegacyConsistency(unittest.TestCase):
    def test_original_1125_cases_against_pinned_legacy(self):
        old_file=Path(__file__).resolve().parents[2]/'src/witnessability_research/finite.py'
        self.assertTrue(old_file.is_file(), 'run this source regression from patched source tree')
        spec=importlib.util.spec_from_file_location('_pinned_legacy_finite',old_file)
        old=importlib.util.module_from_spec(spec);sys.modules[spec.name]=old;spec.loader.exec_module(old)
        records=tuple(product(('0','1'),repeat=2))
        supports=tuple(s for size in range(1,5) for s in combinations(records,size))
        families=(((),),((),('a',)),((),('b',)),((),('a',),('b',)),((),('a',),('b',),('a','b')))
        checked=0
        for left,right,faults in product(supports,supports,families):
            legacy=old.FiniteModel('test','binary-claim',('f','t'),{'f':False,'t':True},('a','b'),(('0','1'),('0','1')),{'f':left,'t':right},faults)
            doc={'schema_version':SCHEMA_VERSION,'semantics_version':SEMANTICS_VERSION,'model':legacy.to_dict()}
            m=validate_document(doc,Budget())
            self.assertEqual(m.pin,legacy.pin)
            self.assertEqual(m.claim_pin,legacy.claim_pin)
            actual=check_capability(m,Budget())
            collision=old.enumerate_exposure(legacy,'f') & old.enumerate_exposure(legacy,'t')
            self.assertEqual(actual['capability'],not collision)
            for r in records:
                result=evaluate_record(m,r,Budget())
                self.assertEqual(result['verdict'],old.judge_direct(legacy,r))
                self.assertEqual(list(result['compatible_histories']),list(old.compatible_direct(legacy,r)))
            if not actual['capability']:
                r,ex,cert=collision_certificate(doc,m,actual['collision'])
                self.assertTrue(verify_ambiguity(m,r,cert,expected_pins=ex,budget=Budget()))
            checked+=1
        self.assertEqual(checked,1125)


if __name__=='__main__': unittest.main()
