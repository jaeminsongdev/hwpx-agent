"""Successors165..249: frozen lossless engine with sealed metadata accounting.

Original product/Frame/checker bodies and guards stay. New entry, tests and
qualification are real source inputs. No case-specific source clones or replay.
"""
import ast
import copy
import hashlib
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import sys

SELF="tools/p09/current_queue_sealed_metadata_runtime_v5.py"
TEST="tools/p09/tests/test_current_queue_sealed_metadata_runtime_v5.py"
PINS=[dict(path="tools/p09/current_queue_successor_lossless_runtime_v4.py",bytes=18227,
    sha256="8ff8d105e753e2727b7fe4294f1e2b6fe6d670bd9d12e69afac5946888602db8"),
    dict(path="tools/p09/lossless_metadata_scope_review_v1.py",bytes=10340,
    sha256="cb42bf7b99e460ca0aaaeadacf11e9aeb14d5fe3717f6ea9b9e7a62515c34c21")]
BASE_QUAL="implementation/p09/evidence/p09-361-case164-lossless-v4-adoption-code003.v1.json"


def require(ok,label):
    if not ok:raise ValueError("SEALED_METADATA_V5_"+label)


def source_qualification(index,attempt):
    require(type(index) is int and 165<=index<=249 and type(attempt) is int and 1<=attempt<=8,"CLOSED_SOURCE_CONTEXT")
    return f"implementation/p09/evidence/p09-361-case{index}-sealed-metadata-code{attempt:03}.v1.json"


def retry_paths(raw,namespace,pin):
    """Only three graph artifact suffixes; existing Native predicates unchanged."""
    require(len(raw)==pin["bytes"] and hashlib.sha256(raw).hexdigest()==pin["sha256"],"EXACT_RETRY_SOURCE")
    original=next(n for n in ast.parse(raw.decode("utf-8")).body if isinstance(n,ast.FunctionDef) and n.name=="previous_stops")
    changed=copy.deepcopy(original);count=0
    for value in ast.walk(changed):
        if isinstance(value,ast.Constant) and type(value.value) is str and value.value.endswith(".v2.json"):
            value.value=value.value[:-8]+".v4.json";count+=1
    require(count==3,"THREE_RETRY_SUFFIXES")
    inverse=copy.deepcopy(changed)
    for value in ast.walk(inverse):
        if isinstance(value,ast.Constant) and type(value.value) is str and value.value.endswith(".v4.json"):
            value.value=value.value[:-8]+".v2.json"
    require(ast.dump(inverse,include_attributes=False)==ast.dump(original,include_attributes=False),"ENTIRE_RETRY_AST_INVERSE")
    env=namespace.previous_stops.__globals__
    exec(compile(ast.fix_missing_locations(ast.Module(body=[changed],type_ignores=[])),SELF,"exec"),env)
    namespace.previous_stops=env["previous_stops"]


