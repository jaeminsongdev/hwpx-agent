"""P192 share a sealed P191 baseline; serial exact-one jobs, one end closing.

The inherited whole baseline is historical, NOT a new pre-batch whole audit.
Every case still freshly checks all1470 baseline inputs except67 historical
EXEs before/after. Supplemental scheduler bytes are checked in both passes.
Only the end closing may qualify candidates, including after a later stop.
"""
import argparse
import io
import json
import re
import sys
import time
import unittest
from unittest.mock import patch

import run_resumable_r07_case as core

c=core.c;v=core.v;run=core.run;s=core.s
SELF='tools/p09/run_shared_resumable_r07_batch.py'
TEST='tools/p09/tests/test_shared_resumable_r07_batch.py'
OLD_RUNTIME_SCOPE=core.runtime_scope
BASE_PREP=dict(path=core.paths(1)['preparation'],bytes=601637,
    sha256='076afa535640a5afad9f50ed3fd932ab29238cc8f6ed0a20b2ca526ff11cc5f1')
BASE_CASE=dict(path=core.DIR+'/p190-case-001-attempt-001.json',bytes=617840,
    sha256='7dfdede3acbe6a1f900a3775beb4512ac173ad4c0599c420b4670bfa608bad64')
BASE_CLOSE=dict(path=core.paths(1)['closing'],bytes=895299,
    sha256='8e220071e5126f80fe9a31ca140c46edf20ae1304bf0233a975990b1ce096f7a')
PREP_PASS='PASS_P191_SEALED_BASELINE_AND_P192_SCHEDULER_PREPARATION_ONLY_NOT_NEW_WHOLE_AUDIT'
EVENT_SCHEMA='hwpx-agent.p09-p192-serial-case-event/v1'


def require(ok,code):core.require(ok,'SHARED_'+code)


def paths(number):
    require(type(number) is int and 2<=number<=99,'GENERATION')
    base=f'implementation/p09/evidence/p09-192-shared-r07-batch{number:02}'
    return dict(light=base+'.light.v1.json',preparation=base+'.preparation.v1.json',
        plan=base+'.plan.v1.json',closing=core.paths(number)['closing'],
        event_prefix=base+'.event-')


def limits(count,budget):
    require(type(count) is int and 1<=count<=5 and type(budget) is int and 1<=budget<=300,'BOUNDED_STARTS')


def source_extension(runtime,historical,engine):
    require(set(runtime).isdisjoint(engine) and not any(n.endswith('.exe') for n in engine),'SUPPLEMENTAL_SCOPE')
    require(set(engine)=={SELF,TEST},'EXACT_SCHEDULER_SOURCES')
    return {**runtime,**engine},historical


def validate_supplement(actual,expected,engine):
    runtime,historical=OLD_RUNTIME_SCOPE(expected,actual['binding']['compiled_test_executable_pin'])
    augmented,_=source_extension(runtime,historical,engine)
    require(v.pins(actual['source_freeze'])==augmented,'ALL_CASE_INPUTS_PLUS_SCHEDULER')
    require(actual['supplemental_scheduler_input_pins']==list(engine.values())
        and actual['baseline_input_manifest_not_rewritten'] is True
        and actual['serial_single_case_job'] is True,'SUPPLEMENTAL_RECEIPT')
    require(len(actual['owned_source_reader_passes'])==2 and all(
        r['read_passes']==len(augmented) and r['bytes_read']==sum(p['bytes'] for p in augmented.values())
        for r in actual['owned_source_reader_passes']),'TWO_FULL_FRESH_CASE_PASSES')


