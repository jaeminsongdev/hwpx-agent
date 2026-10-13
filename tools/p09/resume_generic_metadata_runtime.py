"""P252: 과거 검증204와 현재 큐156+16을 분리한 exact-one 실행기.
수용된 P250/test 코드는 불변이다. 불변 validator로 실제80을 소비하고
literal 미실행 비CPU admission 실패만 검토한다. 새 실패 자동 재시도 없음.
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
import resume_metadata_entry_runtime_r3 as prior
r=prior.r;p=prior.p;g=prior.g;review=prior.review
lower=prior.lower;entry=prior.entry;support=prior.support;candidate=prior.candidate
acquisition=prior.acquisition;metadata_review=prior.metadata_review
ACQUISITION_REVIEW=prior.ACQUISITION_REVIEW;LOWER_SUPPORT=prior.LOWER_SUPPORT
COMPOUND=prior.COMPOUND;SUPPORT=prior.SUPPORT;METADATA_REVIEW=prior.METADATA_REVIEW
ENTRY_SUPPORT=prior.ENTRY_SUPPORT;PROTOTYPE_FAILURE=prior.PROTOTYPE_FAILURE;BUDGET_FAILURE=prior.BUDGET_FAILURE
META_READ_LIMIT=prior.META_READ_LIMIT
SELF='tools/p09/resume_generic_metadata_runtime.py'
TEST='tools/p09/tests/test_generic_metadata_runtime.py'
NEW=(SELF,TEST);EXTRAS=(*prior.EXTRAS,*NEW)
HEALTHY=dict(path=p.DIR+'/p250-case-080-run003.v1.json',bytes=612696,
    sha256='b353add7c8a0e49134d0a7f2983e3a8083192f47151f15f5364a9cdf2fe8e4cd')
ADMISSION_FAILURE=dict(path=p.DIR+'/p250-admission-run004.v1.json',bytes=143215,
    sha256='ac9c1805040421eb945cc3b78cb2577572e9df807312bad20bc7726020e08fb2')
SCHEMA='hwpx-agent.p09-generic-metadata-runtime-pair/v1'
PASS='PASS_EXACT_R07_GENERIC_METADATA_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT='PASS_GENERIC_METADATA_SELECTION_NOT_ACTUAL_OR_GATE'
FILE=re.compile(r'p252-case-([0-9]{3})-run([0-9]{3})\.v1\.json')
require=prior.require
lower_contract=prior.lower_contract
metadata_contract=prior.metadata_contract
capture_for=prior.capture_for
closed_attempt=prior.closed_attempt


class Reader(prior.Reader):
    def json(self,path):
        carrier=super().json(path);name=self.name(path)
        if name.startswith(p.DIR+'/p252-') or name.startswith(p.DIR+'/cases/p252-'):
            r.h.canonical(carrier,self.reader.snapshots[name],self.checkpoint)
            return r.packed.unpack(carrier,self.checkpoint) if carrier.get('schema_version')==r.packed.SCHEMA else carrier
        return carrier


def connected_budget():
    out=dict(prior.connected_budget())
    out.update(new_runtime_inputs_upper_bound=1544,native_reservation_seconds=(3*1544+306)/20,
        predicted_combined_seconds_with_allowances=out['predicted_combined_seconds_with_allowances']+0.6,
        only_new_controller_count_projection_changed=True,original600_CPU_RAM_guards_preserved=True)
    require(out['predicted_combined_seconds_with_allowances']<600,'NEW_SCOPE_FITS_UNCHANGED600')
    return out


def enforce_scope_budget(required,original,added,budget):
    require(required=={**original,**added} and set(original)<set(required)
        and len(original)==1539 and len(required)==1541 and len(added)==2
        and len(required)<=budget['new_runtime_inputs_upper_bound']==1544
        and sum(pin['bytes'] for pin in required.values())-119022055<=1048576
        and required[p.m.EXE['path']]==p.m.EXE and budget==connected_budget(),'FULL_SCOPE_NEW_TWO')


def review_admission(doc):
    require(doc['schema_version']==prior.SCHEMA and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc['error_code']=='P208_POST_STOP_RUNTIME_RUNTIME18_PLUS_CONNECTION8_PLUS_LOWER8_PLUS_ENTRY14'
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc.get('selected_test_index') is None and doc['accepted_exact_product_body_count']==0
        and all(doc[k] is False for k in ('frame_acquisition_requested','frame_acquisition_complete',
            'product_worker_invocation_requested','actual_product_child_executed'))
        and doc['preparation_IO']['finished'] is False and doc['preparation_IO']['read_passes']==438
        and doc['preparation_IO']['bound_inputs']==251 and doc['preparation_IO']['final_fresh_hashes']==0
        and doc['preparation_IO']['bytes_read']==137396099
        and all(doc.get(k) is None for k in ('case_receipt_pin','case_receipt_path','terminal_source_frame',
            'terminal_parent_failure_sidecar_pin')),'EXACT_UNEXECUTED_NON_CPU_FIXED_FIXTURE_FAILURE')
    metadata_contract(doc['preparation_IO'])
    return dict(original_failure_not_accepted=True,product_and_Native_unexecuted=True,
        CPU_STOP_not_present=True,old_fixed74_assertions_retained_for_historical_fixture=True,
        new_current_queue_expectation_is_prior_plus_one=True,automatic_retry_allowed=False)


def prior_head(q,legacy,base,names,expected,required,extras):
    binding=p.v.identity(names,expected,p.m.EXE)
    root=review.bound_json(q,HEALTHY);body=review.bound_json(q,root['case_receipt_pin'])
    require(root['prior_runtime_plan']==base,'EXACT_BASE73_PRIOR80')
    plan=prior.record(root,body,root['case_receipt_pin'],required,binding,extras,names,legacy,base)
    require(plan['runtime_source_qualified_individual_cases']==74 and plan['next_runtime_index']==81,'SEALED74_NEXT81')
    failed=review.bound_json(q,ADMISSION_FAILURE);review_admission(failed)
    folder=p.c.ROOT/p.DIR
    require(sorted(x.name for x in folder.glob('p250-admission-run*.v1.json'))==['p250-admission-run004.v1.json']
        and sorted(x.name for x in folder.glob('p250-case-*-run*.v1.json'))==['p250-case-080-run003.v1.json']
        and sorted(x.name for x in folder.glob('p250-light-run*.v1.json'))==
            ['p250-light-run001.v1.json','p250-light-run002.v1.json']
        and not list((folder/'cases').glob('p250-*081*.json')),'NO_UNKNOWN_PRIOR_ATTEMPT_OR81_BODY')
    light=q.json(p.DIR+'/p250-light-run002.v1.json');prior.closed_attempt(light)
    require(light['prior_runtime_plan']==base and light['state']==prior.LIGHT,'PRIOR_LIGHT_NOT_CURRENT_BODY')
    return plan


def anchor(q):
    legacy,base,names,expected,exe,original,original_extras=prior.anchor(q)
    plan=prior_head(q,legacy,base,names,expected,original,original_extras)
    added={name:q.pin(name) for name in NEW}
    required={**original,**added};extras={**original_extras,**added}
    require(len(extras)==74 and not set(added)&set(original),'ONLY_NEW_CONTROLLERS')
    enforce_scope_budget(required,original,added,connected_budget())
    return legacy,plan,names,expected,exe,required,extras


def progress(q,legacy,base,names,required,binding,extras):
    folder=p.c.ROOT/p.DIR
    early=sorted((*folder.glob('p252-admission-run*.v1.json'),*folder.glob('p252-light-run*.v1.json')))
    require(len(early)<=4096,'BOUNDED_EARLY')
    for path in early:closed_attempt(q.json(path.relative_to(p.c.ROOT).as_posix()))
    plan=base;files=sorted(folder.glob('p252-case-*-run*.v1.json'));require(len(files)<=4096,'BOUNDED_CASES')
    for path in files:
        match=FILE.fullmatch(path.name);require(match is not None,'EXACT_FILENAME')
        index,number=map(int,match.groups());require(1<=index<=249 and 1<=number<=999,'INDEX_RUN')
        doc=q.json(path.relative_to(p.c.ROOT).as_posix());closed_attempt(doc)
        require(doc['selected_test_index']==index,'EXACT_FILENAME_INDEX')
        pin=doc['case_receipt_pin'];require(pin['path']==f'{p.DIR}/cases/p252-case-{index:03}-run{number:03}.json','OWN_BODY_PATH')
        body=review.bound_json(q,pin)
        plan=record(doc,body,pin,required,binding,extras,names,legacy,plan)
    return plan


def contracts(fixtures,healthy_doc,healthy_body,required,extras,historical_doc,historical_body):
    legacy,current,names,stop=fixtures
    original={n:pin for n,pin in required.items() if n not in NEW}
    original_extras={n:pin for n,pin in extras.items() if n not in NEW}
    historical=(legacy,healthy_doc['prior_runtime_plan'],names,stop)
    require(prior.contracts(historical,historical_doc,historical_body,original,original_extras)==18,'HISTORICAL204_RETAINED')
    require(r.contracts(fixtures)==156,'CURRENT_CORE156_RETAINED')
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_post_stop_compound_runtime as fixture
    import test_generic_metadata_runtime as tests
    synthetic=copy.deepcopy(healthy_doc)
    synthetic.update(reviewed_fixed_count_admission_pin=ADMISSION_FAILURE,
        historical_support_contract_tests_passed=204,generic_queue_runtime_contract_tests_passed=16,
        synthetic_following_queue_contract_tests_passed=16,
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
    require(checked.wasSuccessful() and checked.testsRun==16 and not checked.skipped
        and next_checked.wasSuccessful() and next_checked.testsRun==16 and not next_checked.skipped,
        'CURRENT16_AND_EXPLICIT_SYNTHETIC_FOLLOWING16')
    return 18

def native_pair(component,body,pin,required,binding,extras):
    p.validate_closing(component,body,pin,required,binding,extras)
    n=len(required);frame=component['source_frame'];own=frame['handles'];dup=own['borrowed_byte_streams']
    require(n==1541 and own['input_lock_handles_opened']==own['input_lock_handles_closed']==n+306
        and own['maximum_lock_seconds']==600 and own['ancestor_walk_steps']==305
        and own['native_open_pacing']['maximum_opens_per_second']==20
        and own['native_open_pacing']['open_reservations']==3*n+306
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*n
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==dup['byte_stream_pathname_reopens']==0
        and frame['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
            separate_pathname_reopens=0,regular_file_count=n,directory_count=306),
        'ALL_NATIVE_STREAMS_AND_IDENTITIES_1541')
    r.h.h.pressure_contract(own['native_open_backpressure']);lower_contract(own)


def record(doc,body,pin,required,binding,extras,names,legacy,base):
    index,name=g.old.select(base,names)
    require(doc['schema_version']==SCHEMA and doc['state']==PASS and doc.get('error_code') is None
        and doc['reviewed_fixed_count_admission_pin']==ADMISSION_FAILURE
        and doc['historical_support_contract_tests_passed']==204
        and doc['generic_queue_runtime_contract_tests_passed']==16
        and doc['synthetic_following_queue_contract_tests_passed']==16
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
    path=p.c.ROOT/f'{p.DIR}/cases/p252-failure-{index:03}-run{number:03}.json'
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
    root=p.c.ROOT;destination=root/f'{p.DIR}/p252-admission-run{args.run:03}.v1.json'
    if args.mode=='light':destination=root/f'{p.DIR}/p252-light-run{args.run:03}.v1.json'
    require(not destination.exists(),'FRESH_RECEIPT')
    context=g.observation.Context();owner=g.observation.Resources(context)
    q=meta=frame=candidate=body=capture=None;writes=[]
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),
        reviewed_original_stop_pin=r.STOP_PIN,completed_stop_review_pin=r.REVIEW_PIN,
        parent_connection_support_pin=r.CONNECTION_PIN,compound_anchor_pin=COMPOUND,reviewed_fixed_count_admission_pin=ADMISSION_FAILURE,
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
        historical_doc=review.bound_json(q,prior.HEALTHY)
        historical_body=review.bound_json(q,historical_doc['case_receipt_pin'])
        with context.scope('contract_tests'):
            out['post_stop_runtime_contract_tests_passed']=contracts((legacy,plan,names,q.json(r.STOP_PIN['path'])),
                healthy,healthy_body,required,extras,historical_doc,historical_body)
        out.update(current_queue_runtime_contract_tests_passed=156,
            historical_support_contract_tests_passed=204,generic_queue_runtime_contract_tests_passed=16,
            synthetic_following_queue_contract_tests_passed=16,
            historical_support_fixture_scope='PRIOR73_QUALIFIED80_1539_INPUTS',current_queue_fixture_scope='DYNAMIC_NEXT_FULL_INPUTS',uncreated_borrower_connection_contract_tests_passed=8,
            lower_native_runtime_contract_tests_passed=8,lower_native_scope_bounds_enforced=True,
            metadata_entry_runtime_contract_tests_passed=14,metadata_entry_scope_bounds_enforced=True,
            synthetic_pre_GO_stop_connection_verified=True,binding=binding,selected_test_index=index,
            selected_test_name=name,prior_runtime_plan=plan,extra_frame_controller_pins=list(extras.values()),
            compound_anchor_verified_without_body_reexecution=True)
        if args.mode=='light':q.finish();candidate=dict(state=LIGHT)
        else:
            destination=root/f'{p.DIR}/p252-case-{index:03}-run{args.run:03}.v1.json'
            require(not destination.exists(),'FRESH_EXACT_CASE')
            require(not list((root/p.DIR/'cases').glob(f'p252-case-{index:03}-run*.json')),'NO_BODY_RETRY')
            body_path=root/f'{p.DIR}/cases/p252-case-{index:03}-run{args.run:03}.json'
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
    sys.modules.setdefault('resume_generic_metadata_runtime',sys.modules[__name__])
    raise SystemExit(main())






