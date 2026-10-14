"""Entire prepared parent34 admission and separately bounded worker34."""
from types import FunctionType,SimpleNamespace as NS
import successor_current_binding_v6 as original
import successor_bounded_graph_bootstrap_v7 as bootstrap
import runtime_successor_manifest_v8 as manifest
SELF="tools/p09/successor_current_binding_v7.py"
TEST="tools/p09/tests/test_successor_current_binding_v7.py"
SEMANTIC=original.SEMANTIC
PHYSICAL=original.PHYSICAL
same_graph=original.same_graph

def bind(q,controller):
    m=controller.M;step=m.base.CONFIG;old=controller.old;a=m.a
    a.require(step is not None and type(step.index) is int and step.index==160 and type(step.before) is int and step.before==153,
        "EXACT_CURRENT160_QUEUE_CURSOR")
    for path in (SELF,TEST,bootstrap.SELF,bootstrap.TEST,manifest.SELF,manifest.TEST):q.pin(path)
    a.exact(q.pin(step.path),step.pin,"REAL_CURRENT160_CONFIG")
    # Reuse the complete original prepared-source loader body, stopping before
    # its32 admission would install the same failed roles a second time.
    base,base_proof=bootstrap.original.original.load(old,q.checkpoint)
    for p in base_proof["reader_source_pins"]:a.exact(q.pin(p["path"]),p,"REAL_BASE29_BYTES")
    listing=a.read_exact(q,old.base.scope.LIST_PIN)
    rust=original.handoff.rust_inputs(old.base.scope.listing_inputs(listing));a.require(len(rust)==787,"ALL_COMPILED_RUST787")
    s=controller._env["current_binding"].successor
    scope,_,prepared_proof=original.transport.load(q,SEMANTIC,PHYSICAL,base.binding,
        expected_context=dict(index=160,before=153,physical_product_run=3),
        expected_current_pins=dict(data_pin=q.pin(controller.DATA),preflight_pin=q.pin(controller.PREFLIGHT),authority_pin=s.AUTHORITY,prior_runtime_pin=s.ROOT),
        expected_rust=rust,expected_source_paths=frozenset(("tools/p09/produce_prepared_input_checkpoint_r366.py",
            original.prepared.SELF,original.prepared.TEST,original.progress.SELF,original.progress.TEST,
            original.pressure.SELF,original.pressure.TEST,original.distinct.SELF,original.distinct.TEST)))
    live,scope,admission=manifest.load(q,bootstrap.MANIFEST,a,base_graph=base,
        base29_pin=bootstrap.original.original.MANIFEST,base32_pin=bootstrap.original.MANIFEST,prepared_scope=scope)
    worker,worker_proof=bootstrap.load(old,q.checkpoint)
    for p in worker_proof["reader_source_pins"]:a.exact(q.pin(p["path"]),p,"REAL_BOUNDED34_BYTES")
    same_graph(a,live,worker.binding)
    a.require(worker.worker.TASK=="case160-current-r004-tests","EXACT_RUN004_TASK")
    return old.base.scope.extend(scope,q.snapshots),rust,worker,live,dict(prepared_predecessor_proof=prepared_proof,
        complete_actual34_admission=admission,bounded_worker_graph_proof=worker_proof,
        whole_parent_and_bounded_worker_all34_checked=True,original_predecessor_whole_oracle_replayed=False,
        full_two_Native_boundaries_and_independent_current160_oracle_required=True,
        new_controller_engine_worker_Native_or_GO_qualified=False)
