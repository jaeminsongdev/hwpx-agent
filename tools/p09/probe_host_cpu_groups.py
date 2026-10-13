"""Read-only PDH group diagnostic; reuse immutable existing owned30s Job probe."""
import argparse
from datetime import datetime,timezone
import io
import json
import math
import sys
import unittest
from unittest.mock import patch
import probe_host_cpu_observer as base
import host_cpu_group_observer as group

SELF='tools/p09/probe_host_cpu_groups.py'
FILES=(*base.FILES,SELF,'tools/p09/host_cpu_group_observer.py',
    'tools/p09/tests/test_host_cpu_groups.py')
PASS='PASS_NATIVE_HOST_CPU_GROUP_DIAGNOSTIC_ONLY_NOT_FULL249_OR_GATE'


def require(ok,code):group.require(ok,'PROBE_'+code)


def validate_payload(row):
    base.exact_keys(row,('schema_version','state','worker_pid','query_cleanup_confirmed','query_count','samples',
        'causal_attribution','raw_process_names_saved','commands_paths_saved'))
    require(row['schema_version']=='hwpx-agent.p09-host-cpu-observer-probe/v1' and row['state']=='PASS_TWO_NATIVE_SAMPLES_ONLY'
        and type(row['worker_pid']) is int and 1<=row['worker_pid']<=0xffffffff and row['query_cleanup_confirmed'] is True
        and type(row['query_count']) is int and row['query_count']==1 and row['causal_attribution'] is False
        and row['raw_process_names_saved'] is False and row['commands_paths_saved'] is False,'OUTPUT_SCOPE')
    require(type(row['samples']) is list and len(row['samples'])==2,'OUTPUT_SAMPLES');previous=None
    for index,sample in enumerate(row['samples']):
        base.exact_keys(sample,('sequence','observed_at','collect_seconds','observation'))
        require(type(sample['sequence']) is int and sample['sequence']==index+1,'SEQUENCE')
        require(type(sample['observed_at']) is str and len(sample['observed_at'])<=40,'TIMESTAMP')
        stamp=datetime.fromisoformat(sample['observed_at']);require(stamp.tzinfo==timezone.utc and (previous is None or stamp>previous),'TIMESTAMP');previous=stamp
        require(type(sample['collect_seconds']) in (float,int) and math.isfinite(sample['collect_seconds']) and 0<=sample['collect_seconds']<30,'COLLECT_SECONDS')
        snap=sample['observation'];base.exact_keys(snap,('processor_count','cpu_instance_count','pid_instance_count',
            'stable_candidate_count','stable_instance_count','unavailable_instances','unstable_instances',
            'ambiguous_instances','top','causal_attribution','counterset','duplicate_groups_explicit'))
        require(type(snap['processor_count']) is int and 1<=snap['processor_count']<=64 and snap['causal_attribution'] is False
            and snap['counterset']=='Process' and snap['duplicate_groups_explicit'] is True,'SNAPSHOT_SCOPE')
        for name in ('cpu_instance_count','pid_instance_count','stable_candidate_count','stable_instance_count',
                'unavailable_instances','unstable_instances','ambiguous_instances'):
            require(type(snap[name]) is int and 0<=snap[name]<=group.old.MAX_ITEMS,'INSTANCE_SCOPE')
        require(0<snap['stable_candidate_count']<=snap['stable_instance_count']<=snap['pid_instance_count']
            and snap['cpu_instance_count']>=snap['stable_instance_count']+snap['unavailable_instances']+snap['unstable_instances']
            and snap['ambiguous_instances']<=snap['stable_instance_count'],'INSTANCE_ACCOUNTING')
        require(type(snap['top']) is list and len(snap['top'])==min(group.old.TOP,snap['stable_candidate_count']),'TOP_BOUND')
        sortkeys=[]
        for item in snap['top']:
            base.exact_keys(item,('role','instance_count','pid','identity_granularity','owned_member_count',
                'processor_time_raw_percent','machine_cpu_percent'))
            require(item['role'] in group.old.ROLES and type(item['instance_count']) is int and 1<=item['instance_count']<=group.old.MAX_ITEMS,'ROLE_SCOPE')
            require(type(item['owned_member_count']) is int and 0<=item['owned_member_count']<=1,'OWNED_SCOPE')
            if item['instance_count']==1:
                require(item['identity_granularity']=='pid' and type(item['pid']) is int and 1<=item['pid']<=0xffffffff
                    and item['owned_member_count']==int(item['pid']==row['worker_pid']),'PID_SCOPE')
            else:require(item['identity_granularity']=='group' and item['pid'] is None,'NO_FAKE_PID')
            for name in ('processor_time_raw_percent','machine_cpu_percent'):
                require(type(item[name]) in (float,int) and math.isfinite(item[name]) and item[name]>=0,'CPU_SCOPE')
            require(math.isclose(item['machine_cpu_percent'],item['processor_time_raw_percent']/snap['processor_count'],rel_tol=1e-12,abs_tol=1e-12),'NORMALIZATION')
            sortkeys.append((-item['machine_cpu_percent'],item['role'],item['pid'] or 0))
        require(sortkeys==sorted(sortkeys),'TOP_ORDER')
    return row


def light(destination):
    base.c.Windows();before=base.fresh_pins();sys.path.insert(0,str(base.c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in ('test_host_cpu_observer','test_probe_host_cpu_observer','test_host_cpu_groups'))
    with patch('subprocess.Popen',side_effect=AssertionError('LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('LIGHT_THREAD_FORBIDDEN')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    failed=sorted({test.id().split('.')[-1] for test,_ in checked.failures+checked.errors+checked.skipped})
    after=base.fresh_pins();passed=checked.wasSuccessful() and checked.testsRun==40 and not checked.skipped and before==after
    row=dict(state='PASS_HOST_CPU_GROUP_CONTRACTS_ONLY_NOT_NATIVE_OR_GATE' if passed else 'FAILED_NOT_ACCEPTED',
        tests_run=checked.testsRun,tests_passed=checked.testsRun-len(failed),failed_tests=failed,bound_input_pins=after,
        source_closing_exact=before==after,actual_native_counter_run=False,product_complete=False,P09_gate='OPEN')
    with destination.open('x',encoding='utf-8') as stream:json.dump(row,stream,indent=2)
    print(json.dumps({k:row[k] for k in ('state','tests_run','tests_passed','failed_tests')}));return 0 if passed else 2


def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=('light','actual'),required=True);p.add_argument('--run',type=int,choices=range(1,100),required=True);args=p.parse_args()
    require(base.c.Path.cwd().resolve()==base.c.ROOT,'REPOSITORY_CWD');destination=base.c.ROOT/f'implementation/p09/evidence/p09-153-host-cpu-groups.{args.mode}-run{args.run:02}.v1.json'
    require(not destination.exists(),'FRESH_RECEIPT')
    with patch.object(base,'SELF',SELF),patch.object(base,'FILES',FILES),patch.object(base,'PASS',PASS):
        if args.mode=='light':return light(destination)
        with patch.object(base.observer,'Observer',group.Observer),patch.object(base,'validate_payload',validate_payload):return base.actual(args.run,destination)


if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:
            with patch.object(base.observer,'Observer',group.Observer),patch.object(base,'validate_payload',validate_payload):raise SystemExit(base.worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        code=str(error) if isinstance(error,ValueError) else ''
        print(code if base.re.fullmatch(r'P153_[A-Z_]{1,120}',code) else 'P153_REDACTED_NOT_ACCEPTED');raise SystemExit(2) from None
