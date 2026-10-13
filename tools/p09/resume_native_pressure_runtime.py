"""P218: 원 runtime21을 재실행 없이 소비하고 Native pressure frame으로 계속 실행."""
import argparse
import io
import json
import re
import sys
import unittest
from unittest.mock import patch
import resume_generic_locked_runtime as g
import qualify_native_open_backpressure as qualified

p=g.p;native=qualified.native
SELF='tools/p09/resume_native_pressure_runtime.py'
TEST='tools/p09/tests/test_native_pressure_runtime.py'
NEW=(native.SELF,native.TEST,qualified.SELF,SELF,TEST)
EXTRAS=(*g.EXTRAS,*NEW)
SCHEMA='hwpx-agent.p09-native-pressure-runtime-pair/v1'
PASS='PASS_EXACT_R07_NATIVE_PRESSURE_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT='PASS_NATIVE_PRESSURE_RUNTIME_SELECTION_NOT_ACTUAL_OR_GATE'
FILE=re.compile(r'p218-case-([0-9]{3})-run([0-9]{3})\.v1\.json')
NATIVE_LIGHT=dict(path=p.DIR+'/p217-native-open-light-run01.v1.json',bytes=7106,
    sha256='118263568c50a5b36fff75571191592a1917cd601b5a73499e2a366637d37c77')
LAST_OLD=dict(path=p.DIR+'/p215-case-021-run008.v1.json',bytes=2103393,
    sha256='bbba659a0cf07291e5d283acfd63f3f00c2300899f8219605c445efe4070f80c')


def require(ok,code):p.require(ok,'NATIVE_RUNTIME_'+code)


def pressure_contract(row):
    require(row['warning_system_CPU_percent']==95 and row['cool_distinct_sample_windows']==2
        and row['maximum_pause_windows_per_entry']==8
        and all(row[k] is True for k in ('original_hard_resource_decisions_unmodified','original_IO_deadline_unmodified',
            'original_sampler_windows_reused','original_frame_deadline_checked_before_open',
            'original_32_open_rate_limit_and_no_burst_credits_preserved',
            'pressure_applies_to_native_reservations_including_borrowed_streams',
            'original_owner_sample_source_reused','cleanup_not_guarded_by_pressure'))
        and all(row[k] is False for k in ('new_native_query_or_sampler_thread_started','original_read_checks_skipped',
            'measured_CPU_or_PC_freeze_improvement_claimed')),'EXACT_ORIGINAL_OPEN_PRESSURE_POLICY')
    entries=row['warning_entries'];windows=row['completed_pause_windows'];maximum=row['maximum_observed_pause_windows_in_one_entry']
    require(all(type(n) is int and n>=0 for n in (entries,windows,maximum)) and 2*entries<=windows<=8*entries
        and 0<=maximum<=8 and ((entries==0 and maximum==0) or (entries>0 and maximum>=2))
        and row['requested_pause_seconds']==0.5*windows,'COMPLETE_DISTINCT_COOL_WINDOWS_ACCOUNTING')


def native_pair(component,body,pin,required,binding,extras):
    p.validate_closing(component,body,pin,required,binding,extras)
    n=len(required);frame=component['source_frame'];own=frame['handles'];dup=own['borrowed_byte_streams']
    require(n==1493 and own['input_lock_handles_opened']==own['input_lock_handles_closed']==n+306
        and own['maximum_lock_seconds']==600 and own['ancestor_walk_steps']==305
        and own['native_open_pacing']['maximum_opens_per_second']==32
        and own['native_open_pacing']['open_reservations']==3*n+306
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*n
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==dup['byte_stream_pathname_reopens']==0
        and frame['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,separate_pathname_reopens=0,
            regular_file_count=n,directory_count=306),'ALL_ORIGINAL_NATIVE_STREAM_IDENTITY_AND_CLEANUP')
    pressure_contract(own['native_open_backpressure'])


def anchor(q):
    legacy,base,names,expected,exe,old_required,old_extras=g.anchor(q)
    binding=p.v.identity(names,expected,exe);base=g.progress(q,legacy,base,names,old_required,binding,old_extras)
    require(base['runtime_source_qualified_individual_cases']==21 and base['next_runtime_index']==22
        and q.pin(LAST_OLD['path'])==LAST_OLD,'SEALED_ORIGINAL21_NOT_REEXECUTED')
    require(q.pin(NATIVE_LIGHT['path'])==NATIVE_LIGHT,'NATIVE_LIGHT_LITERAL_PIN')
    light=q.json(NATIVE_LIGHT['path'])
    require(light['state']==qualified.PASS and light.get('error_code') is None
        and light['native_open_contract_tests_passed']==10 and light['resource_stop_reason'] is None
        and light['resource_watcher_cleanup_confirmed'] is True
        and light['actual_native_pressure_frame_executed'] is False and light['actual_product_bridge_connected'] is False
        and light['IO']['finished'] is True and light['IO']['bound_inputs']==light['IO']['final_fresh_hashes']==9,
        'ONLY_ORIGINAL_SUPPORT_QUALIFICATION_NOT_ACTUAL')
    require(len(light['bound_input_pins'])==9
        and all(q.pin(pin['path'])==pin for pin in light['bound_input_pins']),'UNCHANGED_QUALIFIED_NATIVE_CODE')
    added={n:q.pin(n) for n in NEW};required={**old_required,**added};extras={**old_extras,**added}
    require(len(required)==1493 and set(old_required)<=set(required) and len(extras)==26,'FULL1488_PLUS_NEW5_NOT_SUBSET')
    return legacy,base,names,expected,exe,required,extras


