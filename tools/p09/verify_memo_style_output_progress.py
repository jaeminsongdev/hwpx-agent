"""Read-only P09-96 source/pin preservation audit. Never asserts native product acceptance."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p95_bytes", Path(__file__).with_name("verify_review_metadata_progress.py"))
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)
ROOT = BASE.ROOT
PREVIOUS = "implementation/p09/evidence/p09-95-review-metadata.source-progress.v1.json"
CURRENT = "implementation/p09/evidence/p09-96-memo-style-output.source-progress.v1.json"
ARCHIVE = "implementation/p09/source-archive/p09-96-pre-memo-style-output/"
PARENTS = (
    "crates/hwpx-package/src/id_index.rs",
    "crates/hwpx-package/src/writer.rs",
    "crates/hwpx-package/src/document_import/fields/semantics/catalog.rs",
    "crates/product-cli/src/form_stored_provider/actual_import/field_ranges/semantics/catalog.rs",
    "crates/product-cli/tests/form_stored_provider/actual_import.rs",
    "crates/product-cli/tests/form_stored_provider/actual_import/source_memo_catalog.rs",
)
NEW_SOURCES = (
    "crates/hwpx-package/src/document_import/fields/semantics/catalog/memo_style.rs",
    "crates/hwpx-package/tests/memo_style_output.rs",
    "crates/product-cli/src/form_stored_provider/actual_import/field_ranges/semantics/catalog/memo_style.rs",
    "crates/product-cli/tests/form_stored_provider/actual_import/source_memo_style.rs",
    "tools/p09/verify_memo_style_output_progress.py",
    "tools/p09/tests/test_memo_style_output_progress.py",
    "implementation/p09/P09-96_MEMO_STYLE_OUTPUT_POLICY.md",
    "implementation/p09/P09-96_MEMO_STYLE_OUTPUT_REPORT.md",
    "protocol/migrations/p09-memo-style-output-v0-to-v1.md",
    "implementation/p09/evidence/p09-96-memo-style-output.initial-failures.v1.json",
    "implementation/p09/evidence/p09-96-memo-style-output.preservation.v1.json",
    "implementation/p09/evidence/p09-96-memo-style-output.source-regression.v1.json",
)
INITIAL_SOURCE_PATHS = NEW_SOURCES[:4]
PREDECESSORS = (PREVIOUS, "implementation/p09/evidence/p09-95-review-metadata.final-audit.v1.json")
EXECUTABLES = (
    "target/p09-96-package/debug/deps/hwpx_package-a850ad738bc59b10.exe",
    "target/p09-96-package/debug/deps/id_index-b06ac4c244093f4c.exe",
    "target/p09-96-package/debug/deps/patch_engine-f16fef8e94eda711.exe",
    "target/p09-96-package/debug/deps/document_import_memo_catalog-093bd8d5c2597e35.exe",
    "target/p09-96-package/debug/deps/document_import_review_metadata-8537eb795457ed5e.exe",
    "target/p09-96-package/debug/deps/memo_style_output-f87ca3d69966fa82.exe",
    "target/p09-96-regression/debug/deps/comment_operation-75493e8123c566c8.exe",
    "target/p09-96-regression/debug/deps/form_stored_provider-e02d02396d2f2bbd.exe",
    "target/p09-96-regression/debug/deps/stored_comment_provider-9065c76bcbac10b7.exe",
)
REQUIRED_GROUPS = {
    "source_delta": set(PARENTS + NEW_SOURCES),
    "source_archives_added": {ARCHIVE + path for path in PARENTS} | {
        "implementation/p09/source-archive/p09-96-initial-core-profile-failure/" + path
        for path in INITIAL_SOURCE_PATHS
    },
    "predecessor_receipts_added": set(PREDECESSORS),
    "current_executables": set(EXECUTABLES),
}


def inverse_parents():
    for path in PARENTS:
        old = (ROOT / (ARCHIVE + path)).read_bytes().decode("utf-8")
        current = (ROOT / path).read_bytes().decode("utf-8")
        if path.endswith("id_index.rs"):
            start = current.index("    // Native OWPML MemoShapeType")
            end = current.index("    ),\n", start) + len("    ),\n")
            addition = current[start:end]
            if '"memoPr"' not in addition or 'IdKind::MemoShape' not in addition:
                raise ValueError("native_declaration_missing")
            current = current[:start] + current[end:]
        elif path.endswith("writer.rs"):
            start = current.index("    /// Reopens and verifies the immutable package")
            end = current.index("    }\n", start) + len("    }\n")
            current = current[:start - 1] + current[end:]
        elif path.endswith("source_memo_catalog.rs"):
            current = current.replace("pub(super) mod fixture;", "mod fixture;", 1)
        elif path.endswith("actual_import.rs"):
            current = current.replace('#[path = "actual_import/source_memo_style.rs"]\nmod source_memo_style;\n', "", 1)
        else:
            current = current.replace("pub mod memo_style;\n", "", 1)
        if current != old:
            raise ValueError("original_parent_body_changed")


def previous():
    pin = BASE.pin(PREVIOUS)
    if pin["bytes"] != 253422 or pin["sha256"] != "9f21a4848e38c89b6ef5858cb0fe668d7a67ca6bb0abdd765cb9fd46d2d65f99":
        raise ValueError("previous_checkpoint_drift")
    data = json.loads((ROOT / PREVIOUS).read_bytes())
    count, unchanged, archived = 0, 0, []
    for key, records in BASE.groups(data):
        for record in records:
            count += 1
            if BASE.exact(record):
                unchanged += key == "source_files"
                continue
            if key != "source_files" or record["path"] not in PARENTS or not BASE.exact(record, ARCHIVE + record["path"]):
                raise ValueError("previous_raw_pin_not_preserved")
            archived.append({**record, "archive_path": ARCHIVE + record["path"]})
    if count != 1183 or unchanged != 797 or len(archived) != 6:
        raise ValueError("previous_coverage_drift")
    inverse_parents()
    return {"state": "pass", "previous_checkpoint": pin, "previous_raw_pin_entries": count,
            "unchanged_previous_source_files": unchanged, "whole_parent_preimages": archived,
            "parent_inverse_exact": True, "old_executables_preserved_not_reexecuted": 62,
            "all_historical_qualification_reexecuted": False}


def verify_current_manifest(data, inherited):
    """Require whole inherited identity and exact scope, not merely nonempty valid-looking pins."""
    if data["inherited_checkpoint"] != inherited["previous_checkpoint"]:
        raise ValueError("inherited_checkpoint_binding_drift")
    if data["current_source_files_count"] != 815:
        raise ValueError("current_source_coverage_drift")
    counts = {}
    for key, required in REQUIRED_GROUPS.items():
        records = data[key]
        if len({r["path"] for r in records}) != len(records) or not all(BASE.exact(r) for r in records):
            raise ValueError("current_raw_pin_drift")
        if {r["path"] for r in records} != required:
            raise ValueError("current_group_coverage_drift")
        counts[key] = len(records)
    for key in ("native_executed", "actual_SQL_executed", "full_comment_product_acceptance",
                "native_author_time_state_binding", "product_complete", "P10_new_implementation",
                "execution_publication_authority"):
        if data["qualification"][key] is not False:
            raise ValueError("unsupported_acceptance_promotion")
    if data["qualification"]["P09_gate"] != "OPEN" or (ROOT / "PLANS.md").exists():
        raise ValueError("gate_or_deleted_plan_changed")
    return counts


def current():
    inherited = previous()
    data = json.loads((ROOT / CURRENT).read_bytes())
    counts = verify_current_manifest(data, inherited)
    return {"state": "pass_scoped_inherited_and_delta_bytes_NOT_native_or_Gate", "checkpoint": BASE.pin(CURRENT),
            "previous_raw_pin_entries": inherited["previous_raw_pin_entries"], "current_groups": counts,
            "P09_gate": "OPEN", "product_complete": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(current() if args.current else previous(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "fail", "error_type": type(error).__name__,
                          "scope": "byte_preservation_NOT_native_acceptance"}))
        raise SystemExit(1) from error
