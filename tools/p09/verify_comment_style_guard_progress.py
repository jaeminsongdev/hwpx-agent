"""P127 exact one-parent inverse and immutable historical audit; not native/Gate qualification."""
import importlib.util
import argparse
import json
import types
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p126_old", Path(__file__).with_name("audit_scoped_stored_regression.py"))
OLD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OLD)
ROOT = OLD.R.ROOT
PARENT = "crates/domain-ir/src/comment_model.rs"
ARCHIVE = "implementation/p09/source-archive/p09-127-pre-comment-style-anchor/" + PARENT
PREVIOUS = OLD.CURRENT
CURRENT = "implementation/p09/evidence/p09-127-comment-style-guard.source-progress.v1.json"
RUN_ROOT = "target/p09-121-resource-optimized/"
EXE = RUN_ROOT + "debug/deps/comment_style_section_protection-b84c0126440d38be.exe"
FAILED_EXE = EXE.removesuffix(".exe") + "-p127-initial.exe"
DELTA = [PARENT, "crates/domain-ir/tests/comment_style_section_protection.rs",
         "tools/p09/run_comment_style_guard.ps1", "tools/p09/verify_comment_style_guard_progress.py",
         "tools/p09/tests/test_comment_style_guard_progress.py",
         "implementation/p09/P09-127_COMMENT_STYLE_SECTION_PROTECTION_REPORT.md"]
RUNS = [RUN_ROOT + f"p127-comment-style-{kind}-{stage}.json"
        for stage in ("initial", "fixed") for kind in ("build", "tests")]
COLLECTION = b"""    // A comment can reference a different style from its section's default.
    // Check its actual anchor section too, without a section scan per comment.
    let locked_sections: BTreeSet<_> = target
        .sections
        .iter()
        .filter(|section| section.locked)
        .map(|section| &section.section_id)
        .collect();
"""
BEFORE = b"            .any(|comment| comment.style_id == style_id && comment.locked)\n"
AFTER = b"""            .any(|comment| {
                comment.style_id == style_id
                    && (comment.locked || locked_sections.contains(&comment.anchor.section_id))
            })
"""


def validate_inverse(before, after):
    OLD.R.P123.require(after.count(COLLECTION) == 1 and after.count(AFTER) == 1,
                       "declared_parent_edit_missing_or_duplicate")
    OLD.R.P123.require(after.replace(COLLECTION, b"", 1).replace(AFTER, BEFORE, 1) == before,
                       "undeclared_parent_edit")


class ArchivedParentReadView:
    def __fspath__(self):
        # cwd remains the real workspace; only explicit file reads redirect one parent.
        return str(ROOT)

    def __truediv__(self, path):
        return ROOT / (ARCHIVE if str(path) == PARENT else path)


def historical_previous():
    base = OLD.R.BASE
    OLD.R.P123.require(base.pin(PREVIOUS) == {
        "path": PREVIOUS, "bytes": 31675,
        "sha256": "29cb739b3dcf38230e52b9bf6aa248d00d392fbbeb6285681f2c64b7290632b4"
    }, "P126_checkpoint_drift")
    OLD.R.P123.require(base.pin(ARCHIVE) == {
        "path": ARCHIVE, "bytes": 55408,
        "sha256": "aa332c72c54480442cf64bf540ce8e75d89817c6620c3fc0b4141bc299956e1b"
    }, "whole_parent_preimage_drift")
    validate_inverse((ROOT / ARCHIVE).read_bytes(), (ROOT / PARENT).read_bytes())
    # Only redirect ROOT reads of this exact declared parent. No old guards/functions are replaced.
    # Original nested preimage views compose with this view through their original ROOT value.
    pending, visited, roots = [OLD], set(), []
    instruction_dir = Path(__file__).parent.resolve()
    while pending:
        module = pending.pop()
        if id(module) in visited:
            continue
        visited.add(id(module))
        if isinstance(getattr(module, "ROOT", None), Path) and module.ROOT == ROOT:
            roots.append((module, module.ROOT))
        for value in vars(module).values():
            if isinstance(value, types.ModuleType) and getattr(value, "__file__", None):
                if Path(value.__file__).resolve().parent == instruction_dir:
                    pending.append(value)
    OLD.R.P123.require(roots, "historical_module_roots_missing")
    try:
        for module, _ in roots:
            module.ROOT = ArchivedParentReadView()
        result = OLD.audit()
    finally:
        for module, original_root in roots:
            module.ROOT = original_root
    return {"state": "PASS_P126_HISTORICAL_ON_WHOLE_PREIMAGE_NOT_CURRENT_REGRESSION",
            "historical_scoped_cases": result["actual_import"] + result["documents"] + result["roots"],
            "previous_source_files": 1131, "whole_parent_preimages": 1, "inverse_bytes_exact": True,
            "old_guards_unmodified": True, "current_all_case_regression_accepted": False,
            "P09_gate": "OPEN", "product_complete": False}