def record(doc,body,pin,required,binding,extras,names,legacy,base):
    index,name=g.old.select(base,names)
    require(doc['schema_version']==SCHEMA and doc['state']==PASS and doc.get('error_code') is None
        and doc['selected_test_index']==index and doc['selected_test_name']==name and doc['binding']==binding
        and doc['prior_runtime_plan']==base and doc['case_receipt_pin']==pin
        and doc['native_pressure_bridge_connected'] is True and doc['frame_acquisition_requested'] is True
        and doc['frame_acquisition_complete'] is True and doc['product_worker_invocation_requested'] is True
        and doc['actual_product_child_executed'] is True
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[k] is False for k in ('whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved'))
        and doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs']==doc['preparation_IO']['final_fresh_hashes'],'COMPLETE_OVERALL_ONLY')
    native_pair(doc['closing_component'],body,pin,required,binding,extras)
    require(body['task']==f'p204-r07-case-{index:03}-tests' and doc['runtime_plan']==g.advance(legacy,base,names,index)
        and doc['accepted_exact_product_body_count']==1,'EXACT_ORIGINAL_BODY_AND_NEXT_QUEUE')
    return doc['runtime_plan']


def closed_attempt(doc):
    # Native 취득/GO 이전 또는 metadata/admission 중단도 검토 없이 재시도하지 않는다.
    require(doc.get('state') in (PASS,LIGHT) and doc.get('error_code') is None
        and doc.get('resource_stop_reason') is None and doc.get('resource_watcher_cleanup_confirmed') is True,
        'INSPECT_ANY_FAILED_ATTEMPT_BEFORE_RESUME')


def progress(q,legacy,base,names,required,binding,extras):
    folder=p.c.ROOT/p.DIR
    early=sorted((*folder.glob('p218-admission-run*.v1.json'),*folder.glob('p218-native-pressure-light-run*.v1.json')))
    require(len(early)<=4096,'BOUNDED_EARLY_ATTEMPTS')
    for path in early:closed_attempt(q.json(path.relative_to(p.c.ROOT).as_posix()))
    files=sorted(folder.glob('p218-case-*-run*.v1.json'));require(len(files)<=4096,'BOUNDED_CASES');plan=base
    for path in files:
        match=FILE.fullmatch(path.name);require(match is not None,'EXACT_CASE_FILENAME')
        index=int(match[1]);run=int(match[2]);require(1<=index<=249 and 1<=run<=999,'CASE_INDEX_RUN')
        doc=q.json(path.relative_to(p.c.ROOT).as_posix());closed_attempt(doc)
        require(doc['selected_test_index']==index,'EXACT_FILENAME_INDEX')
        body_path=doc['case_receipt_pin']['path']
        require(body_path==f'{p.DIR}/cases/p218-case-{index:03}-run{run:03}.json','OWN_EXACT_BODY_PATH_BEFORE_READ')
        pin=q.pin(body_path);require(pin==doc['case_receipt_pin'],'UNCHANGED_BODY_PIN')
        plan=record(doc,q.json(body_path),pin,required,binding,extras,names,legacy,plan)
    return plan