def baseline(q):
    for pin in (BASE_PREP,BASE_CASE,BASE_CLOSE,run.PARENT):require(q.pin(pin['path'])==pin,'SEALED_BASELINE_PINS')
    prep=q.json(BASE_PREP['path']);original=q.json(BASE_CASE['path']);closing=q.json(BASE_CLOSE['path'])
    parent=q.json(run.PARENT['path']);compiled,exe=run.parent_scope(parent)
    expected=v.pins(prep['whole_inputs']);names=parent['source_test_names']
    require(len(expected)==1470 and all(expected.get(n)==p for n,p in compiled.items()),'FULL_BASELINE1470')
    require(prep['state']==core.PREP_PASS and prep['source_closing_exact'] is True
        and prep['resource_stop_reason'] is None and prep['resource_watcher_cleanup_confirmed'] is True
        and prep['IO']['finished'] and prep['IO']['bound_inputs']==prep['IO']['final_fresh_hashes']==1470,
        'SEALED_BASELINE_PREPARATION')
    identity=v.identity(names,expected,exe)
    v.accept_case(original,names[0],identity,closing,expected,BASE_CASE)
    require(closing['IO']['finished'] and closing['IO']['bound_inputs']==closing['IO']['final_fresh_hashes']==1472
        and closing['whole_original68_EXE_and_Rust785_closed'],'SEALED_BASELINE_CLOSING')
    for fixed in v.observed.HISTORY:require(q.pin(fixed['path'])==fixed,'FAILED_HISTORY_IMMUTABLE')
    # Cheap current source inventory and helper freshness; not a whole1470 audit.
    rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
        and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
    require(len(rust)==785 and s.inputs.rust_inputs(c.ROOT,q.resources.checkpoint_io)==rust,'LIVE_RUST_INVENTORY')
    for name in (core.SELF,core.TEST,v.SELF,v.TEST):require(q.pin(name)==expected[name],'CORE_HELPERS_UNCHANGED')
    return expected,names,exe


