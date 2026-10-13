"""Read-only original authenticated persisted rich Flow/compiler evidence; NOT native/SQL/publication."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p108_bytes", Path(__file__).with_name("verify_rich_comment_flow_progress.py"))
P108 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P108)
BASE, ROOT = P108.BASE, P108.ROOT
PREVIOUS = P108.CURRENT
CURRENT = "implementation/p09/evidence/p09-109-stored-rich-comment.source-progress.v1.json"
ARCHIVE = "implementation/p09/source-archive/p09-109-pre-stored-rich-comment/"
PARENTS = (
    "crates/product-cli/src/form_stored_provider/comments.rs",
    "crates/product-cli/tests/stored_comment_provider.rs",
)
NEW_SOURCES = (
    "crates/product-cli/src/form_stored_provider/comments/rich_bodies.rs",
    "crates/product-cli/tests/stored_comment_provider/rich_bodies.rs",
    "tools/p09/verify_stored_rich_comment_progress.py",
    "tools/p09/tests/test_stored_rich_comment_progress.py",
    "implementation/p09/P09-109_STORED_RICH_COMMENT_POLICY.md",
    "implementation/p09/P09-109_STORED_RICH_COMMENT_REPORT.md",
    "protocol/migrations/p09-stored-rich-comment-v0-to-v1.md",
    "implementation/p09/evidence/p09-109-stored-rich-comment.initial-failures.v1.json",
    "implementation/p09/evidence/p09-109-stored-rich-comment.preservation.v1.json",
    "implementation/p09/evidence/p09-109-stored-rich-comment.source-regression.v1.json",
)
PREDECESSORS = (PREVIOUS, "implementation/p09/evidence/p09-108-rich-comment-flow.final-audit.v1.json")
# These inventories are frozen to actual build outputs after tests, not a glob/passing-test count.
EXECUTABLES = [
    "target/p09-109-stored-rich-comment/debug/deps/comment_operation-75493e8123c566c8.exe",
    "target/p09-109-stored-rich-comment/debug/deps/form_stored_provider-e02d02396d2f2bbd.exe",
    "target/p09-109-stored-rich-comment/debug/deps/hwpx_agent_cli.exe",
    "target/p09-109-stored-rich-comment/debug/deps/stored_comment_provider-9065c76bcbac10b7.exe",
    "target/p09-109-stored-rich-comment/debug/deps/stored_comment_provider-9065c76bcbac10b7-failed-oversized-ir.exe",
]
ARCHIVES = [ARCHIVE + p for p in PARENTS] + [
    "implementation/p09/source-archive/p09-109-failed-test-compilation/rich_bodies.rs",
    "implementation/p09/source-archive/p09-109-failed-quarantine-return/rich_bodies.rs",
    "implementation/p09/source-archive/p09-109-failed-oversized-ir-construction/rich_bodies.rs",
]
FALSE_QUALIFICATIONS = P108.FALSE_QUALIFICATIONS + ("durable_stored_full_rich_flow_integration_qualified",)


class PreviousReadView:
    def __init__(self, root):
        self.root = root

    def __truediv__(self, path):
        return self.root / (ARCHIVE + path if path in PARENTS else path)


def original_sources():
    sources = P108.original_sources()
    sources.update({r["path"]: r for r in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 952:
        raise ValueError("prior_source_coverage_drift")
    return sources


def restored_parent(path, current):
    if path not in PARENTS:
        raise ValueError("undeclared_parent")
    added = (b"pub mod rich_bodies;\n" if path == PARENTS[0] else
             b'#[path = "stored_comment_provider/rich_bodies.rs"]\nmod rich_bodies;\n')
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
    old_module, old_base = P108.ROOT, BASE.ROOT
    try:
        P108.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        return P108.current()
    finally:
        P108.ROOT, BASE.ROOT = old_module, old_base


def inherited():
    checkpoint = BASE.pin(PREVIOUS)
    if checkpoint["bytes"] != 10971 or checkpoint["sha256"] != "ce8d77cbd14653f20610cdcc48f503d0114b32faa7290f54abba2a982564956d":
        raise ValueError("previous_checkpoint_drift")
    final = BASE.pin(PREDECESSORS[1])
    if final["bytes"] != 5597 or final["sha256"] != "10206875d9358b63248e16e61855ec74230a74782f5c2ca01e95dbe0afa6db92":
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    parent_inverses(sources)
    prior = previous_audit()
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if prior["checkpoint"] != checkpoint or raw != 1739:
        raise ValueError("prior_raw_coverage_drift")
    unchanged, preimages = 0, []
    for record in sources.values():
        if BASE.exact(record):
            unchanged += 1
        elif record["path"] in PARENTS and BASE.exact(record, ARCHIVE + record["path"]):
            preimages.append({**record, "archive_path": ARCHIVE + record["path"]})
        else:
            raise ValueError("prior_source_drift")
    if unchanged != 950 or len(preimages) != 2:
        raise ValueError("prior_source_or_parent_coverage_drift")
    return {
        "state": "pass_prior_raw_and_whole_parent_inverse_NOT_full_Flow_SQL_native_or_Gate",
        "previous_checkpoint": checkpoint, "inherited_raw_pin_entries": raw,
        "previous_current_source_files": 952, "unchanged_previous_source_files": unchanged,
        "whole_parent_preimages": preimages, "parent_inverse_exact": True,
        "previous_unchanged_audit_passed_on_exact_parent_preimages": True,
        "old_executables_preserved": 278,
        "old_executables_all_reexecuted": False, "all_historical_qualification_reexecuted": False,
    }


def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 962:
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
    if data["qualification"]["stored_rich_body_authenticated_final_compiler_bound"] is not True:
        raise ValueError("rich_body_compiler_evidence_missing")
    if data["qualification"]["P09_gate"] != "OPEN" or (ROOT / "PLANS.md").exists():
        raise ValueError("gate_or_deleted_plan_changed")
    return counts


def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_scoped_authenticated_stored_rich_body_final_compiler_binding_NOT_native_SQL_durability_execution_publication_or_Gate",
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
