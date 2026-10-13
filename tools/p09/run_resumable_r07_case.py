"""P191 current r07 exact-one runtime plus independently closed resume receipt.

Whole historical preservation at batch boundaries; every non-EXE input and
current executable still freshly checked before/after each case. Never skips
corpus inputs or changes tests/guards. One case per invocation; no auto retry.
"""
import argparse
import contextlib
import io
import json
import re
import sys
import time
import unittest
from unittest.mock import patch

import resumable_current_r07 as v

c=v.c; run=v.observed.run; s=v.observed.s
SELF='tools/p09/run_resumable_r07_case.py'
TEST='tools/p09/tests/test_run_resumable_r07_case.py'
DIR='implementation/p09/evidence/resumable-r07'
BASE_CAPTURE=run.original.full.FullCapture
BASE_BOUNDED=run.original.full.bounded.BoundedProcessCapture
PREP_PASS='PASS_CURRENT_R07_RESUMABLE_BATCH_PREPARATION_ONLY_NOT_RUNTIME_OR_GATE'


def require(ok,code):v.require(ok,'RUN_'+code)


def paths(number):
    require(type(number) is int and 1<=number<=99,'GENERATION')
    base=f'implementation/p09/evidence/p09-191-r07-resumable-run{number:02}'
    return dict(light=base+'.light.v1.json',preparation=base+'.preparation.v1.json',
                closing=base+'.closing.v1.json',plan=base+'.plan.v1.json')


def task_for(index):
    require(type(index) is int and 1<=index<=249,'CASE_INDEX')
    return f'p191-r07-case-{index:03}-tests'


def selected_name(index,names):
    require(len(names)==249 and len(set(names))==249,'COMPILED249')
    require(type(index) is int and 1<=index<=249,'CASE_INDEX')
    name=names[index-1]
    require(v.NAME.fullmatch(name) and not name.startswith(v.CORPUS_PREFIX),'REGULAR_CASE_ONLY')
    return name