def contracts():
    core.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_shared_resumable_r07_batch')
    with patch('subprocess.Popen',side_effect=AssertionError('P192_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P192_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P192_NO_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==12 and not checked.skipped,'CONTRACT142_PLUS12')
    return dict(contract_tests_run=154,contract_tests_passed=154)


def select(status):
    require(status['next_index'] is not None and status['successful_candidates_requiring_separate_closing']==0,
        'UNFINISHED_PREVIOUS_CANDIDATES_MUST_CLOSE_FIRST')
    return status


def prepare(number,mode,count,budget):
    limits(count,budget);destination=s.scoped_path(paths(number)['preparation' if mode=='actual' else mode],fresh=True)
    if mode=='actual':s.scoped_path(paths(number)['closing'],fresh=True)
    resources=run.pressure.observation.ObservedResources();q=None;binding=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',**core.flags(),actual_case_body_executed=False,
        current_whole_baseline_inputs_reaudited=False,inherited_before_is_historical_not_fresh=True)
    try:
        resources.admit();q=run.pressure.PressureReader(resources);out.update(contracts())
        expected,names,exe=baseline(q);engine={n:q.pin(n) for n in (SELF,TEST)}
        status=core.progress(q,names,expected,exe)
        select(status);q.finish();binding=(expected,names,exe,status,engine)
        out.update(state=PREP_PASS if mode=='actual' else 'PASS_SHARED_R07_BATCH_CONTRACT154_AND_PLAN_ONLY_NOT_RUNTIME',
            binding=v.identity(names,expected,exe),plan=status,supplemental_scheduler_input_pins=list(engine.values()),
            original_baseline_input_pins=list(expected.values()),sealed_whole_before_anchor=BASE_CLOSE,
            maximum_cases=count,new_case_start_budget_seconds=budget,case_execution_sequential=True,
            case_runtime_sources_checked_before_and_after=True,historical67_EXE_final_closing_required=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=run.original.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):
            out['state']='FAILED_NOT_ACCEPTED';binding=None
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason','wall_seconds')}),flush=True)
    return binding


def one(number,binding,status):
    expected,names,exe,_,engine=binding;dump=json.dump
    def runtime(current,current_exe):
        require(current==expected and current_exe==exe,'UNMODIFIED_BASELINE_IDENTITY')
        rt,historical=OLD_RUNTIME_SCOPE(current,current_exe)
        return source_extension(rt,historical,engine)
    def write(row,stream,**kw):
        if row.get('schema_version')==v.SCHEMA:
            row.update(supplemental_scheduler_input_pins=list(engine.values()),baseline_input_manifest_not_rewritten=True,
                serial_single_case_job=True,shared_batch_generation=number,shared_whole_before_anchor=BASE_CLOSE)
            if row['state']==v.CASE_PASS:validate_supplement(row,expected,engine)
        return dump(row,stream,**kw)
    with patch.object(core,'runtime_scope',runtime),patch.object(json,'dump',write):
        return core.run_case(number,(expected,names,exe,status))


def event(number,step,receipt,code,binding):
    expected,names,exe,_,engine=binding;destination=s.scoped_path(
        paths(number)['event_prefix']+f'{step:02}.v1.json',fresh=True)
    resources=run.pressure.observation.ObservedResources();q=None;next_status=None
    out=dict(schema_version=EVENT_SCHEMA,state='FAILED_NOT_ACCEPTED',**core.flags(),step=step,
        actual_runtime_in_this_metadata_event=False,case_return_code=code,case_receipt_path=receipt,
        supplemental_scheduler_input_pins=list(engine.values()))
    try:
        resources.admit();q=run.pressure.PressureReader(resources)
        for n,p in engine.items():require(q.pin(n)==p,'ENGINE_UNCHANGED')
        doc=q.json(receipt);pin=q.reader.snapshots[receipt]
        require(doc['binding']==v.identity(names,expected,exe) and doc['closing_id']==paths(number)['closing'],'OWN_BATCH_CASE')
        if code==0:
            v.validate_case(doc,doc['selected_test_names'][0],doc['binding']);validate_supplement(doc,expected,engine)
            status=core.progress(q,names,expected,exe)
            require(status['successful_candidates_requiring_separate_closing']==step,'EXACT_PENDING_CANDIDATES')
            next_status=status
        else:require(doc['state'] in ('STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED','FAILED_NOT_ACCEPTED'),'STOP_RECEIPT')
        q.finish();out.update(state='PASS_SERIAL_CASE_EVENT_METADATA_ONLY_NOT_BATCH_CLOSING',
            case_receipt_pin=pin,case_state=doc['state'],plan=next_status)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=run.original.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):
            out['state']='FAILED_NOT_ACCEPTED';next_status=None
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps(dict(state=out['state'],step=step,case_state=out.get('case_state'),
            error_code=out.get('error_code'),resource_stop_reason=out.get('resource_stop_reason'))),flush=True)
    return next_status


