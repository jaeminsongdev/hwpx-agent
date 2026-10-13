"""P250: metadata 형식 연결 오류를 검토한 후 metadata STOP 후 전체1539입력/Native20·metadata32 실행기.

원 P238 actual79/기존 수용 코드를 고치지 않는다. 원 CPU·RAM·Job·두 실제
읽기·Native pacing·실패 차단을 유지하고 P239의 새 Capture를 명시적으로
선택한다. 실제 pre-GO CPU stress는 수행하지 않는다.
"""
import argparse
import copy
import hashlib
import io
import json
import re
import sys
import unittest
from unittest.mock import patch
import resume_lower_native_runtime as previous
import qualify_metadata_read_entry_pacing as entry_support
metadata_review=entry_support.reviewed
entry=entry_support.pacing
import review_native_acquisition_stop as acquisition
import qualify_lower_native_acquisition_pressure as lower_support
lower=lower_support.lower
import qualify_uncreated_borrower_failure as support
accepted=previous.accepted
candidate=support.candidate

r=accepted.r;p=r.p;g=r.g;review=accepted.review;closing=accepted.closing
SELF='tools/p09/resume_metadata_entry_runtime_r3.py'
TEST='tools/p09/tests/test_metadata_entry_runtime_r3.py'
NEW=(metadata_review.SELF,metadata_review.TEST,entry.SELF,entry.TEST,entry_support.SELF,SELF,TEST)
EXTRAS=(*previous.EXTRAS,*NEW)
COMPOUND=dict(path=p.DIR+'/p236-case078-compound-run01.v1.json',bytes=355396,
    sha256='1761365334369863fd3aaf9afc5747456b6a4101dac37cdddbb9e69b3cfbf462')
HEALTHY=dict(path=p.DIR+'/p238-case-079-run002.v1.json',bytes=587604,
    sha256='a26dbc68b08b95a4b4f124f3e5ccb19377b27c4f8a19e5f88acb802288ad9b31')
SUPPORT=dict(path=p.DIR+'/p239-uncreated-borrower-support-run01.v1.json',bytes=4694,
    sha256='c05d84929932d7b99ec988eaef0137ec53b75869f115ae5e69b625fd83a5cfc4')
ACQUISITION_REVIEW=lower_support.REVIEW
LOWER_SUPPORT=dict(path=p.DIR+'/p243-lower-native20-support-run01.v1.json',bytes=15250,
    sha256='b468a36fb3586ecd83758fa220ab5a57bc9092850b3fcbdcbf04a1360abf9dca')
METADATA_REVIEW=entry_support.REVIEW
ENTRY_SUPPORT=dict(path=p.DIR+'/p246-metadata-entry32-support-run01.v1.json',bytes=10741,
    sha256='f44f9c27d569213536cfadc14969f6ef5195f4b883cecc451609b87e859bc261')
PROTOTYPE_FAILURE=dict(path=p.DIR+'/p248-light-run001.v1.json',bytes=139294,
    sha256='d70c4606a6e396dd148236a3444ed9824835dcf414ce66df9366b1708c452c12')
PROTOTYPE_SOURCES=(dict(path='tools/p09/resume_metadata_entry_runtime.py',bytes=31796,
    sha256='4c940a482210cd15e87676837d6aafb68232233ccc30a5ab76f3405d66f00ae1'),
    dict(path='tools/p09/tests/test_metadata_entry_runtime.py',bytes=2631,
    sha256='a637a626e2ce3be641ccbf5687a2698a862776005d520c3c7e0f7ab6df3b344b'))
BUDGET_FAILURE=dict(path=p.DIR+'/p249-light-run001.v1.json',bytes=246502,
    sha256='fdd23ccb0ee0f940ce9509c34cc38673426c6347ae512ca19a092c4556b5781d')
BUDGET_SOURCES=(dict(path='tools/p09/resume_metadata_entry_runtime_r2.py',bytes=34181,
    sha256='bbe358fc1b8747b67fd6afae3f7d112b61ccceafcae6c9d71fe248898a6692e6'),
    dict(path='tools/p09/tests/test_metadata_entry_runtime_r2.py',bytes=2636,
    sha256='05a9838c8e03e7ed9b54ddd43aec241f0808853af7971f531ad002db51d47e56'))
META_READ_LIMIT=720
SCHEMA='hwpx-agent.p09-metadata-entry32-runtime-pair-r3/v1'
PASS='PASS_EXACT_R07_METADATA_ENTRY32_R3_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT='PASS_METADATA_ENTRY32_R3_SELECTION_NOT_ACTUAL_OR_GATE'
FILE=re.compile(r'p250-case-([0-9]{3})-run([0-9]{3})\.v1\.json')


def require(ok,code):p.require(ok,'POST_STOP_RUNTIME_'+code)