def worker(task):
    match=re.fullmatch(r'p191-r07-case-([0-9]{3})-tests',task)
    require(match is not None,'CLOSED_TASK')
    index=int(match[1]);require(task==task_for(index),'CLOSED_TASK')
    # Small immutable public list only; original GO/membership precede EXE call.
    parent=json.loads((c.ROOT/run.PARENT['path']).read_text(encoding='utf-8'))
    _,exe=run.parent_scope(parent);name=selected_name(index,parent['source_test_names'])
    run.original.require_scope(1200)
    original_call=c.subprocess.call
    def selected(args,**kw):
        require(args[1:]==[*run.original.TASK_ARGS,'--locked','--offline','--jobs','1','--color=never',
            '--target-dir',str(run.b.TARGET),'--','--test-threads=1']
            and kw['cwd']==c.ROOT and kw['stdin']==c.subprocess.DEVNULL,'ORIGINAL_CALL')
        env=kw['env']
        require(all(env[k]==value for k,value in dict(CARGO_BUILD_JOBS='1',RUST_TEST_THREADS='1',
            RUSTUP_AUTO_INSTALL='0',CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',
            CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true').items()),'ASSERTIONS_AND_OVERFLOW_RETAINED')
        kw['env']=dict(env,RUST_TEST_NOCAPTURE='0')
        return original_call([str(c.ROOT/exe['path']),*v.arguments(name)],**kw)
    with patch.object(c,'TARGET',run.b.TARGET),patch.object(c,'TASKS',{task:run.original.TASK_ARGS}), \
            patch.object(c.subprocess,'call',selected):return c.worker(task)


def runtime_scope(expected,exe):
    require(expected.get(exe['path'])==exe,'CURRENT_EXE')
    historical={n for n in expected if n.endswith('.exe') and n!=exe['path']}
    require(len(historical)==67,'EXACT67_HISTORICAL_BOUNDARY_ONLY')
    runtime={n:p for n,p in expected.items() if n not in historical}
    require(all(n in runtime for n in c.SOURCES),'ORIGINAL_SOURCES_RETAINED')
    require({n for n in expected if not n.endswith('.exe')}=={n for n in runtime if not n.endswith('.exe')},
            'ALL_NON_EXE_INPUTS_RETAINED')
    return runtime,historical


def contracts():
    v.observed.contracts();v.contracts()
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_run_resumable_r07_case')
    with patch('subprocess.Popen',side_effect=AssertionError('P191_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P191_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P191_NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==11 and not result.skipped,'CONTRACT109_PLUS22_PLUS11')
    return dict(contract_tests_passed=142,contract_tests_run=142)


def helpers():
    return sorted(set(v.observed.helpers())|{SELF,TEST,v.SELF,v.TEST,v.DEST,
        'implementation/p09/source-archive/p09-191-pre-terminal-return-repair/helper-preimages.v1.json',
        'implementation/p09/source-archive/p09-191-pre-history-bind/helper-preimages.v1.json',
        paths(1)['light'],paths(2)['light']})


def progress(q,names,expected,exe,extra=()):
    files=sorted((c.ROOT/DIR).glob('p190-case-*-attempt-*.json'))
    require(len(files)<=4096,'BOUNDED_RECEIPT_INVENTORY')
    rows=[];closings={}
    for file in files:
        q.checkpoint();name=file.relative_to(c.ROOT).as_posix()
        doc=q.json(name);pin=q.reader.snapshots[name]
        rows.append((file.name,doc,pin))
        closing=doc.get('closing_id')
        require(isinstance(closing,str) and re.fullmatch(
            r'implementation/p09/evidence/p09-191-r07-resumable-run[0-9]{2}\.closing\.v1\.json',closing),
            'CLOSING_PATH')
        if (c.ROOT/closing).exists() and closing not in closings:
            value=q.json(closing)
            if value.get('state')==v.CLOSING_PASS:closings[closing]=value
    for key,doc in extra:closings[key]=doc
    return v.plan(names,expected,exe,rows,closings)


def load(q,whole):
    require(q.pin(run.PARENT['path'])==run.PARENT,'CURRENT_PARENT')
    parent=q.json(run.PARENT['path']);expected,exe=run.parent_scope(parent)
    for fixed in v.observed.HISTORY:
        require(q.pin(fixed['path'])==fixed,'ORIGINAL_FAILED_HISTORY_IMMUTABLE')
    if whole:
        q.reader.protected=frozenset(n for n in expected if n.endswith('.exe'))
        for name,pin in expected.items():require(q.pin(name)==pin,'WHOLE_INPUTS')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
              and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and s.inputs.rust_inputs(c.ROOT,q.resources.checkpoint_io)==rust,'RUST785')
        names,modules=run.b.p.source_scope(q,expected)
        require(names==parent['source_test_names'] and modules==parent['source_module_instances'],'ORIGINAL249_59')
        archive=q.json(run.b.parser.ARCHIVE);_,old=run.b.parser.preimage(archive,run.b.parser.SOURCE)
        run.b.parser.inverse(q.text(run.b.parser.SOURCE),old.decode('utf-8'))
    for name in helpers():
        current=q.pin(name)
        if name in expected:require(current==expected[name],'FROZEN_HELPER_DRIFT')
        expected[name]=current
    return expected,parent['source_test_names'],exe


def flags():
    return dict(goal_status='active',full249_current_qualified=False,signed16_current_qualified=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False)


def preparation(number,mode):
    destination=s.scoped_path(paths(number)['preparation' if mode=='actual' else mode],fresh=True)
    resources=run.pressure.observation.ObservedResources();q=None;binding=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',**flags(),test_runtime_or_Cargo_SQL_Hangul_child_executed=False)
    try:
        resources.admit();q=run.pressure.PressureReader(resources);out.update(contracts())
        expected,names,exe=load(q,mode=='actual')
        status=progress(q,names,expected,exe)
        runtime,historical=runtime_scope(expected,exe)
        q.finish();binding=(expected,names,exe,status)
        out.update(state=PREP_PASS if mode=='actual' else 'PASS_CURRENT_R07_EXACT_ONE_CONTRACT_AND_PLAN_ONLY_NOT_RUNTIME',
            binding=v.identity(names,expected,exe),plan=status,whole_inputs=list(expected.values()),
            whole_preservation_audit_executed=mode=='actual',source_closing_exact=mode=='actual',
            historical_EXE_inputs_at_batch_boundaries=len(historical),case_runtime_input_count=len(runtime),
            repeated_historical_EXE_bytes_per_case_pass_avoided=sum(expected[n]['bytes'] for n in historical))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=run.original.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):
            out['state']='FAILED_NOT_ACCEPTED';binding=None
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out.update(wall_seconds=round(time.monotonic()-started,4),resource_tail=run.pressure.observation.parent_tail(resources))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason','wall_seconds')}),flush=True)
    return binding


def run_case(number,binding):
    expected,names,exe,status=binding;index=status['next_index'];attempt=status['next_attempt']
    require(index is not None and type(attempt) is int and 1<=attempt<=999,'NEXT_CASE')
    name=selected_name(index,names);runtime,historical=runtime_scope(expected,exe)
    identity=v.identity(names,expected,exe)
    receipt=f'{DIR}/p190-case-{index:03}-attempt-{attempt:03}.json'
    destination=s.scoped_path(receipt,fresh=True);destination.parent.mkdir(parents=True,exist_ok=True)
    box=run.owned.LatestOriginalSample();readers=[];captures=[];dump=json.dump;accepted_final=False
    class Capture(BASE_CAPTURE):
        def communicate(self,timeout):
            output,errors=BASE_BOUNDED.communicate(self,timeout)
            if self.process.returncode==0:
                v.terminal(output,errors,name);self.accepted=True
            return output,errors
    class RecordingCapture(Capture):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);captures.append(self)
    def fresh(checkpoint=None):
        reader=run.owned.OwnedReader(c.ROOT,checkpoint,samples=box,protected={exe['path']})
        readers.append(reader)
        actual=[]
        for n,p in runtime.items():
            pin=reader.fresh_pin(n);require(pin==p,'CASE_FRESH_ALL_NON_EXE_AND_CURRENT_EXE');actual.append(pin)
        return actual
    def write(row,stream,**kw):
        nonlocal accepted_final
        capture=captures[-1] if captures else None
        passed=row['state']=='PASS_SCOPED_NOT_GATE' and bool(capture and capture.accepted)
        accepted_final=passed
        if row['state']=='PASS_SCOPED_NOT_GATE':
            row['state']=v.CASE_PASS if passed else 'STOPPED_NOT_ACCEPTED'
            if not passed:row['stop_reason']='EXACT_ONE_TERMINAL_MISSING'
        row.update(schema_version=v.SCHEMA,**flags(),binding=identity,selected_test_names=[name],
            test_arguments=v.arguments(name),passed_test_names=[name] if passed else [],
            terminal_summary=dict(passed=1,failed=0,ignored=0,measured=0,filtered_out=248) if passed else None,
            closing_id=paths(number)['closing'],resource_stop_reason=row['stop_reason'],
            actual_job_membership_checked=passed,owned_limits_verified=row.get('owned_limits_readback',{}).get('verified',False),
            actual_Cargo_SQL_Hangul_run=False,raw_logs_saved=False,
            capture=dict(error_code=capture.diagnostics()['error_code'] if capture else 'NO_CAPTURE',
                per_stream_limit_bytes=32768,complete_streams=bool(capture and capture.accepted),raw_logs_saved=False),
            capture_diagnostics=capture.diagnostics() if capture else None,
            owned_source_reader_passes=[r.diagnostics() for r in readers],
            historical_EXE_rechecked_at_each_case=False,historical_EXE_boundary_count=len(historical),
            all_non_EXE_and_current_EXE_fresh_each_case=True,additional_sampler_or_foreign_PID_query=False,
            old_full249_acceptance_not_redefined=True,single_process_full249_qualified=False)
        if passed:v.validate_case(row,name,identity)
        return dump(row,stream,**kw)
    windows=v.observed.observer.windows_type(run.owned.windows_type(box))
    with patch.object(c,'__file__',str(c.ROOT/SELF)),patch.object(c,'TARGET',run.b.TARGET), \
            patch.object(c,'TASKS',{task_for(index):run.original.TASK_ARGS}),patch.object(c,'Windows',windows), \
            patch.object(c,'pins',fresh),patch.object(run.original.full.bounded,'BoundedProcessCapture',RecordingCapture), \
            patch.object(json,'dump',write):code=c.run(task_for(index),destination,1200)
    # c.run's old return compares PASS_SCOPED_NOT_GATE after our writer changes
    # the scoped receipt state. Return the validated exact-case result instead.
    return (0 if accepted_final else code),receipt


def close(number,binding=None):
    destination=s.scoped_path(paths(number)['closing'],fresh=True)
    resources=run.pressure.observation.ObservedResources();q=None;started=time.monotonic()
    out=dict(schema_version=v.CLOSING_SCHEMA,state='FAILED_NOT_ACCEPTED',**flags(),
        source_closing_exact=False,actual_test_runtime_executed=False,case_receipt_pins={})
    try:
        resources.admit();q=run.pressure.PressureReader(resources);out.update(contracts())
        prep=q.json(paths(number)['preparation'])
        require(prep['state']==PREP_PASS and prep['source_closing_exact'] and prep['IO']['finished']
            and prep['resource_watcher_cleanup_confirmed'] and prep['resource_stop_reason'] is None,'PREPARATION_SCOPE')
        expected,names,exe=load(q,True)
        require(v.pins(prep['whole_inputs'])==expected and prep['binding']==v.identity(names,expected,exe),'SAME_BOUNDARIES')
        status=prep['plan'];index=status['next_index'];attempt=status['next_attempt']
        require(index is not None,'PREP_NEXT_CASE')
        receipt=f'{DIR}/p190-case-{index:03}-attempt-{attempt:03}.json'
        doc=q.json(receipt);pin=q.reader.snapshots[receipt]
        v.validate_case(doc,selected_name(index,names),prep['binding'])
        require(doc['closing_id']==paths(number)['closing'],'OWN_CLOSING_ID')
        q.finish()
        out.update(state=v.CLOSING_PASS,source_closing_exact=True,binding=prep['binding'],
            source_freeze_before=prep['whole_inputs'],source_freeze_after=list(expected.values()),
            case_receipt_pins={receipt:pin},actual_preparation_pin=q.reader.snapshots[paths(number)['preparation']],
            whole_original68_EXE_and_Rust785_closed=True,original_P189_stop_preserved=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=run.original.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out.update(wall_seconds=round(time.monotonic()-started,4),resource_tail=run.pressure.observation.parent_tail(resources))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason','wall_seconds')}),flush=True)
    return 0 if out['state']==v.CLOSING_PASS else 2


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','plan','actual','close'),required=True)
    ap.add_argument('--run',type=int,choices=range(1,100),required=True);args=ap.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT,'CWD');run.original.require_scope(1200)
    if args.mode=='close':return close(args.run)
    binding=preparation(args.run,args.mode)
    if binding is None:return 2
    if args.mode!='actual':return 0
    require(binding[3]['next_index'] is not None,'NO_REGULAR_CASE_TO_START')
    code,_=run_case(args.run,binding)
    if code:return code  # No automatic retry or next case after stop.
    return close(args.run,binding)


if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,c.subprocess.SubprocessError) as error:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=run.original.closed_error(error))));raise SystemExit(2) from None
