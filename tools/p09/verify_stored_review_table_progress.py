"""Read-only dual-source stored review table evidence; NOT durable SQL/native/execution."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p104_bytes", Path(__file__).with_name("verify_review_table_output_progress.py"))
P104 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P104)
BASE, ROOT = P104.BASE, P104.ROOT
PREVIOUS = P104.CURRENT
CURRENT = "implementation/p09/evidence/p09-105-stored-review-table.source-progress.v1.json"
ARCHIVE = "implementation/p09/source-archive/p09-105-pre-stored-review-table/"
PARENTS = (
    "crates/product-cli/src/form_stored_provider/actual_import/review.rs",
    "crates/product-cli/tests/form_stored_provider/actual_import.rs",
)
NEW_SOURCES = (
    "crates/product-cli/src/form_stored_provider/actual_import/review/table_output.rs",
    "crates/product-cli/tests/form_stored_provider/actual_import/source_review_table_output.rs",
    "crates/product-cli/tests/form_stored_provider/actual_import/review_table_fixture.rs",
    "tools/p09/verify_stored_review_table_progress.py",
    "tools/p09/tests/test_stored_review_table_progress.py",
    "implementation/p09/P09-105_STORED_REVIEW_TABLE_POLICY.md",
    "implementation/p09/P09-105_STORED_REVIEW_TABLE_REPORT.md",
    "protocol/migrations/p09-stored-review-table-v0-to-v1.md",
    "implementation/p09/evidence/p09-105-stored-review-table.initial-failures.v1.json",
    "implementation/p09/evidence/p09-105-stored-review-table.preservation.v1.json",
    "implementation/p09/evidence/p09-105-stored-review-table.source-regression.v1.json",
)
PREDECESSORS = (PREVIOUS, "implementation/p09/evidence/p09-104-review-table-output.final-audit.v1.json")
EXECUTABLES = [
    "target/p09-105-pre-quarantine-regression/debug/deps/form_stored_provider-e02d02396d2f2bbd.exe",
    "target/p09-105-duplicate-fixture/debug/deps/form_stored_provider-e02d02396d2f2bbd.exe",
    "target/p09-105-stored-review-table/debug/deps/comment_operation-75493e8123c566c8.exe",
    "target/p09-105-stored-review-table/debug/deps/form_stored_provider-e02d02396d2f2bbd.exe",
    "target/p09-105-stored-review-table/debug/deps/hwpx_agent_cli.exe",
    "target/p09-105-stored-review-table/debug/deps/stored_comment_provider-9065c76bcbac10b7.exe"
]
ARCHIVES = [
    "implementation/p09/source-archive/p09-105-pre-quarantine-test/crates/product-cli/tests/form_stored_provider/actual_import/source_review_table_output.rs",
    "implementation/p09/source-archive/p09-105-duplicate-fixture/crates/product-cli/tests/form_stored_provider/actual_import/source_review_table_output.rs",
    "implementation/p09/source-archive/p09-105-initial-build/crates/product-cli/src/form_stored_provider/actual_import/review/table_output.rs",
    "implementation/p09/source-archive/p09-105-initial-build/crates/product-cli/tests/form_stored_provider/actual_import/source_review_table_output.rs",
    "implementation/p09/source-archive/p09-105-pre-stored-review-table/crates/product-cli/src/form_stored_provider/actual_import/review.rs",
    "implementation/p09/source-archive/p09-105-pre-stored-review-table/crates/product-cli/tests/form_stored_provider/actual_import.rs"
]
FALSE_QUALIFICATIONS = P104.FALSE_QUALIFICATIONS + ("durable_stored_table_integration_qualified",)


class PreviousReadView:
    def __init__(self, root):
        self.root = root

    def __truediv__(self, path):
        return self.root / (ARCHIVE + path if path in PARENTS else path)


def original_sources():
    sources = P104.original_sources()
    sources.update({r["path"]: r for r in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 911:
        raise ValueError("prior_source_coverage_drift")
    return sources


def restored_parent(path, current):
    if path == PARENTS[0]:
        added = b"pub mod table_output;\n"
    elif path == PARENTS[1]:
        added = b'#[path = "actual_import/source_review_table_output.rs"]\nmod source_review_table_output;\n'
    else:
        raise ValueError("undeclared_parent")
    if current.count(added) != 1:
        raise ValueError("additive_module_shape_drift")
    return current.replace(added, b"", 1)


def parent_inverses(sources):
    for path in PARENTS:
        if not BASE.exact(sources[path], ARCHIVE + path):
            raise ValueError("parent_whole_preimage_drift")
        if restored_parent(path, (ROOT / path).read_bytes()) != (ROOT / (ARCHIVE + path)).read_bytes():
            raise ValueError("undeclared_original_parent_change")


def previous_audit():
    old_module, old_base = P104.ROOT, BASE.ROOT
    try:
        P104.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        return P104.current()
    finally:
        P104.ROOT, BASE.ROOT = old_module, old_base


def inherited():
    checkpoint = BASE.pin(PREVIOUS)
    if checkpoint["bytes"] != 19684 or checkpoint["sha256"] != "d786eae5bd4e809f2c4392e7dc3ffc61dacb10010acfe3dab0f4d92a0aec621c":
        raise ValueError("previous_checkpoint_drift")
    final = BASE.pin(PREDECESSORS[1])
    if final["bytes"] != 4106 or final["sha256"] != "ab0dbd86e84b890192339cbb76963ace8195b84faf40ac3f657bc4888d64b925":
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    parent_inverses(sources)
    prior = previous_audit()
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if prior["checkpoint"] != checkpoint or raw != 1617:
        raise ValueError("prior_raw_coverage_drift")
    unchanged, preimages = 0, []
    for record in sources.values():
        if BASE.exact(record):
            unchanged += 1
        elif record["path"] in PARENTS and BASE.exact(record, ARCHIVE + record["path"]):
            preimages.append({**record, "archive_path": ARCHIVE + record["path"]})
        else:
            raise ValueError("prior_source_drift")
    if unchanged != 909 or len(preimages) != 2:
        raise ValueError("prior_source_or_parent_coverage_drift")
    return {
        "state": "pass_prior_raw_and_whole_parent_inverses_NOT_durable_SQL_native_or_Gate",
        "previous_checkpoint": checkpoint, "inherited_raw_pin_entries": raw,
        "previous_current_source_files": 911, "unchanged_previous_source_files": unchanged,
        "whole_parent_preimages": preimages, "parent_inverse_exact": True,
        "previous_unchanged_audit_passed_on_exact_parent_preimages": True,
        "old_executables_preserved": 233,
        "old_executables_all_reexecuted": False, "all_historical_qualification_reexecuted": False,
    }


def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 922:
        raise ValueError("checkpoint_or_source_coverage_drift")
    required = {"source_delta": set(PARENTS + NEW_SOURCES), "source_archives_added": set(ARCHIVES),
                "predecessor_receipts_added": set(PREDECESSORS), "current_executables": set(EXECUTABLES)}
    counts = {}
    for key, paths in required.items():
        records = data[key]
        if len(records) != len(paths) or {r["path"] for r in records} != paths:
            raise ValueError("current_group_coverage_drift")
        if not all(BASE.exact(r) for r in records):
            raise ValueError("current_raw_pin_drift")
        counts[key] = len(records)
    for key in FALSE_QUALIFICATIONS:
        if data["qualification"][key] is not False:
            raise ValueError("unsupported_acceptance_promotion")
    if data["qualification"]["stored_source_and_template_table_output_authenticated"] is not True:
        raise ValueError("dual_source_output_evidence_missing")
    if data["qualification"]["P09_gate"] != "OPEN" or (ROOT / "PLANS.md").exists():
        raise ValueError("gate_or_deleted_plan_changed")
    return counts


def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_scoped_inheritance_and_dual_source_stored_table_delta_NOT_durable_SQL_native_full_product_or_Gate",
            "checkpoint": BASE.pin(CURRENT), "inherited_raw_pin_entries": prior["inherited_raw_pin_entries"],
            "current_groups": verify_current_manifest(data, prior), "P09_gate": "OPEN", "product_complete": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(current() if args.current else inherited(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "fail", "error_type": type(error).__name__, "scope": "bytes_NOT_durable_SQL_native_or_Gate"}))
        raise SystemExit(1) from error