def close(number):
    destination=s.scoped_path(paths(number)['closing'],fresh=True)
    resources=run.pressure.observation.ObservedResources();q=None;started=time.monotonic()
    out=dict(schema_version=v.CLOSING_SCHEMA,state='FAILED_NOT_ACCEPTED',**core.flags(),
        source_closing_exact=False,actual_test_runtime_executed=False,case_receipt_pins={},publisher='P192_shared_batch')
    try:
        resources.admit();q=run.pressure.PressureReader(resources);out.update(contracts())
        prep=q.json(paths(number)['preparation'])
        require(prep['state']==PREP_PASS and prep['resource_stop_reason'] is None
            and prep['resource_watcher_cleanup_confirmed'] and prep['IO']['finished'],'SHARED_PREPARATION')
        expected,names,exe=baseline(q)
        require(expected==v.pins(prep['original_baseline_input_pins'])
            and prep['binding']==v.identity(names,expected,exe),'UNCHANGED_BASELINE')
        engine=v.pins(prep['supplemental_scheduler_input_pins'])
        for n,p in engine.items():require(q.pin(n)==p,'SUPPLEMENTAL_END_CLOSING')
        q.reader.protected=frozenset(n for n in expected if n.endswith('.exe'))
        for n,p in expected.items():require(q.pin(n)==p,'WHOLE1470_END')
        actual_names,modules=run.b.p.source_scope(q,expected)
        parent=q.json(run.PARENT['path'])
        require(actual_names==names and modules==parent['source_module_instances'],'CURRENT249_59')
        files=sorted((c.ROOT/'implementation/p09/evidence').glob(
            c.Path(paths(number)['event_prefix']).name+'*.v1.json'))
        require(1<=len(files)<=prep['maximum_cases']<=5,'BOUNDED_EVENTS')
        receipt_pins={};events=[]
        for step,file in enumerate(files,1):
            row=q.json(file.relative_to(c.ROOT).as_posix())
            require(row['schema_version']==EVENT_SCHEMA and row['step']==step
                and row['state']=='PASS_SERIAL_CASE_EVENT_METADATA_ONLY_NOT_BATCH_CLOSING'
                and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'COMPLETE_EVENT')
            doc=q.json(row['case_receipt_path']);pin=q.reader.snapshots[row['case_receipt_path']]
            require(pin==row['case_receipt_pin'],'EVENT_CASE_PIN')
            if row['case_return_code']==0:
                v.validate_case(doc,doc['selected_test_names'][0],prep['binding'])
                validate_supplement(doc,expected,engine)
                require(doc['closing_id']==paths(number)['closing'],'CASE_OWN_CLOSING')
                receipt_pins[pin['path']]=pin
            else:
                require(step==len(files),'STOP_MUST_BE_LAST');require(doc['state']!='PASS_EXACT_R07_SINGLE_CASE_NOT_FULL_OR_GATE','NO_FALSE_STOP')
            events.append(q.reader.snapshots[file.relative_to(c.ROOT).as_posix()])
        require(bool(receipt_pins),'AT_LEAST_ONE_EXIT_ZERO_CASE')
        q.finish();out.update(state=v.CLOSING_PASS,source_closing_exact=True,binding=prep['binding'],
            source_freeze_before=prep['original_baseline_input_pins'],source_freeze_after=list(expected.values()),
            supplemental_scheduler_before=prep['supplemental_scheduler_input_pins'],
            supplemental_scheduler_after=list(engine.values()),case_receipt_pins=receipt_pins,
            sealed_whole_before_anchor=BASE_CLOSE,inherited_before_is_historical_not_new_fresh_audit=True,
            case_event_pins=events,accepted_new_case_count=len(receipt_pins),whole_original68_EXE_and_Rust785_closed=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=run.original.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out.update(wall_seconds=round(time.monotonic()-started,4),resource_tail=run.pressure.observation.parent_tail(resources))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','accepted_new_case_count','error_code','resource_stop_reason','wall_seconds')}),flush=True)
    return 0 if out['state']==v.CLOSING_PASS else 2


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','plan','actual','close'),required=True)
    ap.add_argument('--run',type=int,choices=range(2,100),required=True)
    ap.add_argument('--max-cases',type=int,default=2);ap.add_argument('--start-budget-seconds',type=int,default=300)
    args=ap.parse_args();require(c.Path.cwd().resolve()==c.ROOT,'CWD');core.run.original.require_scope(1200)
    limits(args.max_cases,args.start_budget_seconds)
    if args.mode=='close':return close(args.run)
    binding=prepare(args.run,args.mode,args.max_cases,args.start_budget_seconds)
    if binding is None:return 2
    if args.mode!='actual':return 0
    status=binding[3];started=time.monotonic()
    for step in range(1,args.max_cases+1):
        if time.monotonic()-started>=args.start_budget_seconds or status['next_index'] is None:break
        print(json.dumps(dict(state='STARTING_ONE_OWNED_CASE',index=status['next_index'],step=step)),flush=True)
        code,receipt=one(args.run,binding,status)
        status=event(args.run,step,receipt,code,binding)
        if code or status is None:return 2  # No next case/auto closing after a stop.
    return close(args.run)


if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,c.subprocess.SubprocessError) as error:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=run.original.closed_error(error))));raise SystemExit(2) from None
