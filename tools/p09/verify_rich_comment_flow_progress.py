"""Read-only explicit caller rich Flow/compiler evidence; NOT native/source/SQL/publication."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p107_bytes", Path(__file__).with_name("verify_stored_filled_table_progress.py"))
P107 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P107)
BASE, ROOT = P107.BASE, P107.ROOT
PREVIOUS = P107.CURRENT
CURRENT = "implementation/p09/evidence/p09-108-rich-comment-flow.source-progress.v1.json"
ARCHIVE = "implementation/p09/source-archive/p09-108-pre-rich-comment-flow/"
PARENTS = (
    "crates/product-cli/src/comment_operation.rs",
    "crates/product-cli/tests/comment_operation.rs",
)
NEW_SOURCES = (
    "crates/product-cli/src/comment_operation/rich_bodies.rs",
    "crates/product-cli/tests/comment_operation/rich_bodies.rs",
    "tools/p09/verify_rich_comment_flow_progress.py",
    "tools/p09/tests/test_rich_comment_flow_progress.py",
    "implementation/p09/P09-108_RICH_COMMENT_FLOW_POLICY.md",
    "implementation/p09/P09-108_RICH_COMMENT_FLOW_REPORT.md",
    "protocol/migrations/p09-rich-comment-flow-v0-to-v1.md",
    "implementation/p09/evidence/p09-108-rich-comment-flow.initial-failures.v1.json",
    "implementation/p09/evidence/p09-108-rich-comment-flow.preservation.v1.json",
    "implementation/p09/evidence/p09-108-rich-comment-flow.source-regression.v1.json",
)
PREDECESSORS = (PREVIOUS, "implementation/p09/evidence/p09-107-stored-filled-table.final-audit.v1.json")
# These inventories are frozen to actual build outputs after tests, not a glob/passing-test count.
EXECUTABLES = [
    "target/p09-108-rich-comment-flow/debug/deps/comment_operation-75493e8123c566c8-pre-insertion-budget.exe",
    "target/p09-108-rich-comment-flow/debug/deps/form_stored_provider-e02d02396d2f2bbd-pre-insertion-budget.exe",
    "target/p09-108-rich-comment-flow/debug/deps/hwpx_agent_cli-pre-insertion-budget.exe",
    "target/p09-108-rich-comment-flow/debug/deps/stored_comment_provider-9065c76bcbac10b7-pre-insertion-budget.exe",
    "target/p09-108-rich-comment-flow/debug/deps/comment_operation-75493e8123c566c8-pre-lint-refactor.exe",
    "target/p09-108-rich-comment-flow/debug/deps/form_stored_provider-e02d02396d2f2bbd-pre-lint-refactor.exe",
    "target/p09-108-rich-comment-flow/debug/deps/hwpx_agent_cli-pre-lint-refactor.exe",
    "target/p09-108-rich-comment-flow/debug/deps/stored_comment_provider-9065c76bcbac10b7-pre-lint-refactor.exe",
    "target/p09-108-rich-comment-flow/debug/deps/comment_operation-75493e8123c566c8-failed-protected-body.exe",
    "target/p09-108-rich-comment-flow/debug/deps/comment_operation-75493e8123c566c8.exe",
    "target/p09-108-rich-comment-flow/debug/deps/form_stored_provider-e02d02396d2f2bbd.exe",
    "target/p09-108-rich-comment-flow/debug/deps/hwpx_agent_cli.exe",
    "target/p09-108-rich-comment-flow/debug/deps/stored_comment_provider-9065c76bcbac10b7.exe",
]
ARCHIVES = [ARCHIVE + p for p in PARENTS] + [
    "implementation/p09/source-archive/p09-108-pre-insertion-budget/production-rich_bodies.rs",
    "implementation/p09/source-archive/p09-108-pre-insertion-budget/test-rich_bodies.rs",
    "implementation/p09/source-archive/p09-108-failed-strict-lint/rich_bodies.rs",
    "implementation/p09/source-archive/p09-108-pre-debug-warning/crates/product-cli/src/comment_operation/rich_bodies.rs",
    "implementation/p09/source-archive/p09-108-failed-test-compilation/rich_bodies.rs",
    "implementation/p09/source-archive/p09-108-failed-protected-body/production-rich_bodies.rs",
    "implementation/p09/source-archive/p09-108-failed-protected-body/test-rich_bodies.rs",
]
FALSE_QUALIFICATIONS = P107.FALSE_QUALIFICATIONS + ("actual_native_full_rich_comment_route_qualified",)


class PreviousReadView:
    def __init__(self, root):
        self.root = root

    def __truediv__(self, path):
        return self.root / (ARCHIVE + path if path in PARENTS else path)


def original_sources():
    sources = P107.original_sources()
    sources.update({r["path"]: r for r in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 942:
        raise ValueError("prior_source_coverage_drift")
    return sources


def restored_parent(path, current):
    if path not in PARENTS:
        raise ValueError("undeclared_parent")
    added = (b"pub mod rich_bodies;\n" if path == PARENTS[0] else
             b'#[path = "comment_operation/rich_bodies.rs"]\nmod rich_bodies;\n')
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
    old_module, old_base = P107.ROOT, BASE.ROOT
    try:
        P107.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        return P107.current()
    finally:
        P107.ROOT, BASE.ROOT = old_module, old_base


def inherited():
    checkpoint = BASE.pin(PREVIOUS)
    if checkpoint["bytes"] != 7400 or checkpoint["sha256"] != "f6169feeae378c97a9f09fee81821bb56ee1b69df35f49ea78bea3e551b7631a":
        raise ValueError("previous_checkpoint_drift")
    final = BASE.pin(PREDECESSORS[1])
    if final["bytes"] != 4269 or final["sha256"] != "ba3581d89fedc39f6e18eb1e2f7cc6f2caf12e8231868754a0800ea636cdab64":
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    parent_inverses(sources)
    prior = previous_audit()
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if prior["checkpoint"] != checkpoint or raw != 1703:
        raise ValueError("prior_raw_coverage_drift")
    unchanged, preimages = 0, []
    for record in sources.values():
        if BASE.exact(record):
            unchanged += 1
        elif record["path"] in PARENTS and BASE.exact(record, ARCHIVE + record["path"]):
            preimages.append({**record, "archive_path": ARCHIVE + record["path"]})
        else:
            raise ValueError("prior_source_drift")
    if unchanged != 940 or len(preimages) != 2:
        raise ValueError("prior_source_or_parent_coverage_drift")
    return {
        "state": "pass_prior_raw_and_whole_parent_inverse_NOT_full_Flow_SQL_native_or_Gate",
        "previous_checkpoint": checkpoint, "inherited_raw_pin_entries": raw,
        "previous_current_source_files": 942, "unchanged_previous_source_files": unchanged,
        "whole_parent_preimages": preimages, "parent_inverse_exact": True,
        "previous_unchanged_audit_passed_on_exact_parent_preimages": True,
        "old_executables_preserved": 265,
        "old_executables_all_reexecuted": False, "all_historical_qualification_reexecuted": False,
    }


def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 952:
        raise ValueError("checkpoint_or_source_coverage_drift")
    required = {"source_delta": set(PARENTS + NEW_SOURCES), "source_archives_added": set(ARCHIVES),
                "predecessor_receipts_added": set(PREDECESSORS), "current_executables": set(EXECUTABLES)}
    if not EXECUTABLES:
        raise ValueError("unfrozen_executable_inventory")
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
    if data["qualification"]["caller_complete_rich_comment_flow_final_compiler_bound"] is not True:
        raise ValueError("rich_body_compiler_evidence_missing")
    if data["qualification"]["P09_gate"] != "OPEN" or (ROOT / "PLANS.md").exists():
        raise ValueError("gate_or_deleted_plan_changed")
    return counts


def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_scoped_caller_rich_Flow_final_compiler_binding_NOT_actual_source_SQL_native_product_or_Gate",
            "checkpoint": BASE.pin(CURRENT), "inherited_raw_pin_entries": prior["inherited_raw_pin_entries"],
            "current_groups": verify_current_manifest(data, prior), "P09_gate": "OPEN", "product_complete": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(current() if args.current else inherited(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "fail", "error_type": type(error).__name__, "scope": "bytes_NOT_full_Flow_SQL_native_or_Gate"}))
        raise SystemExit(1) from error
