from __future__ import annotations

import argparse
import json
from pathlib import Path

import universal_package as package


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic, no-overwrite HWPX Agent plugin archive.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--registration-receipt", type=Path)
    args = parser.parse_args()

    binding = None
    if args.registration_receipt is not None:
        binding, errors = package.load_registration_receipt(args.registration_receipt)
        if errors or binding is None:
            print(json.dumps({"decision": "FAIL", "errors": errors}, sort_keys=True))
            return 1

    result, errors = package.publish_archive(args.output, binding=binding)
    if errors or result is None:
        print(json.dumps({"decision": "FAIL", "errors": errors}, sort_keys=True))
        return 1
    print(json.dumps({"decision": "PASS", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
