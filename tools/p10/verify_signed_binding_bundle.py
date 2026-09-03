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
from tools.p10.binding_bundle import VerifyConfig, run_verify  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--signed-p02-registry", type=Path, required=True)
    parser.add_argument("--signed-p02-registry-sha256", required=True)
    parser.add_argument("--p02-public-key", type=Path, required=True)
    parser.add_argument("--p02-public-key-sha256", required=True)
    parser.add_argument("--capability-registry", type=Path, required=True)
    parser.add_argument("--capability-registry-sha256", required=True)
    parser.add_argument("--signed-p10-bundle", type=Path, required=True)
    parser.add_argument("--signed-p10-bundle-sha256", required=True)
    parser.add_argument("--p10-public-key", type=Path, required=True)
    parser.add_argument("--p10-public-key-sha256", required=True)
    parser.add_argument("--p10-trust-policy", type=Path, required=True)
    parser.add_argument("--p10-trust-policy-sha256", required=True)
    parser.add_argument("--bundle-id", required=True)
    parser.add_argument("--sequence", type=int, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--receipt-output-relative", required=True)
    arguments = parser.parse_args()
    try:
        receipt = run_verify(VerifyConfig(**vars(arguments)))
    except (ExtractionError, OSError, ValueError) as error:
        print(
            json.dumps(
                {
                    "schema_version": "hwpx-agent.p10-06-binding-bundle-build-receipt/v1",
                    "state": "failed",
                    "error": str(error),
                    "raw_identifier_values_in_receipt": False,
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
