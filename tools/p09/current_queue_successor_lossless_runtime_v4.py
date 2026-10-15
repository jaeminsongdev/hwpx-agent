"""Actual lossless metadata connection plus independent new-accounting checks.

All frozen v3/v2/original engine and whole checker bodies remain. New helpers
are explicit private source dependencies, never hidden sys.modules imports.
"""
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import ast
import copy
import math
import sys

SELF="tools/p09/current_queue_successor_lossless_runtime_v4.py"
TEST="tools/p09/tests/test_current_queue_successor_lossless_runtime_v4.py"
PINS=[
 dict(path="tools/p09/current_queue_successor_retry_runtime_v3.py",bytes=11451,sha256="c8f2c06f224890581177d8e3d8e55ab3111463ac5b11d505f6c47171d61ce348"),
 dict(path="tools/p09/lossless_metadata_connection_v1.py",bytes=15742,sha256="6a29bb5b9a7eea25edab896b8fa32bd5425a7c567a3ee51a8428a2fb813f2524"),
 dict(path="tools/p09/fresh_lossless_metadata_reader_v1.py",bytes=9403,sha256="aa312b81bb93f1eb800e281b4273abfd06894ea4f5d1f39b0b183295efc39208"),
 dict(path="tools/p09/shared_metadata_frame_decoder_budget_v1.py",bytes=7823,sha256="fb9440e5c89ad684fda6d076a57a940fb2f44114c26d88051d272a4a60a609f6")]
ORACLE=dict(path="tools/p09/current_queue_successor_oracle.py",bytes=10143,
 sha256="5656ef67c1c8521fdce9a95d96c74de84df70e45ff369aef4524059fc7e5cf9a")


def require(ok,label):
    if not ok:raise ValueError("LOSSLESS_V4_"+label)


def validate_accounting(row,binding,a):
    """Expected mapping is independently declared, not copied from the row."""
    explicit=row["bootstrap_metadata"]["early_pressure"]["explicit_fresh_lossless_metadata"]
    counts=explicit["semantic_read_counts"];descriptors=binding.descriptors()
    expected={d["semantic_original_pin"]["path"]:d for d in descriptors}
    require(type(counts) is dict and set(counts)==set(expected),"ALL_DECLARED_METADATA_MAPPINGS")
    require(all(type(n) is int and n>=1 for n in counts.values()),"REAL_METADATA_COUNTS")
    total=sum(counts.values());physical=sum(expected[n]["physical_envelope_pin"]["bytes"]*v for n,v in counts.items())
    semantic=sum(expected[n]["semantic_original_pin"]["bytes"]*v for n,v in counts.items())
    a.fields(explicit,dict(mapping_count=len(expected),mapped_read_attempts=total,mapped_read_completed=total,
        mapped_physical_bytes_read=physical,mapped_semantic_bytes_restored=semantic,
        decoded_bytes_not_added_to_physical_counter=True,byte_hash_or_JSON_cache=False,
        fresh_physical_read_and_decode_per_request=True,original_unmapped_reader_retained=True),"V4_REAL_METADATA_ACCOUNTING")
    decoder=explicit["decoder"]
    a.fields(decoder,dict(limit_seconds=5.0,attempted=total,completed=total,active=False,error_seen=False),"V4_ORIGINAL_METADATA_BUDGET")
    shared=row["source_frame"]["shared_metadata_frame_decoder"]
    frame=row["source_frame"]["aggregate_envelope_decoder"]
    a.fields(shared,dict(shared_limit_seconds=5.0,metadata_registered=True,Frame_registered=True,
        metadata_completed=total,Frame_completed=2*len(expected),terminal_error_seen=False,
        original_budget_classes_run_methods_and_counters_retained=True,original_resource_and_owner_checks_first=True,
        Frame_evidence_not_relabelled_as_combined=True,new_sampler_thread_or_process=False),"V4_SHARED_REAL_FRAME_BUDGET")
    a.exact(shared["metadata_decoder_work_seconds"],decoder["elapsed_work_seconds"],"V4_SAME_METADATA_WORK")
    a.exact(shared["Frame_decoder_work_seconds"],frame["elapsed_decoder_work_seconds"],"V4_SAME_FRAME_ONLY_WORK")
    meta,work=shared["metadata_decoder_work_seconds"],shared["Frame_decoder_work_seconds"]
    require(all(type(x) is float and math.isfinite(x) and x>=0 for x in (meta,work)),"FINITE_REAL_WORK")
    a.exact(shared["total_decoder_work_seconds"],meta+work,"V4_REAL_COMBINED_WORK")
    require(meta+work<=5.0 and type(shared["checks"]) is int and shared["checks"]>0,"SHARED_FIVE_SECOND_BOUND")
    require(row["bootstrap_metadata"]["bytes_read"]>=physical,"PHYSICAL_METADATA_TOTAL")
    return True


