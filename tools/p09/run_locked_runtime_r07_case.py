"""P208 단일 미실행 r07 사례: 전후 실제 전체 byte 읽기+살아 있는 입력 frame.

원 C.run의 GO/Job/환경/중단/정리를 유지한다. 기존 성공 body와 원 whole 원장은
재작성하지 않는다. 별도 frame closing 없이는 새 body를 runtime 수용하지 않는다.
"""
import argparse
import copy
import io
import json
import re
import sys
import time
import unittest
from unittest.mock import patch
import qualify_locked_runtime_inputs as qualification
import locked_runtime_qualification_evidence as native_evidence
import runtime_input_frame as frames

prior=qualification.prior;c=prior.c;b=prior.b;r=prior.r;v=prior.v;core=b.core;m=prior.m
SELF='tools/p09/run_locked_runtime_r07_case.py'
TEST='tools/p09/tests/test_locked_runtime_r07_case.py'
EXTRAS=(frames.SELF,frames.TEST,SELF,TEST,native_evidence.SELF,native_evidence.TEST)
DIR='implementation/p09/evidence/locked-r07'
SCHEMA='hwpx-agent.p09-locked-r07-parent-candidate/v1'
CLOSING_SCHEMA='hwpx-agent.p09-locked-r07-source-frame-closing/v1'
PASS='PASS_EXACT_R07_NATIVE_FRAME_CLOSING_NOT_FULL_OR_GATE'
LIGHT_PASS='PASS_NATIVE_FRAME_BRIDGE_CONTRACTS_NOT_ACTUAL_OR_GATE'
NATIVE=dict(path='implementation/p09/evidence/runtime-r07/p09-206-input-lock-qualification-run07.v1.json',
    bytes=1199486,sha256='fe6e12c51e4cff5180b494be9cb9ada404b9b167d5da3ecefb32c5d845d8f0c5')
ORIGINAL_RUN=prior.ORIGINAL_RUN
RAW_WINDOWS=core.v.observed.observer.windows_type
RAW_DUMP=json.dump
BASE_CAPTURE=core.BASE_CAPTURE;BASE_COMMUNICATE=core.BASE_BOUNDED.communicate


def require(ok,code):c.require(ok,'P208_'+code)


