"""Preparation-only run009 capsule and complete original reconstruction.

No Native launcher, product worker or GO. Three private run upper-bound slots
are extended8->9 with exact code inverses; outer APIs accept only165/run009.
The unchanged68 constructor and original69 scope/byte oracles remain required.
"""
import copy
import hashlib
import json
from types import FunctionType,SimpleNamespace as NS

SELF="tools/p09/native009_worker_transport_v1.py"
TEST="tools/p09/tests/test_native009_worker_transport_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
FIELD="native008_failed_capture_declaration"
PINS=[
dict(path="tools/p09/current_queue_successor_runtime.py",bytes=27293,sha256="523fbe57dc31f73612651cf44dbca9a85fe706a40e563f391ccade2aa0cf63df"),
dict(path="tools/p09/current_queue_successor_connections.py",bytes=19229,sha256="363d9665885eedc096a7c970098cd80568197e13930e13bc10347e044a687fa9"),
dict(path="tools/p09/current_queue_successor_binding.py",bytes=15040,sha256="6d48c8df7a085461bdad22f8ee4be2baa9675f8035b558f7bc3474b52ea6e915"),
dict(path="tools/p09/closed_prebody_worker_connection_v1.py",bytes=16441,sha256="d9c69c7373fc2f475048b1d8a8466f2b8c013e086856da0bed73a9e8c80b265b"),
dict(path="tools/p09/closed_prebody_source_alias_v1.py",bytes=20052,sha256="153f31453a9a87433d3f0b2bdabc6ceb1151e8c14e29fc7e7faea1fe9f5ae0c9"),
dict(path="tools/p09/prior_preparation_alias_v1.py",bytes=7565,sha256="106535e83f4c3af0e6cd928185556118a12411906933fa3f2f2415dc0ec10492"),
dict(path="tools/p09/xz_ordinary_binding_v1.py",bytes=14211,sha256="1ed4280073c804753de316887b7091ef507146dadb5bcb539b0c223b65bfae20"),
dict(path="tools/p09/native008_failure_binding_v1.py",bytes=14859,sha256="6bb8f17b68f549a3885e121da9d48692d17b5c8818ed3aa45315b5b4250b7b6b")]


def require(ok,label):
    if not ok:raise ValueError("NATIVE009_TRANSPORT_"+label)


def run9(original):
    paths={"worker_api":"current_queue_successor_connections.py",
        "validate_worker_hint":"current_queue_successor_runtime.py",
        "declaration":"closed_prebody_worker_connection_v1.py"}
    require(type(original) is FunctionType and original.__name__ in paths
        and original.__code__.co_filename.replace("\\","/").endswith(paths[original.__name__]),"EXACT_RUN_LIMIT_FUNCTION")
    before=original.__code__;slots=[i for i,v in enumerate(before.co_consts) if type(v) is int and v==8]
    require(len(slots)==1,"ONE_TYPED_RUN_UPPER_BOUND_SLOT")
    values=list(before.co_consts);values[slots[0]]=9;changed=before.replace(co_consts=tuple(values))
    undo=list(changed.co_consts);undo[slots[0]]=8
    require(changed.replace(co_consts=tuple(undo))==before,"ENTIRE_RUN_BOUND_CODE_INVERSE")
    revised=FunctionType(changed,original.__globals__,argdefs=original.__defaults__,closure=original.__closure__)
    revised.__kwdefaults__=original.__kwdefaults__
    return revised,dict(function=original.__name__,constant_slot=slots[0],old=8,new=9,entire_code_inverse=True)


def publish_function(module,name,fn):
    old=getattr(module,name);old.__globals__[name]=fn;setattr(module,name,fn)


