"""Actual preparation/worker entry for the fixed case165 ordinary table.

Reuse original orchestration, admission, CODE, pacing, guards and NO-GO worker.
Native uses the original dispatcher's mandatory current-qualification gate.
No review/accept CLI; no source, scope, resource or product gate is bypassed.
"""
from pathlib import Path
from types import FunctionType, SimpleNamespace as NS
from contextlib import ExitStack
import sys

SELF = "tools/p09/level6_closed_preparation_v1.py"
VERSION = "v10"
CORE = dict(path="tools/p09/level6_ordinary_binding_v1.py", bytes=18358,
    sha256="76d78b86681f3032720850ebb1df07333539db25a5a73a3562a61ca50476e9f6")
DRIVER = dict(path="tools/p09/expanded_unhooked_setup_dependency_v1.py", bytes=6110,
    sha256="b286198de3107c9cbbc5a942b16bb4dfd336dd68431a64a061c566a5ec097af0")
SERIAL = dict(path="tools/p09/qualify_expanded_worker_startup_v1.py", bytes=9201,
    sha256="c820344b66f8863eee33c3b44c30a684dc33637e7e9b3c5ba28179ac8a3ee199")
PRIOR_ALIAS = dict(path="tools/p09/prior_preparation_alias_v1.py", bytes=7565,
    sha256="106535e83f4c3af0e6cd928185556118a12411906933fa3f2f2415dc0ec10492")


def require(ok, label):
    if not ok: raise ValueError("LEVEL6_PREPARATION_" + label)


def family(fn, code):
    result = FunctionType(code, fn.__globals__, argdefs=fn.__defaults__, closure=fn.__closure__)
    result.__kwdefaults__ = fn.__kwdefaults__
    return result