class Reader(previous.Reader):
    def __init__(self,owner,context):
        super().__init__(owner,context)
        if not hasattr(owner,'_p250_metadata_budget'):owner._p250_metadata_budget=dict(read_calls=0)
        self.shared_budget=owner._p250_metadata_budget
        self.entry_binding=entry.Binding(self.reader)
        original=self.entry_binding.original
        def bounded(name,parse=False):
            require(self.shared_budget['read_calls']<META_READ_LIMIT,'METADATA_READ_CALL_BUDGET720')
            self.shared_budget['read_calls']+=1
            return original(name,parse=parse)
        self.entry_binding.original=bounded
        self.entry_binding.__enter__()
    def close_entry(self):
        if self.entry_binding.active:self.entry_binding.__exit__(None,None,None)
    def finish(self):
        try:return super().finish()
        finally:self.close_entry()
    def summary(self):
        row=super().summary()
        row['metadata_read_entry_pacing']=self.entry_binding.summary()
        row['shared_metadata_read_budget_limit']=META_READ_LIMIT
        return row
    def json(self,path):
        carrier=super().json(path);name=self.name(path)
        if name.startswith(p.DIR+'/p250-') or name.startswith(p.DIR+'/cases/p250-'):
            r.h.canonical(carrier,self.reader.snapshots[name],self.checkpoint)
            return r.packed.unpack(carrier,self.checkpoint) if carrier.get('schema_version')==r.packed.SCHEMA else carrier
        return carrier


def anchor(q):
    # 불변 P244 anchor가 원 계약·52/16지원·기존 source를 이미 strict 검증한다.
    # 새 caller에서 그 지원 검증을 다시 복제하지 않는다. 새 proof 검증과
    # 모든 기존 실제 fresh 읽기·최종 fresh는 그대로 유지한다.
    legacy,base,names,expected,exe,old_required,old_extras=previous.anchor(q)
    require(base['runtime_source_qualified_individual_cases']==73 and base['next_runtime_index']==80
        and q.reader.snapshots[HEALTHY['path']]==HEALTHY,'SEALED_ACTUAL79_NOT_REEXECUTED')
    reviewed_prototype_error(q);reviewed_budget_failure(q)
    reviewed_metadata_stop(q,base,old_required,old_extras)
    added={name:q.pin(name) for name in NEW};require(not set(added)&set(old_required),'ONLY_NEW_INPUTS')
    required={**old_required,**added};extras={**old_extras,**added}
    require(len(required)==1539 and len(extras)==72 and len(added)==7,'ALL_ORIGINAL1532_PLUS_SEVEN')
    enforce_scope_budget(required,old_required,added,connected_budget())
    return legacy,base,names,expected,exe,required,extras


def connected_budget():
    initial=entry.estimate_budget(lower.estimate(1525,14216704,104805351,119.5))
    out=dict(initial);out.update(metadata_original_read_calls_upper_bound=META_READ_LIMIT,
        additional_metadata_entry_seconds=META_READ_LIMIT/32,
        predicted_combined_seconds_with_allowances=initial['predicted_combined_seconds_with_allowances']+(META_READ_LIMIT-660)/32,
        original_support660_prediction_preserved=True,original_CPU_RAM_IO_guards_not_extended=True,
        count_forecast_revised_from_unexecuted_final_fresh_inventory=True,
        observed_full_preparation_read_count_required_without_reduction=660+242-212,
        observed_budget_failure_pin=BUDGET_FAILURE)
    require(out['predicted_combined_seconds_with_allowances']<600,'BUDGET_FITS_UNCHANGED600')
    return out


def reviewed_budget_failure(q):
    failed=review.bound_json(q,BUDGET_FAILURE);row=failed['preparation_IO'];own=row['metadata_read_entry_pacing']
    require(failed['schema_version']=='hwpx-agent.p09-metadata-entry32-runtime-pair-r2/v1'
        and failed['state']=='FAILED_NOT_ACCEPTED'
        and failed['error_code']=='P208_POST_STOP_RUNTIME_METADATA_READ_CALL_BUDGET660'
        and failed['resource_stop_reason'] is None and failed['resource_watcher_cleanup_confirmed'] is True
        and failed['selected_test_index']==80 and failed['accepted_exact_product_body_count']==0
        and all(failed[k] is False for k in ('frame_acquisition_requested','frame_acquisition_complete',
            'product_worker_invocation_requested','actual_product_child_executed'))
        and failed['current_queue_runtime_contract_tests_passed']==156
        and failed['post_stop_runtime_contract_tests_passed']==18
        and failed['uncreated_borrower_connection_contract_tests_passed']==8
        and failed['lower_native_runtime_contract_tests_passed']==8
        and failed['metadata_entry_runtime_contract_tests_passed']==12
        and row['finished'] is False and row['read_passes']==660 and row['bound_inputs']==242
        and row['final_fresh_hashes']==212 and row['bytes_read']==232321042
        and row['shared_metadata_read_budget_limit']==660
        and own['completed_original_read_calls']==660 and own['entry_calls']==own['reservations']==661
        and own['failed_calls']==1 and own['binding_active'] is False,
        'EXACT_UNEXECUTED_COUNT_FORECAST_FAILURE_NOT_CPU_STOP')
    for pin in BUDGET_SOURCES:require(q.pin(pin['path'])==pin,'BUDGET_PROTOTYPE_SOURCE_PRESERVED')
    folder=p.c.ROOT/p.DIR
    require(sorted(path.name for path in folder.glob('p249-light-run*.v1.json'))==['p249-light-run001.v1.json']
        and not list(folder.glob('p249-admission-run*.v1.json'))
        and not list(folder.glob('p249-case-*-run*.v1.json'))
        and not list((folder/'cases').glob('p249-*080*.json')),'NO_UNKNOWN_BUDGET_PROTOTYPE_BODY')

