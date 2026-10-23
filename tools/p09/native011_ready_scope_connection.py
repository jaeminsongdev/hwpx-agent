"""Admit the exact readonly worker201 declarations into an unopened Native plan.

This does not admit a live Frame or reuse a prior byte boundary. Original
scope projection, current805 version mapping, shared owner and cost remain.
"""
import ast
import copy
import hashlib
from types import SimpleNamespace as NS

SELF='tools/p09/native011_ready_scope_connection.py'
TEST='tools/p09/tests/test_native011_ready_scope_connection.py'
ENTRY='tools/p09/native011_ready_native_construction.py'
ENTRY_TEST='tools/p09/tests/test_native011_ready_native_construction.py'
ORIGINAL=dict(path='tools/p09/native011_current_epoch_shared.py',bytes=17131,
    sha256='db60bee1016ccab236a05363a618435c2d6c813ebe5359ef55e9cae5114d6dc2')
READY=dict(path='implementation/p09/evidence/p09-361-native011-current805-inherited-worker-ready002.v1.json',
    bytes=112623,sha256='93e28beeaff497bef1d14c527d7bfb9c7690d913a3be9aeaec17cfe2cf078733')
OUTPUT='implementation/p09/evidence/p09-361-native011-current805-live-source-parent003.v1.json'
CONTROLS=(SELF,TEST,ENTRY,ENTRY_TEST,
    'tools/p09/native011_inherited_source_probe_child.py','tools/p09/tests/test_native011_inherited_source_probe_child.py',
    'tools/p09/native011_inherited_audit_reader.py','tools/p09/tests/test_native011_inherited_audit_reader.py',
    'tools/p09/native011_worker_source_inheritance.py','tools/p09/tests/test_native011_worker_source_inheritance.py',
    'tools/p09/native011_nested_preparation_job.py','tools/p09/tests/test_native011_nested_preparation_job.py',
    'tools/p09/native011_source_coverage.py','tools/p09/tests/test_native011_mapped_source_descriptor.py',READY['path'],
    'tools/p09/native011_precise_boundary_pacer.py','tools/p09/tests/test_native011_precise_boundary_pacer.py',
    'tools/p09/native011_precise_boundary_connection.py','tools/p09/tests/test_native011_precise_boundary_connection.py',
    'tools/p09/native011_readonly_frame_probe.py','tools/p09/tests/test_native011_readonly_frame_probe.py',
    'tools/p09/native011_readonly_frame_driver.py','tools/p09/tests/test_native011_readonly_frame_driver.py',
    'tools/p09/native011_readonly_frame_entry.py','tools/p09/tests/test_native011_readonly_frame_projection.py',
    'tools/p09/native011_metadata_audit.py','tools/p09/native011_metadata_epochs.py')
EXACT_CONTROLS=('tools/p09/native011_exact_read_budget.py','tools/p09/tests/test_native011_exact_read_budget.py')
TIMING_CONTROLS=('tools/p09/native011_decoder_timing_observer.py',
    'tools/p09/tests/test_native011_decoder_timing_observer.py')
CHUNK_CONTROLS=('tools/p09/native011_decoder_chunk_join.py','tools/p09/tests/test_native011_decoder_chunk_join.py',
    'tools/p09/native011_chunk_join_connection.py','tools/p09/tests/test_native011_chunk_join_connection.py')
METADATA_TAIL_CONTROLS=('tools/p09/native011_metadata_tail_candidate.py','tools/p09/tests/test_native011_metadata_tail_candidate.py',
    'tools/p09/native011_metadata_tail_connection.py','tools/p09/tests/test_native011_metadata_tail_connection.py')


def require(ok,label):
    if not ok:raise ValueError('READY_NATIVE_SCOPE_'+label)


def declarations(proof,scope):
    require(proof['state']=='PASS_ORIGINAL_WORKER_READY15_REAL_EOF_NOT_NATIVE'
        and proof['cleanup_confirmed'] is True and proof['actual_product_GO_writes']==0
        and proof['prewarm_before_gate_started'] is False,'REAL_EOF_ONLY_PREPARATION_RESULT')
    gate=proof['readiness'];child=proof['child']
    require(gate['readiness_limit_seconds']==15 and gate['readiness_confirmed'] is True
        and 0<gate['readiness_elapsed_seconds']<15 and gate['actual_original_GO_written'] is False
        and gate['stopped'] is True and gate['installed_in_Native'] is False,'ORIGINAL_GATE15_WITHOUT_GO')
    require(child['state']=='PASS_ORIGINAL_WORKER_INHERITED_SOURCE_REAL_EOF_NOT_NATIVE'
        and child['fresh_inputs']==child['final_fresh_hashes']==201 and child['actual_EOF_reads']==1
        and child['process_creation_attempts']==0 and child['cleanup_confirmed'] is True
        and child['actual_product_GO_received'] is False and child['actual_product_processes']==0,
        'WHOLE201_ORIGINAL_WORKER_WITHOUT_PRODUCT')
    rows=scope.pins(child['source_pins']);require(len(rows)==201,'EXACT_WORKER201_DECLARATION')
    return rows


