"""P255: sealed r102 체크포인트와 원 실제 pair를 소비하는 후속 실행기.
과거 recursive progress 재생 대신95 원 입력을 첫 읽기+최종 fresh로 검증한다.
전체1543 원 source와 새2를 모두 실제 잠금/두 읽기에 유지한다."""
import argparse
import copy
import hashlib
import io
import json
import re
import sys
import unittest
from unittest.mock import patch
import resume_generic_metadata_runtime_r2 as prior
r=prior.r;p=prior.p;g=prior.g;review=prior.review
lower=prior.lower;entry=prior.entry;support=prior.support;candidate=prior.candidate
acquisition=prior.acquisition;metadata_review=prior.metadata_review
ACQUISITION_REVIEW=prior.ACQUISITION_REVIEW;LOWER_SUPPORT=prior.LOWER_SUPPORT
COMPOUND=prior.COMPOUND;SUPPORT=prior.SUPPORT;METADATA_REVIEW=prior.METADATA_REVIEW
ENTRY_SUPPORT=prior.ENTRY_SUPPORT;PROTOTYPE_FAILURE=prior.PROTOTYPE_FAILURE;BUDGET_FAILURE=prior.BUDGET_FAILURE
META_READ_LIMIT=prior.META_READ_LIMIT
SELF='tools/p09/resume_checkpoint_metadata_runtime.py'
TEST='tools/p09/tests/test_checkpoint_metadata_runtime.py'
NEW=(SELF,TEST);EXTRAS=(*prior.EXTRAS,*NEW)
HEALTHY=dict(path=p.DIR+'/p250-case-080-run003.v1.json',bytes=612696,
    sha256='b353add7c8a0e49134d0a7f2983e3a8083192f47151f15f5364a9cdf2fe8e4cd')
ADMISSION_FAILURE=dict(path=p.DIR+'/p250-admission-run004.v1.json',bytes=143215,
    sha256='ac9c1805040421eb945cc3b78cb2577572e9df807312bad20bc7726020e08fb2')
SCHEMA='hwpx-agent.p09-checkpoint-metadata-runtime-pair/v1'
PASS='PASS_EXACT_R07_CHECKPOINT_METADATA_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT='PASS_CHECKPOINT_METADATA_SELECTION_NOT_ACTUAL_OR_GATE'
FILE=re.compile(r'p255-case-([0-9]{3})-run([0-9]{3})\.v1\.json')
require=prior.require
lower_contract=prior.lower_contract
metadata_contract=prior.metadata_contract
capture_for=prior.capture_for
PROTOTYPE_LIGHT=prior.PROTOTYPE_LIGHT;PROTOTYPE_ADMISSION=prior.PROTOTYPE_ADMISSION
REPAIRED_DECODE=prior.REPAIRED_DECODE
CHECKPOINT=dict(path=p.DIR+'/p254-generic-metadata-status-doc-r0102-run01.v1.json',bytes=40000,
    sha256='f394aded5f736eae6b46ccb8885d5e46e99a845b7135849126f526d366b49e9e')
HEAD=dict(path=p.DIR+'/p253-case-081-run003.v1.json',bytes=615984,
    sha256='22d57ddd87d213c6d41c39c536c5d83e2fec295ea34d110540f5406284b2a246')
CHECKPOINT_SCHEMA='hwpx-agent.p09-generic-metadata-runtime-status-document-snapshot/v1'
CHECKPOINT_PASS='PASS_GENERIC_METADATA_ACTUAL81_STATUS_DOCUMENT_SNAPSHOT_NOT_WHOLE_OR_GATE'
PRIOR_NAMESPACE_FILES={
    'p241':('p241-case-080-run002.v1.json','p241-light-run001.v1.json'),
    'p244':('p244-admission-run002.v1.json','p244-light-run001.v1.json'),
    'p250':('p250-admission-run004.v1.json','p250-case-080-run003.v1.json','p250-light-run001.v1.json','p250-light-run002.v1.json'),
    'p252':('p252-admission-run002.v1.json','p252-light-run001.v1.json'),
    'p253':('p253-case-081-run003.v1.json','p253-light-run001.v1.json','p253-light-run002.v1.json')}