def reviewed_prototype_error(q):
    failed=review.bound_json(q,PROTOTYPE_FAILURE)
    require(failed['schema_version']=='hwpx-agent.p09-metadata-entry32-runtime-pair/v1'
        and failed['state']=='FAILED_NOT_ACCEPTED' and failed['error_code']=='P152_FULL_REDACTED_FAILURE'
        and failed['resource_stop_reason'] is None and failed['resource_watcher_cleanup_confirmed'] is True
        and failed.get('selected_test_index') is None
        and all(failed[k] is False for k in ('frame_acquisition_requested','frame_acquisition_complete',
            'product_worker_invocation_requested','actual_product_child_executed'))
        and failed['preparation_IO']['finished'] is False
        and failed['preparation_IO']['read_passes']==397 and failed['preparation_IO']['bytes_read']==134533809
        and failed['preparation_IO']['final_fresh_hashes']==0,'EXACT_UNEXECUTED_NON_CPU_PROTOTYPE_FAILURE')
    metadata_contract(failed['preparation_IO'])
    for pin in PROTOTYPE_SOURCES:require(q.pin(pin['path'])==pin,'PROTOTYPE_SOURCE_NOT_EDITED_OR_PROMOTED')
    folder=p.c.ROOT/p.DIR
    require(sorted(path.name for path in folder.glob('p248-light-run*.v1.json'))==['p248-light-run001.v1.json']
        and not list(folder.glob('p248-admission-run*.v1.json'))
        and not list(folder.glob('p248-case-*-run*.v1.json'))
        and not list((folder/'cases').glob('p248-*080*.json')),'NO_UNKNOWN_PROTOTYPE_EXECUTION')
    # 원 receipt에 없는 필드 참조는 controller pin 목록으로 교정한다.
    # 이 explicit 미실행 실패 검토가 CPU STOP/본문 실패 재시도를 허용하지 않는다.


def reviewed_metadata_stop(q,base,required,extras):
    failed=review.bound_json(q,metadata_review.ROOT_PIN)
    checked=review.bound_json(q,METADATA_REVIEW)
    require(checked['state']==metadata_review.PASS and checked['review']==metadata_review.review(failed)
        and checked['metadata_stop_contract_tests_passed']==12 and checked['peak_summary_contract_tests_passed']==8
        and checked['IO']['finished'] is True and checked['IO']['bound_inputs']==checked['IO']['final_fresh_hashes']==8
        and checked['resource_stop_reason'] is None and checked['resource_watcher_cleanup_confirmed'] is True,
        'REVIEWED_METADATA_STOP_NOT_RETRY_OR_ACCEPTANCE')
    light=review.bound_json(q,metadata_review.LIGHT_PIN)
    require(light['state']==previous.LIGHT and light['prior_runtime_plan']==base and light['selected_test_index']==80
        and light['resource_stop_reason'] is None and light['resource_watcher_cleanup_confirmed'] is True
        and light['current_queue_runtime_contract_tests_passed']==156 and light['post_stop_runtime_contract_tests_passed']==18
        and light['uncreated_borrower_connection_contract_tests_passed']==8
        and light['lower_native_runtime_contract_tests_passed']==8
        and p.v.pins(light['extra_frame_controller_pins'])==extras,'SEALED_PRIOR190_AND_FULL1532')
    folder=p.c.ROOT/p.DIR
    require(sorted(path.name for path in folder.glob('p244-admission-run*.v1.json'))==['p244-admission-run002.v1.json']
        and sorted(path.name for path in folder.glob('p244-light-run*.v1.json'))==['p244-light-run001.v1.json']
        and not list(folder.glob('p244-case-*-run*.v1.json'))
        and not list((folder/'cases').glob('p244-*080*.json')),'NO_UNKNOWN_PRIOR_ATTEMPT_OR_BODY')
    pins=p.v.pins(light['extra_frame_controller_pins'])
    for name in (previous.SELF,previous.TEST):require(q.pin(name)==pins[name],'UNCHANGED_P244_SOURCE')
    pins=p.v.pins(checked['bound_input_pins'])
    for name in (metadata_review.SELF,metadata_review.TEST):require(q.pin(name)==pins[name],'UNCHANGED_REVIEW_SOURCE')
    support_doc=review.bound_json(q,ENTRY_SUPPORT);entry_support.validate(support_doc)
    require(support_doc['state']==entry_support.PASS and support_doc['actual_runtime_connection_qualified'] is False
        and support_doc['reviewed_metadata_stop_pin']==metadata_review.ROOT_PIN
        and support_doc['reviewed_metadata_receipt_pin']==METADATA_REVIEW
        and support_doc['resource_stop_reason'] is None and support_doc['resource_watcher_cleanup_confirmed'] is True,
        'SEALED_ENTRY25_SMALL_NOT_FULL_RUNTIME')
    for pin in support_doc['bound_input_pins']:require(q.pin(pin['path'])==pin,'UNCHANGED_ENTRY_SUPPORT_SOURCES')
    require(len(required)==1532,'ALL_PRIOR1532_INPUTS')
    return failed


