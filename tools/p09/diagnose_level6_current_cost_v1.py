"""Observe the unchanged complete budget; never bypass its Binding rejection.

Only --preflight is accepted. Preserve original diagnostics, no Native or GO.
The extra diagnostic source is accounted separately in the reported model.
"""
from pathlib import Path
import sys

SELF="tools/p09/diagnose_level6_current_cost_v1.py"
ENTRY=dict(path="tools/p09/level6_closed_preparation_v1.py",bytes=18043,
    sha256="ee3fd53477071e61430e19039a0039c9336776ab75228aa28903186137c6b5c6")


def replay_observed(attempt,observed_attempt,apply_prior_policy=False):
    """Exact scope delta replay and a clearly unauthorized coalescing estimate."""
    import hashlib,json,time
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import successor_preparation_workspace_v1 as publisher
    import case160_run007_controller as old
    prefix="implementation/p09/evidence/p09-361-case165-"
    output=prefix+f"level6-observed-scope-replay{attempt:03}.v1.json"
    a.require(1<=attempt<=8 and 1<=observed_attempt<=8 and not (c.ROOT/output).exists(),"EXCLUSIVE_SCOPE_REPLAY")
    guard=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    row=dict(state="FAILED_LEVEL6_SCOPE_REPLAY_NOT_QUALIFICATION",product_or_Native_executed=False,accepted_count_delta=0,
        full_preflight_replayed=False,physical_or_semantic_scope_change_authorized=False,whole_current_source_bytes_rechecked=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF)
        witness_name=prefix+f"level6-current-cost-diagnostic{observed_attempt:03}.v1.json"
        witness=q.json(witness_name)
        a.fields(witness,dict(state="RECORDED_LEVEL6_CURRENT_COST_DIAGNOSTIC_NOT_QUALIFICATION_OR_PRODUCT",
            original_preflight_exit_code=1,original_Binding_budget_predicate_unchanged=True,
            original_budget_object_restored=True,original_trace_setter_restored=True),"ORIGINAL_REJECTION_NOT_BYPASSED")
        observation=witness["observations"][-1]
        a.fields(observation,dict(full_scope_delta_preserved=True,original_model_reproduced_exactly=True),"COMPLETE_ACTUAL_SCOPE_DELTA")
        baseline=a.read_exact(q,witness["baseline_preflight_pin"])
        physical=scope.pins(baseline["complete_physical_source_scope"])
        for name in observation["removed_input_paths"]:
            a.require(name in physical,"REMOVED_BASELINE_INPUT_MUST_EXIST");physical.pop(name)
        for pin in observation["extra_pins"]:
            a.require(pin["path"] not in physical,"EXTRA_INPUT_MUST_BE_NEW");physical[pin["path"]]=pin
        for pin in observation["changed_common_pins"]:
            a.require(pin["path"] in physical,"CHANGED_COMMON_INPUT_MUST_EXIST");physical[pin["path"]]=pin
        physical=scope.pins(list(physical.values()))
        serialized=json.dumps([physical[n] for n in sorted(physical)],ensure_ascii=True,sort_keys=True,separators=(",",":"),allow_nan=False).encode("ascii")
        a.require(len(physical)==observation["actual_inputs"] and hashlib.sha256(serialized).hexdigest()==observation["actual_scope_sha256"],"ENTIRE_ACTUAL_SCOPE_EXACTLY_RECONSTRUCTED")
        cost=old.old.prior.DIRECT.runtime_budget
        actual=cost(physical,observation["inventory_requests"])["predicted_runtime_combined_seconds"]+5.0
        a.exact(actual,observation["observed_original_rejection_total"],"ORIGINAL_REJECTED_COST_EXACTLY_REPRODUCED")
        old_graph=q.json(prefix+"successor-connections004.v9.json");old_manifest=a.read_exact(q,old_graph["manifest_pin"])
        graph=q.json(prefix+"successor-connections007.v9.json");manifest=a.read_exact(q,graph["manifest_pin"])
        current={r["semantic_original_pin"]["path"]:r for r in manifest["descriptors"]}
        duplicate=[];hypothetical=dict(physical)
        for pair in old_manifest["descriptors"]:
            oldpin=pair["physical_envelope_pin"];new=current[pair["semantic_original_pin"]["path"]]
            a.exact(pair["semantic_original_pin"],new["semantic_original_pin"],"SAME_DECLARED_ORIGINAL_NOT_PATH_ONLY")
            newpin=new["physical_envelope_pin"]
            if oldpin!=newpin and oldpin["path"] in physical:
                a.exact(physical[oldpin["path"]],oldpin,"EXACT_OLD_PHYSICAL_DECLARATION")
                a.exact(physical.get(newpin["path"]),newpin,"EXACT_NEW_PHYSICAL_DECLARATION")
                duplicate.append(dict(semantic_original_pin=pair["semantic_original_pin"],old_physical_pin=oldpin,new_physical_pin=newpin))
                hypothetical.pop(oldpin["path"])
        hypothetical_cost=cost(hypothetical,observation["inventory_requests"])["predicted_runtime_combined_seconds"]+5.0
        policy_result=None
        if apply_prior_policy:
            import flat_current_queue_envelope_runtime_v25 as envelope
            qualification=q.json(prefix+"prior-preparation-alias-code001.v1.json")
            a.fields(qualification,dict(state="PASS_PRIOR_PREPARATION_ALIAS_CODE6_NOT_CURRENT_ENTRY_OR_PRODUCT",
                contracts=dict(run=6,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"CURRENT_PRIOR_ALIAS_CODE6")
            a.require(qualification["fresh_inputs"]==qualification["final_fresh_hashes"]>0,"PRIOR_ALIAS_FINAL_HASHES")
            for pin in qualification["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_PRIOR_ALIAS_CODE")
            adapter_pin=next(p for p in qualification["source_pins"] if p["path"]=="tools/p09/prior_preparation_alias_v1.py")
            names,_=envelope.namespace_bundle.load(c.ROOT,[adapter_pin],{})
            adapter=names.prior_preparation_alias_v1
            prior=a.read_exact(q,graph["step"]["prior_candidate_pin"])
            authority=a.read_exact(q,graph["step"]["prior_queue_pin"])
            a.fields(authority,dict(accepted_count_after=158,next_runtime_index=165,
                runtime_candidate_pin=graph["step"]["prior_candidate_pin"],resource_cleanup_confirmed=True),"APPROVED_PRIOR_NOT_CANDIDATE_EXPECTATION")
            semantic=dict(physical)
            for pair in manifest["descriptors"]:
                original,encoded=pair["semantic_original_pin"],pair["physical_envelope_pin"]
                a.exact(semantic.pop(encoded["path"],None),encoded,"CURRENT_PHYSICAL_TO_LOGICAL_BIJECTION")
                a.require(original["path"] not in semantic,"NO_CURRENT_LOGICAL_COLLISION")
                semantic[original["path"]]=original
            reconciled,stats=adapter.normalize(scope,prior["source_input_representation"]["descriptors"],semantic,165,guard.check)
            for pin in prior["source_input_representation"]["semantic_source_freeze"]:
                a.exact(reconciled.get(pin["path"]),pin,"EVERY_APPROVED_PRIOR_LOGICAL_INPUT_PRESERVED")
            actual_removed=set(semantic)-set(reconciled)
            approved_physical={p["physical_envelope_pin"]["path"]:p for p in prior["source_input_representation"]["descriptors"]}
            a.require(actual_removed<=set(approved_physical) and not (set(reconciled)-set(semantic)),"ONLY_APPROVED_PRIOR_PHYSICAL_DUPLICATES")
            for name in set(reconciled)&set(semantic):a.exact(reconciled[name],semantic[name],"ALL_REMAINING_INPUT_PINS_UNCHANGED")
            after=dict(reconciled)
            for pair in manifest["descriptors"]:
                original,encoded=pair["semantic_original_pin"],pair["physical_envelope_pin"]
                a.exact(after.pop(original["path"],None),original,"CURRENT_ORIGINALS_STILL_COMPLETE")
                a.require(encoded["path"] not in after,"NO_CURRENT_PHYSICAL_COLLISION")
                after[encoded["path"]]=encoded
            remaining=[r for r in duplicate if r["old_physical_pin"]["path"] not in actual_removed]
            a.require(all(after.get(r["old_physical_pin"]["path"])==r["old_physical_pin"] for r in remaining),"UNAPPROVED_PREPARATION_ARTIFACTS_NOT_DROPPED")
            policy_result=dict(reconciled_prior_physical_count=len(actual_removed),reconciled_prior_physical_bytes=sum(semantic[n]["bytes"] for n in actual_removed),
                preserved_other_duplicate_count=len(remaining),all_prior_semantic_pins_preserved=True,all_other_pins_unchanged=True,
                normalized_physical_inputs=len(after),modeled_normalized_cost_seconds=cost(after,observation["inventory_requests"])["predicted_runtime_combined_seconds"]+5.0,
                normalization_contracts=stats,actual_entry_adoption_and_whole_oracle_NOT_RUN=True)
        q.finish();guard.check(force=True)
        row.update(state="RECORDED_EXACT_LEVEL6_SCOPE_AND_DUPLICATE_REPRESENTATIONS_NOT_AUTHORIZED_SCOPE_CHANGE",actual_inputs=len(physical),
            actual_scope_sha256=observation["actual_scope_sha256"],actual_cost_seconds=actual,duplicate_physical_count=len(duplicate),
            duplicate_physical_bytes=sum(r["old_physical_pin"]["bytes"] for r in duplicate),exact_duplicate_pairs=duplicate,
            hypothetical_inputs=len(hypothetical),hypothetical_coalesced_cost_seconds=hypothetical_cost,
            hypothetical_scope_change_requires_independent_policy_and_whole_original_oracle_qualification=True,
            approved_prior_policy_probe=policy_result,
            original_source_files_or_encoded_files_deleted=False,source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and isinstance(error.args[0],str) and len(error.args[0])<160:row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    a.require(guard.cleanup,"SCOPE_REPLAY_CLEANUP");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","actual_inputs","actual_cost_seconds","duplicate_physical_count","duplicate_physical_bytes",
        "hypothetical_coalesced_cost_seconds","fresh_inputs","final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("RECORDED_") else 1


def known_scope(attempt):
    """Original model over mandatory sealed inputs; no failed-preflight replay."""
    import hashlib,json,time
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import flat_current_queue_envelope_runtime_v25 as envelope
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import successor_preparation_workspace_v1 as publisher
    import case160_run007_controller as old
    import current_queue_successor_connections as metadata
    prefix="implementation/p09/evidence/p09-361-case165-"
    output=prefix+f"level6-known-scope-cost{attempt:03}.v1.json"
    a.require(1<=attempt<=8 and not (c.ROOT/output).exists(),"EXCLUSIVE_KNOWN_COST")
    guard=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic();q=None
    row=dict(state="FAILED_LEVEL6_KNOWN_SCOPE_COST_NOT_QUALIFICATION",product_or_Native_executed=False,
        accepted_count_delta=0,current_whole_source_bytes_rechecked=False,full_preflight_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF)
        a.exact(q.pin(ENTRY["path"]),ENTRY,"UNCHANGED_CURRENT_ENTRY")
        graph_name=prefix+"successor-connections007.v9.json";code_name=prefix+"successor-code-run007-attempt001.v1.json"
        setup_name=prefix+"closed-io2-preflight-setup-run007-attempt001.v1.json"
        graph=q.json(graph_name);code=q.json(code_name);setup=q.json(setup_name)
        for record,state in ((graph,"PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO"),
            (code,"PASS_CURRENT_SUCCESSOR_CODE_NOT_FULL_PREFLIGHT_NATIVE_OR_PRODUCT"),
            (setup,"PASS_CLOSED_PREPARATION_IO_SETUP_NOT_NATIVE_OR_PRODUCT")):
            a.fields(record,dict(state=state,cleanup_confirmed=True),"SEALED_MANDATORY_INPUT_WITNESS")
            a.require(record["fresh_inputs"]==record["final_fresh_hashes"]>0,"SEALED_FINAL_HASHES")
        a.fields(code,dict(contracts=dict(run=74,errors=0,failures=0,skipped=0),physical_run=7),"CURRENT_CODE74")
        manifest=a.read_exact(q,graph["manifest_pin"])
        hint=q.json(prefix+"successor-worker-bootstrap007.v9.json")
        prior=a.read_exact(q,graph["step"]["prior_candidate_pin"])
        authority=a.read_exact(q,graph["step"]["prior_queue_pin"])
        baseline=q.json(prefix+"successor-preflight-run004-attempt008.v1.json")
        sealed=scope.pins(graph["source_pins"])
        for record in (code,setup):sealed=scope.extend(sealed,scope.pins(record["source_pins"]))
        for name in (graph_name,code_name,setup_name):sealed=scope.extend(sealed,{name:q.snapshots[name]})
        a.exact(sealed.get(ENTRY["path"]),ENTRY,"SAME_CODE_AND_GRAPH_CURRENT_ENTRY")
        # Recheck executable program sources, not the several-GB original corpus.
        for pin in sealed.values():
            if pin["path"].startswith("tools/p09/") and pin["path"].endswith(".py"):
                a.exact(q.pin(pin["path"]),pin,"CURRENT_KNOWN_MODEL_PROGRAM")
        modules,_=envelope.namespace_bundle.load(c.ROOT,[p for p in sealed.values() if p["path"] in (
            "tools/p09/current_queue_successor_binding.py","tools/p09/closed_prebody_worker_connection_v1.py",
            "tools/p09/closed_prebody_source_alias_v1.py","tools/p09/level6_ordinary_binding_v1.py",
            "tools/p09/current_queue_successor_runtime.py")],{"current_queue_successor_connections":metadata})
        bindings=modules.current_queue_successor_binding;core=modules.level6_ordinary_binding_v1
        transport=modules.closed_prebody_worker_connection_v1;alias=modules.closed_prebody_source_alias_v1
        historical=prior["source_input_representation"]["descriptors"]
        module,_=bindings.connect(c.ROOT,envelope.namespace_bundle,scope,165,manifest["historical_predecessor_provenance"],historical)
        transport.install_declaration(module,hint[transport.FIELD],165,7,alias,scope)
        core.install(module,historical)
        bound=module.Binding(manifest["descriptors"],graph["manifest_pin"],next_case=165)
        # These exact static Native declarations are added by the original
        # controller after its parent callback, before runtime_budget. Construct
        # functions only: no engine run, worker dispatch, subprocess or product.
        old.old.base.configure(165)
        from types import SimpleNamespace
        def factory_load(root,pins,overrides):
            return envelope.namespace_bundle.load(root,pins,dict(flat_current_queue_envelope_runtime_v25=envelope,**overrides))
        factory_loader=SimpleNamespace(load=factory_load)
        template,identity,factory=modules.current_queue_successor_runtime.connect_factory(
            c.ROOT,factory_loader,old.old.prior,165,7,guard.check)
        engine,engine_proof=template()
        native=engine.run_owned.__globals__["native"]
        row["last_model_phase"]="late_native_declarations"
        native_rows=list(native.SOURCES)
        native_pins=scope.pins(native_rows) if native_rows else {}
        archive=[]
        for directory,name,size,digest in engine.run_owned.__globals__["FAILED_PREIMAGES"]:
            archive.append(dict(path="implementation/p09/evidence/"+directory+"/"+name,bytes=size,sha256=digest))
        if native_pins:sealed=scope.extend(sealed,native_pins)
        if archive:sealed=scope.extend(sealed,scope.pins(archive))
        row["last_model_phase"]="whole_mandatory_projection"
        semantic=bindings.inherited_scope(scope,prior["source_input_representation"],authority["fresh_input_pins"],sealed,guard.check)
        semantic,_=bound.semantic_union(semantic,guard.check)
        projected,_=bound.project(semantic,guard.check)
        physical={n:dict(p) for n,p in projected.physical_pins.items()}
        cost=old.old.prior.DIRECT.runtime_budget(physical,167)
        prior_physical=scope.pins(baseline["complete_physical_source_scope"])
        extra={n:p for n,p in physical.items() if n not in prior_physical}
        retired=[]
        # The original v9 graph's manifest is the independent baseline for
        # physical-alias overlap, not candidate-reported coverage.
        oldgraph=q.json(prefix+"successor-connections004.v9.json")
        oldmanifest=a.read_exact(q,oldgraph["manifest_pin"])
        newmap={r["semantic_original_pin"]["path"]:r for r in manifest["descriptors"]}
        for pair in oldmanifest["descriptors"]:
            oldpin=pair["physical_envelope_pin"];newpin=newmap[pair["semantic_original_pin"]["path"]]["physical_envelope_pin"]
            if oldpin!=newpin and oldpin["path"] in physical:retired.append(oldpin)
        q.finish();guard.check(force=True)
        total=cost["predicted_runtime_combined_seconds"]+5.0
        row.update(state="RECORDED_LEVEL6_MANDATORY_KNOWN_COST_FLOOR_NOT_ENTRY_QUALIFICATION",known_semantic_inputs=len(semantic),
            original_late_native_source_count=len(native_pins),original_failure_archive_count=len(archive),
            original_whole_engine_constructed_only=True,original_engine_or_worker_called=False,
            known_physical_inputs=len(physical),known_cost_floor_seconds=total,unchanged_deadline_seconds=600,shared_decoder_seconds=5.0,
            known_scope_already_exceeds_deadline=total>=600,all_unobserved_future_inputs_not_included=True,
            baseline_inputs=len(prior_physical),baseline_cost_seconds=baseline["complete_runtime_budget"]["predicted_runtime_combined_seconds"],
            retired_old_physical_files_also_declared=retired,retired_old_physical_count=len(retired),
            retired_old_physical_bytes=sum(p["bytes"] for p in retired),extra_count=len(extra),
            largest_extra_pins=sorted(extra.values(),key=lambda p:(-p["bytes"],p["path"]))[:16],
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and isinstance(error.args[0],str) and len(error.args[0])<160:row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    a.require(guard.cleanup,"KNOWN_COST_CLEANUP");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","known_physical_inputs","known_cost_floor_seconds","retired_old_physical_count",
        "retired_old_physical_bytes","fresh_inputs","final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("RECORDED_") else 1


def main():
    import argparse,hashlib,json,time
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import flat_current_queue_envelope_runtime_v25 as envelope
    import case160_run007_controller as old
    import successor_preparation_workspace_v1 as publisher
    import accept_case112_current_epoch as a
    parser=argparse.ArgumentParser();parser.add_argument("--diagnostic-attempt",type=int,required=True);parser.add_argument("--known-scope",action="store_true")
    parser.add_argument("--replay-observed",type=int)
    parser.add_argument("--replay-policy",action="store_true")
    args,remainder=parser.parse_known_args()
    if args.replay_observed is not None:
        a.require(not remainder and not args.known_scope,"REPLAY_NO_EXECUTION_ARGUMENTS")
        return replay_observed(args.diagnostic_attempt,args.replay_observed,args.replay_policy)
    if args.known_scope:
        a.require(not remainder,"KNOWN_COST_NO_EXECUTION_ARGUMENTS")
        return known_scope(args.diagnostic_attempt)
    a.require(1<=args.diagnostic_attempt<=8 and "--preflight" in remainder
        and not any(f in remainder for f in ("--native","--qualify","--accept","--review")),"COST_DIAGNOSTIC_PREFLIGHT_ONLY")
    prefix="implementation/p09/evidence/p09-361-case165-"
    output=prefix+f"level6-current-cost-diagnostic{args.diagnostic_attempt:03}.v1.json"
    a.require(not (c.ROOT/output).exists(),"EXCLUSIVE_COST_DIAGNOSTIC")
    baseline_name=prefix+"successor-preflight-run004-attempt008.v1.json"
    baseline_raw=(c.ROOT/baseline_name).read_bytes();baseline=json.loads(baseline_raw)
    a.fields(baseline,dict(state="PASS_CURRENT_SUCCESSOR_WHOLE_METADATA_PREFLIGHT_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",
        cleanup_confirmed=True),"SEALED_COST_COMPARISON_BASELINE")
    previous={p["path"]:p for p in baseline["complete_physical_source_scope"]}
    raw=(c.ROOT/ENTRY["path"]).read_bytes()
    a.require(len(raw)==ENTRY["bytes"] and hashlib.sha256(raw).hexdigest()==ENTRY["sha256"],"FROZEN_CURRENT_ENTRY")
    original=old.old.prior.DIRECT.runtime_budget;observed=[]
    def capture(scope,requests,result):
        if len(scope)>2000:
            extra={n:p for n,p in scope.items() if n not in previous}
            removed={n:p for n,p in previous.items() if n not in scope}
            without={n:p for n,p in scope.items() if n!=SELF}
            clean=original(without,requests)
            observed.append(dict(actual_inputs=len(scope),without_diagnostic_inputs=len(without),
                actual_cost_plus_decoder5=result["predicted_runtime_combined_seconds"]+5.0,
                without_diagnostic_cost_plus_decoder5=clean["predicted_runtime_combined_seconds"]+5.0,
                baseline_inputs=len(previous),baseline_cost_plus_decoder5=baseline["complete_runtime_budget"]["predicted_runtime_combined_seconds"],
                extra_input_count=len(extra),extra_bytes=sum(p["bytes"] for p in extra.values()),
                removed_input_count=len(removed),removed_bytes=sum(p["bytes"] for p in removed.values()),
                largest_extra_pins=sorted(extra.values(),key=lambda p:(-p["bytes"],p["path"]))[:16],
                extra_pins=[extra[n] for n in sorted(extra)],removed_input_paths=sorted(removed),
                changed_common_pins=[scope[n] for n in sorted(set(scope)&set(previous)) if scope[n]!=previous[n]],
                actual_scope_sha256=hashlib.sha256(json.dumps([scope[n] for n in sorted(scope)],ensure_ascii=True,
                    sort_keys=True,separators=(",",":"),allow_nan=False).encode("ascii")).hexdigest(),
                full_scope_delta_preserved=True,
                inventory_requests=requests,original_limits_and_rejection_unchanged=True))
    original_settrace=sys.settrace
    def observe_original_trace(tracer):
        if tracer is None:return original_settrace(None)
        def combined(frame,event,arg):
            result=tracer(frame,event,arg)
            if event=="exception" and not observed:
                kind,error,tb=arg
                if kind is ValueError and error.args and error.args[0]=="ENVELOPE_SCOPE_BINDING_COMPLETE_COST_PLUS_SHARED_DECODER5":
                    while tb is not None:
                        origin=tb.tb_frame
                        if origin.f_code.co_name=="runtime_budget" and origin.f_code.co_filename.replace("\\","/").endswith("/runtime_envelope_scope_binding_v1.py"):
                            values=origin.f_locals
                            if all(k in values for k in ("physical","requests","result","total")):
                                capture(values["physical"],values["requests"],values["result"])
                                observed[-1]["observed_original_rejection_total"]=values["total"]
                                observed[-1]["original_model_reproduced_exactly"]=original(values["physical"],values["requests"])==values["result"]
                                break
                        tb=tb.tb_next
            return combined if result is tracer else result
        return original_settrace(combined)
    row=dict(state="RECORDED_LEVEL6_CURRENT_COST_DIAGNOSTIC_NOT_QUALIFICATION_OR_PRODUCT",product_or_Native_executed=False,
        accepted_count_delta=0,unchanged_complete_budget_always_called=True,original_Binding_budget_predicate_unchanged=True)
    started=time.monotonic();sys.settrace=observe_original_trace
    try:
        modules,_=envelope.namespace_bundle.load(c.ROOT,[ENTRY],{})
        sys.argv=[ENTRY["path"]]+remainder
        result=modules.level6_closed_preparation_v1.main()
        row["original_preflight_exit_code"]=result
    finally:
        original_settrace(None);sys.settrace=original_settrace
    row.update(observations=observed,elapsed_seconds=time.monotonic()-started,
        baseline_preflight_pin=dict(path=baseline_name,bytes=len(baseline_raw),sha256=hashlib.sha256(baseline_raw).hexdigest()),
        original_budget_object_restored=old.old.prior.DIRECT.runtime_budget is original,
        original_trace_setter_restored=sys.settrace is original_settrace,exception_observer_only_no_line_or_opcode_trace=True,
        entry_pin=ENTRY,diagnostic_source_pin=dict(path=SELF,bytes=(c.ROOT/SELF).stat().st_size,
            sha256=hashlib.sha256((c.ROOT/SELF).read_bytes()).hexdigest()))
    publisher.publish(c.ROOT,output,row,a)
    print(json.dumps(dict(state=row["state"],original_preflight_exit_code=result,
        observation_count=len(observed),last_observation=observed[-1] if observed else None)))
    return result


if __name__=="__main__":raise SystemExit(main())
