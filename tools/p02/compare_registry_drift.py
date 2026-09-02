#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.p02.extract_help import ExtractionError, publish_no_overwrite, resolve_output
from tools.p02.registry_signing import (
    MAX_ENVELOPE_BYTES,
    MAX_KEY_BYTES,
    PRIVATE_OUTPUT_ROOT,
    compare_registry_drift,
    read_locked,
    serialize_json,
    sha256_bytes,
    verify_envelope_content,
)


def load_envelope(
    path: Path,
    expected_sha256: str,
    public_key: Path,
    public_key_sha256: str,
):
    content = read_locked(path, expected_sha256, MAX_ENVELOPE_BYTES, "signed registry")
    key_content = read_locked(
        public_key, public_key_sha256, MAX_KEY_BYTES, "trusted public key"
    )
    return verify_envelope_content(content, key_content, public_key_sha256)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--current-sha256", required=True)
    parser.add_argument("--current-public-key", type=Path, required=True)
    parser.add_argument("--current-public-key-sha256", required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--baseline-sha256")
    parser.add_argument("--baseline-public-key", type=Path)
    parser.add_argument("--baseline-public-key-sha256")
    parser.add_argument("--baseline-unavailable", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--output-relative", required=True)
    arguments = parser.parse_args()
    try:
        if arguments.output_root.resolve() != PRIVATE_OUTPUT_ROOT.resolve():
            raise ExtractionError("drift report may publish only under private P02 evidence")
        baseline_values = (
            arguments.baseline,
            arguments.baseline_sha256,
            arguments.baseline_public_key,
            arguments.baseline_public_key_sha256,
        )
        if arguments.baseline_unavailable:
            if any(value is not None for value in baseline_values):
                raise ExtractionError(
                    "baseline inputs must be omitted with --baseline-unavailable"
                )
            baseline = None
        else:
            if any(value is None for value in baseline_values):
                raise ExtractionError("all baseline inputs are required")
            baseline = load_envelope(
                arguments.baseline,
                arguments.baseline_sha256,
                arguments.baseline_public_key,
                arguments.baseline_public_key_sha256,
            )
        current = load_envelope(
            arguments.current,
            arguments.current_sha256,
            arguments.current_public_key,
            arguments.current_public_key_sha256,
        )
        report = compare_registry_drift(current, baseline)
        content = serialize_json(report)
        output = resolve_output(arguments.output_root, arguments.output_relative)
        publish_no_overwrite(output, content)
        receipt = {
            "schema_version": "hwpx-agent.registry-drift-receipt/v1",
            "state": "pass",
            "baseline_state": report["baseline_state"],
            "current_payload_sha256": report["current"]["payload_sha256"],
            "report_sha256": sha256_bytes(content),
            "summary": report["summary"],
            "raw_identifiers_in_receipt": False,
        }
    except (ExtractionError, OSError, ValueError) as error:
        print(
            json.dumps(
                {
                    "schema_version": "hwpx-agent.registry-drift-receipt/v1",
                    "state": "failed",
                    "error": str(error),
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
