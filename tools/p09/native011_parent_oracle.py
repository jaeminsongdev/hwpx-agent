"""Connect the original independent checker to an actual unopened parent.

The original whole checker and additional metadata/Frame accounting stay in
place. This is construction only: no metadata callback, Frame, checker body,
worker, product, queue writer or authority is invoked.
"""
import importlib
import os
from pathlib import Path
import sys
from types import SimpleNamespace as NS

SELF='tools/p09/native011_parent_oracle.py'


def require(ok,code):
    if not ok:raise ValueError('NATIVE011_PARENT_ORACLE_'+code)


def complete_cost(binding,required,original_budget,checkpoint):
    """Use the actual complete original model, shared5 and readiness15."""
    cost=binding.runtime_budget(required,167,original_budget,checkpoint)
    require(cost['unchanged_lock_deadline_seconds']==600 and cost['unallocated_margin_seconds']==60,
        'ORIGINAL_COMPLETE600_AND_MARGIN60')
    # Binding.runtime_budget already adds its original shared decoder5.
    require(cost.get('aggregate_envelope_decoder_allowance_seconds')==5.0,'ORIGINAL_SHARED_DECODER5_INCLUDED')
    total=cost['predicted_runtime_combined_seconds']+15
    require(total<600,'ORIGINAL_COMPLETE600_PLUS_PREPARATION15')
    return dict(original_complete_cost=cost,with_preparation15_seconds=total,
        readiness_allowance_seconds=15,readiness_measured_or_qualified=False,
        actual_runtime_or_full_product_entry_scope_qualified=False)