def admit(q,a,scope,*,exact_read=False,decoder_timing=False,chunk_join=False,metadata_tail=False):
    require(type(exact_read) is bool,'EXPLICIT_OPTIONAL_EXACT_READ_MODE')
    require(type(decoder_timing) is bool and (not decoder_timing or exact_read),'EXPLICIT_OPTIONAL_READONLY_TIMING_MODE')
    require(type(chunk_join) is bool and (not chunk_join or (exact_read and decoder_timing)),
        'EXPLICIT_OPTIONAL_READONLY_CODEC_MODE')
    require(type(metadata_tail) is bool and (not metadata_tail or chunk_join),'EXPLICIT_OPTIONAL_METADATA_TAIL_MODE')
    proof=a.read_exact(q,READY);required=declarations(proof,scope)
    # A PASS is only a source declaration here, never current byte credit.
    for pin in required.values():a.exact(q.pin(pin['path']),pin,'FRESH_CURRENT_WORKER_SOURCE_PIN')
    require(len(CONTROLS)==len(set(CONTROLS))==27,'CLOSED_TWENTYSIX_CODE_ONE_PROVENANCE_CONTROL_LIST')
    controls=CONTROLS+EXACT_CONTROLS if exact_read else CONTROLS
    if decoder_timing:controls+=TIMING_CONTROLS
    if chunk_join:controls+=CHUNK_CONTROLS
    if metadata_tail:controls+=METADATA_TAIL_CONTROLS
    require(len(controls)==len(set(controls))==27+2*exact_read+2*decoder_timing+4*chunk_join+4*metadata_tail,'CLOSED_OPTIONAL_CONTROL_ROLES')
    return NS(required=required,control_names=controls,readiness_pin=dict(READY),exact_read=exact_read,decoder_timing=decoder_timing,chunk_join=chunk_join,
        metadata_tail=metadata_tail,source_declaration_only=True,live_Frame_or_product_qualified=False)


def inspect_current(data,required,scope,frame_type,original_base):
    current,whole,history=({n:dict(p) for n,p in getattr(data.planned,key).items()}
        for key in ('current','whole','history'))
    require(not set(current)&set(history) and {**current,**history}==whole and len(history)==419,
        'EXACT_WHOLE_CURRENT_HISTORY419_PARTITION')
    require(scope.pins(list(required.values()))==required and len(required)==201,'EXACT_REQUIRED201_MAPPING')
    missing=sorted(set(required)-set(current));conflicts=sorted(n for n,p in required.items()
        if n in current and current[n]!=p)
    require(not missing and not conflicts and not set(required)&set(history),
        'EVERY_WORKER_RAW_PIN_DIRECT_CURRENT_NOT_ALIAS_OR_HISTORY')
    require(data.declared.to_physical(list(data.planned.logical.values()))==whole,
        'ENTIRE_LOGICAL_PHYSICAL_RECOMPOSITION')
    require(type(frame_type) is type and len(frame_type.__mro__)==5
        and frame_type.__mro__[-2:] == (original_base,object),
        'ORIGINAL_NATIVE_BASE_AND_FIVE_CLASS_SHARED_FRAME_CHAIN')
    return dict(required_worker_sources=201,direct_current_worker_sources=201,missing_sources=missing,
        conflicting_sources=conflicts,raw_source_alias_or_history_assumed_held=False,
        whole_inputs=len(whole),current_inputs=len(current),history_inputs=len(history),
        original_base_reference_same=True,actual_Frame_class_count=len(frame_type.__mro__),
        original_source_coverage_body_change_required=False,actual_live_Frame_coverage_qualified=False,
        previous_whole_audit_used_as_new_boundary=False,GO_authorized=False)


def complete_budget(model):
    require(model['unchanged_lock_deadline_seconds']==600 and model['unallocated_margin_seconds']==60
        and model['aggregate_envelope_decoder_allowance_seconds']==5
        and model['strict_GO_to_complete_capture_window_seconds']==10
        and model['product_allowance_seconds']==10 and model['actual_completion_guaranteed'] is False,
        'ORIGINAL_COMPLETE600_MARGIN60_SHARED5_PRODUCT10')
    total=model['predicted_runtime_combined_seconds']+15
    require(total<600,'COMPLETE_MODEL_PLUS_ORIGINAL_READY15_FITS')
    return dict(original_complete_model=dict(model),readiness_allowance_seconds=15,
        with_readiness15_seconds=total,remaining_nominal_seconds=600-total,
        estimate_not_runtime_completion_guarantee=True,actual_Native_qualified=False)


