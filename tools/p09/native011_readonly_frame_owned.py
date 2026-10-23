"""Original four-stage owned monitor, closed no-product Frame target only.

The monitor is unchanged. Its original main has an AST-invertible adaptation
of child command, explicit source roles and truthful read-only result checks.
Neither stage markers nor preserved artifacts authorize a product replay.
"""
import ast
import base64
import copy
import hashlib
import json
import sys
from types import SimpleNamespace as NS
import native011_current_epoch_owned_audit as original
from native011_readonly_frame_driver import timing_summary

SELF='tools/p09/native011_readonly_frame_owned.py'
TEST='tools/p09/tests/test_native011_readonly_frame_owned.py'
TARGET='tools/p09/native011_readonly_frame_entry.py'
CHILD_PASS='PASS_READONLY_NATIVE_FRAME_BOUNDARIES_NOT_PRODUCT_OR_BATCH'
OWNED_PASS='PASS_OWNED_READONLY_NATIVE_FRAME_BOUNDARIES_NOT_PRODUCT_OR_BATCH'
PREFIX='implementation/p09/evidence/p09-361-native011-current805-readonly-frame-probe'
SOURCE=original.SOURCE


def require(ok,code):
    if not ok:raise ValueError('READONLY_FRAME_OWNED_'+code)


def restore_parts(index,read):
    require(type(index) is dict and type(index['bytes']) is int and 0<index['bytes']<=16*1048576,
        'BOUNDED_COMPLETE_FRAME_INDEX')
    count=(index['bytes']+179999)//180000
    require(type(index['parts']) is list and len(index['parts'])==count,'EXACT_PART_COUNT')
    pieces=[]
    for number,pin in enumerate(index['parts']):
        require(pin['path'].endswith(f'.frame-part{number:03}.v1.json'),'ORDERED_PART_PATHS')
        row=read(pin)
        require(row['schema_version']=='hwpx-agent.p09-terminal-frame-part/v1'
            and row['Native_execution_finished'] is True
            and row['Native_or_product_acceptance_qualified'] is False
            and row['index']==number,'EXACT_TERMINAL_PART_ROLE')
        raw=base64.b64decode(row['base64'],validate=True)
        require(len(raw)==row['bytes']==min(180000,index['bytes']-180000*number)
            and hashlib.sha256(raw).hexdigest()==row['sha256'],'FRESH_COMPLETE_PART_BYTES')
        pieces.append(raw)
    raw=b''.join(pieces)
    require(len(raw)==index['bytes'] and hashlib.sha256(raw).hexdigest()==index['sha256'],
        'FULL_ORIGINAL_FRAME_RESTORED_WITHOUT_TRUNCATION')
    require(index['Native_handles_closed_before_output'] is True and index['Native_execution_resumed'] is False,
        'TERMINAL_EVIDENCE_NOT_NEW_NATIVE_EPOCH')
    return json.loads(raw)


def validate_metadata_tail(proof,value):
    require(proof.get('chunk_join_mode') is True and proof.get('exact_read_mode') is True
        and proof.get('decoder_timing_mode') is True,'METADATA_TAIL_REQUIRES_SHARED_EXACT_TIMED_CODEC')
    connected=proof['metadata_tail_connection'];meta=value['metadata'];ledger=value['metadata_tail_reader']
    require(connected['original_metadata_two_point_five_four_MiB_rates_retained'] is True
        and connected['metadata_rate_membership_only_code_inverse'] is True
        and connected['entire_original_metadata_factory_and_Router_code_retained'] is True
        and connected['original_decoder_shared_budget_and_reader_tracking_retained'] is True
        and connected['default_modules_classes_or_ctors_changed'] is False
        and meta['state']=='PASS_ACTUAL_NATIVE011_METADATA_CALLBACK_NOT_NATIVE' and meta['metadata_body_executed'] is True
        and meta['Frame_created'] is meta['worker_created'] is meta['GO_authorized'] is False
        and meta['selected_current_inputs']==proof['current_inputs']
        and ledger['actual_factory_selected_reader'] is True
        and ledger['fresh_inputs']==ledger['final_fresh_hashes']==meta['fresh_inputs']==meta['final_fresh_hashes']>0
        and ledger['physical_read_passes']==meta['physical_read_passes']==ledger['query_requests']
        and ledger['physical_bytes_read']==meta['physical_bytes_read']==ledger['bytes_paced']
        ==ledger['reserved_bytes']-ledger['refunded_bytes']
        and ledger['reservations']>=2*ledger['physical_read_passes']
        and ledger['refunded_bytes']>=ledger['physical_read_passes']
        and ledger['actual_declared_whole_inputs']==proof['whole_inputs']
        and ledger['pending_request'] is ledger['failed'] is ledger['hash_JSON_source_or_closing_cache'] is False,
        'ACTUAL_FULL_METADATA_NOT_CONSTRUCTOR_OR_SMALL_COMPONENT_CREDIT')


