from __future__ import annotations

import argparse
import json
from pathlib import Path

import codex_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic no-overwrite P17 Codex bundle core.")
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    result, errors = codex_bundle.publish_archive(arguments.output)
    if errors or result is None:
        print(json.dumps({"decision": "FAIL", "errors": errors}, sort_keys=True))
        return 1
    print(json.dumps({"decision": "PASS", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
