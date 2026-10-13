"""P284: 최신97 준비 STOP·원95/96 수용 보존·전체1595 exact-one 실행.

수용 코드와 원 실패 불변. 생성 중 누적 관측 연결을 명시 사용하고 원 보호·
두 byte 읽기·identity·정리 유지. 미검토 실패 차단, 통과 본체 재실행 없음.
"""
import argparse
import copy
import hashlib
import io
import json
import math
import re
import sys
import unittest
from pathlib import PurePosixPath
from unittest.mock import patch
import resume_monotonic_compound_runtime as old
import qualify_rejected_parent_connection_r2 as connection
import qualify_early_metadata_pressure as metadata
import resume_diagnostic_guarded_runtime as prototype
import resume_diagnostic_guarded_runtime_r2 as decoded_prototype
import resume_reviewed_shared_entry_runtime as previous
import qualify_metadata_entry_early_pressure as entry_pressure
import qualify_acquisition_phase_pressure_r2 as phase
profile=phase.original
a=connection.a
m=old.m;p=old.p;g=old.g;r=old.r
review=old.review;early_review=old.early_review
SELF='tools/p09/resume_post97_stop_runtime.py'
TEST='tools/p09/tests/test_post97_stop_runtime.py'
COMPOUND=dict(path=p.DIR+'/p264-case091-compound-run01.v1.json',bytes=473724,
    sha256='2e638cd49227bce9154690cddd41a65b736b31be6e97260f891ad869bed93827')
NEW=(*previous.NEW,SELF,TEST)
ADDED=(SELF,TEST)
N=1595
DIRECTORIES=308
SCHEMA='hwpx-agent.p09-post97-stop-runtime-pair/v1'
PASS='PASS_EXACT_R07_POST97_STOP_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT='PASS_POST97_STOP_SELECTION_NOT_ACTUAL_OR_GATE'
FILE=re.compile(r'p284-case-([0-9]{3})-run([0-9]{3})\.v1\.json')
COUNT=62
TOTAL=1114


def require(ok,code):m.require(ok,'DIAGNOSTIC_RUNTIME_'+code)


RAW_JSON_READER=m.prior.prior.Reader

class Reader(entry_pressure.Reader):
    def json(self,path):
        # P255와 동일한 원 protected byte-bound 읽기에서 carrier를 가져온다.
        # 원 canonical/decoder를 정확히 한 번 호출하며 byte/identity/신선도 검사를 보존한다.
        carrier=RAW_JSON_READER.json(self,path);name=self.name(path)
        if carrier.get('schema_version')==r.packed.SCHEMA:
            r.h.canonical(carrier,self.reader.snapshots[name],self.checkpoint)
            return r.packed.unpack(carrier,self.checkpoint)
        if name.startswith(tuple(p.DIR+suffix for suffix in
            ('/p253-','/cases/p253-','/p255-','/cases/p255-','/p284-','/cases/p284-'))):
            r.h.canonical(carrier,self.reader.snapshots[name],self.checkpoint)
        return carrier



def closed_attempt(doc):
    require(doc.get('schema_version')==SCHEMA and doc.get('state') in (PASS,LIGHT)
        and doc.get('error_code') is None and doc.get('resource_stop_reason') is None
        and doc.get('resource_watcher_cleanup_confirmed') is True
        and type(doc.get('runtime_contract_executions')) is int and doc['runtime_contract_executions']==TOTAL
        and doc.get('receipt_serialization_policy')==r.policy()
        and doc.get('monotonic_binding_policy')==review.policy(),'OWN_CLOSED_NOT_FAILED_OR_FOREIGN')


def budget(required,original,added):
    require(len(original)==1563 and len(required)==N and len(added)==32
        and set(added)==set(NEW) and not set(original)&set(added) and required=={**original,**added}
        and required[p.m.EXE['path']]==p.m.EXE and sum(x['bytes'] for x in added.values())<=1048576,
        'ORIGINAL1563_PLUS_THIRTY_TWO_ONLY')
    binary=p.m.EXE['bytes'];other=sum(x['bytes'] for x in required.values())-binary
    total=(N+DIRECTORIES)/14+2*N/20+2*binary/1048576+2*other/2097152+60+20+15+60
    require(total<=phase.future_budget()['nominal_seconds']+(DIRECTORIES-306)/14+(N-1587)*(1/14+2/20),
        'QUALIFIED1587_PLUS_EIGHT_CODES_TWO_ANCESTORS_NO_EXTENSION')
    require(total<600,'NOMINAL_FITS_ORIGINAL600')
    return dict(full_runtime_inputs=N,new_inputs=32,native_rate=20,acquisition_native_rate=14,metadata_rate=32,
        actual_ancestor_directory_count=DIRECTORIES,qualified_model_original_directories=306,
        explicit_added_ancestor_directories=2,extra_native_allowance_seconds=2/14+(N-1587)*(1/14+2/20),
        qualified_phase_upper_inputs=1587,explicit_added_entry_controller_inputs=8,
        original_IO_scope_seconds=600,shared_metadata_read_limit=720,extra_bytes_upper_bound=1048576,
        metadata_allowance_seconds=60,product_allowance_seconds=20,early_yield_allowance_seconds=15,
        margin_seconds=60,nominal_combined_seconds=total,prediction_not_completion_guarantee=True)