def validate(proof,read):
    require(proof['state']==CHILD_PASS and proof['cleanup_confirmed'] is True
        and proof['fresh_inputs']==proof['final_fresh_hashes']
        and proof['readonly_driver_bound'] is True and proof['Frame_instances']==1
        and proof['actual_Native_Frame_created'] is True and proof['actual_product_executed'] is False
        and proof['actual_owned_Native_acceptance_qualified'] is False
        and proof['process_creation_attempts']==0 and proof['shared_budget_restored'] is True
        and proof['Native_clock_reset_or_extended'] is False
        and proof['batch_phase_after_readonly_abort']=='BROKEN'
        and proof['parent_attempts']==1 and proof['worker_attempts']==proof['worker_calls']==0,
        'READONLY_ABORT_NEVER_PRODUCT_OR_BATCH_ACCEPTANCE')
    stages=proof['readonly_stage_records']
    require([r['stage'] for r in stages]==['construction','opening','native']
        and all(r['cleanup_confirmed'] and 0<r['elapsed_seconds']<600 for r in stages)
        and stages[-1]['guard_kind']=='original_Native_no_preparation_relaxation','ORIGINAL_NATIVE600_NOT_ROTATED')
    value=proof['readonly_frame_result'];opening=value['whole_opening']
    if proof.get('metadata_tail_mode') is True:
        validate_metadata_tail(proof,value)
    if proof.get('exact_read_mode') is True:
        exact=value['exact_read_factory']
        require(exact['attempts']==exact['completed']==2 and exact['failed'] is False
            and exact['original_factory_and_workspace_retained'] is True and len(exact['readers'])==2,
            'ACTUAL_TWO_OPTIONAL_EXACT_FACTORIES')
        for reader in exact['readers']:
            require(reader['read_passes']==reader['actual_declared_scope_count']==proof['current_inputs']
                and reader['bytes_read']==reader['bytes_paced']
                and reader['reserved_bytes']-reader['refunded_bytes']==reader['bytes_read']
                and reader['reservations']>=2*proof['current_inputs']
                and reader['refunded_bytes']>=proof['current_inputs']
                and reader['pending_request'] is reader['failed'] is False,
                'ACTUAL_EXACT_FULL_BYTES_EOF_AND_REFUND_ACCOUNTING')
    require(opening['actual_complete'] is True and opening['fresh_inputs']==proof['whole_inputs']
        and value['current_inputs']==proof['current_inputs'] and value['worker_source_count']==201
        and 0<value['readonly600_elapsed_seconds']<600
        and value['product_or_worker_processes_created']==value['GO_writes']==0
        and value['original_Job_commit_supplied'] is False and value['case_finished_called'] is False,
        'REAL_WHOLE_OPENING_AND_NO_SYNTHETIC_COMPLETION')
    require(value['original_parent_wrapper_called'] is True and value['original_parent_wrapper_attempts']==1
        and value['original_engine_body_called'] is False and value['explicit_no_product_delegate_only'] is True,
        'ORIGINAL_PARENT_ATTEMPT_NOT_ENGINE_OR_PRODUCT_ACCEPTANCE')
    loan=value['loan']
    require(loan['restore_confirmed'] is True and loan['failed'] is False
        and loan['armed_handles']==loan['restored_handles']==201,'ALL201_SOURCE_FLAGS_RESTORED')
    frame=restore_parts(proof['full_frame_artifact'],read)
    if proof.get('chunk_join_mode') is True:
        require(proof.get('exact_read_mode') is True and proof.get('decoder_timing_mode') is True,
            'CHUNK_JOIN_REQUIRES_ORIGINAL_EXACT_AND_SHARED_TIMING_MODES')
        codec=proof['chunk_join_codec_connection'];actual=value['chunk_join_actual_Frame']
        require(codec['codec_connection_proof']['exact_original_decoder_AST_inverse'] is True
            and codec['exact_same_metadata_and_Frame_projection_class'] is True
            and codec['original_projection_method_and_property_code_retained'] is True
            and codec['default_module_or_class_changed'] is False
            and actual['actual_Frame_and_metadata_projection_class_same'] is True
            and actual['candidate_codec_namespace_used_by_both'] is True
            and proof['terminal_chunk_join_binding']==actual
            and frame['shared_metadata_frame_decoder']['metadata_completed']==325
            and frame['shared_metadata_frame_decoder']['Frame_completed']==324,
            'ACTUAL_SHARED_CHUNK_CODEC_BOTH_ORIGINAL_FULL_BOUNDARIES_NOT_CONSTRUCTOR_PROOF')
    if proof.get('decoder_timing_mode') is True:
        observed=proof['shared_decoder_timing_observation']
        if 'shared_decoder_timing_observation_artifact' in proof:
            detailed=read(proof['shared_decoder_timing_observation_artifact'])
            require(timing_summary(detailed)==observed,'LOSSLESS_TIMING_ARTIFACT_EXACT_SUMMARY_MATCH')
            observed=detailed
        require(proof.get('exact_read_mode') is True
            and observed['attempts']==observed['completed']==2 and observed['failed'] is False
            and set(observed['roles'])=={'metadata','frame'}
            and observed['original_shared']==frame['shared_metadata_frame_decoder']
            and observed['original_shared_and_budget_method_bodies_retained'] is True,
            'ACTUAL_SHARED_TIMING_NOT_SUBSTITUTED_FOR_FRAME_RESULT')
        for role,count_name in (('metadata','metadata_completed'),('frame','Frame_completed')):
            timing=observed['roles'][role];budget=timing['original_budget']
            require(timing['attempts']==timing['completed']==len(timing['rows'])
                ==budget['attempted_decodes']==budget['completed_decodes']==observed['original_shared'][count_name]
                and timing['failed'] is budget['terminal_error_seen'] is budget['active_decode'] is False
                and budget['aggregate_limit_seconds']==5.
                and timing['original_clock_check_run_body_and_limit_unchanged'] is True
                and timing['observation_not_used_for_admission_or_budget'] is True,
                'COMPLETE_ORIGINAL_ROLE_DECODES_WITHOUT_OBSERVATION_CREDIT')
    if proof.get('exact_read_mode') is True:
        require(all(reader['bytes_read']==frame['input_bytes'] for reader in value['exact_read_factory']['readers']),
            'EXACT_READER_ACCOUNTING_EQUALS_ORIGINAL_FULL_FRAME_BYTES')
    require(frame['frame_state']=='CLOSED' and frame['registered_live_frame'] is False
        and frame['input_count']==proof['current_inputs']
        and frame['original_owned_cleanup_confirmed_before_release'] is False,
        'ORIGINAL_FRAME_CLOSED_WITHOUT_FAKE_OWNED_COMMIT')
    handles=frame['handles']
    policy=frame['parent_python_live_raw_access_policy']
    require(frame['parent_live_raw_policy_installed'] is True and policy['active_scope'] is False
        and policy['all_original_open_function_identities_restored'] is True,
        'ORIGINAL_PARENT_RAW_POLICY_RESTORED')
    require(handles['input_lock_cleanup_confirmed'] is True
        and handles['input_lock_handles_opened']==handles['input_lock_handles_closed']
        and handles['input_lock_handles_remaining']==handles['active_reader_bindings']==handles['active_byte_streams']==0,
        'ALL_ORIGINAL_HANDLES_AND_STREAMS_CLOSED')
    boundaries=frame['actual_byte_boundaries'];require(len(boundaries)==2,'EXACT_TWO_ACTUAL_BOUNDARIES')
    pins=boundaries[0]['actual_byte_pins']
    require(len(pins)==frame['input_count'] and len({p['path'] for p in pins})==len(pins)
        and sum(p['bytes'] for p in pins)==frame['input_bytes'],'WHOLE_FRAME_PIN_ACCOUNTING')
    for role,boundary in zip(('before','after'),boundaries):
        require(boundary['role']==role and boundary['actual_byte_pins']==pins
            and boundary['reader_diagnostics']['read_passes']==len(pins)
            and boundary['reader_diagnostics']['bytes_read']==frame['input_bytes'],'BOTH_COMPLETE_FRESH_BYTE_READS')
    for name,role,count in (('before_coverage','before',1),('restored_coverage','before',1),('after_coverage','after',2)):
        coverage=value[name]
        require(coverage['worker_required_count']==201 and coverage['parent_input_count']==len(pins)
            and coverage['boundary']==role and coverage['actual_parent_byte_boundaries']==count
            and coverage['exact_whole_worker_pin_coverage'] is True
            and coverage['live_original_registry_and_OS_handles_verified'] is True,
            'REAL_LIVE201_COVERAGE_NOT_SERIALIZED_HANDLE')
    shared=frame['shared_metadata_frame_decoder']
    require(shared==value['shared_decoder'] and shared['shared_limit_seconds']==5
        and 0<=shared['total_decoder_work_seconds']<=5
        and shared['metadata_registered'] is True and shared['Frame_registered'] is True
        and shared['terminal_error_seen'] is False,'SINGLE_ORIGINAL_COMBINED_DECODER5')
    return dict(current_inputs=len(pins),whole_inputs=opening['fresh_inputs'],
        two_boundary_bytes=2*frame['input_bytes'],worker_source_count=201,
        Native_elapsed_seconds=value['readonly600_elapsed_seconds'],
        shared_decoder_work_seconds=shared['total_decoder_work_seconds'],
        complete_frame_json_bytes=proof['full_frame_artifact']['bytes'],
        batch_phase='BROKEN',accepted_count_delta=0,product_executed=False)