MUTABLE_DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')
NEW_TEST_COUNT=26


def closed_attempt(doc):
    require(doc.get('schema_version')==SCHEMA and doc.get('state') in (PASS,LIGHT)
        and doc.get('error_code') is None and doc.get('resource_stop_reason') is None
        and doc.get('resource_watcher_cleanup_confirmed') is True,'OWN_CLOSED_STATE_NOT_FOREIGN_OR_FAILED')


class Reader(prior.Reader):
    def json(self,path):
        # decode 이전의 원 byte-bound carrier에서 canonical을 확인한다.
        carrier=prior.prior.Reader.json(self,path);name=self.name(path)
        if carrier.get('schema_version')==r.packed.SCHEMA:
            r.h.canonical(carrier,self.reader.snapshots[name],self.checkpoint)
            return r.packed.unpack(carrier,self.checkpoint)
        if name.startswith(tuple(p.DIR+suffix for suffix in ('/p253-','/cases/p253-','/p255-','/cases/p255-'))):
            r.h.canonical(carrier,self.reader.snapshots[name],self.checkpoint)
        return carrier


def checkpoint_policy():
    return dict(checkpoint_pin=CHECKPOINT,qualified_actual_pair_pin=HEAD,
        sealed_checkpoint_bound_inputs=95,each_checkpoint_input_first_byte_pin_and_final_fresh=True,
        metadata_reader_or_parse_cache_installed=False,original_byte_reader_unmodified=True,
        mutable_status_docs_verified_by_exact_r102_archive=True,
        original_full1543_source_retained=True,new_source_inputs=2,
        all_original_parent_frame_identity_and_cleanup_checks_retained=True,
        original_CPU_RAM600_and_shared720_caps_preserved=True,
        unknown_or_new_failed_prior_attempts_block_resume=True,
        prior_accepted_bodies_reexecuted=False,whole_or_Gate_promoted=False,
        CPU_or_freeze_improvement_claimed=False)


def checkpoint_contract(doc):
    require(doc.get('schema_version')==CHECKPOINT_SCHEMA and doc.get('state')==CHECKPOINT_PASS
        and doc.get('resource_stop_reason') is None and doc.get('resource_watcher_cleanup_confirmed') is True
        and doc.get('document_revision')==102 and doc.get('document_contract_tests_passed')==14
        and doc.get('root_actual_pair_pin')==HEAD
        and doc.get('product_body_or_full_source_reexecuted') is False
        and doc.get('exact_r101_document_bytes_preserved') is True,'SEALED_LITERAL_R102_DOCUMENT_CHECKPOINT')
    io=doc['IO'];pins=p.v.pins(doc['bound_input_pins']);plan=doc['runtime_plan']
    require(io['finished'] is True and io['read_passes']==192
        and io['bound_inputs']==io['final_fresh_hashes']==len(pins)==95
        and sorted(pins)==doc['required_bound_input_names']
        and pins.get(doc['report_pin']['path'])==doc['report_pin'],'ALL95_CHECKPOINT_BOUND_INPUTS')
    require(plan['runtime_source_qualified_individual_cases']==75 and plan['next_runtime_index']==82
        and plan['runtime_remaining_individual_cases']==174 and plan['runtime_remaining_regular_cases']==168
        and plan['runtime_remaining_corpus_cases']==6
        and plan['runtime_successful_candidates_requiring_closing']==0
        and plan['all_successful_bodies_pending_whole_reconciliation']==72,'CHECKPOINT75_NEXT82_NOT_GATE')
    require(doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc.get(k) is False for k in ('full249_current_qualified','signed16_current_qualified',
            'product_complete','PC_freeze_resolved','whole1470_current_fresh_qualified','historical67_current_fresh_qualified')),
        'CHECKPOINT_GATES_AND_UNQUALIFIED_FLAGS')
    return pins