LATEST_STOP=previous.LATEST_STOP
CURRENT97_STOP=dict(path=p.DIR+'/p282-case-097-run004.v1.json',bytes=145146,
    sha256='934136216dedefeb8e6148665c72e16a7bb91013499c7be19a1ccb48346fe551')
OLD_LIGHT=dict(path=p.DIR+'/p282-light-run001.v1.json',bytes=46642,
    sha256='e8f6e7a4ea7b15a35a92dc484614bc0e339e33c240ee192181925f6c77556e4e')
OLD_PAIRS=((dict(path=p.DIR+'/p282-case-095-run002.v1.json',bytes=640288,
    sha256='a9b1661b2d81e12b123b20d0c269c79dc7c11019baa297fe46363b6aa046c587'),
    dict(path=p.DIR+'/cases/p282-case-095-run002.json',bytes=185815,
    sha256='42d6dc174a334118c558b00336a86352fcef42cefda3d2f4db46f0ac2c764c43')),
    (dict(path=p.DIR+'/p282-case-096-run003.v1.json',bytes=641320,
    sha256='0c748d7f03e0e8c15f07267b26427ab48fead4401b7819b3febda6cafb489e97'),
    dict(path=p.DIR+'/cases/p282-case-096-run003.json',bytes=186119,
    sha256='01183a3a0a82693775e3f2990618fcb3f09f51afe135620d8fb3965e071de253')))
PREVIOUS_CODE=(dict(path=previous.SELF,bytes=35239,
    sha256='ded2e00a4cf64564928e02a9ca34f63bf7431195495a9b7a57e39eba32a2a9a3'),
    dict(path=previous.TEST,bytes=10311,
    sha256='55535107ba5795161dfe03c0f9bd5bb53a68aba397d13ceaf7e8b7192638da24'))


