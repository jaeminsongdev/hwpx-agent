"""Read-only P09-98 original-source/pin preservation; NOT native or product acceptance."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p97_bytes", Path(__file__).with_name("verify_review_body_output_progress.py"))
P97 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P97)
P96, BASE, ROOT = P97.P96, P97.BASE, P97.ROOT
PREVIOUS = P97.CURRENT
CURRENT = "implementation/p09/evidence/p09-98-review-delete.source-progress.v1.json"
ARCHIVE = "implementation/p09/source-archive/p09-98-pre-review-delete/"
PARENTS = (
    "crates/hwpx-package/src/document_import/structure/review.rs",
    "crates/product-cli/src/form_stored_provider/actual_import/review.rs",
    "crates/product-cli/tests/form_stored_provider/actual_import.rs",
)
NEW_SOURCES = (
    "crates/hwpx-package/src/document_import/structure/review/delete_output.rs",
    "crates/product-cli/src/form_stored_provider/actual_import/review/delete_output.rs",
    "crates/hwpx-package/tests/review_delete_output.rs",
    "crates/product-cli/tests/form_stored_provider/actual_import/source_review_delete.rs",
    "tools/p09/verify_review_delete_progress.py",
    "tools/p09/tests/test_review_delete_progress.py",
    "implementation/p09/P09-98_REVIEW_DELETE_POLICY.md",
    "implementation/p09/P09-98_REVIEW_DELETE_REPORT.md",
    "protocol/migrations/p09-review-delete-v0-to-v1.md",
    "implementation/p09/evidence/p09-98-review-delete.initial-failures.v1.json",
    "implementation/p09/evidence/p09-98-review-delete.preservation.v1.json",
    "implementation/p09/evidence/p09-98-review-delete.source-regression.v1.json",
)
FAILURE_ARCHIVES = {
    "initial-wrapper-fixture-failure": NEW_SOURCES[2],
    "initial-marker-fixture-failure": NEW_SOURCES[2],
    "initial-nested-fixture-failure": NEW_SOURCES[2],
    "initial-lint-failure": NEW_SOURCES[0],
    "second-lint-failure": NEW_SOURCES[0],
    "third-lint-failure": NEW_SOURCES[0],
}
PREDECESSORS = (PREVIOUS, "implementation/p09/evidence/p09-97-review-body-output.final-audit.v1.json")
EXECUTABLES = tuple(p.replace("p09-97", "p09-98") for p in P97.EXECUTABLES) + (
    "target/p09-98-package/debug/deps/review_delete_output-c5dd540b6b40acb8.exe",
)
REQUIRED_GROUPS = {
    "source_delta": set(PARENTS + NEW_SOURCES),
    "source_archives_added": {ARCHIVE + p for p in PARENTS} | {
        f"implementation/p09/source-archive/p09-98-{stage}/{path}"
        for stage, path in FAILURE_ARCHIVES.items()
    },
    "predecessor_receipts_added": set(PREDECESSORS),
    "current_executables": set(EXECUTABLES),
}


def exact_inherited(record, source_record):
    if BASE.exact(record):
        return True
    if source_record:
        for parents, prefix in ((P96.PARENTS, P96.ARCHIVE), (P97.PARENTS, P97.ARCHIVE), (PARENTS, ARCHIVE)):
            if record["path"] in parents and BASE.exact(record, prefix + record["path"]):
                return True
    return False


def inherited():
    pin = BASE.pin(PREVIOUS)
    if pin["bytes"] != 15167 or pin["sha256"] != "50bffa80aaa68b112d325ba60087161a484377fce59b522e2fc9c5c5e798cd96":
        raise ValueError("previous_checkpoint_drift")
    p97 = json.loads((ROOT / PREVIOUS).read_bytes())
    p96 = json.loads((ROOT / P96.CURRENT).read_bytes())
    p95 = json.loads((ROOT / P96.PREVIOUS).read_bytes())
    p96_pin, p95_pin = BASE.pin(P96.CURRENT), BASE.pin(P96.PREVIOUS)
    if (p96_pin != p97["inherited_checkpoint"] or p96_pin["bytes"] != 12952
            or p96_pin["sha256"] != "4aebe074bef35ecca8e5a322b308837f15228f48046a2d3381f1ee8966dc0f13"
            or p95_pin != p96["inherited_checkpoint"] or p95_pin["bytes"] != 253422
            or p95_pin["sha256"] != "9f21a4848e38c89b6ef5858cb0fe668d7a67ca6bb0abdd765cb9fd46d2d65f99"):
        raise ValueError("previous_inheritance_drift")
    count, sources = 0, {}
    for key, records in BASE.groups(p95):
        for record in records:
            count += 1
            if not exact_inherited(record, key == "source_files"):
                raise ValueError("inherited_pin_drift")
        if key == "source_files":
            sources.update({r["path"]: r for r in records})
    if count != 1183 or len(sources) != 803:
        raise ValueError("previous_coverage_drift")
    for data, required, expected_count, expected_sources in (
            (p96, P96.REQUIRED_GROUPS, 1222, 815), (p97, P97.REQUIRED_GROUPS, 1269, 828)):
        for key, expected in required.items():
            records = data[key]
            if len(records) != len(expected) or {r["path"] for r in records} != expected:
                raise ValueError("previous_delta_coverage_drift")
            for record in records:
                count += 1
                if not exact_inherited(record, key == "source_delta"):
                    raise ValueError("inherited_pin_drift")
            if key == "source_delta":
                sources.update({r["path"]: r for r in records})
        if count != expected_count or len(sources) != expected_sources:
            raise ValueError("previous_coverage_drift")
    unchanged, preimages = 0, []
    for record in sources.values():
        if BASE.exact(record):
            unchanged += 1
        elif record["path"] in PARENTS and BASE.exact(record, ARCHIVE + record["path"]):
            preimages.append({**record, "archive_path": ARCHIVE + record["path"]})
        else:
            raise ValueError("current_parent_preimage_drift")
    if unchanged != 825 or len(preimages) != 3:
        raise ValueError("current_parent_coverage_drift")
    for path in PARENTS:
        before = (ROOT / (ARCHIVE + path)).read_bytes()
        after = (ROOT / path).read_bytes()
        declaration = (b'#[path = "actual_import/source_review_delete.rs"]\nmod source_review_delete;\n'
                       if path.endswith("actual_import.rs") else b"pub mod delete_output;\n")
        if after.count(declaration) != 1 or after.replace(declaration, b"", 1) != before:
            raise ValueError("original_parent_body_changed")
    return {"state": "pass_declared_raw_inheritance_and_whole_parent_inverse_NOT_native_or_Gate",
            "previous_checkpoint": pin, "inherited_raw_pin_entries": count,
            "previous_current_source_files": 828, "unchanged_previous_source_files": unchanged,
            "whole_parent_preimages": preimages, "parent_inverse_exact": True,
            "old_executables_preserved_not_reexecuted": 85,
            "all_historical_qualification_reexecuted": False}


def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"]:
        raise ValueError("inherited_checkpoint_binding_drift")
    if data["current_source_files_count"] != 840:
        raise ValueError("current_source_coverage_drift")
    counts = {}
    for key, expected in REQUIRED_GROUPS.items():
        records = data[key]
        if len({r["path"] for r in records}) != len(records) or not all(BASE.exact(r) for r in records):
            raise ValueError("current_raw_pin_drift")
        if {r["path"] for r in records} != expected:
            raise ValueError("current_group_coverage_drift")
        counts[key] = len(records)
    for key in ("native_executed", "actual_SQL_executed", "full_comment_product_acceptance",
                "native_author_time_state_binding", "product_complete", "P10_new_implementation",
                "execution_publication_authority", "full_typed_comment_compiler_route_connected",
                "P11_capability_qualified"):
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
        print(json.dumps({"state": "fail", "error_type": type(error).__name__, "scope": "bytes_NOT_native_acceptance"}))
        raise SystemExit(1) from error
