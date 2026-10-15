"""Whole original CODE74 plus current XZ/EOF source witnesses.

Does not run preflight, dispatch, Native or acceptance. No helper ceiling or
original controller contract is changed. Every stage is a fresh invocation.
"""
from pathlib import Path
import json
import re
import sys

SELF="tools/p09/xz_whole_code_adapter_v1.py"
TEST="tools/p09/tests/test_xz_whole_code_adapter_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
CODE=PREFIX+"xz-whole-code-adapter-code001.v1.json"
CODE_STATE="PASS_XZ_WHOLE_CODE_ADAPTER6_NOT_ORIGINAL_CODE_OR_PRODUCT"
PASS="PASS_WHOLE_ORIGINAL_CODE74_AND_XZ_EOF_SOURCES_NOT_PREFLIGHT_OR_PRODUCT"


def require(ok,label):
    if not ok:raise ValueError("XZ_WHOLE_CODE_"+label)


def arguments(attempt):
    require(type(attempt) is int and 1<=attempt<=8,"ORIGINAL_CODE_ATTEMPT_NOT_NATIVE")
    return ["--code","--case","165","--run","8","--attempt",str(attempt)]


def invoke(profile,root,envelope,a,delivery,attempt):
    argv=arguments(attempt);linked=profile.connect(root,envelope,a,delivery,require_code=True,role="graph");previous=sys.argv
    try:
        sys.argv=[profile.SELF]+argv
        return linked.execute(linked.main,linked.envelope)
    finally:sys.argv=previous


def validate(record,a):
    a.fields(record,dict(state="PASS_CURRENT_SUCCESSOR_CODE_NOT_FULL_PREFLIGHT_NATIVE_OR_PRODUCT",index=165,physical_run=8,
        contracts=dict(run=74,errors=0,failures=0,skipped=0),cleanup_confirmed=True,accepted_count_delta=0,
        product_or_Native_executed=False,GO_authorized=False,runtime_imported_helper_bound=64,
        new_runtime_process_required_before_preflight_or_Native=True,independent_checker_source_and_controller_contracts_included=True),"ORIGINAL_WHOLE_CONTROLLER74")
    require(type(record["runtime_default_import_count"]) is int and 0<record["runtime_default_import_count"]<=64,"ORIGINAL_PRODUCTION_HELPER_CEILING")
    require(type(record["fresh_inputs"]) is int and record["fresh_inputs"]==record["final_fresh_hashes"]>0,"ALL_ORIGINAL_CODE_CLOSING_HASHES")


