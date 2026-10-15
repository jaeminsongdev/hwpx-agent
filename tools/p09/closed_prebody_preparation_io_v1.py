"""Reuse qualified preparation IO on the current closed-source entry.

No Native/GO/product entry. Keep the original whole preflight, complete fresh
closing reads, Rust inventory, imported-helper cap and decoder5 limit.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import sys

SELF="tools/p09/closed_prebody_preparation_io_v1.py"
SETUP_IO=[
    dict(path="tools/p09/reusable_audit_chunk_v1.py",bytes=8088,sha256="1aa1db74585cbdf50df32ac0c9dc07dfd31557fc37647ca6e6ea3969fbb60e75"),
    dict(path="tools/p09/single_snapshot_source_guard_v1.py",bytes=4560,sha256="f3555f4395154be7c929e76eeb451226402b49cc54b0ab6da335ba94555eae43")]


def require(ok,label):
    if not ok:raise ValueError("CLOSED_PREPARATION_IO_"+label)


def main():
    import argparse,json,time
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_envelope_runtime_v25 as envelope
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import successor_preparation_workspace_v1 as publisher
    import audit_evidence_io as original_io
    parser=argparse.ArgumentParser()
    for name in ("case","run","attempt"):parser.add_argument("--"+name,type=int,required=True)
    parser.add_argument("--code-attempt",type=int,default=1)
    parser.add_argument("--preflight-attempt",type=int,default=1)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight",action="store_true");mode.add_argument("--qualify",action="store_true")
    mode.add_argument("--repair-graph",action="store_true")
    args=parser.parse_args()
    require(165<=args.case<=249 and 4<=args.run<=8 and all(1<=n<=8 for n in
        (args.attempt,args.code_attempt,args.preflight_attempt)),"CLOSED_PREPARATION_CONTEXT")
    prefix=f"implementation/p09/evidence/p09-361-case{args.case}-"
    stage="graph" if args.repair_graph else "preflight" if args.preflight else "qualify"
    setup_name=prefix+f"closed-io-{stage}-setup-run{args.run:03}-attempt{args.attempt:03}.v1.json"
    diagnostic_name=prefix+f"closed-io-{stage}-run{args.run:03}-attempt{args.attempt:03}.v1.json"
    target=prefix+"successor-"+(f"connections{args.run:03}.v6.json" if args.repair_graph else
        f"preflight-run{args.run:03}-attempt{args.attempt:03}.v1.json" if args.preflight
        else f"dispatch-qualification-run{args.run:03}-attempt{args.attempt:03}.v1.json")
    require(all(not (c.ROOT/name).exists() for name in (setup_name,diagnostic_name,target)),"EXCLUSIVE_STAGE_NO_REPLAY")
    if args.repair_graph:require(not (c.ROOT/(prefix+f"successor-worker-bootstrap{args.run:03}.v6.json")).exists(),"EXCLUSIVE_REQUALIFIED_BOOTSTRAP")
    guard=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    setup=dict(state="FAILED_CLOSED_PREPARATION_IO_SETUP_NOT_ADOPTED",product_or_Native_executed=False,accepted_count_delta=0)
    code35=prefix+"preparation-rust-inventory-code004.v1.json"
    code10=prefix+"preparation-single-snapshot-code001.v1.json"
    code17=prefix+"preparation-workspace-code001.v1.json"
    q=None;setup_phase="resource_admission"
    try:
        guard.acquire();setup_phase="qualified_setup_reader"
        setup_helpers,_=envelope.namespace_bundle.load(c.ROOT,SETUP_IO,{"audit_evidence_io":original_io})
        raw_leaf=(c.ROOT/setup_helpers.reusable_audit_chunk_v1.ORIGINAL_PIN["path"]).read_bytes()
        setup_workspace,_=setup_helpers.reusable_audit_chunk_v1.reader_type(a.AcceptanceReader,raw_leaf)
        setup_reader,_=setup_helpers.single_snapshot_source_guard_v1.reader_type(setup_workspace,raw_leaf)
        q=setup_reader(c.ROOT,guard.check);q.pin(SELF)
        for pin in SETUP_IO:a.exact(q.pin(pin["path"]),pin,"EXACT_SETUP_IO_HELPERS")
        a.exact(q.pin(setup_helpers.reusable_audit_chunk_v1.ORIGINAL_PIN["path"]),setup_helpers.reusable_audit_chunk_v1.ORIGINAL_PIN,"EXACT_SETUP_LEAF")
        setup_phase="current_component_qualifications"
        qualifications=[]
        for name,state,count in ((code35,"PASS_PREPARATION_RUST_INVENTORY_CODE35_NOT_NATIVE_OR_PRODUCT",35),
            (code10,"PASS_PREPARATION_SINGLE_SNAPSHOT_CODE10_NOT_NATIVE_OR_PRODUCT",10),
            (code17,"PASS_PREPARATION_WORKSPACE_CODE_NOT_NATIVE_OR_PRODUCT",17)):
            row=q.json(name)
            a.fields(row,dict(state=state,contracts=dict(run=count,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"EXACT_CURRENT_IO_QUALIFICATION")
            require(row["fresh_inputs"]==row["final_fresh_hashes"]>0,"COMPLETE_IO_CODE_HASHES")
            for pin in row["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_QUALIFIED_IO_SOURCE")
            qualifications.append(row)
        pins=scope.pins(qualifications[0]["source_pins"])
        for row in qualifications[1:]:pins=scope.extend(pins,scope.pins(row["source_pins"]))
        selected=[pins["tools/p09/"+name+".py"] for name in ("preparation_rust_inventory_snapshot_v1",
            "rust_inventory_single_snapshot_v1","fresh_lossless_metadata_reader_v1","single_snapshot_source_guard_v1","reusable_audit_chunk_v1")]
        helpers,_=envelope.namespace_bundle.load(c.ROOT,selected,{"audit_evidence_io":original_io})
        preparation=helpers.preparation_rust_inventory_snapshot_v1
        snapshot=helpers.rust_inventory_single_snapshot_v1
        fresh=helpers.fresh_lossless_metadata_reader_v1
        source_guard=helpers.single_snapshot_source_guard_v1
        scratch=helpers.reusable_audit_chunk_v1
        raw_pin,raw_buffer=q._read(scratch.ORIGINAL_PIN["path"],parse=True);q._bind(raw_pin["path"],raw_pin)
        a.exact(raw_pin,scratch.ORIGINAL_PIN,"EXACT_IO_LEAF");leaf_raw=bytes(raw_buffer)
        rust_pin,rust_buffer=q._read(snapshot.ORIGINAL_PIN["path"],parse=True);q._bind(rust_pin["path"],rust_pin)
        a.exact(rust_pin,snapshot.ORIGINAL_PIN,"EXACT_RUST_INVENTORY_LEAF");rust_raw=bytes(rust_buffer)
        setup_phase="current_entry_and_transport"
        code=q.json(prefix+f"successor-code-run{args.run:03}-attempt{args.code_attempt:03}.v1.json")
        a.fields(code,dict(state="PASS_CURRENT_SUCCESSOR_CODE_NOT_FULL_PREFLIGHT_NATIVE_OR_PRODUCT",index=args.case,
            physical_run=args.run,contracts=dict(run=74,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"UNCHANGED_CURRENT_CODE74")
        current=scope.pins(code["source_pins"])
        entry_pin=current["tools/p09/closed_prebody_factory_admission_fix_v1.py"]
        a.exact(q.pin(entry_pin["path"]),entry_pin,"QUALIFIED_CURRENT_ENTRY")
        entry_names,_=envelope.namespace_bundle.load(c.ROOT,[entry_pin],{})
        entry=entry_names.closed_prebody_factory_admission_fix_v1
        ctx=NS(preflight=prefix+f"successor-preflight-run{args.run:03}-attempt{(args.attempt if args.preflight else args.preflight_attempt):03}.v1.json",
            qualification=prefix+f"successor-dispatch-qualification-run{args.run:03}-attempt{args.attempt:03}.v1.json")
        linked=entry.load(c.ROOT,a,scope,bytes_policy,envelope,prefix+"sealed-metadata-code001.v1.json",ctx=ctx)
        report_name=prefix+f"successor-connections{args.run:03}.{'v4' if args.repair_graph else 'v6'}.json"
        report=q.json(report_name)
        a.fields(report,dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",
            index=args.case,cleanup_confirmed=True,accepted_count_delta=0,product_or_Native_executed=False,GO_authorized=False),"EXACT_GRAPH_PREPARATION")
        require(report["fresh_inputs"]==report["final_fresh_hashes"]>0,"GRAPH_CLOSED_HASHES")
        if args.repair_graph:
            import re
            for pin in report["source_pins"]:a.exact(q.pin(pin["path"]),pin,"ALL_CURRENT_BASE_GRAPH_SOURCES")
            selection=q.json(prefix+"successor-selection001.v1.json")
            a.fields(selection,dict(state="PREPARED_EXACT_SUCCESSOR_STEP_AND_RECEIPT_SELECTION_NOT_RUNTIME_OR_GO",
                cleanup_confirmed=True,accepted_count_delta=0),"ORIGINAL_STEP_SELECTION_AUTHORITY")
            require(selection["fresh_inputs"]==selection["final_fresh_hashes"]>0,"SELECTION_CLOSED_HASHES")
            selected=scope.pins(selection["fresh_input_pins"])
            for name in ("tools/p09/prepare_current_queue_step.py","tools/p09/tests/test_prepare_current_queue_step.py"):
                a.exact(q.pin(name),selected[name],"STEP_SOURCE_AND_TEST_FROM_ORIGINAL_SELECTION")
            step=report["step"]
            authority=a.read_exact(q,step["prior_queue_pin"]);prior=a.read_exact(q,step["prior_candidate_pin"])
            listing=a.read_exact(q,scope.LIST_PIN)
            steps=a.native.definitions(q.text("tools/p09/prepare_current_queue_step.py"),("derive_step",),dict(re=re))
            a.exact(steps.derive_step(args.case,step["prior_queue_pin"],authority,prior,listing["source_test_names"]),step,"WHOLE_ORIGINAL_STEP_REDERIVED")
        manifest=a.read_exact(q,report["manifest_pin"])
        hint=q.json(prefix+f"successor-worker-bootstrap{args.run:03}.v4.json")
        wire_pin,wire=q._read(report["capsule_pin"]["path"],parse=True);q._bind(wire_pin["path"],wire_pin)
        a.exact(wire_pin,report["capsule_pin"],"ACTUAL_CURRENT_WIRE")
        runtime=linked.modules.current_queue_successor_runtime;bindings=linked.modules.current_queue_successor_binding
        graph,_=linked.transport.reconstruct(runtime,bindings,c.ROOT,envelope.namespace_bundle,scope,bytes_policy,hint,bytes(wire),guard.check,linked.alias)
        a.exact(graph.binding.descriptors(),manifest["descriptors"],"EXACT_CURRENT_DECLARED_ALL_MAPPING_ROWS")
        producer=manifest["closed_prebody_source_policy"]["producer_pin"]
        setup_phase="full_closed_original_admission"
        policy=linked.alias.verify(q,producer,args.case,args.run,a,scope,linked.bridge,graph.binding_module.source.codec,graph.binding_module.source.SCHEMA)
        a.exact(policy.evidence(),hint[linked.transport.FIELD],"INDEPENDENTLY_ADMITTED_SETUP_DECLARATION")
        semantic=scope.pins([d["semantic_original_pin"] for d in graph.binding.descriptors()]+[report["manifest_pin"]])
        projection,_=graph.binding.project(semantic,guard.check)
        budget_type=graph.frames.connection.original.DecoderBudget
        setup_phase="final_fresh_hashes"
        q.finish();guard.check(force=True)
        if args.repair_graph:
            completed=dict(report,source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
                base_graph_report_pin=q.snapshots[report_name],step_source_requalified_from_original_selection=True,
                all_old_source_pins_retained_and_currently_rechecked=True)
        setup.update(state="PASS_CLOSED_PREPARATION_IO_SETUP_NOT_NATIVE_OR_PRODUCT",source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,pair_count=len(graph.binding.descriptors()))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        import re
        setup["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):setup["error_code"]=error.args[0]
    finally:
        guard.close();setup.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            last_setup_phase=setup_phase,
            actual_read_passes=None if q is None else q.read_passes,actual_bytes_read=None if q is None else q.bytes_read,
            parent_resource_tail=[{k:s.get(k) for k in ("system_cpu_percent","parent_cpu_machine_percent","parent_private_mib",
                "available_ram_percent","commit_used_percent")} for s in guard.samples[-3:]],
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"SETUP_CLEANUP");publisher.publish(c.ROOT,setup_name,setup,a)
    if not setup["state"].startswith("PASS_"):
        print(json.dumps({key:setup.get(key) for key in ("state","error_code","error_type","CPU_max","RAM_min","cleanup_confirmed")}));return 1
    if args.repair_graph:
        completed.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=setup["elapsed_seconds"],
            CPU_max=setup["CPU_max"],RAM_min=setup["RAM_min"])
        publisher.publish(c.ROOT,target,completed,a)
        hint_name=prefix+f"successor-worker-bootstrap{args.run:03}.v6.json"
        publisher.publish(c.ROOT,hint_name,hint,a)
        print(json.dumps(dict(state="PREPARED_REQUALIFIED_GRAPH_STEP_SOURCES_NOT_NATIVE_OR_PRODUCT",graph=target,
            fresh_inputs=setup["fresh_inputs"],final_fresh_hashes=setup["final_fresh_hashes"],cleanup_confirmed=guard.cleanup)))
        return 0
    workspace,_=scratch.reader_type(a.AcceptanceReader,leaf_raw)
    guarded,_=source_guard.reader_type(workspace,leaf_raw)
    api,lossless_summary=preparation.lossless_api(NS(**{**vars(a),"AcceptanceReader":guarded}),fresh,projection,graph.binding.descriptors(),budget_type)
    api,readers=preparation.reader_api(api,snapshot,code35)
    base=api.AcceptanceReader
    class Reader(base):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            row=self.json(setup_name)
            a.fields(row,dict(state="PASS_CLOSED_PREPARATION_IO_SETUP_NOT_NATIVE_OR_PRODUCT",cleanup_confirmed=True),"CURRENT_CLOSED_IO_SETUP")
            require(row["fresh_inputs"]==row["final_fresh_hashes"]>0,"COMPLETE_SETUP_HASHES")
            for pin in row["source_pins"]:a.exact(self.pin(pin["path"]),pin,"CURRENT_SETUP_SOURCE")
    api=NS(**{**vars(api),"AcceptanceReader":Reader})
    linked=entry.load(c.ROOT,api,scope,bytes_policy,envelope,prefix+"sealed-metadata-code001.v1.json",ctx=ctx)
    runtime=linked.modules.current_queue_successor_runtime;controller=linked.modules.current_queue_successor_controller
    # Metadata-only graph/bootstrap receipt namespace, with an entire inverse.
    # Capsule pin and all source/Frame/worker validation bodies stay unchanged.
    def current_graph_paths(namespace,names):
        metadata=runtime.metadata
        for name in names:
            fn=getattr(namespace,name)
            require(sum(type(v) is str and v==".v4.json" for v in fn.__code__.co_consts)==1,"ONE_GRAPH_NAMESPACE_LITERAL")
            new=metadata.project(fn,dict(fn.__globals__),{".v4.json":".v6.json"})
            fn.__globals__[name]=new;setattr(namespace,name,new)
    current_graph_paths(controller,("run_preflight",))
    current_graph_paths(linked.modules.current_queue_successor_dispatch,("construct","prepare_bootstrap"))
    traces=[preparation.connect(runtime,snapshot,rust_raw)]
    def configure(runtime,q):
        traces.append(preparation.connect(runtime,snapshot,rust_raw))
    linked.connection.connect_dynamic(linked.modules.current_queue_successor_dispatch,configure)
    original=controller.run_preflight
    controller.run_preflight,compact=preparation.compact_report(original)
    exception_sites=[]
    if args.preflight:
        # Only exceptions crossing the unchanged producer frame are recorded.
        # No line/opcode tracing, log contents, source values or extra observer.
        require(sys.gettrace() is None,"NO_EXISTING_TRACE_TO_REPLACE")
        def trace(frame,event,arg):
            if frame.f_code is not controller.run_preflight.__code__:return None
            frame.f_trace_lines=False;frame.f_trace_opcodes=False
            if event=="exception" and len(exception_sites)<8:
                import re
                kind,error,tb=arg
                field=getattr(error,"name",None)
                if field is None and kind is KeyError and error.args:field=error.args[0]
                while tb is not None and tb.tb_next is not None:tb=tb.tb_next
                origin=None if tb is None else tb.tb_frame.f_code.co_filename.replace("\\","/")
                if origin is not None and "tools/p09/" in origin:origin="tools/p09/"+origin.split("tools/p09/",1)[1]
                else:origin=None
                exception_sites.append(dict(type=kind.__name__,line=frame.f_lineno,origin=origin,
                    origin_line=None if tb is None else tb.tb_lineno,
                    field=field if type(field) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,100}",field) else None))
            return trace
        sys.settrace(trace)
        try:result=controller.run_preflight(args.case,args.run,args.code_attempt,args.attempt)
        finally:sys.settrace(None)
    else:
        dispatch=linked.modules.current_queue_successor_dispatch
        result=dispatch.main(dispatch.context(args.case,args.run,args.code_attempt,args.preflight_attempt,args.attempt),True)
    reader_rows=[dict(scratch.summary(reader),source_snapshot=reader.source_snapshot_diagnostics(),
        fresh_inputs=len(reader.snapshots),final_fresh_hashes=reader.final_fresh_hashes,
        actual_read_passes=reader.read_passes,actual_bytes_read=reader.bytes_read) for reader in readers]
    diagnostic=dict(state="RECORDED_ACTUAL_CLOSED_PREPARATION_IO_NOT_NATIVE_OR_PRODUCT",stage=stage,stage_exit_code=result,
        readers=reader_rows,lossless_metadata=lossless_summary() if readers else None,Rust_inventory_traces=[t.summary() for group in traces for t in group],
        producer_exception_sites=exception_sites,exception_only_target_frame_no_line_or_opcode_trace=True,
        compact_final_report_calls=compact.final_report_calls,product_or_Native_executed=False,accepted_count_delta=0)
    publisher.publish(c.ROOT,diagnostic_name,diagnostic,a)
    print(json.dumps(dict(stage=stage,stage_exit_code=result,diagnostic=diagnostic_name,actual_readers=len(reader_rows))))
    return result


if __name__=="__main__":raise SystemExit(main())
