"""Reuse the qualified whole engine template with one current identity adapter.

Construction only. Full CODE, imported closure, preflight, Native and independent
acceptance remain required. No execution command or queue writer is provided here.
"""
from types import SimpleNamespace as NS
import current_queue_successor_connections as metadata

SELF="tools/p09/current_queue_successor_runtime.py"
TEST="tools/p09/tests/test_current_queue_successor_runtime.py"
WORKER_BOOTSTRAP_SCHEMA="hwpx-agent.p09-current-successor-worker-bootstrap/v1"
PINS=[
    dict(path="tools/p09/reviewed_case158_attempt_v3.py",bytes=3241,sha256="3b1b05141b47aaa8798733ed83fc6fc4232763e9bd8d29a168f3a614bb1b6bdd"),
    dict(path="tools/p09/reviewed_case158_attempt_v4.py",bytes=1984,sha256="9567a847d0def48b5ba5a69262ab7d12d05ce7902cac4c5998dd0f9290f18223")]


def worker_hint(step,run,capsule_pin,manifest_pin,manifest,historical_pairs):
    """Small sealed context, no historical receipt contents or current PASS."""
    import copy
    import produce_current_queue_envelopes as producer
    import current_stored_runtime_scope as scope
    index=step["index"]
    metadata.require(type(index) is int and 161<=index<=249 and type(run) is int and 2<=run<=8,"WORKER_HINT_CONTEXT")
    current={row["semantic_original_pin"]["path"]:row for row in manifest["descriptors"]}
    special=[]
    for row in historical_pairs:
        old,new=row["semantic_original_pin"],row["physical_envelope_pin"]
        if new["path"]==producer.output_path(old,index):continue
        sealed=current[old["path"]]
        metadata.require(old==sealed["semantic_original_pin"] and new==sealed["physical_envelope_pin"],"HINT_PAIR_IN_EXACT_CURRENT_MANIFEST")
        metadata.require(type(row["next_case"]) is int and row["next_case"]<index,"HINT_PRIOR_CONTEXT_NOT_RELABELLED")
        special.append(copy.deepcopy(row))
    hint=dict(schema_version=WORKER_BOOTSTRAP_SCHEMA,index=index,run=run,step=copy.deepcopy(step),
        capsule_pin=scope.pins([capsule_pin])[capsule_pin["path"]],manifest_pin=scope.pins([manifest_pin])[manifest_pin["path"]],
        first_descriptor=copy.deepcopy(manifest["descriptors"][0]),historical_pairs=special,
        historical_provenance=copy.deepcopy(manifest["historical_predecessor_provenance"]))
    validate_worker_hint(hint,f"case{index}-current-r{run:03}-tests")
    return hint