def current97_stop_review(doc,base):
    require(doc['schema_version']==previous.SCHEMA and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc['error_code']==doc['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['failure_diagnostic']['stage']=='final_fresh_preparation'
        and doc['failure_diagnostic']['exception_class']=='ValueError'
        and doc['runtime_contract_executions']==990 and doc['selected_test_index']==97
        and doc['prior_runtime_plan']==base and doc['metadata_entry_pressure_connection_selected'] is True
        and doc['reviewed_latest_preparation_STOP_pin']==LATEST_STOP
        and doc['reviewed_latest_STOP_preserved_not_accepted'] is True
        and doc['accepted_exact_product_body_count']==0 and doc['actual_product_child_executed'] is False
        and doc['acquisition_phase_connection_selected'] is False
        and all(k not in doc for k in ('terminal_source_frame','case_receipt_path','terminal_metadata_IO')),
        'CURRENT97_STOP_BEFORE_FRAME_JOB_OR_PRODUCT_NOT_ACCEPTED')
    row=doc['preparation_IO']
    require(row['read_passes']==435 and row['bound_inputs']==226 and row['final_fresh_hashes']==126
        and row['bytes_read']==51066725 and row['finished'] is False,'CURRENT97_PARTIAL126_NOT_FULL226')
    entry_pressure.connection_contract(row['metadata_entry_early_pressure_connection'])
    require(row['near_saturation_read_backpressure']['warning_entries']==1
        and row['near_saturation_read_backpressure']['completed_pause_windows']==4
        and row['early_metadata_pressure']['original_early_source_algorithm_statistics']['warning_entries']==1
        and row['early_metadata_pressure']['original_early_source_algorithm_statistics']['completed_pause_windows']==2,
        'EXISTING_EARLY90_AND_ORIGINAL95_ACTUALLY_WAITED')
    o=doc['metadata_observation'];tail=o['samples'][-8:]
    require(len(o['samples'])==77 and all(x['system_cpu_percent']==100 for x in tail[-4:])
        and all(x['parent_cpu_machine_percent']==x['audited_logical_read_bytes_delta']==0 for x in tail[-6:])
        and [x['system_cpu_percent'] for x in tail[:4]]==[76.87,93.97,72.24,97.27]
        and o['own_cpu_max_machine_percent']==6.100818 and o['own_private_max_bytes']==58638336,
        'CURRENT97_HOT_HOST_ZERO_OWN_AND_NO_READ_DURING_EXISTING_WAIT')
    require(base['runtime_source_qualified_individual_cases']==90 and base['next_runtime_index']==97
        and base['runtime_remaining_individual_cases']==159,'CURRENT97_STOP_NOT_QUEUE_ADVANCE')
    return dict(original_current97_STOP_preserved=True,accepted_runtime_subset=90,next_index=97,
        original_partial_fresh_not_accepted=True,original_frame_parent_Job_product_invoked=False,
        existing_shared90_and_original95_wait_confirmed=True,CPU_cause_or_PC_freeze_resolution_established=False)


def anchor(q):
    raw=previous.anchor(q)
    legacy,base,names,expected,exe,prior_required,prior_extras,original,old_extras,healthy,healthy_body,historical,historical_body,legacy_original,legacy_extras,qualified=raw
    light=m.review.bound_json(q,OLD_LIGHT);previous.closed_attempt(light)
    require(light['state']==previous.LIGHT and light['prior_runtime_plan']==base,'ORIGINAL990_PREFLIGHT_NOT_BODY')
    binding=p.v.identity(names,expected,exe)
    for root_pin,body_pin in OLD_PAIRS:
        doc=m.review.bound_json(q,root_pin);previous.closed_attempt(doc)
        require(doc['case_receipt_pin']==body_pin,'EXACT_ACCEPTED95_96_PAIR_ONLY')
        body=m.review.bound_json(q,body_pin)
        base=previous.record(doc,body,body_pin,prior_required,binding,prior_extras,names,legacy,base)
    failed=m.review.bound_json(q,CURRENT97_STOP);current97_stop_review(failed,base)
    folder=p.c.ROOT/p.DIR
    old_roots=[OLD_LIGHT,CURRENT97_STOP,*[pair[0] for pair in OLD_PAIRS]]
    require(sorted(x.name for x in folder.glob('p282-*.v1.json'))==
        sorted(pin['path'].split('/')[-1] for pin in old_roots),'ONLY_REVIEWED_PASSED_AND_STOPPED_PREVIOUS_ROOTS')
    require(sorted(x.name for x in (folder/'cases').glob('p282-*.json'))==
        sorted(pair[1]['path'].split('/')[-1] for pair in OLD_PAIRS),'NO_STOPPED97_BODY_OR_PASSED_BODY_RERUN')
    added={name:q.pin(name) for name in NEW}
    for name in previous.NEW:require(added[name]==prior_required[name],'OLD30_CONTROLLER_SCOPE_RETAINED')
    for pin in PREVIOUS_CODE:require(added[pin['path']]==pin,'ORIGINAL_ACCEPTED95_96_AND_FAILED97_CODE_UNCHANGED')
    required={**original,**added};extras={**old_extras,**added}
    directories={PurePosixPath('.')}
    for name in required:directories.update(PurePosixPath(name).parents)
    require(len(directories)==DIRECTORIES,'ALL308_ANCESTORS_NOT_SUBSET')
    require(len(original)==1563 and len(prior_required)==1593 and len(prior_extras)==126
        and len(extras)==128 and set(ADDED)==set(required)-set(prior_required),'FULL_ORIGINAL1593_PLUS_TWO_ONLY')
    budget(required,original,added)
    return (legacy,base,names,expected,exe,required,extras,original,old_extras,healthy,healthy_body,
        historical,historical_body,legacy_original,legacy_extras,qualified)


ENTRY_QUALIFIER=dict(path=p.DIR+'/p279-metadata-entry-early-pressure-run01.v1.json',bytes=25942,
    sha256='5a0bcb6ea02cd41894f0cf306237b9f53c1eaf343832b724bd66d50c2f443ec8')

PHASE_QUALIFIER=dict(path=p.DIR+'/p276-literal-phase-pressure-run02.v1.json',bytes=35487,
    sha256='e92558b203396aa5aa4355fec8c32d50839befdf909cc44d5159bc3bbb710c8d')

METADATA_PIN=dict(path=p.DIR+'/p270-early-metadata-pressure-run02.v1.json',bytes=156551,
    sha256='760509efb02dfb51f3d27a5d09dd6a7f9c07d1f6ce336004afb479e5802b3b60')
METADATA_FAILED_PIN=dict(path=p.DIR+'/p270-early-metadata-pressure-run01.v1.json',bytes=4244,
    sha256='707ed624d2df16780bb8c7c4900ef436a0501a0552593ac00c503ab92da99ae0')


P271_CODE=(
    dict(path='tools/p09/resume_diagnostic_guarded_runtime.py',bytes=28992,sha256='1349828826373ac0c8cdb520fcf96010ec2b9f60a10ab8bee9976a5d3fb82bde'),
    dict(path='tools/p09/tests/test_diagnostic_guarded_runtime.py',bytes=3058,sha256='28dbfb74efdbc147996a4d57e2927b67bd1fc7a57eb409a3f6adc9119523de04'))
P271_FAILED_PIN=dict(path=p.DIR+'/p271-light-run001.v1.json',bytes=43372,
    sha256='618acd5d4647b83970dbd4dd6133896af51cc901a0096ab4e31b7bf1fe426120')

DECODE_LIGHT_PIN=dict(path=p.DIR+'/p272-light-run001.v1.json',bytes=39038,
    sha256='834092d05d380052564e901ad3256fbf62ff97ea261f5c623f472f8f4155c7ba')
DECODE_FAILURE_PIN=dict(path=p.DIR+'/p272-admission-run002.v1.json',bytes=75373,
    sha256='fe57558dbf6d1824c5a54534c302c87e6531dbeb1944396f726a69e1275a2f81')

def constructor_failure(doc):
    require(doc['schema_version']==metadata.SCHEMA and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc['error_code']=='P152_FULL_REDACTED_FAILURE' and 'IO' not in doc
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['actual_product_body_or_full_source_executed'] is False,
        'ORIGINAL_CONSTRUCTOR_FAILURE_MISSING_IO_NOT_PROMOTED')

def diagnostic(error,stage):
    frames=[];cursor=error.__traceback__
    while cursor is not None:
        frames.append(dict(file=p.c.Path(cursor.tb_frame.f_code.co_filename).name,line=cursor.tb_lineno))
        cursor=cursor.tb_next
    return dict(stage=stage,exception_class=type(error).__name__,locations=frames[-8:],
        exception_message_included=False,diagnostic_not_acceptance=True)


def metadata_contract(row):
    require(row['selected_metadata_warning_CPU_percent']==90
        and all(row[k] is True for k in ('constructor_original95_path_retained','original95_pressure_retained_as_base',
            'original_guard_and_sampler_reused'))
        and all(row[k] is False for k in ('reader_or_aggregate_counter_replaced','CPU_RAM600_or720_guard_extended',
            'cleanup_callback_wrapped','new_sampler_or_thread_started','source_byte_or_identity_checks_skipped',
            'CPU_or_PC_freeze_improvement_established')),'ORIGINAL_METADATA95_600_720_NO_DROP')
    old.early_contract(row['original_early_source_algorithm_statistics'])


def timing_contract(row):
    require(row['first_original_error'] is None and row['original_lock_limit_seconds']==600
        and type(row['original_guard_checks']) is int and row['original_guard_checks']>0
        and row['original_check_invoked_without_replacement'] is True
        and row['extra_clock_only_at_boundary_or_first_error'] is True
        and row['unknown_measurements_not_zeroed'] is True
        and all(row[k] is False for k in ('extra_CPU_RAM_or_native_query_started','original_resource_guard_or_deadline_extended',
            'cleanup_callback_wrapped','CPU_or_PC_freeze_improvement_established')),'ORIGINAL_LOCK_TIMING_NO_GUARD_CHANGE')
    events=row['explicit_phase_events'];require([x['label'] for x in events]==list(connection.LABELS),'FIVE_BOUNDARIES')
    previous_seconds=-1;previous_number=0
    for event in events:
        seconds=event['original_lock_elapsed_seconds'];number=event['guard_check_number']
        require(type(seconds) in (float,int) and math.isfinite(seconds) and previous_seconds<=seconds<=600
            and type(number) is int and previous_number<number<=row['original_guard_checks'],'REAL_FINITE_MONOTONIC_BOUNDARIES')
        previous_seconds=seconds;previous_number=number


def native_pair(component,body,pin,required,binding,extras):
    p.validate_closing(component,body,pin,required,binding,extras)
    f=component['source_frame'];h=f['handles'];dup=h['borrowed_byte_streams']
    require(len(required)==N and h['input_lock_handles_opened']==h['input_lock_handles_closed']==N+DIRECTORIES
        and h['maximum_lock_seconds']==600 and h['ancestor_walk_steps']==DIRECTORIES-1
        and h['native_open_pacing']['maximum_opens_per_second']==20
        and h['native_open_pacing']['open_reservations']==3*N+DIRECTORIES
        and h['handle_metadata_checks']==4*N+2*DIRECTORIES
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*N
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==dup['byte_stream_pathname_reopens']==0
        and f['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
            separate_pathname_reopens=0,regular_file_count=N,directory_count=DIRECTORIES),'ALL1595_NATIVE_IDENTITIES_AND_CLOSE')
    m.r.h.h.pressure_contract(h['native_open_backpressure']);m.lower_contract(h)
    timing_contract(h['lock_timing_diagnostic'])
    profile.phase_contract(h['acquisition_phase_pressure'],N+DIRECTORIES,True)


def early_contract(row):
    require(row['early_source_warning_CPU_percent']==90 and row['cool_distinct_samples']==2
        and row['maximum_pause_windows']==8 and all(row[k] is True for k in
        ('original_guard_called_before_pressure','original_hard_CPU_RAM600_guards_preserved','existing_owner_samples_only'))
        and all(row[k] is False for k in ('new_sampler_or_thread_started','source_byte_reads_or_identity_checks_skipped',
            'cleanup_callback_wrapped','CPU_or_PC_freeze_improvement_established')),'ORIGINAL_GUARDS_EARLY_SOURCE_ONLY')


def job_contract(body):
    limits=body['owned_limits_readback'];require(limits['verified'] is True
        and limits['cpu_hard_cap_machine_percent']==6.25 and limits['affinity_mask']==1
        and limits['priority_class']==16384 and limits['active_process_limit']==16
        and limits['kill_on_close'] is True and limits['breakaway_disabled'] is True,'ORIGINAL_JOB_LIMIT_VALUES')


def record(doc,body,pin,required,binding,extras,names,legacy,base):
    index,name=g.old.select(base,names)
    require(doc['schema_version']==SCHEMA and doc['state']==PASS and doc.get('error_code') is None
        and doc['compound_anchor_pin']==COMPOUND and doc['preserved_case091_failure_pin']==review.ROOT_PIN
        and doc['selected_test_index']==index and doc['selected_test_name']==name
        and doc['binding']==binding and doc['prior_runtime_plan']==base and doc['case_receipt_pin']==pin
        and doc['original_retained_contract_executions']==990 and doc['own_queue_contract_tests_passed']==COUNT
        and doc['synthetic_following_queue_contract_tests_passed']==COUNT
        and doc['old_contract_scope']=='ORIGINAL1593_NO_BODY_REEXECUTION'
        and doc['new_contract_scope']=='EXPLICIT_SYNTHETIC_CURRENT_AND_FOLLOWING1595'
        and type(doc['runtime_contract_executions']) is int and doc['runtime_contract_executions']==TOTAL
        and doc['receipt_serialization_policy']==r.policy() and doc['monotonic_binding_policy']==review.policy()
        and doc['aggregate_post_reader_connection_verified'] is True
        and doc['diagnostic_parent_connection_selected'] is True and doc['native_timing_connected'] is True
        and doc['early_metadata_connection_selected'] is True
        and doc['reviewed_case094_failure_pin']==a.FAILURE and doc['qualified_connection_pin']==metadata.ROOT
        and doc['qualified_metadata_pin']==METADATA_PIN
        and doc['qualified_acquisition_phase_pin']==PHASE_QUALIFIER and doc['reviewed_case095_failure_pin']==profile.FAILURE
        and doc['acquisition_phase_connection_selected'] is True
        and doc['qualified_metadata_entry_pressure_pin']==ENTRY_QUALIFIER
        and doc['reviewed_latest_preparation_STOP_pin']==LATEST_STOP
        and doc['reviewed_latest_STOP_preserved_not_accepted'] is True
        and doc['reviewed_current97_STOP_pin']==CURRENT97_STOP
        and doc['reviewed_current97_STOP_preserved_not_accepted'] is True
        and doc['metadata_entry_pressure_connection_selected'] is True
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs']==doc['preparation_IO']['final_fresh_hashes']
        and doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[k] is False for k in ('whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved'))
        and all(doc[k] is True for k in ('compound_anchor_verified_without_body_reexecution','early_source_guard_connected',
            'actual_product_child_executed','packed_root_writer_selected','original_successful_bodies_not_reexecuted',
            'original_parent_capture_adapter_selected')),'COMPLETE_OWN_PAIR_NOT_PARTIAL_OR_GATE')
    m.metadata_contract(doc['preparation_IO']);m.metadata_contract(doc['closing_component']['metadata_IO'])
    require(doc['preparation_IO']['read_passes']+doc['closing_component']['metadata_IO']['read_passes']<=m.META_READ_LIMIT,
        'SAME_SHARED720_CAP')
    metadata_contract(doc['preparation_IO']['early_metadata_pressure'])
    metadata_contract(doc['closing_component']['metadata_IO']['early_metadata_pressure'])
    entry_pressure.connection_contract(doc['preparation_IO']['metadata_entry_early_pressure_connection'])
    entry_pressure.connection_contract(doc['closing_component']['metadata_IO']['metadata_entry_early_pressure_connection'])
    job_contract(body);early_contract(doc['early_source_checkpoint']);native_pair(doc['closing_component'],body,pin,required,binding,extras)
    r.stats_contract(doc['packed_parent_write_statistics'],pin)
    old={n:p for n,p in required.items() if n not in NEW};added={n:required[n] for n in NEW}
    require(doc['scope_budget']==budget(required,old,added)
        and body['task']==f'p204-r07-case-{index:03}-tests' and doc['accepted_exact_product_body_count']==1
        and doc['runtime_plan']==g.advance(legacy,base,names,index),'FULL_SCOPE_AND_EXACT_ONE_ADVANCE')
    return doc['runtime_plan']


