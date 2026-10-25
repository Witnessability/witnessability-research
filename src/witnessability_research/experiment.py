"""Generate and replay a bounded development run, with raw truth kept separate."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import time

from .finite import (FiniteModel, UnsupportedInput, canonical, digest, enumerate_exposure,
                     judge_direct, judge_criterion, make_certificate, pins, powerset,
                     structural_collision, verify_certificate)
from .store import (ACTIONS, BINDING, CARRIER_KIND, MODEL_IDS, admit_counter,
                    histories, receipt, replay, variants)

CLAIM = "zero-completed-writes-between-fixed-fences-v1"
PROTOCOL_VERSION = "endpoint-counter-development-v1"


def protocol(max_length):
    # These declarations precede generation and are pinned into each run.
    return {
        "version": PROTOCOL_VERSION, "phase": "development", "binding": "identity",
        "max_length": max_length, "initial_value": 0, "actions": list(ACTIONS),
        "same_value_writes_count": True, "identity": BINDING,
        "claim": CLAIM, "models": list(MODEL_IDS),
        "counter_contracts": {
            "baseline": "fixed binding and initial/final values only",
            "atomic": "exact completed-write count, atomic and trusted BY MODEL ASSUMPTION",
            "missing_receipt": "exact receipt or missing carrier",
            "bad_binding": "exact receipt or one changed object/run/epoch/start/end binding",
            "crash_gap": "zero or one completed write misses its increment",
            "bypass": "any subset of completed writes may miss increments",
            "reset": "no reset or last reset at any action boundary, including after last action",
            "wrap_mod2": "completed-write counter wraps modulo 2",
            "overcount": "zero or one aborted attempt increments counter without a commit",
            "compromised_issuer": "issuer can MAC any count in 0..max_length+1",
            "shared_control": "both endpoint and counter blocks replaceable by common controller"},
        "carrier": CARRIER_KIND,
        "carrier_warning": "PUBLIC test HMAC key; byte-binding demonstration only; anyone can mint",
        "admission_policy": "reject invalid/missing carrier or binding; no factual judgment or baseline fallback",
        "sigma_scope": "all raw finite supports, including observations rejected by carrier admission",
        "caps": {"max_length": 5, "max_histories": 400, "max_domains": 6,
                 "max_alphabet": 64, "exposure_steps_per_history": 100000,
                 "structural_comparisons": 2000000},
        "nonclaims": ["not preregistered or confirmatory", "identity-binding finite specialization only",
                      "new development implementation; no previous supplementary-run reproduction",
                      "no real independent observer or PKI", "not independent implementations"]}


def build_models(max_length=3):
    traces = []
    raw = {}
    for index, actions in enumerate(histories(max_length)):
        state = replay(actions)
        history_id = "h" + str(index).zfill(4)
        traces.append({"history_id": history_id, "actions": list(actions), "store": state})
    truth = {t["history_id"]: t["store"]["committed_write_count"] == 0 for t in traces}
    models = {}
    for model_id in MODEL_IDS:
        domains = ("endpoint",) if model_id == "baseline" else ("endpoint", "counter")
        joint = {}
        raw[model_id] = []
        for trace in traces:
            h = trace["history_id"]
            observations = variants(model_id, trace["actions"], trace["store"], max_length)
            joint[h] = tuple(sorted({r for _, r in observations}))
            raw[model_id].extend({"history_id": h, "variant": label, "record": r}
                                 for label, r in observations)
        alphabets = [tuple(sorted({r[i] for records in joint.values() for r in records}))
                     for i in range(len(domains))]
        faults = (frozenset(),)
        if model_id == "shared_control":
            # Blocks share a controller. This does NOT assert two independent domains.
            alphabets[1] = tuple(sorted({receipt(n) for n in range(max_length + 2)}))
            faults = powerset(domains)
        model = FiniteModel(model_id, CLAIM, tuple(truth), truth, domains,
                            tuple(alphabets), joint, faults)
        if model_id == "shared_control":
            raw[model_id] = [{"history_id": h, "variant": "common-controller-replacement",
                              "record": r}
                             for h in model.histories for r in sorted(enumerate_exposure(model, h))]
        models[model_id] = model
    return traces, models, raw


def consume(model, record):
    """Consumer takes only a model and projection, never a per-case history/label."""
    admission = "ADMITTED"
    if model.domains != ("endpoint",):
        if not isinstance(record, (tuple, list)) or len(record) != len(model.domains):
            raise UnsupportedInput("wrong projection shape")
        admission = admit_counter(record[1])
    if admission != "ADMITTED":
        return {"admission": admission, "judgment": None, "criterion_judgment": None}
    direct = judge_direct(model, record)
    criterion = judge_criterion(model, record)
    if direct != criterion:
        raise RuntimeError("enumeration and criterion disagree")
    return {"admission": admission, "judgment": direct, "criterion_judgment": criterion}


def generate(max_length=3):
    traces, models, raw = build_models(max_length)
    projections = []
    observations = []
    judgments = []
    summaries = {}
    certificates = []
    for model_id, model in models.items():
        records = sorted({row["record"] for row in raw[model_id]})
        by_record = {}
        for index, record in enumerate(records):
            record_id = model_id + "/r" + str(index).zfill(4)
            result = consume(model, record)
            by_record[record] = (record_id, result)
            projections.append({"record_id": record_id, "model_id": model_id, "record": list(record)})
            judgments.append({"record_id": record_id, "model_id": model_id, **result})
        for index, row in enumerate(raw[model_id]):
            record_id, _ = by_record[row["record"]]
            observations.append({"case_id": model_id + "/c" + str(index).zfill(5),
                                 "model_id": model_id, "history_id": row["history_id"],
                                 "variant": row["variant"], "record_id": record_id})
        unique_admission = Counter(x[1]["admission"] for x in by_record.values())
        unique_judgments = Counter(x[1]["judgment"] for x in by_record.values()
                                   if x[1]["judgment"] is not None)
        case_judgments = Counter(by_record[x["record"]][1]["judgment"] for x in raw[model_id]
                                 if by_record[x["record"]][1]["judgment"] is not None)
        collision = structural_collision(model)
        summaries[model_id] = {
            "histories": len(traces), "true_histories": sum(model.truth.values()),
            "false_histories": len(traces) - sum(model.truth.values()),
            "operational_cases": len(raw[model_id]), "distinct_raw_records": len(records),
            "admission_counts_distinct_records": dict(sorted(unique_admission.items())),
            "judgment_counts_distinct_admitted_records": dict(sorted(unique_judgments.items())),
            "judgment_counts_admitted_cases": dict(sorted(case_judgments.items())),
            "sigma_raw_support": int(collision is None), "collision": collision,
            "model_pin": model.pin, "claim_pin": model.claim_pin}
        for ambiguous in (r for r in records if by_record[r][1]["judgment"] == "UNRESOLVED"):
            cert = make_certificate(model, ambiguous)
            verify_certificate(model, ambiguous, cert, expected_pins=pins(model, ambiguous))
            certificates.append({"model_id": model_id,
                                 "record_id": by_record[ambiguous][0], "certificate": cert})
    # Counter extension is conservative for the old endpoint observation, except
    # shared_control intentionally changes the endpoint's fault assumptions.
    conservation = {}
    for model_id, model in models.items():
        if model_id == "baseline":
            continue
        conservation[model_id] = all(
            {r[:1] for r in enumerate_exposure(model, h)} ==
            set(enumerate_exposure(models["baseline"], h)) for h in model.histories)
    return {
        "models.json": {k: m.to_dict() for k, m in models.items()},
        "raw-traces.json": traces,
        "raw-observations.json": observations,
        "consumer-projections.json": projections,
        "judgments.json": judgments,
        "certificates.json": certificates,
        "summary.json": {"phase": "development", "models": summaries,
                         "endpoint_projection_conservation": conservation,
                         "conservation_exception": "shared_control changes endpoint fault assumptions"}}


def source_pins():
    package = Path(__file__).resolve().parent
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(package.glob("*.py"))}


def write_run(output, max_length=3):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise UnsupportedInput("run directory must be absent or empty; existing runs are never overwritten")
    started = time.perf_counter()
    artifacts = generate(max_length)
    output.mkdir(parents=True, exist_ok=True)
    for name, data in artifacts.items():
        (output / name).write_text(canonical(data) + "\n", encoding="utf-8")
    spec = protocol(max_length)
    files = {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in artifacts}
    sources = source_pins()
    manifest = {
        "schema": "witnessability-development-run-v1", "phase": "development",
        "created_at": datetime.now(timezone.utc).isoformat(), "protocol": spec,
        "protocol_pin": digest(spec), "source_files": sources, "source_pin": digest(sources),
        "model_pins": {k: digest(v) for k, v in artifacts["models.json"].items()},
        "claim_pins": {k: FiniteModel.from_dict(v).claim_pin for k, v in artifacts["models.json"].items()},
        "artifacts_sha256": files,
        "runtime": {"python": platform.python_version(), "implementation": platform.python_implementation(),
                    "platform": platform.platform(), "elapsed_seconds": time.perf_counter() - started}}
    (output / "manifest.json").write_text(canonical(manifest) + "\n", encoding="utf-8")
    return manifest


def verify_run(directory):
    """Rebuild finite results with current pinned code; not a physical replay."""
    directory = Path(directory)
    try:
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        if manifest["schema"] != "witnessability-development-run-v1" or manifest["phase"] != "development":
            raise UnsupportedInput("unsupported run envelope")
        sources = source_pins()
        if manifest["source_files"] != sources or manifest["source_pin"] != digest(sources):
            raise UnsupportedInput("source pin mismatch: use the exact code that produced the run")
        spec = protocol(manifest["protocol"]["max_length"])
        if manifest["protocol"] != spec or manifest["protocol_pin"] != digest(spec):
            raise UnsupportedInput("protocol pin mismatch")
        expected = generate(spec["max_length"])
        if set(manifest["artifacts_sha256"]) != set(expected):
            raise UnsupportedInput("artifact inventory mismatch")
        for name, data in expected.items():
            blob = (directory / name).read_bytes()
            if hashlib.sha256(blob).hexdigest() != manifest["artifacts_sha256"][name]:
                raise UnsupportedInput("artifact digest mismatch: " + name)
            if json.loads(blob) != data:
                raise UnsupportedInput("recomputed artifact mismatch: " + name)
        models = {k: FiniteModel.from_dict(v) for k, v in expected["models.json"].items()}
        if manifest["model_pins"] != {k: m.pin for k, m in models.items()}:
            raise UnsupportedInput("model pins mismatch")
        if manifest["claim_pins"] != {k: m.claim_pin for k, m in models.items()}:
            raise UnsupportedInput("claim pins mismatch")
        projections = {r["record_id"]: r for r in expected["consumer-projections.json"]}
        for row in expected["certificates.json"]:
            model = models[row["model_id"]]
            record = projections[row["record_id"]]["record"]
            verify_certificate(model, record, row["certificate"], expected_pins=pins(model, record))
        return {"status": "VERIFIED_FINITE_RECOMPUTATION", "phase": "development",
                "artifacts": len(expected), "models": len(models),
                "protocol_pin": manifest["protocol_pin"], "source_pin": manifest["source_pin"]}
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise UnsupportedInput("invalid saved-run structure: " + str(exc)) from exc
