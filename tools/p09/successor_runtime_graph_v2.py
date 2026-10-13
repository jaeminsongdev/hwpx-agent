"""One original sixteen-source graph and shared160 Binding/capsule.

No Native frame, worker body, current engine configuration or GO is executed.
One source admission declaration per original reader may be reused; every
source is still fresh/final verified and no JSON/hash/byte cache is created.
"""
from types import SimpleNamespace as NS

SELF="tools/p09/successor_runtime_graph_v2.py"
CAPSULE=dict(path="implementation/p09/evidence/p09-361-case160-worker-policy-capsule001.v3.json",
    bytes=13081,sha256="aec00cb8654f501d6dc6abf49271315412f92fad57a9d9979e6b79644ec73723")


def build(q,old,successor,capsule,*,context=None):
    for pin in old.NAMESPACE_SOURCE_PINS:old.a.exact(q.pin(pin["path"]),pin,"EXACT160_SHARED_CORE_SOURCE")
    core,proof=old.namespace_bundle.load(old.c.ROOT,old.NAMESPACE_SOURCE_PINS,{
        "current_stored_runtime_scope":old.base.scope,
        "owned_source_read_pressure":old.sys.modules["owned_source_read_pressure"],
        "strict_product_window_connection_v1":old.prior.WINDOW_LINK})
    module=core.runtime_envelope_scope_binding_v1
    if context is None:context=successor.admission(q,old.a,old.failed_role,old.failed004_role)
    constructor=successor.connect(module,context,old.failed_role,old.failed004_role)
    worker,worker_proof=capsule.connect(core.runtime_envelope_worker_connection_v1,module,
        successor.AUTHORITY,successor.ROOT,successor)
    parent=core.runtime_envelope_parent_connection_v2;oracle=core.runtime_envelope_full_oracle_connection_v1
    old.a.require(parent.access.source is module and parent.original.frames.binding_module is module and
        worker.source is module and worker.raw_policy.source is module and oracle.binding_module is module,
        "ONE160_PARENT_FRAME_WORKER_ORACLE_BINDING_MODULE")
    actual,raw=q._read(CAPSULE["path"],parse=True);q._bind(actual["path"],actual)
    old.a.exact(actual,CAPSULE,"EXACT160_ACTUAL_CAPSULE_BYTES")
    bound,transport=worker.decode(bytes(raw),{k:CAPSULE[k] for k in ("bytes","sha256")},q.checkpoint)
    old.a.require(type(bound) is module.Binding and bound.next_case==160 and len(bound.descriptors())==24,
        "EXACT160_SHARED_TYPE_TWENTY_FOUR_PAIRS")
    return NS(core=core,binding_module=module,binding=bound,parent=parent,worker=worker,full_oracle=oracle,
        context=context,core_ast_proofs=proof,constructor_proof=constructor,worker_proof=worker_proof,
        transport_proof=transport,actual160_engine_configuration_worker_or_Native_or_GO_qualified=False)
