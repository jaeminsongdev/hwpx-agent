"""Read-only P09-95 byte preservation check; never qualifies native comment meaning."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREVIOUS = "implementation/p09/evidence/p09-94-stored-comments.source-progress.v1.json"
PREVIOUS_HASH = "417a464075f3206f65e39742e3bc0b3503a7a5f53544bac0229178230ddebb24"
CURRENT = "implementation/p09/evidence/p09-95-review-metadata.source-progress.v1.json"
PARENTS = (
    "crates/hwpx-package/src/text_flow.rs",
    "crates/hwpx-package/src/text_flow/source_memo.rs",
    "crates/hwpx-package/src/document_import/structure/review.rs",
    "crates/product-cli/tests/form_stored_provider/actual_import.rs",
)
ARCHIVE = "implementation/p09/source-archive/p09-95-pre-review-metatag/"
GROUPS = (
    "source_files", "source_archives", "predecessor_receipts", "actual_inputs",
    "actual_current_regression_executables", "historical_executables_preserved_not_reexecuted",
)


def pin(path: str) -> dict:
    raw = (ROOT / path).read_bytes()
    return {"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def exact(record: dict, path: str | None = None) -> bool:
    try:
        actual = pin(path or record["path"])
    except OSError:
        return False
    return actual["bytes"] == record["bytes"] and actual["sha256"] == record["sha256"]


def groups(data: dict):
    for key in GROUPS:
        yield key, data[key]
    yield "official_model", data["official_model"]["sources"]


def previous_audit() -> dict:
    checkpoint = pin(PREVIOUS)
    if checkpoint["bytes"] != 252320 or checkpoint["sha256"] != PREVIOUS_HASH:
        raise ValueError("previous_checkpoint_drift")
    data = json.loads((ROOT / PREVIOUS).read_bytes())
    origins, count, unchanged = [], 0, 0
    for key, records in groups(data):
        for record in records:
            count += 1
            if exact(record):
                unchanged += key == "source_files"
                continue
            if key != "source_files" or record["path"] not in PARENTS:
                raise ValueError("previous_raw_pin_not_preserved")
            archived = ARCHIVE + record["path"]
            if not exact(record, archived):
                raise ValueError("whole_preimage_drift")
            origins.append({**record, "archive_path": archived})
    if count != 1149 or unchanged != 788 or len(origins) != 4:
        raise ValueError("previous_coverage_drift")
    # Existing product tests must be byte-identical after removing only the new declaration.
    parent = PARENTS[3]
    current = (ROOT / parent).read_bytes()
    declaration = b'#[path = "actual_import/source_review_metadata.rs"]\nmod source_review_metadata;\n'
    if current.count(declaration) != 1 or current.replace(declaration, b"", 1) != (ROOT / (ARCHIVE + parent)).read_bytes():
        raise ValueError("existing_product_test_body_changed")
    # Original MEMO body guard was moved, not weakened by metadata support.
    old_body = (ROOT / (ARCHIVE + PARENTS[1])).read_bytes()
    now_body = (ROOT / PARENTS[1]).read_bytes()
    start = b"    require_only_whitespace_content(document, body)?;"
    if old_body[old_body.index(start):] != now_body[now_body.index(start):]:
        raise ValueError("original_memo_body_guard_changed")
    return {"state": "pass", "checkpoint": checkpoint, "raw_pin_entries": count,
            "source_files_unchanged": unchanged, "whole_modified_parents": origins,
            "existing_product_test_inverse_exact": True, "original_memo_body_guard_exact": True,
            "old_executables_preserved_not_reexecuted": 51,
            "whole_historical_qualification_reexecuted": False}


def current_audit() -> dict:
    previous_audit()
    previous = json.loads((ROOT / PREVIOUS).read_bytes())
    data = json.loads((ROOT / CURRENT).read_bytes())
    counts = {}
    for key, records in groups(data):
        if len({r["path"] for r in records}) != len(records):
            raise ValueError("duplicate_raw_pin_path")
        if not all(exact(r) for r in records):
            raise ValueError("current_raw_pin_drift")
        counts[key] = len(records)
    for key in ("source_files", "source_archives", "predecessor_receipts", "actual_inputs"):
        old_paths = {r["path"] for r in previous[key]}
        if not old_paths <= {r["path"] for r in data[key]}:
            raise ValueError("previous_coverage_omitted")
    required = {
        "crates/hwpx-package/src/text_flow/source_memo/meta_tests.rs",
        "crates/hwpx-package/tests/document_import_review_metadata.rs",
        "crates/product-cli/tests/form_stored_provider/actual_import/source_review_metadata.rs",
        "tools/p09/verify_review_metadata_progress.py",
    }
    if not required <= {r["path"] for r in data["source_files"]}:
        raise ValueError("new_implementation_coverage_omitted")
    old_exes = {r["path"] for key in GROUPS[-2:] for r in previous[key]}
    if old_exes != {r["path"] for r in data["historical_executables_preserved_not_reexecuted"]}:
        raise ValueError("historical_executable_coverage_omitted")
    if not {r["path"] for r in previous["official_model"]["sources"]} <= {r["path"] for r in data["official_model"]["sources"]}:
        raise ValueError("official_source_coverage_omitted")
    qualification = data["qualification"]
    for key in ("native_executed", "actual_SQL_executed", "native_author_time_binding",
                "native_visibility_resolution_binding", "HWPX_comment_lowering",
                "full_comment_product_acceptance", "p09_complete", "product_complete",
                "P10_new_implementation", "operation_execution_or_publication_authority"):
        if qualification[key] is not False:
            raise ValueError("unsupported_acceptance_promotion")
    if qualification["p09_gate"] != "OPEN" or (ROOT / "PLANS.md").exists():
        raise ValueError("gate_or_user_deleted_plan_changed")
    return {"state": "pass_scoped_byte_checks_NOT_native_or_product_gate", "checkpoint": pin(CURRENT),
            "groups": counts, "raw_pin_entries": sum(counts.values()), "P09_gate": "OPEN",
            "native_executed": False, "actual_SQL_executed": False, "product_complete": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(current_audit() if args.current else previous_audit(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        # Do not print source XML, comments, credentials or whole diagnostic logs.
        print(json.dumps({"state": "fail", "error_type": type(error).__name__,
                          "scope": "byte_preservation_not_native_or_product_gate"}))
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