def contracts():
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
        ('test_runtime_input_frame','test_locked_runtime_r07_case'))
    with patch('subprocess.Popen',side_effect=AssertionError('P208_NO_CONTRACT_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P208_NO_CONTRACT_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P208_NO_CONTRACT_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==30 and not checked.skipped,'CONTRACT20_PLUS10')
    return 30


def capture_type(name,on_new,base=BASE_CAPTURE,communicate=BASE_COMMUNICATE):
    class Capture(base):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);self.accepted=False;on_new(self)
        def communicate(self,timeout):
            output,errors=communicate(self,timeout)
            if self.process.returncode==0:v.terminal(output,errors,name);self.accepted=True
            return output,errors
    return Capture


def validate_parent(row,name,binding,required):
    require(row['schema_version']==SCHEMA and row['state']=='PASS_SCOPED_NOT_GATE'
        and row['native_frame_candidate_only'] is True and row['native_frame_closing_required'] is True
        and row['binding']==binding and row['selected_test_names']==[name]
        and row['test_arguments']==v.arguments(name),'EXACT_CANDIDATE_IDENTITY')
    v.closed_scope(row)
    require(row['terminal_summary']==dict(passed=1,failed=0,ignored=0,measured=0,filtered_out=248)
        and row['passed_test_names']==[name] and row['tests_passed']==1,'EXACT_TERMINAL')
    require(row['capture']==dict(error_code=None,per_stream_limit_bytes=32768,complete_streams=True,raw_logs_saved=False),
        'COMPLETE_BOUNDED_CAPTURE')
    require(v.pins(row['source_freeze'])==required and len(row['owned_source_reader_passes'])==2
        and all(p['read_passes']==len(required) and p['bytes_read']==sum(item['bytes'] for item in required.values())
            and p['read_rates_by_kind']==dict(binary=1048576,other=2097152)
            and p['original_owned_read_operations_preserved'] is True for p in row['owned_source_reader_passes']),
        'ORIGINAL_TWO_FULL_PER_CASE_BYTE_PASSES')
    require(row['task']==row['minimal_worker_task'] and re.fullmatch('p204-r07-case-[0-9]{3}-tests',row['task'])
        and row['minimal_owned_worker_path']==m.SELF and row['minimal_worker_source_only_import_connected'] is True,
        'ORIGINAL_MINIMAL_WORKER_CONNECTION')


def run_parent(frame,index,name,destination,context,binding):
    require(type(index) is int and 1<=index<=249 and v.NAME.fullmatch(name)
        and not name.startswith(v.CORPUS_PREFIX),'REGULAR_EXACT_CASE')
    frame.check();task=f'p204-r07-case-{index:03}-tests';captures=[];box=core.run.owned.LatestOriginalSample()
    def fresh(checkpoint=None):
        def factory(guard):return core.run.owned.OwnedReader(c.ROOT,guard,samples=box,protected={m.EXE['path']})
        with context.scope('metadata_hash' if not frame.boundaries else 'final_fresh_hash'):
            return frame.read_boundary(factory,checkpoint)
    windows=RAW_WINDOWS(core.run.owned.windows_type(box))
    class Windows(windows):
        def sample(self):frame.check();return super().sample()
    capture=capture_type(name,captures.append)
    def write(row,stream,**kw):
        cap=captures[-1] if captures else None;accepted=bool(cap and cap.accepted)
        row.update(r.flags())
        row.update(schema_version=SCHEMA,native_frame_candidate_only=True,native_frame_closing_required=True,
            binding=binding,selected_test_names=[name],test_arguments=v.arguments(name),
            terminal_summary=dict(passed=1,failed=0,ignored=0,measured=0,filtered_out=248) if accepted else None,
            passed_test_names=[name] if accepted else [],resource_stop_reason=row['stop_reason'],
            actual_job_membership_checked=accepted,owned_limits_verified=row.get('owned_limits_readback',{}).get('verified',False),
            actual_Cargo_SQL_Hangul_run=False,raw_logs_saved=False,
            capture=dict(error_code=cap.diagnostics()['error_code'] if cap else 'NO_CAPTURE',
                per_stream_limit_bytes=32768,complete_streams=accepted,raw_logs_saved=False),
            capture_diagnostics=cap.diagnostics() if cap else None,
            owned_source_reader_passes=[reader.diagnostics() for reader in frame.readers],
            minimal_owned_worker_path=m.SELF,minimal_worker_task=task,minimal_worker_source_only_import_connected=True,
            actual_product_child_executed=accepted)
        if row['state']=='PASS_SCOPED_NOT_GATE':validate_parent(row,name,binding,{n:dict(p) for n,p in frame.inputs.items()})
        return RAW_DUMP(row,stream,**kw)
    with patch.object(c,'__file__',str(c.ROOT/m.SELF)),patch.object(c,'TARGET',m.TARGET), \
            patch.object(c,'TASKS',{task:m.TASK_ARGS}),patch.object(c,'Windows',Windows),patch.object(c,'pins',fresh), \
            patch.object(core.run.original.full.bounded,'BoundedProcessCapture',capture),patch.object(json,'dump',write):
        return ORIGINAL_RUN(task,destination,1200)


def validate_closing(doc,body,pin,required,binding,extras):
    require(doc['schema_version']==CLOSING_SCHEMA and doc['state']==PASS and doc['binding']==binding
        and doc['case_receipt_pin']==pin and doc['extra_frame_controller_pins']==list(extras.values()),'EXACT_FRAME_CLOSING')
    validate_parent(body,doc['selected_test_name'],binding,required)
    frame=doc['source_frame'];own=frame['handles'];boundaries=frame['actual_byte_boundaries'];files=len(required)
    require(frame['frame_state']=='COMMITTED' and frame['registered_live_frame'] is False
        and frame['input_count']==files and frame['input_bytes']==sum(p['bytes'] for p in required.values())
        and frame['original_owned_cleanup_confirmed_before_release'] is True
        and frame['original_two_actual_per_case_byte_reads_retained'] is True
        and all(frame[k] is False for k in ('serialized_pin_reused_as_live_handle','input_exclusions_added','security_sandbox_claimed')),
        'LIVE_FRAME_CLOSED_NOT_SERIALIZED_CACHE')
    require(len(boundaries)==2 and [row['role'] for row in boundaries]==['before','after']
        and all(v.pins(row['actual_byte_pins'])==required
            and row['reader_diagnostics']==body['owned_source_reader_passes'][i] for i,row in enumerate(boundaries)),
        'SAME_ORIGINAL_ACTUAL_BEFORE_AFTER_BYTE_PASSES')
    require(own['input_lock_cleanup_confirmed'] is True and own['input_lock_handles_opened']==own['input_lock_handles_closed']
        and own['input_lock_handles_opened']>files and own['input_lock_handles_remaining']==0
        and own['probe_handles_opened']==own['probe_handles_closed']==own['probe_handles_remaining']==0
        and own['active_reader_bindings']==own['active_byte_streams']==0
        and own['byte_stream_identity_checks']==2*files and own['separate_pathname_reopens']==0
        and own['handle_close_failed_attempts']==0 and frame['held_identity_after_owned_cleanup']['held_identity_checks_complete'] is True,
        'ALL_SOURCE_HANDLES_AND_STREAMS_CLOSED_AFTER_JOB')
    require(doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and all(doc[k] is False for k in ('whole1470_current_fresh_qualified','full249_current_qualified',
            'signed16_current_qualified','product_complete','PC_freeze_resolved','actual_product_child_executed'))
        and doc['P09_gate']=='OPEN' and doc['sealed_whole_before_anchor']==b.BASE_CLOSE,'FRAME_NOT_WHOLE_OR_GATE')
    require(doc['metadata_IO']['finished'] is True and doc['metadata_IO']['bound_inputs']==doc['metadata_IO']['final_fresh_hashes'],
        'BODY_RECEIPT_FRESH_NOT_RAW_MEMORY_ONLY')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),default='light')
    ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT and 1<=args.run<=99,'CWD_RUN')
    path=b.s.scoped_path(f'{DIR}/p208-frame-{args.mode}-run{args.run:02}.v1.json',fresh=True)
    context=r.observation.Context();owner=r.observation.Resources(context);q=meta=frame=None;body=None;counter=None
    out=dict(schema_version=CLOSING_SCHEMA,state='FAILED_NOT_ACCEPTED',**r.flags(),
        product_test_body_started=False,original_successful_bodies_not_reexecuted=True)
    started=time.monotonic()
    try:
        owner.admit();q=qualification.Reader(owner,context);out['frame_contract_tests_passed']=contracts()
        extras={name:q.pin(name) for name in EXTRAS}
        if args.mode=='light':
            q.finish();out.update(state=LIGHT_PASS,extra_frame_controller_pins=list(extras.values()))
        else:
            expected,names,exe,runtime,fixture_inputs,helpers,base_scope=qualification.current_inputs(q)
            require(q.pin(NATIVE['path'])==NATIVE,'QUALIFIED_NATIVE_SOURCE_FRAME_PIN')
            native= q.json(NATIVE['path'])
            native_evidence.validate(native,base_scope,v.identity(names,expected,exe),helpers,1421,38)
            controllers={n:q.pin(n) for n in prior.CONTROLLERS};engine={n:q.pin(n) for n in (b.SELF,b.TEST)}
            with patch.object(prior.j,'case_controller',prior.case_controller):
                legacy,plan,closing_pins,attempts=prior.progress(q,expected,names,exe,engine,controllers)
            require(plan['runtime_successful_candidates_requiring_closing']==0,'NO_PENDING_ORIGINAL_BODY')
            index=plan['next_runtime_index'];require(index is not None,'NEXT_UNEXECUTED_CASE')
            name,argv=m.select(index, q.json(m.PARENT['path']))
            require(name==names[index-1] and name not in plan['runtime_qualified_test_names'],'NO_REPEAT_PASSED_TEST')
            required=qualification.combine(base_scope,{}, {},extras)
            require(len(required)==1473 and set(base_scope)<=set(required),'FULL_PRIOR_PLUS_FRAME_CONTROLLERS')
            body_path=b.s.scoped_path(f'{DIR}/cases/p208-case-{index:03}-run{args.run:02}.json',fresh=True)
            existing=list((c.ROOT/DIR/'cases').glob(f'p208-case-{index:03}-run*.json'))
            require(not existing,'INSPECT_EXISTING_FRAME_ATTEMPT_BEFORE_NEW_PRODUCT_EXECUTION')
            body_path.parent.mkdir(parents=True,exist_ok=True);q.finish()
            frame=frames.Frame(frames.Registry(),required,owner.checkpoint_io)
            counter=frames.Counters(q.reader,frame.readers);context.reader=counter
            with context.scope('metadata_hash'):frame.acquire()
            binding=v.identity(names,expected,exe)
            out.update(selected_test_name=name,selected_test_index=index,prior_runtime_plan=plan,
                case_receipt_path=body_path.relative_to(c.ROOT).as_posix(),product_test_body_started=True)
            code=run_parent(frame,index,name,body_path,context,binding)
            meta=qualification.Reader(owner,context);counter.metadata.append(meta.reader);context.reader=counter
            body=meta.json(body_path.relative_to(c.ROOT).as_posix());pin=meta.reader.snapshots[body_path.relative_to(c.ROOT).as_posix()]
            require(code==0,'ORIGINAL_PARENT_NOT_ACCEPTED');validate_parent(body,name,binding,required)
            meta.finish();out.update(binding=binding,case_receipt_pin=pin,metadata_IO=meta.summary(),
                source_frame=frame.commit(body),extra_frame_controller_pins=list(extras.values()),
                sealed_whole_before_anchor=b.BASE_CLOSE,native_qualification_anchor=NATIVE,state=PASS,
                selected_test_name=name)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt,c.subprocess.SubprocessError) as error:
        out['error_code']=b.run.original.closed_error(error)
    finally:
        if frame is not None:
            try:
                if not frame.close():out['state']='FAILED_NOT_ACCEPTED'
            except (ValueError,OSError) as error:out.update(state='FAILED_NOT_ACCEPTED',error_code=b.run.original.closed_error(error))
            out['source_frame']=frame.summary()
        b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
        if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(preparation_IO=q.summary(),preparation_bound_input_pins=list(q.reader.snapshots.values()))
        out.update(metadata_observation=r.observation.summary(owner),wall_seconds=round(time.monotonic()-started,4))
        if out['state']==PASS:
            try:validate_closing(out,body,pin,required,binding,extras)
            except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
                out.update(state='FAILED_NOT_ACCEPTED',error_code=b.run.original.closed_error(error))
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('x',encoding='utf-8') as stream:RAW_DUMP(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','frame_contract_tests_passed','selected_test_index','error_code','resource_stop_reason')}),flush=True)
    return 0 if out['state'] in (LIGHT_PASS,PASS) else 2


if __name__=='__main__':raise SystemExit(main())