def connect(root,loader,scope,bytes_policy,xz,bounded,checkpoint,exact):
    names,proof=loader.load(root,PINS,{})
    runtime=names.current_queue_successor_runtime;metadata=names.current_queue_successor_connections
    transport=names.closed_prebody_worker_connection_v1;alias=names.closed_prebody_source_alias_v1
    bindings=names.current_queue_successor_binding;core=names.xz_ordinary_binding_v1
    failed=names.native008_failure_binding_v1;prior_alias=names.prior_preparation_alias_v1
    limits=[]
    for module,name in ((metadata,"worker_api"),(runtime,"validate_worker_hint"),(transport,"declaration")):
        fn,item=run9(getattr(module,name));publish_function(module,name,fn);limits.append(item)
    revised=metadata.worker_api;check=require
    def only9(original,compact,binding_module,step,run):
        check(type(run) is int and run==9 and type(step) is dict and step.get("index")==165
            and type(step.get("index")) is int and step.get("before")==158,"ONLY165_RUN009_GRAPH")
        return revised(original,compact,binding_module,step,run)
    only9=FunctionType(only9.__code__,revised.__globals__,argdefs=only9.__defaults__,closure=only9.__closure__)
    publish_function(metadata,"worker_api",only9);bounded.install(metadata,checkpoint)
    def factory(hint,prior_rows):
        module,_=bindings.connect(root,loader,scope,165,hint["historical_provenance"],hint["historical_pairs"])
        transport.install_declaration(module,hint[transport.FIELD],165,9,alias,scope)
        core.install(module,hint["historical_pairs"],xz)
        prior_alias.install(module,hint["historical_pairs"],165)
        failed.install(module,prior_rows,hint[FIELD],xz,physical_run=9)
        return module
    def validate(hint):
        require(type(hint) is dict and FIELD in hint and transport.FIELD in hint,"TWO_EXPLICIT_DISTINCT_DECLARATIONS")
        exact(hint[FIELD],failed.ROLE,"EXACT_FAILED_CAPTURE_ROLE_NOT_PREBODY")
        base={k:v for k,v in hint.items() if k not in (FIELD,transport.FIELD)}
        index,run=runtime.validate_worker_hint(base,"case165-current-r009-tests")
        require(index==165 and run==9,"EXACT_NEW_CONTEXT_NOT_REPLAY8")
        transport.declaration(hint[transport.FIELD],165,9,alias,scope,NS(
            SCHEMA="hwpx-agent.p09-lossless-runtime-source-projection/v1",codec=NS(MAX_BYTES=16*1048576)))
        return base
    def reconstruct(hint,wire,checkpoint):
        checkpoint();base=validate(hint)
        require(type(wire) is bytes and 0<len(wire)<=16384,"UNCHANGED_WIRE16K")
        expected={k:hint["capsule_pin"][k] for k in ("bytes","sha256")}
        exact(expected,dict(bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest()),"EXACT_NEW_TRANSPORT_HASH")
        # Bounded parse is metadata for descriptor admission, not a substitute
        # for original decode: the full unchanged decoder parses again below.
        compact=bounded.decode_compact(wire.decode("ascii"),checkpoint)
        require(type(compact) is dict and type(compact.get("bindings")) is list and len(compact["bindings"])==69,"FULL69_BOUNDED_METADATA")
        pin_unpack=lambda values:dict(zip(("path","bytes","sha256"),values))
        common=compact["descriptor_context"]
        rows=[dict(schema_version=common[0],next_case=common[1],semantic_original_pin=pin_unpack(v[0]),physical_envelope_pin=pin_unpack(v[1])) for v in compact["bindings"]]
        require(failed.fingerprint(rows[:68])==failed.TABLE,"FIXED_PRIOR68_BEFORE_ORIGINAL_DECODER")
        built=[];seeds=[]
        from contextlib import ExitStack
        with ExitStack() as stack:
            def connected(*args,**kwargs):
                require(not built,"ONE_ORIGINAL_RECONSTRUCTION_FACTORY")
                module=factory(hint,rows[:68]);built.append(module)
                seeds.append(stack.enter_context(core.bootstrap_seed(module,hint["first_descriptor"],hint["manifest_pin"])))
                return module,dict(worker_declarations_only=True,parent_admission_still_required=True)
            facade=NS(**{**vars(bindings),"connect":connected})
            original=runtime.reconstruct_worker_graph;builtins=dict(original.__builtins__);prior=builtins["__import__"]
            def declared(name,globals=None,locals=None,fromlist=(),level=0):
                if name=="current_queue_successor_binding" and level==0:return facade
                return prior(name,globals,locals,fromlist,level)
            builtins["__import__"]=declared
            fn=FunctionType(original.__code__,dict(original.__globals__,__builtins__=builtins),argdefs=original.__defaults__,closure=original.__closure__)
            fn.__kwdefaults__=original.__kwdefaults__
            graph,details=fn(root,loader,scope,bytes_policy,base,wire,checkpoint)
            require(len(built)==1 and len(graph.binding.descriptors())==69,"ORIGINAL_FULL69_RECONSTRUCTION")
            exact(graph.binding.descriptors(),rows,"COMPLETE_TRANSPORT_NOT_PREPARSED_SUBSTITUTION")
            require(fn.__code__ is original.__code__ and fn.__defaults__ is original.__defaults__
                and fn.__closure__ is original.__closure__,"WHOLE_ORIGINAL_RECONSTRUCTION_BODY")
        return graph,dict(details,whole_original_reconstruction_code_retained=True,exact_failed_role_declaration_only=True,
            parent_fresh_source_Frame_and_independent_oracle_still_required=True,Native009_or_GO_qualified=False)
    return NS(runtime=runtime,metadata=metadata,factory=factory,validate=validate,reconstruct=reconstruct,
        source_proofs=proof,run_limit_proofs=limits,original_default_modules_mutated=False)


