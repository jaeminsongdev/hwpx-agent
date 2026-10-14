"""Actual two failed roles in a private31 binding; not a manifest adoption."""
import ctypes
import io
import json
from pathlib import Path
import re
import sys
import time
import unittest
SELF="tools/p09/qualify_failed160_extras_r369.py"
OUTPUT="implementation/p09/evidence/p09-361-failed160-extras-code12-private31-r846.v1.json"

def main():
    k=ctypes.WinDLL("kernel32",use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p
    k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
    k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    handle=k.GetCurrentProcess()
    if not(k.SetPriorityClass(handle,0x4000) and k.SetProcessAffinityMask(handle,1)):raise ValueError("LOCAL_LIMITS_NOT_APPLIED")
    sys.path.insert(0,str(Path(__file__).resolve().parent));sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    sys.path.insert(0,str(Path(__file__).resolve().parent/"tests"))
    import accept_case112_current_epoch as a
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    import runtime_failed160_extras_v1 as extras
    import compact_worker_capsule_wire_v1 as compact
    import prepared_checkpoint_transport_v1 as transport
    import prepared_scope_handoff_v1 as handoff
    import prepared_input_checkpoint_v1 as prepared
    import preparation_terminal_progress_v1 as progress
    destination=a.c.ROOT/OUTPUT;a.require(not destination.exists(),"EXTRAS_CODE_EXCLUSIVE_REPORT")
    g=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    out=dict(state="FAILED_EXTRA_FAILURE_ROLES_NOT_ACCEPTED",accepted_count_delta=0,
        Native_or_product_executed=False,GO_authorized=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        paths=(SELF,extras.SELF,extras.TEST,compact.SELF,compact.TEST)
        for path in paths:q.pin(path)
        tested=unittest.TextTestRunner(stream=io.StringIO()).run(
            unittest.defaultTestLoader.loadTestsFromName("tools.p09.tests.test_runtime_failed160_extras_v1"))
        a.require(tested.wasSuccessful() and tested.testsRun==12 and not tested.skipped,"ALL_EXTRA_ROLE_CODE12")
        import flat_current_queue_envelope_runtime_v31 as c
        c.M.base.configure(160);graph,bootstrap=c.bootstrap.load(c.old,q.checkpoint)
        for pin in bootstrap["reader_source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_BOUNDED_GRAPH_SOURCE")
        declared=q.json("implementation/p09/evidence/p09-361-prepared-checkpoint-transport-producer-r839.v1.json")
        listing=a.read_exact(q,a.scope.LIST_PIN);rust=handoff.rust_inputs(a.scope.listing_inputs(listing))
        s=c._env["current_binding"].successor
        scope,_,_=transport.load(q,declared["original_pin"],declared["physical_pin"],graph.binding,
            expected_context=dict(index=160,before=153,physical_product_run=3),
            expected_current_pins=dict(data_pin=q.pin(c.DATA),preflight_pin=q.pin(c.PREFLIGHT),authority_pin=s.AUTHORITY,prior_runtime_pin=s.ROOT),
            expected_rust=rust,expected_source_paths=frozenset(("tools/p09/produce_prepared_input_checkpoint_r366.py",prepared.SELF,prepared.TEST,
                progress.SELF,progress.TEST,pressure.SELF,pressure.TEST,distinct.SELF,distinct.TEST)))
        admitted=extras.admission(q,a)
        original_descriptors=graph.binding.descriptors();a.exact(len(original_descriptors),29,"ALL_BASE29")
        connected=extras.connect(graph.binding_module.source,graph.binding_module,admitted)
        rows=original_descriptors+[graph.binding_module.source.descriptor(r["failed_runtime_pin"],r["physical_pin"],next_case=160) for r in admitted]
        # The old manifest pin is a diagnostic constructor input only. No31
        # manifest is fabricated, published or admitted by this qualification.
        bound=graph.binding_module.Binding(rows,dict(graph.binding.manifest_pin),next_case=160)
        for item in admitted:
            scope=c.M.base.scope.extend(scope,{item["failed_runtime_pin"]["path"]:item["failed_runtime_pin"]})
        complete=c.M.base.scope.extend(scope,q.snapshots)
        projection,_=bound.project(complete,q.checkpoint)
        representation=bound.representation(projection)
        a.exact(len(representation["same_case_failed160_extra_receipt_provenance"]),2,"BOTH_FAILURE_ROLES_EXPLICIT")
        api,wire_proof=compact.connect(graph.worker)
        wire,wire_pin=api.encode(bound,s.AUTHORITY,s.ROOT,q.checkpoint)
        restored,_=api.decode(wire,wire_pin,q.checkpoint)
        a.exact(restored.descriptors(),bound.descriptors(),"EVERY_REAL31_DESCRIPTOR_RESTORED")
        physical={n:dict(p) for n,p in projection.physical_pins.items()}
        model=c.old.prior.DIRECT.runtime_budget(physical,167)
        predicted=model["predicted_runtime_combined_seconds"]+5.0
        q.finish();g.check(force=True)
        out.update(state="PASS_EXTRA_FAILED160_ROLE_CODE12_REAL_PRIVATE31_COMPACT_WIRE_NOT_MANIFEST_OR_GO",
            contracts=dict(run=12,errors=0,failures=0,skipped=0),extra_failure_admissions=admitted,
            connection_proof=connected,compact_wire_proof=wire_proof,base_source_pairs=29,private_source_pairs=31,
            compact31_wire_bytes=len(wire),maximum_capsule_bytes=16384,
            all_original29_descriptors_retained=True,actual_manifest31_published_or_admitted=False,
            diagnostic_constructor_uses_old_manifest_pin_not_a31_manifest=True,
            all_source_pins=[dict(p) for p in q.snapshots.values()],
            source_pins=[q.snapshots[p] for p in paths],fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            diagnostic_Native_cost_including_decoder5=predicted,original600_cost_accepted=predicted<600,
            cost_includes_qualifier_source_inputs_not_future_controller=True,
            new_runtime_identity_manifest_or_independent_product_oracle_qualified=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    a.require(g.cleanup,"EXTRAS_CODE_CLEANUP")
    with destination.open("x",encoding="utf-8") as stream:json.dump(out,stream,ensure_ascii=True,indent=2,allow_nan=False)
    print(json.dumps({key:out.get(key) for key in ("state","contracts","private_source_pairs","compact31_wire_bytes",
        "diagnostic_Native_cost_including_decoder5","original600_cost_accepted","fresh_inputs","final_fresh_hashes",
        "CPU_max","RAM_min","cleanup_confirmed","error_code")},allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1
if __name__=="__main__":raise SystemExit(main())