def project(raw,namespace,admit_callback,validate_callback,*,driver=None):
    require(type(raw) is bytes and len(raw)==ORIGINAL['bytes']
        and hashlib.sha256(raw).hexdigest()==ORIGINAL['sha256'],'EXACT_FULL_ORIGINAL_SHARED_CONSTRUCTOR')
    original=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='main')
    node=copy.deepcopy(original);output_hits=declaration_hits=validation_hits=0
    revised=[];undo=[];guard_hits=0;run_hits=0;finish_hits=0
    for item in node.body:
        if (isinstance(item,ast.Assign) and len(item.targets)==1 and isinstance(item.targets[0],ast.Name)
            and item.targets[0].id=='output'):
            before=copy.deepcopy(item);item.value=ast.Constant(OUTPUT if driver is None else driver.output);output_hits+=1
            undo.append(('output',before))
        if (driver is not None and isinstance(item,ast.Assign) and len(item.targets)==1
            and isinstance(item.targets[0],ast.Name) and item.targets[0].id=='g'):
            item._live_before_value=copy.deepcopy(item.value);item.value=ast.Name(id='_readonly_driver',ctx=ast.Load());guard_hits+=1
        if isinstance(item,ast.Try):
            body=[]
            for statement in item.body:
                if (isinstance(statement,ast.Assign) and len(statement.targets)==1
                    and isinstance(statement.targets[0],ast.Name) and statement.targets[0].id=='explicit'):
                    added=ast.parse('_live=_live_declaration(q,a,scope)\ndeclared_names+=_live.control_names').body
                    for extra in added:extra._live_added=True
                    body.extend(added);declaration_hits+=1
                if (isinstance(statement,ast.Expr) and isinstance(statement.value,ast.Call)
                    and isinstance(statement.value.func,ast.Attribute) and isinstance(statement.value.func.value,ast.Name)
                    and statement.value.func.value.id=='q' and statement.value.func.attr=='finish'):
                    added=ast.parse('_live_validate(q,a,scope,data,resources,actual,prepared,entry,row,_live)').body[0]
                    added._live_added=True;body.append(added);validation_hits+=1
                body.append(statement)
            if driver is not None:
                closing=[i for i,statement in enumerate(body) if isinstance(statement,ast.Expr)
                    and isinstance(statement.value,ast.Call) and isinstance(statement.value.func,ast.Name)
                    and statement.value.func.id=='require' and len(statement.value.args)>1
                    and isinstance(statement.value.args[1],ast.Constant)
                    and statement.value.args[1].value=='SHARED_CONSTRUCTION_CLOSING_BYTES']
                require(len(closing)==1,'ONE_CONSTRUCTION_CLOSING_BEFORE_READONLY_RUN')
                added=ast.parse('_readonly_result=_readonly_driver.run(c.ROOT,q,a,loader,entry,original.batch,data,prepared,bound,resources,checked,row,private_load,publisher)').body[0]
                added._live_added=True;body.insert(closing[0]+1,added);run_hits+=1
                added=ast.parse('row.update(_readonly_result)').body[0];added._live_added=True;body.append(added)
                added=ast.parse('_readonly_driver.finish(c.ROOT,row,publisher,a)').body[0]
                added._live_added=True;item.finalbody.insert(len(item.finalbody)-2,added);finish_hits+=1
            item.body=body
        revised.append(item)
    node.body=revised
    require(output_hits==declaration_hits==validation_hits==1,'THREE_EXACT_CONSTRUCTOR_CONNECTION_SITES')
    require(driver is None or guard_hits==run_hits==finish_hits==1,'EXACT_READONLY_DRIVER_SITES')
    inverse=copy.deepcopy(node)
    for item in inverse.body:
        if (isinstance(item,ast.Assign) and len(item.targets)==1 and isinstance(item.targets[0],ast.Name)
            and item.targets[0].id=='output'):item.value=undo[0][1].value
        if hasattr(item,'_live_before_value'):item.value=item._live_before_value
        if isinstance(item,ast.Try):
            item.body=[statement for statement in item.body if not hasattr(statement,'_live_added')]
            item.finalbody=[statement for statement in item.finalbody if not hasattr(statement,'_live_added')]
    require(ast.dump(inverse,include_attributes=False)==ast.dump(original,include_attributes=False),
        'ENTIRE_ORIGINAL_CONSTRUCTOR_AST_INVERSE')
    env=dict(namespace,_live_declaration=admit_callback,_live_validate=validate_callback,_readonly_driver=driver)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),ORIGINAL['path'],'exec'),env)
    return env['main'],dict(entire_original_constructor_AST_inverse=True,
        declaration_admission_site_count=1,preclosing_validation_site_count=1,
        exclusive_new_output=OUTPUT if driver is None else driver.output,
        original_metadata_deny_and_shared_constructor_retained=True,readonly_driver_sites=guard_hits+run_hits+finish_hits,
        actual_Native_or_GO_qualified=False)
