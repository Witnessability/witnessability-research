# Authorship and input provenance

This is a separately authored reference implementation made by a child agent
within the same internal agent system as the parent validation effort. It is
**not independent external validation**. Shared model training, runtime, tools,
task coordination and the supplied contract are common dependencies.

The sole pre-existing project file read for this implementation was:

`standalone/CONTRACT.md` from candidate PC-WR-02-002, source tree
`57ab2f7494d14f74e711a3a75ea8f722e53a7ee5`. Its SHA-256 is
`d7b22c16ae45181972192b4be96552f4f670d681ff6c328c9b03b8e3003cddd1`. The included contract has these same bytes.

The contract was read in full. No fixture, prior implementation source, test,
`finite.py`, `analysis.py`, `verify.py` or another agent's implementation was
read. The contract itself describes existing algorithms. Therefore the correct
description is source-blind separate authoring from a shared specification,
not theory-blind independence. No implementation or test code was reused.

The parent initially proposed an observation-to-history relational construction
using faulty substitutions, and later requested the universe-once coordinate
bit-mask/cylinder-intersection design to distinguish this implementation from
an existing substitution-expansion path. That design direction is explicitly
shared provenance, not an independent algorithm discovery. A first local draft
used substitution enumeration; it was replaced with the bit-mask construction
before testing or delivery. The final proof sketch and tests were authored for
the final design from the same mathematical contract.

Authored files in this directory are `third_checker.py`,
`test_third_checker.py`, `README.md`, `DERIVATION.md`, and this document.
`test-output.txt` records the actual small local suite run. No remote or public
repository mutation was performed by this agent.

Disclosure note: this document replaces only the original host-specific input
locator with a source-relative identity. Its historical input-document
SHA-256 was `9df256359bad7a2ac52d47cf4f9ae58c0e00aa727d81ff3353890676d4ad46bf`.
That digest identifies the document read by the earlier validation run,
not this disclosure version. Shared design and authorship statements
above are retained. `test-output.txt` is the original small-suite log,
copied without alteration; this preparation did not rerun the tests.