def override_import(namespace,name,value):
    """Preserve each original private import map and original function code."""
    for key,fn in tuple(vars(namespace).items()):
        if type(fn) is not FunctionType or not fn.__globals__.get("__name__","").startswith("p09_exact_"):continue
        previous=fn.__builtins__["__import__"]
        def declared(target,globals=None,locals=None,fromlist=(),level=0,prior=previous):
            if level==0 and target==name:return value
            return prior(target,globals,locals,fromlist,level)
        env=fn.__globals__;env["__builtins__"]={**fn.__builtins__,"__import__":declared}
        changed=FunctionType(fn.__code__,env,argdefs=fn.__defaults__,closure=fn.__closure__)
        changed.__kwdefaults__=fn.__kwdefaults__
        if env.get(key) is fn:env[key]=changed
        setattr(namespace,key,changed)
        require(changed.__code__ is fn.__code__ and changed.__closure__ is fn.__closure__,"WHOLE_PRIVATE_FUNCTION_RETAINED")


def oracle_namespace(root,envelope,metadata,a):
    names,proof=envelope.namespace_bundle.load(root,[ORACLE],{"current_queue_successor_connections":metadata})
    oracle=names.current_queue_successor_oracle;original=oracle.connect
    def connect(*args,**kwargs):
        checker,proof=original(*args,**kwargs);binding=checker.graph.binding
        whole=checker.validate_candidate;parameters=whole.__code__.co_varnames[:whole.__code__.co_argcount]
        require("row" in parameters,"ORIGINAL_WHOLE_CHECKER_ROW_INTERFACE");index=parameters.index("row")
        def checked(*items,**options):
            result=whole(*items,**options)
            row=items[index] if len(items)>index else options["row"]
            validate_accounting(row,binding,a)
            return result
        checker.environment["validate_candidate"]=checked;checker.validate_candidate=checked
        return checker,proof
    original.__globals__["connect"]=connect;oracle.connect=connect
    return oracle


def graph_v4_namespace(root,bridge,retry):
    """Only receipt/capsule/bootstrap suffix metadata; exact AST inverse."""
    raw=(root/retry.BRIDGE["path"]).read_bytes()
    require(len(raw)==retry.BRIDGE["bytes"] and hashlib_sha(raw)==retry.BRIDGE["sha256"],"EXACT_GRAPH_PROJECTOR_SOURCE")
    node=next(n for n in ast.parse(raw.decode("utf-8")).body if isinstance(n,ast.FunctionDef) and n.name=="graph_v2_paths")
    changed=copy.deepcopy(node);count=0
    for value in ast.walk(changed):
        if isinstance(value,ast.Constant) and value.value==".v2.json":value.value=".v4.json";count+=1
    require(count==1,"ONE_GRAPH_NAMESPACE_SUFFIX")
    inverse=copy.deepcopy(changed)
    for value in ast.walk(inverse):
        if isinstance(value,ast.Constant) and value.value==".v4.json":value.value=".v2.json"
    require(ast.dump(inverse,include_attributes=False)==ast.dump(node,include_attributes=False),"WHOLE_GRAPH_PROJECTOR_INVERSE")
    env=bridge.graph_v2_paths.__globals__
    exec(compile(ast.fix_missing_locations(ast.Module(body=[changed],type_ignores=[])),retry.BRIDGE["path"],"exec"),env)
    bridge.graph_v2_paths=env["graph_v2_paths"]


def hashlib_sha(raw):
    import hashlib
    return hashlib.sha256(raw).hexdigest()


def configure(runtime,components):
    original=runtime.compose_parent;connection=components.lossless_metadata_connection_v1
    fresh=components.fresh_lossless_metadata_reader_v1;budget_module=components.shared_metadata_frame_decoder_budget_v1
    def compose_parent(template,graph,binding_callback,checkpoint):
        shared=budget_module.SharedBudget();frame_factory=graph.frames.frame_type
        graph.frames.frame_type=lambda base,binding:budget_module.frame_type(base,binding,frame_factory,shared)
        def template_with_metadata():
            engine,proof=template()
            state=connection.connect_engine(engine,graph.binding,fresh,graph.frames.connection.original.DecoderBudget,checkpoint,shared)
            return engine,dict(proof,lossless_metadata_private_connection=True)
        def complete(reader):
            required,rust=binding_callback(reader)
            for descriptor in graph.binding.descriptors():
                pin=descriptor["semantic_original_pin"]
                graph.binding.__class__.project.__globals__["exact"](reader.pin(pin["path"]),pin,"V4_ALL_REAL_METADATA_SEMANTIC_PINS")
            return required,rust
        return original(template_with_metadata,graph,complete,checkpoint)
    original.__globals__["compose_parent"]=compose_parent;runtime.compose_parent=compose_parent
    return runtime


