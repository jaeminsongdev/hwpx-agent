"""Whole original readonly evidence checks plus exact worker202/no-GO checks.

Historical201 validation is unchanged. A private whole-AST inverse selects202,
one diagnostic child, and the actual owned metadata factory. All original byte,
handle, raw-policy, decoder5, Native600, cleanup and failed-batch checks remain.
"""
import ast
import copy
import hashlib
import math
from types import CodeType, FunctionType, SimpleNamespace as NS

SELF='tools/p09/native011_full_frame_worker_validation.py'
TEST='tools/p09/tests/test_native011_full_frame_worker_validation.py'
SOURCE=dict(path='tools/p09/native011_readonly_frame_owned.py',bytes=20555,
    sha256='562f48c18ae4e24c8f4698c38e0d1362480d38742288793cbb9c00a2cb6b0e01')
CHILD_PASS='PASS_FULL_FRAME_WORKER202_READY_REAL_EOF_NOT_PRODUCT_OR_BATCH'
ENGINE=dict(path='tools/p09/run_case112_current_stored.py',bytes=23159,
    sha256='6f2a79556ebcfae40765ebd127a8fcc1022e5ee8611d666fd3daa723a4236713')
RATES=dict(binary=1048576,other=2097152)


def require(ok,code):
    if not ok:raise ValueError('FULL_FRAME_WORKER_VALIDATION_'+code)


def finite(value,minimum,maximum):
    return type(value) in (int,float) and math.isfinite(value) and minimum<=value<maximum


def declared_worker(read,control,qualification,scope):
    """Closed qualified declaration only, never former byte/READY credit."""
    prior=control.declarations(read(control.READY),scope)
    proof=read(qualification.READY);pins=scope.pins(proof['source_pins'])
    entry=pins[qualification.CHILD]
    required,_=qualification.qualified(proof,prior,entry,scope)
    require(len(required)==202 and required[qualification.CHILD]==entry,'CLOSED_QUALIFIED_SOURCE202_DECLARATION')
    return {name:dict(pin) for name,pin in required.items()}


