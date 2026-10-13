"""All immutable original signed formula SOURCE component and preservation; not production trust/SQL/native/Gate."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p119_bytes", Path(__file__).with_name("verify_formula_policy_issuer_progress.py"))
P119 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P119)
BASE, ROOT = P119.BASE, P119.ROOT
PREVIOUS = P119.CURRENT
CURRENT = "implementation/p09/evidence/p09-120-signed-original-corpus.source-progress.v1.json"
PARENTS = ["crates/product-cli/tests/form_stored_provider/actual_import/formula_policy_issuer.rs"]
ARCHIVE = "implementation/p09/source-archive/p09-120-pre-signed-original-corpus/"
NEW_SOURCES = [
    "crates/product-cli/tests/form_stored_provider/actual_import/formula_policy_issuer/corpus.rs",
    "crates/product-cli/tests/form_stored_provider/actual_import/formula_policy_issuer/corpus/verification.rs",
    "tools/p09/verify_signed_formula_corpus_progress.py",
    "tools/p09/tests/test_signed_formula_corpus_progress.py",
    "implementation/p09/P09-120_SIGNED_ORIGINAL_FORMULA_CORPUS_REPORT.md",
    "protocol/migrations/p09-signed-formula-original-corpus-v1.md",
    "implementation/p09/evidence/p09-120-signed-original-corpus.source-regression.v1.json",
    "implementation/p09/evidence/p09-120-signed-original-corpus.original-corpus.v1.json",
    "tools/p09/resource_bounded_test_support.ps1",
    "tools/p09/run_resource_bounded_tests.ps1",
    "tools/p09/build_resource_optimized_tests.ps1",
    "tools/p09/tests/test_resource_bounded_test_support.ps1",
    "implementation/p09/P09-120_RESOURCE_BOUNDED_VALIDATION_REPORT.md",
    "implementation/p09/evidence/p09-120-resource-optimization.v1.json",
]
ARCHIVES = [ARCHIVE + PARENTS[0]] + [
    "implementation/p09/source-archive/p09-120-initial-corpus-lint/" + p for p in PARENTS + NEW_SOURCES[:2]] + [
    "implementation/p09/source-archive/p09-120-pre-corpus-privacy/" + p for p in NEW_SOURCES[:2]]
ARCHIVES += ["implementation/p09/source-archive/p09-120-pre-resource-finalization/" + p for p in [
    NEW_SOURCES[2], NEW_SOURCES[3], NEW_SOURCES[4], NEW_SOURCES[6]]]
PREDECESSORS = [PREVIOUS, "implementation/p09/evidence/p09-119-formula-policy-issuer.final-audit.v1.json"]
EXE_ROOT = "target/p09-120-signed-original-corpus/debug/"
EXECUTABLES = [EXE_ROOT + p for p in ["deps/form_stored_provider-9df9b9ece65a1dfd.exe",
               "deps/hwpx_agent_cli.exe", "hwpx-agent-cli.exe",
               "deps/form_stored_provider-9df9b9ece65a1dfd-initial-corpus-lint.exe"]]
OPTIMIZED_ROOT = "target/p09-120-resource-optimized/"
OPTIMIZED_EXE = OPTIMIZED_ROOT + "debug/deps/form_stored_provider-658c5ea10a96d565.exe"
EXECUTABLES += [OPTIMIZED_EXE, OPTIMIZED_ROOT + "debug/deps/hwpx_agent_cli.exe", OPTIMIZED_ROOT + "debug/hwpx-agent-cli.exe"]
RESOURCE_RUNS = [
    "target/p09-120-signed-original-corpus/resource-bounded-smoke-20261005-b.json",
    OPTIMIZED_ROOT + "build-resource-20261005-a.json",
    OPTIMIZED_ROOT + "smoke-resource-20261005-a.json",
    OPTIMIZED_ROOT + "full225-resource-20261005-a.json",
]
EDIT = b'#[path = "formula_policy_issuer/corpus.rs"]\nmod corpus;\n'
FALSE_QUALIFICATIONS = list(P119.FALSE_QUALIFICATIONS)

class PreviousReadView:
    def __init__(self, root): self.root = root
    def __truediv__(self, path):
        return self.root / (ARCHIVE + str(path) if str(path) in PARENTS else path)

def original_sources():
    sources = P119.original_sources()
    sources.update({r["path"]: r for r in json.loads((ROOT / PREVIOUS).read_bytes())["source_delta"]})
    if len(sources) != 1081: raise ValueError("prior_source_coverage_drift")
    return sources

def restored_parent(path, data):
    if path not in PARENTS or data.count(EDIT) != 1:
        raise ValueError("declared_corpus_parent_edit_shape_drift")
    return data.replace(EDIT, b"", 1)

def inherited():
    checkpoint, final = [BASE.pin(p) for p in PREDECESSORS]
    if (checkpoint["bytes"], checkpoint["sha256"]) != (11299, "e0bde72679b19b1bdba86c60b22adf4524bee454aaadec85fd04e2325d5f6537"):
        raise ValueError("previous_checkpoint_drift")
    if (final["bytes"], final["sha256"]) != (10122, "6fb89492c9d916f5f080b695db32bbc5722829fd6ab3a8ce126c3f6bde85c8a9"):
        raise ValueError("previous_final_audit_drift")
    sources = original_sources()
    for path in PARENTS:
        if not BASE.exact(sources[path], ARCHIVE + path): raise ValueError("whole_parent_preimage_drift")
        if restored_parent(path, (ROOT / path).read_bytes()) != (ROOT / (ARCHIVE + path)).read_bytes():
            raise ValueError("undeclared_parent_mutation")
    old_root, old_base = P119.ROOT, BASE.ROOT
    try:
        P119.ROOT = BASE.ROOT = PreviousReadView(ROOT)
        prior = P119.current()
    finally:
        P119.ROOT, BASE.ROOT = old_root, old_base
    raw = prior["inherited_raw_pin_entries"] + sum(prior["current_groups"].values())
    if raw != 2271 or prior["checkpoint"] != checkpoint: raise ValueError("inherited_raw_coverage_drift")
    unchanged = sum(BASE.exact(r) for p, r in sources.items() if p not in PARENTS)
    if unchanged != 1080: raise ValueError("unrelated_original_source_drift")
    return {"state":"pass_whole_previous_source_and_evidence_NOT_production_trust_SQL_native_or_Gate",
            "previous_checkpoint":checkpoint,"inherited_raw_pin_entries":raw,"previous_source_files":1081,
            "unchanged_previous_source_files":unchanged,"whole_parent_preimages":1,"whole_parent_inverse_exact":True,
            "previous_unmodified_audit_on_preimages_passed":True,"old_executables_preserved":497,
            "all_old_executables_reexecuted":False}

def verify_corpus(data):
    if data["state"] != "PASS_original_signed_source_component_NOT_production_trust_SQL_native_or_Gate":
        raise ValueError("corpus_not_terminal_pass")
    result = data["result"]
    counts = result["counts"]
    if len(counts) != 6 or any(type(n) is not int for n in counts) or counts[:4] != [16,20,16,128] or sum(counts[4:]) != 16:
        raise ValueError("corpus_count_drift")
    original_manifest = "implementation/p09/evidence/p09-77-document-import-active-security.source-progress.v1.json"
    pin = BASE.pin(original_manifest)
    if (pin["bytes"],pin["sha256"]) != (112797,"36b30c931b760bddedb4950c46c8bf7ed84a046dc8998f7f4a51530cfe9f693d"):
        raise ValueError("original_input_manifest_drift")
    inputs = json.loads((ROOT / original_manifest).read_bytes())["actual_inputs"]
    rows = result["originals"]
    if len(rows) != 36: raise ValueError("corpus_original_coverage_drift")
    observed = {"changed":0,"unchanged":0,"no_formula_denied_no_policy_proof_or_result":0}
    for index, (row, original) in enumerate(zip(rows,inputs,strict=True)):
        if type(row["index"]) is not int or row["index"] != index or row["source_sha256"] != original["sha256"] or not BASE.exact(original):
            raise ValueError("corpus_original_binding_drift")
        outcome = row["outcome"]
        if outcome not in observed: raise ValueError("corpus_unknown_outcome")
        observed[outcome] += 1
        if outcome != "no_formula_denied_no_policy_proof_or_result":
            digest = row["candidate_sha256"]
            if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError("corpus_candidate_identity_drift")
            if type(row["formula_targets"]) is not int or type(row["source_cell_bindings"]) is not int or row["formula_targets"] != 1 or row["source_cell_bindings"] != 8:
                raise ValueError("corpus_target_coverage_drift")
            if row["whole_candidate_and_outside_leaves_exact"] is not True or row["live_revocation_denied_callback"] is not True:
                raise ValueError("corpus_preservation_or_revocation_unverified")
            if (digest == row["source_sha256"]) != (outcome == "unchanged"):
                raise ValueError("corpus_noop_identity_drift")
    if observed != {"changed":counts[4],"unchanged":counts[5],"no_formula_denied_no_policy_proof_or_result":20}:
        raise ValueError("corpus_outcome_count_drift")
    if type(data["derived_current_cases"]) is not int or type(data["protected_derivative_cases"]) is not int or data["derived_current_cases"] != 16 or data["protected_derivative_cases"] != 32:
        raise ValueError("corpus_derivative_coverage_drift")
    for key in ["production_trust_verified","actual_SQL_run","native_recalculation_verified","product_complete"]:
        if data[key] is not False: raise ValueError("corpus_unsupported_qualification")

def verify_regression(regression, manifest):
    if regression["state"] != "PASS_scoped_stored225_signed_original_component_NOT_production_trust_SQL_native_or_Gate":
        raise ValueError("regression_not_terminal_pass")
    expected = original_sources()
    expected.update({r["path"]:r for r in manifest["source_delta"]})
    previous = json.loads((ROOT / P119.NEW_SOURCES[-1]).read_bytes())
    code_paths = {r["path"] for r in previous["source_freeze"]} | set(NEW_SOURCES[:2])
    freeze = regression["source_freeze"]
    if len(freeze) != 11 or {r["path"] for r in freeze} != code_paths:
        raise ValueError("tested_source_coverage_drift")
    if any(r != expected[r["path"]] or not BASE.exact(r) for r in freeze):
        raise ValueError("tested_source_pin_drift")
    run = regression["runtime"]
    if any(type(run[k]) is not int for k in ["exit_code","passed","failed","ignored","filtered","new_corpus_tests_included"]):
        raise ValueError("regression_noninteger_counter")
    if (run["exit_code"],run["passed"],run["failed"],run["ignored"],run["filtered"],run["new_corpus_tests_included"]) != (0,225,0,0,0,3):
        raise ValueError("regression_counter_drift")
    if not run["terminal"] or run["other_P119_suites_rerun"] is not False or run["full_workspace_run"] is not False:
        raise ValueError("regression_scope_drift")
    exe = regression["test_executable"]
    if exe["path"] != OPTIMIZED_EXE or not BASE.exact(exe) or exe not in manifest["current_executables"]:
        raise ValueError("tested_executable_pin_drift")

def verify_resources(manifest, runs=None, optimization=None):
    old, build, smoke, full = runs if runs is not None else [json.loads((ROOT / p).read_bytes()) for p in RESOURCE_RUNS]
    if old["state"] != "NOT_ACCEPTED_STOP_OR_FAILURE" or old["stop_reason"] != "STOP_DURATION_LIMIT" or old["tests"]["terminal_summary"] is not None:
        raise ValueError("interrupted_smoke_promoted")
    if build["state"] != "PASS_BUILD_NOT_TEST_EXECUTION" or build["exit_code"] != 0 or build["opt_level"] != 1 or build["cargo_jobs"] != 1:
        raise ValueError("optimized_build_unqualified")
    if any(type(build[k]) is not int for k in ["exit_code","opt_level","cargo_jobs","logical_cpu_limit","descendant_limit_observations"]):
        raise ValueError("optimized_build_noninteger_policy")
    for key in ["optimized_test_profile","debug_assertions","overflow_checks","source_freeze_exact_after"]:
        if build[key] is not True: raise ValueError("optimized_build_guard_removed")
    if build["logical_cpu_limit"] != 2 or build["priority"] != "BelowNormal" or build["descendant_limit_observations"] < 1:
        raise ValueError("build_resource_limits_unverified")
    regression = json.loads((ROOT / NEW_SOURCES[6]).read_bytes())
    if build["source_freeze"] != regression["source_freeze"]:
        raise ValueError("optimized_build_source_drift")
    for data, counters in [(smoke,(1,0,0,224)),(full,(225,0,0,0))]:
        if data["state"] != "PASS_RESOURCE_BOUNDED_SCOPED_TESTS_NOT_Gate" or data["exit_code"] != 0 or data["stop_reason"] is not None:
            raise ValueError("resource_run_not_terminal_pass")
        plan, tests = data["plan"], data["tests"]
        if type(data["exit_code"]) is not int or any(type(plan[k]) is not int for k in ["logical_cpu_limit","affinity_mask","sample_seconds","cpu_stop_percent","cpu_stop_consecutive_samples","minimum_available_ram_mib","maximum_test_working_set_mib"]):
            raise ValueError("resource_noninteger_policy")
        expected_arguments = ["--nocapture","--test-threads=1"]
        if counters[0] == 1:
            expected_arguments.insert(0,"actual_import::formula_policy_issuer::genuine_ed25519_generated_policy_gates_original_changed_and_current_products_and_authorized_reader")
        if plan["test_arguments"] != expected_arguments or plan["logical_cpu_limit"] != 2 or plan["priority"] != "BelowNormal" or plan["affinity_mask"] != 3:
            raise ValueError("test_resource_policy_drift")
        if (plan["sample_seconds"],plan["cpu_stop_percent"],plan["cpu_stop_consecutive_samples"],plan["minimum_available_ram_mib"],plan["maximum_test_working_set_mib"]) != (5,85,3,4096,2048):
            raise ValueError("resource_stop_guards_weakened")
        result = tests["terminal_summary"]
        if result["outcome"] != "ok" or any(type(result[k]) is not int for k in ["passed","failed","ignored","filtered"]):
            raise ValueError("resource_test_summary_unqualified")
        if tuple(result[k] for k in ["passed","failed","ignored","filtered"]) != counters or len(tests["passed_test_names"]) != counters[0] or tests["failed_test_names"]:
            raise ValueError("resource_test_coverage_drift")
        if data["source_freeze_exact_after"] is not True or data["source_freeze"] != regression["source_freeze"] or data["executable_pin"] != regression["test_executable"] or not BASE.exact(data["executable_pin"]):
            raise ValueError("resource_test_source_or_binary_drift")
        for key in ["full_workspace_run","native_or_SQL_run","product_complete"]:
            if data[key] is not False: raise ValueError("resource_unsupported_qualification")
        if data["P09_gate"] != "OPEN" or len(data["samples"]) < 1:
            raise ValueError("resource_gate_or_observation_drift")
        if any(sample["available_ram_mib"] < 4096 or sample["test_working_set_mib"] > 2048 for sample in data["samples"]):
            raise ValueError("resource_observed_memory_limit_violation")
    corpus = json.loads((ROOT / NEW_SOURCES[7]).read_bytes())
    if full["tests"]["corpus_result"] != corpus["result"] or full["tests"]["current_derivatives_pass"] is not True or full["tests"]["protection_derivatives_pass"] is not True:
        raise ValueError("resource_original_corpus_receipt_drift")
    optimization = optimization if optimization is not None else json.loads((ROOT / NEW_SOURCES[-1]).read_bytes())
    if optimization["state"] != "PASS_RESOURCE_BOUNDED_STORED225_NOT_full_performance_or_Gate" or optimization["full225_pass"] is not True or optimization["product_complete"] is not False:
        raise ValueError("resource_optimization_not_final")
    tools = optimization["tool_sources"]
    if len(tools) != 4 or {r["path"] for r in tools} != set(NEW_SOURCES[8:12]) or any(not BASE.exact(r) for r in tools):
        raise ValueError("resource_tool_pin_drift")

def verify_current_manifest(data, prior):
    if data["inherited_checkpoint"] != prior["previous_checkpoint"] or data["current_source_files_count"] != 1095:
        raise ValueError("current_source_coverage_drift")
    required = {"source_delta":set(PARENTS + NEW_SOURCES),"source_archives_added":set(ARCHIVES),
                "predecessor_receipts_added":set(PREDECESSORS),"current_executables":set(EXECUTABLES),"resource_runs":set(RESOURCE_RUNS)}
    counts = {}
    for key, paths in required.items():
        rows = data[key]
        if len(rows) != len(paths) or {r["path"] for r in rows} != paths:
            raise ValueError("current_group_coverage_drift")
        if not all(BASE.exact(r) for r in rows): raise ValueError("current_raw_pin_drift")
        counts[key] = len(rows)
    if any(data["qualification"][k] is not False for k in FALSE_QUALIFICATIONS):
        raise ValueError("unsupported_qualification_promotion")
    if data["qualification"]["all36_original_signed_source_component_verified"] is not True:
        raise ValueError("missing_original_corpus_component")
    if data["P09_gate"] != "OPEN" or data["P10_new_implementation"] is not False or data["product_complete"] is not False:
        raise ValueError("gate_or_product_promotion")
    if (data["remaining_coarse_groups_minimum"],data["remaining_coarse_groups_closed_by_slice"]) != (6,0):
        raise ValueError("unsupported_remaining_reduction")
    if data["conversation_minimum_30_conditions_not_exhaustive_or_decremented"] is not True:
        raise ValueError("unsupported_granular_remaining_reduction")
    verify_corpus(json.loads((ROOT / NEW_SOURCES[7]).read_bytes()))
    verify_regression(json.loads((ROOT / NEW_SOURCES[6]).read_bytes()),data)
    verify_resources(data)
    return counts

def current():
    prior = inherited()
    data = json.loads((ROOT / CURRENT).read_bytes())
    return {"state":"pass_all_original_signed_source_component_and_preservation_NOT_production_trust_SQL_native_or_Gate",
            "checkpoint":BASE.pin(CURRENT),"inherited_raw_pin_entries":prior["inherited_raw_pin_entries"],
            "current_groups":verify_current_manifest(data,prior),"P09_gate":"OPEN","product_complete":False}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current",action="store_true")
    args = parser.parse_args()
    try: print(json.dumps(current() if args.current else inherited(),separators=(",",":")))
    except (OSError,ValueError,KeyError,TypeError) as error:
        print(json.dumps({"state":"fail","error_type":type(error).__name__,"scope":"bytes_NOT_production_trust_SQL_native_or_Gate"}))
        raise SystemExit(1) from None
