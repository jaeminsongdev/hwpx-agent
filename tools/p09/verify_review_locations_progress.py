"""Read-only P09-99 exact prior/current byte audit; never native position/product authority."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p98_bytes", Path(__file__).with_name("verify_review_delete_progress.py"))
P98 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P98)
BASE, ROOT = P98.BASE, P98.ROOT
PREVIOUS = P98.CURRENT
CURRENT = "implementation/p09/evidence/p09-99-review-locations.source-progress.v1.json"
ARCHIVE = "implementation/p09/source-archive/p09-99-pre-review-locations/"
PARENTS = P98.PARENTS
NEW_SOURCES = (
    "crates/hwpx-package/src/document_import/structure/review/locations.rs",
    "crates/product-cli/src/form_stored_provider/actual_import/review/locations.rs",
    "crates/hwpx-package/tests/review_locations.rs",
    "crates/product-cli/tests/form_stored_provider/actual_import/source_review_locations.rs",
    "tools/p09/verify_review_locations_progress.py",
    "tools/p09/tests/test_review_locations_progress.py",
    "implementation/p09/P09-99_REVIEW_LOCATIONS_POLICY.md",
    "implementation/p09/P09-99_REVIEW_LOCATIONS_REPORT.md",
    "protocol/migrations/p09-review-locations-v0-to-v1.md",
    "implementation/p09/evidence/p09-99-review-locations.initial-failures.v1.json",
    "implementation/p09/evidence/p09-99-review-locations.preservation.v1.json",
    "implementation/p09/evidence/p09-99-review-locations.source-regression.v1.json",
)
PREDECESSORS = (PREVIOUS, "implementation/p09/evidence/p09-98-review-delete.final-audit.v1.json")
EXECUTABLES = tuple(p.replace("p09-98", "p09-99") for p in P98.EXECUTABLES) + (
    "target/p09-99-package/debug/deps/review_locations-64747444168c92b2.exe",
)
REQUIRED_GROUPS = {
    "source_delta": set(PARENTS + NEW_SOURCES),
    "source_archives_added": {ARCHIVE + p for p in PARENTS} | {
        "implementation/p09/source-archive/p09-99-initial-compile-failure/" + NEW_SOURCES[0],
    },
    "predecessor_receipts_added": set(PREDECESSORS),
    "current_executables": set(EXECUTABLES),
}


class PreviousReadView:
    """Only known parent reads use exact frozen preimages; no writes or disk mutations."""
    def __init__(self, root):
        self.root = root

    def __truediv__(self, path):
        return self.root / (ARCHIVE + path if path in PARENTS else path)


def parent_inverses(prior):
    pins = {p["path"]: p for p in prior["source_delta"]}
    for path in PARENTS:
        if not BASE.exact(pins[path], ARCHIVE + path):
            raise ValueError("current_parent_whole_preimage_drift")
        before = (ROOT / (ARCHIVE + path)).read_bytes()
        after = (ROOT / path).read_bytes()
        declaration = (b'#[path = "actual_import/source_review_locations.rs"]\nmod source_review_locations;\n'
                       if path.endswith("actual_import.rs") else b"pub mod locations;\n")
        if after.count(declaration) != 1 or after.replace(declaration, b"", 1) != before:
            raise ValueError("original_parent_body_changed")


def previous_audit():
    # Run the UNCHANGED predecessor audit on its exact parent bytes, not on new source.
    # Only after whole preimages and exact current inverses have been proven.
    old_module_root, old_base_root = P98.ROOT, BASE.ROOT
    try:
        view = PreviousReadView(ROOT)
        P98.ROOT = BASE.ROOT = view
        return P98.current()
    finally:
        P98.ROOT, BASE.ROOT = old_module_root, old_base_root


def inherited():
    pin = BASE.pin(PREVIOUS)
    if pin["bytes"] != 10168 or pin["sha256"] != "0ee405068fb4f98368b416dc131d0edf043d01175296ba036decf566629539ab":
        raise ValueError("previous_checkpoint_drift")
    if BASE.pin(PREDECESSORS[1])["sha256"] != "b72bafef4f4d9aaa28b9b73f507e8a39569c5caf29d9cdd7c264ed59dfbec4fc":
        raise ValueError("previous_final_audit_drift")
    p98 = json.loads((ROOT / PREVIOUS).read_bytes())
    parent_inverses(p98)
    previous = previous_audit()
    if previous["checkpoint"] != pin or previous["inherited_raw_pin_entries"] != 1269:
        raise ValueError("previous_audit_scope_drift")
    raw_pins = previous["inherited_raw_pin_entries"] + sum(previous["current_groups"].values())
    if raw_pins != 1310:
        raise ValueError("previous_raw_coverage_drift")
    sources = {p["path"]: p for p in json.loads((ROOT / P98.P96.PREVIOUS).read_bytes())["source_files"]}
    for checkpoint in (P98.P96.CURRENT, P98.P97.CURRENT, PREVIOUS):
        data = json.loads((ROOT / checkpoint).read_bytes())
        sources.update({p["path"]: p for p in data["source_delta"]})
    if len(sources) != 840:
        raise ValueError("previous_source_coverage_drift")
    unchanged, preimages = 0, []
    for record in sources.values():
        if BASE.exact(record):
            unchanged += 1
        elif record["path"] in PARENTS and BASE.exact(record, ARCHIVE + record["path"]):
            preimages.append({**record, "archive_path": ARCHIVE + record["path"]})
        else:
            raise ValueError("current_source_drift")
    if unchanged != 837 or len(preimages) != 3:
        raise ValueError("current_parent_coverage_drift")
    return {"state": "pass_declared_raw_prior_view_and_exact_parent_inverse_NOT_native_or_Gate",
            "previous_checkpoint": pin, "inherited_raw_pin_entries": raw_pins,
            "previous_current_source_files": 840, "unchanged_previous_source_files": unchanged,
            "whole_parent_preimages": preimages, "parent_inverse_exact": True,
            "previous_unchanged_audit_passed_on_exact_parent_preimages": True,
            "old_executables_preserved_not_reexecuted": 100,
            "all_historical_qualification_reexecuted": False}


def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"]:
        raise ValueError("inherited_checkpoint_binding_drift")
    if data["current_source_files_count"] != 852:
        raise ValueError("current_source_coverage_drift")
    counts = {}
    for key, expected in REQUIRED_GROUPS.items():
        records = data[key]
        if len(records) != len(expected) or {r["path"] for r in records} != expected:
            raise ValueError("current_group_coverage_drift")
        if not all(BASE.exact(r) for r in records):
            raise ValueError("current_raw_pin_drift")
        counts[key] = len(records)
    for key in ("native_executed", "actual_SQL_executed", "full_comment_product_acceptance",
                "native_author_time_state_binding", "product_complete", "P10_new_implementation",
                "execution_publication_authority", "full_typed_comment_compiler_route_connected",
                "native_caret_or_visual_coordinates_verified"):
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
        print(json.dumps({"state": "fail", "error_type": type(error).__name__, "scope": "bytes_NOT_native_positions"}))
        raise SystemExit(1) from error