def enforce_scope_budget(required,original,added,budget):
    require(set(original)<set(required) and required=={**original,**added}
        and len(original)==1532 and len(required)==1539 and len(added)==7
        and len(required)<=budget['new_runtime_inputs_upper_bound']==1540
        and original[p.m.EXE['path']]==p.m.EXE and sum(pin['bytes'] for pin in required.values())-119022055
            <=budget['future_added_controller_bytes_upper_bound']==1048576
        and budget==connected_budget(),
        'EXACT_SCOPE_BUDGET_NO_IO_EXTENSION')


def metadata_contract(row):
    own=row['metadata_read_entry_pacing'];count=row['read_passes']
    require(own['completed_original_read_calls']==own['reservations']==own['entry_calls']==count
        and own['failed_calls']==0 and own['binding_active'] is False
        and own['maximum_metadata_read_entries_per_second']==32
        and row['shared_metadata_read_budget_limit']==META_READ_LIMIT and 0<count<=META_READ_LIMIT,
        'ALL_ORIGINAL_METADATA_READS_PACED_AND_CLOSED')
    require(all(own[k] is True for k in ('no_idle_burst','original_reader_and_bytes_and_fresh_checks_preserved',
        'original_CPU_RAM_IO_and_parse_budget_preserved','original_pressure_checkpoint_reused','cleanup_not_guarded_or_paced'))
        and all(own[k] is False for k in ('extra_sampler_or_thread_started','original_reads_skipped',
            'cached_pins_or_parsed_JSON_substituted','measured_CPU_or_PC_freeze_improvement_claimed')),
        'ORIGINAL_METADATA_POLICY_NOT_RELAXED')

def lower_contract(own):
    require(own['lower_native_fan_out']==dict(original_upper_ceiling_per_second=32,
        selected_maximum_reservations_per_second=20,nominal_reservation_density_reduction_percent=37.5,
        original_pacer_and_no_burst_preserved=True,original_CPU_RAM_IO_lock_guards_preserved=True,
        all_identity_and_byte_checks_retained=True,cleanup_not_rate_or_pressure_guarded=True,
        measured_CPU_or_PC_freeze_improvement_claimed=False),'EXACT_RATE20_WITHOUT_GUARD_OR_CPU_CLAIM')


def native_pair(component,body,pin,required,binding,extras):
    p.validate_closing(component,body,pin,required,binding,extras)
    n=len(required);frame=component['source_frame'];own=frame['handles'];dup=own['borrowed_byte_streams']
    require(n==1539 and own['input_lock_handles_opened']==own['input_lock_handles_closed']==n+306
        and own['maximum_lock_seconds']==600 and own['ancestor_walk_steps']==305
        and own['native_open_pacing']['maximum_opens_per_second']==20
        and own['native_open_pacing']['open_reservations']==3*n+306
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*n
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==dup['byte_stream_pathname_reopens']==0
        and frame['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
            separate_pathname_reopens=0,regular_file_count=n,directory_count=306),
        'ALL_NATIVE_STREAMS_AND_IDENTITIES_1539')
    r.h.h.pressure_contract(own['native_open_backpressure']);lower_contract(own)


