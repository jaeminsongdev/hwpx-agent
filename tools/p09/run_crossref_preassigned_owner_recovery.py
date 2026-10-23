"""401: preserve400 init1/prefix7; new diagnostic1 + remaining11, no success replay."""
import hashlib,json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r

OUTPUT='implementation/p09/evidence/p09-361-crossref-preassigned-owner-recovery401.v1.json'
DRIVER='tools/p09/run_crossref_preassigned_owner_recovery.py'
FAILED='implementation/p09/evidence/p09-361-crossref-preassigned-owner400.v1.json'
PS='implementation/p09/tools/test-crossref-preassigned-owner.ps1'
CS='implementation/p09/tools/test-crossref-preassigned-owner.cs'
TEST='implementation/p09/tools/test-crossref-preassigned-owner-recovery.ps1'
SHELL=Path(r'C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe')
PREFIX={'unowned_type_rejected','four_exact_inverse_ports','successor_install_keeps_original','original_p58_predicate_preserved',
    'descriptor_tick_not_cim_rounding','descriptor_authority_rejected','no_descriptor_rejected_before_attach'}
NAMES={'powershell_new_factory_name_collision','lease_references_released_once','second_release_rejected',
    'failed_release_retained_no_retry','document_failure_still_disposes_lease','managed_lease_never_com_authority',
    'canonical_proxy_preserves_cim','canonical_one_tick_mismatch_rejected','case_cleanup_retains_unverified_owner',
    'case_cleanup_no_second_quit','completion_keeps_cleanup_failure','reopen_failure_does_not_inherit_closed_latch'}


def run_worker(guard,env,row):
    c=r.c;owned=capture=None;started=last=time.monotonic();step=dict(stage='remaining_lease_ports11_and_new_name_collision1',cleanup=False);row['steps'].append(step)
    try:
        owned=r.shared.OwnedSQLJobProcess([str(SHELL),'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(c.ROOT/TEST),'-RemainingModelsOnly'],
            windows=guard.windows,allowed_executables=[str(SHELL)],cwd=c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();c.require(time.monotonic()-started<90,'STOP_PREASSIGNED_OWNER_RECOVERY_READONLY_DEADLINE')
            try:stdout,stderr=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:
                capture.progress();account=owned.observe()
                if time.monotonic()-last>=15:
                    sample=guard.samples[-1];print(json.dumps(dict(stage=step['stage'],elapsed=round(time.monotonic()-started,1),
                        system_CPU=sample['system_cpu_percent'],available_RAM_percent=sample['available_ram_percent'],
                        job_private_percent=account['peak_job_private_percent'])),flush=True);last=time.monotonic()
        tests=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',stdout)
        step.update(exit_code=owned.returncode,tests=tests,stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
            safe_error_codes=re.findall(r'(?m)^Error: ((?:P09_XREF_[A-Z0-9_]{1,120})|CS[0-9]{4})\r?$',stdout+stderr),
            summary_observed='12 passed; 0 failed; 0 ignored; remaining_models_and_diagnostic_not_ROT_COM_or_Native'in stdout)
        c.require(step['exit_code']==0,'PREASSIGNED_OWNER_RECOVERY_WORKER_FAILED')
        c.require(len(tests)==12 and {name for name,status in tests}=={'preassigned_owner::'+n for n in NAMES}
            and all(status=='ok'for name,status in tests)and step['summary_observed']and not stderr,'EXACT12_REMAINING_AND_DIAGNOSTIC_NO_PREFIX_REPLAY')
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'PREASSIGNED_OWNER401_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_PREASSIGNED_OWNER_RECOVERY401',steps=[],own_cpu_selection=selection,
        actual_Hangul_ROT_COM_or_native_started=False,readonly_x86_managed_models_and_diagnostic_only=True,
        fixed_eight_executed=False,native_startup_qualified=False,Native011_executed=False,prior_Native_replayed=False,
        old_successful_tests_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=r.compact.unpack(q.json(FAILED))
        c.require(q.snapshots[FAILED]['sha256']=='f9837ab547368eeb016b7426252d1678ce0700a6d8d2ff88533e157971108737'
            and failed['state']=='FAILED_PREASSIGNED_OWNER400'and failed['cleanup']and failed['fresh_inputs']==failed['final_fresh_hashes']==212
            and len(failed['steps'])==2,'ORIGINAL400_FAILURE_NOT_RELABELED_PASS')
        init,prefix=failed['steps'];c.require(init['exit_code']==0 and init['tests']==[['preassigned_owner::actual_adapter_initialize_idempotent','ok']]
            and len(prefix['tests'])==7 and {n for n,s in prefix['tests']}=={'preassigned_owner::'+n for n in PREFIX}
            and all(s=='ok'for n,s in prefix['tests'])and prefix['exit_code']==2 and init['cleanup']and prefix['cleanup'],
            'EXACT400_INIT1_PREFIX7_PRESERVED_CURRENT_NOT_RERUN')
        pins={p['path']:p for p in failed['source_pins']}
        for path,pin in sorted(pins.items()):
            if path not in(PS,CS):c.require(q.pin(path)==pin,'ALL_PRODUCTION_ORIGINAL_ADAPTER_PORT_AND_GUARD_INPUTS_UNCHANGED')
        for path in(PS,CS):
            text=q.text(path);c.require(text.count('CreateLease')==1,'ONE_FACTORY_RENAME_PER_TEST_SOURCE')
            r.audit.inverse(text.replace('CreateLease','New'),pins[path],'ONLY_TEST_FACTORY_NAME_FIX_NO_CHANGED_PREVIOUS_EIGHT_CONTRACTS')
        q.pin(TEST);q.pin(DRIVER)
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        image=a.AcceptanceReader(SHELL.parent,guard.check);image.pin(SHELL.name)
        scratch=c.ROOT/'target/p09-crossref-preassigned-owner-scratch-401'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'PREASSIGNED_OWNER401_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        print(json.dumps(dict(state='PREASSIGNED_OWNER401_PREFLIGHT',inputs=len(q.snapshots),preserved_successes=8,remaining_models=11,new_diagnostic=1)),flush=True)
        run_worker(guard,env,row)
        entries=list(scratch.iterdir());c.require(len(entries)<=32,'PREASSIGNED_OWNER401_BOUNDED_SCRATCH');row['retained_compiler_scratch_entries']=len(entries)
        image.finish();q.finish();guard.check(force=True);row.update(state='PASS_PRESERVED_INIT1_PREFIX7_NEW_DIAGNOSTIC1_REMAINING11_NOT_NATIVE_OR_GATE',
            current_distinct_cases=20,preserved_successful_cases=8,new_current_cases=12,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,external_shell_final_hashes=image.final_fresh_hashes,
            next_work='bounded_one_percent_worker_fixed_eight_controller_then_live_existing_owner_session_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'PREASSIGNED_OWNER_RECOVERY_FAILURE_NO_RAW_VALUES')
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
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','current_distinct_cases','preserved_successful_cases','new_current_cases','fresh_inputs','final_fresh_hashes','external_shell_final_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','safe_error_codes','cleanup')},'cases':len(s.get('tests',[]))}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