def connect(root,q,a,source_loader,batch,data,prepared,actual,parent_entry,evidence):
    """Fresh explicit source loading; preserve every original checker body."""
    q.checkpoint();owner=data.planned.batch;connection=owner.parent_connection
    require(owner.phase=='NEW' and connection is not None and connection.parent is actual
        and connection.state.attempts==0 and connection.state.frames==[]
        and owner.initial is owner.final is owner.active is None,'ACTUAL_UNOPENED_SAME_PARENT')
    linked=prepared.linked;graph=prepared.entry.graph
    require(linked.state.attempts==linked.state.calls==0,'ZERO_WORKER_ATTEMPTS')
    scope=batch.scope
    known=scope.extend(data.planned.logical,scope.pins(data.evidence['source_pins']))
    known=scope.extend(known,scope.pins(prepared.entry.runtime.PINS))
    paths=('ast_clone_namespace_v1','ast_copy_namespace_connection_v1','native009_full72_construction_v1',
        'post_product_recovery_connection_v1','post_product_recovery_window_v1',
        'current_queue_successor_lossless_runtime_v4','native009_full75_dispatch_connection_v1',
        'current_queue_successor_oracle','case160_run007_controller')
    missing=['tools/p09/'+n+'.py' for n in paths if 'tools/p09/'+n+'.py' not in known]
    evidence.update(stage='EXPLICIT_CHECKER_SOURCE_PREFLIGHT',missing_declared_sources=missing)
    require(not missing,'ALL_CHECKER_CONSTRUCTION_SOURCES_DECLARED_BEFORE_IO')
    initial=batch.PacedNamespaceLoader(source_loader,q,known).api
    libs,_=initial.load(root,[known['tools/p09/'+n+'.py'] for n in paths[:2]],{})
    optimized,_=libs.ast_copy_namespace_connection_v1.connect(source_loader,libs.ast_clone_namespace_v1)
    paced=batch.PacedNamespaceLoader(optimized,q,known)
    libs,_=paced.api.load(root,[known['tools/p09/native009_full72_construction_v1.py']],{})
    construction=libs.native009_full72_construction_v1
    loader,_=construction.private_runtime_imports(paced.api)
    components,_=loader.load(root,[known['tools/p09/'+n+'.py'] for n in paths[3:7]],{})
    recovery=components.post_product_recovery_connection_v1
    window=components.post_product_recovery_window_v1
    configuration=components.current_queue_successor_lossless_runtime_v4
    dispatch=components.native009_full75_dispatch_connection_v1
    metadata=prepared.entry.runtime.metadata
    oracle_loader,oracle_state=dispatch.oracle_loader(root,loader,configuration,metadata,a,known[configuration.ORACLE['path']])
    audit_state=dict(active=True,checking=False,opens=0,pyc_denied=0)
    def audit(event,args):
        if (not audit_state['active'] or audit_state['checking'] or event!='open' or not args
            or not isinstance(args[0],(str,bytes))):
            return
        path=Path(os.fsdecode(args[0])).absolute()
        if not path.is_relative_to(root):return
        mode=args[1] if len(args)>1 else None;flags=args[2] if len(args)>2 else 0
        require(not (isinstance(mode,str) and any(c in mode for c in 'wax+'))
            and not (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)),
            'READONLY_ORIGINAL_CHECKER_CONSTRUCTION')
        if path.suffix in ('.pyc','.pyo'):
            audit_state['pyc_denied']+=1;raise OSError('ORACLE_SOURCE_NOT_BYTECODE')
        name=path.relative_to(root).as_posix()
        if name not in known:evidence['missing_source_open']=name
        require(name in known,'ALL_CHECKER_OPEN_INPUTS_ALREADY_DECLARED')
        audit_state['checking']=True
        try:
            a.exact(q.pin(name),known[name],'ACTUAL_CHECKER_CONSTRUCTION_SOURCE_PIN')
            audit_state['opens']+=1
        finally:audit_state['checking']=False
    sys.addaudithook(audit)
    try:
        evidence['stage']='REAL_HISTORICAL_VALIDATOR_AND_CURRENT_ORACLE'
        envelope=importlib.import_module('flat_current_queue_envelope_runtime_v25')
        proxy=NS(**{**vars(envelope),'namespace_bundle':loader})
        libraries,_=loader.load(root,[known['tools/p09/case160_run007_controller.py']],
            {'flat_current_queue_envelope_runtime_v25':proxy,'sys':NS(**{**vars(sys),'argv':[]})})
        legacy=libraries.case160_run007_controller
        require(legacy.NATIVE==7 and legacy.CURRENT is not None,'ORIGINAL_HISTORICAL_CHECKER_FAMILY')
        step=linked.window.M.base.CONFIG
        a.fields(vars(step),dict(index=165,before=158),'UNCHANGED_CURRENT_CONFIGURATION')
        libraries,_=oracle_loader.load(root,[known[configuration.ORACLE['path']]],
            {'current_queue_successor_connections':metadata})
        wrapped=NS(**{**vars(graph),'full_oracle':owner.connect_full_oracle(graph.full_oracle,graph.binding,index=165)})
        actual_pin,raw=q._read(window.WINDOW_PIN['path'],parse=True);q._bind(actual_pin['path'],actual_pin)
        a.exact(actual_pin,window.WINDOW_PIN,'ORIGINAL_WINDOW_SOURCE_FOR_CHECKER')
        selected=recovery.connect_oracle(libraries.current_queue_successor_oracle.connect,window,bytes(raw))
        checker,proof=selected(legacy.CURRENT,wrapped,step,linked.names,data.planned.logical,q.checkpoint)
        checker.environment['only159']()
        accounting=dispatch.verify_checker(checker,wrapped,configuration)
        require(oracle_state.loads==1 and oracle_state.oracle is libraries.current_queue_successor_oracle,
            'ONE_ORIGINAL_ADDITIONAL_ACCOUNTING_ORACLE')
        evidence.update(stage='ACTUAL_HELPER_INVENTORY_AND_DECLARED_COMPLETE_COST',
            original_checker_connection=proof,additional_accounting=accounting)
        inventory=construction.helper_inventory(root,actual)
        evidence['helper_inventory']=inventory
        parent_entry.admit_helpers(inventory,known,q,a.exact)
        require(inventory['Native_count']<=64,'ORIGINAL_NATIVE_HELPER64_NOT_HIDDEN_OR_RAISED')
        required=parent_entry.current_logical(data,graph.binding,q.checkpoint,scope,a.exact)
        budget=complete_cost(graph.binding,required,linked.window.DIRECT.runtime_budget,q.checkpoint)
        require(connection.state.attempts==0 and connection.state.frames==[]
            and linked.state.attempts==linked.state.calls==0 and owner.phase=='NEW'
            and not checker.projectors and linked.window.WINDOW.SECONDS==10,
            'UNCHANGED_NO_BODY_NO_FRAME_NO_WORKER_PRODUCT10')
        evidence.update(stage='CONNECTED_CHECKER_AND_DECLARATION_COST_NOT_NATIVE',budget=budget,
            independent_checker_connected=True,checker_body_or_candidate_executed=False,
            helpers_freshly_checked=len(inventory['original_Native_helper_union']),
            project_source_opens=audit_state['opens'],bytecode_reads_denied=audit_state['pyc_denied'],
            parent_attempts=0,Frame_instances=0,worker_attempts=0,worker_calls=0,
            metadata_or_shared_Frame_or_readiness15_or_product_qualified=False,
            complete_product_entry_scope_qualified=False,GO_authorized=False)
        return NS(checker=checker,graph=wrapped,known=known,loader=loader)
    finally:audit_state['active']=False
