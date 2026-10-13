"""P198: one unexecuted case, separately closed runtime sources, legacy Gate intact.

P190/P191 실제 terminal/Job/전후 source 검증을 그대로 사용한다.
P198 receipt는 별도 디렉터리이며 frozen P196 및 원 whole 큐를 재작성하지 않는다.
실패/중단 뒤 자동 retry나 다음 case는 없다. corpus6은 미실행으로 유지한다.
"""
import argparse
import io
import json
import re
import sys
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import runtime_source_closing_r07 as r
import process_cpu_attribution as attribution

c=r.c;b=r.b;core=r.core;v=r.v
SELF='tools/p09/run_runtime_resumable_r07_case.py'
TEST='tools/p09/tests/test_runtime_resumable_r07_case.py'
DIR='implementation/p09/evidence/runtime-r07/cases'
META='implementation/p09/evidence/runtime-r07'
CONTROLLERS=(SELF,TEST,r.SELF,r.TEST,r.observation.SELF,r.observation.TEST,attribution.SELF,attribution.TEST)
CASE_FILE=re.compile(r'p190-case-([0-9]{3})-attempt-([0-9]{3})\.json')
CLOSE_FILE=re.compile(r'p198-case-([0-9]{3})-attempt-([0-9]{3})-close-([0-9]{2})\.v1\.json')
RAW_WINDOWS_TYPE=v.observed.observer.windows_type
RAW_DUMP=json.dump


def require(ok,code):c.require(ok,'P198_'+code)


def target(mode,number,index=None,attempt=None):
    require(type(number) is int and 1<=number<=99,'RUN')
    require(mode in ('light','plan','preparation','close'),'MODE')
    if mode=='close':
        r.case_path(index,attempt)
        return f'{META}/p198-case-{index:03}-attempt-{attempt:03}-close-{number:02}.v1.json'
    return f'{META}/p198-runtime-resume-{mode}-run{number:02}.v1.json'


def controllers(q):return {name:q.pin(name) for name in CONTROLLERS}


def extended_scope(expected,exe,engine,controller):
    runtime,historical=b.OLD_RUNTIME_SCOPE(expected,exe)
    runtime,_=b.source_extension(runtime,historical,engine)
    require(set(controller)==set(CONTROLLERS) and set(runtime).isdisjoint(controller)
        and not set(controller)&historical,'EXACT_EXECUTION_CONTROLLERS')
    return {**runtime,**controller},historical


def select(plan,names,attempts):
    require(plan['runtime_successful_candidates_requiring_closing']==0,'CLOSE_PASSED_BODY_BEFORE_NEXT')
    index=plan['next_runtime_index'];require(index is not None,'NO_REGULAR_CASE')
    require(names[index-1] not in plan['runtime_qualified_test_names'],'NO_REPEAT_PASSED_CASE')
    core.selected_name(index,names)
    attempt=attempts.get(index,0)+1
    require(attempt<=999,'ATTEMPT_LIMIT')
    return dict(next_index=index,next_attempt=attempt)


def progress(q,expected,names,exe,engine,controller):
    legacy,base,pins=r.progress(q,expected,names,exe,engine,{n:controller[n] for n in (r.SELF,r.TEST)})
    files=sorted((c.ROOT/DIR).glob('p190-case-*-attempt-*.json'))
    require(len(files)<=4096,'BOUNDED_CASES');passed={};attempts={};seen=set()
    for file in files:
        match=CASE_FILE.fullmatch(file.name);require(match is not None,'CASE_FILENAME')
        index,attempt=map(int,match.groups());r.case_path(index,attempt)
        require((index,attempt) not in seen,'DUPLICATE_ATTEMPT');seen.add((index,attempt))
        attempts[index]=max(attempts.get(index,0),attempt)
        name=file.relative_to(c.ROOT).as_posix();doc=q.json(name)
        require(doc['binding']==v.identity(names,expected,exe) and doc['schema_version']==v.SCHEMA
            and doc['selected_test_names']==[names[index-1]],'CASE_IDENTITY')
        if doc['state']==v.CASE_PASS:
            r.case_scope(doc,expected,names,exe,engine,controller)
            passed[name]=(doc,q.reader.snapshots[name])
        else:require(doc['state'] in ('STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED','FAILED_NOT_ACCEPTED'),'CASE_STATE')
    closed=[];closings=sorted((c.ROOT/META).glob('p198-case-*-attempt-*-close-*.v1.json'))
    require(len(closings)<=4096,'BOUNDED_CLOSINGS')
    for file in closings:
        match=CLOSE_FILE.fullmatch(file.name);require(match is not None,'CLOSING_FILENAME')
        name=file.relative_to(c.ROOT).as_posix();doc=q.json(name)
        if doc['state']!=r.PASS:
            require(doc['state']=='FAILED_NOT_ACCEPTED','CLOSING_STATE');continue
        source=f'{DIR}/p190-case-{int(match[1]):03}-attempt-{int(match[2]):03}.json'
        require(source in passed,'CLOSING_HAS_PASSED_CASE');case,pin=passed[source]
        r.validate(doc,case,pin,expected,names,exe,engine,controller)
        closed.append(case['selected_test_names'][0]);pins.append(q.reader.snapshots[name])
    original=set(base['runtime_qualified_test_names'])
    require(not original&set(closed),'NO_DUPLICATE_ORIGINAL_SUCCESS')
    combined=dict(legacy,accepted_test_names=base['runtime_qualified_test_names'],
        accepted_individual_cases=len(original))
    all_passed=list(original|{doc['selected_test_names'][0] for doc,_ in passed.values()})
    plan=r.runtime_plan(combined,names,closed,all_passed)
    # 집합 계산에 prior runtime 수용을 쓰되 원 whole 수용 수를 바꾸지 않는다.
    plan['legacy_whole_accepted_individual_cases']=legacy['accepted_individual_cases']
    plan['legacy_whole_pending_successful_candidates']=legacy['successful_candidates_requiring_separate_closing']
    plan['prior_runtime_qualified_cases']=len(original)
    return legacy,plan,pins,attempts


