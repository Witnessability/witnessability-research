#!/usr/bin/env python3
"""Read-only validation of the retained v0.4 local file study; never executes it.

The only mutation is in-memory target tampering for a new signature check.
Results are printed to stdout. No original study module is imported or run.
"""
from __future__ import annotations
import argparse
import base64
import copy
import hashlib
import itertools
import json
import platform
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import cryptography
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key {key!r} in {path}")
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique)


def require(condition, label):
    if not condition:
        raise ValueError(label)


def manifest_check(root, manifest, excluded):
    actual = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
    require(actual == set(manifest) | set(excluded), "Manifest file coverage mismatch")
    for relative, expected in manifest.items():
        path = root / relative
        require(path.resolve().is_relative_to(root.resolve()), "Manifest path escapes root")
        require(sha(path.read_bytes()) == expected, f"Manifest hash mismatch: {relative}")
    return {"listed_files": len(manifest), "all_hashes_match": True,
            "exact_coverage_excluding_self": True}


def classes(histories, key):
    grouped = {}
    for history in histories:
        grouped.setdefault(tuple(history[key]), []).append(history)
    count = Counter()
    members = []
    for record, hs in sorted(grouped.items()):
        claims = {h["claim"] for h in hs}
        status = "unresolved" if len(claims) == 2 else ("true" if claims == {1} else "false")
        count[status] += 1
        members.append({"record": record, "verdict": status, "history_ids": [h["id"] for h in hs]})
    return {"total": len(grouped), **{key: count[key] for key in ("false", "true", "unresolved")}}, members