def record(doc,body,pin,required,binding,extras,names,legacy,base):
    index,name=g.old.select(base,names)
    require(doc['schema_version']==SCHEMA and doc['state']==PASS and doc.get('error_code') is None
        and doc['current_queue_runtime_contract_tests_passed']==156 and doc['post_stop_runtime_contract_tests_passed']==18
        and doc['selected_test_index']==index and doc['selected_test_name']==name
        and doc['reviewed_original_stop_pin']==r.STOP_PIN and doc['completed_stop_review_pin']==r.REVIEW_PIN
        and doc['parent_connection_support_pin']==r.CONNECTION_PIN
        and doc['reviewed_native_acquisition_stop_pin']==acquisition.ROOT_PIN
        and doc['native_acquisition_review_pin']==ACQUISITION_REVIEW and doc['lower_native_support_pin']==LOWER_SUPPORT
        and doc['reviewed_metadata_stop_pin']==metadata_review.ROOT_PIN and doc['metadata_stop_review_pin']==METADATA_REVIEW
        and doc['preserved_budget_failure_pin']==BUDGET_FAILURE
        and doc['preserved_prototype_failure_pin']==PROTOTYPE_FAILURE
        and doc['metadata_entry_support_pin']==ENTRY_SUPPORT and doc['metadata_entry_adapter_selected'] is True
        and doc['metadata_entry_runtime_contract_tests_passed']==12 and doc['metadata_entry_scope_bounds_enforced'] is True
        and doc['lower_native_runtime_contract_tests_passed']==8
        and doc['lower_native20_adapter_selected'] is True and doc['lower_native_scope_bounds_enforced'] is True
        and doc['uncreated_borrower_support_pin']==SUPPORT
        and doc['uncreated_borrower_adapter_selected'] is True
        and doc['uncreated_borrower_connection_contract_tests_passed']==8
        and doc['synthetic_pre_GO_stop_connection_verified'] is True
        and doc['actual_pre_GO_CPU_STOP_observed'] is False
        and doc['compound_anchor_pin']==COMPOUND and doc['preserved_case078_stop_pin']==review.ROOT_PIN
        and doc['binding']==binding and doc['prior_runtime_plan']==base and doc['case_receipt_pin']==pin
        and all(doc[k] is True for k in ('native_pressure_bridge_connected','packed_parent_writer_connected',
            'packed_root_writer_selected','deferred_failure_capture_connected','frame_acquisition_requested',
            'frame_acquisition_complete','product_worker_invocation_requested','actual_product_child_executed',
            'resource_watcher_cleanup_confirmed','compound_anchor_verified_without_body_reexecution'))
        and doc['receipt_serialization_policy']==r.policy() and doc['resource_stop_reason'] is None
        and doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[k] is False for k in ('whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved'))
        and doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs']==doc['preparation_IO']['final_fresh_hashes'],
        'COMPLETE_NEW_RUNTIME_WITH_ALL_ORIGINAL_GUARDS')
    metadata_contract(doc['preparation_IO']);metadata_contract(doc['closing_component']['metadata_IO'])
    require(doc['preparation_IO']['read_passes']+doc['closing_component']['metadata_IO']['read_passes']<=META_READ_LIMIT,
        'SHARED_METADATA_CAP720_NOT_PER_READER_ONLY')
    native_pair(doc['closing_component'],body,pin,required,binding,extras)
    r.stats_contract(doc['packed_parent_write_statistics'],pin)
    require(body['task']==f'p204-r07-case-{index:03}-tests'
        and doc['runtime_plan']==g.advance(legacy,base,names,index)
        and doc['accepted_exact_product_body_count']==1,'EXACT_ONE_BODY_NEXT_QUEUE')
    return doc['runtime_plan']


def closed_attempt(doc):
    require(doc.get('state') in (PASS,LIGHT) and doc.get('error_code') is None
        and doc.get('resource_stop_reason') is None and doc.get('resource_watcher_cleanup_confirmed') is True,
        'INSPECT_ANY_NEW_FAILED_ATTEMPT_BEFORE_RESUME')


def progress(q,legacy,base,names,required,binding,extras):
    folder=p.c.ROOT/p.DIR
    early=sorted((*folder.glob('p250-admission-run*.v1.json'),*folder.glob('p250-light-run*.v1.json')))
    require(len(early)<=4096,'BOUNDED_EARLY')
    for path in early:closed_attempt(q.json(path.relative_to(p.c.ROOT).as_posix()))
    files=sorted(folder.glob('p250-case-*-run*.v1.json'));require(len(files)<=4096,'BOUNDED_CASES')
    plan=base
    for path in files:
        match=FILE.fullmatch(path.name);require(match is not None,'EXACT_FILENAME')
        index,number=map(int,match.groups());require(1<=index<=249 and 1<=number<=999,'INDEX_RUN')
        doc=q.json(path.relative_to(p.c.ROOT).as_posix());closed_attempt(doc)
        require(doc['selected_test_index']==index,'EXACT_FILENAME_INDEX')
        pin=doc['case_receipt_pin'];require(pin['path']==f'{p.DIR}/cases/p250-case-{index:03}-run{number:03}.json',
            'OWN_BODY_PATH')
        body=review.bound_json(q,pin)
        plan=record(doc,body,pin,required,binding,extras,names,legacy,plan)
    return plan


def capture_for(frame,writes,index,name,binding):
    return candidate.Capture(frame,writes,index,name,binding)


