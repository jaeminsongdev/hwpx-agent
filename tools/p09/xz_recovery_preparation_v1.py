"""Current XZ profile on whole original post-body recovery preparation.

No Native/worker/review/accept entry. Historical closure worker pins remain
unchanged. CODE references read the actual qualified CODE005, not a copy.
"""
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import ast
import copy
import hashlib
import json
import re
import sys

SELF="tools/p09/xz_recovery_preparation_v1.py"
TEST="tools/p09/tests/test_xz_recovery_preparation_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
CODE=PREFIX+"xz-recovery-preparation-code004.v1.json"
CODE_STATE="PASS_XZ_CURRENT_CODE_REFERENCE_AND_RECOVERY_ADAPTER12_NOT_STAGE_OR_PRODUCT"
ACTUAL_CODE=PREFIX+"successor-code-run008-attempt005.v1.json"
RECOVERY_CODE=PREFIX+"successor-recovery-code-run008-attempt005.v1.json"
STARTUP=dict(path="tools/p09/xz_startup_adapter_v1.py",bytes=10562,
    sha256="2748aa439e6143ef665494df08f5ad4da96f7646f0bae85891509a6cd4f46ccf")
WHOLE=dict(path="tools/p09/xz_whole_code_adapter_v1.py",bytes=9651,
    sha256="9f96d79209d207db003df8218febe62a2fda5e048b344ea696f7c7d93d1dfcdb")


def require(ok,label):
    if not ok:raise ValueError("XZ_RECOVERY_PREPARATION_"+label)


def context(stage,attempt,preflight_attempt=None):
    require(stage in ("preflight","qualify"),"PREPARATION_ONLY_NOT_NATIVE_WORKER_OR_ACCEPT")
    limit=16 if stage=="preflight" else 8
    require(type(attempt) is int and 1<=attempt<=limit,"FINITE_STAGE_ATTEMPT")
    require((stage=="preflight" and preflight_attempt is None) or
        (stage=="qualify" and type(preflight_attempt) is int and 1<=preflight_attempt<=16),"EXPLICIT_PREPARATION_REFERENCE")
    args=["--"+stage,"--case","165","--run","8","--attempt",str(attempt),"--code-attempt","5"]
    if stage=="qualify":args.extend(["--preflight-attempt",str(preflight_attempt)])
    return args


def code_reference(value):
    require(type(value) is str and value in (RECOVERY_CODE,ACTUAL_CODE),"ONLY_EXACT_CURRENT165_RUN008_CODE005_REFERENCE")
    return ACTUAL_CODE


def publish(namespace,name,fn):
    previous=getattr(namespace,name);previous.__globals__[name]=fn;setattr(namespace,name,fn)


def reference_loader(original,recovery,*,witness=None):
    def load(*args,**kwargs):
        modules,proof=original.load(*args,**kwargs)
        driver=getattr(modules,"expanded_unhooked_setup_dependency_v1",None)
        if driver is not None:
            previous=driver.project_setup_main
            def setup(*items,**options):
                result=previous(*items,**options)
                return recovery.receipt_namespace(result,{"successor-recovery-code-run":"successor-code-run"})
            owner=getattr(driver,"main",previous)
            revised=FunctionType(setup.__code__,owner.__globals__,argdefs=setup.__defaults__,closure=setup.__closure__)
            publish(driver,"project_setup_main",revised)
            owner.__globals__["project_setup_main"]=revised
        fix=getattr(modules,"closed_prebody_factory_admission_fix_v1",None)
        if fix is not None:
            whole=fix.load
            def connected(*items,**options):
                values=list(items)
                if witness is not None:
                    api=values[1]
                    class Reader(api.AcceptanceReader):
                        def __init__(self,*args,**kwargs):
                            super().__init__(*args,**kwargs);witness(self)
                    values[1]=NS(**{**vars(api),"AcceptanceReader":Reader})
                linked=whole(*values,**options)
                controller=linked.modules.current_queue_successor_controller;dispatch=linked.modules.current_queue_successor_dispatch
                previous=controller.destination
                def destination(index,run,mode,attempt):
                    value=previous(index,run,mode,attempt)
                    return code_reference(value) if mode=="code" else value
                publish(controller,"destination",destination)
                prior=dispatch.context
                def current(*args,**kwargs):
                    ctx=prior(*args,**kwargs)
                    return NS(**{**vars(ctx),"code":code_reference(ctx.code)})
                publish(dispatch,"context",current)
                return linked
            fix.load=connected
        return modules,proof
    return NS(**{**vars(original),"load":load})