def contracts(fixtures):
    require(g.contracts(fixtures)==18 and qualified.contracts()==10,'ORIGINAL28_SUPPORT_CONTRACTS')
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_native_pressure_runtime as tests
    with patch.object(tests,'FIXTURES',fixtures),patch('subprocess.Popen',side_effect=AssertionError('NO_BRIDGE_CONTRACT_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_BRIDGE_CONTRACT_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_BRIDGE_CONTRACT_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun==12 and not result.skipped,'BRIDGE_CONTRACT12')
    return 40


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),default='light')
    ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=999,'CWD_RUN')
    root=p.c.ROOT;destination=root/f'{p.DIR}/p218-admission-run{args.run:03}.v1.json'
    if args.mode=='light':destination=root/f'{p.DIR}/p218-native-pressure-light-run{args.run:03}.v1.json'
    require(not destination.exists(),'FRESH_RECEIPT')
    context=g.observation.Context();owner=g.observation.Resources(context);q=meta=frame=None;candidate=body=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),native_pressure_bridge_connected=False,
        frame_acquisition_requested=False,frame_acquisition_complete=False,product_worker_invocation_requested=False,
        accepted_exact_product_body_count=0,original_successful_bodies_not_reexecuted=True)
    try:
        owner.admit();q=p.qualification.Reader(owner,context)
        legacy,base,names,expected,exe,required,extras=anchor(q);binding=p.v.identity(names,expected,exe)
        plan=progress(q,legacy,base,names,required,binding,extras);index,name=g.old.select(plan,names)
        with context.scope('contract_tests'):out['native_pressure_runtime_contract_tests_passed']=contracts((legacy,plan,names))
        out.update(binding=binding,selected_test_index=index,selected_test_name=name,prior_runtime_plan=plan,
            immutable_original21_pin=LAST_OLD,extra_frame_controller_pins=list(extras.values()))
        if args.mode=='light':q.finish();candidate=dict(state=LIGHT)
        else:
            destination=root/f'{p.DIR}/p218-case-{index:03}-run{args.run:03}.v1.json'
            require(not destination.exists(),'FRESH_EXACT_CASE')
            require(not list((root/p.DIR/'cases').glob(f'p218-case-{index:03}-run*.json')),'NO_EXISTING_BODY_RETRY')
            body_path=root/f'{p.DIR}/cases/p218-case-{index:03}-run{args.run:03}.json'
            body_path.parent.mkdir(parents=True,exist_ok=True);q.finish()
            held=native.PressureInputLocks(root,owner.checkpoint_io,owner)
            require(held.api.pacer.checkpoint is held.open_pressure and held.open_pressure.resources is owner,
                'ACTUAL_ORIGINAL_OWNER_PRESSURE_CONNECTION')
            frame=p.frames.Frame(p.frames.Registry(),required,owner.checkpoint_io,held=held)
            counter=p.frames.Counters(q.reader,frame.readers);context.reader=counter
            out.update(native_pressure_bridge_connected=True,frame_acquisition_requested=True)
            with context.scope('metadata_hash'):frame.acquire()
            out.update(frame_acquisition_complete=True,product_worker_invocation_requested=True,
                case_receipt_path=body_path.relative_to(root).as_posix())
            code=p.run_parent(frame,index,name,body_path,context,binding)
            meta=p.qualification.Reader(owner,context);counter.metadata.append(meta.reader);context.reader=counter
            body=meta.json(body_path.relative_to(root).as_posix());pin=meta.reader.snapshots[body_path.relative_to(root).as_posix()]
            out['actual_product_child_executed']=True if body.get('actual_product_child_executed') is True else None
            require(code==0,'ORIGINAL_PARENT_NOT_ACCEPTED');p.validate_parent(body,name,binding,required);meta.finish()
            component=dict(schema_version=p.CLOSING_SCHEMA,state=p.PASS,**p.r.flags(),selected_test_name=name,
                binding=binding,case_receipt_pin=pin,metadata_IO=meta.summary(),source_frame=frame.commit(body),
                extra_frame_controller_pins=list(extras.values()),sealed_whole_before_anchor=p.b.BASE_CLOSE)
            out.update(case_receipt_pin=pin,closing_component=component)
            candidate=dict(state=PASS,runtime_plan=g.advance(legacy,plan,names,index),accepted_exact_product_body_count=1)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt,p.c.subprocess.SubprocessError) as error:
        out.update(state='FAILED_NOT_ACCEPTED',error_code=p.b.run.original.closed_error(error));candidate=None
    finally:
        if frame is not None:
            try:
                if not frame.close():out.update(error_code='NATIVE_RUNTIME_FRAME_CLEANUP_FAILED');candidate=None
            except (ValueError,OSError):out.update(error_code='NATIVE_RUNTIME_FRAME_CLEANUP_FAILED');candidate=None
            out['terminal_source_frame']=frame.summary()
        if q is not None:out['preparation_IO']=q.summary()
        out['metadata_observation']=g.observation.summary(owner)
        def validate(doc):
            if doc['state']==PASS:
                doc['closing_component'].update(resource_stop_reason=doc['resource_stop_reason'],
                    resource_watcher_cleanup_confirmed=doc['resource_watcher_cleanup_confirmed'])
                record(doc,body,pin,required,binding,extras,names,legacy,plan)
            else:require(doc['state']==LIGHT and doc['preparation_IO']['finished'] is True,'LIGHT_FINAL_FRESH')
        g.complete(out,owner,candidate,validate)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','native_pressure_runtime_contract_tests_passed',
            'selected_test_index','error_code','resource_stop_reason')}))
    return 0 if out['state'] in (PASS,LIGHT) else 2


if __name__=='__main__':raise SystemExit(main())
