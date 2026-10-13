#!/usr/bin/env python3
"""Reproduce the pinned preparation receipt. Never launches Hangul/COM."""
from __future__ import annotations

import json
from pathlib import Path
import zipfile
from xml.etree import ElementTree

if __package__:
    from . import inspect_field_object_caption_target as oracle
    from . import validate_field_object_caption_hwpx_contract as source_contract
else:
    import inspect_field_object_caption_target as oracle
    import validate_field_object_caption_hwpx_contract as source_contract

ROOT = Path(__file__).resolve().parents[2]
QUALIFICATION = "implementation/p09/evidence/p09-19-object-caption-number-target-preparation.current-2020.v1.json"
QUALIFICATION_SHA256 = "aca01bc5aaac5e3b05896c2d9dee08a6134ed63d08f6878c218b029e227b277c"


def verify(root: Path = ROOT) -> dict:
    errors = []
    checked = 0
    try:
        raw = oracle.bounded_bytes(root / QUALIFICATION, 1024 * 1024)
        if oracle.sha256(raw) != QUALIFICATION_SHA256:
            raise ValueError("qualification_identity_changed")
        qualification = json.loads(raw, object_pairs_hook=oracle.duplicate_guard)
        for field in ("source_sha256", "seed_sha256"):
            for relative, expected in qualification[field].items():
                path = source_contract.bounded_file(root, relative)
                if oracle.sha256(path.read_bytes()) != expected:
                    errors.append("source_or_seed_digest_drift")
        if source_contract.validate(root)["state"] != "pass":
            errors.append("caption_source_contract_failed")
        manifests = []
        for field in ("primary_manifest", "retry_manifest"):
            record = qualification[field]
            manifest_path = source_contract.bounded_file(root, record["path"])
            manifest = oracle.load_manifest(manifest_path, record["sha256"])
            manifests.append(oracle.bounded_bytes(manifest_path, 1024 * 1024))
            for case_id in oracle.CASES:
                path = manifest_path.parent / oracle.FILES[case_id]
                result = oracle.inspect(path, manifest, case_id, "input")
                checked += 1
                if result["state"] != "pass":
                    errors.append("prepared_package_oracle_failed")
        if len(manifests) != 2 or manifests[0] != manifests[1]:
            errors.append("deterministic_manifest_mismatch")
    except (OSError, ValueError, UnicodeError, KeyError, TypeError, zipfile.BadZipFile, ElementTree.ParseError):
        errors.append("bounded_preparation_or_source_rejected")
    return {
        "schema_version": "hwpx-agent.p09-object-caption-number-target-preparation-validation/v1",
        "state": "fail" if errors else "pass", "errors": sorted(set(errors)),
        "prepared_packages_checked": checked, "actual_hangul": False,
        "model_expectation_target_qualified": False, "semantic_save_reopen": "not_run",
        "render": "not_run", "differential": "not_run", "green_rows": 0,
        "p09": "in_progress", "product_complete": False,
    }


if __name__ == "__main__":
    value = verify()
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if value["state"] == "pass" else 1)
