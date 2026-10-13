"""P164 four real host polls with adaptive ONE native query in owned30s Job.

No product EXE/test body runs; original all249 acceptance remains unqualified.
"""
import argparse
from datetime import datetime,timezone
import io
import json
import os
import sys
import time
import unittest
from unittest.mock import patch
import adaptive_host_cpu_sampler as a
import probe_host_cpu_groups as native
import run_source_xml_product_full as full

base=native.base
SELF='tools/p09/probe_adaptive_host_cpu_sampler_r2.py'
TEST='tools/p09/tests/test_adaptive_host_cpu_sampler.py'
FILES=tuple(dict.fromkeys((*native.FILES,SELF,TEST,a.SELF)))
# Bind every imported local helper, not just the original minimal probe set.
# Explicit original test sources also remain bound; no tests run at import.
_scope=set(FILES)|{
    'tools/p09/tests/test_current_stored_full.py',
    'tools/p09/tests/test_compression_full_stored.py',
    'tools/p09/tests/test_observed_stored_full.py',
    'tools/p09/tests/test_current_graph_full.py',
    'tools/p09/tests/test_source_xml_product_full.py'}
for _module in tuple(sys.modules.values()):
    _file=getattr(_module,'__file__',None)
    if _file:
        _path=base.c.Path(_file).absolute()
        if _path.is_relative_to(base.c.ROOT/'tools/p09') and _path.suffix=='.py':
            _scope.add(_path.relative_to(base.c.ROOT).as_posix())
FILES=tuple(sorted(_scope))
POLLS=4
PASS='PASS_ADAPTIVE_NATIVE_QUERY_SCHEDULE_ONLY_NOT_FULL249_OR_GATE'

def require(ok,code):a.require(ok,'PROBE_'+code)

def pair_payload(worker,left,right):
    # Auxiliary schema adapter only: genuine timestamps/snapshots, sequence
    # renumbering only; no adapted pair is persisted as physical evidence.
    return dict(schema_version='hwpx-agent.p09-host-cpu-observer-probe/v1',state='PASS_TWO_NATIVE_SAMPLES_ONLY',
        worker_pid=worker,query_cleanup_confirmed=True,query_count=1,
        samples=[dict(left,sequence=1),dict(right,sequence=2)],causal_attribution=False,
        raw_process_names_saved=False,commands_paths_saved=False)

def validate_payload(row):
    require(type(row) is dict and set(row)=={'schema_version','state','worker_pid','query_cleanup_confirmed',
        'query_count','samples','host_polls','schedule','causal_attribution','raw_process_names_saved','commands_paths_saved'},'KEYS')
    require(row['schema_version']=='hwpx-agent.p09-adaptive-native-query-probe/v1'
        and row['state']=='PASS_FOUR_HOST_POLLS_ADAPTIVE_NATIVE_ONLY' and row['query_cleanup_confirmed'] is True
        and type(row['query_count']) is int and row['query_count']==1
        and row['causal_attribution'] is False and row['raw_process_names_saved'] is False
        and row['commands_paths_saved'] is False,'SCOPE')
    schedule=a.validate_schedule(row['schedule']);require(schedule['host_polls']==POLLS,'FOUR_POLLS')
    require(type(row['samples']) is list and len(row['samples'])==schedule['emitted_samples']<=POLLS,'SAMPLES')
    for index,sample in enumerate(row['samples']):
        require(sample['sequence']==index+1,'SEQUENCE')
        if index:native.validate_payload(pair_payload(row['worker_pid'],row['samples'][index-1],sample))
    require(type(row['host_polls']) is list and len(row['host_polls'])==POLLS,'HOST_POLLS')
    replay=a.Sampler();replay.initial_warm();previous=None
    for index,poll in enumerate(row['host_polls']):
        require(type(poll) is dict and set(poll)=={'sequence','observed_at','system_cpu_percent','action'}
            and poll['sequence']==index+1,'HOST_RECORD')
        stamp=datetime.fromisoformat(poll['observed_at'])
        require(stamp.tzinfo==timezone.utc and (previous is None or stamp>previous),'HOST_TIME');previous=stamp
        action,_=replay.poll(poll['system_cpu_percent'],lambda:'schema-replay-only')
        require(poll['action']==action,'REAL_HOST_POLICY_BINDING')
    require(replay.summary()==schedule,'REPLAY_ACCOUNTING')
    return row