def progress(q,legacy,base,names,required,binding,extras):
    folder=p.c.ROOT/p.DIR
    early=sorted((*folder.glob('p284-admission-run*.v1.json'),*folder.glob('p284-light-run*.v1.json')))
    require(len(early)<=4096,'BOUNDED_EARLY')
    for path in early:closed_attempt(q.json(path.relative_to(p.c.ROOT).as_posix()))
    files=sorted(folder.glob('p284-case-*-run*.v1.json'));require(len(files)<=4096,'BOUNDED_CASES')
    plan=base
    for path in files:
        match=FILE.fullmatch(path.name);require(match is not None,'FILENAME')
        index,number=map(int,match.groups());require(1<=index<=249 and 1<=number<=999,'INDEX_RUN')
        doc=q.json(path.relative_to(p.c.ROOT).as_posix());closed_attempt(doc)
        require(doc['selected_test_index']==index,'FILENAME_INDEX')
        pin=doc['case_receipt_pin'];require(pin['path']==f'{p.DIR}/cases/p284-case-{index:03}-run{number:03}.json','BODY_NAMESPACE')
        body=m.review.bound_json(q,pin);plan=record(doc,body,pin,required,binding,extras,names,legacy,plan)
    return plan


def contracts(fixtures,healthy,healthy_body,required,extras,original,old_extras,
        historical,historical_body,legacy_original,legacy_extras):
    prior_required={name:pin for name,pin in required.items() if name not in ADDED}
    prior_extras={name:pin for name,pin in extras.items() if name not in ADDED}
    require(previous.contracts(fixtures,healthy,healthy_body,prior_required,prior_extras,original,old_extras,
        historical,historical_body,legacy_original,legacy_extras)==990,'ORIGINAL990_RETAINED')
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_post_stop_compound_runtime as f
    import test_monotonic_compound_runtime as retained
    import test_post97_stop_runtime as tests
    legacy,current,names,stop=fixtures;synthetic=copy.deepcopy(healthy)
    synthetic.update(original_retained_contract_executions=990,own_queue_contract_tests_passed=COUNT,
        synthetic_following_queue_contract_tests_passed=COUNT,old_contract_scope='ORIGINAL1593_NO_BODY_REEXECUTION',
        new_contract_scope='EXPLICIT_SYNTHETIC_CURRENT_AND_FOLLOWING1595',preserved_case091_failure_pin=review.ROOT_PIN,
        runtime_contract_executions=TOTAL,receipt_serialization_policy=r.policy(),monotonic_binding_policy=review.policy(),
        aggregate_post_reader_connection_verified=True,early_source_guard_connected=True,original_parent_capture_adapter_selected=True,
        original_successful_bodies_not_reexecuted=True,actual_product_child_executed=True,packed_root_writer_selected=True,
        early_source_checkpoint=early_review.EarlySourceCheckpoint(lambda:None,None).summary(),
        scope_budget=budget(required,original,{n:required[n] for n in NEW}),
        diagnostic_parent_connection_selected=True,native_timing_connected=True,early_metadata_connection_selected=True,
        reviewed_case094_failure_pin=a.FAILURE,qualified_connection_pin=metadata.ROOT,qualified_metadata_pin=METADATA_PIN,
        qualified_acquisition_phase_pin=PHASE_QUALIFIER,reviewed_case095_failure_pin=profile.FAILURE,acquisition_phase_connection_selected=True,
        qualified_metadata_entry_pressure_pin=ENTRY_QUALIFIER,metadata_entry_pressure_connection_selected=True,
        reviewed_latest_preparation_STOP_pin=LATEST_STOP,reviewed_latest_STOP_preserved_not_accepted=True,
        reviewed_current97_STOP_pin=CURRENT97_STOP,reviewed_current97_STOP_preserved_not_accepted=True)
    with patch.object(f,'m',sys.modules[__name__]),patch.object(f,'FIXTURES',(fixtures,synthetic,healthy_body,required,extras)), \
            patch.object(retained,'m',sys.modules[__name__]), \
            patch('subprocess.Popen',side_effect=AssertionError('NO_RUNTIME_CONTRACT_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_RUNTIME_CONTRACT_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_RUNTIME_CONTRACT_THREAD')):
        first=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        index,_=g.old.select(current,names);following=g.advance(legacy,current,names,index)
        with patch.object(f,'FIXTURES',((legacy,following,names,stop),synthetic,healthy_body,required,extras)):
            second=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(first.wasSuccessful() and first.testsRun==COUNT and not first.skipped
        and second.wasSuccessful() and second.testsRun==COUNT and not second.skipped,'CURRENT62_AND_FOLLOWING62')
    return TOTAL