def project_closure(original,raw,wrap):
    require(type(original) is FunctionType and original.__code__.co_filename.replace("\\","/").endswith("prepared_run_closure_v1.py"),"WHOLE_FROZEN_CLOSURE_ENTRY")
    node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=="main")
    def compiled(value):
        env=dict(original.__globals__,_xz_current_recovery_profile=wrap)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[value],type_ignores=[])),original.__code__.co_filename,"exec",dont_inherit=True),env)
        return env["main"]
    require(compiled(copy.deepcopy(node)).__code__==original.__code__,"ENTIRE_ORIGINAL_CLOSURE_BODY_BEFORE_ADAPTER")
    before=ast.dump(node,include_attributes=False)
    expected=ast.parse("entry.main.__globals__['loader_profile']=profile").body[0].targets[0]
    targets=[n for n in ast.walk(node) if isinstance(n,ast.Assign) and len(n.targets)==1
        and ast.dump(n.targets[0],include_attributes=False)==ast.dump(expected,include_attributes=False)
        and isinstance(n.value,ast.Name) and n.value.id=="profile"]
    require(len(targets)==1,"ONE_COMPLETED_RECOVERY_PROFILE_DEPENDENCY")
    target=targets[0];old=target.value;target.value=ast.copy_location(ast.Call(func=ast.Name(id="_xz_current_recovery_profile",ctx=ast.Load()),args=[old],keywords=[]),old)
    result=compiled(copy.deepcopy(node));target.value=old
    require(ast.dump(node,include_attributes=False)==before and compiled(node).__code__==original.__code__,"WHOLE_CLOSURE_AST_AND_RECURSIVE_CODE_INVERSE")
    return result


def build(root,envelope,a,delivery,entry,closure,profile,policy,role,instances,*,witness=None):
    current=profile.connect(root,envelope,a,delivery,require_code=True,role="code")
    original=current.envelope.namespace_bundle;holder={}
    raw=(root/entry.ENTRY["path"]).read_bytes()
    require(len(raw)==entry.ENTRY["bytes"] and hashlib.sha256(raw).hexdigest()==entry.ENTRY["sha256"],"EXACT_FROZEN_CLOSURE_SOURCE")
    def aliased(*args,**kwargs):
        modules,proof=original.load(*args,**kwargs)
        legacy=getattr(modules,"level6_closed_preparation_v1",None)
        if legacy is not None:
            api=NS(**{**vars(current.frozen),"main":current.main,"loader_profile":current.main.__globals__["loader_profile"],
                "SELF":profile.SELF,"CORE":profile.CORE,"VERSION":profile.VERSION})
            # Same live family: later recovery-profile publication must remain
            # visible in the whole original main's actual import dependency.
            entry.bind_envelope(api,holder["envelope"])
            modules.level6_closed_preparation_v1=api
        return modules,proof
    alias=NS(**{**vars(original),"load":aliased})
    routed=entry.route_loader(root,entry.metadata_loader(alias),policy,a,role,instances,
        require_connection=True,connection_attempt=10,envelope=envelope)
    windows=entry.window_components(root,envelope);window=windows.post_product_recovery_window_v1
    routed,observations=windows.recovery_dispatch_window_v1.connect_loader(routed,envelope,
        windows.post_product_recovery_connection_v1,window,(root/window.WINDOW_PIN["path"]).read_bytes(),entry.bind_envelope,
        controller_transform=lambda old:entry.connect_old(old,policy,role,instances))
    proxy=NS(**{**vars(envelope),"namespace_bundle":routed});holder["envelope"]=proxy
    recovery=windows.post_product_recovery_connection_v1
    def wrap(previous):
        def completed(*args,**kwargs):return reference_loader(previous(*args,**kwargs),recovery,witness=witness)
        return completed
    fn=project_closure(closure.main,raw,wrap)
    return NS(main=fn,envelope=proxy,dispatch_window_observations=observations,
        legacy_closure_worker_ENTRY_pin=closure.ENTRY,current_worker_entry=profile.SELF,actual_CODE_reference=ACTUAL_CODE)


