"""One closed readonly parent-oracle diagnostic, never a product dispatcher.

Keep the first failure even if cleanup also fails. Never reacquire a stopped
guard, replay the child, or replace missing closing bytes with a PASS. Poll
this one process handle; do not run sibling shell queries during inspection.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS

SELF='tools/p09/native011_owned_preparation.py'
BASELINE=dict(path='implementation/p09/evidence/p09-361-native011-parent-plan-owned102.v1.json',
    bytes=110227,sha256='13d25087c845808b143267895fae566beed10e735abdd695835f2c848fe10550')
TARGET='tools/p09/native011_parent_plan.py'


def require(ok,code):
    if not ok:raise ValueError('NATIVE011_OWNED_PREPARATION_'+code)


def failure_record(error,samples):
    value=error.args[0] if error.args else None
    code=value if type(value) is str and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_READONLY_FAILURE'
    row=samples[-1] if samples else {}
    ram=row.get('available_ram_percent');commit=row.get('commit_used_percent');cpu=row.get('system_cpu_percent')
    memory=(type(ram) in (int,float) and ram<5) or (type(commit) in (int,float) and commit>=95)
    cause='SYSTEM_MEMORY_PRESSURE' if memory else 'SYSTEM_CPU_IMMEDIATE' if type(cpu) in (int,float) and cpu>=90 else 'ORIGINAL_FAILURE_CODE'
    return dict(error_type=type(error).__name__,first_error_code=code,observed_resource_condition=cause,
        last_available_RAM_percent=ram,last_commit_used_percent=commit,last_system_CPU_percent=cpu,
        resource_condition_not_process_attribution=True)


def cleanup_owned(owned,capture,result,primary):
    """Release the known owned helper; never mask a preceding failure."""
    failures=[]
    calls=[]
    if owned is not None:calls.extend((owned.kill,lambda:owned.wait(timeout=2)))
    if capture is not None:calls.append(capture.close)
    if owned is not None:calls.append(owned.close)
    for call in calls:
        try:call()
        except (ValueError,OSError,subprocess.SubprocessError) as error:failures.append(error)
    result['cleanup_errors']=[failure_record(error,[]) for error in failures]
    if owned is not None:
        result['owned_job']=owned.profile
        result['cleanup']=not failures and owned.profile.get('cleanup_confirmed') is True
        result['stage']='TERMINAL_OWNED_JOB_CLEANED' if result['cleanup'] else 'TERMINAL_CLEANUP_UNCONFIRMED'
    elif not result['constructor_entered']:
        result.update(cleanup=not failures,stop_before_process_creation=True,stage='TERMINAL_BEFORE_PROCESS_CREATION')
    else:result.update(cleanup=False,stage='TERMINAL_PARTIAL_CONSTRUCTOR_UNCONFIRMED')
    if primary is None and failures:raise failures[0]


def run_once(command,guard,env,peak,result):
    from owned_sql_job import OwnedSQLJobProcess
    from bounded_process_progress import BoundedProcessCapture
    owned=capture=None;primary=None;started=time.monotonic()
    result.update(constructor_entered=False,cleanup=False,stage='FRESH_RESOURCE_ADMISSION')
    try:
        guard.check(force=True);sample=guard.samples[-1]
        room=sample['available_ram_mib']-.05*sample['total_ram_mib']
        result['launch_admission']=dict(headroom_mib=room,prior_measured_job_peak_mib=peak,
            admitted=room>=peak,actual_sample=dict(sample))
        require(room>=peak,'MEASURED_HEADROOM_STOP_BEFORE_CHILD')
        result['constructor_entered']=True
        owned=OwnedSQLJobProcess(command,windows=guard.windows,allowed_executables=[sys.executable],
            cwd=Path(__file__).resolve().parents[2],checkpoint=guard.check,env=env)
        capture=BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        result['stage']='ONE_LIVE_OWNED_READONLY_CHILD';deadline=time.monotonic()+120;announcement=time.monotonic()
        while True:
            guard.check();require(time.monotonic()<deadline,'READONLY_CHILD120_DEADLINE')
            try:output,errors=capture.communicate(timeout=.5)
            except subprocess.TimeoutExpired:
                capture.progress();owned.observe()
                if time.monotonic()-announcement>=15:
                    sample=guard.samples[-1]
                    print(json.dumps(dict(stage=result['stage'],elapsed=time.monotonic()-started,
                        system_CPU=sample['system_cpu_percent'],available_RAM_percent=sample['available_ram_percent'])),flush=True)
                    announcement=time.monotonic()
                continue
            owned.observe();result.update(exit_code=owned.returncode,
                stdout_bytes=len(output.encode()),stderr_bytes=len(errors.encode()),
                stdout_sha256=hashlib.sha256(output.encode()).hexdigest(),stderr_sha256=hashlib.sha256(errors.encode()).hexdigest())
            if output.splitlines():result['child_summary']=json.loads(output.splitlines()[-1])
            require(owned.returncode==0,'READONLY_CHILD_FAILED_NO_RETRY')
            return result['child_summary']
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        primary=error;result['first_failure']=failure_record(error,guard.samples);raise
    finally:
        cleanup_owned(owned,capture,result,primary)
        result['elapsed_seconds']=time.monotonic()-started


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    parser.add_argument('--shared',action='store_true');parser.add_argument('--metadata-generation',type=int)
    args=parser.parse_args();require(1<=args.attempt<=8,'CLOSED_SINGLE_DIAGNOSTIC_ATTEMPT')
    require((args.metadata_generation is not None)==args.shared,'EXACT_SHARED_REPORT_MODE')
    if args.shared:require(1<=args.metadata_generation<=8,'BOUNDED_METADATA_REPORT_GENERATION')
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import successor_preparation_workspace_v1 as publisher
    host.configure_host_policy(c)
    guard=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    output=f'implementation/p09/evidence/p09-361-native011-owned-preparation-attempt{args.attempt:03}.v1.json'
    row=dict(state='FAILED_NATIVE011_OWNED_READONLY_PREPARATION_NOT_NATIVE',official_accepted_count=158,
        accepted_count_delta=0,GO_authorized=False,owned={},automatic_retry=False)
    q=None;started=time.monotonic()
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        require(not (c.ROOT/output).exists(),'EXCLUSIVE_NEW_DIAGNOSTIC_RECEIPT')
        for name in (SELF,TARGET,'tools/p09/native011_parent_oracle.py','tools/p09/owned_sql_job.py',
            'tools/p09/bounded_process_progress.py','tools/p09/prepared_run_closure_v1.py',
            'tools/p09/owned_cpu_baseline_v1.py','tools/p09/preparation_attributed_cpu_v1.py',
            'tools/p09/distinct_final_sample_guard_v1.py'):q.pin(name)
        if args.shared:
            for name in ('tools/p09/native011_shared_parent.py','tools/p09/native011_metadata_report.py'):q.pin(name)
        prior=a.read_exact(q,BASELINE)
        require(prior['cleanup'] and prior['state']=='PASS_OWNED_REAL_NATIVE011_UNOPENED_PLAN_AND_PARENT_NOT_NATIVE',
            'MEASURED_BASELINE_NOT_NATIVE_AUTHORITY')
        peak=prior['steps'][0]['owned_job']['last_job_accounting']['peak_job_private_mib']
        require(type(peak) in (int,float) and peak==83.47,'EXACT_MEASURED_BASELINE_PEAK')
        command=[sys.executable,'-B',str(c.ROOT/TARGET),'--attempt',str(args.attempt),'--inspect-oracle']
        if args.shared:command+=['--inspect-shared','--metadata-generation',str(args.metadata_generation)]
        guard.close()
        # Deliberately no failed-run finally: guard.acquire(). That used to
        # overwrite the first RAM failure with PREPARATION_CPU_STOP_LATCHED.
        child=run_once(command,guard,dict(os.environ),peak,row['owned'])
        guard.acquire()  # Success only, after verified cleanup of this child.
        require(row['owned']['cleanup'] and child['cleanup'],'KNOWN_EMPTY_OWNED_TREE')
        proof=a.read_exact(q,child['receipt'])
        expected='PASS_REAL_NATIVE011_SHARED_METADATA_CALLBACK_CONSTRUCTION_NOT_NATIVE' if args.shared else 'PASS_REAL_NATIVE011_PARENT_ORACLE_AND_DECLARED_BUDGET_NOT_NATIVE'
        require(proof['state']==expected
            and proof['fresh_inputs']==proof['final_fresh_hashes'] and proof['process_creation_attempts']==0
            and proof['parent_attempts']==proof['Frame_instances']==proof['worker_attempts']==proof['worker_calls']==0
            and proof['independent_checker_connected'],'ACTUAL_READONLY_CONNECTION_NOT_CANDIDATE_PASS')
        if args.shared:
            shared=proof['shared_parent_connection']
            require(shared['actual_metadata_callback_bound'] and shared['original_preaudit_denial_before_metadata_IO']
                and not shared['metadata_body_executed'] and shared['metadata_reader_instances']==shared['Frame_instances']==0
                and proof['shared_budget_restored'],'ACTUAL_SHARED_CONNECTION_NO_METADATA_BODY_OR_FRAME')
        # Retain the former parent source comparison; no runtime IO exemption.
        for pin in proof['source_pins']:a.exact(q.pin(pin['path']),pin,'POST_CHILD_CONSTRUCTION_SOURCE_CHECK')
        q.finish();guard.check(force=True)
        row.update(state='PASS_NATIVE011_OWNED_PARENT_ORACLE_DECLARED_COST_NOT_NATIVE',
            child_receipt=child['receipt'],oracle_construction=proof['oracle_construction'],
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_Native_Frame_or_product_qualified=False)
        if args.shared:row.update(state='PASS_NATIVE011_OWNED_SHARED_METADATA_CALLBACK_CONSTRUCTION_NOT_NATIVE',
            shared_parent_connection=proof['shared_parent_connection'],partition=proof['partition'])
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        row['failure']=failure_record(error,guard.samples)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and row['owned'].get('cleanup',True),
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=guard.samples,
            elapsed_seconds=time.monotonic()-started)
        receipt=publisher.publish(c.ROOT,output,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],failure=row.get('failure'),cleanup=row['cleanup'],
            owned_stage=row['owned'].get('stage'),fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),
            elapsed=row['elapsed_seconds'],receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__=='__main__':raise SystemExit(main())
