"""395: call-site audit fixes comment false-positive; actual source unchanged; compile/model+self only."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import crossref_existing_owner_test_runtime as worker

OUTPUT='implementation/p09/evidence/p09-361-crossref-existing-owner-recovery395.v1.json'
DRIVER='tools/p09/run_crossref_existing_owner_recovery.py'
CORE='implementation/p09/tools/crossref-existing-owner.cs'
MODELS='implementation/p09/tools/test-crossref-existing-owner.cs'
FAILED='implementation/p09/evidence/p09-361-crossref-existing-owner394.v1.json'
BASE='implementation/p09/evidence/p09-361-crossref-preassigned-scope392.v1.json'


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'EXISTING_OWNER_RECOVERY_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_EXISTING_ROT_OWNER_RECOVERY',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_ROT_or_COM_queried=False,actual_x86_test_worker_and_CSharp_compiler=False,
        fixed_eight_executed=False,native_startup_qualified=False,Native011_executed=False,prior_Native_replayed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();scratch=c.ROOT/'target/p09-crossref-existing-owner-scratch-395'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'EXISTING_OWNER_UNIQUE_TEST_SCRATCH')
        q=a.AcceptanceReader(c.ROOT,guard.check);failed=r.compact.unpack(q.json(FAILED));before=r.compact.unpack(q.json(BASE))
        c.require(q.snapshots[FAILED]['sha256']=='3d952367e854432123aadc0a9e41bb51d90a823e4269a4321c1761650672d282'
            and failed['cleanup']and failed['fresh_inputs']==failed['final_fresh_hashes']==12 and failed['steps']==[]
            and failed['error_code']=='EXISTING_OWNER_HAS_NO_ACTIVATION_LAUNCH_LATE_ASSIGNMENT_DOCUMENT_OR_QUIT_CALLS','EXACT394_COMMENT_FALSE_POSITIVE_BEFORE_TESTS_RETAINED')
        old={p['path']:p for p in failed['source_pins']}
        for path in(CORE,MODELS,worker.TEST,'tools/p09/run_crossref_existing_owner.py'):
            c.require(q.pin(path)==old[path],'PRODUCTION_CSHARP_ALL21_TEST_BODIES_AND_ORIGINAL_FAILED_DRIVER_UNCHANGED')
        c.require(q.snapshots[BASE]['sha256']=='3387bf3b49a3e1cde216c668d961b5cab1130ced40502997dc358283637cfef8'
            and before['cleanup']and before['fresh_inputs']==before['final_fresh_hashes']==205,'EXACT392_PRIOR_SCOPE20_NOT_REPLAYED')
        pins={p['path']:p for p in before['source_pins']}
        for path in('tools/p09/crossref_preassigned_session_scope.py','tools/p09/crossref_native_startup.py','tools/p09/crossref_native_host_limits.py',
            'tools/p09/crossref_native_host_channel.py','implementation/p09/tools/sdk-baseline-owned-session.ps1','implementation/p09/tools/crossref-native-case-ports.ps1'):
            c.require(q.pin(path)==pins[path],'ORIGINAL_NATIVE_STARTUP_PORTS_AND_SCOPE_UNCHANGED')
        for path in(DRIVER,'tools/p09/crossref_existing_owner_test_runtime.py'):q.pin(path)
        core=q.text(CORE);models=q.text(MODELS);test=q.text(worker.TEST)
        # Match actual call-like syntax, not mentions in source comments. The
        # complete immutable source bytes remain pinned, no payload substitution.
        forbidden=r'\b(?:CoCreateInstance|GetTypeFromProgID|CreateInstance|BindToObject|CreateProcess\w*|TerminateProcess|AssignProcessToJobObject)\s*\(|\.(?:Quit|Open|SaveAs)\s*\('
        c.require(re.search(forbidden,core)is None,'NO_ACTIVATION_LAUNCH_LATE_ASSIGNMENT_DOCUMENT_OR_QUIT_CALL_SITES')
        c.require('ExistingOwner.Attach('not in models and 'NativeCatalog('not in models and '::Attach('not in test
            and 'GetRunningObjectTable'not in models and 'GetRunningObjectTable'not in test,'TEST_WORKER_NEVER_QUERIES_ACTUAL_ROT_OR_NATIVE_COM')
        block=test[test.index('$names=@('):test.index('    foreach ($name in $names)')]
        c.require(set(re.findall("'([a-z_]+)'",block))==worker.NAMES and len(worker.NAMES)==21,'EXACT21_COMPILED_CASE_IDENTITIES')
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        image=a.AcceptanceReader(worker.SHELL.parent,guard.check);image.pin(worker.SHELL.name)
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        print(json.dumps(dict(state='EXISTING_OWNER_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),new_compiled_models=20,actual_self_kernel_cases=1,no_actual_ROT_or_Hwp=True)),flush=True)
        row['actual_x86_test_worker_and_CSharp_compiler']=True;worker.run(guard,env,row)
        contents=list(scratch.iterdir());c.require(len(contents)<=32,'BOUNDED_COMPILER_SCRATCH_CONTENTS');row['retained_compiler_scratch_entries']=len(contents)
        image.finish();q.finish();guard.check(force=True);row.update(state='PASS_COMPILED_X86_EXISTING_OWNER_MODELS20_AND_KERNEL_SELF1_NOT_ACTUAL_ROT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,external_shell_final_hashes=image.final_fresh_hashes,
            next_work='resource_bound_worker_and_descriptor_protocol_owner_factory_integration_then_live_existing_ROT_attachment_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'EXISTING_OWNER_TEST_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:
                if image is not None:image.finish();row['external_shell_final_hashes']=image.final_fresh_hashes
                q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),external_shell_pins=[]if image is None else list(image.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','external_shell_final_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','safe_error_codes','cleanup')},'cases':len(s.get('tests',[])),
                'failed_cases':[name for name,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
