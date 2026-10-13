"""P241: P239 미생성 Borrower 지원을 전체1525입력에 묶는 후속 실행기.

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
import resume_post_stop_compound_runtime as previous
import qualify_uncreated_borrower_failure as support
accepted=previous.accepted
candidate=support.candidate

r=accepted.r;p=r.p;g=r.g;review=accepted.review;closing=accepted.closing
SELF='tools/p09/resume_uncreated_borrower_runtime.py'
TEST='tools/p09/tests/test_uncreated_borrower_runtime.py'
NEW=(candidate.SELF,candidate.TEST,support.SELF,SELF,TEST)
EXTRAS=(*previous.EXTRAS,*NEW)
COMPOUND=dict(path=p.DIR+'/p236-case078-compound-run01.v1.json',bytes=355396,
    sha256='1761365334369863fd3aaf9afc5747456b6a4101dac37cdddbb9e69b3cfbf462')
HEALTHY=dict(path=p.DIR+'/p238-case-079-run002.v1.json',bytes=587604,
    sha256='a26dbc68b08b95a4b4f124f3e5ccb19377b27c4f8a19e5f88acb802288ad9b31')
SUPPORT=dict(path=p.DIR+'/p239-uncreated-borrower-support-run01.v1.json',bytes=4694,
    sha256='c05d84929932d7b99ec988eaef0137ec53b75869f115ae5e69b625fd83a5cfc4')
SCHEMA='hwpx-agent.p09-uncreated-borrower-runtime-pair/v1'
PASS='PASS_EXACT_R07_UNCREATED_BORROWER_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT='PASS_UNCREATED_BORROWER_SELECTION_NOT_ACTUAL_OR_GATE'
FILE=re.compile(r'p241-case-([0-9]{3})-run([0-9]{3})\.v1\.json')


def require(ok,code):p.require(ok,'POST_STOP_RUNTIME_'+code)


class Reader(previous.Reader):
    def json(self,path):
        carrier=super().json(path);name=self.name(path)
        if name.startswith(p.DIR+'/p241-') or name.startswith(p.DIR+'/cases/p241-'):
            r.h.canonical(carrier,self.reader.snapshots[name],self.checkpoint)
            return r.packed.unpack(carrier,self.checkpoint) if carrier.get('schema_version')==r.packed.SCHEMA else carrier
        return carrier


def anchor(q):
    legacy,base,names,expected,exe,old_required,old_extras=previous.anchor(q)
    binding=p.v.identity(names,expected,exe)
    base=previous.progress(q,legacy,base,names,old_required,binding,old_extras)
    require(base['runtime_source_qualified_individual_cases']==73 and base['next_runtime_index']==80
        and q.reader.snapshots[HEALTHY['path']]==HEALTHY,'SEALED_ACTUAL79_NOT_REEXECUTED')
    checked=review.bound_json(q,SUPPORT)
    require(checked['state']==support.PASS and checked['support_contract_tests_passed']==52
        and checked['runtime_connection_qualified'] is False and checked['actual_product_body_executed'] is False
        and checked['actual_Native_frame_or_CPU_STOP_executed'] is False
        and checked['resource_stop_reason'] is None and checked['resource_watcher_cleanup_confirmed'] is True
        and checked['IO']['finished'] is True and checked['IO']['bound_inputs']==checked['IO']['final_fresh_hashes']==12,
        'SEALED_SUPPORT52_NOT_ACTUAL_PRE_GO')
    for pin in checked['bound_input_pins']:require(q.pin(pin['path'])==pin,'SUPPORT_ALL_SOURCES_UNCHANGED')
    added={name:q.pin(name) for name in NEW};require(not set(added)&set(old_required),'ONLY_NEW_INPUTS')
    required={**old_required,**added};extras={**old_extras,**added}
    require(len(required)==1525 and len(extras)==58 and len(added)==5 and set(old_required)<set(required),
        'ALL_ORIGINAL1520_PLUS_FIVE')
    return legacy,base,names,expected,exe,required,extras

def native_pair(component,body,pin,required,binding,extras):
    p.validate_closing(component,body,pin,required,binding,extras)
    n=len(required);frame=component['source_frame'];own=frame['handles'];dup=own['borrowed_byte_streams']
    require(n==1525 and own['input_lock_handles_opened']==own['input_lock_handles_closed']==n+306
        and own['maximum_lock_seconds']==600 and own['ancestor_walk_steps']==305
        and own['native_open_pacing']['maximum_opens_per_second']==32
        and own['native_open_pacing']['open_reservations']==3*n+306
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*n
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==dup['byte_stream_pathname_reopens']==0
        and frame['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
            separate_pathname_reopens=0,regular_file_count=n,directory_count=306),
        'ALL_NATIVE_STREAMS_AND_IDENTITIES_1525')
    r.h.h.pressure_contract(own['native_open_backpressure'])


def record(doc,body,pin,required,binding,extras,names,legacy,base):
    index,name=g.old.select(base,names)
    require(doc['schema_version']==SCHEMA and doc['state']==PASS and doc.get('error_code') is None
        and doc['current_queue_runtime_contract_tests_passed']==156 and doc['post_stop_runtime_contract_tests_passed']==18
        and doc['selected_test_index']==index and doc['selected_test_name']==name
        and doc['reviewed_original_stop_pin']==r.STOP_PIN and doc['completed_stop_review_pin']==r.REVIEW_PIN
        and doc['parent_connection_support_pin']==r.CONNECTION_PIN
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
    early=sorted((*folder.glob('p241-admission-run*.v1.json'),*folder.glob('p241-light-run*.v1.json')))
    require(len(early)<=4096,'BOUNDED_EARLY')
    for path in early:closed_attempt(q.json(path.relative_to(p.c.ROOT).as_posix()))
    files=sorted(folder.glob('p241-case-*-run*.v1.json'));require(len(files)<=4096,'BOUNDED_CASES')
    plan=base
    for path in files:
        match=FILE.fullmatch(path.name);require(match is not None,'EXACT_FILENAME')
        index,number=map(int,match.groups());require(1<=index<=249 and 1<=number<=999,'INDEX_RUN')
        doc=q.json(path.relative_to(p.c.ROOT).as_posix());closed_attempt(doc)
        require(doc['selected_test_index']==index,'EXACT_FILENAME_INDEX')
        pin=doc['case_receipt_pin'];require(pin['path']==f'{p.DIR}/cases/p241-case-{index:03}-run{number:03}.json',
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
    # 계약 fixture만 새 schema/명시적 wiring 사실로 구성한다. 실제 증거 재작성 아님.
    fixture_doc=copy.deepcopy(healthy_doc)
    fixture_doc.update(uncreated_borrower_support_pin=SUPPORT,uncreated_borrower_adapter_selected=True,
        uncreated_borrower_connection_contract_tests_passed=8,synthetic_pre_GO_stop_connection_verified=True,
        actual_pre_GO_CPU_STOP_observed=False)
    with patch.object(original_tests,'m',sys.modules[__name__]), \
            patch.object(original_tests,'FIXTURES',(fixtures,fixture_doc,healthy_body,required,extras)), \
            patch('subprocess.Popen',side_effect=AssertionError('NO_WIRING_CONTRACT_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_WIRING_CONTRACT_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_WIRING_CONTRACT_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(original_tests))
        connection=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(connection_tests))
    require(result.wasSuccessful() and result.testsRun==18 and not result.skipped
        and connection.wasSuccessful() and connection.testsRun==8 and not connection.skipped,'RUNTIME18_PLUS_CONNECTION8')
    return 18

def terminal_checkpoint(doc,owner):
    require(owner.done.is_set() and doc.get('state') in (PASS,LIGHT,'FAILED_NOT_ACCEPTED'),
        'TERMINAL_ONLY_NO_RESOURCE_RESTART')


def preserve_failure(capture,frame,owner,out,index,number):
    path=p.c.ROOT/f'{p.DIR}/cases/p241-failure-{index:03}-run{number:03}.json'
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
    root=p.c.ROOT;destination=root/f'{p.DIR}/p241-admission-run{args.run:03}.v1.json'
    if args.mode=='light':destination=root/f'{p.DIR}/p241-light-run{args.run:03}.v1.json'
    require(not destination.exists(),'FRESH_RECEIPT')
    context=g.observation.Context();owner=g.observation.Resources(context)
    q=meta=frame=candidate=body=capture=None;writes=[]
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),
        reviewed_original_stop_pin=r.STOP_PIN,completed_stop_review_pin=r.REVIEW_PIN,
        parent_connection_support_pin=r.CONNECTION_PIN,compound_anchor_pin=COMPOUND,
        preserved_case078_stop_pin=review.ROOT_PIN,compound_anchor_verified_without_body_reexecution=False,
        uncreated_borrower_support_pin=SUPPORT,uncreated_borrower_adapter_selected=False,
        synthetic_pre_GO_stop_connection_verified=False,actual_pre_GO_CPU_STOP_observed=False,
        native_pressure_bridge_connected=False,packed_parent_writer_connected=False,deferred_failure_capture_connected=False,
        packed_root_writer_selected=True,frame_acquisition_requested=False,frame_acquisition_complete=False,
        product_worker_invocation_requested=False,accepted_exact_product_body_count=0,
        original_successful_bodies_not_reexecuted=True,receipt_serialization_policy=r.policy())
    try:
        owner.admit();q=Reader(owner,context)
        legacy,base,names,expected,exe,required,extras=anchor(q);binding=p.v.identity(names,expected,exe)
        plan=progress(q,legacy,base,names,required,binding,extras);index,name=g.old.select(plan,names)
        healthy=review.bound_json(q,HEALTHY);healthy_body=review.bound_json(q,healthy['case_receipt_pin'])
        with context.scope('contract_tests'):
            out['post_stop_runtime_contract_tests_passed']=contracts((legacy,plan,names,q.json(r.STOP_PIN['path'])),
                healthy,healthy_body,required,extras)
        out.update(current_queue_runtime_contract_tests_passed=156,uncreated_borrower_connection_contract_tests_passed=8,
            synthetic_pre_GO_stop_connection_verified=True,binding=binding,selected_test_index=index,
            selected_test_name=name,prior_runtime_plan=plan,extra_frame_controller_pins=list(extras.values()),
            compound_anchor_verified_without_body_reexecution=True)
        if args.mode=='light':q.finish();candidate=dict(state=LIGHT)
        else:
            destination=root/f'{p.DIR}/p241-case-{index:03}-run{args.run:03}.v1.json'
            require(not destination.exists(),'FRESH_EXACT_CASE')
            require(not list((root/p.DIR/'cases').glob(f'p241-case-{index:03}-run*.json')),'NO_BODY_RETRY')
            body_path=root/f'{p.DIR}/cases/p241-case-{index:03}-run{args.run:03}.json'
            body_path.parent.mkdir(parents=True,exist_ok=True);q.finish()
            held=r.h.h.native.PressureInputLocks(root,owner.checkpoint_io,owner)
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
        if q is not None:out['preparation_IO']=q.summary()
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
    sys.modules.setdefault('resume_uncreated_borrower_runtime',sys.modules[__name__])
    raise SystemExit(main())