def loader_profile(root, original, core, a, prior_alias):
    state = dict(seed_stack=None, seed_hint=None)
    def load(*args, **options):
        modules, proof = original.load(*args, **options)
        bindings = getattr(modules, "current_queue_successor_binding", None)
        if bindings is not None and not getattr(bindings, "level6_entry_hook", False):
            whole = bindings.connect
            def connect(*items, **kwargs):
                module, result = whole(*items, **kwargs)
                historical = items[5] if len(items) > 5 else kwargs.get("historical_pairs", ())
                core.install(module, historical)
                if not getattr(module,"prior_preparation_alias_installed",False):
                    prior_alias.install(module,historical,items[3] if len(items)>3 else kwargs["index"])
                if state["seed_stack"] is not None and not getattr(module, "level6_seed_registered", False):
                    hint = state["seed_hint"]
                    state["seed_stack"].enter_context(core.bootstrap_seed(module, hint["first_descriptor"], hint["manifest_pin"]))
                    module.level6_seed_registered = True
                return module, result
            bindings.connect = connect; bindings.level6_entry_hook = True
        connection = getattr(modules, "closed_prebody_runtime_connection_v1", None)
        if connection is not None:
            whole = connection.connect
            def connect_runtime(*items, **kwargs):
                result = whole(*items, **kwargs); runtime = items[0]
                reconstruct = runtime.reconstruct_worker_graph
                def reconstruct_current(root, loader, scope, bytes_policy, hint, wire, checkpoint):
                    require(state["seed_stack"] is None, "ONE_SERIAL_RECONSTRUCTION")
                    try:
                        with ExitStack() as stack:
                            state.update(seed_stack=stack, seed_hint=hint)
                            graph, info = reconstruct(root, loader, scope, bytes_policy, hint, wire, checkpoint)
                            rows = [r for r in graph.binding.descriptors() if core.is_new(r)]
                            require(len(graph.binding.descriptors()) == 68 and len(rows) == 61
                                and core.fingerprint(rows) == core.SPEC["mapping_sha256"], "FULL_WORKER_TABLE_AFTER_SEED")
                            return graph, info
                    finally: state.update(seed_stack=None, seed_hint=None)
                connection.publish_function(runtime, "reconstruct_worker_graph", reconstruct_current)
                original_scope=runtime.current_input_scope
                def parent_input_scope(q,graph,step,report_pin,manifest_pin,source_pins):
                    authority=a.read_exact(q,step["prior_queue_pin"])
                    a.fields(authority,dict(accepted_count_after=step["index"]-7,next_runtime_index=step["index"],
                        runtime_candidate_pin=step["prior_candidate_pin"],resource_cleanup_confirmed=True),"FRESH_PARENT_PRIOR_AUTHORITY")
                    prior=a.read_exact(q,step["prior_candidate_pin"])
                    representation=prior["source_input_representation"]
                    a.fields(representation,dict(schema_version="hwpx-agent.p09-explicit-runtime-source-binding/v1",
                        next_case=step["index"]-1,full_original_product_oracle_required=True),"ADMITTED_PRIOR_LOGICAL_SCOPE")
                    module=graph.binding_module
                    seal=dict(authority_pin=dict(step["prior_queue_pin"]),prior_pin=dict(step["prior_candidate_pin"]))
                    previous_seal=getattr(module,"level6_admitted_parent_history",None)
                    if previous_seal is None:
                        require(getattr(module,"prior_preparation_alias_installed",False),"QUALIFIED_PRIOR_ALIAS_ADAPTER_REQUIRED")
                        original_union=module.Binding.semantic_union
                        pairs=[dict(r,semantic_original_pin=dict(r["semantic_original_pin"]),
                            physical_envelope_pin=dict(r["physical_envelope_pin"])) for r in representation["descriptors"]]
                        def union(self,rows,checkpoint):
                            normalized,_=prior_alias.normalize(module.source.scope,pairs,rows,step["index"],checkpoint)
                            return original_union(self,normalized,checkpoint)
                        module.Binding.semantic_union=union
                        module.level6_admitted_parent_history=seal
                    else:a.exact(previous_seal,seal,"ONE_FRESH_PARENT_HISTORY_EPOCH")
                    return original_scope(q,graph,step,report_pin,manifest_pin,source_pins)
                connection.publish_function(runtime,"current_input_scope",parent_input_scope)
                # owned_worker_entry belongs to the original runtime family,
                # not the connector wrapper's globals. Publish to that same
                # private family before its literal-only suffix projection.
                for fn in vars(runtime).values():
                    if type(fn) is FunctionType and fn.__globals__.get("__name__", "").startswith("p09_exact_current_queue_successor_runtime"):
                        fn.__globals__["reconstruct_worker_graph"] = reconstruct_current
                        fn.__globals__["current_input_scope"] = parent_input_scope
                return result
            connection.connect = connect_runtime
        transport = getattr(modules, "closed_prebody_worker_connection_v1", None)
        if transport is not None and not getattr(transport, "level6_seed_connected", False):
            raw_reconstruct = transport.reconstruct
            def reconstruct_transport(*items, **kwargs):
                # Original IO setup calls transport.reconstruct directly,
                # before a parent stage reader configures the public runtime.
                if state["seed_stack"] is not None:
                    return raw_reconstruct(*items, **kwargs)
                hint = items[6] if len(items) > 6 else kwargs["hint"]
                try:
                    with ExitStack() as stack:
                        state.update(seed_stack=stack, seed_hint=hint)
                        graph, info = raw_reconstruct(*items, **kwargs)
                        rows = [r for r in graph.binding.descriptors() if core.is_new(r)]
                        require(len(graph.binding.descriptors()) == 68 and len(rows) == 61
                            and core.fingerprint(rows) == core.SPEC["mapping_sha256"], "FULL_DIRECT_TRANSPORT_TABLE_AFTER_SEED")
                        return graph, info
                finally: state.update(seed_stack=None, seed_hint=None)
            transport.reconstruct = reconstruct_transport; transport.level6_seed_connected = True
        namespace = getattr(modules, "expanded_preparation_namespace_v1", None)
        if namespace is not None:
            raw_literal=namespace.literal_function
            profile_version=VERSION
            def profile_literal(fn,mapping):
                targets={"v9":profile_version,".v9.json":"."+profile_version+".json",
                    ".compact.v9.json":".compact."+profile_version+".json"}
                return raw_literal(fn,{k:targets.get(v,v) for k,v in mapping.items()})
            # Keep the namespace family so the frozen serialization connector's
            # late-reader dependency injection remains visible to the factory.
            literal=FunctionType(profile_literal.__code__,raw_literal.__globals__,argdefs=profile_literal.__defaults__,closure=profile_literal.__closure__)
            raw_literal.__globals__["literal_function"]=literal;namespace.literal_function=literal
            whole = namespace.retarget_worker
            def retarget(runtime, ignored): return whole(runtime, SELF)
            namespace.retarget_worker = retarget
        serializer=getattr(modules,"qualify_expanded_worker_startup_v1",None)
        if serializer is not None:
            ns,_=original.load(root,[linked_profile_namespace],{})
            fn=serializer.expected_dumps
            changed,_=ns.expanded_preparation_namespace_v1.literal_function(fn,{
                ".compact.v9.json":".compact."+VERSION+".json",
                r"implementation/p09/evidence/p09-361-case([0-9]{3})-successor-worker-capsule([0-9]{3})\.compact\.v9\.json":
                    r"implementation/p09/evidence/p09-361-case([0-9]{3})-successor-worker-capsule([0-9]{3})\.compact\.v10\.json"})
            fn.__globals__["expected_dumps"]=changed;serializer.expected_dumps=changed
        entry = getattr(modules, "closed_prebody_factory_admission_fix_v1", None)
        if entry is not None:
            whole = entry.load
            def connected(*items, **kwargs):
                values = list(items); api = values[1]
                class Reader(api.AcceptanceReader):
                    def __init__(self, *args, **options):
                        super().__init__(*args, **options)
                        self.pin(SELF)
                        a.exact(self.pin(CORE["path"]), CORE, "EXACT_CURRENT_LEVEL6_COMPONENT")
                        code = self.json(core.PREFIX + "level6-binding-code005.v1.json")
                        a.fields(code, dict(state="PASS_LEVEL6_ORDINARY_BINDING_CODE10_NOT_ENTRY_OR_PRODUCT",
                            contracts=dict(run=10, errors=0, failures=0, skipped=0), cleanup_confirmed=True), "CURRENT_LEVEL6_CODE10")
                        require(code["fresh_inputs"] == code["final_fresh_hashes"] > 0, "CODE10_FINAL_HASHES")
                        for pin in code["source_pins"]: a.exact(self.pin(pin["path"]), pin, "CURRENT_LEVEL6_QUALIFICATION_SOURCES")
                        core.admit(self, a, scope_outer)
                        a.exact(self.pin(PRIOR_ALIAS["path"]),PRIOR_ALIAS,"EXACT_PRIOR_ALIAS_SCOPE_ADAPTER")
                        alias_code=self.json(core.PREFIX+"prior-preparation-alias-code001.v1.json")
                        a.fields(alias_code,dict(state="PASS_PRIOR_PREPARATION_ALIAS_CODE6_NOT_CURRENT_ENTRY_OR_PRODUCT",
                            contracts=dict(run=6,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"CURRENT_PRIOR_ALIAS_CODE6")
                        require(alias_code["fresh_inputs"]==alias_code["final_fresh_hashes"]>0,"PRIOR_ALIAS_FINAL_HASHES")
                        for pin in alias_code["source_pins"]:a.exact(self.pin(pin["path"]),pin,"CURRENT_PRIOR_ALIAS_QUALIFIED_SOURCES")
                scope_outer = values[2]
                values[1] = NS(**{**vars(api), "AcceptanceReader": Reader})
                linked = whole(*values, **kwargs)
                # Separate factory receipt namespace; all original body checks
                # and the current suffix remain. Avoid consuming old slots.
                runtime = linked.modules.current_queue_successor_runtime
                if not getattr(runtime, "level6_factory_receipt_namespace", False):
                    names,_ = original.load(root, [linked_profile_namespace], {})
                    fn = runtime.qualify_factory
                    changed,_ = names.expanded_preparation_namespace_v1.literal_function(fn,
                        {"-successor-factory": "-successor-level6-factory"})
                    revised = family(fn, changed.__code__)
                    fn.__globals__["qualify_factory"] = revised; runtime.qualify_factory = revised
                    runtime.level6_factory_receipt_namespace = True
                return linked
            entry.load = connected
        return modules, proof
    # Frozen namespace component shared by all existing prepared frontends.
    linked_profile_namespace = dict(path="tools/p09/expanded_preparation_namespace_v1.py", bytes=4549,
        sha256="96a9ebbca1197d877238de195bab3465ab3f8916675dd5b3e1a34f93f6071f89")
    return NS(**{**vars(original), "load": load})


def execute(fn, envelope):
    builtins = dict(fn.__builtins__); previous = builtins["__import__"]
    def declared(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "flat_current_queue_envelope_runtime_v25" and level == 0: return envelope
        return previous(name, globals, locals, fromlist, level)
    builtins["__import__"] = declared
    result = FunctionType(fn.__code__, dict(fn.__globals__, __builtins__=builtins),
        argdefs=fn.__defaults__, closure=fn.__closure__)
    result.__kwdefaults__ = fn.__kwdefaults__
    return result()


def main():
    import argparse, hashlib, json, os, re, time
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_envelope_runtime_v25 as envelope
    raw,_ = envelope.namespace_bundle.load(c.ROOT, [CORE,PRIOR_ALIAS], {})
    core = raw.level6_ordinary_binding_v1
    profiled = loader_profile(c.ROOT, envelope.namespace_bundle, core, a, raw.prior_preparation_alias_v1)
    proxy = NS(**{**vars(envelope), "namespace_bundle": profiled})
    sources,_ = profiled.load(c.ROOT, [core.FRONT], {})
    front = sources.expanded_closed_preparation_v1
    if len(sys.argv) == 4 and sys.argv[1:3] == ["--owned-worker", "--task"]:
        return execute(front.main, proxy)
    require(not any(f in sys.argv for f in ("--review", "--accept")), "NO_REVIEW_OR_ACCEPT_ENTRY")
    if any(f in sys.argv for f in ("--preflight", "--qualify")):
        modules,_ = profiled.load(c.ROOT, [DRIVER], {})
        return execute(modules.expanded_unhooked_setup_dependency_v1.main, proxy)
    if "--bootstrap" in sys.argv:
        modules,_ = profiled.load(c.ROOT, [SERIAL], {})
        return execute(modules.qualify_expanded_worker_startup_v1.main, proxy)
    parser = argparse.ArgumentParser()
    for n in ("case", "run", "attempt"): parser.add_argument("--"+n, type=int, required=True)
    for n in ("code-attempt","preflight-attempt","qualification-attempt"):parser.add_argument("--"+n,type=int,default=1)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--graph", action="store_true"); mode.add_argument("--code", action="store_true");mode.add_argument("--native",action="store_true")
    args = parser.parse_args()
    require(args.case == 165 and 5 <= args.run <= 8 and 1 <= args.attempt <= 8, "CLOSED_CURRENT_CONTEXT")
    namespace, private, entry_proxy, routed = front.components(c.ROOT, proxy)
    utils,_ = envelope.namespace_bundle.load(c.ROOT, private.PINS, {})
    prefix = core.PREFIX
    ctx = NS(preflight=prefix+f"successor-preflight-run{args.run:03}-attempt001.v1.json",
        qualification=prefix+f"successor-dispatch-qualification-run{args.run:03}-attempt001.v1.json")
    entry_ns,_ = entry_proxy.namespace_bundle.load(c.ROOT, [front.FIX], {})
    linked = entry_ns.closed_prebody_factory_admission_fix_v1.load(c.ROOT, a, scope, bytes_policy,
        entry_proxy, prefix+"sealed-metadata-code001.v1.json", ctx=ctx)
    if args.native:
        require(all(1<=n<=8 for n in (args.code_attempt,args.preflight_attempt,args.qualification_attempt)),"NATIVE_CONTEXT")
        runtime=linked.modules.current_queue_successor_runtime;dispatch=linked.modules.current_queue_successor_dispatch
        # Same exact metadata-only projection used by the qualified original IO
        # orchestration. The complete original dispatch/Frame/GO body is called.
        for name in ("construct","prepare_bootstrap"):
            fn=getattr(dispatch,name)
            require(sum(type(v) is str and v==".v4.json" for v in fn.__code__.co_consts)==1,"ONE_NATIVE_GRAPH_NAMESPACE_LITERAL")
            changed=runtime.metadata.project(fn,dict(fn.__globals__),{".v4.json":"."+VERSION+".json"})
            fn.__globals__[name]=changed;setattr(dispatch,name,changed)
        return dispatch.main(dispatch.context(165,args.run,args.code_attempt,args.preflight_attempt,args.qualification_attempt),False)
    if args.code: return linked.modules.current_queue_successor_controller.run_code(165, args.run, args.attempt)
    output = prefix+f"successor-connections{args.run:03}.{VERSION}.json"
    diagnostic = prefix+f"level6-entry-{VERSION}-graph-run{args.run:03}-attempt{args.attempt:03}.v1.json"
    require(all(not (c.ROOT/n).exists() for n in (output, diagnostic)), "EXCLUSIVE_GRAPH_RECEIPTS")
    guard = utils.terminal_metadata_pressure_v1.guard_type(utils.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    started = time.monotonic(); q = None
    row = dict(state="FAILED_SUCCESSOR_GRAPH_PREPARATION_NOT_ADOPTED", index=165, accepted_count_delta=0,
        product_or_Native_executed=False, GO_authorized=False, P09_gate="OPEN")
    try:
        guard.acquire(); q = linked.api.AcceptanceReader(c.ROOT, guard.check)
        baseline, rows, spec = core.admit(q, a, scope)
        base_name = prefix+"successor-connections004.v9.json"; base = q.json(base_name)
        a.fields(base, dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",
            index=165, cleanup_confirmed=True), "QUALIFIED_BASE_GRAPH")
        for pin in base["source_pins"]: a.exact(q.pin(pin["path"]), pin, "EVERY_OLD_GRAPH_SOURCE_RETAINED")
        step = base["step"]; prior = a.read_exact(q, step["prior_candidate_pin"])
        authority = a.read_exact(q, step["prior_queue_pin"])
        a.fields(authority, dict(accepted_count_after=158, next_runtime_index=165,
            runtime_candidate_pin=step["prior_candidate_pin"], resource_cleanup_confirmed=True), "CURRENT_PREDECESSOR_AUTHORITY")
        bindings = linked.modules.current_queue_successor_binding
        module, proof = linked.connection.binding_api(bindings, linked.alias, q.closed_source_policy).connect(
            c.ROOT, entry_proxy.namespace_bundle, scope, 165, baseline["historical_predecessor_provenance"], prior["source_input_representation"]["descriptors"])
        runtime = linked.modules.current_queue_successor_runtime
        require(runtime.owned_worker_entry.__globals__.get("reconstruct_worker_graph") is runtime.reconstruct_worker_graph,
            "SAME_PUBLIC_AND_ACTUAL_WORKER_RECONSTRUCTION")
        manifest = dict(baseline, descriptors=rows, ordinary_recompression_spec=spec, ordinary_recompression_proof_pin=core.PROOF)
        def metadata_file(name, value):
            raw = (json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2)+"\n").encode("ascii")
            pin = dict(path=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            if (c.ROOT/name).exists(): a.exact(q.fresh_pin(name), pin, "EXISTING_METADATA_EXACT_ONLY")
            else: a.exact(utils.successor_preparation_workspace_v1.publish(c.ROOT,name,value,a),pin,"NEW_METADATA_PUBLISHED")
            a.exact(q.pin(name),pin,"ACTUAL_METADATA_BYTES")
            return pin
        manifest_pin = metadata_file(prefix+f"successor-level6-{VERSION}-manifest{args.run:03}.v1.json",manifest)
        bound = module.Binding(rows, manifest_pin, next_case=165)
        graph, connected = runtime.metadata.connect(c.ROOT, entry_proxy.namespace_bundle, bytes_policy, module, bound, step, args.run, guard.check)
        wire,_ = graph.worker.encode(bound,step["prior_queue_pin"],step["prior_candidate_pin"],guard.check)
        require(0 < len(wire) <= 16384,"UNCHANGED_WIRE16K")
        name = prefix+f"successor-worker-capsule{args.run:03}.compact.{VERSION}.json"
        pin = dict(path=name, bytes=len(wire), sha256=hashlib.sha256(wire).hexdigest()); path=c.ROOT/name
        for parent in (path.parent,*path.parent.parents):
            require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_CAPSULE_ANCESTORS")
            if parent==c.ROOT: break
        if path.exists(): a.exact(q.fresh_pin(name),pin,"EXISTING_CAPSULE_EXACT_ONLY")
        else:
            with path.open("xb") as stream: require(stream.write(wire)==len(wire),"ALL_WIRE_BYTES");stream.flush();os.fsync(stream.fileno())
        a.exact(q.pin(name),pin,"ACTUAL_CAPSULE_BYTES")
        hint=runtime.worker_hint(step,args.run,pin,manifest_pin,manifest,prior["source_input_representation"]["descriptors"])
        require(len((json.dumps(hint,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("ascii")) <=16384,"UNCHANGED_BOOTSTRAP16K")
        hint_pin=metadata_file(prefix+f"successor-worker-bootstrap{args.run:03}.{VERSION}.json",hint)
        restored, decoder=runtime.reconstruct_worker_graph(c.ROOT,entry_proxy.namespace_bundle,scope,bytes_policy,hint,wire,guard.check)
        a.exact(restored.binding.descriptors(),bound.descriptors(),"ALL68_CURRENT_PARENT_WORKER_ROWS")
        q.finish();guard.check(force=True)
        row.update(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",step=step,
            manifest_pin=manifest_pin,capsule_pin=pin,bootstrap_pin=hint_pin,base_graph_pin=q.snapshots[base_name],
            base_manifest_pin=base["manifest_pin"],task=graph.worker.TASK,pair_count=68,new_ordinary_count=61,preserved_special_count=7,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            decoder=decoder,all_worker_rows_restored=True,original_binding_source_AST_proofs=proof["source_proofs"],
            original_graph_source_AST_proofs=connected["source_proofs"],actual_entry_qualification_Native_product_or_GO_NOT_RUN=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if q is not None:row.update(source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"GRAPH_CLEANUP"); utils.successor_preparation_workspace_v1.publish(c.ROOT,diagnostic,row,a)
    if row["state"].startswith("PREPARED_"):utils.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","pair_count","fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_type","error_code")}))
    return 0 if row["state"].startswith("PREPARED_") else 1


if __name__ == "__main__":raise SystemExit(main())