def witness_api(a,qualification_path):
    class Reader(a.AcceptanceReader):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            for name in (SELF,TEST):self.pin(name)
            for pin in PINS:a.exact(self.pin(pin["path"]),pin,"V5_FROZEN_ENGINE_AND_SCOPE_CHECKER")
            if qualification_path is not None:
                row=self.json(qualification_path)
                a.fields(row,dict(state="PASS_SEALED_METADATA_V5_CODE_NOT_NATIVE_PRODUCT_OR_QUEUE",
                    contracts=dict(run=19,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
                    accepted_count_delta=0,product_or_Native_executed=False),"MANDATORY_V5_SOURCE_QUALIFICATION")
                a.require(row["fresh_inputs"]==row["final_fresh_hashes"]>0,"CLOSED_V5_CODE_HASHES")
                for pin in row["source_pins"]:a.exact(self.pin(pin["path"]),pin,"ALL_CURRENT_V5_QUALIFIED_SOURCES")
    return NS(**{**vars(a),"AcceptanceReader":Reader})


def load(root,a,scope,bytes_policy,envelope,qualification_path,*,worker=False,ctx=None):
    names,proof=envelope.namespace_bundle.load(root,PINS,{})
    v4=names.current_queue_successor_lossless_runtime_v4;review_policy=names.lossless_metadata_scope_review_v1
    components,proof=envelope.namespace_bundle.load(root,v4.PINS,{})
    retry=components.current_queue_successor_retry_runtime_v3
    retry_paths((root/v4.PINS[0]["path"]).read_bytes(),retry,v4.PINS[0])
    # Entry/test path metadata only; v4's frozen bodies remain private and exact.
    for fn in vars(v4).values():
        if type(fn) is FunctionType and fn.__globals__.get("__name__","").startswith("p09_exact_"):
            fn.__globals__.update(SELF=SELF,TEST=TEST)
    v4.SELF,v4.TEST=SELF,TEST
    wrap=None
    if ctx is not None:
        wrap=review_policy.connect_review(v4,(root/PINS[0]["path"]).read_bytes(),ctx)
    api=witness_api(a,None if worker else qualification_path)
    modules,bridge,oracle=v4.load(root,api,scope,bytes_policy,envelope,components,None if worker else BASE_QUAL,worker=worker)
    return NS(modules=modules,bridge=bridge,oracle=oracle,v4=v4,components=components,api=api,
        review_policy=review_policy,wrap=wrap)


def qualify(root,a,envelope,output):
    import io,json,os,time,unittest
    names,proof=envelope.namespace_bundle.load(root,PINS,{})
    v4=names.current_queue_successor_lossless_runtime_v4
    retry,proof=envelope.namespace_bundle.load(root,[v4.PINS[0]],{})
    bridge,proof=envelope.namespace_bundle.load(root,[retry.current_queue_successor_retry_runtime_v3.BRIDGE],{})
    old,proof=envelope.namespace_bundle.load(root,[bridge.current_queue_successor_wire_runtime_v2.OLD_CONTROLLER],
        {"flat_current_queue_envelope_runtime_v25":envelope})
    guards=old.case160_run007_controller.base.FIRST
    guard=guards.terminal_metadata_pressure_v1.guard_type(guards.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    require(not (root/output).exists(),"EXCLUSIVE_CODE_REPORT");started=time.monotonic()
    row=dict(state="FAILED_SEALED_METADATA_V5_CODE_NOT_ADOPTED",accepted_count_delta=0,product_or_Native_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(root,guard.check)
        for name in (SELF,TEST,"tools/p09/tests/test_current_queue_successor_lossless_runtime_v4.py",
            "tools/p09/tests/test_lossless_metadata_scope_review_v1.py"):q.pin(name)
        for pin in PINS+v4.PINS+[v4.ORACLE]:a.exact(q.pin(pin["path"]),pin,"EXACT_V5_COMPONENTS")
        base=q.json(BASE_QUAL)
        a.fields(base,dict(state="PASS_LOSSLESS_V4_ADOPTION_CODE_NOT_NATIVE_OR_PRODUCT",cleanup_confirmed=True,
            contracts=dict(run=6,errors=0,failures=0,skipped=0)),"FROZEN_COMPONENT_QUALIFICATION_NOT_NEW_NATIVE")
        for pin in base["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_FROZEN_COMPONENT_PROOFS")
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in
            ("tests.test_current_queue_successor_lossless_runtime_v4","tests.test_lossless_metadata_scope_review_v1",
             "tests.test_current_queue_sealed_metadata_runtime_v5"))
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row["contracts"]=contracts;a.exact(contracts,dict(run=19,errors=0,failures=0,skipped=0),"ALL_V5_19_CONTRACTS")
        q.finish();guard.check(force=True)
        row.update(state="PASS_SEALED_METADATA_V5_CODE_NOT_NATIVE_PRODUCT_OR_QUEUE",source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        import re
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"CODE_CLEANUP")
    raw=(json.dumps(row,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8")
    require(0<len(raw)<=262144,"BOUNDED_CODE_REPORT")
    path=root/output
    for parent in (path.parent,*path.parent.parents):require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_CODE_PARENTS")
    with path.open("xb") as stream:require(stream.write(raw)==len(raw),"COMPLETE_CODE_REPORT");stream.flush();os.fsync(stream.fileno())
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
    if len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]:
        linked=load(c.ROOT,a,scope,bytes_policy,envelope,None,worker=True)
        return linked.modules.current_queue_successor_runtime.owned_worker_entry(sys.argv[3])
    parser=argparse.ArgumentParser()
    for name in ("case","run","attempt"):parser.add_argument("--"+name,type=int,required=True)
    for name in ("source-attempt","code-attempt","preflight-attempt","qualification-attempt","review-attempt","acceptance-attempt"):
        parser.add_argument("--"+name,type=int,default=1)
    parser.add_argument("--root-bytes",type=int);parser.add_argument("--root-sha256")
    mode=parser.add_mutually_exclusive_group(required=True)
    for name in ("source-code","graph","bootstrap","code","preflight","qualify","native","review","accept"):mode.add_argument("--"+name,action="store_true")
    args=parser.parse_args();qualification=source_qualification(args.case,args.source_attempt)
    require(type(args.run) is int and 2<=args.run<=8,"CLOSED_RUN")
    if args.source_code:return qualify(c.ROOT,a,envelope,qualification)
    prefix=f"implementation/p09/evidence/p09-361-case{args.case}-successor-"
    ctx=NS(preflight=prefix+f"preflight-run{args.run:03}-attempt{args.preflight_attempt:03}.v1.json",
        qualification=prefix+f"dispatch-qualification-run{args.run:03}-attempt{args.qualification_attempt:03}.v1.json")
    linked=load(c.ROOT,a,scope,bytes_policy,envelope,qualification,ctx=ctx)
    modules=linked.modules;runtime=modules.current_queue_successor_runtime;dispatch=modules.current_queue_successor_dispatch
    if args.graph:return modules.current_queue_successor_connections.prepare(args.case,1,args.run,0)
    if args.bootstrap:return runtime.qualify_factory(args.case,args.run,args.run,args.attempt,True)
    if args.code:return modules.current_queue_successor_controller.run_code(args.case,args.run,args.attempt)
    if args.preflight:return modules.current_queue_successor_controller.run_preflight(args.case,args.run,args.code_attempt,args.attempt)
    ctx=dispatch.context(args.case,args.run,args.code_attempt,args.preflight_attempt,args.qualification_attempt)
    if args.qualify or args.native:return dispatch.main(ctx,args.qualify)
    adapters,proof=envelope.namespace_bundle.load(c.ROOT,[linked.components.current_queue_successor_retry_runtime_v3.REVIEW],{})
    facade=NS(**{**vars(linked.bridge),"load":lambda root,aa,ss,bb,ee:(linked.v4.load(root,witness_api(aa,qualification),ss,bb,ee,linked.components,BASE_QUAL)[0],{})})
    reviewer,acceptor,proof=adapters.current_queue_successor_wire_review_v2.load(c.ROOT,a,scope,bytes_policy,envelope,facade)
    linked.v4.override_import(reviewer,"current_queue_successor_oracle",linked.oracle)
    linked.v4.override_import(acceptor,"current_queue_successor_oracle",linked.oracle)
    import reusable_audit_chunk_v1 as scratch
    reader,proof=scratch.reader_type(a.AcceptanceReader,(c.ROOT/scratch.ORIGINAL_PIN["path"]).read_bytes())
    linked.v4.override_import(reviewer,"accept_case112_current_epoch",NS(**{**vars(a),"AcceptanceReader":reader}))
    linked.wrap(reviewer,dict(run=19,errors=0,failures=0,skipped=0),scratch,a)
    for namespace in (reviewer,acceptor):
        for fn in vars(namespace).values():
            if type(fn) is FunctionType and fn.__globals__.get("__name__","").startswith("p09_exact_"):fn.__globals__.update(SELF=SELF,TEST=TEST)
    root_pin=dict(path=ctx.root,bytes=args.root_bytes,sha256=args.root_sha256)
    if args.review:return reviewer.main(ctx,root_pin,args.review_attempt)
    return acceptor.main(ctx,root_pin,args.review_attempt,args.acceptance_attempt)


if __name__=="__main__":raise SystemExit(main())