def worker(task):
    require(task==base.task_for(1),'CLOSED_TASK')
    require(sys.stdin.readline()=='P149_GO\n','GO')
    windows=base.c.Windows();member=base.w.BOOL()
    require(windows.k.IsProcessInJob(windows.k.GetCurrentProcess(),None,base.ctypes.byref(member)) and member.value,'JOB_BEFORE_QUERY')
    observer=native.group.Observer(windows.processors);sampler=a.Sampler();saved=[];polls=[];closed=False
    try:
        require(observer.collect() is None,'INITIAL_WARM');sampler.initial_warm()
        for index in range(POLLS):
            time.sleep(1);host=windows.sample()['system_cpu_percent'];stamp=datetime.now(timezone.utc).isoformat()
            def collect():
                started=time.monotonic();snapshot=observer.collect((os.getpid(),));elapsed=time.monotonic()-started
                require(snapshot is not None and snapshot['stable_candidate_count']>0,'NATIVE_COLLECTION')
                sample=dict(sequence=len(saved)+1,observed_at=datetime.now(timezone.utc).isoformat(),
                    collect_seconds=elapsed,observation=snapshot)
                if saved:native.validate_payload(pair_payload(os.getpid(),saved[-1],sample))
                return sample
            action,sample=sampler.poll(host,collect)
            polls.append(dict(sequence=index+1,observed_at=stamp,system_cpu_percent=host,action=action))
            if action=='sample':saved.append(sample)
    finally:observer.close();closed=True
    row=dict(schema_version='hwpx-agent.p09-adaptive-native-query-probe/v1',
        state='PASS_FOUR_HOST_POLLS_ADAPTIVE_NATIVE_ONLY',worker_pid=os.getpid(),query_cleanup_confirmed=closed,
        query_count=1,samples=saved,host_polls=polls,schedule=sampler.summary(),causal_attribution=False,
        raw_process_names_saved=False,commands_paths_saved=False)
    validate_payload(row);encoded=json.dumps(row,separators=(',',':'))
    require(len(encoded.encode('utf-8'))<=16384,'ORIGINAL_PROBE_OUTPUT_BOUND')
    print(encoded);return 0

def contracts():
    full.contracts();sys.path.insert(0,str(base.c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n)
        for n in ('test_host_cpu_groups','test_adaptive_host_cpu_sampler'))
    with patch('subprocess.Popen',side_effect=AssertionError('P164_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P164_LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P164_LIGHT_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==29 and not result.skipped,'CONTRACT29_PLUS52')
    return dict(contract_tests_run=81,contract_tests_passed=81)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True);mode=parser.parse_args().mode
    require(base.c.Path.cwd().resolve()==base.c.ROOT,'CWD')
    destination=full.p.s.scoped_path(f'implementation/p09/evidence/p09-164-adaptive-native-query.{mode}-run02.v1.json',fresh=True)
    if mode=='light':
        resources=full.p.s.SQLRuntimeResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED')
        try:
            resources.admit();q=full.p.s.LiveSQLReader(resources)
            for n in FILES:q.pin(n)
            out.update(contracts());q.finish()
            out.update(state='PASS_ADAPTIVE_QUERY_CONTRACTS_ONLY_NOT_NATIVE_RUNTIME_OR_GATE',source_closing_exact=True,
                actual_native_counter_run=False,full249_current_qualified=False,signed16_current_qualified=False,
                product_complete=False,P09_gate='OPEN',PC_freeze_resolved=False)
        except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:out['error_code']=full.s.original.closed_error(e)
        finally:
            full.p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
            if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
            if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
            with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
            print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
        return 0 if out['state'].startswith('PASS_') else 2
    dump=json.dump
    def write(row,stream,**kw):
        row.update(schema_version='hwpx-agent.p09-adaptive-native-schedule/v1',actual_product_test_body_executed=False,
            full_product_performance_improvement_measured=False,host_CPU_cause_proven=False,
            adaptive_scope_host_polls=POLLS,original_owned_policy_unchanged=True,
            original_full249_1200_scope_unchanged=True,legacy_total_samples_counts_host_polls=True)
        return dump(row,stream,**kw)
    with patch.object(base,'SELF',SELF),patch.object(base,'FILES',FILES),patch.object(base,'PASS',PASS), \
            patch.object(base,'validate_payload',validate_payload),patch.object(json,'dump',write):
        return base.actual(1,destination)

if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,base.subprocess.SubprocessError) as e:
        print(full.s.original.closed_error(e));raise SystemExit(2) from None