def contracts(fixtures,healthy_doc,healthy_body,required,extras):
    require(r.contracts(fixtures)==156,'UNCHANGED_ORIGINAL156_CONTRACTS')
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_post_stop_compound_runtime as original_tests
    import test_uncreated_borrower_runtime as connection_tests
    import test_lower_native_runtime as lower_tests
    import test_metadata_entry_runtime_r3 as entry_tests
    # 계약 fixture만 새 schema/명시적 wiring 사실로 구성한다. 실제 증거 재작성 아님.
    fixture_doc=copy.deepcopy(healthy_doc)
    fixture_doc.update(uncreated_borrower_support_pin=SUPPORT,uncreated_borrower_adapter_selected=True,
        uncreated_borrower_connection_contract_tests_passed=8,synthetic_pre_GO_stop_connection_verified=True,
        actual_pre_GO_CPU_STOP_observed=False,reviewed_native_acquisition_stop_pin=acquisition.ROOT_PIN,
        native_acquisition_review_pin=ACQUISITION_REVIEW,lower_native_support_pin=LOWER_SUPPORT,
        lower_native_runtime_contract_tests_passed=8,lower_native20_adapter_selected=True,
        lower_native_scope_bounds_enforced=True,reviewed_metadata_stop_pin=metadata_review.ROOT_PIN,
        metadata_stop_review_pin=METADATA_REVIEW,metadata_entry_support_pin=ENTRY_SUPPORT,
        preserved_prototype_failure_pin=PROTOTYPE_FAILURE,preserved_budget_failure_pin=BUDGET_FAILURE,
        metadata_entry_adapter_selected=True,metadata_entry_runtime_contract_tests_passed=12,
        metadata_entry_scope_bounds_enforced=True)
    # 아래 행은 계약에만 쓰는 명시적인 synthetic fixture이다. 실제 증거는 변경하지 않는다.
    for row in (fixture_doc['preparation_IO'],fixture_doc['closing_component']['metadata_IO']):
        count=row['read_passes'];row['shared_metadata_read_budget_limit']=META_READ_LIMIT
        row['metadata_read_entry_pacing']=dict(maximum_metadata_read_entries_per_second=32,
            entry_calls=count,completed_original_read_calls=count,failed_calls=0,reservations=count,
            requested_sleep_seconds=0,binding_active=False,no_idle_burst=True,
            original_reader_and_bytes_and_fresh_checks_preserved=True,original_CPU_RAM_IO_and_parse_budget_preserved=True,
            original_pressure_checkpoint_reused=True,extra_sampler_or_thread_started=False,original_reads_skipped=False,
            cached_pins_or_parsed_JSON_substituted=False,cleanup_not_guarded_or_paced=True,
            measured_CPU_or_PC_freeze_improvement_claimed=False)
    fixture_doc['closing_component']['source_frame']['handles']['native_open_pacing']['maximum_opens_per_second']=20
    fixture_doc['closing_component']['source_frame']['handles']['lower_native_fan_out']=dict(
        original_upper_ceiling_per_second=32,selected_maximum_reservations_per_second=20,
        nominal_reservation_density_reduction_percent=37.5,original_pacer_and_no_burst_preserved=True,
        original_CPU_RAM_IO_lock_guards_preserved=True,all_identity_and_byte_checks_retained=True,
        cleanup_not_rate_or_pressure_guarded=True,measured_CPU_or_PC_freeze_improvement_claimed=False)
    with patch.object(original_tests,'m',sys.modules[__name__]), \
            patch.object(lower_tests,'m',sys.modules[__name__]), \
            patch.object(connection_tests,'m',sys.modules[__name__]), \
            patch.object(original_tests,'FIXTURES',(fixtures,fixture_doc,healthy_body,required,extras)), \
            patch('subprocess.Popen',side_effect=AssertionError('NO_WIRING_CONTRACT_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_WIRING_CONTRACT_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_WIRING_CONTRACT_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(original_tests))
        connection=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(connection_tests))
        lowered=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(lower_tests))
        paced=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(entry_tests))
    require(result.wasSuccessful() and result.testsRun==18 and not result.skipped
        and connection.wasSuccessful() and connection.testsRun==8 and not connection.skipped
        and lowered.wasSuccessful() and lowered.testsRun==8 and not lowered.skipped
        and paced.wasSuccessful() and paced.testsRun==12 and not paced.skipped,'RUNTIME18_PLUS_CONNECTION8_PLUS_LOWER8_PLUS_ENTRY12')
    return 18

def terminal_checkpoint(doc,owner):
    require(owner.done.is_set() and doc.get('state') in (PASS,LIGHT,'FAILED_NOT_ACCEPTED'),
        'TERMINAL_ONLY_NO_RESOURCE_RESTART')


