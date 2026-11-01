#!/usr/bin/env python3
"""Portable, bounded replay of retained D3 Python checks.

This does not execute executed_case.py, use private signing keys, run a native
Wolfram/Lean engine, or independently implement the mathematical criterion.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time

import cryptography

RETAINED_VOLATILE = {"validation_time_utc", "package_path", "python", "cryptography"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inventory(root: Path, subdirs=("data", "code", "expected", "native")):
    return {p.relative_to(root).as_posix(): sha(p)
            for name in subdirs for p in sorted((root / name).rglob("*")) if p.is_file()}


def compare_json(actual: Path, expected: Path, omitted=()):
    a, b = read(actual), read(expected)
    for key in omitted:
        a.pop(key, None)
        b.pop(key, None)
    require(a == b, f"Result mismatch: {actual.name} versus {expected.name}")
    return {"equal": True, "omitted_top_level_fields": sorted(omitted),
            "actual_sha256": sha(actual), "expected_sha256": sha(expected)}


def refresh_manifests(package: Path):
    study = package / "evidence/executed_case"
    write(study / "manifest.json", {p.relative_to(study).as_posix(): sha(p)
          for p in sorted(study.rglob("*")) if p.is_file() and p.name != "manifest.json"})
    manifest = read(package / "PACKAGE_MANIFEST.json")
    manifest["files"] = {p.relative_to(package).as_posix(): sha(p)
                         for p in sorted(package.rglob("*"))
                         if p.is_file() and p.name != "PACKAGE_MANIFEST.json"}
    write(package / "PACKAGE_MANIFEST.json", manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="New results directory; existing paths are refused")
    args = parser.parse_args()
    require(not sys.flags.optimize and not os.environ.get("PYTHONOPTIMIZE"),
            "Run without -O/-OO and without PYTHONOPTIMIZE; original checkers use assertions")
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    require(not output.exists(), "Output already exists; choose a fresh directory")
    require(not any(output.is_relative_to(root / x) for x in ("data", "code", "expected", "native", "tools")),
            "Output must not be inside supplied input or tool directories")
    before = inventory(root)
    runner_before = sha(Path(__file__))
    pins_before = sha(root / "SOURCE-PINS.json")
    pins = read(root / "SOURCE-PINS.json")
    require(all(before.get(k) == v for k, v in pins["sha256"].items()), "Historical input differs from its pin")
    release = read(root / "RELEASE-PINS.json")
    require(before == release["sha256"], "Complete release inventory differs from its pins")
    output.mkdir(parents=True)
    study_source = root / "data/retained-study"
    code = root / "code"
    expected = root / "expected"
    receipts, comparisons = [], {}
    started = datetime.now(timezone.utc).isoformat()
    env = os.environ.copy()
    env.pop("PYTHONOPTIMIZE", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    def execute(name, arguments, expected_exit=0, expected_error=None, stdout_json=None):
        argv = [sys.executable, "-B"] + [str(x) for x in arguments]
        t0 = time.monotonic()
        begin = datetime.now(timezone.utc).isoformat()
        done = subprocess.run(argv, cwd=output, env=env, capture_output=True, timeout=180)
        stdout = output / "logs" / (name + ".stdout.txt")
        stderr = output / "logs" / (name + ".stderr.txt")
        stdout.parent.mkdir(exist_ok=True)
        stdout.write_bytes(done.stdout)
        stderr.write_bytes(done.stderr)
        passed = done.returncode == expected_exit and (expected_error is None or
                 expected_error.encode() in done.stderr)
        receipts.append({"name": name, "argv": argv, "cwd": str(output),
                         "started_utc": begin, "completed_utc": datetime.now(timezone.utc).isoformat(),
                         "elapsed_seconds": round(time.monotonic() - t0, 6),
                         "exit_code": done.returncode, "expected_exit_code": expected_exit,
                         "expected_error": expected_error, "pass": passed,
                         "stdout": stdout.relative_to(output).as_posix(), "stdout_sha256": sha(stdout),
                         "stderr": stderr.relative_to(output).as_posix(), "stderr_sha256": sha(stderr)})
        write(output / "COMMAND-RECEIPTS.json", receipts)
        require(passed, f"Unexpected result from {name}; see its stderr log")
        if stdout_json is not None:
            # Parse to ensure a tool did not return a non-JSON success message.
            json.loads(done.stdout)
            (output / stdout_json).write_bytes(done.stdout)

    with tempfile.TemporaryDirectory(prefix="d3-reproduction-") as scratch:
        scratch = Path(scratch)
        original = scratch / "retained-study"
        shutil.copytree(study_source, original)
        original_before = {p.relative_to(original).as_posix(): sha(p)
                           for p in sorted(original.rglob("*")) if p.is_file()}
        execute("finite", [code / "witnessability_checker.py", "--output", output / "finite"])
        comparisons["finite"] = compare_json(output / "finite/verification_results.json",
            expected / "finite.json", {"elapsed_seconds"})
        execute("resolution", [code / "check_resolution.py", "--certificates",
            root / "data/local_certificates.json", "--out", output / "resolution.json"])
        comparisons["resolution"] = compare_json(output / "resolution.json", expected / "resolution.json")
        execute("boundary", [code / "boundary_checks.py", "--out", output / "boundary.json"])
        comparisons["boundary"] = compare_json(output / "boundary.json", expected / "boundary.json")
        validator = code / "validate_retained_file_study.py"
        execute("retained-evidence", [validator, original], stdout_json="retained-validation.json")
        comparisons["retained-evidence"] = compare_json(output / "retained-validation.json",
            expected / "retained-validation.json", RETAINED_VOLATILE)
        execute("projection", [code / "recalculate_projection.py"], stdout_json="projection.json")
        comparisons["projection"] = compare_json(output / "projection.json", expected / "projection.json")
        execute("anchors", [code / "enumerate_anchors.py", "--output", output / "anchors.json"])
        comparisons["anchors"] = compare_json(output / "anchors.json", expected / "anchors.json")

        for kind in ("bad-signature", "bad-payload", "bad-manifest"):
            changed = scratch / kind
            shutil.copytree(original, changed)
            record = changed / "evidence/executed_case/runs/h-0000/records/authority-0.json"
            if kind == "bad-manifest":
                record.write_bytes(record.read_bytes() + b" ")
                expected = "Manifest hash mismatch"
            else:
                obj = read(record)
                if kind == "bad-signature":
                    sig = obj[0]["signature"]
                    obj[0]["signature"] = ("A" if sig[0] != "A" else "B") + sig[1:]
                else:
                    obj[0]["payload"]["principal"] = "negative-control-foreign-principal"
                write(record, obj)
                refresh_manifests(changed)
                expected = "InvalidSignature"
            execute(kind, [validator, changed], expected_exit=1, expected_error=expected)
        original_after = {p.relative_to(original).as_posix(): sha(p)
                          for p in sorted(original.rglob("*")) if p.is_file()}
        require(original_before == original_after, "Original unpacked inputs changed during the run")
    after = inventory(root)
    require(before == after, "Published input/retained files changed during the run")
    require(runner_before == sha(Path(__file__)), "Portable runner changed during the run")
    require(pins_before == sha(root / "SOURCE-PINS.json"), "Source pins changed during the run")
    finite = read(output / "finite/verification_results.json")
    retained = read(output / "retained-validation.json")
    anchor = read(output / "anchors.json")
    summary = {
        "schema": "d3-curated-replay/v1", "status": "PASS",
        "kind": "fresh replay of supplied Python checkers and retained-evidence validation",
        "started_utc": started, "completed_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "cryptography": cryptography.__version__,
        "assertions_enabled": True,
        "runner_sha256": sha(Path(__file__)), "source_pins_sha256": sha(root / "SOURCE-PINS.json"),
        "runner_sha256_before": runner_before, "runner_sha256_after": sha(Path(__file__)),
        "source_pins_sha256_before": pins_before,
        "source_pins_sha256_after": sha(root / "SOURCE-PINS.json"),
        "curated_study_file_count": len(original_before),
        "curated_study_manifest_entries": len(original_before)-1, "curated_manifest_verified": True,
        "input_and_retained_file_count": len(before), "input_and_retained_unchanged": before == after,
        "unpacked_original_unchanged": original_before == original_after,
        "comparisons": comparisons, "command_count": len(receipts), "all_expected_command_outcomes": True,
        "counts": {
            "exhaustive_binary_configurations": finite["exhaustive_binary_configurations_total"],
            "seeded_configurations": finite["randomized"]["configurations"],
            "portfolio_checks": sum(v["portfolios_checked"] for v in finite["portfolios"].values()),
            "verified_retained_signatures": retained["observed_and_recalculated"]["verified_signed_records"],
            "signed_target_mutation_rejections": retained["observed_and_recalculated"]["signed_target_tamper_rejections"],
            "isolated_negative_controls": 3,
            "anchor_model_group_pairs": anchor["separate_domain_model_group_pairs"] + anchor["shared_domain_model_group_pairs"],
            "anchor_budget_comparisons": anchor["cardinality_budget_comparisons"],
        },
        "scope": {
            "original_file_experiment_executed": False, "private_signing_keys_used": False,
            "native_wolfram_executed": False, "native_lean_executed": False,
            "independently_authored_implementation": False, "general_theorem_proved_by_this_run": False,
            "historical_os_execution_trace_verified": False,
            "historical_record_claims_raised_by_new_validation": False,
        },
    }
    write(output / "SUMMARY.json", summary)
    write(output / "INPUT-INVENTORY.json", {"before": before, "after": after})
    write(output / "RESULTS-SHA256.json", {p.relative_to(output).as_posix(): sha(p)
          for p in sorted(output.rglob("*")) if p.is_file() and p.name != "RESULTS-SHA256.json"})
    print(json.dumps({"status": summary["status"], "counts": summary["counts"], "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
