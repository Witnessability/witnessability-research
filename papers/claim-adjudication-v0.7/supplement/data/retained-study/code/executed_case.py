#!/usr/bin/env python3
"""Actual local authorization decisions, file effects, and signed readbacks.

This is an observation experiment, not an authorization enforcement service.
The controller intentionally includes actions performed after a DENY decision.
All participants run on one host under one controlling user. Different keys
or processes establish no organizational/administrative independence.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def sign(payload, key):
    return {"payload": payload, "signature": base64.b64encode(key.sign(canonical(payload))).decode()}


def verify(envelope, public):
    Ed25519PublicKey.from_public_bytes(base64.b64decode(public)).verify(
        base64.b64decode(envelope["signature"]), canonical(envelope["payload"]))


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def child(role, request_path, key_path, output_path, effects_path):
    request = json.loads(request_path.read_text())
    key = Ed25519PrivateKey.from_private_bytes(key_path.read_bytes())
    reports = []
    for action in request["actions"]:
        common = {"schema": "local-witness-study/1", "run": request["run"],
                  "target": action["target"], "action": action["action"],
                  "principal": action["principal"], "request_sha256": digest(canonical(action)),
                  "context": request["context"], "producer": output_path.stem,
                  "role": role}
        if role == "authority":
            common.update({"decision": "ALLOW" if action["sensitivity"] <= 4 else "DENY",
                           "policy_sha256": request["policy_sha256"],
                           "warrant": "declared-local-rule:sensitivity<=4"})
        elif role == "executor":
            destination = effects_path / action["resource"]
            if action["perform"]:
                destination.parent.mkdir(parents=True, exist_ok=True)
                # Controlled write, deliberately independent of the policy decision.
                with destination.open("xb") as stream:
                    stream.write(action["content"].encode())
                    stream.flush()
                    os.fsync(stream.fileno())
            common.update({"invoked": action["perform"], "execution_mode": "observation-study",
                           "claimed_effect_sha256": digest(action["content"].encode()) if action["perform"] else None})
        elif role == "reader":
            destination = effects_path / action["resource"]
            content = destination.read_bytes() if destination.is_file() else None
            common.update({"exists_at_readback": content is not None,
                           "effect_sha256": digest(content) if content is not None else None,
                           "matches_expected_content": content == action["content"].encode(),
                           "coverage": "two declared paths at this readback; no claim about other actions"})
        else:
            raise ValueError(role)
        reports.append(sign(common, key))
    write_json(output_path, reports)


def run(out):
    if out.exists():
        raise SystemExit("Use a new output directory; existing evidence is never overwritten.")
    out.mkdir(parents=True)
    started = time.time()
    policy = {"id": "local-policy/1", "decision_rule": "sensitivity <= 4",
              "authority": "experiment-controller", "scope": "declared local file actions"}
    write_json(out / "policy.json", policy)
    keys, public = {}, {}
    roles = [(f"authority-{i}", "authority") for i in range(3)] + [("executor", "executor")] + [
        (f"reader-{i}", "reader") for i in range(3)]
    for name, _ in roles:
        key = Ed25519PrivateKey.generate()
        keys[name] = key
        public[name] = base64.b64encode(key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()
    write_json(out / "public_keys.json", public)
    histories, verified, tamper_rejections, subprocesses, effects = [], 0, 0, 0, 0
    with tempfile.TemporaryDirectory(prefix="witness-study-keys-") as secret_dir:
        secret = Path(secret_dir)
        for name, key in keys.items():
            path = secret / name
            path.write_bytes(key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                              serialization.NoEncryption()))
            path.chmod(0o600)
        for bits in itertools.product((0, 1), repeat=4):
            ua, ub, xa, xb = bits
            run_id = "h-" + "".join(map(str, bits))
            root = out / "runs" / run_id
            request = {"run": str(uuid.uuid4()), "context": "one-host-local-study/2026-10-13",
                       "policy_sha256": digest(canonical(policy)), "actions": []}
            for label, authorized, executed in [("A", ua, xa), ("B", ub, xb)]:
                request["actions"].append({"target": request["run"] + "/" + label, "action": "create-experiment-file",
                    "principal": "synthetic-local-actor", "resource": label + ".txt",
                    "sensitivity": 3 if authorized else 5, "perform": bool(executed),
                    "content": "actual effect for " + request["run"] + "/" + label + "\n"})
            request_path = root / "request.json"
            write_json(request_path, request)
            for name, role in roles:
                destination = root / "records" / (name + ".json")
                subprocess.run([sys.executable, str(Path(__file__).resolve()), "--child", role,
                    "--request", str(request_path), "--key", str(secret / name), "--record", str(destination),
                    "--effects", str(root / "effects")], check=True, capture_output=True, text=True)
                subprocesses += 1
                envelopes = json.loads(destination.read_text())
                for envelope in envelopes:
                    verify(envelope, public[name]); verified += 1
                    expected = next(a for a in request["actions"] if a["target"] == envelope["payload"]["target"])
                    assert envelope["payload"]["request_sha256"] == digest(canonical(expected))
                    assert envelope["payload"]["run"] == request["run"]
                    assert envelope["payload"]["context"] == request["context"]
                    modified = json.loads(json.dumps(envelope))
                    modified["payload"]["target"] += "/foreign"
                    try:
                        verify(modified, public[name])
                    except InvalidSignature:
                        tamper_rejections += 1
                    else:
                        raise AssertionError("Payload substitution was accepted.")
            auth = json.loads((root / "records" / "authority-0.json").read_text())
            reads = json.loads((root / "records" / "reader-0.json").read_text())
            for i in range(1, 3):
                other_auth = json.loads((root / "records" / f"authority-{i}.json").read_text())
                other_reads = json.loads((root / "records" / f"reader-{i}.json").read_text())
                assert [x["payload"]["decision"] for x in auth] == [x["payload"]["decision"] for x in other_auth]
                assert [x["payload"]["matches_expected_content"] for x in reads] == [x["payload"]["matches_expected_content"] for x in other_reads]
            actual = [int(x["payload"]["decision"] == "ALLOW") for x in auth] + [
                int(x["payload"]["matches_expected_content"]) for x in reads]
            assert tuple(actual) == bits
            effects += xa + xb
            # Validated semantic projection: unordered projection is deliberately
            # incomplete, retaining the authentic originals for contrast.
            pair_u, pair_x = 2 * ua + ub, 2 * xa + xb
            histories.append({"id": run_id, "bits": actual, "claim": ua * xa,
                "bound_record": [pair_u] * 3 + [pair_x] * 3,
                "unbound_record": [ua + ub] * 3 + [xa + xb] * 3})
    bound, unbound = {}, {}
    for h in histories:
        bound.setdefault(tuple(h["bound_record"]), set()).add(h["claim"])
        unbound.setdefault(tuple(h["unbound_record"]), set()).add(h["claim"])
    def classes(values):
        return {"total": len(values), "false": sum(x == {0} for x in values.values()),
                "true": sum(x == {1} for x in values.values()),
                "unresolved": sum(x == {0, 1} for x in values.values())}
    before = next(h for h in histories if h["id"] == "h-1010")
    after = next(h for h in histories if h["id"] == "h-1001")
    assert before["claim"] == 1 and after["claim"] == 0
    assert before["unbound_record"] == after["unbound_record"]
    summary = {"schema": "executed-local-case/1", "executed": True,
        "controlled_histories": 16, "actions": 32, "actual_created_files": effects,
        "subprocess_invocations": subprocesses, "verified_signed_records": verified,
        "signed_target_tamper_rejections": tamper_rejections,
        "bound_observation_classes": classes(bound), "unbound_observation_classes": classes(unbound),
        "counterexample_histories": [before["id"], after["id"]],
        "actual_failure_domains": 1, "domain_basis": "all processes, keys, policy and files under same host/user",
        "hypothetical_six_domain_margin": 3, "actual_one_domain_margin": 1,
        "guarantee_for_one_arbitrary_actual_domain_failure": False,
        "claim_scope": "local rule permits A and expected A file is present at readback",
        "not_established": ["production-system validity", "organizational independence", "trusted complete capture outside this experiment",
                            "OS/host integrity against its controller", "durability after the readback", "Cedar runtime replay"],
        "elapsed_seconds": round(time.time() - started, 3),
        "python": sys.version.split()[0], "code_sha256": digest(Path(__file__).read_bytes())}
    write_json(out / "histories.json", histories)
    write_json(out / "summary.json", summary)
    manifest = {str(p.relative_to(out)): digest(p.read_bytes()) for p in sorted(out.rglob("*")) if p.is_file()}
    write_json(out / "manifest.json", manifest)
    print(json.dumps(summary, indent=2, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--child", choices=("authority", "executor", "reader"))
    for name in ("request", "key", "record", "effects"):
        parser.add_argument("--" + name, type=Path)
    args = parser.parse_args()
    if args.child:
        child(args.child, args.request, args.key, args.record, args.effects)
    elif args.out:
        run(args.out.resolve())
    else:
        parser.error("--out or --child is required")


if __name__ == "__main__":
    main()