def main():
    import argparse,importlib.util,io,os,re,time,unittest
    import sys
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    import prepared_run_closure_v1 as host
    host.configure_host_policy(c);c.Windows()
    import accept_case112_current_epoch as a
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import owned_cpu_baseline_v1 as baseline
    import flat_current_queue_envelope_runtime_v25 as envelope
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import xz_unified_runtime_v1 as unified
    import xz_unified_preparation_binding_v1 as binder
    import receipt_xz_envelope_v1 as xz
    import bounded_successor_capsule_wire_v2 as bounded
    import ast_clone_namespace_v1 as cloner
    import ast_copy_namespace_connection_v1 as optimization
    import native008_failure_binding_v1 as failed
    import prepare_native008_carrier_v1 as producer
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument("--attempt",type=int,required=True)
    attempt=producer.identifier(parser.parse_args().attempt)
    output=PREFIX+f"native009-worker-transport-code{attempt:03}.v1.json"
    manifest_name=PREFIX+"successor-native009-failure69-manifest001.v1.json"
    capsule_name=PREFIX+"successor-worker-capsule009.compact.v1.json"
    hint_name=PREFIX+"successor-worker-bootstrap009.v1.json"
    a.require(not(c.ROOT/output).exists(),"EXCLUSIVE_NEW_TRANSPORT_REPORT")
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))();started=time.monotonic();q=None;old=None
    row=dict(state="FAILED_NATIVE009_WORKER_TRANSPORT_NOT_ADOPTED",accepted_count_delta=0,
        actual_product_Native_or_worker_process_executed=False,GO_authorized=False,
        whole_current_source_Frame_or_Native009_qualified=False,files_created=[],files_reused=[])
    def publish_bytes(name,data,limit):
        a.require(name in (manifest_name,capsule_name,hint_name) and type(data) is bytes and 0<len(data)<=limit,"SCOPED_BOUNDED_NEW_METADATA")
        path=c.ROOT/name
        for parent in (path.parent,*path.parent.parents):
            a.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_METADATA_ANCESTORS")
            if parent==c.ROOT:break
        expected=dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        if path.exists():
            a.exact(q.fresh_pin(name),expected,"ONLY_IDENTICAL_PREPARATION_BYTES_REUSED_NOT_OLD_VERDICT")
            row["files_reused"].append(expected);return expected
        pacer=bytes_policy.OwnedPacer();pacer.select(name)
        with path.open("xb") as stream:
            for offset in range(0,len(data),65536):
                guard.check();block=data[offset:offset+65536];pacer.reserve(guard.check)
                a.exact(stream.write(block),len(block),"COMPLETE_NEW_METADATA_WRITE");pacer.refund(len(block))
            stream.flush();os.fsync(stream.fileno())
        pin=dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest());row["files_created"].append(pin)
        a.exact(q.pin(name),pin,"ACTUAL_NEW_METADATA_PIN");return pin
    def encoded(value):return (json.dumps(value,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("ascii")
    try:
        guard.acquire();guard.check(force=True);q=a.AcceptanceReader(c.ROOT,guard.check)
        q.pin(SELF);q.pin(TEST)
        for pin in PINS:a.exact(q.pin(pin["path"]),pin,"EXACT_UNMODIFIED_TRANSPORT_DEPENDENCY")
        loader,proof=optimization.connect(envelope.namespace_bundle,cloner);proxy=optimization.envelope(envelope,loader)
        old=failed.existing(c,a,proxy,unified,binder,scope,bytes_policy,guard)
        admitted=failed.admission(q,a,producer)
        base=a.read_exact(q,binder.GRAPH)
        old_hint=q.json(PREFIX+"successor-worker-bootstrap008.v18.json")
        step=base["step"];authority=a.read_exact(q,step["prior_queue_pin"])
        a.fields(authority,dict(accepted_count_after=158,next_runtime_index=165,runtime_candidate_pin=step["prior_candidate_pin"]),"ACTUAL_UNADVANCED_AUTHORITY")
        api=connect(c.ROOT,loader,scope,bytes_policy,xz,bounded,guard.check,a.exact)
        rows=copy.deepcopy(old.rows)+[dict(schema_version="hwpx-agent.p09-lossless-runtime-source-projection/v1",next_case=165,
            semantic_original_pin=dict(failed.ORIGINAL),physical_envelope_pin=dict(failed.PHYSICAL))]
        manifest=dict(schema_version="hwpx-agent.p09-native009-preparation-manifest/v1",index=165,before=158,physical_run=9,
            descriptors=rows,source_step=step,existing68_graph_pin=binder.GRAPH,
            failed_capture_role=admitted,current_whole_Native_source_scope_qualified=False)
        manifest_pin=publish_bytes(manifest_name,encoded(manifest),262144)
        hint={k:copy.deepcopy(v) for k,v in old_hint.items() if k not in ("run","capsule_pin","manifest_pin","first_descriptor")}
        hint.update(run=9,manifest_pin=manifest_pin,first_descriptor=copy.deepcopy(rows[0]),**{FIELD:admitted})
        module=api.factory(hint,old.rows);bound=module.Binding(rows,manifest_pin,next_case=165)
        graph,_=api.metadata.connect(c.ROOT,loader,bytes_policy,module,bound,step,9,guard.check)
        wire,_=graph.worker.encode(bound,step["prior_queue_pin"],step["prior_candidate_pin"],guard.check)
        hint["capsule_pin"]=publish_bytes(capsule_name,wire,16384)
        hint_pin=publish_bytes(hint_name,encoded(hint),16384)
        observed=dict(active=False,data_file_opens=0)
        def audit(event,args):
            if observed["active"] and event=="open" and args and isinstance(args[0],str) and args[0].lower().endswith(".json"):
                observed["data_file_opens"]+=1
        sys.addaudithook(audit);observed["active"]=True
        try:rebuilt,details=api.reconstruct(hint,wire,guard.check)
        finally:observed["active"]=False
        a.exact(observed["data_file_opens"],0,"ORIGINAL_RECONSTRUCTION_WITHOUT_RECEIPT_OR_MANIFEST_IO")
        module.exact(rebuilt.binding.descriptors(),rows,"ACTUAL_RECONSTRUCTED69_MATCH_PARENT")
        spec=importlib.util.spec_from_file_location("native009_transport_contracts",c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        tests.MODULE=sys.modules[__name__];tests.API=api;tests.HINT=hint;tests.WIRE=wire;tests.GRAPH=graph;tests.CHECKPOINT=guard.check
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row["contract_failures"]=[dict(test=t.id().rsplit(".",1)[-1],exception_type=trace.splitlines()[-1].split(":",1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row["contracts"],dict(run=12,errors=0,failures=0,skipped=0),"TRANSPORT12")
        for module in tuple(sys.modules.values()):
            filename=getattr(module,"__file__",None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/"tools/p09") and path.suffix==".py":q.pin(path.relative_to(c.ROOT).as_posix())
        old.reader.finish();q.finish();guard.check(force=True)
        row.update(state="PASS_NATIVE009_CAPSULE69_AND_ORIGINAL_RECONSTRUCTION12_NOT_NATIVE_OR_DISPATCH",
            manifest_pin=manifest_pin,capsule_pin=hint["capsule_pin"],bootstrap_pin=hint_pin,
            descriptor_count=69,task=graph.worker.TASK,reconstruction_proof=details,run_limit_proofs=api.run_limit_proofs,
            actual_reconstruction_data_file_opens=observed["data_file_opens"],
            existing_foundation_context=8,existing_foundation_source_pins=list(old.reader.snapshots.values()),
            existing_foundation_fresh=len(old.reader.snapshots),existing_foundation_final=old.reader.final_fresh_hashes,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            parent_Frame_live_locks_or_whole_source_not_claimed=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        import traceback
        row["error_frames"]=[dict(file=Path(item.filename).name,function=item.name,line=item.lineno)
            for item in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    a.require(guard.cleanup,"TRANSPORT_OWNER_CLEANUP");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","contract_failures","capsule_pin","bootstrap_pin","descriptor_count","task",
        "existing_foundation_fresh","existing_foundation_final","fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
