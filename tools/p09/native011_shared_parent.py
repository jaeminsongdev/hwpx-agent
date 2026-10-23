"""Original shared Frame and metadata callback, construction and denial only.

No Batch.begin, metadata body, Frame instance, worker or GO is executed here.
The whole original callback retains its approved source-policy AST inverse.
"""
from types import SimpleNamespace as NS
import native011_metadata_report as reports

SELF='tools/p09/native011_shared_parent.py'


def require(ok,code):
    if not ok:raise ValueError('NATIVE011_SHARED_PARENT_'+code)


def admit_report(root,q,a,batch,data,generation):
    old=data.planned;old.batch.check()
    require(type(old.batch) is batch.Batch and old.batch.phase=='NEW' and old.batch.parent_connection is None,
        'REPORT_BEFORE_ANY_PARENT_CONNECTION')
    path=reports.output_path(generation);record=q.json(path);report_pin=dict(q.snapshots[path])
    sources=reports.validate(record,data.report,batch.scope,generation)
    for name,pin in sources.items():a.exact(q.pin(name),pin,'FRESH_EXPLICIT_METADATA_REPORT_SOURCE')
    added=batch.scope.extend(sources,{path:report_pin})
    logical=data.declared.normalize(list(added.values()));physical=data.declared.to_physical(list(added.values()))
    require(not set(physical)&set(old.history),'NO_COLD_HISTORY_RECLASSIFICATION')
    whole=batch.scope.extend(old.whole,physical);current=batch.scope.extend(old.current,physical)
    owner=batch.Batch(whole,current,batch.plain(old.history),first_index=165,checkpoint=q.checkpoint,identity=old.batch.identity)
    data.planned=NS(**{**vars(old),'whole':whole,'current':current,
        'logical':batch.scope.extend(old.logical,logical),'batch':owner})
    require(data.declared.to_physical(list(data.planned.logical.values()))==whole,'FULL_DECLARED_WHOLE_EQUALITY')
    return NS(pin=report_pin,report=record,sources=sources,proof=dict(report_pin=report_pin,
        original_whole_pins_retained=True,preservation_unchanged=True,source_count=len(sources),
        actual_full_corpus_byte_boundary_or_runtime_qualified=False))


def prepare(root,q,a,source_loader,batch,data,prepared,parent_entry):
    old=data.planned;old.batch.check()
    require(type(old.batch) is batch.Batch and old.batch.phase=='NEW' and old.batch.parent_connection is None,
        'ORIGINAL_UNOPENED_BATCH_ONLY')
    scope=batch.scope;known=scope.extend(old.logical,scope.pins(data.evidence['source_pins']))
    known=scope.extend(known,scope.pins(prepared.entry.runtime.PINS))
    initial=batch.PacedNamespaceLoader(source_loader,q,known).api
    libraries,_=initial.load(root,[known['tools/p09/'+n+'.py'] for n in
        ('ast_clone_namespace_v1','ast_copy_namespace_connection_v1')],{})
    optimized,_=libraries.ast_copy_namespace_connection_v1.connect(source_loader,libraries.ast_clone_namespace_v1)
    paced=batch.PacedNamespaceLoader(optimized,q,known)
    libraries,_=paced.api.load(root,[known['tools/p09/native009_full72_construction_v1.py']],{})
    loader,_=libraries.native009_full72_construction_v1.private_runtime_imports(paced.api)
    names=('lossless_metadata_connection_v1','fresh_lossless_metadata_reader_v1','shared_metadata_frame_decoder_budget_v1')
    components,_=loader.load(root,[known['tools/p09/'+n+'.py'] for n in names],{})
    pin,raw=q._read(batch.SELF,parse=True);q._bind(pin['path'],pin)
    a.exact(pin,known[batch.SELF],'ENTIRE_ORIGINAL_BATCH_SHARED_SLOT_SOURCE')
    selected=parent_entry.shared_batch_type(batch,bytes(raw),components)
    owner=selected(batch.plain(old.whole),batch.plain(old.current),batch.plain(old.history),
        first_index=165,checkpoint=q.checkpoint,identity=old.batch.identity)
    require(owner.__class__.__bases__==(batch.Batch,) and owner.phase=='NEW','EXACT_ORIGINAL_PRIVATE_SHARED_BATCH')
    data.planned=NS(**{**vars(old),'batch':owner})
    return NS(batch=owner,components=components,known=known,loader=loader)


def attach(root,q,a,batch,data,prepared,actual,parent_entry,resources,admitted):
    owner=resources.batch;connection=owner.parent_connection;linked=prepared.linked
    require(connection is not None and connection.parent is actual and connection.state.frames==[]
        and connection.state.attempts==0 and len(connection.frame_type.__mro__)==5,'ACTUAL_SHARED_PARENT_UNEXECUTED')
    require(owner.shared.metadata is owner.shared.frame is None and not owner.shared.restored,
        'ONE_UNUSED_SHARED_OWNER')
    require(owner.metadata_connection.original_run is linked.engine.run_owned
        and owner.metadata_connection.readers==owner.metadata_connection.budgets==[],
        'ACTUAL_ENGINE_READER_ROUTER_CONNECTED_NOT_RUN')
    actual_pin,raw=q._read(batch.RUNTIME,parse=True);q._bind(actual_pin['path'],actual_pin)
    a.exact(actual_pin,resources.known[batch.RUNTIME],'ORIGINAL_SCOPE_FOR_APPROVED_BATCH_INVERSE')
    explicit=batch.scope.extend(admitted.sources,{admitted.pin['path']:admitted.pin})
    connected=NS(graph=prepared.entry.graph,runtime=prepared.entry.runtime,core=prepared.entry.core)
    assembled=NS(batch=owner,built=linked,parent=actual)
    attached=parent_entry.attach_callback(assembled,connected,data,explicit,batch,bytes(raw),
        admitted.pin,dict(prepared.entry.graph.binding.manifest_pin))
    denied=NS(checkpoint=q.checkpoint)
    try:attached.callback(denied)
    except ValueError as error:require(error.args==('BATCH_VERIFY_READY_METADATA_OWNER_ONLY',),'EXACT_PREAUDIT_DENIAL_BEFORE_IO')
    else:require(False,'METADATA_MUST_REFUSE_BEFORE_WHOLE_BATCH_AUDIT')
    require(owner.phase=='NEW' and owner.metadata_connection.readers==[]
        and owner.shared.metadata is owner.shared.frame is None and connection.state.attempts==0
        and connection.state.frames==[] and linked.state.attempts==linked.state.calls==0,
        'PREAUDIT_DENIAL_DID_NOT_CONSTRUCT_READERS_FRAME_OR_WORKER')
    return NS(attached=attached,connected=connected,proof=dict(
        original_shared_five_class_Frame_chain_verified=True,original_shared_constructor_owner_verified=True,
        actual_engine_lossless_metadata_router_connected=True,
        approved_complete_scope_AST_inverse=attached.inverse['exact_original_AST_inverse'],
        actual_metadata_callback_bound=True,preaudit_callback_attempts=len(attached.calls),
        original_preaudit_denial_before_metadata_IO=True,metadata_body_executed=False,
        metadata_reader_instances=0,Frame_instances=0,worker_attempts=0,worker_calls=0,
        shared_decoder=owner.shared.evidence(),metadata_report=admitted.proof,
        actual_Native_Frame_or_shared_decoding_or_product_qualified=False))