def project(raw,*,terminal_protocol=False):
    require(type(terminal_protocol) is bool,'EXPLICIT_TERMINAL_PROTOCOL_VERSION')
    before,base_proof=original.project(raw);node=copy.deepcopy(before);changes=[]
    labels={original.LABELS[next(k for k in original.LABELS if k.startswith('implementation/'))]:
        'implementation/p09/evidence/p09-361-native011-current805-readonly-frame-owned',
        'FAILED_OWNED_NATIVE011_METADATA_AND_WHOLE_NOT_NATIVE':'FAILED_OWNED_READONLY_NATIVE_FRAME_NOT_ACCEPTED',
        'PASS_OWNED_NATIVE011_ACTUAL_METADATA_AND_WHOLE_BOUNDARIES_NOT_NATIVE':OWNED_PASS}
    class Adapt(ast.NodeTransformer):
        def visit_Constant(self,n):
            if type(n.value) is str and n.value in labels:
                after=ast.copy_location(ast.Constant(labels[n.value]),n);after._frame_before=copy.deepcopy(n)
                changes.append(n.value);return after
            return n
        def visit_Assign(self,n):
            if len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='command':
                after=ast.parse("command=[sys.executable,'-B',str(c.ROOT/TARGET),'--attempt',str(args.attempt)]").body[0]
                after._frame_before=copy.deepcopy(n);changes.append('command');return after
            return self.generic_visit(n)
        def visit_Expr(self,n):
            if terminal_protocol and ast.dump(n,include_attributes=False)==ast.dump(ast.parse(
                "cleanup_owned(owned,capture,row['owned'],None)").body[0],include_attributes=False):
                after=ast.parse("row['readonly_terminal_protocol']=_cleanup_terminal(owned,capture,row['owned'],monitor)").body[0]
                after._frame_before=copy.deepcopy(n);changes.append('terminal_cleanup');return after
            if isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='require':
                if terminal_protocol and any(isinstance(v,ast.Constant) and v.value=='FOUR_PHASES_AND_KNOWN_EMPTY_JOB'
                        for v in ast.walk(n)):
                    after=ast.parse("_terminal_complete(monitor,row['owned'])").body[0]
                    after._frame_before=copy.deepcopy(n);changes.append('terminal_complete');return after
                if any(isinstance(v,ast.Constant) and v.value=='EXACT_ACTUAL_METADATA_NOT_NATIVE_OR_PRODUCT' for v in ast.walk(n)):
                    after=ast.parse("_readonly_summary=_validate_readonly(proof,lambda pin:a.read_exact(q,pin))").body[0]
                    after._frame_before=copy.deepcopy(n);changes.append('validate');return after
            if (isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute)
                and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=='row' and n.value.func.attr=='update'
                and any(k.arg=='whole_batch' for k in n.value.keywords)):
                after=copy.deepcopy(n);after._frame_before=copy.deepcopy(n)
                after.value.keywords=[k for k in after.value.keywords if k.arg not in ('metadata','whole_batch')]
                after.value.keywords.append(ast.keyword(arg='readonly_Frame_summary',value=ast.Name(id='_readonly_summary',ctx=ast.Load())))
                after=self.generic_visit(after);changes.append('summary');return after
            return self.generic_visit(n)
        def visit_Tuple(self,n):
            if len(n.elts)>2 and isinstance(n.elts[0],ast.Name) and n.elts[0].id=='SELF' and isinstance(n.elts[1],ast.Name) and n.elts[1].id=='TARGET':
                after=copy.deepcopy(n);after._frame_before=copy.deepcopy(n)
                after.elts += [ast.Constant(v) for v in (TEST,original.SELF,'tools/p09/native011_readonly_frame_driver.py',
                    'tools/p09/native011_readonly_frame_probe.py','tools/p09/native011_ready_scope_connection.py',
                    'tools/p09/native011_ready_native_construction.py')]
                if terminal_protocol:after.elts += [ast.Constant(v) for v in (
                    'tools/p09/native011_readonly_terminal_monitor.py','tools/p09/tests/test_native011_readonly_terminal_monitor.py')]
                changes.append('sources');return after
            return self.generic_visit(n)
    node=Adapt().visit(node)
    expected=[*labels,'command','validate','summary','sources']
    if terminal_protocol:expected+=['terminal_cleanup','terminal_complete']
    require(sorted(changes)==sorted(expected),'EXACT_READONLY_MONITOR_ADAPTATIONS')
    class Undo(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,'_frame_before'):return copy.deepcopy(n._frame_before)
            return super().visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==ast.dump(before,include_attributes=False),
        'COMPLETE_READONLY_MONITOR_MAIN_AST_INVERSE')
    return node,dict(original_projection=base_proof,readonly_main_AST_inverse=True,
        original_Monitor_Job_capture_cleanup_deadlines_retained=True,product_authorized=False,
        terminal_protocol=terminal_protocol,terminal_marker_has_no_live_epoch_credit=terminal_protocol,
        post_cleanup_audit_has_distinct_actual_guard=terminal_protocol)


