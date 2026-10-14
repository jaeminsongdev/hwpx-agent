"""Prepared predecessor plus full fresh32 manifest admission; not runtime GO."""
import runtime_successor_manifest_v7 as manifest
import successor_bounded_graph_bootstrap_v6 as bootstrap
import prepared_checkpoint_transport_v1 as transport
import prepared_scope_handoff_v1 as handoff
import prepared_input_checkpoint_v1 as prepared
import preparation_terminal_progress_v1 as progress
import terminal_metadata_pressure_v1 as pressure
import distinct_final_sample_guard_v1 as distinct

SELF="tools/p09/successor_current_binding_v6.py"
TEST="tools/p09/tests/test_successor_current_binding_v6.py"
SEMANTIC=dict(path="implementation/p09/evidence/p09-361-case160-prepared-input-checkpoint-r834.v1.json",bytes=2693611,
    sha256="73f321efd4ffd05adebeff806c2d5f5c620c8307e73209a47583de35371b1233")
PHYSICAL=dict(path="implementation/p09/evidence/p361-lossless-runtime-inputs/case160-prepared-r834.envelope.v1.json",bytes=973539,
    sha256="499ee01169ea94b7fbb5ddab8ac95f3160cc55215fff26d7bd3093d5c086b394")

def same_graph(a,admitted,live):
    a.exact(admitted.descriptors(),live.descriptors(),"WHOLE_PARENT_AND_BOUNDED_WORKER_ALL32_DESCRIPTORS")
    a.exact(dict(admitted.manifest_pin),dict(live.manifest_pin),"WHOLE_PARENT_AND_BOUNDED_SAME_ACTUAL_MANIFEST029")

def bind(q,controller):
    m=controller.M;step=m.base.CONFIG;old=controller.old;a=m.a
    a.require(step is not None and type(step.index) is int and step.index==160
        and type(step.before) is int and step.before==153,"EXACT_CURRENT160_UNCHANGED_QUEUE_CURSOR")
    for path in (SELF,TEST,manifest.SELF,manifest.TEST,bootstrap.SELF,bootstrap.TEST,
        transport.SELF,transport.TEST,handoff.SELF,handoff.TEST):q.pin(path)
    a.exact(q.pin(step.path),step.pin,"REAL_CURRENT_STEP_CONFIG")
    # Fresh private original29 source graph for the full parent checker. This
    # is separate from the already-created bounded32 worker graph.
    base,base_proof=bootstrap.original.load(old,q.checkpoint)
    for pin in base_proof["reader_source_pins"]:a.exact(q.pin(pin["path"]),pin,"EXACT_REAL_BASE29_SOURCE")
    listing=a.read_exact(q,old.base.scope.LIST_PIN)
    rust=handoff.rust_inputs(old.base.scope.listing_inputs(listing))
    a.require(len(rust)==787,"ALL_CURRENT_COMPILED_RUST787")
    successor=controller._env["current_binding"].successor
    scope,_,prepared_proof=transport.load(q,SEMANTIC,PHYSICAL,base.binding,
        expected_context=dict(index=160,before=153,physical_product_run=3),
        expected_current_pins=dict(data_pin=q.pin(controller.DATA),preflight_pin=q.pin(controller.PREFLIGHT),
            authority_pin=successor.AUTHORITY,prior_runtime_pin=successor.ROOT),
        expected_rust=rust,expected_source_paths=frozenset(("tools/p09/produce_prepared_input_checkpoint_r366.py",
            prepared.SELF,prepared.TEST,progress.SELF,progress.TEST,pressure.SELF,pressure.TEST,distinct.SELF,distinct.TEST)))
    live,scope,admission=manifest.load(q,bootstrap.MANIFEST,a,base_graph=base,base_pin=bootstrap.original.MANIFEST,prepared_scope=scope)
    worker,worker_proof=bootstrap.load(old,q.checkpoint)
    for pin in worker_proof["reader_source_pins"]:a.exact(q.pin(pin["path"]),pin,"EXACT_BOUNDED32_CURRENT_SOURCES")
    same_graph(a,live,worker.binding)
    a.require(worker.worker.TASK=="case160-current-r004-tests","EXACT_RUN004_WORKER_TASK_NO_DISPATCH")
    return old.base.scope.extend(scope,q.snapshots),rust,worker,live,dict(
        prepared_predecessor_proof=prepared_proof,full_current32_manifest_admission=admission,
        bounded_worker_graph_proof=worker_proof,parent_and_worker_declarations_checked_exactly=True,
        original_predecessor_whole_oracle_replayed_in_this_function=False,
        full_scope_actual_two_Native_boundaries_and_independent_current160_oracle_required=True,
        controller_engine_Native_or_GO_qualified=False)