def project(raw,original,*,extra_functions=()):
    require(type(raw) is bytes and len(raw)==SOURCE['bytes']
        and hashlib.sha256(raw).hexdigest()==SOURCE['sha256'],'EXACT_ORIGINAL_WHOLE_VALIDATOR_SOURCE')
    require(extra_functions in ((),('project',)),'CLOSED_ADDITIONAL_ORIGINAL_FUNCTION_ATTESTATION')
    names=('restore_parts','validate_metadata_tail','validate');checked_names=names+extra_functions
    filename=original.validate.__code__.co_filename
    require(filename.replace('\\','/').endswith(SOURCE['path']),'ORIGINAL_VALIDATOR_FUNCTION_ORIGIN')
    tree=ast.parse(raw)
    def matches(compiled):
        expected={value.co_name:value for value in compiled.co_consts if type(value) is CodeType and value.co_name in checked_names}
        return set(expected)==set(checked_names) and all(type(getattr(original,name)) is FunctionType
            and getattr(original,name).__code__==expected[name] for name in checked_names)
    matched=matches(compile(raw,filename,'exec'))
    if not matched:
        matched=matches(compile(ast.fix_missing_locations(ast.Module(body=[node for node in tree.body
            if not isinstance(node,(ast.Import,ast.ImportFrom))],type_ignores=[])),filename,'exec'))
    require(matched,'ALL_THREE_ORIGINAL_VALIDATOR_FUNCTION_CODES')
    nodes={node.name:node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names}
    selected={name:copy.deepcopy(node) for name,node in nodes.items()}
    counts=dict(worker=0,label=0,process=0,metadata_owner=0,unused_field=0)
    process=ast.parse("value['product_or_worker_processes_created']==value['GO_writes']==0",mode='eval').body
    connected=ast.parse("connected=proof['metadata_tail_connection']").body[0]
    def changed(after,before):
        after=ast.copy_location(after,before);after._worker_before=copy.deepcopy(before);return after
    class Frame(ast.NodeTransformer):
        def visit_Compare(self,node):
            if ast.dump(node,include_attributes=False)==ast.dump(process,include_attributes=False):
                counts['process']+=1
                return changed(ast.parse("value['product_or_worker_processes_created']==1 and value['GO_writes']==0",mode='eval').body,node)
            return self.generic_visit(node)
        def visit_Constant(self,node):
            if type(node.value) is int and node.value==201:
                counts['worker']+=1;return changed(ast.Constant(202),node)
            labels={'ALL201_SOURCE_FLAGS_RESTORED':'ALL202_SOURCE_FLAGS_RESTORED',
                'REAL_LIVE201_COVERAGE_NOT_SERIALIZED_HANDLE':'REAL_LIVE202_COVERAGE_NOT_SERIALIZED_HANDLE'}
            if type(node.value) is str and node.value in labels:
                counts['label']+=1;return changed(ast.Constant(labels[node.value]),node)
            return node
    class Metadata(ast.NodeTransformer):
        def visit_Assign(self,node):
            if ast.dump(node,include_attributes=False)==ast.dump(connected,include_attributes=False):
                counts['metadata_owner']+=1
                return changed(ast.parse("connected=proof['metadata_tail_connection']['metadata_factory_connection']").body[0],node)
            return self.generic_visit(node)
        def visit_Subscript(self,node):
            if (isinstance(node.value,ast.Name) and node.value.id=='connected' and isinstance(node.slice,ast.Constant)
                and node.slice.value in ('original_metadata_two_point_five_four_MiB_rates_retained','metadata_rate_membership_only_code_inverse')):
                counts['unused_field']+=1
                after=copy.deepcopy(node);after.value=ast.parse("connected['unused_allocator_stage']",mode='eval').body
                return changed(after,node)
            return self.generic_visit(node)
    selected['validate']=Frame().visit(selected['validate'])
    selected['validate_metadata_tail']=Metadata().visit(selected['validate_metadata_tail'])
    require(counts==dict(worker=4,label=2,process=1,metadata_owner=1,unused_field=2),'EXACT_CLOSED_VALIDATOR_EDIT_SITES')
    class Undo(ast.NodeTransformer):
        def visit(self,node):
            if hasattr(node,'_worker_before'):return copy.deepcopy(node._worker_before)
            return super().visit(node)
    for name in names:
        require(ast.dump(Undo().visit(copy.deepcopy(selected[name])),include_attributes=False)
            ==ast.dump(nodes[name],include_attributes=False),'ENTIRE_ORIGINAL_VALIDATOR_AST_INVERSE')
    env=dict(original.validate.__globals__,CHILD_PASS=CHILD_PASS)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[selected['validate_metadata_tail'],selected['validate']],
        type_ignores=[])),filename,'exec'),env)
    return NS(frame=env['validate'],metadata=env['validate_metadata_tail'],restore=original.restore_parts),dict(
        entire_original_three_function_AST_inverse=True,changes=counts,original_decoder_counts325_324_retained=True,
        exact_original_function_codes_attested=len(checked_names),
        original_whole_byte_raw_policy_Handle_cleanup_Native600_decoder5_and_abort_checks_retained=True,
        old_validator_or_receipts_mutated=False,GO_authorized=False)


def metadata_checks(proof,value,original):
    original(proof,value)
    connected=proof['metadata_tail_connection'];factory=connected['metadata_factory_connection']
    stage=factory['engine_assignment_stage'];ledger=value['metadata_tail_reader'];meta=value['metadata']
    adopted=ledger['actual_owned_engine_adoption'];prefix=meta['original_owned_allocation_assignment_prefix']
    paced=ledger['actual_paced_bytes_by_kind']
    require(connected['original_engine_owned_assignment_required'] is True
        and connected['original_engine_metadata_IO_rates']==RATES
        and connected['default_candidate_or_original_classes_mutated'] is False
        and connected['reader_allocations_during_connection']==0
        and stage['original_engine_assignment_required_before_IO'] is True
        and stage['original_owned_binary1_other2_MiB_rates_retained'] is True
        and stage['all_original_read_wrappers_still_called'] is True
        and stage['used_or_failed_pacer_reset_permitted'] is False
        and stage['original_Native_guard_deadline_or_shared_budget_changed'] is False,
        'ORIGINAL_OWNED_ASSIGNMENT_BEFORE_ALL_METADATA_IO')
    require(ledger['original_metadata_binary2p5_other4_MiB_policy_retained'] is False
        and ledger['original_owned_binary1_other2_MiB_policy_retained'] is True
        and ledger['actual_metadata_rates']==RATES and adopted['original_owned_rates']==RATES
        and adopted['assignment_attempts']==adopted['assignment_completed']==1 and adopted['failed'] is False
        and adopted['original_engine_owned_assignment_adopted'] is True
        and adopted['source_table_and_read_proxy_retained'] is True
        and adopted['physical_read_passes']==ledger['physical_read_passes']
        and adopted['physical_bytes_read']==ledger['physical_bytes_read']
        and adopted['semantic_fresh_inputs']==adopted['semantic_final_fresh_hashes']==ledger['fresh_inputs']
        and set(paced)<=set(RATES) and all(type(number) is int and number>=0 for number in paced.values())
        and sum(paced.values())==ledger['physical_bytes_read'],'ACTUAL_ONE_TWO_MIB_ASSIGNMENT_AND_COMPLETE_PACED_BYTES')
    require(prefix['whole_original_engine_source_pin']==ENGINE and prefix['original_statements_executed']==2
        and prefix['actual_factory_and_byte_policy_dependencies_used'] is True
        and prefix['GO_authorized'] is False and meta['preparation_only_owned_allocation'] is True
        and meta['complete_product_input_pins_qualified'] is False,'ORIGINAL_TWO_STATEMENT_PREFIX_NOT_PRODUCT_BODY_CREDIT')