def prior_namespace_inventory(folder):
    for prefix,names in PRIOR_NAMESPACE_FILES.items():
        actual=sorted(path.name for path in folder.glob(prefix+'-*.v1.json'))
        require(actual==list(names),'UNKNOWN_OR_CHANGED_PRIOR_NAMESPACE_'+prefix)


def bind_checkpoint(q,doc):
    # 새 call graph에서 증거 파일을 한 곳에서 읽고 해석한 결과를 반환한다.
    # Reader/pin/json을 가로채는 캐시나 기존 byte 검사를 대신하는 값은 없다.
    pins=checkpoint_contract(doc);parsed={}
    for name,pin in pins.items():
        bound_name=name
        if name in MUTABLE_DOCS:
            bound_name='implementation/p09/evidence/runtime-progress-r102/'+name.split('/')[-1]
        if name.endswith('.json'):parsed[name]=review.bound_json(q,dict(pin,path=bound_name))
        else:require(q.pin(bound_name)==dict(pin,path=bound_name),'EACH_CHECKPOINT_INPUT_CURRENT_BYTES')
    require(len(pins)==95 and len(parsed)==10,'CHECKPOINT_EXACT95_AND10_JSON')
    return parsed


def anchor(q):
    # 원 baseline의 compiled249·1470 manifest·Rust785 inventory·legacy acceptance 검사 유지.
    expected,names,exe=p.b.baseline(q)
    sealed=review.bound_json(q,CHECKPOINT);docs=bind_checkpoint(q,sealed)
    prior_namespace_inventory(p.c.ROOT/p.DIR)
    root=docs[HEAD['path']];prior.closed_attempt(root)
    body=docs[root['case_receipt_pin']['path']]
    compound=docs[COMPOUND['path']];legacy=compound['legacy_plan']
    previous=docs[sealed['previous_document_receipt_pin']['path']]
    require(compound['state']=='PASS_CURRENT_CASE078_BODY_AND_SEPARATE_FULL_SOURCE_COMPOUND_NOT_WHOLE_OR_GATE'
        and compound['resource_stop_reason'] is None and compound['resource_watcher_cleanup_confirmed'] is True,
        'UNCHANGED_COMPOUND_ANCHOR')
    require(previous['document_revision']==101
        and previous['state']=='PASS_METADATA_ENTRY_ACTUAL80_STATUS_DOCUMENT_SNAPSHOT_NOT_WHOLE_OR_GATE'
        and previous['resource_stop_reason'] is None and previous['resource_watcher_cleanup_confirmed'] is True,
        'UNCHANGED_PRIOR74_DOCUMENT')
    original=p.v.pins(root['closing_component']['source_frame']['actual_byte_boundaries'][0]['actual_byte_pins'])
    original_extras=p.v.pins(root['extra_frame_controller_pins']);binding=p.v.identity(names,expected,exe)
    require(set(original_extras)==set(prior.EXTRAS) and len(original)==1543 and len(original_extras)==76
        and all(q.reader.snapshots[n]==pin==original[n] for n,pin in original_extras.items()),
        'ORIGINAL1543_AND_EXECUTED76_UNCHANGED')
    base=prior.record(root,body,root['case_receipt_pin'],original,binding,original_extras,
        names,legacy,previous['runtime_plan'])
    require(base==sealed['runtime_plan'],'SEALED_PROGRESS_EQUALS_ORIGINAL_EXACT_PAIR_VALIDATOR')
    # 원 literal 실패 semantic 검사도 한 번은 실제 protected byte 읽기로 수행한다.
    prior.review_admission(docs[ADMISSION_FAILURE['path']])
    prior.reviewed_state_protocol(q,{n:pin for n,pin in original_extras.items() if n not in prior.NEW})
    prior.reviewed_decode_error(q)
    healthy=review.bound_json(q,HEALTHY);healthy_body=review.bound_json(q,healthy['case_receipt_pin'])
    original250={n:pin for n,pin in original.items() if n not in prior.NEW}
    extras250={n:pin for n,pin in original_extras.items() if n not in prior.NEW}
    historical_base=prior.prior.record(healthy,healthy_body,healthy['case_receipt_pin'],original250,binding,
        extras250,names,legacy,healthy['prior_runtime_plan'])
    require(historical_base==previous['runtime_plan'],'HISTORICAL_FIXTURE74_EQUALS_SEALED_PRIOR')
    historical=review.bound_json(q,prior.prior.HEALTHY)
    historical_body=review.bound_json(q,historical['case_receipt_pin'])
    added={name:q.pin(name) for name in NEW}
    required={**original,**added};extras={**original_extras,**added}
    enforce_scope_budget(required,original,added,connected_budget())
    return legacy,base,names,expected,exe,required,extras,healthy,healthy_body,historical,historical_body