def witnesses(q,a,profile,startup,*,adapter_code):
    for path in (SELF,TEST):q.pin(path)
    startup.witnesses(q,a,profile)
    probe=q.json(PREFIX+"xz-startup-probe001.v1.json")
    a.fields(probe,dict(state=startup.PASS,cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False,
        product_or_Native_executed=False,actual_startup_invoked=True,original_factory_exit_code=0),"ACTUAL_EOF_PROBE_NOT_PRODUCT")
    require(type(probe["fresh_inputs"]) is int and probe["fresh_inputs"]==probe["final_fresh_hashes"]>0,"EOF_SOURCE_CLOSURE")
    factory=a.read_exact(q,probe["factory_receipt_pin"]);startup.check_factory(factory,a)
    for pin in probe["source_pins"]:
        if pin["path"].startswith("tools/p09/") and pin["path"].endswith(".py"):a.exact(q.pin(pin["path"]),pin,"ALL_CURRENT_EOF_SOURCE_PROGRAMS")
    if adapter_code:
        record=q.json(CODE)
        a.fields(record,dict(state=CODE_STATE,contracts=dict(run=6,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
            accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False),"CURRENT_WHOLE_CODE_ADAPTER6")
        require(type(record["fresh_inputs"]) is int and record["fresh_inputs"]==record["final_fresh_hashes"]>0,"ADAPTER_FRESH_SOURCE_CLOSURE")
        for pin in record["source_pins"]:a.exact(q.pin(pin["path"]),pin,"UNCHANGED_CODE_ADAPTER_SOURCES")


def main():
    import argparse,hashlib,io,time,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import flat_current_queue_envelope_runtime_v25 as envelope
    import xz_corpus_delivery_v1 as delivery
    import xz_startup_adapter_v1 as startup
    parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--code",action="store_true");mode.add_argument("--qualify",action="store_true")
    parser.add_argument("--attempt",type=int,required=True);args=parser.parse_args();arguments(args.attempt)
    output=PREFIX+f"xz-whole-code-{'adapter-code' if args.code else 'qualification'}{args.attempt:03}.v1.json"
    original_output=PREFIX+f"successor-code-run008-attempt{args.attempt:03}.v1.json"
    require(not(c.ROOT/output).exists() and (args.code or not(c.ROOT/original_output).exists()),"EXCLUSIVE_WHOLE_CODE_OUTPUTS")
    profile_ns,_=envelope.namespace_bundle.load(c.ROOT,[startup.PROFILE],{})
    profile=profile_ns.xz_closed_preparation_v1
    def dynamic(path):
        data=(c.ROOT/path).read_bytes();return dict(path=path,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    entries,_=envelope.namespace_bundle.load(c.ROOT,[dynamic("tools/p09/preparation_attributed_entry_v1.py")],{})
    entry=entries.preparation_attributed_entry_v1
    raw,_=envelope.namespace_bundle.load(c.ROOT,[entry.ENTRY,entry.POLICY_SOURCE]+entry.UTIL_PINS+[delivery.BASELINE],{})
    raw.prepared_run_closure_v1.configure_host_policy(c);policy=raw.preparation_attributed_cpu_v1
    metrics={};phase=dict(value="bootstrap_policy")
    original_guard=delivery.observed_guard(raw.terminal_metadata_pressure_v1.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard)),metrics,phase)
    def prep():
        phase["value"]="bootstrap_connection"
        return delivery.observed_guard(raw.owned_cpu_baseline_v1.guard_type(policy.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard),role="whole_metadata_preflight")),metrics,phase)()
    guards=[];guard=None;q=None;started=time.monotonic()
    row=dict(state="FAILED_XZ_WHOLE_CODE_NOT_ADOPTED",accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False,
        actual_original_CODE_invoked=False,Native_policy_changed=False,original_helper_ceiling=64,automatic_retry=False)
    try:
        def verify_policy(q):
            entry.policy_witnesses(q,a,policy)
            a.exact(q.pin(delivery.BASELINE["path"]),delivery.BASELINE,"MEASURED_CPU_BASELINE")
        def verify(q):
            entry.witnesses(q,a,policy,connection_attempt=10)
            witnesses(q,a,profile,startup,adapter_code=not args.code)
            if args.code:
                from tests import test_xz_whole_code_adapter_v1 as tests
                tests.MODULE=sys.modules[__name__];tests.ACCEPTANCE=a
                result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
                row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
                a.exact(row["contracts"],dict(run=6,errors=0,failures=0,skipped=0),"ALL_WHOLE_CODE_ADAPTER6")
        q,proof=entry.closed_bootstrap(c.ROOT,a,original_guard,prep,verify_policy,verify,guards);row["bootstrap_policy_validation"]=proof
        if args.code:
            row.update(state=CODE_STATE,source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
        else:
            require(all(g.cleanup for g in guards),"ALL_BOOTSTRAP_OWNERS_CLOSED")
            root=c.ROOT/(PREFIX+"current-runtime-run008.v1.json");require(not root.exists(),"NO_NATIVE_BEFORE_CODE")
            row["actual_original_CODE_invoked"]=True;exit_code=invoke(profile,c.ROOT,envelope,a,delivery,args.attempt);row["original_CODE_exit_code"]=exit_code
            guard=prep();guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
            witnesses(q,a,profile,startup,adapter_code=True)
            original=q.json(original_output);row["original_CODE_pin"]=q.snapshots[original_output]
            validate(original,a);require(type(exit_code) is int and exit_code==0,"ORIGINAL_WHOLE_CODE_SUCCESS")
            for pin in original["source_pins"]:a.exact(q.pin(pin["path"]),pin,"ALL_CURRENT_CODE74_SOURCES")
            require(not root.exists(),"NO_NATIVE_AFTER_CODE");q.finish();guard.check(force=True)
            row.update(state=PASS,original_contracts=original["contracts"],runtime_default_import_count=original["runtime_default_import_count"],
                code_and_test_import_count=original["code_and_test_import_count"],source_pins=list(q.snapshots.values()),
                fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        if guard is not None:guard.close()
        samples=[s for g in guards for s in g.samples]+([] if guard is None else guard.samples)
        row.update(cleanup_confirmed=all(g.cleanup for g in guards) and (guard is None or guard.cleanup),elapsed_seconds=time.monotonic()-started,
            original_fresh_sample_resource_summary=metrics,CPU_max=max((s["system_cpu_percent"] for s in samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in samples),default=None))
    require(row["cleanup_confirmed"],"ALL_WHOLE_CODE_GUARDS_CLOSED");raw.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","original_contracts","actual_original_CODE_invoked","original_CODE_exit_code",
        "runtime_default_import_count","fresh_inputs","final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed","elapsed_seconds","error_code")}))
    return 0 if row["state"] in (PASS,CODE_STATE) else 1


if __name__=="__main__":raise SystemExit(main())
