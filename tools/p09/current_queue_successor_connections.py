"""One private parent/Frame/worker/oracle graph for successors161..249.

Preserve qualified source bodies and limits. Only closed case/count/key/task
metadata changes. Constructing this graph is NOT runtime, Native, GO or acceptance.
"""
from types import FunctionType, SimpleNamespace as NS

SELF="tools/p09/current_queue_successor_connections.py"
TEST="tools/p09/tests/test_current_queue_successor_connections.py"
CAPSULE_SCHEMA="hwpx-agent.p09-current-successor-worker-capsule/v1"
PINS=[
    dict(path="tools/p09/runtime_envelope_physical_io_v1.py",bytes=7214,sha256="b3bf5637c1f5d13bf9090236274826440e4c6c543b6db219a95b0869919c324c"),
    dict(path="tools/p09/held_envelope_boundary_guard_v1.py",bytes=1809,sha256="a65cd3c4c091e4e94b27b4d0474b2eafaf3fe2c4ac0682d7d95fa11c4d32e884"),
    dict(path="tools/p09/runtime_envelope_frame_connection_v1.py",bytes=3065,sha256="579aa5fb2e0d479077cf965c1dd449ab9fc48305bff9ea52a37bfb0f2688b4e5"),
    dict(path="tools/p09/runtime_envelope_raw_access_policy_v1.py",bytes=4423,sha256="74eff97e55402e5e08798ce03a122218b1047844caaf9f61cca92287601bb535"),
    dict(path="tools/p09/runtime_envelope_raw_access_policy_v2.py",bytes=1810,sha256="4070a0b1c7e717220fe2513398e1fa135eca4b1f40c11ab449cc6dce918d6bdf"),
    dict(path="tools/p09/runtime_envelope_parent_connection_v1.py",bytes=6385,sha256="24c08ee3ebfa5898aba7f7548471f4bb4c30f05c7a35bff22923fa0e6563db19"),
    dict(path="tools/p09/runtime_envelope_parent_connection_v2.py",bytes=768,sha256="12360108843c71f4be058059470f26797a50c4e500fbe75d7d289f33c59dfeab"),
    dict(path="tools/p09/runtime_envelope_worker_connection_v1.py",bytes=4745,sha256="4730608693080a9492dee36c14cbc606e69f5ec4d5aa2ea4c14a90475110bd92"),
    dict(path="tools/p09/runtime_envelope_full_oracle_connection_v1.py",bytes=4080,sha256="570dd57f96234991e5762689d11c404a64279d0a1fbf8ba38297680932a61863"),
    dict(path="tools/p09/compact_worker_capsule_wire_v1.py",bytes=5168,sha256="2649fcca9479ae889b71b548e7a079357121b5df0a127c7cd85d66671cd9e7bd")]


def require(ok,code):
    if not ok:raise ValueError("CURRENT_SUCCESSOR_CONNECTION_"+code)


def clone(fn,env):
    require(type(fn) is FunctionType,"ORIGINAL_FUNCTION")
    result=FunctionType(fn.__code__,env,argdefs=fn.__defaults__,closure=fn.__closure__)
    result.__kwdefaults__=fn.__kwdefaults__
    return result


def project(fn,env,mapping):
    """Exact reversible constant-only metadata projection, never body rewriting."""
    require(len(set(mapping.values()))==len(mapping),"INJECTIVE_METADATA_MAP")
    inverse={v:k for k,v in mapping.items()}
    def constant(value,pairs):
        if type(value) is tuple:return tuple(constant(v,pairs) for v in value)
        if type(value) is frozenset:return frozenset(constant(v,pairs) for v in value)
        return pairs.get(value,value) if type(value) in (int,str) else value
    code=fn.__code__
    revised=code.replace(co_consts=tuple(constant(v,mapping) for v in code.co_consts))
    restored=revised.replace(co_consts=tuple(constant(v,inverse) for v in revised.co_consts))
    require(restored==code,"ENTIRE_METADATA_INVERSE")
    result=FunctionType(revised,env,argdefs=fn.__defaults__,closure=fn.__closure__)
    result.__kwdefaults__=fn.__kwdefaults__
    return result


