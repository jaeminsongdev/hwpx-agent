"""Invoke whole frozen factory/startup qualification on the v17 graph.

Not a Native or product entry. The original engine construction, worker EOF
probe, historical-open audit, limits, source checks and cleanup are retained.
The stable v17 worker source and its graph packets are never rewritten here.
"""
from pathlib import Path
import hashlib
import json
import re
import sys

SELF="tools/p09/xz_startup_adapter_v1.py"
TEST="tools/p09/tests/test_xz_startup_adapter_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
PROFILE=dict(path="tools/p09/xz_closed_preparation_v1.py",bytes=21098,
    sha256="a57347fa0df57fa6d296e3563fe66234d36d217799d399f3948072ac070b0cc5")
GRAPH=PREFIX+"successor-connections008.v17.json"
CODE=PREFIX+"xz-startup-adapter-code001.v1.json"
CODE_STATE="PASS_XZ_STARTUP_ORIGINAL_FACTORY_ADAPTER_CODE8_NOT_CHILD_OR_PRODUCT"
PASS="PASS_ACTUAL_XZ_WORKER_EOF_NO_GO_NOT_PARENT_PREFLIGHT_NATIVE_OR_PRODUCT"


def require(ok,label):
    if not ok:raise ValueError("XZ_STARTUP_ADAPTER_"+label)


def identifier(value):
    require(type(value) is int and 1<=value<=8,"FINITE_PREPARATION_ATTEMPT_NOT_NATIVE_RETRY")
    return value


def original_arguments(attempt):
    identifier(attempt)
    return ["--bootstrap","--case","165","--run","8","--attempt",str(attempt),"--code-attempt","2"]


def invoke(profile,root,envelope,a,delivery,attempt):
    arguments=original_arguments(attempt)
    linked=profile.connect(root,envelope,a,delivery,require_code=True,role="graph")
    previous=sys.argv
    try:
        sys.argv=[PROFILE["path"]]+arguments
        return linked.execute(linked.main,linked.envelope)
    finally:sys.argv=previous


def check_factory(record,a):
    a.fields(record,dict(state="PASS_WORKER_CLI_NO_GO_STARTUP_NOT_PARENT_ADMISSION_NATIVE_OR_PRODUCT",index=165,
        contracts=dict(run=11,errors=0,failures=0,skipped=0),accepted_count_delta=0,
        product_or_Native_executed=False,GO_authorized=False,cleanup_confirmed=True,
        actual_parent_and_worker_dispatch_counts=dict(parent=0,worker=0),owned_worker_cli_startup_connected=True,
        full_current_parent_admission_deferred_to_whole_preflight=True),"ACTUAL_ORIGINAL_FACTORY_STARTUP_NOT_RUNTIME")
    require(type(record["fresh_inputs"]) is int and record["fresh_inputs"]==record["final_fresh_hashes"]>0,"FRESH_FACTORY_SOURCE_CLOSURE")
    proof=record["worker_cli_NO_GO_rejection"]
    a.fields(proof,dict(original_GO_rejection_observed=True,historical_runtime_or_authority_opens=0,GO_sent=False,
        product_child_execution_authorized=False,full_worker_product_qualification=False),"ACTUAL_NO_GO_AND_ZERO_HISTORICAL_IO")
    require(type(proof["exit_code"]) is int and proof["exit_code"]!=0,"REAL_UNAUTHORIZED_WORKER_EXIT")


