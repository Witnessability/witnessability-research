"""Simulated toy store, separate commit ledger, and public-fixture-key HMAC.

The HMAC key below is PUBLIC TEST DATA. A valid MAC demonstrates byte binding
inside this test convention only: anyone can mint a false count. It is not a
public-key signature, trusted hardware, or an independent observation channel.
"""

from itertools import product
import hashlib
import hmac
import json

from .finite import UnsupportedInput, canonical

ACTIONS = ("noop", "write0", "write1")
PUBLIC_TEST_KEY = b"witnessability-research-public-test-key-NOT-A-SECRET-v1"
BINDING = {"object": "object-0", "run": "run-0", "epoch": "epoch-0",
           "start_fence": "start-0", "end_fence": "end-0"}
CARRIER_KIND = "public-test-hmac-sha256-v1"


def histories(max_length=3):
    if type(max_length) is not int or not 0 <= max_length <= 5:
        raise UnsupportedInput("max_length must be an integer in 0..5")
    return tuple(actions for n in range(max_length + 1) for actions in product(ACTIONS, repeat=n))


def replay(actions):
    """Authoritative within this toy model; no counter is consulted."""
    value = 0
    commits = []
    events = []
    for step, action in enumerate(actions):
        if action not in ACTIONS:
            raise UnsupportedInput("unknown store action")
        before = value
        committed = action != "noop"
        if committed:
            value = int(action[-1])
            commits.append({"step": step, "before": before, "after": value})
        events.append({"step": step, "action": action, "before": before,
                       "after": value, "committed_write": committed})
    return {"initial": 0, "final": value, "commits": commits, "events": events,
            "committed_write_count": len(commits)}


def endpoint(state):
    return canonical({"binding": BINDING, "initial": state["initial"], "final": state["final"]})


def receipt(count, binding=None):
    if type(count) is not int or count < 0:
        raise UnsupportedInput("counter must be a nonnegative integer")
    payload = {"binding": dict(BINDING if binding is None else binding), "count": count}
    mac = hmac.new(PUBLIC_TEST_KEY, canonical(payload).encode(), hashlib.sha256).hexdigest()
    return canonical({"kind": CARRIER_KIND, "payload": payload, "mac": mac})


def admit_counter(atom):
    """Admission errors are never factual FALSE or an implicit zero count."""
    try:
        obj = json.loads(atom)
        if set(obj) != {"kind", "payload", "mac"} or obj["kind"] != CARRIER_KIND:
            return "REJECTED_CARRIER"
        payload = obj["payload"]
        if set(payload) != {"binding", "count"} or type(payload["count"]) is not int or payload["count"] < 0:
            return "REJECTED_CARRIER"
        expected = hmac.new(PUBLIC_TEST_KEY, canonical(payload).encode(), hashlib.sha256).hexdigest()
        if not isinstance(obj["mac"], str) or not hmac.compare_digest(expected, obj["mac"]):
            return "REJECTED_CARRIER"
        if payload["binding"] != BINDING:
            return "REJECTED_BINDING"
        return "ADMITTED"
    except (ValueError, TypeError, KeyError):
        return "REJECTED_CARRIER"


MODEL_IDS = ("baseline", "atomic", "missing_receipt", "bad_binding", "crash_gap",
             "bypass", "reset", "wrap_mod2", "overcount", "compromised_issuer", "shared_control")


def counter_value(actions, *, missed=(), reset_before=None, modulo=None, aborted=False):
    """Counter transitions from actions, independently of replay's commit ledger.

    The toy operation semantics say each write action completes; failure variants
    change the counter transition, never the separate store transition.
    """
    value = 0
    for boundary in range(len(actions) + 1):
        if boundary == reset_before:
            value = 0
        if boundary == len(actions):
            break
        action = actions[boundary]
        if action not in ACTIONS:
            raise UnsupportedInput("unknown counter action")
        if action in ("write0", "write1") and boundary not in missed:
            value += 1
            if modulo is not None:
                value %= modulo
    if aborted:
        value += 1
    return value


def variants(model_id, actions, state, max_length):
    """Operational counter states; the world/commit ledger never changes here."""
    if model_id not in MODEL_IDS:
        raise UnsupportedInput("unknown counter model")
    ep = endpoint(state)
    count = counter_value(actions)
    write_steps = tuple(i for i, action in enumerate(actions) if action in ("write0", "write1"))
    if model_id == "baseline":
        return [("endpoint-only", (ep,))]
    if model_id in ("atomic", "shared_control"):
        return [("atomic-exact", (ep, receipt(count)))]
    if model_id == "missing_receipt":
        return [("present", (ep, receipt(count))), ("missing", (ep, canonical({"missing": True})))]
    if model_id == "bad_binding":
        result = [("correct-binding", (ep, receipt(count)))]
        for field in BINDING:
            binding = dict(BINDING)
            binding[field] += "-other"
            result.append(("wrong-" + field, (ep, receipt(count, binding))))
        return result
    if model_id == "crash_gap":
        result = [("no-crash", (ep, receipt(count)))]
        # A completed write followed by crash before its increment, at most once.
        for step in write_steps:
            observed = counter_value(actions, missed=(step,))
            result.append(("miss-commit-" + str(step), (ep, receipt(observed))))
        return result
    if model_id == "bypass":
        result = []
        for mask in product((False, True), repeat=count):
            missed = tuple(step for step, kept in zip(write_steps, mask) if not kept)
            retained = counter_value(actions, missed=missed)
            result.append(("counted-commits-" + "".join("1" if x else "0" for x in mask),
                           (ep, receipt(retained))))
        return result
    if model_id == "reset":
        result = [("no-reset", (ep, receipt(count)))]
        for boundary in range(len(actions) + 1):
            retained = counter_value(actions, reset_before=boundary)
            result.append(("last-reset-before-step-" + str(boundary), (ep, receipt(retained))))
        return result
    if model_id == "wrap_mod2":
        return [("modulo-2", (ep, receipt(counter_value(actions, modulo=2))))]
    if model_id == "overcount":
        return [("no-abort", (ep, receipt(count))),
                ("one-aborted-attempt-counted", (ep, receipt(counter_value(actions, aborted=True))))]
    if model_id == "compromised_issuer":
        return [("issuer-reports-" + str(n), (ep, receipt(n)))
                for n in range(max_length + 2)]
    raise AssertionError("unreachable model")