def connected_budget():
    out=dict(prior.connected_budget())
    out.update(new_runtime_inputs_upper_bound=1546,native_reservation_seconds=(3*1546+306)/20,
        predicted_combined_seconds_with_allowances=out['predicted_combined_seconds_with_allowances']+0.3,
        only_new_controller_count_projection_changed=True,original600_CPU_RAM_guards_preserved=True)
    require(out['predicted_combined_seconds_with_allowances']<600,'NEW_SCOPE_FITS_UNCHANGED600')
    return out


def enforce_scope_budget(required,original,added,budget):
    require(required=={**original,**added} and set(original)<set(required)
        and len(original)==1543 and len(required)==1545 and len(added)==2
        and len(required)<=budget['new_runtime_inputs_upper_bound']==1546
        and sum(pin['bytes'] for pin in required.values())-119022055<=1048576
        and required[p.m.EXE['path']]==p.m.EXE and budget==connected_budget(),'FULL_SCOPE_NEW_TWO')


def progress(q,legacy,base,names,required,binding,extras):
    folder=p.c.ROOT/p.DIR
    early=sorted((*folder.glob('p255-admission-run*.v1.json'),*folder.glob('p255-light-run*.v1.json')))
    require(len(early)<=4096,'BOUNDED_EARLY')
    for path in early:
        name=path.relative_to(p.c.ROOT).as_posix()
        closed_attempt(q.json(name))
    plan=base;files=sorted(folder.glob('p255-case-*-run*.v1.json'));require(len(files)<=4096,'BOUNDED_CASES')
    for path in files:
        match=FILE.fullmatch(path.name);require(match is not None,'EXACT_FILENAME')
        index,number=map(int,match.groups());require(1<=index<=249 and 1<=number<=999,'INDEX_RUN')
        doc=q.json(path.relative_to(p.c.ROOT).as_posix());closed_attempt(doc)
        require(doc['selected_test_index']==index,'EXACT_FILENAME_INDEX')
        pin=doc['case_receipt_pin'];require(pin['path']==f'{p.DIR}/cases/p255-case-{index:03}-run{number:03}.json','OWN_BODY_PATH')
        body=review.bound_json(q,pin)
        plan=record(doc,body,pin,required,binding,extras,names,legacy,plan)
    return plan


