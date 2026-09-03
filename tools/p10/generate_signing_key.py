#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.p02.extract_help import ExtractionError  # noqa: E402
from tools.p10.binding_bundle import generate_p10_key_pair  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-output-root", type=Path, required=True)
    parser.add_argument("--private-output-relative", required=True)
    parser.add_argument("--public-output-root", type=Path, required=True)
    parser.add_argument("--public-output-relative", required=True)
    arguments = parser.parse_args()
    try:
        receipt = generate_p10_key_pair(
            arguments.private_output_root,
            arguments.private_output_relative,
            arguments.public_output_root,
            arguments.public_output_relative,
        )
    except (ExtractionError, OSError, ValueError) as error:
        print(
            json.dumps(
                {
                    "schema_version": "hwpx-agent.p10-06-signing-key-generation-receipt/v1",
                    "state": "failed",
                    "error": str(error),
                    "private_key_material_printed": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
