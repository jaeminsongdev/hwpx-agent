"""Explicit graph-only retry admission with immutable v2 execution bodies.

A failed graph receipt is not fabricated Native evidence. Actual absence of
the old Native/capsule/bootstrap and the closed graph failure are required.
Existing Native records still use v2's complete closed-prebody validator.
"""
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import math
import sys

SELF="tools/p09/current_queue_successor_retry_runtime_v3.py"
TEST="tools/p09/tests/test_current_queue_successor_retry_runtime_v3.py"
BRIDGE=dict(path="tools/p09/current_queue_successor_wire_runtime_v2.py",bytes=11932,
    sha256="74c509ee713b571a8ed8d52f904513a567ff19391fb418942d1336a5ce6d6efd")
BRIDGE_TEST=dict(path="tools/p09/tests/test_current_queue_successor_wire_runtime_v2.py",bytes=3940,
    sha256="fae649027fe5cfa4951f6f082331e27971f35118f274a53dd04118716fa0a4fa")
REVIEW=dict(path="tools/p09/current_queue_successor_wire_review_v2.py",bytes=4774,
    sha256="d27372827c7142fa4bcd5fdc0822bb2136d42bd53a110df354f046d2b98557c6")


def absent(q,name,a):
    q.checkpoint()
    path=q.root/name
    for parent in (path.parent,*path.parent.parents):
        a.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"V3_DIRECT_ABSENCE_ANCESTORS")
        if parent==q.root:break
    try:path.lstat()
    except FileNotFoundError:return True
    return False  # Includes symlinks, broken links and directories, not just files.


def failed_graph(row,index,a):
    keys={"state","index","accepted_count_delta","product_or_Native_executed","GO_authorized",
        "P09_gate","error_code","cleanup_confirmed","elapsed_seconds","CPU_max","RAM_min"}
    a.require(type(row) is dict and set(row)==keys,"V3_EXACT_CLOSED_GRAPH_FAILURE")
    a.fields(row,dict(state="FAILED_SUCCESSOR_GRAPH_PREPARATION_NOT_ADOPTED",index=index,
        accepted_count_delta=0,product_or_Native_executed=False,GO_authorized=False,
        P09_gate="OPEN",cleanup_confirmed=True,error_code="STOP_TERMINAL_METADATA_WARNING_BEFORE_MORE_WORK"),
        "V3_GRAPH_ONLY_PRESSURE_STOP")
    for name in ("elapsed_seconds","CPU_max","RAM_min"):
        value=row[name]
        a.require(type(value) in (int,float) and math.isfinite(value) and value>=0,"V3_REAL_GRAPH_METRIC")
    a.require(row["CPU_max"]<=100 and row["RAM_min"]<=100,"V3_REAL_GRAPH_PERCENT")


def previous_stops(q,ctx,a,bridge):
    for run in range(2,ctx.run):
        root=f"implementation/p09/evidence/p09-361-case{ctx.index}-current-runtime-run{run:03}.v1.json"
        if not absent(q,root,a):
            bridge.closed_prebody_stop(q.json(root),ctx.index,run,a)
            continue
        graph=f"implementation/p09/evidence/p09-361-case{ctx.index}-successor-connections{run:03}.v2.json"
        failed_graph(q.json(graph),ctx.index,a)
        for suffix in (f"successor-worker-capsule{run:03}.compact.v2.json",f"successor-worker-bootstrap{run:03}.v2.json"):
            a.require(absent(q,f"implementation/p09/evidence/p09-361-case{ctx.index}-"+suffix,a),
                "V3_NO_UNRESOLVED_PREPARED_WORKER_ARTIFACT")
        a.require(absent(q,root,a),"V3_NATIVE_ABSENCE_RECHECK")


def bind_metadata(bridge):
    # Only current entry/test filename metadata changes; the frozen v2 source
    # is not edited and every original function body/default/closure survives.
    for fn in vars(bridge).values():
        if type(fn) is FunctionType and fn.__globals__.get("__name__","").startswith("p09_exact_"):
            fn.__globals__.update(SELF=SELF,TEST=TEST)
    bridge.SELF,bridge.TEST=SELF,TEST


