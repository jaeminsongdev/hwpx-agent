#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.p02.extract_help import ExtractionError
from tools.p02.registry_signing import SigningConfig, run_signing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--registry-sha256", required=True)
    parser.add_argument("--target-profile", type=Path, required=True)
    parser.add_argument("--profile-sha256", required=True)
    parser.add_argument("--contracts", type=Path, required=True)
    parser.add_argument("--contracts-sha256", required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--request-sha256", required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--trace-sha256", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--receipt-sha256", required=True)
    parser.add_argument("--private-key", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--output-relative", required=True)
    arguments = parser.parse_args()
    try:
        receipt = run_signing(
            SigningConfig(
                registry=arguments.registry,
                registry_sha256=arguments.registry_sha256,
                target_profile=arguments.target_profile,
                profile_sha256=arguments.profile_sha256,
                contracts=arguments.contracts,
                contracts_sha256=arguments.contracts_sha256,
                request=arguments.request,
                request_sha256=arguments.request_sha256,
                trace=arguments.trace,
                trace_sha256=arguments.trace_sha256,
                receipt=arguments.receipt,
                receipt_sha256=arguments.receipt_sha256,
                private_key=arguments.private_key,
                source_commit=arguments.source_commit,
                output_root=arguments.output_root,
                output_relative=arguments.output_relative,
            )
        )
    except (ExtractionError, OSError, ValueError) as error:
        print(
            json.dumps(
                {
                    "schema_version": "hwpx-agent.registry-signing-receipt/v1",
                    "state": "failed",
                    "error": str(error),
                    "private_key_material_printed": False,
                    "raw_identifiers_in_receipt": False,
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
