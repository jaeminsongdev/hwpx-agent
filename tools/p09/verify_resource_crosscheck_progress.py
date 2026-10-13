"""P122 immutable P121 partial predecessor, real metric pairs and bounded full228 terminal."""
import argparse
import importlib.util
import json
import math
from pathlib import Path

SPEC=importlib.util.spec_from_file_location("p121_preserved",Path(__file__).with_name("verify_changed_original_formula_progress.py"))
P121=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P121)
BASE,ROOT=P121.BASE,P121.ROOT
PARTIAL="implementation/p09/evidence/p09-121-signed-changed-original.partial-progress.v1.json"
FINAL="implementation/p09/evidence/p09-121-signed-changed-original.partial-final-audit.v1.json"
CURRENT="implementation/p09/evidence/p09-122-resource-crosscheck.source-progress.v1.json"
SCRIPTS=["tools/p09/native_resource_crosscheck_support.ps1","tools/p09/measure_resource_crosscheck.ps1",
         "tools/p09/tests/test_native_resource_crosscheck_support.ps1"]
DELTA=[*SCRIPTS,"tools/p09/verify_resource_crosscheck_progress.py","tools/p09/tests/test_resource_crosscheck_progress.py",
       "implementation/p09/P09-122_RESOURCE_METRIC_CROSSCHECK_REPORT.md",
       "implementation/p09/evidence/p09-122-initial-measurement-failure.v1.json",
       "implementation/p09/evidence/p09-122-resource-crosscheck.measurement-summary.v1.json"]
ARCHIVES=["implementation/p09/source-archive/"+stage+"/"+path
          for stage in ("p09-122-initial-measurement-failure","p09-122-initial-successful-pair-measurement") for path in SCRIPTS]
RUNS=["target/p09-122-resource-crosscheck/resource-pairs-20261005-"+letter+".json" for letter in ("b","c")]
FULL=[P121.RUN_ROOT+"p121-full-resources-20261005-"+letter+".json" for letter in ("d","e")]

def require(condition,code):
    if not condition: raise ValueError(code)

def number(value,minimum,maximum):
    return type(value) in (int,float) and math.isfinite(value) and minimum<=value<=maximum

def validate_pairs(doc,observed_hot):
    require(doc["state"]=="MEASURED_READ_ONLY_NOT_TEST_RUN_OR_MONITOR_REPLACEMENT"
            and doc["logical_processors"]==16 and doc["measurement_process_cpu_limit"]==1
            and doc["priority"]=="BelowNormal" and doc["stored_test_started"] is False
            and doc["measurements_have_adjacent_not_identical_windows"] is True
            and doc["existing_runner_or_thresholds_modified"] is False
            and doc["system_settings_changed"] is False and doc["P09_gate"]=="OPEN"
            and doc["product_complete"] is False,"measurement_scope_drift")
    require(len(doc["samples"])==4,"measurement_count_drift")
    hot=0
    for index,sample in enumerate(doc["samples"]):
        require(type(sample["index"]) is int and sample["index"]==index
                and number(sample["native_interval_seconds"],1,60),"measurement_order_or_window_drift")
        for key in ("native_cpu_percent","cim_cpu_percent"):
            require(number(sample[key],0,100),"measurement_cpu_invalid")
        require(number(sample["native_total_ram_mib"],1,1024*1024),"measurement_memory_invalid")
        for key in ("native_available_ram_mib","cim_available_ram_mib"):
            require(number(sample[key],0,sample["native_total_ram_mib"]),"measurement_memory_invalid")
        cpu=max(sample["native_cpu_percent"],sample["cim_cpu_percent"])
        free=min(sample["native_available_ram_mib"],sample["cim_available_ram_mib"])
        require(sample["conservative_inputs"]=={"system_cpu_percent":cpu,"available_ram_mib":free},"conservative_inputs_relaxed")
        hot=hot+1 if cpu>=85 else 0
        if observed_hot:
            require(type(sample["consecutive_hot_samples"]) is int and sample["consecutive_hot_samples"]==hot,"hot_sample_count_drift")
            decision="STOP_LOW_AVAILABLE_RAM" if free<4096 else "STOP_SUSTAINED_SYSTEM_CPU" if hot>=3 else "CONTINUE"
            require(sample["resource_decision"]==decision,"measurement_decision_drift")
    return {"samples":4,"native_cpu_max":max(s["native_cpu_percent"] for s in doc["samples"]),
            "native_available_ram_min_mib":min(s["native_available_ram_mib"] for s in doc["samples"])}

def inherited():
    require(BASE.pin(PARTIAL)=={"path":PARTIAL,"bytes":8731,"sha256":"e898d52c8efaf9a34838efddfc36ec442e4029e2bba7fb5189417412688e4dcb"},"P121_partial_checkpoint_drift")
    require(BASE.pin(FINAL)=={"path":FINAL,"bytes":2858,"sha256":"b9fc666c52883956f38a59f95f26fcfcdcc9d1fa73e0de64771d47a5c27a7bf1"},"P121_final_partial_audit_drift")
    old=P121.partial()
    require(old["current_source_files"]==1109 and old["full228_accepted"] is False,"P121_partial_scope_drift")
    return old

