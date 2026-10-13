"""Fresh sixteen-source graph for159 with one shared successor Binding.

Reuse exact original parent/frame/raw-policy/full-oracle code. Replace only
qualified constructor/provenance and capsule metadata dependencies privately.
This factory does not execute a Native frame, worker body or product GO.
"""
from types import SimpleNamespace as NS

SELF="tools/p09/successor_runtime_graph_v1.py"
CAPSULE=dict(path="implementation/p09/evidence/p09-361-case159-worker-policy-capsule001.v2.json",
    bytes=11020,sha256="307eb20b57ed084f01cd69ae5d20b8a5f8e45ef71a363306f12e98a041a2c0f8")


def build(q,old,successor,capsule,*,lineage=None):
    for pin in old.NAMESPACE_SOURCE_PINS:
        old.a.exact(q.pin(pin["path"]),pin,"EXACT_SUCCESSOR_CORE_NAMESPACE_SOURCE")
    core,ast_proof=old.namespace_bundle.load(old.c.ROOT,old.NAMESPACE_SOURCE_PINS,{
        "current_stored_runtime_scope":old.base.scope,
        "owned_source_read_pressure":old.sys.modules["owned_source_read_pressure"],
        "strict_product_window_connection_v1":old.prior.WINDOW_LINK})
    module=core.runtime_envelope_scope_binding_v1
    if lineage is None:lineage=successor.admission(q,old.a,old.failed_role,old.failed004_role)
    constructor_proof=successor.connect(module,lineage,old.failed_role,old.failed004_role)
    worker,worker_proof=capsule.connect(core.runtime_envelope_worker_connection_v1,module,
        successor.AUTHORITY,successor.ROOT,successor)
    parent=core.runtime_envelope_parent_connection_v2
    oracle=core.runtime_envelope_full_oracle_connection_v1
    old.a.require(parent.access.source is module and parent.original.frames.binding_module is module and
        worker.source is module and worker.raw_policy.source is module and oracle.binding_module is module,
        "ONE_SUCCESSOR_PARENT_WORKER_FRAME_ORACLE_BINDING_MODULE")
    actual,raw=q._read(CAPSULE["path"],parse=True);q._bind(actual["path"],actual)
    old.a.exact(actual,CAPSULE,"ACTUAL159_CAPSULE_FILE_BYTES")
    binding,transport=worker.decode(bytes(raw),{k:CAPSULE[k] for k in ("bytes","sha256")},q.checkpoint)
    old.a.require(type(binding) is module.Binding and binding.next_case==159 and len(binding.descriptors())==20,
        "EXACT_SHARED159_BINDING_AND_TWENTY_PAIRS")
    return NS(core=core,binding_module=module,binding=binding,parent=parent,worker=worker,
        full_oracle=oracle,lineage=lineage,ast_proof=ast_proof,constructor_proof=constructor_proof,
        worker_proof=worker_proof,transport_proof=transport,
        current159_controller_scope_cost_Native_or_GO_qualified=False)