def preserve_failure(capture,frame,owner,out,index,number):
    path=p.c.ROOT/f'{p.DIR}/cases/p284-failure-{index:03}-run{number:03}.json';digest=hashlib.sha256();written=0
    class Output:
        def __init__(self,stream):self.stream=stream
        def write(self,block):
            nonlocal written
            count=self.stream.write(block);require(type(count) is int and count==len(block),'SIDECAR_ONCE')
            digest.update(block.encode('ascii'));written+=count;return count
    with path.open('x',encoding='utf-8') as stream:stats=capture.write_rejected(Output(stream),owner,out) if capture.rejected else capture.write_terminal(Output(stream),owner,out)
    out.update(terminal_parent_failure_sidecar_pin=dict(path=path.relative_to(p.c.ROOT).as_posix(),bytes=written,
        sha256=digest.hexdigest()),terminal_parent_failure_statistics=stats,original_failure_body_placeholder_preserved=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),default='light');ap.add_argument('--run',type=int,required=True)
    args=ap.parse_args();require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=999,'CWD_RUN')
    destination=p.c.ROOT/f'{p.DIR}/p284-{args.mode if args.mode=="light" else "admission"}-run{args.run:03}.v1.json'
    require(not destination.exists(),'FRESH_ONLY')
    context=g.observation.Context();owner=g.observation.Resources(context)
    q=meta=frame=early=capture=parent=proposed=None;body=None;writes=[]
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),compound_anchor_pin=COMPOUND,
        preserved_case091_failure_pin=review.ROOT_PIN,original_retained_contract_executions=990,
        own_queue_contract_tests_passed=COUNT,synthetic_following_queue_contract_tests_passed=COUNT,
        old_contract_scope='ORIGINAL1593_NO_BODY_REEXECUTION',new_contract_scope='EXPLICIT_SYNTHETIC_CURRENT_AND_FOLLOWING1595',
        original_successful_bodies_not_reexecuted=True,compound_anchor_verified_without_body_reexecution=False,
        early_source_guard_connected=False,original_parent_capture_adapter_selected=False,
        packed_root_writer_selected=True,accepted_exact_product_body_count=0,receipt_serialization_policy=r.policy(),
        monotonic_binding_policy=review.policy(),aggregate_post_reader_connection_verified=False,diagnostic_parent_connection_selected=False,
        native_timing_connected=False,early_metadata_connection_selected=False,reviewed_case094_failure_pin=a.FAILURE,
        qualified_connection_pin=metadata.ROOT,qualified_metadata_pin=METADATA_PIN,
        qualified_acquisition_phase_pin=PHASE_QUALIFIER,reviewed_case095_failure_pin=profile.FAILURE,acquisition_phase_connection_selected=False,
        qualified_metadata_entry_pressure_pin=ENTRY_QUALIFIER,metadata_entry_pressure_connection_selected=False,
        reviewed_latest_preparation_STOP_pin=LATEST_STOP,reviewed_latest_STOP_preserved_not_accepted=False,
        reviewed_current97_STOP_pin=CURRENT97_STOP,reviewed_current97_STOP_preserved_not_accepted=False)
    stage='admission'
    try:
        owner.admit();stage='reader_constructor';q=Reader(owner,context)
        out['metadata_entry_pressure_connection_selected']=type(q.entry_early_binding) is entry_pressure.Binding and q.entry_binding.pacer.checkpoint is q.reader.checkpoint
        stage='anchor'
        legacy,base,names,expected,exe,required,extras,original,old_extras,healthy,healthy_body,historical,historical_body,legacy_original,legacy_extras,qualified_probe=anchor(q)
        stage='selection';binding=p.v.identity(names,expected,exe);plan=progress(q,legacy,base,names,required,binding,extras);index,name=g.old.select(plan,names)
        stage='contract_tests'
        with context.scope('contract_tests'):
            out['runtime_contract_executions']=contracts((legacy,plan,names,q.json(r.STOP_PIN['path'])),healthy,healthy_body,
                required,extras,original,old_extras,historical,historical_body,legacy_original,legacy_extras)
        out.update(reviewed_latest_STOP_preserved_not_accepted=True,reviewed_current97_STOP_preserved_not_accepted=True,binding=binding,selected_test_index=index,selected_test_name=name,prior_runtime_plan=plan,
            extra_frame_controller_pins=list(extras.values()),compound_anchor_verified_without_body_reexecution=True,
            scope_budget=budget(required,original,{n:required[n] for n in NEW}),early_metadata_connection_selected=True)
        stage='final_fresh_preparation'
        if args.mode=='light':q.finish();proposed=dict(state=LIGHT)
        else:
            destination=p.c.ROOT/f'{p.DIR}/p284-case-{index:03}-run{args.run:03}.v1.json';require(not destination.exists(),'FRESH_CASE')
            require(not list((p.c.ROOT/p.DIR/'cases').glob(f'p284-case-{index:03}-run*.json')),'NO_BODY_RETRY')
            body_path=p.c.ROOT/f'{p.DIR}/cases/p284-case-{index:03}-run{args.run:03}.json';q.finish()
            require(q.shared_budget['read_calls']<=m.META_READ_LIMIT-2,'POST_BODY_TWO_READS_RESERVED')
            early=early_review.EarlySourceCheckpoint(owner.checkpoint_io,owner);held=profile.InputLocks(p.c.ROOT,early,owner,context)
            require(held.checkpoint is early and held.api.pacer.rate==20 and held.open_pressure.resources is owner,'EXACT_OWNER_EARLY_NATIVE20')
            frame=p.frames.Frame(p.frames.Registry(),required,early,held=held);counter=p.frames.Counters(q.reader,frame.readers);context.reader=counter
            out.update(early_source_guard_connected=True,acquisition_phase_connection_selected=type(held) is profile.InputLocks,case_receipt_path=body_path.relative_to(p.c.ROOT).as_posix())
            stage='source_frame_acquire';held.mark('before_acquire')
            with context.scope('metadata_hash'):frame.acquire()
            held.mark('after_acquire')
            parent=connection.ParentConnection(frame,writes,index,name,binding);capture=parent.capture
            out['original_parent_capture_adapter_selected']=isinstance(capture,m.support.candidate.Capture)
            out['diagnostic_parent_connection_selected']=type(parent) is connection.ParentConnection and type(capture) is a.Capture
            out['native_timing_connected']=isinstance(held,connection.TimedInputLocks)
            stage='owned_parent';held.mark('before_parent');code=parent.run(body_path,context);held.mark('after_parent')
            if capture.pending:
                out['original_parent_STOP_captured_not_accepted']=True
                raise ValueError('ORIGINAL_PARENT_STOP_DEFERRED_NOT_ACCEPTED')
            stage='post_reader_constructor';meta=review.construct(Reader,owner,context,counter)
            require(context.reader is counter and counter.metadata==[meta.reader],'MONOTONIC_ORIGINAL_AGGREGATE')
            out['aggregate_post_reader_connection_verified']=True
            body=meta.json(body_path.relative_to(p.c.ROOT).as_posix());pin=meta.reader.snapshots[body_path.relative_to(p.c.ROOT).as_posix()]
            require(code==0 and len(writes)==1,'ORIGINAL_PARENT_COMPLETE_ONCE')
            p.validate_parent(body,name,binding,required);job_contract(body);r.stats_contract(writes[0],pin);meta.finish()
            stage='source_frame_closing';held.mark('before_release')
            component=dict(schema_version=p.CLOSING_SCHEMA,state=p.PASS,**p.r.flags(),selected_test_name=name,
                binding=binding,case_receipt_pin=pin,metadata_IO=meta.summary(),source_frame=frame.commit(body),
                extra_frame_controller_pins=list(extras.values()),sealed_whole_before_anchor=p.b.BASE_CLOSE)
            out.update(case_receipt_pin=pin,closing_component=component,packed_parent_write_statistics=writes[0],
                actual_product_child_executed=body.get('actual_product_child_executed') is True)
            proposed=dict(state=PASS,runtime_plan=g.advance(legacy,plan,names,index),accepted_exact_product_body_count=1)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,KeyboardInterrupt,p.c.subprocess.SubprocessError) as error:
        out['error_code']=p.b.run.original.closed_error(error);out['failure_diagnostic']=diagnostic(error,stage);proposed=None
    finally:
        if frame is not None:
            try:
                if not frame.close():out['error_code']='MONOTONIC_RUNTIME_FRAME_CLEANUP_FAILED';proposed=None
            except (ValueError,OSError):out['error_code']='MONOTONIC_RUNTIME_FRAME_CLEANUP_FAILED';proposed=None
            out['terminal_source_frame']=frame.summary()
        if early is not None:out['early_source_checkpoint']=early.summary()
        for reader in (q,meta):
            if reader is not None:reader.close_entry()
        if q is not None:out.update(preparation_IO=q.summary(),bound_preparation_input_pins=list(q.reader.snapshots.values()))
        if meta is not None:out['terminal_metadata_IO']=meta.summary()
        out['metadata_observation']=g.observation.summary(owner)
        def validate(doc):
            if doc['state']==PASS:
                doc['closing_component'].update(resource_stop_reason=doc['resource_stop_reason'],resource_watcher_cleanup_confirmed=doc['resource_watcher_cleanup_confirmed'])
                record(doc,body,pin,required,binding,extras,names,legacy,plan)
            else:
                require(doc['state']==LIGHT and doc['preparation_IO']['finished'] is True
                    and doc['runtime_contract_executions']==TOTAL and doc['monotonic_binding_policy']==review.policy(),
                    'LIGHT_ALL_FRESH_AND1114')
                m.metadata_contract(doc['preparation_IO']);metadata_contract(doc['preparation_IO']['early_metadata_pressure'])
                entry_pressure.connection_contract(doc['preparation_IO']['metadata_entry_early_pressure_connection'])
                require(doc['metadata_entry_pressure_connection_selected'] is True and doc['reviewed_latest_STOP_preserved_not_accepted'] is True
                    and doc['reviewed_latest_preparation_STOP_pin']==LATEST_STOP
                    and doc['reviewed_current97_STOP_pin']==CURRENT97_STOP
                    and doc['reviewed_current97_STOP_preserved_not_accepted'] is True,'LIGHT_REAL_CACHED_ENTRY_AND_REVIEWED97_STOP')
        g.complete(out,owner,proposed,validate)
        if capture is not None and (capture.pending or capture.rejected):
            try:preserve_failure(capture,frame,owner,out,index,args.run)
            except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:out.update(state='FAILED_NOT_ACCEPTED',terminal_failure_write_error=p.b.run.original.closed_error(error))
        try:
            with destination.open('x',encoding='utf-8') as stream:
                writer=r.packed.dump if out['state'] in (PASS,LIGHT) else r.compact.dump
                def terminal():require(owner.done.is_set(),'NO_RESOURCE_RESTART')
                writer(out,stream,checkpoint=terminal,indent=2)
        except (ValueError,OSError,TypeError):
            print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code='MONOTONIC_RUNTIME_TERMINAL_SERIALIZATION_FAILED')));return 2
        print(json.dumps({k:out.get(k) for k in ('state','runtime_contract_executions','selected_test_index','error_code','resource_stop_reason')}))
    return 0 if out['state'] in (PASS,LIGHT) else 2


if __name__=='__main__':
    sys.modules.setdefault('resume_post97_stop_runtime',sys.modules[__name__])
    raise SystemExit(main())