def coverage(value,required,parent_count):
    require(value['worker_required_count']==len(required)==202 and value['parent_input_count']==parent_count
        and value['boundary']=='before' and value['actual_parent_byte_boundaries']==1
        and value['exact_whole_worker_pin_coverage'] is True
        and value['live_original_registry_and_OS_handles_verified'] is True,'WORKER_USES_THE_SAME_WHOLE_FIRST_BOUNDARY')


def worker_checks(proof,frame,required,validate_child,digest):
    require(type(required) is dict and len(required)==202 and all(name==pin['path'] for name,pin in required.items()),
        'EXACT_DECLARED_WORKER202_PIN_MAPPING')
    actual={pin['path']:pin for pin in frame['actual_byte_boundaries'][0]['actual_byte_pins']}
    require(set(required)<=set(actual) and all(actual[name]==pin for name,pin in required.items()),
        'ALL202_DECLARED_SOURCE_PINS_IN_ACTUAL_FULL_NATIVE_BYTE_BOUNDARY')
    value=proof['readonly_frame_result'];phase=value['whole_Frame_worker_ready'];link=proof['full_frame_worker_connection']
    worker=phase['worker'];audit=link['process_audit']
    require(phase['callback_attempts']==1 and phase['callback_completed'] is True
        and phase['original_product_Job_or_commit_qualified'] is False and phase['product_or_GO_authorized'] is False
        and link['worker']==worker and link['full_Native_phase_created'] is True
        and link['actual_whole_Frame_or_child_executed'] is True and link['metadata_allocation_or_body_executed'] is True
        and link['original_product_parent_still_denied'] is True,'ONE_ACTUAL_NO_GO_CALLBACK_AND_UNCHANGED_PRODUCT_DENIAL')
    require(all(type(audit[key]) is int and audit[key]==1 for key in ('original_process_denial_registrations',
        'exact_child_factory_attempts','exact_worker_Popen_events_allowed'))
        and audit['other_Popen_events_denied']==0 and audit['launch_scope_active'] is False
        and audit['product_GO_or_intent_authorized'] is False,'ONE_CLOSED_NO_GO_PROCESS_AUDIT_NOT_RETRY_PERMISSION')
    require(worker['state']=='PASS_WHOLE_FRAME_WORKER202_SOURCE_READY_REAL_EOF_NOT_NATIVE_ACCEPTANCE'
        and worker['cleanup_confirmed'] is True and worker['child_launch_attempts']==1
        and worker['child_exit_code']==1 and worker['product_GO_writes']==0
        and worker['original_product_Job_or_commit_qualified'] is False
        and worker['original_Native_Frame_and_guard_closed_by_child_probe'] is False
        and worker['preparation_only_nested_Job_not_product_Job'] is True
        and finite(worker['elapsed_seconds'],0,value['readonly600_elapsed_seconds']),'ACTUAL_SOURCE_CHILD_CLEANUP_NOT_PRODUCT_OR_NATIVE_ACCEPTANCE')
    gate=worker['readiness']
    require(gate['readiness_limit_seconds']==15 and finite(gate['readiness_elapsed_seconds'],0,15)
        and gate['readiness_confirmed'] is True and gate['stopped'] is True and gate['actual_original_GO_written'] is False,
        'ORIGINAL_READY15_AND_EXACT_GO_DENIAL')
    validate_child(worker['child'],required,digest)
    for field in ('before_coverage','restored_coverage'):coverage(worker[field],required,len(actual))
    handoff=worker['source_handoff']
    require(handoff['failed'] is False and handoff['spawn_attempts']==1
        and handoff['process_returned_for_original_cleanup'] is True
        and handoff['source_flags_and_descriptor_cleanup_errors']==[]
        and handoff['preparation_START_sent'] is True and handoff['original_Gate15_bound'] is True
        and handoff['raw_START_outside_original_product_Input10'] is True
        and handoff['source_bytes_hashes_JSON_or_AST_cached'] is False
        and handoff['original_parent_byte_read_credit_changed'] is False
        and handoff['original_Job_or_deadline_or_resource_policy_changed'] is False
        and handoff['product_GO_written_by_handoff'] is False,'ORIGINAL_HANDLE_TRANSFER_START_AND_CLEANUP_WITHOUT_BYTE_CREDIT')
    limits=worker['preparation_job_limits'];parent=limits['parent_original_limit_readback']
    require(limits==worker['preparation_job_limits_after_ready'] and limits['verified'] is True
        and parent['verified'] is True and parent['cpu_hard_cap_machine_percent']==limits['maximum_system_CPU_percent']==6.25
        and limits['relative_parent_cpu_hard_cap_percent']==100 and limits['default_Windows_or_Native_policy_changed'] is False
        and limits['product_or_GO_authorized'] is False and worker['inner_job_final']['active_processes']==0,
        'PREPARATION_ONLY_RELATIVE_JOB_WITH_VERIFIED_MACHINE_CAP_AND_EMPTY_TREE')
    for key,expected in (('affinity_mask',1),('priority_class',16384),('active_process_limit',16),
        ('kill_on_close',True),('breakaway_disabled',True)):
        require(parent[key]==expected,'ORIGINAL_PARENT_JOB_PROTECTIONS')
        if key!='active_process_limit':require(limits[key]==expected,'ORIGINAL_INNER_PREPARATION_JOB_PROTECTIONS')
    require(finite(parent['job_private_limit_mib'],1,float('inf'))
        and limits['job_private_limit_mib']==parent['job_private_limit_mib'],'UNCHANGED_INNER_RAM_LIMIT')


