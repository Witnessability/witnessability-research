"""Shared errors, work accounting and the unchanged local legacy encoding.

The encoding is CPython json.dumps with the listed options, not RFC 8785 JCS.
The work budget is a deterministic operation counter, not a wall-clock limit.
"""

import hashlib
import json


class InvalidInput(ValueError):
    """The supplied representation violates the input contract."""


class Unsupported(ValueError):
    """A well-formed version, binding or scope is not implemented."""


class PinMismatch(ValueError):
    """The input does not match the caller's externally supplied context."""


class AdmissionRejected(ValueError):
    """The supported admission policy did not admit the request."""


class InvalidCertificate(ValueError):
    """This supplied ambiguity witness failed validation, not a determinacy proof."""


class ComputeLimit(RuntimeError):
    """A structural or deterministic work limit prevented completion."""


MAX_WORK = 2_000_000


class Budget:
    def __init__(self, limit=MAX_WORK):
        if type(limit) is not int or not 1 <= limit <= MAX_WORK:
            raise InvalidInput("work limit must be an integer in 1..2000000")
        self.limit = limit
        self.used = 0

    def tick(self, n=1):
        if type(n) is not int or n < 0:
            raise InvalidInput("work increment must be a nonnegative integer")
        self.used += n
        if self.used > self.limit:
            raise ComputeLimit("deterministic work limit exceeded")


def canonical(value):
    """Byte-for-byte legacy encoder; supported input is validated separately."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False)


def digest(value, budget=None):
    encoded = canonical(value).encode("utf-8")
    if budget is not None:
        budget.tick(max(1, (len(encoded) + 63) // 64))
    return hashlib.sha256(encoded).hexdigest()
