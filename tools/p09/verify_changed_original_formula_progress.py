"""P121 inherited whole accepted P120 source/evidence; no native/trust/SQL/Gate promotion."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p120_preserved",Path(__file__).with_name("verify_signed_formula_corpus_progress.py"))
P120 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P120)
BASE, ROOT = P120.BASE, P120.ROOT
PREVIOUS = P120.CURRENT
PARENT = "crates/product-cli/tests/form_stored_provider/actual_import/formula_policy_issuer/corpus.rs"
ARCHIVE = "implementation/p09/source-archive/p09-121-pre-signed-changed-originals/" + PARENT
EDIT = b'#[path = "corpus/changed.rs"]\nmod changed;\n'
CURRENT = "implementation/p09/evidence/p09-121-signed-changed-original.source-progress.v1.json"
FREEZE = "implementation/p09/evidence/p09-121-signed-changed-original.source-regression.v1.json"
PREFIX="crates/product-cli/tests/form_stored_provider/actual_import/formula_policy_issuer/corpus/"
NEW_RUST=[PREFIX+"changed.rs",PREFIX+"changed/consumer.rs",PREFIX+"changed/mutation.rs"]
FAILED_ARCHIVE="implementation/p09/source-archive/p09-121-initial-targeted-failure/"
EXE="target/p09-121-resource-optimized/debug/deps/form_stored_provider-658c5ea10a96d565.exe"
FAILED_EXE=EXE.removesuffix(".exe")+"-initial-targeted-failure.exe"
RUN_ROOT="target/p09-121-resource-optimized/"
RUNS=[RUN_ROOT+"p121-"+name+"-resources-20261005-"+suffix+".json"
      for name,suffix in (("build","a"),("lint","a"),("targeted","a"),("diagnostic","a"),
                          ("build","b"),("lint","b"),("targeted","b"),("full","b"),("full","c"))]
DELTA=[PARENT,*NEW_RUST,"tools/p09/build_changed_formula_tests.ps1","tools/p09/run_changed_formula_tests.ps1",
       "tools/p09/changed_formula_test_support.ps1","tools/p09/tests/test_changed_formula_test_support.ps1",
       "tools/p09/verify_changed_original_formula_progress.py","tools/p09/tests/test_changed_original_formula_progress.py",
       "implementation/p09/P09-121_SIGNED_CHANGED_ORIGINAL_FORMULA_REPORT.md",
       "protocol/migrations/p09-signed-changed-original-formula-v1.md",FREEZE,
       "implementation/p09/evidence/p09-121-signed-changed-original.changed-corpus.v1.json",
       "implementation/p09/evidence/p09-121-resource-optimization.v1.json"]
ARCHIVES=[ARCHIVE,*[FAILED_ARCHIVE+p for p in NEW_RUST],FAILED_ARCHIVE+FREEZE]

def require(condition, code):
    if not condition: raise ValueError(code)

def validate_runtime(doc, passed, filtered, freeze, executable):
    require(doc["state"]=="PASS_RESOURCE_BOUNDED_SCOPED_TESTS_NOT_Gate" and doc["exit_code"]==0
            and doc["stop_reason"] is None and doc["source_freeze_exact_after"] is True,"runtime_not_accepted")
    require(doc["source_freeze"]==freeze and doc["executable_pin"]==executable,"runtime_identity_drift")
    summary=doc["tests"]["terminal_summary"]
    require(summary["outcome"]=="ok" and type(summary["passed"]) is int and summary["passed"]==passed
            and summary["failed"]==0 and summary["ignored"]==0 and summary["measured"]==0
            and summary["filtered"]==filtered,"runtime_test_count_drift")
    require(doc["full_workspace_run"] is False and doc["native_or_SQL_run"] is False
            and doc["product_complete"] is False and doc["P09_gate"]=="OPEN","runtime_scope_promoted")
    plan=doc["plan"]
    require(plan["test_arguments"].count("--test-threads=1")==1
            and plan["executable"]==executable["path"] and plan["affinity_mask"].bit_count()==2
            and plan["logical_cpu_limit"]==2 and plan["priority"]=="BelowNormal"
            and plan["cpu_stop_percent"]==85 and plan["cpu_stop_consecutive_samples"]==3
            and plan["minimum_available_ram_mib"]==4096 and plan["maximum_test_working_set_mib"]==2048,
            "resource_policy_drift")
    require(doc["samples"] and doc["elapsed_seconds"]<=plan["maximum_seconds"],"runtime_samples_or_duration")
    hot=0
    for sample in doc["samples"]:
        hot=hot+1 if sample["system_cpu_percent"]>=85 else 0
        require(hot<3 and sample["available_ram_mib"]>=4096 and sample["test_working_set_mib"]<=2048,
                "runtime_resource_guard_violation")
    tests=doc["tests"]
    require(tests["changed_protection_pass"] is True and tests["outside_leaf_counterexamples_pass"] is True,
            "changed_counterexamples_missing")
    corpus=tests["changed_corpus_result"]
    require(corpus["cases"]==16 and len(corpus["rows"])==16,"changed_corpus_count_drift")
    require(len({r["index"] for r in corpus["rows"]})==16,"changed_original_index_duplicate")
    for row in corpus["rows"]:
        require(type(row["index"]) is int and 0<=row["index"]<36,"changed_original_index_invalid")
        for key in ("original_sha256","derivative_sha256","candidate_sha256"):
            require(type(row[key]) is str and len(row[key])==64 and all(c in "0123456789abcdef" for c in row[key]),"changed_digest_invalid")
        require(len({row[k] for k in ("original_sha256","derivative_sha256","candidate_sha256")})==3,"changed_bytes_not_distinct")
        require((row["formula_targets"],row["source_cell_bindings"],row["changed_parts"])==(1,8,1)
                and all(type(row[k]) is int for k in ("formula_targets","source_cell_bindings","changed_parts")),"changed_bindings_drift")
        for key in ("only_numeric_input_leaf_changed","outside_result_leaves_exact",
                    "signed_changed_and_current_noop_verified","live_revocation_and_rebinding_denied_callback"):
            require(row[key] is True,"changed_claim_not_verified")
    return corpus

def current():
    previous=inherited()
    doc=json.loads((ROOT/CURRENT).read_bytes())
    require(doc["state"]=="PASS_SOURCE_COMPONENT_STORED228_NOT_NATIVE_TRUST_SQL_OR_GATE"
            and doc["product_complete"] is False and doc["P09_gate"]=="OPEN"
            and doc["P10_new_implementation"] is False,"checkpoint_scope_promoted")
    require(doc["inherited_checkpoint"]==previous["previous_checkpoint"] and doc["inherited_raw_pin_entries"]==2309,
            "checkpoint_predecessor_drift")
    groups=("source_delta","source_archives_added","current_executables","resource_runs")
    expected_groups={"source_delta":DELTA,"source_archives_added":ARCHIVES,"current_executables":[EXE,FAILED_EXE],"resource_runs":RUNS}
    for group in groups:
        rows=doc[group]
        require({r["path"] for r in rows}==set(expected_groups[group]),"checkpoint_pin_coverage_drift")
        require(len({r["path"] for r in rows})==len(rows),"duplicate_pin_path")
        require(all(BASE.exact(r) for r in rows),"checkpoint_pin_drift")
    sources=original_sources()
    sources.update({r["path"]:r for r in doc["source_delta"]})
    require(len(sources)==doc["current_source_files_count"] and all(BASE.exact(r) for r in sources.values()),"source_coverage_drift")
    freeze=json.loads((ROOT/FREEZE).read_bytes())["source_freeze"]
    require(len(freeze)==14 and all(BASE.exact(r) for r in freeze),"source_freeze_drift")
    initial=json.loads((ROOT/(FAILED_ARCHIVE+FREEZE)).read_bytes())["source_freeze"]
    require(len(initial)==14 and all(BASE.exact(r,FAILED_ARCHIVE+r["path"] if r["path"] in NEW_RUST else r["path"]) for r in initial),"initial_failed_source_not_preserved")
    for index,count in ((2,3),(3,1)):
        failed=json.loads((ROOT/RUNS[index]).read_bytes())
        summary=failed["tests"]["terminal_summary"]
        require(failed["state"]=="NOT_ACCEPTED_STOP_OR_FAILURE" and failed["exit_code"]==101
                and failed["source_freeze"]==initial and failed["source_freeze_exact_after"] is True
                and summary["passed"]==0 and summary["failed"]==count
                and BASE.exact(failed["executable_pin"],FAILED_EXE),"failed_execution_not_preserved")
    stopped=json.loads((ROOT/RUNS[7]).read_bytes())
    require(stopped["state"]=="NOT_ACCEPTED_STOP_OR_FAILURE" and stopped["stop_reason"]=="STOP_LOW_AVAILABLE_RAM"
            and stopped["source_freeze"]==freeze and stopped["source_freeze_exact_after"] is True
            and stopped["tests"]["terminal_summary"] is None and stopped["samples"][-1]["available_ram_mib"]<4096,
            "resource_stopped_execution_not_preserved")
    runtime=json.loads((ROOT/doc["accepted_full_runtime"]).read_bytes())
    executable=doc["accepted_executable"]
    require(executable in doc["current_executables"] and BASE.exact(executable),"accepted_executable_drift")
    changed=validate_runtime(runtime,228,0,freeze,executable)
    targeted=json.loads((ROOT/doc["accepted_targeted_runtime"]).read_bytes())
    require(validate_runtime(targeted,3,225,freeze,executable)==changed,"targeted_full_corpus_drift")
    tests=runtime["tests"]
    require(tests["corpus_result"]["counts"]==[16,20,16,128,0,16]
            and tests["current_derivatives_pass"] is True and tests["protection_derivatives_pass"] is True,
            "original_corpus_guard_missing")
    originals={r["index"]:r for r in tests["corpus_result"]["originals"] if r["outcome"]=="unchanged"}
    require(set(originals)=={r["index"] for r in changed["rows"]}
            and all(originals[r["index"]]["source_sha256"]==r["original_sha256"] for r in changed["rows"]),"changed_original_identity_drift")
    for field,state in (("accepted_build_runtime","PASS_BUILD_NOT_TEST_EXECUTION"),("accepted_lint_runtime","PASS_STRICT_LINT_NOT_TEST_EXECUTION")):
        run=json.loads((ROOT/doc[field]).read_bytes())
        require(run["state"]==state and run["exit_code"]==0 and run["stop_reason"] is None
                and run["source_freeze"]==freeze and run["source_freeze_exact_after"] is True,"build_lint_not_accepted")
    return {"state":doc["state"],"stored_tests_passed":228,"changed_derivatives":16,"current_derivatives":16,
            "protected_denials":32,"outside_leaf_counterexamples":16,"inherited_raw_pin_entries":2309,
            "current_groups":{g:len(doc[g]) for g in groups},"current_source_files":len(sources),
            "P09_gate":"OPEN","product_complete":False,"previous_checkpoint":previous["previous_checkpoint"]}

def partial():
    previous=inherited()
    checkpoint="implementation/p09/evidence/p09-121-signed-changed-original.partial-progress.v1.json"
    doc=json.loads((ROOT/checkpoint).read_bytes())
    require(doc["state"]=="PASS_TARGETED3_FULL228_RESOURCE_BLOCKED_NOT_PRODUCT_OR_GATE"
            and doc["product_complete"] is False and doc["P09_gate"]=="OPEN"
            and doc["P10_new_implementation"] is False and doc["full228_accepted"] is False,"partial_scope_promoted")
    require(doc["inherited_checkpoint"]==previous["previous_checkpoint"] and doc["inherited_raw_pin_entries"]==2309,
            "partial_predecessor_drift")
    expected_groups={"source_delta":DELTA,"source_archives_added":ARCHIVES,"current_executables":[EXE,FAILED_EXE],"resource_runs":RUNS}
    for group,paths in expected_groups.items():
        rows=doc[group]
        require(len(rows)==len(paths) and {r["path"] for r in rows}==set(paths)
                and all(BASE.exact(r) for r in rows),"partial_pin_coverage_drift")
    sources=original_sources()
    sources.update({r["path"]:r for r in doc["source_delta"]})
    require(len(sources)==1109 and doc["current_source_files_count"]==1109
            and all(BASE.exact(r) for r in sources.values()),"partial_source_coverage_drift")
    freeze=json.loads((ROOT/FREEZE).read_bytes())["source_freeze"]
    require(len(freeze)==14 and all(BASE.exact(r) for r in freeze),"partial_freeze_drift")
    initial=json.loads((ROOT/(FAILED_ARCHIVE+FREEZE)).read_bytes())["source_freeze"]
    require(len(initial)==14 and all(BASE.exact(r,FAILED_ARCHIVE+r["path"] if r["path"] in NEW_RUST else r["path"]) for r in initial),"partial_initial_source_drift")
    targeted=json.loads((ROOT/RUNS[6]).read_bytes())
    changed=validate_runtime(targeted,3,225,freeze,BASE.pin(EXE))
    original=json.loads((ROOT/"implementation/p09/evidence/p09-120-signed-original-corpus.original-corpus.v1.json").read_bytes())["result"]
    rows={r["index"]:r for r in original["originals"] if r["outcome"]=="unchanged"}
    require(set(rows)=={r["index"] for r in changed["rows"]}
            and all(rows[r["index"]]["source_sha256"]==r["original_sha256"] for r in changed["rows"]),"partial_original_identity_drift")
    receipt=json.loads((ROOT/DELTA[-2]).read_bytes())
    require(receipt["result"]==changed and receipt["full228_accepted"] is False
            and receipt["native_recalculation_verified"] is False and receipt["production_trust_verified"] is False,"partial_changed_receipt_drift")
    for index,count in ((2,3),(3,1)):
        failed=json.loads((ROOT/RUNS[index]).read_bytes())
        require(failed["state"]=="NOT_ACCEPTED_STOP_OR_FAILURE" and failed["exit_code"]==101
                and failed["source_freeze"]==initial and failed["source_freeze_exact_after"] is True
                and failed["tests"]["terminal_summary"]["passed"]==0
                and failed["tests"]["terminal_summary"]["failed"]==count
                and BASE.exact(failed["executable_pin"],FAILED_EXE),"partial_failed_evidence_drift")
    stopped=json.loads((ROOT/RUNS[7]).read_bytes())
    deferred=json.loads((ROOT/RUNS[8]).read_bytes())
    require(stopped["state"]=="NOT_ACCEPTED_STOP_OR_FAILURE" and stopped["stop_reason"]=="STOP_LOW_AVAILABLE_RAM"
            and stopped["source_freeze"]==freeze and stopped["source_freeze_exact_after"] is True
            and stopped["tests"]["terminal_summary"] is None and stopped["samples"][-1]["available_ram_mib"]<4096
            and stopped["executable_pin"]==BASE.pin(EXE),"partial_resource_stop_drift")
    require(deferred["state"]=="DEFERRED_BASELINE_RESOURCE_PRESSURE_NOT_STARTED" and deferred["test_process_started"] is False
            and deferred["samples"][0]["system_cpu_percent"]>=85,"partial_deferred_evidence_drift")
    for index,state in ((4,"PASS_BUILD_NOT_TEST_EXECUTION"),(5,"PASS_STRICT_LINT_NOT_TEST_EXECUTION")):
        run=json.loads((ROOT/RUNS[index]).read_bytes())
        require(run["state"]==state and run["exit_code"]==0 and run["source_freeze"]==freeze
                and run["source_freeze_exact_after"] is True and run["stop_reason"] is None,"partial_build_lint_drift")
    return {"state":doc["state"],"targeted_tests_passed":3,"full228_accepted":False,
            "changed_derivatives":16,"current_derivatives":16,"protected_denials":32,"outside_leaf_counterexamples":16,
            "previous_source_files":1095,"current_source_files":1109,"inherited_raw_pin_entries":2309,
            "current_groups":{g:len(doc[g]) for g in expected_groups},"old_executables_preserved":504,
            "goal_record_status":doc["goal_status"],"P09_gate":"OPEN","product_complete":False}

class PreviousReadView:
    def __init__(self, root): self.root=root
    def __truediv__(self, path): return self.root / (ARCHIVE if str(path)==PARENT else path)

def original_sources():
    result=P120.original_sources()
    result.update({r["path"]:r for r in json.loads((ROOT/PREVIOUS).read_bytes())["source_delta"]})
    if len(result)!=1095: raise ValueError("previous_source_coverage_drift")
    return result

def inherited():
    previous=BASE.pin(PREVIOUS)
    final=BASE.pin("implementation/p09/evidence/p09-120-signed-original-corpus.final-audit.v1.json")
    if (previous["bytes"],previous["sha256"])!=(11307,"e93d9137b44bc7d33f01beec5b6403be42526bc919f6d3984688f6bd13c00deb"):
        raise ValueError("previous_checkpoint_drift")
    if (final["bytes"],final["sha256"])!=(4271,"8112f6e5d1fda327ca9054424a0bdd99454c50550011b56f7e44e3db72a9549d"):
        raise ValueError("previous_final_audit_drift")
    sources=original_sources()
    if not BASE.exact(sources[PARENT],ARCHIVE): raise ValueError("whole_parent_preimage_drift")
    data=(ROOT/PARENT).read_bytes()
    if data.count(EDIT)!=1 or data.replace(EDIT,b"",1)!=(ROOT/ARCHIVE).read_bytes():
        raise ValueError("undeclared_parent_edit")
    old_root, old_base=P120.ROOT,BASE.ROOT
    try:
        P120.ROOT=BASE.ROOT=PreviousReadView(ROOT)
        result=P120.current()
    finally:
        P120.ROOT,BASE.ROOT=old_root,old_base
    raw=result["inherited_raw_pin_entries"]+sum(result["current_groups"].values())
    if raw!=2309 or result["checkpoint"]!=previous: raise ValueError("inherited_evidence_coverage_drift")
    unchanged=sum(BASE.exact(row) for path,row in sources.items() if path!=PARENT)
    if unchanged!=1094: raise ValueError("previous_unrelated_source_drift")
    return {"state":"pass_whole_P120_source_and_evidence_NOT_changed_derivative_native_trust_SQL_or_Gate",
            "previous_checkpoint":previous,"previous_source_files":1095,"unchanged_source_files":unchanged,
            "whole_parent_preimages":1,"whole_parent_inverse_exact":True,"previous_unmodified_audit_on_preimages_passed":True,
            "inherited_raw_pin_entries":raw,"old_executables_preserved":504,"all_old_executables_reexecuted":False,
            "P09_gate":"OPEN","product_complete":False}

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current",action="store_true")
    parser.add_argument("--partial",action="store_true")
    args=parser.parse_args()
    try: print(json.dumps(current() if args.current else partial() if args.partial else inherited(),separators=(",",":")))
    except (OSError,ValueError,KeyError,TypeError) as error:
        print(json.dumps({"state":"fail","error_type":type(error).__name__,"scope":"bytes_NOT_native_trust_SQL_or_Gate"}))
        raise SystemExit(1) from None