def contracts(fixtures,healthy_doc,healthy_body,required,extras,historical_doc,historical_body):
    legacy,current,names,stop=fixtures
    original={n:pin for n,pin in required.items() if n not in NEW}
    original_extras={n:pin for n,pin in extras.items() if n not in NEW}
    historical=(legacy,healthy_doc['prior_runtime_plan'],names,stop)
    require(prior.contracts(fixtures,healthy_doc,healthy_body,original,original_extras,historical_doc,historical_body)==18,'PRIOR398_RETAINED')
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_post_stop_compound_runtime as fixture
    import test_checkpoint_metadata_runtime as tests
    synthetic=copy.deepcopy(healthy_doc)
    synthetic.update(metadata_checkpoint_pin=CHECKPOINT,metadata_checkpoint_actual_pair_pin=HEAD,
        metadata_checkpoint_policy=checkpoint_policy(),retained_prior_generation_contract_executions=398,
        reviewed_fixed_count_admission_pin=ADMISSION_FAILURE,reviewed_state_protocol_admission_pin=PROTOTYPE_ADMISSION,
        historical_support_contract_tests_passed=204,generic_queue_runtime_contract_tests_passed=NEW_TEST_COUNT,
        synthetic_following_queue_contract_tests_passed=NEW_TEST_COUNT,
        historical_support_fixture_scope='PRIOR73_QUALIFIED80_1539_INPUTS',current_queue_fixture_scope='DYNAMIC_NEXT_FULL_INPUTS')
    with (patch.object(fixture,'m',sys.modules[__name__]),
            patch.object(fixture,'FIXTURES',(fixtures,synthetic,healthy_body,required,extras)),
            patch('subprocess.Popen',side_effect=AssertionError('NO_GENERIC_CHILD')),
            patch('subprocess.run',side_effect=AssertionError('NO_GENERIC_CHILD')),
            patch('threading.Thread.start',side_effect=AssertionError('NO_GENERIC_THREAD'))):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        index,_=g.old.select(current,names)
        following=g.advance(legacy,current,names,index)
        with patch.object(fixture,'FIXTURES',((legacy,following,names,stop),synthetic,healthy_body,required,extras)):
            next_checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(checked.wasSuccessful() and checked.testsRun==NEW_TEST_COUNT and not checked.skipped
        and next_checked.wasSuccessful() and next_checked.testsRun==NEW_TEST_COUNT and not next_checked.skipped,
        'CURRENT26_AND_EXPLICIT_SYNTHETIC_FOLLOWING26')
    return 18

def native_pair(component,body,pin,required,binding,extras):
    p.validate_closing(component,body,pin,required,binding,extras)
    n=len(required);frame=component['source_frame'];own=frame['handles'];dup=own['borrowed_byte_streams']
    require(n==1545 and own['input_lock_handles_opened']==own['input_lock_handles_closed']==n+306
        and own['maximum_lock_seconds']==600 and own['ancestor_walk_steps']==305
        and own['native_open_pacing']['maximum_opens_per_second']==20
        and own['native_open_pacing']['open_reservations']==3*n+306
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*n
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==dup['byte_stream_pathname_reopens']==0
        and frame['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
            separate_pathname_reopens=0,regular_file_count=n,directory_count=306),
        'ALL_NATIVE_STREAMS_AND_IDENTITIES_1545')
    r.h.h.pressure_contract(own['native_open_backpressure']);lower_contract(own)