def load(root,a,scope,bytes_policy,envelope,bridge,qualification_path,*,worker=False):
    class WitnessReader(a.AcceptanceReader):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            for pin in (BRIDGE,BRIDGE_TEST):a.exact(self.pin(pin["path"]),pin,"V3_FROZEN_BRIDGE_AND_TEST")
            if qualification_path is not None:
                row=self.json(qualification_path)
                a.fields(row,dict(state="PASS_GRAPH_RETRY_CODE_NOT_NATIVE_OR_PRODUCT",
                    contracts=dict(run=6,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
                    accepted_count_delta=0,product_or_Native_executed=False),"V3_QUALIFIED_RETRY_CODE")
                for pin in row["source_pins"]:a.exact(self.pin(pin["path"]),pin,"V3_CURRENT_TESTED_RETRY_CODE")
    api=NS(**{**vars(a),"AcceptanceReader":WitnessReader})
    modules,proof=bridge.load(root,api,scope,bytes_policy,envelope,worker=worker)
    dispatch=modules.current_queue_successor_dispatch
    def closed(q,ctx,aa):return previous_stops(q,ctx,aa,bridge)
    for fn in vars(dispatch).values():
        if type(fn) is FunctionType and fn.__globals__.get("__name__","").startswith("p09_exact_current_queue_successor_dispatch"):
            fn.__globals__["previous_stops"]=closed
    dispatch.previous_stops=closed
    return modules,proof


def qualify(root,a,envelope,bridge,output):
    import io,json,os,time,unittest
    names,proof=envelope.namespace_bundle.load(root,[bridge.OLD_CONTROLLER],
        {"flat_current_queue_envelope_runtime_v25":envelope})
    guards=names.case160_run007_controller.base.FIRST
    guard=guards.terminal_metadata_pressure_v1.guard_type(guards.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    a.require(not (root/output).exists(),"V3_EXCLUSIVE_RETRY_CODE")
    started=time.monotonic();q=None
    row=dict(state="FAILED_GRAPH_RETRY_CODE_NOT_ADOPTED",accepted_count_delta=0,product_or_Native_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(root,guard.check)
        own=q.pin(SELF);test=q.pin(TEST)
        for pin in (BRIDGE,BRIDGE_TEST,bridge.OLD_CONTROLLER):a.exact(q.pin(pin["path"]),pin,"V3_ALL_FROZEN_PINS")
        tests,proof=envelope.namespace_bundle.load(root,[test],{"current_queue_successor_retry_runtime_v3":
            NS(absent=absent,failed_graph=failed_graph,previous_stops=previous_stops,bind_metadata=bind_metadata,SELF=SELF,TEST=TEST)})
        suite_module=tests.test_current_queue_successor_retry_runtime_v3
        suite_module.Tests.setUp.__globals__["CHECKPOINT"]=guard.check
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(suite_module))
        contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row["contracts"]=contracts
        a.exact(contracts,dict(run=6,errors=0,failures=0,skipped=0),"V3_ALL_RETRY6_CONTRACTS")
        q.finish();guard.check(force=True)
        row.update(state="PASS_GRAPH_RETRY_CODE_NOT_NATIVE_OR_PRODUCT",source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        import re
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    a.require(guard.cleanup,"V3_CODE_CLEANUP")
    path=root/output
    for parent in (path.parent,*path.parent.parents):
        a.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"V3_DIRECT_CODE_ANCESTORS")
        if parent==root:break
    raw=(json.dumps(row,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8")
    a.require(0<len(raw)<=262144,"V3_BOUNDED_CODE_RECEIPT")
    with path.open("xb") as stream:
        a.exact(stream.write(raw),len(raw),"V3_COMPLETE_CODE_RECEIPT");stream.flush();os.fsync(stream.fileno())
    print(json.dumps({k:row.get(k) for k in ("state","contracts","fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


def main():
    import argparse
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_envelope_runtime_v25 as envelope
    frozen,proof=envelope.namespace_bundle.load(c.ROOT,[BRIDGE],{})
    bridge=frozen.current_queue_successor_wire_runtime_v2
    bind_metadata(bridge)
    is_worker=len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]
    if is_worker:
        modules,proof=load(c.ROOT,a,scope,bytes_policy,envelope,bridge,None,worker=True)
        return modules.current_queue_successor_runtime.owned_worker_entry(sys.argv[3])
    parser=argparse.ArgumentParser()
    for name in ("case","run","attempt"):parser.add_argument("--"+name,type=int,required=True)
    for name in ("code-attempt","preflight-attempt","qualification-attempt","retry-code-attempt","binding-attempt","review-attempt","acceptance-attempt"):
        parser.add_argument("--"+name,type=int,default=1)
    parser.add_argument("--root-bytes",type=int);parser.add_argument("--root-sha256")
    mode=parser.add_mutually_exclusive_group(required=True)
    for name in ("retry-code","graph","bootstrap","code","preflight","qualify","native","review","accept"):mode.add_argument("--"+name,action="store_true")
    args=parser.parse_args()
    a.require(164<=args.case<=249 and 2<=args.run<=8,"V3_CLOSED_CONTEXT")
    qualification=f"implementation/p09/evidence/p09-361-case{args.case}-retry-code{args.retry_code_attempt:03}.v1.json"
    if args.retry_code:return qualify(c.ROOT,a,envelope,bridge,qualification)
    modules,proof=load(c.ROOT,a,scope,bytes_policy,envelope,bridge,qualification)
    runtime=modules.current_queue_successor_runtime;controller=modules.current_queue_successor_controller;dispatch=modules.current_queue_successor_dispatch
    if args.graph:return modules.current_queue_successor_connections.prepare(args.case,args.binding_attempt,args.run,0)
    if args.bootstrap:return runtime.qualify_factory(args.case,args.run,args.run,args.attempt,True)
    if args.code:return controller.run_code(args.case,args.run,args.attempt)
    if args.preflight:return controller.run_preflight(args.case,args.run,args.code_attempt,args.attempt)
    ctx=dispatch.context(args.case,args.run,args.code_attempt,args.preflight_attempt,args.qualification_attempt)
    if args.qualify or args.native:return dispatch.main(ctx,args.qualify)
    a.require(type(args.root_bytes) is int and args.root_bytes>0 and type(args.root_sha256) is str,"V3_EXACT_ROOT_PIN_REQUIRED")
    review_modules,proof=envelope.namespace_bundle.load(c.ROOT,[REVIEW],{})
    adapter=review_modules.current_queue_successor_wire_review_v2
    facade=NS(**{**vars(bridge),"load":lambda root,aa,ss,bb,ee:load(root,aa,ss,bb,ee,bridge,qualification)})
    reviewer,acceptor,proof=adapter.load(c.ROOT,a,scope,bytes_policy,envelope,facade)
    root_pin=dict(path=ctx.root,bytes=args.root_bytes,sha256=args.root_sha256)
    if args.review:return reviewer.main(ctx,root_pin,args.review_attempt)
    return acceptor.main(ctx,root_pin,args.review_attempt,args.acceptance_attempt)


if __name__=="__main__":raise SystemExit(main())