def load(root,a,scope,bytes_policy,envelope,components,qualification_path,*,worker=False):
    retry=components.current_queue_successor_retry_runtime_v3
    bridge_ns,proof=envelope.namespace_bundle.load(root,[retry.BRIDGE],{})
    bridge=bridge_ns.current_queue_successor_wire_runtime_v2
    for fn in vars(retry).values():
        if type(fn) is FunctionType and fn.__globals__.get("__name__","").startswith("p09_exact_"):fn.__globals__.update(SELF=SELF,TEST=TEST)
    retry.bind_metadata(bridge)
    graph_v4_namespace(root,bridge,retry)
    class WitnessReader(a.AcceptanceReader):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            for name in (SELF,TEST):self.pin(name)
            for pin in PINS+[ORACLE]:a.exact(self.pin(pin["path"]),pin,"V4_ALL_FROZEN_COMPONENTS")
            if qualification_path:
                receipt=self.json(qualification_path)
                a.fields(receipt,dict(state="PASS_LOSSLESS_V4_ADOPTION_CODE_NOT_NATIVE_OR_PRODUCT",
                    contracts=dict(run=6,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"V4_REQUIRED_ADOPTION_CODE")
                for pin in receipt["source_pins"]:a.exact(self.pin(pin["path"]),pin,"V4_ALL_CURRENT_ADOPTION_PINS")
    api=NS(**{**vars(a),"AcceptanceReader":WitnessReader})
    modules,proof=retry.load(root,api,scope,bytes_policy,envelope,bridge,
        None if worker else f"implementation/p09/evidence/p09-361-case{qualification_path.split('case')[1][:3]}-retry-code002.v1.json",worker=worker)
    runtime=configure(modules.current_queue_successor_runtime,components)
    oracle=oracle_namespace(root,envelope,runtime.metadata,a)
    override_import(modules.current_queue_successor_dispatch,"current_queue_successor_oracle",oracle)
    override_import(modules.current_queue_successor_controller,"current_queue_successor_oracle",oracle)
    dispatch=modules.current_queue_successor_dispatch;old=dispatch.current_namespaces
    def current_namespaces(q,*args,**kwargs):
        linked,controller,proof=old(q,*args,**kwargs);configure(linked,components)
        override_import(controller,"current_queue_successor_oracle",oracle_namespace(root,envelope,linked.metadata,a))
        for pin in PINS+[ORACLE]:a.exact(q.pin(pin["path"]),pin,"V4_DYNAMIC_NAMESPACE_SOURCE_PINS")
        for name in (SELF,TEST):q.pin(name)
        return linked,controller,proof
    for fn in vars(dispatch).values():
        if type(fn) is FunctionType and fn.__globals__.get("__name__","").startswith("p09_exact_current_queue_successor_dispatch"):
            fn.__globals__["current_namespaces"]=current_namespaces
    dispatch.current_namespaces=current_namespaces
    return modules,bridge,oracle


def qualify_code(root,a,envelope,components,output):
    import io,json,os,time,unittest
    retry=components.current_queue_successor_retry_runtime_v3
    bridge_ns,proof=envelope.namespace_bundle.load(root,[retry.BRIDGE],{})
    bridge=bridge_ns.current_queue_successor_wire_runtime_v2
    old_ns,proof=envelope.namespace_bundle.load(root,[bridge.OLD_CONTROLLER],{"flat_current_queue_envelope_runtime_v25":envelope})
    guards=old_ns.case160_run007_controller.base.FIRST
    guard=guards.terminal_metadata_pressure_v1.guard_type(guards.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    require(not (root/output).exists(),"EXCLUSIVE_ADOPTION_CODE");started=time.monotonic();q=None
    row=dict(state="FAILED_LOSSLESS_V4_ADOPTION_CODE_NOT_ADOPTED",accepted_count_delta=0,product_or_Native_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(root,guard.check);q.pin(SELF);test=q.pin(TEST)
        for pin in PINS+[ORACLE]:a.exact(q.pin(pin["path"]),pin,"EXACT_V4_COMPONENTS")
        tests,proof=envelope.namespace_bundle.load(root,[test],{"current_queue_successor_lossless_runtime_v4":NS(validate_accounting=validate_accounting,override_import=override_import)})
        module=tests.test_current_queue_successor_lossless_runtime_v4;module.Tests.setUp.__globals__["CHECKPOINT"]=guard.check
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(module))
        contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row["contracts"]=contracts;require(contracts==dict(run=6,errors=0,failures=0,skipped=0),"ALL_ADOPTION6")
        for name in ("lossless-metadata-connection-run004-attempt003","shared-metadata-frame-decoder-code003"):
            index=output.split("case")[1][:3]
            receipt=q.json(f"implementation/p09/evidence/p09-361-case{index}-{name}.v1.json")
            require(receipt["state"].startswith("PASS_") and receipt["cleanup_confirmed"] is True,"LIVE_COMPONENT_QUALIFICATION")
            for pin in receipt["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_COMPONENT_QUALIFICATIONS")
        q.finish();guard.check(force=True)
        row.update(state="PASS_LOSSLESS_V4_ADOPTION_CODE_NOT_NATIVE_OR_PRODUCT",source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        import re
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"ADOPTION_CODE_CLEANUP")
    raw=(json.dumps(row,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8");require(0<len(raw)<=262144,"BOUNDED_ADOPTION_CODE")
    path=root/output
    for parent in (path.parent,*path.parent.parents):require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_ADOPTION_PARENT")
    with path.open("xb") as stream:require(stream.write(raw)==len(raw),"COMPLETE_ADOPTION_CODE");stream.flush();os.fsync(stream.fileno())
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
    components,proof=envelope.namespace_bundle.load(c.ROOT,PINS,{})
    worker=len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]
    if worker:
        modules,bridge,oracle=load(c.ROOT,a,scope,bytes_policy,envelope,components,None,worker=True)
        return modules.current_queue_successor_runtime.owned_worker_entry(sys.argv[3])
    parser=argparse.ArgumentParser()
    for name in ("case","run","attempt"):parser.add_argument("--"+name,type=int,required=True)
    for name in ("code-attempt","preflight-attempt","qualification-attempt","adoption-attempt","review-attempt","acceptance-attempt"):parser.add_argument("--"+name,type=int,default=1)
    parser.add_argument("--root-bytes",type=int);parser.add_argument("--root-sha256")
    mode=parser.add_mutually_exclusive_group(required=True)
    for name in ("adoption-code","graph","bootstrap","code","preflight","qualify","native","review","accept"):mode.add_argument("--"+name,action="store_true")
    args=parser.parse_args();require(164<=args.case<=249 and 2<=args.run<=8,"CLOSED_V4_CONTEXT")
    qualification=f"implementation/p09/evidence/p09-361-case{args.case}-lossless-v4-adoption-code{args.adoption_attempt:03}.v1.json"
    if args.adoption_code:return qualify_code(c.ROOT,a,envelope,components,qualification)
    modules,bridge,oracle=load(c.ROOT,a,scope,bytes_policy,envelope,components,qualification)
    runtime=modules.current_queue_successor_runtime;controller=modules.current_queue_successor_controller;dispatch=modules.current_queue_successor_dispatch
    if args.graph:return modules.current_queue_successor_connections.prepare(args.case,1,args.run,0)
    if args.bootstrap:return runtime.qualify_factory(args.case,args.run,args.run,args.attempt,True)
    if args.code:return controller.run_code(args.case,args.run,args.attempt)
    if args.preflight:return controller.run_preflight(args.case,args.run,args.code_attempt,args.attempt)
    ctx=dispatch.context(args.case,args.run,args.code_attempt,args.preflight_attempt,args.qualification_attempt)
    if args.qualify or args.native:return dispatch.main(ctx,args.qualify)
    retry=components.current_queue_successor_retry_runtime_v3
    names,proof=envelope.namespace_bundle.load(c.ROOT,[retry.REVIEW],{})
    adapter=names.current_queue_successor_wire_review_v2
    facade=NS(**{**vars(bridge),"load":lambda root,aa,ss,bb,ee:(load(root,aa,ss,bb,ee,components,qualification)[0],{})})
    reviewer,acceptor,proof=adapter.load(c.ROOT,a,scope,bytes_policy,envelope,facade)
    override_import(reviewer,"current_queue_successor_oracle",oracle);override_import(acceptor,"current_queue_successor_oracle",oracle)
    root_pin=dict(path=ctx.root,bytes=args.root_bytes,sha256=args.root_sha256)
    if args.review:return reviewer.main(ctx,root_pin,args.review_attempt)
    return acceptor.main(ctx,root_pin,args.review_attempt,args.acceptance_attempt)


if __name__=="__main__":raise SystemExit(main())
