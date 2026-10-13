"""P238: 불변 P236 결합 수용을 소비하는 exact-one 후속 runtime 실행기.

원 P230·78 STOP는 수정하지 않는다. 정상 과거 기록의 원 validator와 P236
strict 결합 검사를 유지하고 새 실행의 전체1520입력/두 실제 읽기/자원 보호를
유지한다. 새 STOP/partial/실패를 자동 재시도하거나 다음 사례로 넘기지 않는다.
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
import accept_current_stop_compound as accepted

r=accepted.r;p=r.p;g=r.g;review=accepted.review;closing=accepted.closing
SELF='tools/p09/resume_post_stop_compound_runtime.py'
TEST='tools/p09/tests/test_post_stop_compound_runtime.py'
NEW=(*closing.EXTRAS,accepted.SELF,accepted.TEST,SELF,TEST)
EXTRAS=(*r.EXTRAS,*NEW)
COMPOUND=dict(path=p.DIR+'/p236-case078-compound-run01.v1.json',bytes=355396,
    sha256='1761365334369863fd3aaf9afc5747456b6a4101dac37cdddbb9e69b3cfbf462')
HEALTHY=dict(path=p.DIR+'/p230-case-077-run017.v1.json',bytes=581136,
    sha256='1e3bb6ada09cf04ea3ab083da9f772f180c22f90668aa274255200086a0a56b2')
SCHEMA='hwpx-agent.p09-post-stop-compound-runtime-pair/v1'
PASS='PASS_EXACT_R07_POST_STOP_COMPOUND_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT='PASS_POST_STOP_COMPOUND_SELECTION_NOT_ACTUAL_OR_GATE'
FILE=re.compile(r'p238-case-([0-9]{3})-run([0-9]{3})\.v1\.json')


def require(ok,code):p.require(ok,'POST_STOP_RUNTIME_'+code)


class Reader(r.Reader):
    def json(self,path):
        carrier=super().json(path);name=self.name(path)
        if name.startswith(p.DIR+'/p238-') or name.startswith(p.DIR+'/cases/p238-'):
            r.h.canonical(carrier,self.reader.snapshots[name],self.checkpoint)
            return r.packed.unpack(carrier,self.checkpoint) if carrier.get('schema_version')==r.packed.SCHEMA else carrier
        return carrier


def qualified_anchor(doc,compound,base,binding):
    require(doc['schema_version']==accepted.SCHEMA and doc['state']==accepted.PASS
        and doc.get('error_code') is None and doc['resource_stop_reason'] is None
        and doc['resource_watcher_cleanup_confirmed'] is True and doc['compound_contract_tests_passed']==20
        and doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']==206
        and doc['compound']==compound and doc['prior_runtime_plan']==base and doc['binding']==binding
        and doc['original_failed_root_pin']==review.ROOT_PIN and doc['original_stopped_parent_pin']==review.BODY_PIN
        and doc['original_zero_placeholder_pin']==review.ZERO_PIN
        and doc['separate_source_frame_pin']==accepted.SOURCE_PIN and doc['stop_review_pin']==closing.REVIEW_PIN
        and doc['actual_new_product_body_executed'] is False and doc['additional_full_source_frame_executed'] is False
        and doc['original_partial_post_hash_not_retroactively_promoted'] is True
        and doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[k] is False for k in ('full249_current_qualified','signed16_current_qualified',
            'whole1470_current_fresh_qualified','product_complete','PC_freeze_resolved')),
        'SEALED_COMPLETE_COMPOUND_NOT_ORIGINAL_STOP_PASS')


def anchor(q):
    legacy,base,names,expected,exe,old_required,old_extras=r.anchor(q)
    binding=p.v.identity(names,expected,exe)
    base,root=accepted.before_stop(q,legacy,base,names,old_required,binding,old_extras)
    body=review.bound_json(q,review.BODY_PIN);source=review.bound_json(q,accepted.SOURCE_PIN)
    prior=review.bound_json(q,COMPOUND)
    post_extras={name:q.pin(name) for name in closing.EXTRAS}
    compound=accepted.combine(root,body,source,names,expected,exe,old_required,post_extras)
    qualified_anchor(prior,compound,base,binding)
    require(q.pin(review.ZERO_PIN['path'])==review.ZERO_PIN,'ORIGINAL_EMPTY_BODY_PRESERVED')
    plan=accepted.advance(legacy,base,names);require(prior['runtime_plan']==plan,'EXACT72_NEXT79_ANCHOR')
    sealed=p.v.pins(prior['bound_input_pins'])
    for name in (*closing.EXTRAS,accepted.SELF,accepted.TEST):require(q.pin(name)==sealed[name],'COMPOUND_CODE_UNCHANGED')
    added={name:q.pin(name) for name in NEW}
    require(not set(added)&set(old_required),'ONLY_NEW_CONTROLLER_INPUTS')
    required={**old_required,**added};extras={**old_extras,**added}
    require(len(required)==1520 and len(extras)==53 and len(added)==8 and set(old_required)<set(required),
        'ALL_ORIGINAL1512_PLUS_EIGHT')
    return legacy,plan,names,expected,exe,required,extras


def native_pair(component,body,pin,required,binding,extras):
    p.validate_closing(component,body,pin,required,binding,extras)
    n=len(required);frame=component['source_frame'];own=frame['handles'];dup=own['borrowed_byte_streams']
    require(n==1520 and own['input_lock_handles_opened']==own['input_lock_handles_closed']==n+306
        and own['maximum_lock_seconds']==600 and own['ancestor_walk_steps']==305
        and own['native_open_pacing']['maximum_opens_per_second']==32
        and own['native_open_pacing']['open_reservations']==3*n+306
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*n
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==dup['byte_stream_pathname_reopens']==0
        and frame['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
            separate_pathname_reopens=0,regular_file_count=n,directory_count=306),
        'ALL_NATIVE_STREAMS_AND_IDENTITIES_1520')
    r.h.h.pressure_contract(own['native_open_backpressure'])


def record(doc,body,pin,required,binding,extras,names,legacy,base):
    index,name=g.old.select(base,names)
    require(doc['schema_version']==SCHEMA and doc['state']==PASS and doc.get('error_code') is None
        and doc['current_queue_runtime_contract_tests_passed']==156 and doc['post_stop_runtime_contract_tests_passed']==18
        and doc['selected_test_index']==index and doc['selected_test_name']==name
        and doc['reviewed_original_stop_pin']==r.STOP_PIN and doc['completed_stop_review_pin']==r.REVIEW_PIN
        and doc['parent_connection_support_pin']==r.CONNECTION_PIN
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
    early=sorted((*folder.glob('p238-admission-run*.v1.json'),*folder.glob('p238-light-run*.v1.json')))
    require(len(early)<=4096,'BOUNDED_EARLY')
    for path in early:closed_attempt(q.json(path.relative_to(p.c.ROOT).as_posix()))
    files=sorted(folder.glob('p238-case-*-run*.v1.json'));require(len(files)<=4096,'BOUNDED_CASES')
    plan=base
    for path in files:
        match=FILE.fullmatch(path.name);require(match is not None,'EXACT_FILENAME')
        index,number=map(int,match.groups());require(1<=index<=249 and 1<=number<=999,'INDEX_RUN')
        doc=q.json(path.relative_to(p.c.ROOT).as_posix());closed_attempt(doc)
        require(doc['selected_test_index']==index,'EXACT_FILENAME_INDEX')
        pin=doc['case_receipt_pin'];require(pin['path']==f'{p.DIR}/cases/p238-case-{index:03}-run{number:03}.json',
            'OWN_BODY_PATH')
        body=review.bound_json(q,pin)
        plan=record(doc,body,pin,required,binding,extras,names,legacy,plan)
    return plan


def contracts(fixtures,healthy_doc,healthy_body,required,extras):
    require(r.contracts(fixtures)==156,'UNCHANGED_ORIGINAL156_CONTRACTS')
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_post_stop_compound_runtime as tests
    with patch.object(tests,'FIXTURES',(fixtures,healthy_doc,healthy_body,required,extras)), \
            patch('subprocess.Popen',side_effect=AssertionError('NO_NEW_RUNTIME_CONTRACT_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_NEW_RUNTIME_CONTRACT_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_NEW_RUNTIME_CONTRACT_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun==18 and not result.skipped,'NEW_CONTRACT18')
    return 18


def terminal_checkpoint(doc,owner):
    require(owner.done.is_set() and doc.get('state') in (PASS,LIGHT,'FAILED_NOT_ACCEPTED'),
        'TERMINAL_ONLY_NO_RESOURCE_RESTART')


def preserve_failure(capture,frame,owner,out,index,number):
    path=p.c.ROOT/f'{p.DIR}/cases/p238-failure-{index:03}-run{number:03}.json'
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
    root=p.c.ROOT;destination=root/f'{p.DIR}/p238-admission-run{args.run:03}.v1.json'
    if args.mode=='light':destination=root/f'{p.DIR}/p238-light-run{args.run:03}.v1.json'
    require(not destination.exists(),'FRESH_RECEIPT')
    context=g.observation.Context();owner=g.observation.Resources(context)
    q=meta=frame=candidate=body=capture=None;writes=[]
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),
        reviewed_original_stop_pin=r.STOP_PIN,completed_stop_review_pin=r.REVIEW_PIN,
        parent_connection_support_pin=r.CONNECTION_PIN,compound_anchor_pin=COMPOUND,
        preserved_case078_stop_pin=review.ROOT_PIN,compound_anchor_verified_without_body_reexecution=False,
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
        out.update(current_queue_runtime_contract_tests_passed=156,binding=binding,selected_test_index=index,
            selected_test_name=name,prior_runtime_plan=plan,extra_frame_controller_pins=list(extras.values()),
            compound_anchor_verified_without_body_reexecution=True)
        if args.mode=='light':q.finish();candidate=dict(state=LIGHT)
        else:
            destination=root/f'{p.DIR}/p238-case-{index:03}-run{args.run:03}.v1.json'
            require(not destination.exists(),'FRESH_EXACT_CASE')
            require(not list((root/p.DIR/'cases').glob(f'p238-case-{index:03}-run*.json')),'NO_BODY_RETRY')
            body_path=root/f'{p.DIR}/cases/p238-case-{index:03}-run{args.run:03}.json'
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
            capture=r.adapter.Capture(frame,writes,index,name,binding)
            with patch.object(p,'RAW_DUMP',capture.writer):code=p.run_parent(frame,index,name,body_path,context,binding)
            if capture.pending:
                out['original_parent_STOP_captured_not_accepted']=True
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


if __name__=='__main__':raise SystemExit(main())