def main():
    from pathlib import Path
    import native011_readonly_terminal_monitor as terminal_protocol
    require(sys.argv[1:] in (['--attempt','1','--generation','3'],['--attempt','2','--generation','3'],
        ['--attempt','3','--generation','3'],['--attempt','4','--generation','3'],
        ['--attempt','5','--generation','3'],['--attempt','6','--generation','3'],
        ['--attempt','7','--generation','3'],['--attempt','8','--generation','3']),'ONLY_CLOSED_NO_PRODUCT_READONLY_MONITOR')
    root=Path(__file__).resolve().parents[2];raw=(root/SOURCE['path']).read_bytes();node,_=project(raw,terminal_protocol=True)
    env=dict(__name__='p09_readonly_frame_owned_private',__file__=SOURCE['path'])
    exec(compile(raw,SOURCE['path'],'exec'),env)
    def terminal(owned,capture,row,stdout,stderr,monitor):
        return original.preserve_terminal_failure(owned,capture,row,stdout,stderr,NS(seen=monitor.seen,MARKERS=env['MARKERS']))
    def observing(monitor,markers,owned,capture,row):
        return original.observe_markers(monitor,markers,owned,capture,row,terminal)
    def cleanup_terminal(owned,capture,result,monitor):
        return terminal_protocol.cleanup_and_audit(owned,capture,result,monitor,env['cleanup_owned'])
    Monitor=terminal_protocol.monitor_type(env['Monitor'],env['MARKERS'],('construction','opening','native_readonly'))
    env.update(SELF=SELF,TARGET=TARGET,STAGES=('construction','opening','native_readonly','terminal_evidence'),
        _preserve_terminal_failure=terminal,_observe_markers=observing,_validate_readonly=validate,Monitor=Monitor,
        _cleanup_terminal=cleanup_terminal,_terminal_complete=lambda monitor,result:monitor.terminal_complete(result))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),SOURCE['path'],'exec'),env)
    return env['main']()


if __name__=='__main__':raise SystemExit(main())