def current():
    historical_previous()
    require, base = OLD.R.P123.require, OLD.R.BASE
    doc = json.loads((ROOT / CURRENT).read_bytes())
    groups = {"source_delta": DELTA, "source_archives": [ARCHIVE, RUN_ROOT + "p127-initial-preimage-audit.py.txt"],
              "predecessor_receipts_added": [PREVIOUS], "current_executables": [EXE, FAILED_EXE],
              "runtime_runs": RUNS}
    for key, paths in groups.items():
        rows = doc[key]
        require(len(rows) == len(paths) and {r["path"] for r in rows} == set(paths)
                and all(base.exact(row) for row in rows), "current_pin_coverage_drift")
    require(doc["current_source_files_count"] == 1136 and doc["previous_source_files_count"] == 1131
            and doc["inherited_raw_pin_entries"] == 2592, "current_source_coverage_drift")
    runs = [json.loads((ROOT / path).read_bytes()) for path in RUNS]
    for index, run in enumerate(runs):
        require(run["source_freeze_exact_after"] is True and run["stop_reason"] is None
                and run["logical_cpu_limit"] == 1 and run["affinity_mask"] == 1 and run["priority"] == "BelowNormal"
                and run["cpu_stop_percent"] == 85 and run["cpu_stop_consecutive_samples"] == 3
                and run["minimum_available_ram_mib"] == 4096 and run["maximum_root_working_set_mib"] == 2048
                and run["sample_seconds"] == 2 and run["product_complete"] is False and run["P09_gate"] == "OPEN",
                "runtime_policy_or_scope_drift")
        require(len(run["source_freeze"]) == 3 and all(base.exact(row, ARCHIVE if index < 2 and row["path"] == PARENT else None)
                                                    for row in run["source_freeze"]), "runtime_source_drift")
    initial, fixed = runs[1], runs[3]
    require(initial["exit_code"] == 101 and initial["tests"]["terminal_summary"]["passed"] == 3
            and initial["tests"]["terminal_summary"]["failed"] == 1
            and initial["tests"]["failed_test_names"] == ["locked_anchor_section_rejects_comment_style_even_when_its_default_style_differs"],
            "initial_counterexample_drift")
    for index in (0, 2, 3):
        require(runs[index]["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and runs[index]["exit_code"] == 0,
                "fixed_or_build_not_accepted")
    require(fixed["tests"]["terminal_summary"]["passed"] == 4
            and fixed["tests"]["terminal_summary"]["failed"] == 0
            and fixed["tests"]["terminal_summary"]["ignored"] == 0
            and fixed["tests"]["terminal_summary"]["filtered"] == 0
            and len(set(fixed["tests"]["passed_test_names"])) == 4
            and fixed["executable_pin"] == base.pin(EXE), "fixed_tests_or_executable_drift")
    failed = base.pin(FAILED_EXE)
    require(all(failed[k] == initial["executable_pin"][k] for k in ("bytes", "sha256")), "failed_executable_lost")
    require(doc["current_all_case_regression_accepted"] is False and doc["product_complete"] is False
            and doc["P09_gate"] == "OPEN" and doc["P10_new_implementation"] is False and doc["goal_status"] == "active",
            "scope_promoted")
    return {"state": "PASS_COMMENT_STYLE_LOCKED_ANCHOR_GUARD_NOT_GATE", "initial_passed": 3,
            "initial_failed": 1, "fixed_passed": 4, "inverse_bytes_exact": True,
            "historical_scoped228_preserved": True, "current_all_case_regression_accepted": False,
            "current_source_files": 1136, "P09_gate": "OPEN", "product_complete": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(current() if args.current else historical_previous(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "FAIL_CLOSED", "error_type": type(error).__name__, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