def margin(histories, key, one_host=False):
    return min(int(a[key] != b[key]) if one_host else sum(x != y for x, y in zip(a[key], b[key]))
               for a in histories for b in histories if a["claim"] != b["claim"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    package = args.package.resolve()
    root = package / "evidence/executed_case"
    package_manifest = read(package / "PACKAGE_MANIFEST.json")
    manifests = {
        "package": manifest_check(package, package_manifest["files"], {"PACKAGE_MANIFEST.json"}),
        "executed_case": manifest_check(root, read(root / "manifest.json"), {"manifest.json"})}
    original_summary = read(root / "summary.json")
    source = package / "code/executed_case.py"
    require(original_summary["code_sha256"] == sha(source.read_bytes()), "Historical source digest mismatch")
    policy = read(root / "policy.json")
    require(policy["decision_rule"] == "sensitivity <= 4", "Unexpected local policy")
    roles = {**{f"authority-{i}": "authority" for i in range(3)}, "executor": "executor",
             **{f"reader-{i}": "reader" for i in range(3)}}
    keys = read(root / "public_keys.json")
    require(set(keys) == set(roles), "Unexpected public key set")
    require(len(set(keys.values())) == 7, "Duplicate public keys")
    public = {name: Ed25519PublicKey.from_public_bytes(base64.b64decode(value, validate=True))
              for name, value in keys.items()}
    retained_histories = read(root / "histories.json")
    history_by_id = {h["id"]: h for h in retained_histories}
    require(len(history_by_id) == len(retained_histories) == 16, "Historical history cardinality mismatch")
    runs = sorted((root / "runs").iterdir())
    require(len(runs) == 16 and all(run.is_dir() for run in runs), "Unexpected run layout")
    report_receipts, action_receipts, reconstructed, run_ids = [], [], [], set()
    envelopes_seen, tamper_rejects, record_files, files_present, denied_effects = 0, 0, 0, 0, 0
    for run in runs:
        request = read(run / "request.json")
        require(request["run"] not in run_ids, "Duplicate run UUID")
        run_ids.add(request["run"])
        require(request["context"] == "one-host-local-study/2026-10-13", "Unexpected context")
        require(request["policy_sha256"] == sha(canonical(policy)), "Policy binding mismatch")
        actions = request["actions"]
        require(len(actions) == 2, "Expected two actions per request")
        expected_targets = {request["run"] + "/A", request["run"] + "/B"}
        require({a["target"] for a in actions} == expected_targets, "Unexpected target set")
        require([a["resource"] for a in actions] == ["A.txt", "B.txt"], "Unexpected action order/resources")
        expected_files = set()
        material = {}
        for action in actions:
            path = run / "effects" / action["resource"]
            raw = path.read_bytes() if path.is_file() else None
            require((raw is not None) == action["perform"], "Retained effect presence differs from perform")
            if raw is not None:
                require(raw == action["content"].encode(), "Retained effect content mismatch")
                expected_files.add(path.name)
                files_present += 1
                denied_effects += int(action["sensitivity"] > 4)
            material[action["target"]] = (action, raw)
            action_receipts.append({"history": run.name, "target": action["target"],
                                    "request_sha256": sha(canonical(action)),
                                    "effect_present": raw is not None,
                                    "effect_sha256": sha(raw) if raw is not None else None})
        present_files = {p.name for p in (run / "effects").iterdir()} if (run / "effects").exists() else set()
        require(present_files == expected_files, "Unexpected effect directory contents")
        records = sorted((run / "records").glob("*.json"))
        require({p.stem for p in records} == set(roles), "Unexpected producer record set")
        payloads = {}
        for record in records:
            producer = record.stem
            envelopes = read(record)
            require(len(envelopes) == 2, "Expected two envelopes per producer record")
            require({e["payload"]["target"] for e in envelopes} == expected_targets,
                    "Missing or duplicate target in producer records")
            payloads[producer] = {}
            record_files += 1
            for envelope in envelopes:
                require(set(envelope) == {"payload", "signature"}, "Unexpected envelope structure")
                payload = envelope["payload"]
                action, raw = material[payload["target"]]
                signature = base64.b64decode(envelope["signature"], validate=True)
                public[producer].verify(signature, canonical(payload))
                envelopes_seen += 1
                expected = {"schema": "local-witness-study/1", "run": request["run"],
                            "target": action["target"], "action": action["action"],
                            "principal": action["principal"], "request_sha256": sha(canonical(action)),
                            "context": request["context"], "producer": producer, "role": roles[producer]}
                if roles[producer] == "authority":
                    expected.update(decision="ALLOW" if action["sensitivity"] <= 4 else "DENY",
                                    policy_sha256=request["policy_sha256"], warrant="declared-local-rule:sensitivity<=4")
                elif roles[producer] == "executor":
                    expected.update(invoked=action["perform"], execution_mode="observation-study",
                                    claimed_effect_sha256=sha(action["content"].encode()) if action["perform"] else None)
                else:
                    expected.update(exists_at_readback=raw is not None,
                                    effect_sha256=sha(raw) if raw is not None else None,
                                    matches_expected_content=raw == action["content"].encode(),
                                    coverage="two declared paths at this readback; no claim about other actions")
                require(payload == expected, f"Payload binding/semantic mismatch: {record}")
                changed = copy.deepcopy(payload)
                changed["target"] += "/foreign"
                try:
                    public[producer].verify(signature, canonical(changed))
                except InvalidSignature:
                    tamper_rejects += 1
                else:
                    raise ValueError("Tampered signed target accepted")
                payloads[producer][action["resource"]] = payload
                report_receipts.append({"path": str(record.relative_to(package)), "target": payload["target"],
                                        "canonical_payload_sha256": sha(canonical(payload)),
                                        "signature_verified": True, "bindings_and_semantics_match": True,
                                        "new_target_mutation_rejected": True})
        # Derived solely from signed retained records after verification, not folder bits.
        ua, ub = [int(payloads["authority-0"][r]["decision"] == "ALLOW") for r in ("A.txt", "B.txt")]
        xa, xb = [int(payloads["reader-0"][r]["matches_expected_content"]) for r in ("A.txt", "B.txt")]
        history = {"id": run.name, "bits": [ua, ub, xa, xb], "claim": ua * xa,
                   "bound_record": [2 * ua + ub] * 3 + [2 * xa + xb] * 3,
                   "unbound_record": [ua + ub] * 3 + [xa + xb] * 3}
        require(history == history_by_id[run.name], "Raw-derived history differs from retained histories.json")
        reconstructed.append(history)
    require({tuple(h["bits"]) for h in reconstructed} == set(itertools.product((0, 1), repeat=4)),
            "Expected exhaustive four-bit histories")
    bound, bound_members = classes(reconstructed, "bound_record")
    unbound, unbound_members = classes(reconstructed, "unbound_record")
    observed = {"controlled_histories": len(reconstructed), "actions": len(action_receipts),
                "actual_created_files": files_present, "verified_signed_records": envelopes_seen,
                "signed_target_tamper_rejections": tamper_rejects,
                "bound_observation_classes": bound, "unbound_observation_classes": unbound,
                "hypothetical_six_domain_margin": margin(reconstructed, "bound_record"),
                "actual_one_domain_margin": margin(reconstructed, "bound_record", one_host=True)}
    for key, actual in observed.items():
        require(original_summary[key] == actual, f"Historical summary disagreement: {key}")
    result = {"status": "PASS", "validation_time_utc": datetime.now(timezone.utc).isoformat(),
              "validation_kind": "new read-only verification of retained v0.4 evidence",
              "package_path": str(package), "source_sha256": sha(source.read_bytes()),
              "validator_sha256": sha(Path(__file__).read_bytes()),
              "python": platform.python_version(), "cryptography": cryptography.__version__,
              "manifests": manifests, "observed_and_recalculated": observed,
              "record_json_files": record_files, "request_json_files": len(runs),
              "retained_effect_files_count": files_present,
              "summary_field_interpretation": {"actual_created_files": "16 retained files verified now; historical creation events not independently traced"},
              "distinct_public_keys": len(keys), "retained_effects_after_deny": denied_effects,
              "unbound_margin": margin(reconstructed, "unbound_record"),
              "historical_execution_boundary": {
                  "claimed_subprocess_invocations": original_summary["subprocess_invocations"],
                  "code_expected_invocations": 16 * 7, "retained_per_process_record_groups": record_files,
                  "independent_os_execution_receipts_verified": 0,
                  "historical_fsync_calls_independently_verified": 0,
                  "new_native_effect_execution": False,
                  "historical_timestamp_or_controller_identity_authenticated": False,
                  "public_keys_prove_organizational_independence": False,
                  "retained_file_bytes_prove_historical_write_syscalls": False},
              "bound_classes": bound_members, "unbound_classes": unbound_members,
              "action_receipts": action_receipts, "report_receipts": report_receipts,
              "source_inventory": {str(p.relative_to(package)): sha(p.read_bytes())
                                   for p in sorted(root.rglob("*")) if p.is_file()}}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