def worker_api(original,compact,binding_module,step,run):
    index=step["index"]
    require(type(index) is int and 161<=index<=249 and type(step["before"]) is int
        and step["before"]==index-7,"CLOSED_CASE_CONTEXT")
    require(type(run) is int and 1<=run<=8,"CLOSED_PHYSICAL_RUN")
    source=binding_module
    authority=source.source.copy_pin(step["prior_queue_pin"])
    prior=source.source.copy_pin(step["prior_candidate_pin"])
    require(authority["path"]==f"implementation/p09/evidence/p09-361-case{index-1}-current-epoch-accept001.v1.json",
        "EXACT_PRIOR_AUTHORITY_PATH")
    import re
    require(re.fullmatch(f"implementation/p09/evidence/p09-361-case{index-1}-current-runtime-run[0-9]{{3}}\\.v1\\.json",prior["path"])
        is not None,"EXACT_PRIOR_RUNTIME_PATH")
    task=f"case{index}-current-r{run:03}-tests"
    compact_env=dict(vars(compact))
    compact_env["pack"]=project(compact.pack,compact_env,{160:index,153:index-7})
    compact_env["unpack"]=clone(compact.unpack,compact_env)
    WireJSON=type("PrivateCurrentWireJSON",(),{
        name:staticmethod(clone(getattr(compact.JSON,name),compact_env)) for name in ("dumps","loads")})
    env=dict(original.encode.__globals__,source=source,AUTHORITY=authority,ROOT=prior,SCHEMA=CAPSULE_SCHEMA,TASK=task,json=WireJSON)
    mapping={158:index,151:index-7,"authority151_pin":"authority_pin","actual157_pin":"prior_runtime_pin"}
    functions={}
    for name in ("encode","decode"):
        fn=getattr(original,name)
        require(all(sum(type(v) is int and v==old for v in fn.__code__.co_consts)==1 for old in (158,151)),
            "ONE_CASE_AND_ONE_COUNT_LITERAL")
        functions[name]=project(fn,dict(fn.__globals__,**env),mapping)
    worker=clone(original.connect_worker,dict(original.connect_worker.__globals__,source=source,
        raw_policy=original.raw_policy,TASK=task))
    api=NS(**{**vars(original),**env,**functions,"connect_worker":worker})
    require(api.MAX_BYTES==compact.MAX_BYTES==16384,"ORIGINAL_16K_WIRE_LIMIT")
    return api,dict(encoder_decoder_and_compact_pack_entire_inverse=True,
        original_worker_connector_code_defaults_closure_retained=True,
        no_original_module_mutated=True,maximum_wire_bytes=16384,current_task=task,
        parent_whole_source_lock_and_independent_oracle_still_required=True,
        actual_worker_Native_product_or_GO_qualified=False)


def connect(root,loader,bytes_policy,binding_module,bound,step,run,checkpoint):
    checkpoint()
    require(type(bound) is binding_module.Binding and bound.next_case==step["index"],"EXACT_PRIVATE_CURRENT_BINDING")
    namespaces,proofs=loader.load(root,PINS,{
        "runtime_envelope_scope_binding_v1":binding_module,
        "runtime_envelope_source_projection_v1":binding_module.source,
        "owned_source_read_pressure":bytes_policy})
    parent=namespaces.runtime_envelope_parent_connection_v2
    frames=namespaces.runtime_envelope_frame_connection_v1
    original_worker=namespaces.runtime_envelope_worker_connection_v1
    oracle=namespaces.runtime_envelope_full_oracle_connection_v1
    worker,wire_proof=worker_api(original_worker,namespaces.compact_worker_capsule_wire_v1,binding_module,step,run)
    require(parent.access.source is binding_module and frames.binding_module is binding_module
        and original_worker.raw_policy.source is binding_module and worker.source is binding_module
        and oracle.binding_module is binding_module,"ONE_PARENT_FRAME_WORKER_ORACLE_BINDING_NAMESPACE")
    checkpoint()
    return NS(binding_module=binding_module,binding=bound,parent=parent,frames=frames,worker=worker,
        full_oracle=oracle,namespaces=namespaces),dict(source_proofs=proofs,wire_projection=wire_proof,
        one_private_binding_namespace=True,all_original_nonmetadata_source_AST_retained=True,
        whole_engine_worker_dispatch_and_oracle_NOT_RUN=True,GO_authorized=False)


