"""Local development-run CLI. No network or external mutations."""

import argparse
import json
import sys

from .experiment import verify_run, write_run
from .finite import CertificateError, ComputeLimit, UnsupportedInput


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="generate a bounded development run")
    run.add_argument("--output", required=True)
    run.add_argument("--max-length", type=int, default=3)
    verify = commands.add_parser("verify-run", help="verify bytes and recompute the finite experiment")
    verify.add_argument("directory")
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            manifest = write_run(args.output, args.max_length)
            result = {"status": "DEVELOPMENT_RUN_WRITTEN", "output": args.output,
                      "phase": manifest["phase"], "source_pin": manifest["source_pin"],
                      "protocol_pin": manifest["protocol_pin"], "runtime": manifest["runtime"]}
        else:
            result = verify_run(args.directory)
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0
    except (UnsupportedInput, CertificateError) as exc:
        print(json.dumps({"status": "UNSUPPORTED_OR_INVALID_INPUT", "error": str(exc)}), file=sys.stderr)
        return 2
    except ComputeLimit as exc:
        print(json.dumps({"status": "COMPUTE_LIMIT", "error": str(exc)}), file=sys.stderr)
        return 3
    except Exception as exc:
        print(json.dumps({"status": "COMPUTE_ERROR", "error": str(exc)}), file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