def build(raw,original,validate_child,digest,*,extra_functions=()):
    selected,projection=project(raw,original,extra_functions=extra_functions)
    require(callable(validate_child) and callable(digest),'EXPLICIT_ORIGINAL_CHILD_AND_PIN_DIGEST_CHECKERS')
    def validate(proof,read,required):
        require(proof.get('metadata_tail_mode') is proof.get('exact_read_mode') is proof.get('decoder_timing_mode')
            is proof.get('chunk_join_mode') is True,'COMPLETE_ORIGINAL_TIMED_EXACT_SHARED_OWNED_METADATA_MODE')
        restored=[]
        def restore(index,reader):
            require(not restored,'ONE_ORIGINAL_FULL_FRAME_RESTORATION')
            frame=selected.restore(index,reader)
            worker_checks(proof,frame,required,validate_child,digest);restored.append(True)
            return frame
        def metadata(proof,value):return metadata_checks(proof,value,selected.metadata)
        old=selected.frame
        fn=FunctionType(old.__code__,dict(old.__globals__,restore_parts=restore,validate_metadata_tail=metadata),
            argdefs=old.__defaults__,closure=old.__closure__);fn.__kwdefaults__=old.__kwdefaults__
        result=fn(proof,read)
        require(restored==[True],'ADDITIONAL_WORKER_CHECKS_USE_SAME_ORIGINAL_RESTORED_FRAME')
        return dict(result,source_worker_creation_attempts=1,legacy_denied_process_counter=proof['process_creation_attempts'],
            actual_source_worker_READY_and_EOF_qualified=True,original_product_Job_or_commit_qualified=False,
            product_GO_writes=0,GO_authorized=False)
    return NS(validate=validate,projection=projection)