def current():
    old=inherited()
    doc=json.loads((ROOT/CURRENT).read_bytes())
    require(doc["product_complete"] is False and doc["P09_gate"]=="OPEN"
            and doc["P10_new_implementation"] is False and doc["goal_status"]=="active","checkpoint_scope_drift")
    require(doc["previous_source_files_count"]==1109 and doc["current_source_files_count"]==1117
            and doc["inherited_raw_pin_entries"]==2340,"source_or_evidence_coverage_drift")
    groups={"source_delta":DELTA,"source_archives_added":ARCHIVES,"predecessor_receipts_added":[PARTIAL,FINAL],"runtime_runs":[*RUNS,*FULL]}
    for group,paths in groups.items():
        rows=doc[group]
        require(len(rows)==len(paths) and {r["path"] for r in rows}==set(paths)
                and all(BASE.exact(r) for r in rows),"checkpoint_pin_coverage_drift")
    sources=P121.original_sources()
    sources.update({r["path"]:r for r in json.loads((ROOT/PARTIAL).read_bytes())["source_delta"]})
    sources.update({r["path"]:r for r in doc["source_delta"]})
    require(len(sources)==1117 and all(BASE.exact(r) for r in sources.values()),"whole_source_inventory_drift")
    pairs=[json.loads((ROOT/path).read_bytes()) for path in RUNS]
    values=[validate_pairs(pairs[0],False),validate_pairs(pairs[1],True)]
    summary=json.loads((ROOT/DELTA[-1]).read_bytes())
    require(summary["pair_results"]==values and summary["existing_runner_modified"] is False,"measurement_summary_drift")
    failure=json.loads((ROOT/DELTA[-2]).read_bytes())
    require(failure["state"]=="FAILED_BEFORE_FIRST_NATIVE_SAMPLE_NOT_MEASURED" and failure["actual_command_exit_code"]==1
            and failure["planned_initial_receipt_created"] is False and failure["native_metric_API_called"] is False,"initial_measurement_failure_drift")
    freeze=json.loads((ROOT/P121.FREEZE).read_bytes())["source_freeze"]
    stopped=json.loads((ROOT/FULL[0]).read_bytes())
    require(stopped["state"]=="NOT_ACCEPTED_STOP_OR_FAILURE" and stopped["stop_reason"]=="STOP_SUSTAINED_SYSTEM_CPU"
            and stopped["source_freeze"]==freeze and stopped["source_freeze_exact_after"] is True
            and stopped["tests"]["terminal_summary"] is None
            and all(s["system_cpu_percent"]>=85 for s in stopped["samples"][-3:]),"full_D_stop_not_preserved")
    latest=json.loads((ROOT/FULL[1]).read_bytes())
    accepted=latest["state"]=="PASS_RESOURCE_BOUNDED_SCOPED_TESTS_NOT_Gate"
    require(doc["full228_accepted"] is accepted,"full228_state_drift")
    if accepted:
        changed=P121.validate_runtime(latest,228,0,freeze,BASE.pin(P121.EXE))
        prior=json.loads((ROOT/P121.RUNS[6]).read_bytes())["tests"]["changed_corpus_result"]
        require(changed==prior and latest["tests"]["corpus_result"]["counts"]==[16,20,16,128,0,16]
                and latest["tests"]["current_derivatives_pass"] is True and latest["tests"]["protection_derivatives_pass"] is True,
                "full_original_or_changed_corpus_drift")
        require(doc["state"]=="PASS_METRIC_CROSSCHECK_AND_STORED228_NOT_PRODUCT_OR_GATE","full_accepted_state_drift")
    else:
        require(latest["state"]=="NOT_ACCEPTED_STOP_OR_FAILURE" and latest["stop_reason"]=="STOP_SUSTAINED_SYSTEM_CPU"
                and latest["exit_code"]==-1 and all(s["system_cpu_percent"]>=85 for s in latest["samples"][-3:])
                and latest["source_freeze"]==freeze and latest["executable_pin"]==BASE.pin(P121.EXE)
                and latest["source_freeze_exact_after"] is True and latest["tests"]["terminal_summary"] is None
                and doc["state"]=="PASS_METRIC_CROSSCHECK_FULL228_RESOURCE_BLOCKED_NOT_PRODUCT_OR_GATE","full_pending_state_drift")
    return {"state":doc["state"],"full228_accepted":accepted,"metric_pairs":8,"metric_unit_assertions":16,
            "previous_source_files":1109,"current_source_files":1117,"inherited_raw_pin_entries":2340,
            "current_groups":{g:len(doc[g]) for g in groups},"goal_status":"active","P09_gate":"OPEN","product_complete":False}

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current",action="store_true")
    args=parser.parse_args()
    try: print(json.dumps(current() if args.current else inherited(),separators=(",",":")))
    except (OSError,ValueError,KeyError,TypeError) as error:
        print(json.dumps({"state":"fail","error_type":type(error).__name__,"scope":"bytes_NOT_PRODUCT_OR_GATE"}))
        raise SystemExit(1) from None