def contracts():
    result=r.contracts();result['process_cpu_attribution_contract_tests_passed']=attribution.contracts()
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_runtime_resumable_r07_case')
    with patch('subprocess.Popen',side_effect=AssertionError('P198_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P198_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P198_NO_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==12 and not checked.skipped,'CONTRACT12')
    result['runtime_resume_contract_tests_passed']=12;return result


def prepare(mode,number):
    destination=b.s.scoped_path(target('preparation' if mode=='actual' else mode,number),fresh=True)
    context=r.observation.Context();owner=attribution.Resources(context);q=None;binding=None
    out=dict(state='FAILED_NOT_ACCEPTED',**r.flags(),actual_case_body_executed=False)
    try:
        owner.admit();q=r.Reader(owner,context);control=controllers(q);out.update(contracts())
        expected,names,exe=b.baseline(q);engine={n:q.pin(n) for n in (b.SELF,b.TEST)}
        legacy,plan,pins,attempts=progress(q,expected,names,exe,engine,control)
        status=select(plan,names,attempts) if mode=='actual' else None
        if status:
            b.s.scoped_path(f"{DIR}/p190-case-{status['next_index']:03}-attempt-{status['next_attempt']:03}.json",fresh=True)
            b.s.scoped_path(target('close',number,status['next_index'],status['next_attempt']),fresh=True)
        q.finish();out.update(state='PASS_RUNTIME_RESUME_PREPARATION_NOT_BODY_OR_WHOLE_OR_GATE',
            runtime_plan=plan,legacy_plan=legacy,runtime_closing_receipt_pins=pins,
            selected_case_status=status,closing_controller_pins=list(control.values()))
        binding=(expected,names,exe,status,engine,control)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.run.original.closed_error(error)
    finally:
        b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
        if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED';binding=None
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['metadata_observation']=r.observation.summary(owner)
        out['process_CPU_attribution']=attribution.summary(owner)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:RAW_DUMP(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','runtime_resume_contract_tests_passed','error_code','resource_stop_reason')}),flush=True)
    return binding if out['state'].startswith('PASS_') else None


def tracked_windows_type(base,registry):
    prior=RAW_WINDOWS_TYPE(base)
    class Windows(prior):
        def __init__(self):
            super().__init__();require(not registry,'ONE_RUNTIME_WINDOWS');registry.append(self)
            self.attribution=[];self.attribution_error=None;self.previous=None;self.due=0
            self.process_cpu=attribution.ProcessCPU(self.k,self.times)
        def sample(self):
            row=super().sample();row.update(r.observation.own_memory(self.k,self.total_ram))
            now=time.monotonic()
            if self.attribution_error is None and now>=self.due:
                try:
                    current=self.process_cpu.snapshot()
                    if self.previous is not None:
                        require(len(self.attribution)<600,'CPU_ATTRIBUTION_SAMPLE_LIMIT')
                        item=attribution.compare(self.previous,current);item['time_utc']=row['time_utc']
                        self.attribution.append(item)
                    self.previous=current;self.due=time.monotonic()+attribution.INTERVAL_SECONDS
                except (ValueError,OSError,AttributeError) as error:
                    self.attribution_error=b.run.original.closed_error(error)
            return row
    return Windows


def one(number,binding):
    expected,names,exe,status,engine,controller=binding;registry=[]
    required,_=extended_scope(expected,exe,engine,controller)
    def scope(current,current_exe):
        require(current==expected and current_exe==exe,'ORIGINAL_BASELINE')
        return extended_scope(current,current_exe,engine,controller)
    def write(row,stream,**kw):
        if row.get('schema_version')==v.SCHEMA:
            row.update(supplemental_scheduler_input_pins=list(engine.values()),
                runtime_resume_controller_input_pins=list(controller.values()),
                baseline_input_manifest_not_rewritten=True,serial_single_case_job=True,
                runtime_resume_publisher='P198',
                additional_sampler_or_foreign_PID_query=True,additional_sampler_thread_started=False)
            if registry:row['process_CPU_attribution']=attribution.summary(SimpleNamespace(windows=registry[0]))
            if row['state']==v.CASE_PASS:r.case_scope(row,expected,names,exe,engine,controller)
        return RAW_DUMP(row,stream,**kw)
    with patch.object(core,'DIR',DIR),patch.object(core,'runtime_scope',scope), \
            patch.object(v.observed.observer,'windows_type',lambda base:tracked_windows_type(base,registry)), \
            patch.object(json,'dump',write):
        return core.run_case(number,(expected,names,exe,status))


def close(number,binding,source):
    expected,names,exe,status,engine,controller=binding
    destination=b.s.scoped_path(target('close',number,status['next_index'],status['next_attempt']),fresh=True)
    context=r.observation.Context();owner=attribution.Resources(context);q=None;started=time.monotonic()
    out=dict(schema_version=r.SCHEMA,state='FAILED_NOT_ACCEPTED',**r.flags())
    try:
        owner.admit();q=r.Reader(owner,context)
        require(controllers(q)==controller,'CLOSING_EXECUTION_CONTROLLERS_UNCHANGED')
        require(source==f"{DIR}/p190-case-{status['next_index']:03}-attempt-{status['next_attempt']:03}.json",'EXACT_CASE_PATH')
        case=q.json(source);pin=q.reader.snapshots[source]
        require(case['selected_test_names']==[names[status['next_index']-1]],'EXACT_SELECTED_CASE')
        required,historical=r.case_scope(case,expected,names,exe,engine,controller)
        q.reader.protected=frozenset({exe['path']})
        for name,p in required.items():require(q.pin(name)==p,'FRESH_RUNTIME_SOURCE')
        q.finish();out.update(state=r.PASS,binding=v.identity(names,expected,exe),case_receipt_pin=pin,
            selected_test_name=case['selected_test_names'][0],pending_legacy_whole_closing_reference=case['closing_id'],
            runtime_source_before=list(required.values()),runtime_source_after=[q.reader.snapshots[n] for n in required],
            closing_controller_before=list(controller.values()),closing_controller_after=[q.reader.snapshots[n] for n in controller],
            historical_EXE_boundary_count=len(historical),sealed_whole_before_anchor=b.BASE_CLOSE)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.run.original.closed_error(error)
    finally:
        b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
        if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        if out['state']==r.PASS:
            try:r.validate(out,case,pin,expected,names,exe,engine,controller)
            except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
                out.update(state='FAILED_NOT_ACCEPTED',error_code=b.run.original.closed_error(error))
        out.update(wall_seconds=round(time.monotonic()-started,4),metadata_observation=r.observation.summary(owner),
            process_CPU_attribution=attribution.summary(owner))
        with destination.open('x',encoding='utf-8') as stream:RAW_DUMP(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','wall_seconds')}),flush=True)
    return 0 if out['state']==r.PASS else 2


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','plan','actual'),required=True)
    ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT,'CWD');target('plan',args.run);core.run.original.require_scope(1200)
    binding=prepare(args.mode,args.run)
    if binding is None:return 2
    if args.mode!='actual':return 0
    print(json.dumps(dict(state='STARTING_ONE_UNEXECUTED_RUNTIME_CASE',index=binding[3]['next_index'])),flush=True)
    code,source=one(args.run,binding)
    if code:return code  # No automatic retry, closing, or next case after a stop.
    return close(args.run,binding,source)


if __name__=='__main__':
    sys.modules.setdefault('run_runtime_resumable_r07_case',sys.modules[__name__])
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,c.subprocess.SubprocessError) as error:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=b.run.original.closed_error(error))))
        raise SystemExit(2) from None
