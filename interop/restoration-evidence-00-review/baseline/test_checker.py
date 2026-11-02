"""Locally authored boundary and precedence controls; not upstream vectors."""
import copy
import hashlib
import json
import unittest
from checker import BASE, TYPES, SLOTS, REGISTRY, Reader, bundle, acyclic

def raw(s):
    return json.dumps(s, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def common():
    return {"incident": {"issuer": "https://example.org/incidents", "id": "own-1"},
            "producer": {"id": "https://example.org/producer"},
            "issuedAt": "2026-11-02T00:00:00Z", "registryDigest": {"sha256": REGISTRY},
            "doesNotAssert": ["Safety of resuming is not established."]}

def statement(kind, additions):
    return {"_type": "https://in-toto.io/Statement/v1", "subject": [{"digest": {"sha256": "0"*64}}],
            "predicateType": BASE + TYPES[kind], "predicate": {**common(), **additions}}

def ref(s):
    return {"predicateType": s["predicateType"], "digest": {"sha256": hashlib.sha256(raw(s)).hexdigest()}}

def r1():
    return statement(0, {"action": {"functions": ["restriction"], "targets": [{"id": "cred-a"}],
                         "inducedEffects": {"declared": "unknown"}},
            "parties": [{"id": "operator", "roles": ["accountable", "authorized"], "authorityBasis": "unknown"}],
            "authorizedAt": "2026-11-02T00:00:00Z", "notAfter": "2026-11-02T00:00:00Z",
            "intentBinding": "asserted_after_execution"})

def r2(previous):
    return statement(1, {"predecessors": [ref(previous)], "population": {"credentials": ["cred-a"]},
            "partition": [{"state": "retained", "credentials": ["cred-a"]}], "revocations": [],
            "coverage": {"claim": "partial"}})

def r3(previous):
    return statement(2, {"predecessors": [ref(previous)],
            "restoration": {"decision": "resume_staged", "restoredScope": {
                "agents": [], "tools": [], "routes": [], "credentials": ["cred-a"]}},
            "approvers": [{"id": "operator", "roles": ["authorized"], "independenceBasis": "subject_supplied"}],
            "setSufficiency": "insufficient", "evidence": {k: {"notAddressed": "Not collected."} for k in SLOTS}})

def r4():
    return statement(3, {"sharedIndicators": [{"sha256": "0"*64}],
            "parties": [{"id": p, "organization": p, "correlationId": "own", "assets": ["a"], "authorityBasis": "unknown"}
                        for p in ("one", "two")]})

def rb():
    return statement(4, {"sink": {"id": "s", "kind": "database", "commitBoundary": "COMMIT"},
            "observer": {"id": "o", "vantage": "sink_side"},
            "revocation": {"credential": "c", "effectiveAt": "2026-11-02T00:00:00Z", "timeSource": "test"},
            "window": {"start": "2026-11-02T00:00:00Z", "end": "2026-11-02T00:00:00Z"},
            "counts": {"attempts": 1, "inFlightAtRevocation": 1, "postRevocationCommits": 0,
                       "replaysAttempted": 0, "replaysCommitted": 0},
            "exclusions": [], "result": "no_post_revocation_commit_observed"})

class Controls(unittest.TestCase):
    def reason(self, record, expected, mode="draft"):
        self.assertEqual(Reader(mode).record(raw(record))["reason"], expected)

    def chain(self):
        a = r1()
        b = r2(a)
        c = r3(b)
        return a, b, c

    def test_five_controls(self):
        a, b, c = self.chain()
        for value in (a, b, c, r4(), rb()):
            with self.subTest(predicate=value["predicateType"]):
                self.assertEqual(Reader().record(raw(value))["verdict"], "accept")

    def test_b7_is_membership_not_successful_revocation_or_admission(self):
        self.assertEqual(bundle([raw(x) for x in self.chain()]),
                         {"verdict": "accept", "reason": "bundle-consistent"})

    def test_first_reason_not_last_r1(self):
        s = r1()
        s["predicate"]["parties"][0]["roles"] = ["executed"]
        s["predicate"]["authorizedAt"] = "2026-11-03T00:00:00Z"
        self.reason(s, "no-authorizer")

    def test_shape_precedes_vocabulary(self):
        s = rb()
        s["predicate"]["sink"]["kind"] = "unregistered"
        s["predicate"]["counts"]["attempts"] = True
        self.reason(s, "predicate-malformed")

    def test_draft_profile_source_conflict_rb(self):
        s = rb()
        s["predicate"]["sink"]["kind"] = "unregistered"
        self.reason(s, "closed-vocabulary-violation")
        self.reason(s, "predicate-malformed", "profile")

    def test_draft_profile_source_conflict_r4(self):
        s = r4()
        s["predicate"]["parties"][0]["authorityBasis"] = "unregistered"
        self.reason(s, "closed-vocabulary-violation")
        self.reason(s, "predicate-malformed", "profile")

    def test_duplicate_decoded_keys(self):
        data = raw(r1()).replace(b'"id":"own-1"', b'"id":"own-1","\\u0069d":"other"')
        self.assertEqual(Reader().record(data)["reason"], "statement-malformed")

    def test_unknown_nested_key(self):
        s = rb()
        s["predicate"]["counts"]["extra"] = 0
        self.reason(s, "predicate-malformed")

    def test_invalid_calendar_date(self):
        s = rb()
        s["predicate"]["issuedAt"] = "2026-02-30T00:00:00Z"
        self.reason(s, "predicate-malformed")

    def test_authorization_equal_boundaries(self):
        s = r1()
        s["predicate"]["executedAt"] = s["predicate"]["authorizedAt"]
        s["predicate"]["intentBinding"] = "committed_before_execution"
        self.reason(s, "authorization-recorded")

    def test_evidence_missing_precedes_unexplained_and_no_approver(self):
        s = r3(r1())
        del s["predicate"]["evidence"]["persistence"]
        s["predicate"]["evidence"]["rootCause"] = {"notAddressed": ""}
        s["predicate"]["approvers"] = []
        self.reason(s, "evidence-slot-missing")

    def test_evidence_empty_precedes_no_approver(self):
        s = r3(r1())
        s["predicate"]["evidence"]["rootCause"] = {"notAddressed": ""}
        s["predicate"]["approvers"] = []
        self.reason(s, "evidence-slot-unexplained")

    def test_late_rule_authority_basis_not_swallowed_by_shape(self):
        s = r4()
        del s["predicate"]["parties"][0]["authorityBasis"]
        self.reason(s, "authority-basis-missing")

    def test_observation_reason_not_swallowed_by_shape(self):
        s = r1()
        s["predicate"]["action"]["inducedEffects"] = {"declared": "none_observed"}
        self.reason(s, "induced-effects-unobserved")

    def test_partition_overlap_precedes_revocation_mismatch(self):
        a, s, _ = self.chain()
        s["predicate"]["partition"].append({"state": "revoked", "credentials": ["cred-a"]})
        self.reason(s, "denominator-union-mismatch")

    def test_graph_self_cycle(self):
        self.assertFalse(acyclic([[0]]))

    def test_graph_indirect_cycle(self):
        self.assertFalse(acyclic([[1], [2], [0]]))

    def test_graph_diamond_dag(self):
        self.assertTrue(acyclic([[1, 2], [3], [3], []]))

    def test_b1_precedes_unresolved(self):
        a, b, c = self.chain()
        del b["predicate"]["producer"]
        self.assertEqual(bundle([raw(x) for x in (a, b, c)])["reason"], "predicate-malformed")

    def test_b2_precedes_incident_mismatch(self):
        a, b, c = self.chain()
        c["predicate"]["incident"]["id"] = "other"
        c["predicate"]["predecessors"][0]["digest"]["sha256"] = "f"*64
        self.assertEqual(bundle([raw(x) for x in (a, b, c)])["reason"], "predecessor-not-carried")

    def test_b2_duplicate_carried_bytes(self):
        a, b, c = self.chain()
        self.assertEqual(bundle([raw(x) for x in (a, a, b, c)])["reason"], "predecessor-not-carried")

    def test_b3_type_mismatch(self):
        a, b, c = self.chain()
        c["predicate"]["predecessors"][0]["predicateType"] = BASE + TYPES[0]
        self.assertEqual(bundle([raw(x) for x in (a, b, c)])["reason"], "predecessor-type-mismatch")

    def test_b5_precedes_b6(self):
        a = r1()
        a["predicate"]["incident"]["id"] = "other"
        a["predicate"]["issuedAt"] = "2026-11-03T00:00:00Z"
        b = r2(a)
        c = r3(b)
        self.assertEqual(bundle([raw(x) for x in (a, b, c)])["reason"], "incident-mismatch")

    def test_b6_precedes_b7(self):
        a = r1()
        a["predicate"]["issuedAt"] = "2026-11-03T00:00:00Z"
        b = r2(a)
        c = r3(b)
        c["predicate"]["restoration"]["restoredScope"]["credentials"] = ["other"]
        self.assertEqual(bundle([raw(x) for x in (a, b, c)])["reason"], "predecessor-issued-later")

    def test_b7_unswept(self):
        a, b, c = self.chain()
        c["predicate"]["restoration"]["restoredScope"]["credentials"] = ["other"]
        self.assertEqual(bundle([raw(x) for x in (a, b, c)])["reason"], "restored-credential-unswept")

    def test_byte_hash_not_reserialization(self):
        a, b, c = self.chain()
        self.assertEqual(bundle([raw(a) + b"\n", raw(b), raw(c)])["reason"], "predecessor-not-carried")

    def test_b5_related_common_pair(self):
        a = r1()
        b = r2(a)
        b["predicate"]["incident"] = {"issuer": "https://example.com/incidents", "id": "other",
            "related": [copy.deepcopy(a["predicate"]["incident"])]}
        c = r3(b)
        self.assertEqual(bundle([raw(x) for x in (a, b, c)])["reason"], "bundle-consistent")

    def test_listed_effects_do_not_require_sorting(self):
        s = r1()
        s["predicate"]["action"]["inducedEffects"] = {"declared": "listed", "items": ["z", "a"]}
        self.reason(s, "authorization-recorded")

    def test_partition_members_do_not_require_sorting(self):
        s = r2(r1())
        s["predicate"]["population"]["credentials"] = ["a", "z"]
        s["predicate"]["partition"][0]["credentials"] = ["z", "a"]
        self.reason(s, "sweep-recorded")

    def test_unsupported_registry_is_not_accept(self):
        s = rb()
        s["predicate"]["registryDigest"]["sha256"] = "1"*64
        self.assertEqual(Reader().record(raw(s))["verdict"], "unsupported")

if __name__ == "__main__":
    unittest.main()
