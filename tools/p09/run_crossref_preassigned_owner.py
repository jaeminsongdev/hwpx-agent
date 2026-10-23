"""400: original adapter compile1 and new managed lease/successor18 only; no Native/ROT/COM."""
import hashlib,json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r

OUTPUT='implementation/p09/evidence/p09-361-crossref-preassigned-owner400.v1.json'
DRIVER='tools/p09/run_crossref_preassigned_owner.py'
PREVIOUS='implementation/p09/evidence/p09-361-crossref-preassigned-host398.v1.json'
TEST='implementation/p09/tools/test-crossref-preassigned-owner.ps1'
SHELL=Path(r'C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe')
NAMES={'unowned_type_rejected','four_exact_inverse_ports','successor_install_keeps_original','original_p58_predicate_preserved',
    'descriptor_tick_not_cim_rounding','descriptor_authority_rejected','no_descriptor_rejected_before_attach',
    'lease_references_released_once','second_release_rejected','failed_release_retained_no_retry',
    'document_failure_still_disposes_lease','managed_lease_never_com_authority','canonical_proxy_preserves_cim',
    'canonical_one_tick_mismatch_rejected','case_cleanup_retains_unverified_owner','case_cleanup_no_second_quit',
    'completion_keeps_cleanup_failure','reopen_failure_does_not_inherit_closed_latch'}
NEW={DRIVER,TEST,'implementation/p09/tools/crossref-preassigned-owner.ps1',
    'implementation/p09/tools/crossref-preassigned-case-ports.ps1','implementation/p09/tools/test-crossref-preassigned-owner.cs'}
DUAL='implementation/p09/tools/crossref-dual-owner-identity.ps1'


def run_worker(guard,env,row,mode,names,summary):
    c=r.c;owned=capture=None;started=last=time.monotonic();step=dict(stage=mode,cleanup=False);row['steps'].append(step)
    try:
        owned=r.shared.OwnedSQLJobProcess([str(SHELL),'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(c.ROOT/TEST),mode],
            windows=guard.windows,allowed_executables=[str(SHELL)],cwd=c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();c.require(time.monotonic()-started<90,'STOP_PREASSIGNED_OWNER_READONLY_TEST_DEADLINE')
            try:stdout,stderr=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:
                capture.progress();account=owned.observe()
                if time.monotonic()-last>=15:
                    sample=guard.samples[-1];print(json.dumps(dict(stage=mode,elapsed=round(time.monotonic()-started,1),
                        system_CPU=sample['system_cpu_percent'],available_RAM_percent=sample['available_ram_percent'],
                        job_private_percent=account['peak_job_private_percent'])),flush=True);last=time.monotonic()
        tests=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',stdout)
        step.update(exit_code=owned.returncode,tests=tests,stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
            safe_error_codes=re.findall(r'(?m)^Error: ((?:P09_XREF_[A-Z0-9_]{1,120})|CS[0-9]{4})\r?$',stdout+stderr),summary_observed=summary in stdout)
        c.require(step['exit_code']==0,'PREASSIGNED_OWNER_READONLY_WORKER_FAILED')
        c.require(len(tests)==len(names)and {name for name,status in tests}=={'preassigned_owner::'+n for n in names}
            and all(status=='ok'for name,status in tests)and step['summary_observed']and not stderr,
            'EXACT_NEW_PREASSIGNED_OWNER_CASES_NO_SKIPS')
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'PREASSIGNED_OWNER400_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_PREASSIGNED_OWNER400',steps=[],own_cpu_selection=selection,
        actual_Hangul_ROT_COM_or_native_started=False,readonly_x86_compile_and_managed_lease_tests_only=True,
        fixed_eight_executed=False,native_startup_qualified=False,Native011_executed=False,prior_Native_replayed=False,
        old_tests_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);previous=r.compact.unpack(q.json(PREVIOUS))
        c.require(q.snapshots[PREVIOUS]['sha256']=='93e045b3f74cf3e555d356a54cb265922c13e1ad0be02bc10fec09ddf0dd84f1'
            and previous['state'].startswith('PASS_')and previous['cleanup']and previous['fresh_inputs']==previous['final_fresh_hashes']==205,
            'EXACT398_PROTOCOL_PIPE_EVIDENCE_PRESERVED_NOT_REEXECUTED')
        for pin in previous['source_pins']:c.require(q.pin(pin['path'])==pin,'ALL_ORIGINAL_PROTOCOL_NATIVE_ADAPTER_AND_EVIDENCE_INPUTS_UNCHANGED')
        for path in sorted(NEW):q.pin(path)
        c.require(q.pin(DUAL)['sha256']=='af7ad1a1b0cf652e92bc0552a0ac603779f0592a359d32fd71795e8cb6e8766f','ORIGINAL_DUAL_KERNEL_CIM_IDENTITY_UNCHANGED')
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        image=a.AcceptanceReader(SHELL.parent,guard.check);image.pin(SHELL.name)
        scratch=c.ROOT/'target/p09-crossref-preassigned-owner-scratch-400'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'PREASSIGNED_OWNER_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        print(json.dumps(dict(state='PREASSIGNED_OWNER400_PREFLIGHT',inputs=len(q.snapshots),compile_initialization=1,new_managed_and_port_models=18,actual_native=False)),flush=True)
        run_worker(guard,env,row,'-InitializeOnly',{'actual_adapter_initialize_idempotent'},
            '1 passed; 0 failed; 0 ignored; compile_only_not_ROT_COM_or_Native')
        run_worker(guard,env,row,'-ModelsOnly',NAMES,
            '18 passed; 0 failed; 0 ignored; managed_leases_ports_only_not_ROT_COM_or_Native')
        entries=list(scratch.iterdir());c.require(len(entries)<=32,'PREASSIGNED_OWNER_BOUNDED_SCRATCH_CONTENTS');row['retained_compiler_scratch_entries']=len(entries)
        image.finish();q.finish();guard.check(force=True);row.update(state='PASS_EXISTING_ADAPTER_INIT1_PREASSIGNED_LEASE_PORT_MODELS18_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,external_shell_final_hashes=image.final_fresh_hashes,
            next_work='bounded_one_percent_worker_fixed_eight_controller_and_live_existing_owner_session_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'PREASSIGNED_OWNER_FAILURE_NO_RAW_VALUES')
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
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','safe_error_codes','cleanup')},'cases':len(s.get('tests',[]))}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
