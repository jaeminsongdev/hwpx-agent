"""One original sixteen-source graph, partial160 role, shared25-pair capsule."""
from types import SimpleNamespace as NS

SELF="tools/p09/successor_runtime_graph_v3.py"
CAPSULE={"path":"implementation/p09/evidence/p09-361-case160-worker-policy-capsule002.v4.json","sha256":"3f230f4273530d6536f68ef679dd6afb9ab6401faad077c58d570f263f83a79c","bytes":13604}


def build(q,old,successor,capsule,partial,*,context=None,partial_admission=None):
    for pin in old.NAMESPACE_SOURCE_PINS:old.a.exact(q.pin(pin["path"]),pin,"EXACT160_SHARED_CORE_SOURCE")
    core,proof=old.namespace_bundle.load(old.c.ROOT,old.NAMESPACE_SOURCE_PINS,{
        "current_stored_runtime_scope":old.base.scope,
        "owned_source_read_pressure":old.sys.modules["owned_source_read_pressure"],
        "strict_product_window_connection_v1":old.prior.WINDOW_LINK})
    module=core.runtime_envelope_scope_binding_v1
    if context is None:context=successor.admission(q,old.a,old.failed_role,old.failed004_role)
    constructor=successor.connect(module,context,old.failed_role,old.failed004_role)
    if partial_admission is None:partial_admission=partial.admission(q,old.a)
    partial_connection=partial.connect(module.source,module,partial_admission)
    worker,worker_proof=capsule.connect(core.runtime_envelope_worker_connection_v1,module,
        successor.AUTHORITY,successor.ROOT,successor)
    parent=core.runtime_envelope_parent_connection_v2;oracle=core.runtime_envelope_full_oracle_connection_v1
    old.a.require(parent.access.source is module and parent.original.frames.binding_module is module and
        worker.source is module and worker.raw_policy.source is module and oracle.binding_module is module,
        "ONE160_RUN002_PARENT_FRAME_WORKER_ORACLE_BINDING_MODULE")
    actual,raw=q._read(CAPSULE["path"],parse=True);q._bind(actual["path"],actual)
    old.a.exact(actual,CAPSULE,"EXACT160_RUN002_ACTUAL_CAPSULE_BYTES")
    bound,transport=worker.decode(bytes(raw),{k:CAPSULE[k] for k in ("bytes","sha256")},q.checkpoint)
    old.a.require(type(bound) is module.Binding and bound.next_case==160 and len(bound.descriptors())==25 and
        worker.TASK=="case160-current-r002-tests","EXACT_SHARED_RUN002_TYPE_TWENTY_FIVE_PAIRS")
    return NS(core=core,binding_module=module,binding=bound,parent=parent,worker=worker,full_oracle=oracle,
        context=context,partial_admission=partial_admission,partial_connection=partial_connection,
        core_ast_proofs=proof,constructor_proof=constructor,worker_proof=worker_proof,
        transport_proof=transport,actual160_engine_configuration_worker_or_Native_or_GO_qualified=False)