def record(doc,body,pin,required,binding,extras,names,legacy,base):
    index,name=g.old.select(base,names)
    require(doc['schema_version']==SCHEMA and doc['state']==PASS and doc.get('error_code') is None
        and doc['metadata_checkpoint_pin']==CHECKPOINT and doc['metadata_checkpoint_actual_pair_pin']==HEAD
        and doc['metadata_checkpoint_policy']==checkpoint_policy()
        and doc['retained_prior_generation_contract_executions']==398
        and doc['reviewed_fixed_count_admission_pin']==ADMISSION_FAILURE
        and doc['reviewed_state_protocol_admission_pin']==PROTOTYPE_ADMISSION
        and doc['historical_support_contract_tests_passed']==204
        and doc['generic_queue_runtime_contract_tests_passed']==NEW_TEST_COUNT
        and doc['synthetic_following_queue_contract_tests_passed']==NEW_TEST_COUNT
        and doc['historical_support_fixture_scope']=='PRIOR73_QUALIFIED80_1539_INPUTS'
        and doc['current_queue_fixture_scope']=='DYNAMIC_NEXT_FULL_INPUTS'
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
        and doc['metadata_entry_runtime_contract_tests_passed']==14 and doc['metadata_entry_scope_bounds_enforced'] is True
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



def terminal_checkpoint(doc,owner):
    require(owner.done.is_set() and doc.get('state') in (PASS,LIGHT,'FAILED_NOT_ACCEPTED'),
        'TERMINAL_ONLY_NO_RESOURCE_RESTART')


def preserve_failure(capture,frame,owner,out,index,number):
    path=p.c.ROOT/f'{p.DIR}/cases/p255-failure-{index:03}-run{number:03}.json'
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
    root=p.c.ROOT;destination=root/f'{p.DIR}/p255-admission-run{args.run:03}.v1.json'
    if args.mode=='light':destination=root/f'{p.DIR}/p255-light-run{args.run:03}.v1.json'
    require(not destination.exists(),'FRESH_RECEIPT')
    context=g.observation.Context();owner=g.observation.Resources(context)
    q=meta=frame=candidate=body=capture=None;writes=[]
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),
        metadata_checkpoint_pin=CHECKPOINT,metadata_checkpoint_actual_pair_pin=HEAD,
        metadata_checkpoint_policy=checkpoint_policy(),retained_prior_generation_contract_executions=398,
        reviewed_original_stop_pin=r.STOP_PIN,completed_stop_review_pin=r.REVIEW_PIN,
        parent_connection_support_pin=r.CONNECTION_PIN,compound_anchor_pin=COMPOUND,reviewed_fixed_count_admission_pin=ADMISSION_FAILURE,
        reviewed_state_protocol_admission_pin=PROTOTYPE_ADMISSION,
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
        legacy,base,names,expected,exe,required,extras,healthy,healthy_body,historical_doc,historical_body=anchor(q);binding=p.v.identity(names,expected,exe)
        plan=progress(q,legacy,base,names,required,binding,extras);index,name=g.old.select(plan,names)
        with context.scope('contract_tests'):
            out['post_stop_runtime_contract_tests_passed']=contracts((legacy,plan,names,q.json(r.STOP_PIN['path'])),
                healthy,healthy_body,required,extras,historical_doc,historical_body)
        out.update(current_queue_runtime_contract_tests_passed=156,
            historical_support_contract_tests_passed=204,generic_queue_runtime_contract_tests_passed=NEW_TEST_COUNT,
            synthetic_following_queue_contract_tests_passed=NEW_TEST_COUNT,
            historical_support_fixture_scope='PRIOR73_QUALIFIED80_1539_INPUTS',current_queue_fixture_scope='DYNAMIC_NEXT_FULL_INPUTS',uncreated_borrower_connection_contract_tests_passed=8,
            lower_native_runtime_contract_tests_passed=8,lower_native_scope_bounds_enforced=True,
            metadata_entry_runtime_contract_tests_passed=14,metadata_entry_scope_bounds_enforced=True,
            synthetic_pre_GO_stop_connection_verified=True,binding=binding,selected_test_index=index,
            selected_test_name=name,prior_runtime_plan=plan,extra_frame_controller_pins=list(extras.values()),
            compound_anchor_verified_without_body_reexecution=True)
        if args.mode=='light':q.finish();candidate=dict(state=LIGHT)
        else:
            destination=root/f'{p.DIR}/p255-case-{index:03}-run{args.run:03}.v1.json'
            require(not destination.exists(),'FRESH_EXACT_CASE')
            require(not list((root/p.DIR/'cases').glob(f'p255-case-{index:03}-run*.json')),'NO_BODY_RETRY')
            body_path=root/f'{p.DIR}/cases/p255-case-{index:03}-run{args.run:03}.json'
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
    sys.modules.setdefault('resume_checkpoint_metadata_runtime',sys.modules[__name__])
    raise SystemExit(main())
