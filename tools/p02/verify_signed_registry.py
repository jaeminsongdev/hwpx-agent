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
from tools.p02.registry_signing import (
    SignedRegistryVerificationConfig,
    verify_signed_registry,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--signed-registry", type=Path, required=True)
    parser.add_argument("--signed-registry-sha256", required=True)
    parser.add_argument("--public-key", type=Path, required=True)
    parser.add_argument("--public-key-sha256", required=True)
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
    arguments = parser.parse_args()
    try:
        result = verify_signed_registry(
            SignedRegistryVerificationConfig(
                signed_registry=arguments.signed_registry,
                signed_registry_sha256=arguments.signed_registry_sha256,
                public_key=arguments.public_key,
                public_key_sha256=arguments.public_key_sha256,
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
            )
        )
    except (ExtractionError, OSError, ValueError) as error:
        result = {
            "schema_version": "hwpx-agent.signed-registry-verification/v1",
            "state": "failed",
            "target_profile_id": None,
            "exact_build": None,
            "key_id": None,
            "envelope_sha256": None,
            "payload_sha256": None,
            "source_registry_sha256": None,
            "signature_valid": False,
            "runtime_evidence_valid": False,
            "coverage": {
                "binding_count": 0,
                "candidate_count": 0,
                "unavailable_count": 0,
                "verified_count": 0,
                "failed_count": 0,
                "blocked_by_risk_count": 0,
                "not_run_count": 0,
                "routing_enabled_count": 0,
            },
            "routing_enabled": False,
            "raw_identifier_value_leak_count": 0,
            "errors": [str(error)],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("state") == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