def prepare(index,binding_attempt,attempt):
    """Fresh actual context and transport preparation, not full runtime CODE."""
    import argparse
    import copy
    import hashlib
    import json
    import os
    from pathlib import Path
    import re
    import sys
    import time
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import current_queue_successor_binding as bindings
    import runtime_envelope_namespace_bundle_v1 as loader
    import owned_source_read_pressure as bytes_policy
    import prepare_current_queue_step as steps
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    require(type(index) is int and 161<=index<=249,"PREPARE_INDEX")
    require(all(type(v) is int and 1<=v<=8 for v in (binding_attempt,attempt)),"PREPARE_ATTEMPTS")
    capsule_name=f"implementation/p09/evidence/p09-361-case{index}-successor-worker-capsule{attempt:03}.compact.v1.json"
    output=f"implementation/p09/evidence/p09-361-case{index}-successor-connections{attempt:03}.v1.json"
    require(all(not (c.ROOT/n).exists() for n in (capsule_name,output)),"EXCLUSIVE_GRAPH_OUTPUTS")
    guard=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    out=dict(state="FAILED_SUCCESSOR_GRAPH_PREPARATION_NOT_ADOPTED",index=index,accepted_count_delta=0,
        product_or_Native_executed=False,GO_authorized=False,P09_gate="OPEN")
    def publish(name,raw,limit):
        require(type(raw) is bytes and 0<len(raw)<=limit,"BOUNDED_GRAPH_PUBLICATION")
        path=c.ROOT/name
        for parent in (path.parent,*path.parent.parents):
            require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_GRAPH_ANCESTORS")
            if parent==c.ROOT:break
        with path.open("xb") as stream:
            require(stream.write(raw)==len(raw),"ALL_GRAPH_PUBLICATION_BYTES");stream.flush();os.fsync(stream.fileno())
        return dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,TEST,bindings.SELF,bindings.TEST,loader.SELF,bytes_policy.SELF,steps.SELF,steps.TEST):q.pin(name)
        for pin in bindings.PINS+PINS:a.exact(q.pin(pin["path"]),pin,"EXACT_ALL_PRIVATE_GRAPH_SOURCES")
        prepared=q.json(f"implementation/p09/evidence/p09-361-case{index}-successor-binding{binding_attempt:03}.v1.json")
        a.fields(prepared,dict(state="PREPARED_REAL_SUCCESSOR_BINDING_ALL_PAIRS_NOT_WHOLE_RUNTIME_OR_GO",index=index,
            cleanup_confirmed=True,accepted_count_delta=0,product_or_Native_executed=False,GO_authorized=False),"REAL_PREPARED_BINDING")
        require(prepared["fresh_inputs"]==prepared["final_fresh_hashes"],"CLOSED_BINDING_INPUT_HASHES")
        sealed=scope.pins(prepared["source_pins"])
        for name in (bindings.SELF,bindings.TEST):a.exact(q.pin(name),sealed[name],"UNCHANGED_PREPARED_BINDING_CODE")
        manifest=a.read_exact(q,prepared["manifest_pin"])
        a.fields(manifest,dict(schema_version="hwpx-agent.p09-current-successor-binding-manifest/v1",
            index=index,before=index-7),"EXACT_BINDING_MANIFEST_CONTEXT")
        step=q.json(f"implementation/p09/evidence/p09-361-case{index}-step-config001.v1.json")
        authority=a.read_exact(q,step["prior_queue_pin"]);prior=a.read_exact(q,step["prior_candidate_pin"])
        listing=a.read_exact(q,scope.LIST_PIN)
        expected=steps.derive_step(index,step["prior_queue_pin"],authority,prior,listing["source_test_names"])
        a.exact(step,expected,"ACTUAL_FULL_COMPILED_LIST_STEP")
        a.exact(manifest["authority_pin"],step["prior_queue_pin"],"CURRENT_MANIFEST_AUTHORITY")
        a.exact(manifest["prior_runtime_pin"],step["prior_candidate_pin"],"CURRENT_MANIFEST_PRIOR_RUNTIME")
        representation=prior["source_input_representation"]
        history={k:copy.deepcopy(representation[k]) for k in bindings.PROVENANCE_KEYS if k in representation}
        a.exact(manifest["historical_predecessor_provenance"],history,"UNCHANGED_HISTORICAL_PROVENANCE")
        module,proof=bindings.connect(c.ROOT,loader,scope,index,history,representation["descriptors"])
        bound=module.Binding(manifest["descriptors"],prepared["manifest_pin"],next_case=index)
        require(len(bound.descriptors())==prepared["pair_count"],"ALL_REAL_BINDING_ROWS")
        graph,connected=connect(c.ROOT,loader,bytes_policy,module,bound,step,attempt,guard.check)
        wire,transport=graph.worker.encode(bound,step["prior_queue_pin"],step["prior_candidate_pin"],guard.check)
        decoded,decoder=graph.worker.decode(wire,transport,guard.check)
        a.exact(decoded.descriptors(),bound.descriptors(),"EVERY_REAL_WORKER_DESCRIPTOR_RESTORED")
        a.exact(dict(decoded.manifest_pin),dict(bound.manifest_pin),"EXACT_REAL_WORKER_MANIFEST")
        capsule_pin=publish(capsule_name,wire,16384)
        a.exact(q.pin(capsule_name),capsule_pin,"ACTUAL_PUBLISHED_WORKER_WIRE_BYTES")
        q.finish();guard.check(force=True)
        out.update(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",
            binding_report_pin=q.snapshots[f"implementation/p09/evidence/p09-361-case{index}-successor-binding{binding_attempt:03}.v1.json"],
            step=step,manifest_pin=prepared["manifest_pin"],capsule_pin=capsule_pin,task=graph.worker.TASK,
            pair_count=len(bound.descriptors()),all_worker_rows_restored=True,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_read_passes=q.read_passes,actual_bytes_read=q.bytes_read,
            one_private_binding_namespace=connected["one_private_binding_namespace"],
            original_binding_source_AST_proofs=proof["source_proofs"],original_graph_source_AST_proofs=connected["source_proofs"],
            wire_projection=connected["wire_projection"],decoder=decoder,
            entire_current_runtime_imported_closure_and_cost_NOT_qualified=True,
            actual_parent_engine_worker_dispatch_and_full_oracle_NOT_RUN=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):out["error_code"]=error.args[0]
    finally:
        guard.close();out.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((r["system_cpu_percent"] for r in guard.samples),default=None),
            RAM_min=min((r["available_ram_percent"] for r in guard.samples),default=None))
    require(guard.cleanup,"GRAPH_PREPARATION_CLEANUP")
    publish(output,(json.dumps(out,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8"),262144)
    print(json.dumps({k:out.get(k) for k in ("state","pair_count","capsule_pin","fresh_inputs","final_fresh_hashes",
        "elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if out["state"].startswith("PREPARED_") else 1


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument("--case",type=int,required=True)
    parser.add_argument("--binding-attempt",type=int,required=True);parser.add_argument("--attempt",type=int,required=True)
    args=parser.parse_args();raise SystemExit(prepare(args.case,args.binding_attempt,args.attempt))