def validate_worker_hint(hint,task):
    import re
    import current_stored_runtime_scope as scope
    import current_queue_successor_binding as bindings
    metadata.require(type(hint) is dict and set(hint)=={"schema_version","index","run","step","capsule_pin","manifest_pin",
        "first_descriptor","historical_pairs","historical_provenance"},"CLOSED_WORKER_HINT")
    index,run=hint["index"],hint["run"]
    metadata.require(hint["schema_version"]==WORKER_BOOTSTRAP_SCHEMA and type(index) is int and 161<=index<=249
        and type(run) is int and 2<=run<=8 and task==f"case{index}-current-r{run:03}-tests","EXACT_WORKER_HINT_TASK")
    step=hint["step"]
    metadata.require(type(step) is dict and set(step)=={"schema_version","index","before","case","prior_queue_pin","prior_candidate_pin"},"CLOSED_WORKER_STEP")
    metadata.require(step["schema_version"]=="hwpx-agent.p09-flat-current-queue-step/v1" and type(step["index"]) is int
        and step["index"]==index and type(step["before"]) is int and step["before"]==index-7
        and type(step["case"]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_:]*",step["case"]),"EXACT_WORKER_STEP_CONTEXT")
    scope.pins([step["prior_queue_pin"],step["prior_candidate_pin"],hint["capsule_pin"],hint["manifest_pin"]])
    metadata.require(hint["capsule_pin"]["path"]==f"implementation/p09/evidence/p09-361-case{index}-successor-worker-capsule{run:03}.compact.v1.json"
        and hint["capsule_pin"]["bytes"]<=16384,"EXACT_BOUNDED_WORKER_CAPSULE_PATH")
    metadata.require(hint["manifest_pin"]["path"].startswith(f"implementation/p09/evidence/p09-361-case{index}-successor-")
        and hint["manifest_pin"]["path"].endswith(".v1.json"),"EXPLICIT_CURRENT_MANIFEST_PATH")
    metadata.require(type(hint["historical_pairs"]) is list and len(hint["historical_pairs"])<=249
        and type(hint["historical_provenance"]) is dict and set(hint["historical_provenance"])<=set(bindings.PROVENANCE_KEYS),"CLOSED_PRIOR_HINTS")
    return index,run


def reconstruct_worker_graph(root,loader,scope,bytes_policy,hint,wire,checkpoint):
    """Decode the exact bounded current transport without original receipt IO."""
    import current_queue_successor_binding as bindings
    index,run=validate_worker_hint(hint,f"case{hint['index']}-current-r{hint['run']:03}-tests")
    module,proof=bindings.connect(root,loader,scope,index,hint["historical_provenance"],hint["historical_pairs"])
    initial=module.Binding([hint["first_descriptor"]],hint["manifest_pin"],next_case=index)
    graph,graph_proof=metadata.connect(root,loader,bytes_policy,module,initial,hint["step"],run,checkpoint)
    expected={k:hint["capsule_pin"][k] for k in ("bytes","sha256")}
    bound,decoder=graph.worker.decode(wire,expected,checkpoint)
    module.exact(dict(bound.manifest_pin),hint["manifest_pin"],"EXACT_WORKER_HINT_MANIFEST")
    metadata.require(bound.descriptors()[0]==hint["first_descriptor"],"EXACT_FIRST_DESCRIPTOR_NOT_SCOPE_SUBSTITUTION")
    return NS(**{**vars(graph),"binding":bound}),dict(decoder,all_current_rows_reconstructed=True,
        original_receipt_manifest_or_authority_files_read=False,whole_worker_Native_product_or_GO_qualified=False)


def owned_worker_entry(task):
    """Minimal current startup; original worker still requires GO and Job."""
    import json
    from pathlib import Path
    import re
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import current_stored_runtime_scope as scope
    import runtime_envelope_namespace_bundle_v1 as loader
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_product_window_runtime_v18 as window
    match=re.fullmatch(r"case([0-9]{3})-current-r([0-9]{3})-tests",task)
    metadata.require(match is not None,"EXACT_OWNED_WORKER_TASK_SHAPE")
    index,run=int(match[1]),int(match[2])
    metadata.require(161<=index<=249 and 2<=run<=8,"CLOSED_OWNED_WORKER_CONTEXT")
    def read(name):
        path=c.ROOT/name
        for parent in (path.parent,*path.parent.parents):
            metadata.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_WORKER_ANCESTORS")
            if parent==c.ROOT:break
        metadata.require(path.is_file() and not path.is_symlink() and not path.is_junction(),"DIRECT_WORKER_METADATA_FILE")
        with path.open("rb") as stream:raw=stream.read(16385)
        metadata.require(0<len(raw)<=16384,"BOUNDED_WORKER_METADATA_BYTES")
        return raw
    def unique(pairs):
        row={}
        for key,value in pairs:
            metadata.require(key not in row,"NO_DUPLICATE_WORKER_HINT_KEY");row[key]=value
        return row
    name=f"implementation/p09/evidence/p09-361-case{index}-successor-worker-bootstrap{run:03}.v1.json"
    hint=json.loads(read(name).decode("ascii"),object_pairs_hook=unique)
    validate_worker_hint(hint,task)
    wire=read(hint["capsule_pin"]["path"])
    graph,proof=reconstruct_worker_graph(c.ROOT,loader,scope,bytes_policy,hint,wire,lambda:None)
    window.M.base.configure(index)
    template,names,proof=connect_factory(c.ROOT,loader,window,index,run,lambda:None)
    execute,state,policy,proof=compose_worker(template,graph,c.ROOT,lambda:None)
    return execute(task)


def compose_parent(template,graph,binding_callback,checkpoint):
    """Connect the real whole engine to the same private Binding and Frame."""
    checkpoint();metadata.require(callable(template) and callable(binding_callback),"PARENT_FACTORY_AND_BINDING")
    engine,proof=template()
    original_run=engine.run_owned;original_worker=engine.worker
    env=original_run.__globals__
    metadata.require(all(n in env for n in ("binding","native","runtime_budget","SELF","TEST")),"PARENT_WHOLE_BINDING_INTERFACE")
    env.update(SELF=SELF,TEST=TEST,binding=binding_callback)
    original_worker.__globals__.update(SELF=SELF,TEST=TEST)
    connected,state=graph.parent.connect_engine(engine,graph.binding)
    metadata.require(state.original is original_run and state.original_worker is original_worker,
        "SAME_WHOLE_ENGINE_AND_WORKER_NOT_REPLACED")
    metadata.require(connected.run_owned.__globals__ is env and connected.worker is original_worker,
        "SAME_PRIVATE_PARENT_ENVIRONMENT")
    checkpoint()
    return connected,state,dict(proof,original_whole_engine_and_worker_retained=True,
        actual_current_binding_callback_connected=True,current_parent_binding_namespace_shared=True,
        actual_parent_Native_product_or_GO_qualified=False)


def compose_worker(template,graph,root,checkpoint):
    """Original worker body under the once-only current policy connector."""
    checkpoint();engine,proof=template();worker=engine.worker
    worker.__globals__.update(SELF=SELF,TEST=TEST)
    policy=graph.worker.raw_policy.Policy(root,graph.binding,lambda:True,checkpoint)
    execute,state=graph.worker.connect_worker(worker,policy)
    metadata.require(state.original is worker,"ORIGINAL_CURRENT_WORKER_BODY")
    return execute,state,policy,dict(proof,whole_original_worker_body_retained=True,
        current_exact_task_and_once_only_policy_connected=True,
        no_historical_receipt_read_added=True,actual_worker_Native_product_or_GO_qualified=False)


def current_input_scope(q,graph,step,report_pin,manifest_pin,source_pins):
    """Actual parent metadata admission; execution CODE/preflight are separate."""
    import copy
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import current_queue_successor_binding as bindings
    import re
    q.checkpoint()
    index=step["index"]
    metadata.require(type(index) is int and 161<=index<=249 and graph.binding.next_case==index,"PARENT_EXACT_CURRENT_STEP")
    a.exact(q.pin(f"implementation/p09/evidence/p09-361-case{index}-step-config001.v1.json"),source_pins[f"implementation/p09/evidence/p09-361-case{index}-step-config001.v1.json"],"CURRENT_STEP_PIN")
    report=a.read_exact(q,report_pin)
    a.fields(report,dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",index=index,
        cleanup_confirmed=True,accepted_count_delta=0,product_or_Native_executed=False,GO_authorized=False),"CURRENT_PARENT_GRAPH_PREPARATION")
    a.exact(report["step"],step,"SAME_PARENT_AND_WORKER_STEP")
    a.exact(report["manifest_pin"],manifest_pin,"CURRENT_PARENT_MANIFEST_PIN")
    metadata.require(report["fresh_inputs"]==report["final_fresh_hashes"],"ALL_GRAPH_PREPARATION_CLOSING_HASHES")
    for pin in report["source_pins"]:
        a.exact(q.pin(pin["path"]),pin,"UNCHANGED_CURRENT_PREPARED_GRAPH_DEPENDENCIES")
    for pin in source_pins.values():a.exact(q.pin(pin["path"]),pin,"ALL_EXPLICIT_CURRENT_PARENT_SOURCES")
    manifest=a.read_exact(q,manifest_pin)
    a.exact(manifest["descriptors"],graph.binding.descriptors(),"SAME_ALL_PARENT_AND_WORKER_DESCRIPTORS")
    a.exact(dict(graph.binding.manifest_pin),manifest_pin,"SAME_ACTUAL_PARENT_MANIFEST")
    a.exact(q.pin(report["capsule_pin"]["path"]),report["capsule_pin"],"CAPSULE_IN_ACTUAL_PARENT_SCOPE")
    authority=a.read_exact(q,step["prior_queue_pin"]);prior=a.read_exact(q,step["prior_candidate_pin"])
    listing=a.read_exact(q,scope.LIST_PIN)
    # Use the exact already-declared function body, not another default module
    # import. All source bytes stay in the same Native/qualifier scope.
    step_source_name="tools/p09/prepare_current_queue_step.py"
    step_sources=scope.pins(report["source_pins"])
    raw=q.text(step_source_name)
    a.exact(q.snapshots[step_source_name],step_sources[step_source_name],"EXACT_ORIGINAL_STEP_DERIVATION_SOURCE")
    steps=a.native.definitions(raw,("derive_step",),dict(re=re))
    a.exact(steps.derive_step(index,step["prior_queue_pin"],authority,prior,listing["source_test_names"]),step,
        "APPROVED_PREDECESSOR_AND_FULL_COMPILED_LIST")
    representation=prior["source_input_representation"]
    history={k:copy.deepcopy(representation[k]) for k in bindings.PROVENANCE_KEYS if k in representation}
    a.exact(manifest["historical_predecessor_provenance"],history,"ORIGINAL_HISTORICAL_LINEAGE_NOT_CURRENT_ACCEPTANCE")
    for pin in prior["bootstrap_metadata"]["input_pins"]:
        a.exact(q.pin(pin["path"]),pin,"ALL_ORIGINAL_INITIAL_BOOTSTRAP_SOURCES")
    required=bindings.inherited_scope(scope,representation,authority["fresh_input_pins"],q.snapshots,q.checkpoint)
    required,aliases=graph.binding.semantic_union(required,q.checkpoint)
    current=scope.listing_inputs(listing)
    rust={n for n in current if n.startswith(("crates/","protocol/generated/rust/","tools/xtask/"))
        and (n.endswith(".rs") or n.endswith("/Cargo.toml"))}
    metadata.require(len(rust)==787 and required[scope.EXE_PIN["path"]]==scope.EXE_PIN,"CURRENT_RUST787_AND_BINARY")
    q.checkpoint()
    return required,rust