def preserve_failure(capture,frame,owner,out,index,number):
    path=p.c.ROOT/f'{p.DIR}/cases/p250-failure-{index:03}-run{number:03}.json'
    digest=hashlib.sha256();written=0
    class Output:
        def __init__(self,stream):self.stream=stream
        def write(self,block):
            nonlocal written
            count=self.stream.write(block);require(type(count) is int and count==len(block),'SIDECAR_WRITE_ONCE')
            digest.update(block.encode('ascii'));written+=count;return count
    with path.open('x',encoding='utf-8') as stream:stats=capture.write_terminal(Output(stream),owner,out)
    out.update(terminal_parent_failure_sidecar_pin=dict(path=path.relative_to(p.c.ROOT).as_posix(),
        bytes=written,sha256=digest.hexdigest()),terminal_parent_failure_statistics=stats,
        original_failure_body_placeholder_preserved=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),default='light')
    ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=999,'CWD_RUN')
    root=p.c.ROOT;destination=root/f'{p.DIR}/p250-admission-run{args.run:03}.v1.json'
    if args.mode=='light':destination=root/f'{p.DIR}/p250-light-run{args.run:03}.v1.json'
    require(not destination.exists(),'FRESH_RECEIPT')
    context=g.observation.Context();owner=g.observation.Resources(context)
    q=meta=frame=candidate=body=capture=None;writes=[]
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),
        reviewed_original_stop_pin=r.STOP_PIN,completed_stop_review_pin=r.REVIEW_PIN,
        parent_connection_support_pin=r.CONNECTION_PIN,compound_anchor_pin=COMPOUND,
        preserved_case078_stop_pin=review.ROOT_PIN,compound_anchor_verified_without_body_reexecution=False,
        reviewed_native_acquisition_stop_pin=acquisition.ROOT_PIN,native_acquisition_review_pin=ACQUISITION_REVIEW,
        reviewed_metadata_stop_pin=metadata_review.ROOT_PIN,metadata_stop_review_pin=METADATA_REVIEW,
        preserved_prototype_failure_pin=PROTOTYPE_FAILURE,preserved_budget_failure_pin=BUDGET_FAILURE,
        metadata_entry_support_pin=ENTRY_SUPPORT,metadata_entry_adapter_selected=False,
        metadata_entry_scope_bounds_enforced=False,lower_native_support_pin=LOWER_SUPPORT,lower_native20_adapter_selected=False,
        lower_native_scope_bounds_enforced=False,uncreated_borrower_support_pin=SUPPORT,uncreated_borrower_adapter_selected=False,
        synthetic_pre_GO_stop_connection_verified=False,actual_pre_GO_CPU_STOP_observed=False,
        native_pressure_bridge_connected=False,packed_parent_writer_connected=False,deferred_failure_capture_connected=False,
        packed_root_writer_selected=True,frame_acquisition_requested=False,frame_acquisition_complete=False,
        product_worker_invocation_requested=False,accepted_exact_product_body_count=0,
        original_successful_bodies_not_reexecuted=True,receipt_serialization_policy=r.policy())
    try:
        owner.admit();q=Reader(owner,context)
        out['metadata_entry_adapter_selected']=type(q.entry_binding) is entry.Binding
        legacy,base,names,expected,exe,required,extras=anchor(q);binding=p.v.identity(names,expected,exe)
        plan=progress(q,legacy,base,names,required,binding,extras);index,name=g.old.select(plan,names)
        healthy=review.bound_json(q,HEALTHY);healthy_body=review.bound_json(q,healthy['case_receipt_pin'])
        with context.scope('contract_tests'):
            out['post_stop_runtime_contract_tests_passed']=contracts((legacy,plan,names,q.json(r.STOP_PIN['path'])),
                healthy,healthy_body,required,extras)
        out.update(current_queue_runtime_contract_tests_passed=156,uncreated_borrower_connection_contract_tests_passed=8,
            lower_native_runtime_contract_tests_passed=8,lower_native_scope_bounds_enforced=True,
            metadata_entry_runtime_contract_tests_passed=12,metadata_entry_scope_bounds_enforced=True,
            synthetic_pre_GO_stop_connection_verified=True,binding=binding,selected_test_index=index,
            selected_test_name=name,prior_runtime_plan=plan,extra_frame_controller_pins=list(extras.values()),
            compound_anchor_verified_without_body_reexecution=True)
        if args.mode=='light':q.finish();candidate=dict(state=LIGHT)
        else:
            destination=root/f'{p.DIR}/p250-case-{index:03}-run{args.run:03}.v1.json'
            require(not destination.exists(),'FRESH_EXACT_CASE')
            require(not list((root/p.DIR/'cases').glob(f'p250-case-{index:03}-run*.json')),'NO_BODY_RETRY')
            body_path=root/f'{p.DIR}/cases/p250-case-{index:03}-run{args.run:03}.json'
            body_path.parent.mkdir(parents=True,exist_ok=True);q.finish()
            require(q.shared_budget['read_calls']<=META_READ_LIMIT-2,'POST_BODY_METADATA_TWO_READS_RESERVED')
            held=lower.InputLocks(root,owner.checkpoint_io,owner)
            out['lower_native20_adapter_selected']=type(held) is lower.InputLocks and held.api.pacer.rate==20
            require(held.api.pacer.checkpoint is held.open_pressure and held.open_pressure.resources is owner,
                'ORIGINAL_NATIVE_OWNER_PRESSURE')
            frame=p.frames.Frame(p.frames.Registry(),required,owner.checkpoint_io,held=held)
            counter=p.frames.Counters(q.reader,frame.readers);context.reader=counter
            out.update(native_pressure_bridge_connected=True,frame_acquisition_requested=True)
            with context.scope('metadata_hash'):frame.acquire()
            out.update(frame_acquisition_complete=True,product_worker_invocation_requested=True,
                packed_parent_writer_connected=True,deferred_failure_capture_connected=True,
                case_receipt_path=body_path.relative_to(root).as_posix())
            capture=capture_for(frame,writes,index,name,binding)
            out['uncreated_borrower_adapter_selected']=type(capture) is support.candidate.Capture
            with patch.object(p,'RAW_DUMP',capture.writer):code=p.run_parent(frame,index,name,body_path,context,binding)
            if capture.pending:
                out['original_parent_STOP_captured_not_accepted']=True
                out['actual_pre_GO_CPU_STOP_observed']=capture._document.get('state')=='DEFERRED_NOT_STARTED'
                raise ValueError('ORIGINAL_PARENT_STOP_DEFERRED_NOT_ACCEPTED')
            meta=Reader(owner,context);counter.metadata.append(meta.reader);context.reader=counter
            body=meta.json(body_path.relative_to(root).as_posix());pin=meta.reader.snapshots[body_path.relative_to(root).as_posix()]
            out['actual_product_child_executed']=True if body.get('actual_product_child_executed') is True else None
            require(code==0 and len(writes)==1,'ORIGINAL_PARENT_COMPLETE_ONCE')
            p.validate_parent(body,name,binding,required);r.stats_contract(writes[0],pin);meta.finish()
            component=dict(schema_version=p.CLOSING_SCHEMA,state=p.PASS,**p.r.flags(),selected_test_name=name,
                binding=binding,case_receipt_pin=pin,metadata_IO=meta.summary(),source_frame=frame.commit(body),
                extra_frame_controller_pins=list(extras.values()),sealed_whole_before_anchor=p.b.BASE_CLOSE)
            out.update(case_receipt_pin=pin,closing_component=component,packed_parent_write_statistics=writes[0])
            candidate=dict(state=PASS,runtime_plan=g.advance(legacy,plan,names,index),accepted_exact_product_body_count=1)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,KeyboardInterrupt,p.c.subprocess.SubprocessError) as error:
        out.update(error_code=p.b.run.original.closed_error(error));candidate=None
    finally:
        if frame is not None:
            try:
                if not frame.close():out['error_code']='POST_STOP_RUNTIME_FRAME_CLEANUP_FAILED';candidate=None
            except (ValueError,OSError):out['error_code']='POST_STOP_RUNTIME_FRAME_CLEANUP_FAILED';candidate=None
            out['terminal_source_frame']=frame.summary()
        for reader in (q,meta):
            if reader is not None:reader.close_entry()
        if q is not None:out['preparation_IO']=q.summary()
        if meta is not None:out['terminal_metadata_IO']=meta.summary()
        out['metadata_observation']=g.observation.summary(owner)
        def validate(doc):
            if doc['state']==PASS:
                doc['closing_component'].update(resource_stop_reason=doc['resource_stop_reason'],
                    resource_watcher_cleanup_confirmed=doc['resource_watcher_cleanup_confirmed'])
                record(doc,body,pin,required,binding,extras,names,legacy,plan)
            else:require(doc['state']==LIGHT and doc['preparation_IO']['finished'] is True,'LIGHT_ALL_FRESH')
        g.complete(out,owner,candidate,validate);destination.parent.mkdir(parents=True,exist_ok=True)
        if capture is not None and capture.pending:
            try:preserve_failure(capture,frame,owner,out,index,args.run)
            except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
                out.update(state='FAILED_NOT_ACCEPTED',terminal_failure_write_error=p.b.run.original.closed_error(error))
        try:
            with destination.open('x',encoding='utf-8') as stream:
                writer=r.packed.dump if out['state'] in (PASS,LIGHT) else r.compact.dump
                writer(out,stream,checkpoint=lambda:terminal_checkpoint(out,owner),indent=2)
        except (ValueError,OSError,TypeError):
            print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code='POST_STOP_RUNTIME_TERMINAL_SERIALIZATION_FAILED')));return 2
        print(json.dumps({k:out.get(k) for k in ('state','post_stop_runtime_contract_tests_passed',
            'selected_test_index','error_code','resource_stop_reason')}))
    return 0 if out['state'] in (PASS,LIGHT) else 2


if __name__=='__main__':
    sys.modules.setdefault('resume_metadata_entry_runtime_r3',sys.modules[__name__])
    raise SystemExit(main())