def witnesses(q,a,profile,*,code=True):
    for name in (SELF,TEST):q.pin(name)
    a.exact(q.pin(PROFILE["path"]),PROFILE,"STABLE_QUALIFIED_V17_WORKER_SOURCE")
    profile.code_witness(q,a)
    graph=q.json(GRAPH)
    a.fields(graph,dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",index=165,
        pair_count=68,new_ordinary_count=61,preserved_special_count=7,all_worker_rows_restored=True,
        accepted_count_delta=0,product_or_Native_executed=False,GO_authorized=False,cleanup_confirmed=True,
        fresh_inputs=222,final_fresh_hashes=222),"CURRENT_PARENT_WORKER_GRAPH_NOT_PRODUCT")
    for pin in graph["source_pins"]:
        if pin["path"].startswith("tools/p09/") and pin["path"].endswith(".py"):a.exact(q.pin(pin["path"]),pin,"ALL_CURRENT_GRAPH_PROGRAMS")
    for key in ("manifest_pin","capsule_pin","bootstrap_pin"):
        pin=graph[key];a.exact(q.pin(pin["path"]),pin,"ALL_ACTUAL_V17_PACKETS")
    if code:
        record=q.json(CODE)
        a.fields(record,dict(state=CODE_STATE,contracts=dict(run=8,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
            accepted_count_delta=0,product_or_Native_executed=False,GO_authorized=False),"CURRENT_STARTUP_ADAPTER_CODE8")
        require(type(record["fresh_inputs"]) is int and record["fresh_inputs"]==record["final_fresh_hashes"]>0,"ADAPTER_SOURCE_CLOSURE")
        for pin in record["source_pins"]:a.exact(q.pin(pin["path"]),pin,"UNCHANGED_ADAPTER_QUALIFIED_INPUTS")
    return graph


def main():
    import argparse,io,time,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import flat_current_queue_envelope_runtime_v25 as envelope
    import xz_corpus_delivery_v1 as delivery
    parser=argparse.ArgumentParser();modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--code",action="store_true");modes.add_argument("--probe",action="store_true")
    parser.add_argument("--attempt",required=True,type=int);args=parser.parse_args();identifier(args.attempt)
    output=PREFIX+f"xz-startup-{'adapter-code' if args.code else 'probe'}{args.attempt:03}.v1.json"
    require(not(c.ROOT/output).exists(),"EXCLUSIVE_STARTUP_RECORD")
    modules,_=envelope.namespace_bundle.load(c.ROOT,[PROFILE],{})
    profile=modules.xz_closed_preparation_v1
    def dynamic(path):
        raw=(c.ROOT/path).read_bytes();return dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    entries,_=envelope.namespace_bundle.load(c.ROOT,[dynamic("tools/p09/preparation_attributed_entry_v1.py")],{})
    entry=entries.preparation_attributed_entry_v1
    raw,_=envelope.namespace_bundle.load(c.ROOT,[entry.ENTRY,entry.POLICY_SOURCE]+entry.UTIL_PINS+[delivery.BASELINE],{})
    raw.prepared_run_closure_v1.configure_host_policy(c);policy=raw.preparation_attributed_cpu_v1
    metrics={};phase=dict(value="bootstrap_policy")
    original_guard=delivery.observed_guard(raw.terminal_metadata_pressure_v1.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard)),metrics,phase)
    def prep():
        phase["value"]="bootstrap_connection"
        return delivery.observed_guard(raw.owned_cpu_baseline_v1.guard_type(policy.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard),role="whole_metadata_preflight")),metrics,phase)()
    guards=[];started=time.monotonic();guard=None;q=None
    publisher=raw.successor_preparation_workspace_v1
    row=dict(state="FAILED_XZ_STARTUP_ADAPTER_NOT_ADOPTED",accepted_count_delta=0,GO_authorized=False,
        product_or_Native_executed=False,actual_startup_invoked=False,Native_policy_changed=False,automatic_retry=False)
    try:
        def verify_policy(q):
            entry.policy_witnesses(q,a,policy)
            a.exact(q.pin(delivery.BASELINE["path"]),delivery.BASELINE,"MEASURED_BASELINE")
        def verify(q):
            entry.witnesses(q,a,policy,connection_attempt=10)
            witnesses(q,a,profile,code=not args.code)
            if args.code:
                from tests import test_xz_startup_adapter_v1 as tests
                tests.MODULE=sys.modules[__name__];tests.ACCEPTANCE=a
                result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
                row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
                row["contract_errors"]=[dict(test=t.id().rsplit(".",1)[-1],exception_type=trace.splitlines()[-1].split(":",1)[0]) for t,trace in result.errors+result.failures]
                a.exact(row["contracts"],dict(run=8,errors=0,failures=0,skipped=0),"ALL_ORIGINAL_STARTUP_ADAPTER8")
        q,proof=entry.closed_bootstrap(c.ROOT,a,original_guard,prep,verify_policy,verify,guards)
        row["bootstrap_policy_validation"]=proof
        if args.code:
            row.update(state=CODE_STATE,source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
        else:
            # Previous mutex/sampler owners are closed before the original
            # factory constructs its own Guard and bounded EOF subprocess.
            require(all(g.cleanup for g in guards),"ALL_OWNERS_CLOSED_BEFORE_ORIGINAL_FACTORY")
            require(not(c.ROOT/(PREFIX+"current-runtime-run008.v1.json")).exists(),"NATIVE008_ABSENT_BEFORE")
            row["actual_startup_invoked"]=True;exit_code=invoke(profile,c.ROOT,envelope,a,delivery,args.attempt)
            row["original_factory_exit_code"]=exit_code
            guard=prep();guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
            witnesses(q,a,profile)
            factory_name=PREFIX+f"successor-xz-factory{args.attempt:03}.v1.json"
            factory=q.json(factory_name);row["factory_receipt_pin"]=q.snapshots[factory_name]
            check_factory(factory,a);require(type(exit_code) is int and exit_code==0,"WHOLE_ORIGINAL_FACTORY_SUCCESS")
            for pin in factory["source_pins"]:a.exact(q.pin(pin["path"]),pin,"UNCHANGED_ACTUAL_FACTORY_SOURCES")
            require(not(c.ROOT/(PREFIX+"current-runtime-run008.v1.json")).exists(),"NATIVE008_ABSENT_AFTER")
            q.finish();guard.check(force=True)
            row.update(state=PASS,worker_cli_NO_GO_rejection=factory["worker_cli_NO_GO_rejection"],
                source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        if guard is not None:guard.close()
        samples=[s for g in guards for s in g.samples]+([] if guard is None else guard.samples)
        row.update(cleanup_confirmed=all(g.cleanup for g in guards) and (guard is None or guard.cleanup),
            original_fresh_sample_resource_summary=metrics,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in samples),default=None),RAM_min=min((s["available_ram_percent"] for s in samples),default=None))
    require(row["cleanup_confirmed"],"ALL_ADAPTER_GUARDS_CLOSED");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","contract_errors","actual_startup_invoked","original_factory_exit_code",
        "fresh_inputs","final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed","elapsed_seconds","error_code")}))
    return 0 if row["state"] in (PASS,CODE_STATE) else 1


if __name__=="__main__":raise SystemExit(main())
