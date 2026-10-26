"""Bounded strict JSON and shape checks; contains no finite-model search."""

import json

from .common import ComputeLimit, InvalidInput

MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 200_000
MAX_STRING_LENGTH = 4096
MAX_INTEGER = 2**63 - 1
MIN_INTEGER = -(2**63)


def validated_string(value, label, nonempty=False):
    if type(value) is not str or (nonempty and not value):
        raise InvalidInput(label + " must be " + ("a nonempty string" if nonempty else "a string"))
    if len(value) > MAX_STRING_LENGTH:
        raise ComputeLimit(label + " exceeds the string length limit")
    if any(0xD800 <= ord(c) <= 0xDFFF for c in value):
        raise InvalidInput(label + " contains an unpaired Unicode surrogate")
    return value


def exact_keys(obj, required, label):
    if type(obj) is not dict:
        raise InvalidInput(label + " must be an object")
    if any(type(k) is not str for k in obj):
        raise InvalidInput(label + " has a non-string key")
    if set(obj) != set(required):
        raise InvalidInput(label + " has missing or unexpected fields")
    return obj


def _preflight_depth(text, budget):
    # Bound nesting before CPython's recursive JSON decoder is entered. Quoted
    # brackets and escaped quotes do not affect depth. Syntax remains json's job.
    budget.tick(max(1, (len(text) + 63) // 64))
    depth = 0
    quoted = False
    escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise ComputeLimit("JSON nesting depth limit exceeded")
        elif char in "]}":
            depth -= 1


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidInput("duplicate JSON object key")
        result[key] = value
    return result


def _no_float(value):
    raise InvalidInput("floating-point JSON numbers are not supported")


def _no_constant(value):
    raise InvalidInput("NaN and Infinity are not JSON inputs")


def _integer(value):
    # Avoid arbitrary-precision integer conversion and CPython-dependent limits.
    if len(value.lstrip("-")) > 19:
        raise InvalidInput("JSON integer is outside signed 64-bit range")
    result = int(value)
    if result < MIN_INTEGER or result > MAX_INTEGER:
        raise InvalidInput("JSON integer is outside signed 64-bit range")
    return result


def validate_json_value(value, budget):
    """Check a parsed JSON tree, including Python callers bypassing the decoder."""
    stack = [(value, 0)]
    nodes = 0
    while stack:
        current, depth = stack.pop()
        nodes += 1
        budget.tick()
        if nodes > MAX_JSON_NODES:
            raise ComputeLimit("JSON node limit exceeded")
        if type(current) is dict:
            if depth + 1 > MAX_JSON_DEPTH:
                raise ComputeLimit("JSON nesting depth limit exceeded")
            for key, item in current.items():
                validated_string(key, "object key")
                budget.tick(max(1, (len(key) + 63) // 64))
                stack.append((item, depth + 1))
        elif type(current) is list:
            if depth + 1 > MAX_JSON_DEPTH:
                raise ComputeLimit("JSON nesting depth limit exceeded")
            stack.extend((item, depth + 1) for item in current)
        elif type(current) is str:
            validated_string(current, "string")
            budget.tick(max(1, (len(current) + 63) // 64))
        elif current is None or type(current) is bool:
            pass
        elif type(current) is int:
            if not MIN_INTEGER <= current <= MAX_INTEGER:
                raise InvalidInput("JSON integer is outside signed 64-bit range")
        else:
            raise InvalidInput("value is not in the supported JSON type language")
    return value


def loads_strict(data, budget):
    if type(data) is not bytes:
        raise InvalidInput("JSON input must be UTF-8 bytes")
    if len(data) > MAX_JSON_BYTES:
        raise ComputeLimit("JSON byte limit exceeded")
    budget.tick(max(1, (len(data) + 63) // 64))
    if data.startswith(b"\xef\xbb\xbf"):
        raise InvalidInput("UTF-8 BOM is not permitted")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise InvalidInput("JSON input is not strict UTF-8") from exc
    _preflight_depth(text, budget)
    try:
        value = json.loads(text, object_pairs_hook=_pairs, parse_float=_no_float,
                           parse_int=_integer, parse_constant=_no_constant)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise InvalidInput("invalid JSON syntax or trailing data") from exc
    return validate_json_value(value, budget)
