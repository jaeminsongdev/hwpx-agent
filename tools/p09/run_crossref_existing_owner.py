"""394: compile actual x86 C# adapter;20 new models + self-kernel1, never ROT/COM/Hwp."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r

OUTPUT='implementation/p09/evidence/p09-361-crossref-existing-owner394.v1.json'
DRIVER='tools/p09/run_crossref_existing_owner.py'
CORE='implementation/p09/tools/crossref-existing-owner.cs'
MODELS='implementation/p09/tools/test-crossref-existing-owner.cs'
TEST='implementation/p09/tools/test-crossref-existing-owner.ps1'
BASE='implementation/p09/evidence/p09-361-crossref-preassigned-scope392.v1.json'
DOCS='implementation/p09/evidence/p09-361-crossref-preassigned-scope-sync393.v1.json'
SHELL=Path(r'C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe')
NAMES={'name_family','name_bound','one_exact_owner','no_owner_no_fallback','duplicate_owners','incomplete_enumeration',
    'pid_mismatch','session_mismatch','birth_one_tick_mismatch','image_mismatch','version_mismatch','window_required',
    'window_changed_after_scan','exact_enum_limit','enum_overflow_not_first_match','get_object_missing','catalog_cleanup_failure',
    'invalid_expected_identity','unknown_names_never_get_objects','lease_close_once','stable_kernel_self_not_hancom'}


def test_worker(guard,env,row):
    c,shared=r.c,r.shared;owned=capture=None;started=last=time.monotonic();step=dict(stage='compiled_x86_ROT_models20_and_actual_kernel_self1',cleanup=False)
    row['steps'].append(step)
    try:
        args=[str(SHELL),'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(c.ROOT/TEST),'-ModelsAndSelfOnly']
        owned=shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[str(SHELL)],cwd=c.ROOT,checkpoint=guard.check,env=env)
        capture=shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();c.require(time.monotonic()-started<90,'STOP_ROT_READONLY_TEST_COMMAND_DEADLINE')
            try:
                stdout,stderr=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:
                capture.progress();account=owned.observe()
                if time.monotonic()-last>=15:
                    sample=guard.samples[-1]
                    print(json.dumps(dict(stage=step['stage'],elapsed=round(time.monotonic()-started,1),system_CPU=sample['system_cpu_percent'],
                        available_RAM_percent=sample['available_ram_percent'],job_private_percent=account['peak_job_private_percent'],job_cpu_seconds=account['job_cpu_seconds'])),flush=True)
                    last=time.monotonic()
        step.update(exit_code=owned.returncode,stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
            tests=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)$',stdout),
            safe_error_codes=re.findall(r'(?m)^Error: ((?:P09_XREF_ROT_[A-Z_]{1,120})|CS[0-9]{4})\r?$',stdout+stderr),
            summary_observed='21 passed; 0 failed; 0 ignored; models_and_self_only_not_ROT_or_Native'in stdout)
        expected={'rot_existing::'+name for name in NAMES}
        c.require(step['exit_code']==0,'ROT_COMPILED_TEST_WORKER_FAILED')
        c.require(len(step['tests'])==21 and {name for name,status in step['tests']}==expected
            and all(status=='ok'for name,status in step['tests'])and step['summary_observed']and not step['safe_error_codes'],'EXACT21_COMPILED_MODELS_AND_SELF_CASES_NO_SKIPS')
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'EXISTING_OWNER_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_EXISTING_ROT_OWNER_TESTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_ROT_or_COM_queried=False,actual_x86_test_worker_and_CSharp_compiler=True,
        fixed_eight_executed=False,native_startup_qualified=False,Native011_executed=False,prior_Native_replayed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();scratch=c.ROOT/'target/p09-crossref-existing-owner-scratch-394'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'EXISTING_OWNER_UNIQUE_TEST_SCRATCH')
        q=a.AcceptanceReader(c.ROOT,guard.check);before=r.compact.unpack(q.json(BASE));docs=r.compact.unpack(q.json(DOCS))
        c.require(q.snapshots[BASE]['sha256']=='3387bf3b49a3e1cde216c668d961b5cab1130ced40502997dc358283637cfef8'
            and before['cleanup']and before['fresh_inputs']==before['final_fresh_hashes']==205
            and before['contracts']==dict(run=20,errors=0,failures=0,skipped=0),'EXACT392_PRIOR_SCOPE20_NOT_REPLAYED')
        c.require(q.snapshots[DOCS]['sha256']=='7845bd371cbea3c46929195a0e90966b9ffabb285a10d7a1b282cd40be0f27c9'
            and docs['cleanup']and docs['fresh_inputs']==docs['final_fresh_hashes']==16,'EXACT393_PREVIOUS_SCOPE_DOCS')
        for path in(DRIVER,CORE,MODELS,TEST):q.pin(path)
        pins={p['path']:p for p in before['source_pins']}
        for path in('tools/p09/crossref_preassigned_session_scope.py','tools/p09/crossref_native_startup.py','tools/p09/crossref_native_host_limits.py',
            'tools/p09/crossref_native_host_channel.py','implementation/p09/tools/sdk-baseline-owned-session.ps1','implementation/p09/tools/crossref-native-case-ports.ps1'):
            c.require(q.pin(path)==pins[path],'ALL_ORIGINAL_NATIVE_STARTUP_CASE_PORTS_AND_VERIFIED_SCOPE_UNCHANGED')
        core=q.text(CORE);models=q.text(MODELS);test=q.text(TEST)
        c.require(len(core.encode())<=64*1024 and len(models.encode())<=64*1024 and len(test.encode())<=16*1024,'BOUNDED_NEW_CSHARP_AND_TEST_INPUTS')
        for forbidden in('CoCreateInstance','GetTypeFromProgID','CreateInstance','BindToObject','CreateProcess','TerminateProcess','AssignProcessToJobObject','\.Quit(','.Open(','.SaveAs('):
            c.require(forbidden not in core,'EXISTING_OWNER_HAS_NO_ACTIVATION_LAUNCH_LATE_ASSIGNMENT_DOCUMENT_OR_QUIT_CALLS')
        c.require('ExistingOwner.Attach('not in models and 'NativeCatalog('not in models and '::Attach('not in test
            and 'GetRunningObjectTable'not in models and 'GetRunningObjectTable'not in test,'TEST_WORKER_NEVER_QUERIES_ACTUAL_ROT_OR_NATIVE_COM')
        block=test[test.index('$names=@('):test.index('    foreach ($name in $names)')]
        c.require(set(re.findall("'([a-z_]+)'",block))==NAMES and len(NAMES)==21,'EXACT_NEW21_COMPILED_CASE_IDENTITIES_BEFORE_LAUNCH')
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        image=a.AcceptanceReader(SHELL.parent,guard.check);image.pin(SHELL.name)
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        print(json.dumps(dict(state='EXISTING_OWNER_PREFLIGHT',inputs=len(q.snapshots),new_compiled_models=20,actual_self_kernel_cases=1,no_actual_ROT_or_Hwp=True)),flush=True)
        test_worker(guard,env,row)
        contents=list(scratch.iterdir());c.require(len(contents)<=32,'BOUNDED_COMPILER_SCRATCH_CONTENTS');row['retained_compiler_scratch_entries']=len(contents)
        image.finish();q.finish();guard.check(force=True);row.update(state='PASS_COMPILED_X86_EXISTING_OWNER_MODELS20_AND_KERNEL_SELF1_NOT_ACTUAL_ROT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,external_shell_final_hashes=image.final_fresh_hashes,
            next_work='resource_bound_worker_and_descriptor_protocol_owner_factory_integration_then_live_existing_ROT_attachment_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'EXISTING_OWNER_TEST_FAILURE_NO_RAW_VALUES')
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
