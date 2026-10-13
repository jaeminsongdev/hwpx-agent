"""Read-only P09-101 source preservation; no DB, native, cause or Gate acceptance."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p100_bytes", Path(__file__).with_name("verify_review_cell_body_progress.py"))
P100 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P100)
BASE, ROOT = P100.BASE, P100.ROOT
PREVIOUS = P100.CURRENT
CURRENT = "implementation/p09/evidence/p09-101-oracle-diagnostics.source-progress.v1.json"
ARCHIVE = "implementation/p09/source-archive/p09-101-pre-oracle-diagnostics/"
PARENTS = tuple(["tools/p09/run_stored_source_policy_postgres_checks.py","crates/product-cli/examples/stored_source_policy_postgres_probe/worker.rs"])
TRANSFORMS = {"tools/p09/run_stored_source_policy_postgres_checks.py":[["from tools.p09.run_stored_full_request_postgres_checks import CONTEXT\n","from tools.p09.run_stored_full_request_postgres_checks import CONTEXT\nfrom tools.p09 import source_policy_oracle_diagnostics as oracle_diagnostics\n"],["        'crates/product-cli/examples/stored_source_policy_postgres_probe/worker.rs',\n","        'crates/product-cli/examples/stored_source_policy_postgres_probe/worker.rs',\n        'crates/product-cli/examples/stored_source_policy_postgres_probe/worker/oracle_snapshot.rs',\n        'crates/product-cli/examples/stored_source_policy_postgres_probe/worker/oracle_snapshot.sql',\n        'tools/p09/source_policy_oracle_diagnostics.py',\n"],["            receipt['safe_sql_fixture_reasons'] = sorted(set(re.findall(r'\\b(?:FORM_POLICY|TEST_POLICY|IDEMPOTENCY|TEST_AUTHORIZED_IR)_[A-Z0-9_]{1,96}\\b', child.stderr)))","            fixture_texts = [h.load_bounded_text(ROOT/path, 1024*1024) for path in (\n                'tools/p14/fixtures/p14_idempotency_reconciliation_smoke.sql',\n                'tools/p09/fixtures/authorized_full_ir_intent.sql', 'tools/p09/fixtures/source_form_policy.sql')]\n            allowed_reasons = oracle_diagnostics.literal_reason_codes(list(texts.values()) + fixture_texts)\n            receipt['safe_sql_fixture_reasons'] = oracle_diagnostics.closed_literal_reasons(child.stderr, allowed_reasons)\n            if stage == 'real_encrypted_policy_sealed_source_seed':\n                receipt['owned_oracle_observation'] = oracle_diagnostics.capture(\n                    ROOT, child.stderr, environment,\n                    lambda text: h.psql(docker, container, text, check=False))"]],"crates/product-cli/examples/stored_source_policy_postgres_probe/worker.rs":[["//! Actual disposable SQL leases and policy entry points; no minted product/native authority.\n","//! Actual disposable SQL leases and policy entry points; no minted product/native authority.\nmod oracle_snapshot;\n"],["    let row=db(c.query_one(\"SELECT * FROM hwpx_agent.complete_idempotent_job_success_v2(","    let completion=c.query_one(\"SELECT * FROM hwpx_agent.complete_idempotent_job_success_v2("],["        &req.new_revision_id().as_uuid(),&receipt.as_uuid(),&\"7\".repeat(64)]))?;","        &req.new_revision_id().as_uuid(),&receipt.as_uuid(),&\"7\".repeat(64)]);\n    if completion.is_err() {\n        oracle_snapshot::observe(req, l, receipt);\n    }\n    let row=db(completion)?;"]]}
NEW_SOURCES = tuple(["crates/product-cli/examples/stored_source_policy_postgres_probe/worker/oracle_snapshot.rs","crates/product-cli/examples/stored_source_policy_postgres_probe/worker/oracle_snapshot.sql","tools/p09/source_policy_oracle_diagnostics.py","tools/p09/tests/test_source_policy_oracle_diagnostics.py","tools/p09/verify_source_policy_oracle_progress.py","tools/p09/tests/test_source_policy_oracle_progress.py","implementation/p09/P09-101_SQL_ORACLE_DIAGNOSTICS_POLICY.md","implementation/p09/P09-101_SQL_ORACLE_DIAGNOSTICS_REPORT.md","protocol/migrations/p09-owned-oracle-diagnostics-v0-to-v1.md","implementation/p09/evidence/p09-101-oracle-diagnostics.initial-failures.v1.json","implementation/p09/evidence/p09-101-oracle-diagnostics.preservation.v1.json","implementation/p09/evidence/p09-101-oracle-diagnostics.source-regression.v1.json"])
PREDECESSORS = (PREVIOUS, "implementation/p09/evidence/p09-100-review-cell-body.final-audit.v1.json")
EXECUTABLES = (
    "target/p09-101-diagnostics/debug/examples/stored_source_policy_postgres_probe-b39470de4fcebdcb.exe",
    "target/p09-101-diagnostics/debug/deps/artifact_service-c722486ab67dc904.exe",
    "target/p09-101-diagnostics/debug/deps/revision_service-1b137e63992c86e2.exe",
)
REQUIRED_GROUPS = {
    "source_delta": set(PARENTS + NEW_SOURCES),
    "source_archives_added": {ARCHIVE + p for p in PARENTS} | {
        "implementation/p09/source-archive/p09-101-initial-failure/" + NEW_SOURCES[0],
        "implementation/p09/source-archive/p09-101-initial-failure/" + NEW_SOURCES[3],
    },
    "predecessor_receipts_added": set(PREDECESSORS), "current_executables": set(EXECUTABLES),
}

class PreviousReadView:
    def __init__(self, root):
        self.root = root
    def __truediv__(self, path):
        return self.root / (ARCHIVE + path if path in PARENTS else path)

def original_sources():
    sources = P100.original_sources()
    sources.update({p["path"]: p for p in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 865:
        raise ValueError("prior_source_coverage_drift")
    return sources

def expected_parent(path, before):
    for old, new in TRANSFORMS[path]:
        old, new = old.encode(), new.encode()
        if before.count(old) != 1:
            raise ValueError("parent_transform_preimage_shape_drift")
        before = before.replace(old, new, 1)
    return before

def parent_inverses(sources):
    for path in PARENTS:
        if not BASE.exact(sources[path], ARCHIVE + path):
            raise ValueError("parent_whole_preimage_drift")
        if expected_parent(path, (ROOT / (ARCHIVE + path)).read_bytes()) != (ROOT / path).read_bytes():
            raise ValueError("undeclared_parent_change")

def previous_audit():
    old_root, old_base_root = P100.ROOT, BASE.ROOT
    try:
        P100.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        return P100.current()
    finally:
        P100.ROOT, BASE.ROOT = old_root, old_base_root

def inherited():
    pin = BASE.pin(PREVIOUS)
    if pin["bytes"] != 12471 or pin["sha256"] != "abb5c1c3bf4f613b9d4f86f270e400677f3e4410da7af3eada640885488eb050":
        raise ValueError("previous_checkpoint_drift")
    if BASE.pin(PREDECESSORS[1])["sha256"] != "7564ad7ab7f014698e5ad55407b4453832d62736e1a29bb11da72a1359e4f6dc":
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    parent_inverses(sources)
    prior = previous_audit()
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if prior["checkpoint"] != pin or raw != 1398:
        raise ValueError("prior_raw_coverage_drift")
    unchanged, preimages = 0, []
    for record in sources.values():
        if BASE.exact(record):
            unchanged += 1
        elif record["path"] in PARENTS and BASE.exact(record, ARCHIVE + record["path"]):
            preimages.append({**record, "archive_path": ARCHIVE + record["path"]})
        else:
            raise ValueError("prior_source_drift")
    if unchanged != 863 or len(preimages) != 2:
        raise ValueError("prior_parent_coverage_drift")
    return {"state": "pass_original_raw_prior_view_and_exact_declared_diagnostic_changes_NOT_DB_native_cause_or_Gate",
            "previous_checkpoint": pin, "inherited_raw_pin_entries": raw, "previous_current_source_files": 865,
            "unchanged_previous_source_files": unchanged, "whole_parent_preimages": preimages,
            "parent_inverse_exact": True, "previous_unchanged_audit_passed_on_exact_parent_preimages": True,
            "old_executables_preserved_not_reexecuted": 133, "all_historical_qualification_reexecuted": False}

def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 877:
        raise ValueError("checkpoint_or_source_coverage_drift")
    counts = {}
    for key, expected in REQUIRED_GROUPS.items():
        records = data[key]
        if len(records) != len(expected) or {r["path"] for r in records} != expected:
            raise ValueError("current_group_coverage_drift")
        if not all(BASE.exact(r) for r in records):
            raise ValueError("current_raw_pin_drift")
        counts[key] = len(records)
    for key in ("native_executed", "actual_SQL_executed", "SQL_failure_root_cause_proven",
                "original_atomic_oracle_verified", "full_comment_product_acceptance",
                "native_author_time_state_binding", "product_complete", "P10_new_implementation",
                "execution_publication_authority", "new_table_insertion_implemented"):
        if data["qualification"][key] is not False:
            raise ValueError("unsupported_acceptance_promotion")
    if data["qualification"]["P09_gate"] != "OPEN" or (ROOT / "PLANS.md").exists():
        raise ValueError("gate_or_deleted_plan_changed")
    return counts

def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state": "pass_scoped_inheritance_and_delta_NOT_DB_native_cause_or_Gate", "checkpoint": BASE.pin(CURRENT),
            "inherited_raw_pin_entries": prior["inherited_raw_pin_entries"],
            "current_groups": verify_current_manifest(data, prior), "P09_gate": "OPEN", "product_complete": False}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(current() if args.current else inherited(), separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "fail", "error_type": type(error).__name__, "scope": "bytes_NOT_DB_native_cause_or_Gate"}))
        raise SystemExit(1) from error
