"""Observe real inherited READY and EOF, never write the original product GO.

Startup observation is not the original 15-second Gate.write qualification.
Both that gate and the product10 clock stay untouched and unstarted.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback
from types import SimpleNamespace as NS

SELF='tools/p09/native011_readiness_inspection.py'
PINS=(
    dict(path='tools/p09/batch_worker_launch.py',bytes=13040,sha256='a643b9c1fc1cf570e688e4e8d34ef2ff38e4277aecdc96ecdd6505be45b0c02f'),
    dict(path='tools/p09/native009_worker_launch_v1.py',bytes=4057,sha256='30088c308a7294dec10c295bcaba1d396382a7194541e5e21bd599dc03762f4b'),
    dict(path='tools/p09/worker_readiness_v1.py',bytes=6890,sha256='047c3f78f8a4472feeec4d56b65716f57e0429091321cb49afe5b685047d3a45'),
    dict(path='tools/p09/worker_readiness_connection_v1.py',bytes=5775,sha256='d306d62a08e16f717bb526b2a7fa6c60ac44890f6fed965fdf4a70daca3c0a9b'),
    dict(path='tools/p09/strict_product_window_v1.py',bytes=4696,sha256='cd35710cbd11e47cc0a83dd2f28c03772b86267713d52bb8129ed52c670cc701'),
    dict(path='tools/p09/post_product_recovery_window_v1.py',bytes=12876,sha256='ce0dd3fdddc238dd7181d5c12c0a161a2dea74c791dc8053dd99a2b0ca7e8890'))


def main():
    sys.dont_write_bytecode=True
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    args=parser.parse_args()
    if not 1<=args.attempt<=8:raise ValueError('NATIVE011_READY_BOUNDED_ATTEMPT')
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import runtime_envelope_namespace_bundle_v1 as loader,native011_ready_worker as worker
    import successor_preparation_workspace_v1 as publisher
    from bounded_process_progress import BoundedProcessCapture
    host.configure_host_policy(c)
    guard=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    output=f'implementation/p09/evidence/p09-361-native011-physical-readiness-attempt{args.attempt:03}.v1.json'
    started=time.monotonic();q=None;job=process=capture=binding=None;assigned=False;raw_pipe=None
    row=dict(state='FAILED_NATIVE011_PHYSICAL_EVENT_EOF_NOT_GATE15_OR_NATIVE',GO_authorized=False,
        actual_product_GO_writes=0,product_created=False,accepted_count_delta=0,
        original_Gate_write15_qualified=False,Native_Frame_or_dispatch_qualified=False,
        prior_suites_reexecuted=False)
    launches=[]
    def audit(event,arguments):
        if event=='subprocess.Popen':
            command=arguments[1]
            c.require(len(launches)==1 and (command==launches[0]
                or type(command) is str and command==subprocess.list2cmdline(launches[0])),
                'NATIVE011_READY_ONLY_DECLARED_WORKER_PROCESS')
        elif event in ('os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            raise ValueError('NATIVE011_READY_OTHER_PROCESS_DENIED')
    sys.addaudithook(audit)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        c.require(not (c.ROOT/output).exists() and not (c.ROOT/worker.RESULT).exists(),
            'NATIVE011_READY_NEW_PARENT_AND_WORKER_RESULTS')
        for name in (SELF,worker.SELF,loader.SELF):q.pin(name)
        for pin in PINS:a.exact(q.pin(pin['path']),pin,'NATIVE011_READY_UNCHANGED_ORIGINAL_COMPONENT_SOURCE')
        libs,_=loader.load(c.ROOT,list(PINS),{})
        protocol=libs.worker_readiness_v1;connection=libs.worker_readiness_connection_v1
        window=libs.strict_product_window_v1;tool=libs.post_product_recovery_window_v1
        actual,raw=q._read(tool.WINDOW_PIN['path'],parse=True);q._bind(actual['path'],actual)
        a.exact(actual,tool.WINDOW_PIN,'NATIVE011_READY_ORIGINAL_PRODUCT_WINDOW_SOURCE')
        component=tool.tighten_window(window,bytes(raw))
        launch=libs.batch_worker_launch.family(libs.native009_worker_launch_v1,
            dict(ENTRY=worker.SELF,TASK=worker.TASK))
        job=guard.windows.job();row['owned_limits']=guard.windows.verify_job_limits(job)
        c.require(row['owned_limits']['verified'],'NATIVE011_READY_JOB_LIMIT_READBACK')
        def factory(command,**options):
            nonlocal raw_pipe,process
            c.require(not launches and command[:3]==[sys.executable,'-B',str(c.ROOT/worker.SELF)]
                and len(command)==7 and command[3]=='--ready-handle' and command[5:]==['--task',worker.TASK],
                'NATIVE011_READY_ONE_EXACT_FIXED_COMMAND')
            launches.append(list(command))
            process=subprocess.Popen(command,**options);raw_pipe=process.stdin
            return process
        def owned(actual):return launch.same_owned_job(guard.windows,job,process,actual)
        binding=launch.connect(c.ROOT,q.snapshots[worker.SELF],component,protocol,connection,
            factory,BoundedProcessCapture,subprocess,owned,guard.check)
        command=[sys.executable,str(c.ROOT/'tools/p09/current_queue_successor_runtime.py'),
            '--owned-worker','--task',worker.TASK]
        spawn_start=time.monotonic()
        process=binding.Popen(command,cwd=c.ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW)
        c.require(guard.windows.k.AssignProcessToJobObject(job,int(process._handle)),
            'NATIVE011_READY_ASSIGN_EXACT_JOB_BEFORE_PREPARATION')
        assigned=True;c.require(owned(process),'NATIVE011_READY_SAME_JOB_BEFORE_START_TOKEN')
        # This separate bootstrap token cannot reach the original product
        # reader. Its raw one-byte consumer runs before any heavy preparation.
        c.require(raw_pipe.write(worker.START)==len(worker.START),'NATIVE011_READY_COMPLETE_PREPARATION_START')
        raw_pipe.flush()
        row['separate_preparation_start_writes']=1
        observed_start=time.monotonic()
        c.require(len(binding.events)==len(binding.gates)==1 and not binding.launch_state.postspawn_inheritance_error,
            'NATIVE011_READY_SINGLE_REAL_INHERITED_EVENT')
        while True:
            guard.check();c.require(time.monotonic()-observed_start<120,'NATIVE011_READY_READONLY_STARTUP_OBSERVATION120')
            c.require(process.poll() is None and owned(process),'NATIVE011_READY_SAME_LIVE_JOB_BEFORE_EVENT')
            if binding.events[0].wait(50):break
        guard.check();c.require(process.poll() is None and owned(process),'NATIVE011_READY_SAME_LIVE_JOB_AFTER_EVENT')
        row.update(actual_inherited_event_observed=True,start_token_to_READY_seconds=time.monotonic()-observed_start,
            spawn_to_READY_seconds=time.monotonic()-spawn_start,spawn_smoke15_passed=time.monotonic()-spawn_start<15,
            original_gate_readiness_seconds=protocol.SECONDS,product_window_seconds=component.SECONDS,
            startup_observation_is_not_Gate15_qualification=True)
        c.require(binding.state.started is None and binding.state.go_writes==0,'NATIVE011_READY_ORIGINAL_PRODUCT_CLOCK_UNSTARTED')
        process.stdin.close();capture=BoundedProcessCapture(process,output_limit=16384,parse_markers=False)
        deadline=time.monotonic()+2
        while True:
            guard.check();c.require(time.monotonic()<deadline,'NATIVE011_READY_ORIGINAL_EOF_CAPTURE2')
            try:stdout,stderr=capture.communicate(.1);break
            except subprocess.TimeoutExpired:capture.progress()
        c.require(process.returncode==1 and stdout=='' and len(stderr)<=16384,'NATIVE011_READY_ORIGINAL_EOF_EXIT')
        terminal=json.loads(stderr)
        a.fields(terminal,dict(terminal='WORKER_NOT_AUTHORIZED',task=worker.TASK,descriptor_count=162,
            actual_worker_attempts=1,actual_worker_calls=1,raw_policy_restored=True,
            source_step_pin_checked_before_after=True,actual_EOF_reads=1,process_creation_attempts=0,
            actual_product_GO_received=False),'NATIVE011_READY_ORIGINAL_EOF_TERMINAL')
        receipt=a.read_exact(q,terminal['preparation_receipt_pin'])
        a.fields(receipt,dict(state='PASS_ORIGINAL_INHERITED_EVENT_EOF_WORKER_NOT_PRODUCT',actual_EOF_reads=1,
            process_creation_attempts=0,actual_product_GO_received=False),'NATIVE011_READY_MEASURED_WORKER_RECEIPT')
        c.require(receipt['fresh_inputs']==receipt['final_fresh_hashes'] and receipt['preparation']['default_helper_count']<=64,
            'NATIVE011_READY_CHILD_PREPARATION_CLOSING_AND_HELPER64')
        for name in (worker.SELF,'tools/p09/native011_worker_preparation.py'):
            expected=next(pin for pin in receipt['source_pins'] if pin['path']==name)
            a.exact(q.pin(name),expected,'NATIVE011_READY_SHARED_ENTRY_SOURCE_IDENTITY')
        for pin in receipt['preparation']['published_pins']:a.exact(q.pin(pin['path']),pin,'NATIVE011_READY_SAME_UNREBUILT_PACKAGE')
        q.finish();guard.check(force=True)
        row.update(state='PASS_NATIVE011_PHYSICAL_INHERITED_EVENT_AND_ORIGINAL_EOF_NOT_GATE15_OR_NATIVE',
            child_receipt_pin=terminal['preparation_receipt_pin'],child_fresh_inputs=receipt['fresh_inputs'],
            child_final_hashes=receipt['final_fresh_hashes'],child_default_helper_count=receipt['preparation']['default_helper_count'],
            actual_worker_calls=1,actual_product_calls=0,raw_policy_restored=True,
            original_launch_and_ReadyReader_code_retained=True,
            original_binding_diagnostics=binding.state.diagnostics(),existing_package_republished=False)
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,MemoryError,NameError,ImportError,subprocess.SubprocessError) as error:
        row['error_type']=type(error).__name__
        row['error_code']=error.args[0] if error.args and type(error.args[0]) is str and re.fullmatch(
            '[A-Za-z0-9_]{1,160}',error.args[0]) else 'CLOSED_READINESS_OBSERVATION_FAILURE'
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-5:]]
    finally:
        cleanup=dict(active_processes=None,job_handle_closed=job is None)
        try:
            if job is not None:
                if process is not None and process.poll() is None:
                    if assigned:c.require(guard.windows.k.TerminateJobObject(job,1),'NATIVE011_READY_OWNED_READONLY_STOP')
                    else:process.terminate()
                if process is not None:process.wait(timeout=2)
                last=guard.windows.accounting(job);cleanup.update(last)
                c.require(last['active_processes']==0,'NATIVE011_READY_EMPTY_OWNED_JOB')
            if capture is not None:capture.close()
            elif process is not None:
                for pipe in (process.stdin,process.stdout,process.stderr):pipe.close()
            if binding is not None:
                for event in binding.events:event.close()
        finally:
            if job is not None:cleanup['job_handle_closed']=bool(guard.windows.k.CloseHandle(job))
            guard.close()
        row.update(cleanup=cleanup,cleanup_confirmed=guard.cleanup and cleanup['job_handle_closed']
            and cleanup['active_processes'] in (None,0),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=guard.samples,
            elapsed_seconds=time.monotonic()-started)
        if not row['cleanup_confirmed']:row['state']='FAILED_NATIVE011_READINESS_CLEANUP'
        pin=publisher.publish(c.ROOT,output,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),error_frames=row.get('error_frames'),
            cleanup=row['cleanup_confirmed'],fresh=row['fresh_inputs'],final=row['final_fresh_hashes'],
            elapsed=row['elapsed_seconds'],ready_seconds=row.get('start_token_to_READY_seconds'),
            spawn_smoke15_passed=row.get('spawn_smoke15_passed'),job=cleanup,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            RAM_available_min=min((s['available_ram_percent'] for s in guard.samples),default=None),receipt=pin)),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup_confirmed'] else 2


if __name__=='__main__':raise SystemExit(main())