def connect_factory(root,loader,window,index,run,checkpoint):
    metadata.require(type(index) is int and 161<=index<=249 and type(run) is int and 2<=run<=8,"CLOSED_TEMPLATE_CONTEXT")
    checkpoint()
    namespaces,proofs=loader.load(root,PINS,{})
    original=namespaces.reviewed_case158_attempt_v3
    identity=namespaces.reviewed_case158_attempt_v4
    task=f"case{index}-current-r{run:03}-tests"
    path=f"implementation/p09/evidence/p09-361-case{index}-current-runtime-run{run:03}.v1.json"
    values=dict(INDEX=index,PHYSICAL_RUN=run,TASK=task,ROOT=path)
    first=original.connect_template
    factory=metadata.project(first,dict(first.__globals__,**values),{158:index,2:run})
    template,proof=factory(window)
    retry=template.__globals__["OLD17"].template.__globals__["OLD16"].template.__globals__["OLD15"].template.__globals__["RETRY"]
    old_identity=identity.identity
    name_factory=metadata.project(old_identity,dict(old_identity.__globals__,**values),{2:run})
    names=name_factory(retry)
    metadata.require(names.physical_run(index)==retry.physical_run(index)==run,"ONE_PHYSICAL_ADAPTER_AND_IDENTITY")
    metadata.require(names.root_path(NS(index=index))==path and names.task(index)==task and names.public_run(index,run)==1,
        "EXACT_CURRENT_ROOT_TASK_AND_LOGICAL_RUN")
    checkpoint()
    return template,names,dict(proof,current_index=index,physical_product_run=run,task=task,root_path=path,
        original_template_chain_code_defaults_and_closures_retained=True,
        original_single_argument_adapter_not_stacked=True,original_identity_entire_code_inverse=True,
        source_proofs=proofs,current_engine_constructed=False,actual_Native_product_or_GO_qualified=False)


