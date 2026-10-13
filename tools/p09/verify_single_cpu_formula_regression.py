"""P123 same frozen Rust source, full stored228 with stricter one-CPU resource policy."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC=importlib.util.spec_from_file_location("p122_preserved",Path(__file__).with_name("verify_resource_crosscheck_progress.py"))
P122=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P122)
P121,BASE,ROOT=P122.P121,P122.BASE,P122.ROOT
PREVIOUS=P122.CURRENT
PREVIOUS_FINAL="implementation/p09/evidence/p09-122-resource-crosscheck.final-audit.v1.json"
CURRENT="implementation/p09/evidence/p09-123-single-cpu-formula-regression.source-progress.v1.json"
RUN=P121.RUN_ROOT+"p121-full-resources-20261005-f.json"
DOCUMENT_RUN=P121.RUN_ROOT+"p123-full-document-resources-20261005-a.json"
ROOT_NAMES=["stored_actual_capture_uses_real_sealed_node_acl_aead_and_original_compiler_without_publish",
            "stored_all_five_kinds_required_radio_defaults_empty_clear_match_whole_predecessor",
            "stored_fresh_acl_revocation_blocks_preparation_verification_and_route",
            "stored_fresh_map_policy_access_and_malformed_input_fail_without_ingest_or_commit",
            "stored_provider_tenant_subject_scope_branch_document_cannot_be_substituted",
            "stored_quarantine_unverified_wrong_artifact_kind_and_corrupt_ciphertext_never_prepare",
            "stored_real_head_advance_rejects_old_preparation_even_when_actual_artifact_is_unchanged",
            "stored_receipts_debug_and_fixed_errors_do_not_expose_source_subject_artifact_or_paths"]
ROOT_RUNS=[P121.RUN_ROOT+f"p123-root-{index:02d}-resources-20261005-a.json" for index in range(1,9)]
DELTA=["tools/p09/verify_single_cpu_formula_regression.py","tools/p09/tests/test_single_cpu_formula_regression.py",
       "implementation/p09/P09-123_SINGLE_CPU_FORMULA_REGRESSION_REPORT.md",
       "implementation/p09/evidence/p09-123-single-cpu-formula-regression.runtime-summary.v1.json"]

def require(condition,code):
    if not condition: raise ValueError(code)

def validate_policy(doc,cpu_limit):
    plan=doc["plan"]
    require(type(cpu_limit) is int and cpu_limit in (1,2),"unsupported_cpu_limit")
    require(type(plan["logical_cpu_limit"]) is int and plan["logical_cpu_limit"]==cpu_limit
            and type(plan["affinity_mask"]) is int and plan["affinity_mask"]>0
            and plan["affinity_mask"].bit_count()==cpu_limit,"resource_affinity_drift")
    require(plan["test_arguments"].count("--test-threads=1")==1 and plan["priority"]=="BelowNormal"
            and plan["cpu_stop_percent"]==85 and plan["cpu_stop_consecutive_samples"]==3
            and plan["minimum_available_ram_mib"]==4096 and plan["maximum_test_working_set_mib"]==2048,
            "resource_thresholds_drift")
    require(doc["samples"] and 0<doc["elapsed_seconds"]<=plan["maximum_seconds"],"runtime_samples_or_duration_drift")
    hot=0
    for sample in doc["samples"]:
        hot=hot+1 if sample["system_cpu_percent"]>=85 else 0
        require(hot<3 and sample["available_ram_mib"]>=4096 and sample["test_working_set_mib"]<=2048,
                "resource_guard_violated")

def validate_scoped(doc,passed,filtered,freeze,executable,cpu_limit):
    require(doc["state"]=="PASS_RESOURCE_BOUNDED_SCOPED_TESTS_NOT_Gate" and doc["exit_code"]==0
            and doc["stop_reason"] is None and doc["source_freeze_exact_after"] is True,"runtime_not_accepted")
    require(doc["source_freeze"]==freeze and doc["executable_pin"]==executable
            and doc["plan"]["executable"]==executable["path"],"runtime_source_or_executable_drift")
    summary=doc["tests"]["terminal_summary"]
    require(summary["outcome"]=="ok" and type(summary["passed"]) is int and summary["passed"]==passed
            and summary["failed"]==0 and summary["ignored"]==0 and summary["measured"]==0
            and summary["filtered"]==filtered,"runtime_test_count_drift")
    require(doc["full_workspace_run"] is False and doc["native_or_SQL_run"] is False
            and doc["product_complete"] is False and doc["P09_gate"]=="OPEN","runtime_scope_promoted")
    validate_policy(doc,cpu_limit)
    tests=doc["tests"]
    require(len(tests["passed_test_names"])==passed and len(set(tests["passed_test_names"]))==passed
            and not tests["failed_test_names"],"distinct_scoped_tests_drift")
    return tests

def validate_component(doc,passed,filtered,freeze,executable,cpu_limit):
    tests=validate_scoped(doc,passed,filtered,freeze,executable,cpu_limit)
    require(tests["changed_protection_pass"] is True and tests["outside_leaf_counterexamples_pass"] is True,
            "changed_guards_missing")
    expected=json.loads((ROOT/P121.RUNS[6]).read_bytes())["tests"]["changed_corpus_result"]
    # P121's unchanged validator already validates every original digest/count/closed flag on that real run.
    require(tests["changed_corpus_result"]==expected,"changed_original_results_drift")
    return expected

def partial():
    old=inherited()
    doc=json.loads((ROOT/CURRENT).read_bytes())
    require(doc["state"]=="PASS_DOCUMENT20_ROOT8_SINGLE_CPU_FULL228_RESOURCE_BLOCKED_NOT_PRODUCT_OR_GATE"
            and doc["full228_accepted"] is False and doc["P09_gate"]=="OPEN"
            and doc["product_complete"] is False and doc["P10_new_implementation"] is False
            and doc["goal_status"]=="active","partial_scope_promoted")
    groups={"source_delta":DELTA,"predecessor_receipts_added":[PREVIOUS,PREVIOUS_FINAL],"runtime_runs":[RUN,DOCUMENT_RUN,*ROOT_RUNS]}
    for group,paths in groups.items():
        rows=doc[group]
        require(len(rows)==len(paths) and {r["path"] for r in rows}==set(paths)
                and all(BASE.exact(r) for r in rows),"partial_pin_coverage_drift")
    require(old["current_source_files"]==1117 and doc["current_source_files_count"]==1121
            and doc["inherited_raw_pin_entries"]==2360,"partial_coverage_drift")
    sources=P121.original_sources()
    for checkpoint in (P122.PARTIAL,P122.CURRENT,CURRENT):
        sources.update({r["path"]:r for r in json.loads((ROOT/checkpoint).read_bytes())["source_delta"]})
    require(len(sources)==1121 and all(BASE.exact(r) for r in sources.values()),"whole_partial_source_inventory_drift")
    freeze=json.loads((ROOT/P121.FREEZE).read_bytes())["source_freeze"]
    stopped=json.loads((ROOT/RUN).read_bytes())
    require(stopped["state"]=="NOT_ACCEPTED_STOP_OR_FAILURE" and stopped["stop_reason"]=="STOP_SUSTAINED_SYSTEM_CPU"
            and stopped["source_freeze"]==freeze and stopped["source_freeze_exact_after"] is True
            and stopped["executable_pin"]==BASE.pin(P121.EXE) and stopped["exit_code"]==-1
            and stopped["plan"]["logical_cpu_limit"]==1 and stopped["plan"]["affinity_mask"]==1
            and stopped["tests"]["terminal_summary"] is None
            and all(s["system_cpu_percent"]>=85 for s in stopped["samples"][-3:]),"stopped_full_runtime_drift")
    runtime=json.loads((ROOT/DOCUMENT_RUN).read_bytes())
    tests=validate_scoped(runtime,20,208,freeze,BASE.pin(P121.EXE),1)
    require(runtime["plan"]["test_arguments"]==["full_document::","--nocapture","--test-threads=1"]
            and all(name.startswith("full_document::") for name in tests["passed_test_names"]),"full_document_scope_drift")
    for path,name in zip(ROOT_RUNS,ROOT_NAMES):
        root=json.loads((ROOT/path).read_bytes())
        tested=validate_scoped(root,1,227,freeze,BASE.pin(P121.EXE),1)
        require(tested["passed_test_names"]==[name] and root["plan"]["test_arguments"]==[name,"--nocapture","--test-threads=1"],"root_scope_drift")
    summary=json.loads((ROOT/DELTA[-1]).read_bytes())
    require(summary["full228_accepted"] is False and summary["full_document_tests_passed"]==20
            and summary["independently_accepted_root_tests"]==8
            and summary["accepted_document_runtime"]==BASE.pin(DOCUMENT_RUN),"partial_summary_drift")
    return {"state":doc["state"],"full228_accepted":False,"full_document_tests_passed":20,
            "full_document_filtered":208,"root_tests_passed":8,"interrupted_full_ok_markers":201,"cpu_limit":1,
            "source_freeze":14,"current_source_files":1121,"inherited_raw_pin_entries":2360,
            "current_groups":{g:len(doc[g]) for g in groups},"goal_status":"active","P09_gate":"OPEN","product_complete":False}

def inherited():
    require(BASE.pin(PREVIOUS)=={"path":PREVIOUS,"bytes":5749,"sha256":"dde748e23b6cbdf1f6a8e49f6c6c34189fdd129eff2800fe36565fe7fd9cefb6"},"P122_checkpoint_drift")
    require(BASE.pin(PREVIOUS_FINAL)=={"path":PREVIOUS_FINAL,"bytes":2517,"sha256":"3af242bc74ea132fae96dda78d58280e15f315a0772f5d6452b7181d7f3274c3"},"P122_final_audit_drift")
    return P122.current()

def current():
    old=inherited()
    doc=json.loads((ROOT/CURRENT).read_bytes())
    require(doc["state"]=="PASS_SAME_SOURCE_STORED228_SINGLE_CPU_NOT_PRODUCT_OR_GATE"
            and doc["P09_gate"]=="OPEN" and doc["product_complete"] is False
            and doc["P10_new_implementation"] is False and doc["goal_status"]=="active","checkpoint_scope_promoted")
    groups={"source_delta":DELTA,"predecessor_receipts_added":[PREVIOUS,PREVIOUS_FINAL],"runtime_runs":[RUN]}
    for group,paths in groups.items():
        rows=doc[group]
        require(len(rows)==len(paths) and {r["path"] for r in rows}==set(paths)
                and all(BASE.exact(r) for r in rows),"checkpoint_pin_coverage_drift")
    require(old["current_source_files"]==1117 and doc["previous_source_files_count"]==1117
            and doc["current_source_files_count"]==1121 and doc["inherited_raw_pin_entries"]==2360,"source_or_evidence_coverage_drift")
    freeze=json.loads((ROOT/P121.FREEZE).read_bytes())["source_freeze"]
    require(len(freeze)==14 and all(BASE.exact(r) for r in freeze),"source_freeze_drift")
    runtime=json.loads((ROOT/RUN).read_bytes())
    changed=validate_component(runtime,228,0,freeze,BASE.pin(P121.EXE),1)
    require(runtime["plan"]["test_arguments"]==["--nocapture","--test-threads=1"],"full_runtime_filter_present")
    require(len(runtime["tests"]["passed_test_names"])==228 and len(set(runtime["tests"]["passed_test_names"]))==228
            and not runtime["tests"]["failed_test_names"],"full_distinct_test_coverage_drift")
    originals=runtime["tests"]["corpus_result"]
    require(originals["counts"]==[16,20,16,128,0,16] and len(originals["originals"])==36
            and runtime["tests"]["current_derivatives_pass"] is True
            and runtime["tests"]["protection_derivatives_pass"] is True,"full_original_guards_missing")
    prior_originals=json.loads((ROOT/"implementation/p09/evidence/p09-120-signed-original-corpus.original-corpus.v1.json").read_bytes())["result"]
    require(originals==prior_originals,"original_corpus_identity_drift")
    summary=json.loads((ROOT/DELTA[-1]).read_bytes())
    require(summary["accepted_runtime"]==BASE.pin(RUN) and summary["stored_tests_passed"]==228
            and summary["formula_changed_derivatives"]==changed["cases"] and summary["full_workspace_run"] is False
            and summary["P09_gate"]=="OPEN" and summary["product_complete"] is False,"runtime_summary_drift")
    return {"state":doc["state"],"stored_tests_passed":228,"cpu_limit":1,"source_freeze":14,
            "changed_derivatives":16,"current_derivatives":16,"protected_denials":32,"outside_leaf_counterexamples":16,
            "previous_source_files":1117,"current_source_files":1121,"inherited_raw_pin_entries":2360,
            "current_groups":{g:len(doc[g]) for g in groups},"goal_status":"active","P09_gate":"OPEN","product_complete":False}

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current",action="store_true")
    parser.add_argument("--partial",action="store_true")
    args=parser.parse_args()
    try: print(json.dumps(current() if args.current else partial() if args.partial else inherited(),separators=(",",":")))
    except (OSError,ValueError,KeyError,TypeError) as error:
        print(json.dumps({"state":"fail","error_type":type(error).__name__,"scope":"SOURCE_NOT_PRODUCT_OR_GATE"}))
        raise SystemExit(1) from None
