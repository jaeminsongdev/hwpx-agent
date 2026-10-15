"""Production entry/launch diagnostics; product Popen permanently denied.

Serial owned Jobs only. The external diagnostic audit surrounds the unchanged
production __main__; no denial or diagnostic GO bypass is added to production.
"""
import json
import sys
from pathlib import Path

SELF='tools/p09/qualify_native009_worker_launch_v1.py'
LAUNCH='tools/p09/native009_worker_launch_v1.py'
ENTRY='tools/p09/native009_worker_entry_v1.py'
TEST='tools/p09/tests/test_native009_worker_launch_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
CONSTRUCTION=dict(path='tools/p09/native009_full72_construction_v1.py',bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
QUALIFIED=dict(path=PREFIX+'native009-full72-construction003.v1.json',bytes=82460,
    sha256='f4593cd202f7e7ef146f1615d4cd6a34d26261d8743322536301180a1e3bf27a')
READINESS=[dict(path='tools/p09/worker_readiness_v1.py',bytes=6890,
    sha256='047c3f78f8a4472feeec4d56b65716f57e0429091321cb49afe5b685047d3a45'),
 dict(path='tools/p09/worker_readiness_connection_v1.py',bytes=5775,
    sha256='d306d62a08e16f717bb526b2a7fa6c60ac44890f6fed965fdf4a70daca3c0a9b')]

# Fixed external harness: denies ALL product/process creation before OS entry,
# records only closed booleans/counts, and executes the actual production CLI.
DIAGNOSTIC='''import sys,runpy,json,subprocess
from pathlib import Path
entry=sys.argv[1];expected=json.loads(sys.argv[2]);root=Path(entry).parents[2]
prefix='implementation/p09/evidence/p09-361-case165-'
allowed={str(root/(prefix+n)).replace('\\\\','/') for n in ('successor-worker-bootstrap009.v3.json','successor-worker-capsule009.compact.v3.json','step-config001.v1.json')}
seen=dict(product_popen_calls=0,exact_product_command=None,other_JSON_opens=0,step_JSON_reads=0)
def audit(event,args):
    if event=='subprocess.Popen':
        seen['product_popen_calls']+=1
        seen['exact_product_command']=args[1] in (expected,subprocess.list2cmdline(expected))
        raise ValueError('DIAG_SUBPROCESS_DENIED')
    if event=='open' and args and isinstance(args[0],str) and args[0].lower().endswith('.json'):
        name=args[0].replace('\\\\','/')
        if name.endswith('p09-361-case165-step-config001.v1.json'):seen['step_JSON_reads']+=1
        if name not in allowed:
            seen['other_JSON_opens']+=1;raise ValueError('DIAG_OTHER_JSON_OPEN_DENIED')
sys.addaudithook(audit);sys.argv=[entry,*sys.argv[3:]]
try:runpy.run_path(entry,run_name='__main__')
finally:print(json.dumps(dict(diagnostic_audit=seen,all_subprocess_denied_before_OS_create=True)),file=sys.stderr)
'''


def require(ok,label):
    if not ok:raise ValueError('NATIVE009_LAUNCH_QUAL_'+label)


def main():
    import argparse,ctypes,importlib.util,io,re,subprocess,time,traceback,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    from bounded_process_progress import BoundedProcessCapture
    bootstrap,_=envelope.namespace_bundle.load(c.ROOT,[CONSTRUCTION],{})
    construction=bootstrap.native009_full72_construction_v1
    libs,_=envelope.namespace_bundle.load(c.ROOT,construction.PINS+READINESS,{})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader,_=libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle,libs.ast_clone_namespace_v1)
    protocol=libs.worker_readiness_v1;connection=libs.worker_readiness_connection_v1
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);attempt=parser.parse_args().attempt
    require(type(attempt) is int and 1<=attempt<=8,'BOUNDED_ATTEMPT')
    output=PREFIX+f'native009-production-worker-launch{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists(),'EXCLUSIVE_REPORT')
    require(not(c.ROOT/(PREFIX+'current-runtime-run009.v1.json')).exists(),'NO_NATIVE009')
    Guard=libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))
    guard=Guard();started=time.monotonic();phase='CURRENT_SOURCE_ADMISSION'
    row=dict(state='FAILED_PRODUCTION_WORKER9_LAUNCH_NOT_NATIVE',accepted_count_delta=0,GO_authorized=False,
        actual_product_or_Native_executed=False,whole_Native_parent_integration_or_dispatch_qualified=False,
        previous_Native_replayed=False,new_source_and_result_cost_recalculation_required=True,cases=[])
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,LAUNCH,ENTRY,TEST):q.pin(name)
        for pin in [CONSTRUCTION]+construction.PINS+READINESS:a.exact(q.pin(pin['path']),pin,'FRESH_PROGRAM_PINS')
        prior=a.read_exact(q,QUALIFIED)
        a.fields(prior,dict(state='PASS_FULL72_PARENT_FRAME_CLASS_OUTER_AND_INDEPENDENT_ORACLE8_NOT_NATIVE',
            contracts=dict(run=8,errors=0,failures=0,skipped=0),fresh_inputs=374,final_fresh_hashes=374,cleanup_confirmed=True,
            actual_worker_calls=0,actual_Frame_instances=0),'CURRENT_CONSTRUCTION8')
        for pin in prior['source_pins']:
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
                a.exact(q.pin(pin['path']),pin,'CURRENT_INHERITED_CODE_NOT_NATIVE_SOURCE_PASS')
        names,_=loader.load(c.ROOT,[q.snapshots[LAUNCH],q.snapshots[ENTRY]],{})
        launch=names.native009_worker_launch_v1;entry=names.native009_worker_entry_v1
        for pin in (entry.HINT,entry.WIRE,entry.STEP):a.exact(q.pin(pin['path']),pin,'EXACT_CURRENT_WORKER_PACKET')
        raw=q.text(libs.post_product_recovery_window_v1.WINDOW_PIN['path']).encode('utf-8')
        component=libs.post_product_recovery_window_v1.tighten_window(envelope.prior.WINDOW,raw)
        phase='CLOSED_LAUNCH_CONTRACTS'
        spec=importlib.util.spec_from_file_location('native009_worker_launch_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        tests.MODULE=launch;tests.PROTOCOL=protocol;tests.CONNECTION=connection;tests.WINDOW=component
        tests.ENTRY=entry;tests.ROOT=c.ROOT;tests.PIN=q.snapshots[ENTRY]
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=12,errors=0,failures=0,skipped=0),'ALL_LAUNCH12')
        for mode in ('EOF','GO_DENIED'):
            phase='ACTUAL_PRODUCTION_MAIN_'+mode;guard.check(force=True)
            windows=c.Windows();job=windows.job();process=capture=api=None;assigned=False;terminal=None;details=None
            begin=time.monotonic()
            try:
                limits=windows.verify_job_limits(job)
                expected=[str(c.ROOT/scope.EXE_PIN['path']),q.json(entry.HINT['path'])['step']['case'],'--exact','--test-threads=1','--format=pretty','--color=never']
                def diagnostic_factory(command,**kwargs):
                    # The adapter requested the exact production command. Only
                    # this diagnostic factory adds the permanently-denying audit.
                    require(command[:3]==[sys.executable,'-B',str(c.ROOT/ENTRY)],'UNCHANGED_PRODUCTION_COMMAND_AT_DIAGNOSTIC_BOUNDARY')
                    return subprocess.Popen([sys.executable,'-B','-c',DIAGNOSTIC,command[2],json.dumps(expected),*command[3:]],**kwargs)
                def owned(actual):return launch.same_owned_job(windows,job,process,actual)
                api=launch.connect(c.ROOT,q.snapshots[ENTRY],component,protocol,connection,diagnostic_factory,
                    BoundedProcessCapture,subprocess,owned,guard.check)
                command=[sys.executable,str(c.ROOT/'tools/p09/current_queue_successor_runtime.py'),'--owned-worker','--task',launch.TASK]
                process=api.Popen(command,cwd=c.ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                    creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW)
                handle=windows.k.OpenProcess(0x101,False,process.pid)
                try:require(handle and windows.k.AssignProcessToJobObject(job,handle),'ORIGINAL_JOB_ASSIGN');assigned=True
                finally:
                    if handle:require(windows.k.CloseHandle(handle),'PROCESS_HANDLE_CLOSE')
                if mode=='EOF':process.stdin.close();capture=BoundedProcessCapture(process)
                else:process.stdin.write(protocol.GO);process.stdin.flush();capture=api.Capture(process)
                deadline=time.monotonic()+15
                while True:
                    guard.check();require(time.monotonic()<deadline,'CHILD_CAPTURE_BOUND')
                    try:stdout,stderr=capture.communicate(.1);break
                    except subprocess.TimeoutExpired:capture.progress()
                lines=stderr.splitlines()
                require(len(lines)==2 and all(len(line)<=4096 for line in lines),'ONLY_CLOSED_CHILD_METADATA')
                details=json.loads(lines[0]);audit=json.loads(lines[1])
                a.fields(details,dict(terminal='WORKER_NOT_AUTHORIZED' if mode=='EOF' else 'NATIVE009_WORKER_EXECUTION_FAILED',
                    task=launch.TASK,descriptor_count=72,actual_worker_attempts=1,actual_worker_calls=1,raw_policy_restored=True,
                    original_worker_code='run_case112_current_stored.py',source_step_pin_checked_before_after=True,
                    Native_source_Frame_or_acceptance_qualified=False),'ORIGINAL_FULL72_PRODUCTION_WORKER_MAIN')
                a.exact(audit,dict(diagnostic_audit=dict(product_popen_calls=0 if mode=='EOF' else 1,
                    exact_product_command=None if mode=='EOF' else True,other_JSON_opens=0,step_JSON_reads=3),
                    all_subprocess_denied_before_OS_create=True),'PERMANENT_EXTERNAL_AUDIT_NOT_PRODUCT_EXECUTION')
                require(type(details['child_default_project_helper_count']) is int and details['child_default_project_helper_count']<=64,'ACTUAL_CHILD_HELPER64')
                require(process.returncode==1 and stdout=='','ORIGINAL_DIAGNOSTIC_EXIT')
            finally:
                require(windows.k.TerminateJobObject(job,1),'OWNED_JOB_TERMINATE')
                if process is not None:
                    if not assigned and process.poll() is None:process.terminate()
                    process.wait(timeout=2)
                if capture is not None:capture.close()
                elif process is not None:
                    for stream in (process.stdin,process.stdout,process.stderr):stream.close()
                until=time.monotonic()+2
                while True:
                    terminal=windows.accounting(job)
                    if terminal['active_processes']==0:break
                    require(time.monotonic()<until,'OWNED_JOB_EMPTY_BOUND');time.sleep(.02)
                require(windows.k.CloseHandle(job),'OWNED_JOB_CLOSE')
                if api is not None:
                    for event in api.events:event.close()
                row['last_owned_cleanup']=dict(active_after_cleanup=terminal['active_processes'],Job_CPU_seconds=terminal['job_cpu_seconds'],
                    Job_peak_private_MiB=terminal['peak_job_private_mib'],job_handle_closed=True)
            row['cases'].append(dict(mode=mode,child_terminal=details,diagnostic_audit=audit,window=api.state.diagnostics(),
                owned_limits_readback=limits,active_after_cleanup=terminal['active_processes'],cleanup_confirmed=True,
                elapsed_seconds=time.monotonic()-begin,Job_CPU_seconds=terminal['job_cpu_seconds'],Job_peak_private_MiB=terminal['peak_job_private_mib']))
        phase='FINAL_METADATA_HASHES'
        for loaded in tuple(sys.modules.values()):
            filename=getattr(loaded,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        q.finish();guard.check(force=True)
        require(not(c.ROOT/(PREFIX+'current-runtime-run009.v1.json')).exists(),'NATIVE009_STILL_ABSENT')
        row.update(state='PASS_PRODUCTION_WORKER9_MAIN_AND_LAUNCH12_EOF_AND_PRODUCT_DENIED_NOT_NATIVE',
            production_entry_and_launch_path_executed_only_inside_permanent_diagnostic_denial=True,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        row['error_type']=type(error).__name__;row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-5:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None))
    require(guard.cleanup,'OWNER_CLEANUP');libs.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','cases','fresh_inputs','final_fresh_hashes',
        'elapsed_seconds','CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed','operation_phase','error_code','error_frames')},allow_nan=False))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