def qualify_factory(index,run,connection_attempt,attempt,startup_only=False):
    """Bounded real engine construction witness, not runtime authorization."""
    import io
    import json
    import os
    from pathlib import Path
    import re
    import sys
    import time
    import unittest
    import subprocess
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    # Script execution puts tools/p09, not the repository, on sys.path[0].
    # The named unittest package must resolve to this checked repository.
    sys.path.insert(0,str(c.ROOT))
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import runtime_envelope_namespace_bundle_v1 as loader
    import current_queue_successor_binding as bindings
    import owned_source_read_pressure as bytes_policy
    import case160_run007_controller as old
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    metadata.require(type(index) is int and 161<=index<=249 and type(run) is int and 2<=run<=8,"FACTORY_QUALIFICATION_CONTEXT")
    metadata.require(all(type(v) is int and 1<=v<=8 for v in (connection_attempt,attempt)),"FACTORY_QUALIFICATION_ATTEMPTS")
    output=c.ROOT/f"implementation/p09/evidence/p09-361-case{index}-successor-factory{attempt:03}.v1.json"
    metadata.require(not output.exists(),"EXCLUSIVE_FACTORY_QUALIFICATION")
    guard=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    out=dict(state="FAILED_SUCCESSOR_FACTORY_NOT_ADOPTED",index=index,accepted_count_delta=0,
        product_or_Native_executed=False,GO_authorized=False,P09_gate="OPEN")
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,TEST,metadata.SELF,metadata.TEST,loader.SELF):q.pin(name)
        for pin in PINS:a.exact(q.pin(pin["path"]),pin,"EXACT_FACTORY_ORIGINAL_SOURCE")
        report_name=f"implementation/p09/evidence/p09-361-case{index}-successor-connections{connection_attempt:03}.v1.json"
        report=q.json(report_name)
        a.fields(report,dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",
            index=index,cleanup_confirmed=True,accepted_count_delta=0,product_or_Native_executed=False,GO_authorized=False),"REAL_CURRENT_CONNECTION_PREPARATION")
        metadata.require(report["fresh_inputs"]==report["final_fresh_hashes"],"COMPLETE_CONNECTION_CLOSING_HASHES")
        sealed=scope.pins(report["source_pins"])
        for name in (metadata.SELF,metadata.TEST):a.exact(q.pin(name),sealed[name],"UNCHANGED_CURRENT_CONNECTION_SOURCES")
        manifest=a.read_exact(q,report["manifest_pin"])
        a.exact(q.pin(report["capsule_pin"]["path"]),report["capsule_pin"],"REAL_CURRENT_WORKER_WIRE")
        step=q.json(f"implementation/p09/evidence/p09-361-case{index}-step-config001.v1.json")
        a.exact(step,report["step"],"FACTORY_STEP_AND_CURRENT_PREPARATION")
        a.exact(report["task"],f"case{index}-current-r{run:03}-tests","FACTORY_AND_WORKER_TASK")
        prior=a.read_exact(q,step["prior_candidate_pin"])
        pinned=scope.pins(prior["source_input_representation"]["semantic_source_freeze"])
        original_window=old.old.prior
        for name in (original_window.SELF,original_window.TEST,old.SELF,old.TEST):
            a.exact(q.pin(name),pinned[name],"UNCHANGED_QUALIFIED_WHOLE_WINDOW_CONSTRUCTION")
        suite=unittest.defaultTestLoader.loadTestsFromName("tools.p09.tests.test_current_queue_successor_runtime")
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        out["contracts"]=contracts
        a.exact(contracts,dict(run=11,errors=0,failures=0,skipped=0),"ALL_FACTORY_CONTRACTS")
        guard.check(force=True);old.old.base.configure(index)
        template,names,proof=connect_factory(c.ROOT,loader,original_window,index,run,guard.check)
        engine,engine_proof=template()
        metadata.require(callable(engine.run_owned) and callable(engine.worker),"REAL_WHOLE_ENGINE_AND_WORKER_CONSTRUCTED")
        metadata.require(all(n in engine.run_owned.__globals__ for n in ("binding","native","SELF","TEST","runtime_budget")),
            "REAL_ENGINE_CURRENT_BINDING_INTERFACE")
        representation=prior["source_input_representation"]
        history={k:representation[k] for k in bindings.PROVENANCE_KEYS if k in representation}
        module,binding_proof=bindings.connect(c.ROOT,loader,scope,index,history,representation["descriptors"])
        bound=module.Binding(manifest["descriptors"],report["manifest_pin"],next_case=index)
        graph,graph_proof=metadata.connect(c.ROOT,loader,bytes_policy,module,bound,step,run,guard.check)
        hint=worker_hint(step,run,report["capsule_pin"],report["manifest_pin"],manifest,representation["descriptors"])
        hint_name=f"implementation/p09/evidence/p09-361-case{index}-successor-worker-bootstrap{run:03}.v1.json"
        hint_raw=(json.dumps(hint,ensure_ascii=True,allow_nan=False,separators=(",",":"))+"\n").encode("ascii")
        metadata.require(0<len(hint_raw)<=16384,"ORIGINAL_BOUNDED_WORKER_HINT")
        import hashlib
        hint_pin=dict(path=hint_name,bytes=len(hint_raw),sha256=hashlib.sha256(hint_raw).hexdigest())
        hint_path=c.ROOT/hint_name
        if not hint_path.exists():
            for parent in (hint_path.parent,*hint_path.parent.parents):
                metadata.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_HINT_ANCESTORS")
                if parent==c.ROOT:break
            guard.check(force=True)
            with hint_path.open("xb") as stream:
                metadata.require(stream.write(hint_raw)==len(hint_raw),"ALL_WORKER_HINT_BYTES");stream.flush();os.fsync(stream.fileno())
        a.exact(q.fresh_pin(hint_name),hint_pin,"ACTUAL_WORKER_HINT_BYTES")
        declared=dict(q.snapshots)
        callback=lambda reader:current_input_scope(reader,graph,step,q.snapshots[report_name],report["manifest_pin"],declared)
        required,rust=(None,None) if startup_only else callback(q)
        parent,parent_state,parent_proof=compose_parent(lambda:(engine,engine_proof),graph,callback,guard.check)
        worker,worker_state,policy,worker_proof=compose_worker(template,graph,c.ROOT,guard.check)
        metadata.require(parent_state.attempts==worker_state.attempts==0 and not parent_state.frames,"NO_RUNTIME_DISPATCH_DURING_PREPARATION")
        model=None if startup_only else bound.runtime_budget(required,167,original_window.DIRECT.runtime_budget,guard.check)
        # A separate bounded Python startup receives EOF, never the original GO.
        # Audit only counts historical runtime/authority opens; paths/logs stay private.
        audit_program="""import json,os,re,runpy,sys
hits=[]
def audit(event,args):
 if event=='open' and args and isinstance(args[0],(str,bytes,os.PathLike)):
  name=os.fsdecode(os.fspath(args[0])).replace('\\\\','/').rsplit('/',1)[-1]
  if re.fullmatch(r'p09-361-case[0-9]{3}-current-(?:runtime-run[0-9]{3}|epoch-accept[0-9]{3})\\.v1\\.json',name):hits.append(1)
sys.addaudithook(audit)
path=sys.argv[1];sys.argv=sys.argv[1:];sys.path.insert(0,os.path.dirname(path))
try:runpy.run_path(path,run_name='__main__')
finally:print(json.dumps({'historical_runtime_or_authority_opens':len(hits)}))
"""
        guard.check(force=True)
        child=subprocess.run([sys.executable,"-B","-c",audit_program,str(c.ROOT/SELF),"--owned-worker","--task",names.task(index)],
            input="",text=True,encoding="utf-8",errors="replace",capture_output=True,timeout=15,cwd=c.ROOT,
            creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW)
        metadata.require(len(child.stdout.encode("utf-8"))<=4096 and len(child.stderr.encode("utf-8"))<=16384,"BOUNDED_NO_GO_STARTUP_OUTPUT")
        audit_result=json.loads(child.stdout.strip())
        metadata.require(child.returncode!=0 and "WORKER_NOT_AUTHORIZED" in child.stderr,"ORIGINAL_GO_REJECTION_BEFORE_PRODUCT")
        a.exact(audit_result,dict(historical_runtime_or_authority_opens=0),"NO_HISTORICAL_RECEIPT_IO_IN_WORKER_STARTUP")
        guard.check(force=True)
        q.finish();guard.check(force=True)
        out.update(state=("PASS_WORKER_CLI_NO_GO_STARTUP_NOT_PARENT_ADMISSION_NATIVE_OR_PRODUCT" if startup_only else
            "CONSTRUCTED_REAL_SUCCESSOR_ENGINE_FACTORY_NOT_WHOLE_CODE_PREFLIGHT_NATIVE_OR_GO"),
            contracts=contracts,connection_report_pin=q.snapshots[report_name],manifest_pin=report["manifest_pin"],
            capsule_pin=report["capsule_pin"],task=names.task(index),root_path=names.root_path(old.old.base.CONFIG),
            factory_proof=proof,whole_original_engine_construction_proof=engine_proof,
            worker_body_origin=engine.worker.__code__.co_filename,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,source_pins=list(q.snapshots.values()),
            whole_current_imported_closure_and_cost_NOT_qualified=True,
            current_parent_readonly_input_admission=not startup_only,current_worker_policy_callable_connected=True,
            worker_bootstrap_pin=hint_pin,worker_cli_NO_GO_rejection=dict(exit_code=child.returncode,
                original_GO_rejection_observed=True,historical_runtime_or_authority_opens=0,
                GO_sent=False,product_child_execution_authorized=False,full_worker_product_qualification=False),
            parent_composition_proof=parent_proof,worker_composition_proof=worker_proof,
            prepared_semantic_inputs=None if startup_only else len(required),prepared_Rust_inputs=None if startup_only else len(rust),
            prepared_scope_cost=model,full_current_parent_admission_deferred_to_whole_preflight=startup_only,
            actual_parent_and_worker_dispatch_counts=dict(parent=parent_state.attempts,worker=worker_state.attempts),
            owned_worker_cli_startup_connected=True,independent_whole_oracle_and_actual_GO_dispatch_NOT_qualified=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError,subprocess.TimeoutExpired) as error:
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):out["error_code"]=error.args[0]
    finally:
        guard.close();out.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((r["system_cpu_percent"] for r in guard.samples),default=None),
            RAM_min=min((r["available_ram_percent"] for r in guard.samples),default=None))
    metadata.require(guard.cleanup,"FACTORY_QUALIFICATION_CLEANUP")
    raw=(json.dumps(out,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8")
    metadata.require(0<len(raw)<=262144,"BOUNDED_FACTORY_REPORT")
    for parent in (output.parent,*output.parent.parents):
        metadata.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_FACTORY_ANCESTORS")
        if parent==c.ROOT:break
    with output.open("xb") as stream:metadata.require(stream.write(raw)==len(raw),"ALL_FACTORY_REPORT_BYTES");stream.flush();os.fsync(stream.fileno())
    print(json.dumps({k:out.get(k) for k in ("state","contracts","root_path","fresh_inputs","final_fresh_hashes",
        "elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if out["state"].startswith(("CONSTRUCTED_","PASS_")) else 1


if __name__=="__main__":
    import argparse
    import sys
    if len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]:
        raise SystemExit(owned_worker_entry(sys.argv[3]))
    parser=argparse.ArgumentParser();parser.add_argument("--case",type=int,required=True);parser.add_argument("--run",type=int,required=True)
    parser.add_argument("--connections-attempt",type=int,required=True);parser.add_argument("--qualification-attempt",type=int,required=True)
    parser.add_argument("--startup-only",action="store_true")
    args=parser.parse_args();raise SystemExit(qualify_factory(args.case,args.run,args.connections_attempt,args.qualification_attempt,args.startup_only))