def witnesses(q,a,entry,policy,profile,startup,whole,*,code):
    entry.witnesses(q,a,policy,connection_attempt=10)
    for path in (SELF,TEST):q.pin(path)
    for pin in (STARTUP,WHOLE):a.exact(q.pin(pin["path"]),pin,"CURRENT_COMPLETED_CODE_AND_EOF_ADAPTERS")
    whole.witnesses(q,a,profile,startup,adapter_code=True)
    record=q.json(PREFIX+"xz-whole-code-qualification005.v1.json")
    a.fields(record,dict(state=whole.PASS,cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False,
        product_or_Native_executed=False,runtime_default_import_count=62),"ACTUAL_CURRENT_CODE74_CLOSURE")
    original=a.read_exact(q,record["original_CODE_pin"]);whole.validate(original,a)
    a.exact(record["original_CODE_pin"]["path"],ACTUAL_CODE,"REAL_CODE005_NOT_RENAMED_COPY")
    for pin in record["source_pins"]:
        if pin["path"].startswith("tools/p09/") and pin["path"].endswith(".py"):a.exact(q.pin(pin["path"]),pin,"UNCHANGED_CURRENT_CODE74_PROGRAMS")
    if code:
        own=q.json(CODE)
        a.fields(own,dict(state=CODE_STATE,contracts=dict(run=12,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
            product_or_Native_executed=False,accepted_count_delta=0,GO_authorized=False),"CURRENT_RECOVERY_ADAPTER_CODE10")
        require(type(own["fresh_inputs"]) is int and own["fresh_inputs"]==own["final_fresh_hashes"]>0,"ADAPTER_SOURCE_CLOSURE")
        for pin in own["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_RECOVERY_ADAPTER_PROGRAMS")


def main():
    import argparse,io,time,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import flat_current_queue_envelope_runtime_v25 as envelope
    import xz_corpus_delivery_v1 as delivery
    parser=argparse.ArgumentParser();modes=parser.add_mutually_exclusive_group(required=True)
    for mode in ("code","preflight","qualify"):modes.add_argument("--"+mode,action="store_true")
    parser.add_argument("--attempt",type=int,required=True);parser.add_argument("--preflight-attempt",type=int)
    args=parser.parse_args();stage="preflight" if args.preflight else "qualify"
    if args.code:
        require(type(args.attempt) is int and 1<=args.attempt<=8 and args.preflight_attempt is None,"FINITE_ADAPTER_CODE")
        output=PREFIX+f"xz-recovery-preparation-code{args.attempt:03}.v1.json";forward=None
    else:
        forward=context(stage,args.attempt,args.preflight_attempt);output=PREFIX+f"xz-recovery-{stage}-audit{args.attempt:03}.v1.json"
        target=PREFIX+(f"successor-recovery-preflight-run008-attempt{args.attempt:03}.v1.json" if args.preflight else f"successor-recovery-dispatch-qualification-run008-attempt{args.attempt:03}.v1.json")
        require(not(c.ROOT/target).exists(),"EXCLUSIVE_ORIGINAL_PREPARATION_RESULT")
    require(not(c.ROOT/output).exists(),"EXCLUSIVE_RECOVERY_ADAPTER_RESULT")
    def dynamic(path):
        data=(c.ROOT/path).read_bytes();return dict(path=path,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    entries,_=envelope.namespace_bundle.load(c.ROOT,[dynamic("tools/p09/preparation_attributed_entry_v1.py")],{})
    entry=entries.preparation_attributed_entry_v1
    raw,_=envelope.namespace_bundle.load(c.ROOT,[entry.ENTRY,entry.POLICY_SOURCE]+entry.UTIL_PINS+[delivery.BASELINE,STARTUP,WHOLE],{})
    closure=raw.prepared_run_closure_v1;closure.configure_host_policy(c);original_policy=raw.preparation_attributed_cpu_v1
    startup=raw.xz_startup_adapter_v1;whole=raw.xz_whole_code_adapter_v1
    profile_ns,_=envelope.namespace_bundle.load(c.ROOT,[startup.PROFILE],{});profile=profile_ns.xz_closed_preparation_v1
    baseline=raw.owned_cpu_baseline_v1
    def attributed(original,*,role):return baseline.guard_type(original_policy.guard_type(original,role=role))
    policy=NS(**{**vars(original_policy),"guard_type":attributed})
    metrics={};phase=dict(value="bootstrap_policy")
    old=delivery.observed_guard(raw.terminal_metadata_pressure_v1.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard)),metrics,phase)
    def prep():
        phase["value"]="bootstrap_connection"
        return delivery.observed_guard(policy.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard),role="whole_metadata_preflight"),metrics,phase)()
    guards=[];instances=[];started=time.monotonic()
    row=dict(state="FAILED_XZ_RECOVERY_PREPARATION_NOT_ADOPTED",actual_stage_invoked=False,accepted_count_delta=0,
        GO_authorized=False,product_or_Native_executed=False,actual_CODE_reference=ACTUAL_CODE,Native_policy_changed=False)
    try:
        def verify_policy(q):
            entry.policy_witnesses(q,a,policy);a.exact(q.pin(delivery.BASELINE["path"]),delivery.BASELINE,"MEASURED_BASELINE")
        def verify(q):
            witnesses(q,a,entry,policy,profile,startup,whole,code=not args.code)
            if args.code:
                from tests import test_xz_recovery_preparation_v1 as tests
                tests.MODULE=sys.modules[__name__];tests.ROOT=c.ROOT;tests.ENVELOPE=envelope;tests.ACCEPTANCE=a
                tests.DELIVERY=delivery;tests.ENTRY=entry;tests.CLOSURE=closure;tests.PROFILE=profile;tests.POLICY=policy
                result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
                row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
                row["contract_errors"]=[dict(test=t.id().rsplit(".",1)[-1],exception_type=trace.splitlines()[-1].split(":",1)[0]) for t,trace in result.errors+result.failures]
                a.exact(row["contracts"],dict(run=12,errors=0,failures=0,skipped=0),"ALL_CURRENT_CODE_REFERENCE_ADAPTER12")
        q,proof=entry.closed_bootstrap(c.ROOT,a,old,prep,verify_policy,verify,guards)
        row["bootstrap_policy_validation"]=proof
        if args.code:row.update(state=CODE_STATE,source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
        else:
            require(all(g.cleanup for g in guards),"ALL_BOOTSTRAP_OWNERS_CLOSED")
            root=c.ROOT/(PREFIX+"current-runtime-run008.v1.json");require(not root.exists(),"NO_NATIVE_BEFORE_PREPARATION")
            linked=build(c.ROOT,envelope,a,delivery,entry,closure,profile,policy,"whole_metadata_preflight" if args.preflight else "dispatch_construction",instances,
                witness=lambda q:witnesses(q,a,entry,policy,profile,startup,whole,code=True))
            row["actual_stage_invoked"]=True
            api=NS(main=linked.main);exit_code=entry.execute(api,linked.envelope,forward)
            require(not root.exists() and instances and all(g.cleanup for g in instances),"ALL_STAGE_GUARDS_CLOSED_AND_NO_NATIVE")
            row.update(state="RECORDED_CURRENT_XZ_RECOVERY_PREPARATION_NOT_NATIVE_OR_ACCEPTANCE",stage=stage,original_stage_exit_code=exit_code,
                guard_summaries=[g.preparation_CPU.summary() for g in instances],dispatch_window_observations=linked.dispatch_window_observations,
                actual_stage_record_pin=dynamic(target) if(c.ROOT/target).is_file() else None)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        samples=[s for g in guards+instances for s in g.samples]
        row.update(cleanup_confirmed=all(g.cleanup for g in guards+instances),elapsed_seconds=time.monotonic()-started,
            original_fresh_sample_resource_summary=metrics,CPU_max=max((s["system_cpu_percent"] for s in samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in samples),default=None))
    require(row["cleanup_confirmed"],"ALL_RECOVERY_PREPARATION_GUARDS_CLOSED");raw.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","contract_errors","actual_stage_invoked","original_stage_exit_code",
        "fresh_inputs","final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed","elapsed_seconds","error_code")}))
    return 0 if row["state"]==CODE_STATE or row.get("original_stage_exit_code")==0 else 1


if __name__=="__main__":raise SystemExit(main())
