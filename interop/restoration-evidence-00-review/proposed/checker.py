"""Independent unsigned Restoration Evidence rule checker, candidate 0.1.
NOT a DSSE verifier, admission engine, or full draft conformance implementation.
See INTERPRETATIONS.md before interpreting accept or comparing reason codes.
Python 3.12+; standard library only. No upstream checker/generator imports.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

BASE = "https://probityai.github.io/agent-evidence-vectors/predicate/v1/"
TYPES = ("incident-action-authorization", "revocation-sweep",
         "re-enable-decision", "joint-authority", "revocation-boundary")
REGISTRY = "1c5ff80bd97237a603afc402db692ffe5abe15e4a7f9eca13f20068ada347fdc"
SLOTS = ("actorObjective persistence rootCause affectedScope assetIntegrity "
         "restoredAssetsClean containmentReproof incidentReplay restoreOrder "
         "postRestartMonitoring exclusiveControl controlsNotDegraded residualRisk "
         "seniorApproval multiPartyAuthorization ownerConfirmation").split()
ACCEPT = ("authorization-recorded", "sweep-recorded", "decision-recorded",
          "assignment-recorded", "boundary-recorded")
ROLES = "accountable advised authorized executed"
AUTH = "contract_third_party executive_approval policy_preauthorized role_grant unknown"
INDEPENDENCE = "independent_sources subject_supplied undeclared"

class ShapeError(ValueError):
    pass

def require(ok):
    if not ok:
        raise ShapeError("shape")

def pairs(items):
    out = {}
    for key, value in items:
        if key in out:
            raise ShapeError("duplicate-member")
        out[key] = value
    return out

def strict(raw):
    def bad_constant(value):
        raise ShapeError("non-finite-number")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                       parse_constant=bad_constant)
    def walk(x, depth=0):
        require(depth <= 128)
        if isinstance(x, str):
            require(not any(0xD800 <= ord(c) <= 0xDFFF for c in x))
        elif isinstance(x, dict):
            for k, v in x.items():
                walk(k, depth + 1)
                walk(v, depth + 1)
        elif isinstance(x, list):
            for v in x:
                walk(v, depth + 1)
        elif type(x) is int:
            require(abs(x) <= 9007199254740991)
        elif type(x) is float:
            # This record language has no floating-point members.
            raise ShapeError("unsupported-number")
    walk(value)
    return value

def text(x):
    return isinstance(x, str) and len(x) > 0

def https(x):
    return text(x) and re.fullmatch(r"https://[^\s]+", x) is not None

def digest(x):
    return (isinstance(x, dict) and set(x) == {"sha256"}
            and isinstance(x["sha256"], str)
            and re.fullmatch("[0-9a-f]{64}", x["sha256"]) is not None)

def timestamp(x):
    if not isinstance(x, str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", x):
        return False
    try:
        dt.datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except ValueError:
        return False

def integer(x):
    return type(x) is int and 0 <= x <= 9007199254740991

def array(check, minimum=0, sorted_unique=False, unique=False):
    def validate(x):
        return (isinstance(x, list) and len(x) >= minimum and all(check(v) for v in x)
                and (not sorted_unique or x == sorted(set(x)))
                and (not unique or len(x) == len(set(x))))
    return validate

def obj(x, required, optional=None):
    optional = optional or {}
    require(isinstance(x, dict))
    require(set(required) <= set(x) <= set(required) | set(optional))
    for key, check in {**required, **optional}.items():
        if key in x:
            require(check(x[key]))
    return True

def resource(x):
    return obj(x, {"digest": digest}, {"uri": text, "mediaType": text})

def identity(x):
    return obj(x, {"issuer": https, "id": text})

def incident(x):
    return obj(x, {"issuer": https, "id": text}, {"related": array(identity)})

def reference(x):
    return obj(x, {"predicateType": https, "digest": digest})

def result(code, verdict="reject"):
    return {"verdict": verdict, "reason": code}

class Reader:
    def __init__(self, vocabulary_mode="profile"):
        if vocabulary_mode not in ("draft", "profile"):
            raise ValueError("unknown vocabulary mode")
        self.mode = vocabulary_mode
        self.closed_errors = []

    def enum(self, values, registered=False):
        allowed = values.split()
        def check(x):
            if not isinstance(x, str):
                return False
            if x not in allowed:
                if registered or self.mode == "draft":
                    self.closed_errors.append(x)
                else:
                    return False
            return True
        return check

    def roles(self):
        return array(self.enum(ROLES), 1, True)

    def party(self, x):
        return obj(x, {"id": text, "roles": self.roles()},
                   {"authorityBasis": self.enum(AUTH),
                    "independenceBasis": self.enum(INDEPENDENCE, True)})

    def approver(self, x):
        return obj(x, {"id": text, "roles": self.roles(),
                       "independenceBasis": self.enum(INDEPENDENCE, True)})

    def effects(self, x):
        require(isinstance(x, dict))
        declared = x.get("declared")
        fields = {"listed": {"items": array(text, 1, unique=True)},
                  "none_observed": {}, "unknown": {}}
        if declared not in fields:
            # Unknown discriminant: field names and field types still checked.
            return obj(x, {"declared": self.enum("listed none_observed unknown")},
                       {"items": array(text, 1, unique=True), "observation": digest})
        optional = {"observation": digest} if declared == "none_observed" else {}
        return obj(x, {"declared": self.enum("listed none_observed unknown"),
                       **fields[declared]}, optional)

    def evidence(self, x):
        require(isinstance(x, dict))
        # Keys and non-empty explanations deliberately deferred to R3.4/.5.
        for value in x.values():
            if isinstance(value, dict) and "notAddressed" in value:
                obj(value, {"notAddressed": lambda v: isinstance(v, str)})
            else:
                resource(value)
        return True

    def shape(self, kind, p):
        common = {"incident": incident, "producer": lambda x: obj(x, {"id": https}),
                  "issuedAt": timestamp, "registryDigest": digest,
                  "doesNotAssert": array(text)}
        opt = {}
        if kind == TYPES[0]:
            extra = {
                "action": lambda x: obj(x, {
                    "functions": array(self.enum("isolation monitoring_increase pause remediation restoration restriction", True), 1, True),
                    "targets": array(lambda y: obj(y, {"id": text}), 1),
                    "inducedEffects": self.effects}),
                "parties": array(self.party, 1),
                "authorizedAt": timestamp, "notAfter": timestamp,
                "intentBinding": self.enum("asserted_after_execution committed_before_execution", True)}
            opt = {"executedAt": timestamp,
                   "pause": lambda x: obj(x, {
                       "hold": self.enum("effect_after_pause held in_flight_unknown not_established residual_state_remains", True),
                       "holdProof": digest})}
        elif kind == TYPES[1]:
            extra = {
                "predecessors": array(reference, 1),
                "population": lambda x: obj(x, {"credentials": array(text, 1, True)}),
                "partition": array(lambda x: obj(x, {
                    "state": self.enum("retained revoked unassessed"),
                    "credentials": array(text, 1, unique=True)}), 1),
                "revocations": array(lambda x: obj(x, {
                    "credential": text, "revokedAt": timestamp, "evidence": resource,
                    "relyingParties": array(lambda y: obj(y, {
                        "id": text, "state": self.enum("enforced_observed issued not_established use_after_revocation", True)}))})),
                "coverage": lambda x: obj(x, {
                    "claim": self.enum("complete_verified issued_after_only partial unknown")},
                    {"issuedAfter": timestamp})}
        elif kind == TYPES[2]:
            scope = lambda x: obj(x, {k: array(text, 0, True) for k in ("agents", "tools", "routes", "credentials")})
            extra = {
                "predecessors": array(reference, 1),
                "restoration": lambda x: obj(x, {
                    "decision": self.enum("resume_full resume_staged remain_restricted not_established", True)},
                    {"restoredScope": scope}),
                "approvers": array(self.approver),
                "setSufficiency": self.enum("sufficient insufficient not_assessed", True),
                "evidence": self.evidence}
        elif kind == TYPES[3]:
            extra = {
                "sharedIndicators": array(digest, 1),
                "parties": array(lambda x: obj(x, {
                    "id": text, "organization": text, "correlationId": text,
                    "assets": array(text, 0, True)},
                    {"authorityBasis": self.enum(AUTH)}), 2)}
            opt = {"actions": array(lambda x: obj(x, {
                "party": text, "asset": text, "record": digest}))}
        else:
            extra = {
                "sink": lambda x: obj(x, {"id": text,
                    "kind": self.enum("database filesystem http_endpoint subprocess queue other"),
                    "commitBoundary": text}),
                "observer": lambda x: obj(x, {"id": text, "vantage": self.enum("sink_side agent_side")}),
                "revocation": lambda x: obj(x, {"credential": text, "effectiveAt": timestamp, "timeSource": text}),
                "window": lambda x: obj(x, {"start": timestamp, "end": timestamp}),
                "counts": lambda x: obj(x, {k: integer for k in (
                    "attempts", "inFlightAtRevocation", "postRevocationCommits", "replaysAttempted", "replaysCommitted")}),
                "exclusions": array(lambda x: obj(x, {"count": integer, "reason": text})),
                "result": self.enum("no_post_revocation_commit_observed post_revocation_commit_observed not_established")}
            opt = {"predecessors": array(reference, 1)}
        obj(p, {**common, **extra}, opt)
        if kind == TYPES[3]:
            values = [x["sha256"] for x in p["sharedIndicators"]]
            require(values == sorted(values))
        if kind == TYPES[1]:
            require(any(x["predicateType"] == BASE + TYPES[0] for x in p["predecessors"]))
        if kind == TYPES[2]:
            require(all(x["predicateType"] in [BASE + t for t in TYPES] for x in p["predecessors"]))

    def record(self, raw):
        self.closed_errors = []
        try:
            s = strict(raw)
            obj(s, {"_type": lambda x: x == "https://in-toto.io/Statement/v1",
                    "predicateType": lambda x: x in [BASE + t for t in TYPES],
                    "subject": array(lambda x: obj(x, {"digest": digest}, {"name": text}), 1),
                    "predicate": lambda x: True})
            kind = s["predicateType"][len(BASE):]
            if kind in (TYPES[1], TYPES[3], TYPES[4]):
                require(len(s["subject"]) == 1)
        except (ValueError, TypeError, UnicodeError, RecursionError):
            return result("statement-malformed")
        p = s["predicate"]
        try:
            self.shape(kind, p)
        except (ValueError, TypeError, KeyError, RecursionError):
            return result("predicate-malformed")
        if self.closed_errors:
            return result("closed-vocabulary-violation")
        # An unknown registry is not silently treated as the pinned registry.
        if p["registryDigest"]["sha256"] != REGISTRY:
            return result("unsupported-registry", "unsupported")
        checks = []
        if kind == TYPES[0]:
            parties = p["parties"]
            checks = [
                (any("authorized" in x["roles"] for x in parties), "no-authorizer"),
                (any("accountable" in x["roles"] for x in parties), "no-accountable-party"),
                (all("authorityBasis" in x for x in parties if "authorized" in x["roles"]), "authority-basis-missing"),
                (p["authorizedAt"] <= p["notAfter"], "authorization-window-inverted"),
                (p["intentBinding"] != "committed_before_execution" or "executedAt" not in p or p["executedAt"] >= p["authorizedAt"], "intent-not-committed-before"),
                ("executedAt" not in p or p["executedAt"] <= p["notAfter"], "authorization-expired"),
                (p["action"]["inducedEffects"]["declared"] != "none_observed" or "observation" in p["action"]["inducedEffects"], "induced-effects-unobserved")]
        elif kind == TYPES[1]:
            pop = set(p["population"]["credentials"])
            parts = [c for x in p["partition"] for c in x["credentials"]]
            revoked = {c for x in p["partition"] if x["state"] == "revoked" for c in x["credentials"]}
            entries = [x["credential"] for x in p["revocations"]]
            checks = [
                (len(parts) == len(set(parts)) and set(parts) == pop, "denominator-union-mismatch"),
                (len(entries) == len(set(entries)) and set(entries) == revoked, "revocation-entries-mismatch"),
                (p["coverage"]["claim"] != "complete_verified" or revoked == pop, "coverage-claim-exceeds-proof"),
                (p["coverage"]["claim"] != "issued_after_only" or "issuedAfter" in p["coverage"], "coverage-claim-incomplete")]
        elif kind == TYPES[2]:
            scope = p["restoration"].get("restoredScope")
            checks = [
                (set(p["evidence"]) == set(SLOTS), "evidence-slot-missing"),
                (all(text(x["notAddressed"]) for x in p["evidence"].values() if "notAddressed" in x), "evidence-slot-unexplained"),
                (any("authorized" in x["roles"] for x in p["approvers"]), "no-approver"),
                (p["restoration"]["decision"] != "resume_staged" or (scope is not None and any(scope.values())), "partial-without-scope"),
                (p["restoration"]["decision"] != "resume_full" or scope is None, "full-with-scope")]
        elif kind == TYPES[3]:
            checks = [
                (all("authorityBasis" in x for x in p["parties"]), "authority-basis-missing"),
                (len({x["organization"] for x in p["parties"]}) >= 2, "single-organization"),
                (all(any(a["party"] == x["id"] and a["asset"] in x["assets"] for x in p["parties"]) for a in p.get("actions", [])), "party-acts-outside-assignment")]
        else:
            c = p["counts"]
            positive = c["postRevocationCommits"] > 0 or c["replaysCommitted"] > 0
            checks = [
                (p["window"]["start"] <= p["revocation"]["effectiveAt"] <= p["window"]["end"], "revocation-outside-window"),
                (c["inFlightAtRevocation"] <= c["attempts"] and c["postRevocationCommits"] <= c["inFlightAtRevocation"] and c["replaysCommitted"] <= c["replaysAttempted"], "counts-inconsistent"),
                (p["result"] == "not_established" or (p["result"] == "post_revocation_commit_observed") == positive, "result-contradicts-counts"),
                (p["result"] != "no_post_revocation_commit_observed" or p["observer"]["vantage"] == "sink_side", "observer-not-at-sink")]
        for passed, code in checks:
            if not passed:
                return result(code)
        return result(ACCEPT[TYPES.index(kind)], "accept")

def acyclic(edges):
    # Kahn's algorithm; deliberately independently unit-testable.
    incoming = [0] * len(edges)
    for refs in edges:
        for j in refs:
            incoming[j] += 1
    queue = [i for i, n in enumerate(incoming) if n == 0]
    seen = 0
    while queue:
        i = queue.pop()
        seen += 1
        for j in edges[i]:
            incoming[j] -= 1
            if incoming[j] == 0:
                queue.append(j)
    return seen == len(edges)

def bundle(raw_records, mode="profile"):
    if not raw_records:
        return result("input-empty-bundle", "input-error")
    reader = Reader(mode)
    records = []
    for raw in raw_records:  # Explicit B1 tie-break: caller's order.
        verdict = reader.record(raw)
        if verdict["verdict"] != "accept":
            return verdict
        records.append(strict(raw))
    by_hash = {}
    for i, raw in enumerate(raw_records):
        by_hash.setdefault(hashlib.sha256(raw).hexdigest(), []).append(i)
    refs = [s["predicate"].get("predecessors", []) for s in records]
    if any(len(by_hash.get(r["digest"]["sha256"], [])) != 1 for rs in refs for r in rs):
        return result("predecessor-not-carried")
    edges = [[by_hash[r["digest"]["sha256"]][0] for r in rs] for rs in refs]
    if any(records[j]["predicateType"] != r["predicateType"]
           for rs, js in zip(refs, edges) for r, j in zip(rs, js)):
        return result("predecessor-type-mismatch")
    if not acyclic(edges):
        return result("predecessor-cycle")
    incident_sets = []
    for s in records:
        inc = s["predicate"]["incident"]
        incident_sets.append({(x["issuer"], x["id"]) for x in [inc] + inc.get("related", [])})
    if not set.intersection(*incident_sets):
        return result("incident-mismatch")
    if any(records[i]["predicate"]["issuedAt"] < records[j]["predicate"]["issuedAt"]
           for i, js in enumerate(edges) for j in js):
        return result("predecessor-issued-later")
    credentials = {c for s in records if s["predicateType"] == BASE + TYPES[1]
                   for c in s["predicate"]["population"]["credentials"]}
    roots = [i for i, s in enumerate(records) if s["predicateType"] == BASE + TYPES[2]]
    for i in roots:
        restored = records[i]["predicate"]["restoration"].get("restoredScope", {}).get("credentials", [])
        if not set(restored) <= credentials:
            return result("restored-credential-unswept")
    # Bundle membership requirements have no published reason code.
    if len(roots) != 1:
        return result("input-requires-one-r3", "input-error")
    reached, pending = set(), roots[:]
    while pending:
        i = pending.pop()
        if i not in reached:
            reached.add(i)
            pending.extend(edges[i])
    if any(i not in reached and s["predicateType"] not in (BASE + TYPES[3], BASE + TYPES[4])
           for i, s in enumerate(records)):
        return result("input-unrelated-record", "input-error")
    return result("bundle-consistent", "accept")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("draft", "profile"), default="profile")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--record", type=Path)
    group.add_argument("--bundle", type=Path)
    args = parser.parse_args()
    if args.record:
        answer = Reader(args.mode).record(args.record.read_bytes())
    else:
        answer = bundle([p.read_bytes() for p in sorted(args.bundle.glob("*.json"))], args.mode)
    print(json.dumps(answer, sort_keys=True))
    return 0 if answer["verdict"] == "accept" else 1 if answer["verdict"] == "reject" else 2

if __name__ == "__main__":
    raise SystemExit(main())
