"""Read-only P09-97 inherited raw bytes and complete delta audit, NOT native product proof."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p96_bytes", Path(__file__).with_name("verify_memo_style_output_progress.py"))
P96 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P96)
BASE, ROOT = P96.BASE, P96.ROOT
PREVIOUS = P96.CURRENT
CURRENT = "implementation/p09/evidence/p09-97-review-body-output.source-progress.v1.json"
ARCHIVE = "implementation/p09/source-archive/p09-97-pre-review-body-output/"
PARENTS = (
    "crates/hwpx-package/src/patch.rs",
    "crates/hwpx-package/src/document_import/structure/review.rs",
    "crates/product-cli/src/form_stored_provider/actual_import/review.rs",
    "crates/product-cli/tests/form_stored_provider/actual_import.rs",
)
NEW_SOURCES = (
    "crates/hwpx-package/src/document_import/structure/review/body_output.rs",
    "crates/product-cli/src/form_stored_provider/actual_import/review/body_output.rs",
    "crates/hwpx-package/tests/review_body_output.rs",
    "crates/hwpx-package/tests/patch_element_content.rs",
    "crates/product-cli/tests/form_stored_provider/actual_import/source_review_output.rs",
    "tools/p09/verify_review_body_output_progress.py",
    "tools/p09/tests/test_review_body_output_progress.py",
    "implementation/p09/P09-97_REVIEW_BODY_OUTPUT_POLICY.md",
    "implementation/p09/P09-97_REVIEW_BODY_OUTPUT_REPORT.md",
    "protocol/migrations/p09-review-body-output-v0-to-v1.md",
    "implementation/p09/evidence/p09-97-review-body-output.initial-failures.v1.json",
    "implementation/p09/evidence/p09-97-review-body-output.preservation.v1.json",
    "implementation/p09/evidence/p09-97-review-body-output.source-regression.v1.json",
)
FAILURE_ARCHIVES = {
    "initial-compile-failure": (PARENTS[0], NEW_SOURCES[0], NEW_SOURCES[2]),
    "initial-tab-fixture-failure": (NEW_SOURCES[2], NEW_SOURCES[4]),
    "initial-private-method-failure": (NEW_SOURCES[3],),
    "initial-duplicate-fixture-failure": (NEW_SOURCES[3],),
    "initial-lint-failure": (NEW_SOURCES[3], NEW_SOURCES[2]),
    "initial-opaque-fixture-failure": (NEW_SOURCES[2],),
}
PREDECESSORS = (PREVIOUS, "implementation/p09/evidence/p09-96-memo-style-output.final-audit.v1.json")
EXECUTABLES = tuple(p.replace("p09-96", "p09-97") for p in P96.EXECUTABLES) + (
    "target/p09-97-package/debug/deps/text_flow-511dd1904a1b61b0.exe",
    "target/p09-97-package/debug/deps/document_import_review-67551457d524f20f.exe",
    "target/p09-97-package/debug/deps/document_import_assembly_review-312fc213dbce8bd9.exe",
    "target/p09-97-package/debug/deps/review_body_output-8759bbf6453e18f5.exe",
    "target/p09-97-package/debug/deps/patch_element_content-4a43081747b336ae.exe",
)
REQUIRED_GROUPS = {
    "source_delta": set(PARENTS + NEW_SOURCES),
    "source_archives_added": {ARCHIVE + p for p in PARENTS} | {
        f"implementation/p09/source-archive/p09-97-{stage}/{p}"
        for stage, files in FAILURE_ARCHIVES.items() for p in files
    },
    "predecessor_receipts_added": set(PREDECESSORS),
    "current_executables": set(EXECUTABLES),
}


def inverse_parents():
    for path in PARENTS:
        before = (ROOT / (ARCHIVE + path)).read_bytes().decode("utf-8")
        after = (ROOT / path).read_bytes().decode("utf-8")
        if path.endswith("patch.rs"):
            for begin, end in (
                ("    /// Replace only element content;", "    AllocateId {"),
                ("            Self::ReplaceElementContent { target, children } => formatter", "            Self::AllocateId {"),
                ("                PatchIntent::ReplaceElementContent { target, children } => {", "                PatchIntent::AllocateId {"),
                ("    fn plan_content_edit(", "    fn plan_allocation_edit("),
            ):
                start = after.index(begin)
                stop = after.index(end, start)
                after = after[:start] + after[stop:]
        elif path.endswith("actual_import.rs"):
            after = after.replace('#[path = "actual_import/source_review_output.rs"]\nmod source_review_output;\n', "", 1)
        else:
            after = after.replace("pub mod body_output;\n", "", 1)
        if before != after:
            raise ValueError("original_parent_body_changed")


def exact_inherited(record, source_record):
    if BASE.exact(record):
        return True
    if source_record and record["path"] in set(P96.PARENTS) | set(PARENTS):
        for prefix in (P96.ARCHIVE, ARCHIVE):
            if BASE.exact(record, prefix + record["path"]):
                return True
    return False


def inherited():
    previous = BASE.pin(PREVIOUS)
    if previous["bytes"] != 12952 or previous["sha256"] != "4aebe074bef35ecca8e5a322b308837f15228f48046a2d3381f1ee8966dc0f13":
        raise ValueError("previous_checkpoint_drift")
    p96 = json.loads((ROOT / PREVIOUS).read_bytes())
    p95_pin = BASE.pin(P96.PREVIOUS)
    if p95_pin != p96["inherited_checkpoint"] or p95_pin["bytes"] != 253422 or p95_pin["sha256"] != "9f21a4848e38c89b6ef5858cb0fe668d7a67ca6bb0abdd765cb9fd46d2d65f99":
        raise ValueError("previous_inheritance_drift")
    p95 = json.loads((ROOT / P96.PREVIOUS).read_bytes())
    records = {}
    count = 0
    for key, items in BASE.groups(p95):
        for record in items:
            count += 1
            if not exact_inherited(record, key == "source_files"):
                raise ValueError("inherited_pin_drift")
        if key == "source_files":
            records.update({r["path"]: r for r in items})
    if count != 1183 or len(records) != 803:
        raise ValueError("previous_coverage_drift")
    for key, expected in P96.REQUIRED_GROUPS.items():
        items = p96[key]
        if len(items) != len(expected) or {r["path"] for r in items} != expected:
            raise ValueError("previous_delta_coverage_drift")
        for record in items:
            count += 1
            if not exact_inherited(record, key == "source_delta"):
                raise ValueError("inherited_pin_drift")
        if key == "source_delta":
            records.update({r["path"]: r for r in items})
    if count != 1222 or len(records) != 815:
        raise ValueError("previous_coverage_drift")
    unchanged = 0
    preimages = []
    for record in records.values():
        if BASE.exact(record):
            unchanged += 1
        elif record["path"] in PARENTS and BASE.exact(record, ARCHIVE + record["path"]):
            preimages.append({**record, "archive_path": ARCHIVE + record["path"]})
        else:
            raise ValueError("current_parent_preimage_drift")
    if unchanged != 811 or len(preimages) != 4:
        raise ValueError("current_parent_coverage_drift")
    inverse_parents()
    return {"state": "pass_declared_inherited_bytes_and_exact_parent_inverses",
            "previous_checkpoint": previous, "inherited_raw_pin_entries": count,
            "previous_current_source_files": 815, "unchanged_previous_source_files": unchanged,
            "whole_parent_preimages": preimages, "parent_inverse_exact": True,
            "old_executables_preserved_not_reexecuted": 71,
            "all_historical_qualification_reexecuted": False}


def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"]:
        raise ValueError("inherited_checkpoint_binding_drift")
    if data["current_source_files_count"] != 828:
        raise ValueError("current_source_coverage_drift")
    counts = {}
    for key, expected in REQUIRED_GROUPS.items():
        items = data[key]
        if len({r["path"] for r in items}) != len(items) or not all(BASE.exact(r) for r in items):
            raise ValueError("current_raw_pin_drift")
        if {r["path"] for r in items} != expected:
            raise ValueError("current_group_coverage_drift")
        counts[key] = len(items)
    for key in ("native_executed", "actual_SQL_executed", "full_comment_product_acceptance",
                "native_author_time_state_binding", "product_complete", "P10_new_implementation",
                "execution_publication_authority", "full_typed_comment_compiler_route_connected"):
        if data["qualification"][key] is not False:
            raise ValueError("unsupported_acceptance_promotion")
    if data["qualification"]["P09_gate"] != "OPEN" or (ROOT / "PLANS.md").exists():
        raise ValueError("gate_or_deleted_plan_changed")
    return counts


def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_scoped_inheritance_and_delta_NOT_native_or_Gate", "checkpoint": BASE.pin(CURRENT),
            "inherited_raw_pin_entries": prior["inherited_raw_pin_entries"],
            "current_groups": verify_current_manifest(data, prior), "P09_gate": "OPEN", "product_complete": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(current() if args.current else inherited(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "fail", "error_type": type(error).__name__, "scope": "byte_preservation_NOT_native_acceptance"}))
        raise SystemExit(1) from error
