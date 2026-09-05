from __future__ import annotations

import argparse
import json
from pathlib import Path

import skills_package as package


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic no-overwrite P16-03 skills archive.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--composed-plugin", action="store_true")
    args = parser.parse_args()
    result, errors = package.publish_archive(args.output, composed_plugin=args.composed_plugin)
    if errors or result is None:
        print(json.dumps({"decision": "FAIL", "errors": errors}, sort_keys=True))
        return 1
    print(json.dumps({"decision": "PASS", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
