"""402: exact parameter preservation; remaining11/affected1/new1, preserve prior8; no Native."""
import hashlib,json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r

OUTPUT='implementation/p09/evidence/p09-361-crossref-preassigned-owner-parameters402.v1.json'
DRIVER='tools/p09/run_crossref_preassigned_owner_parameters.py'
FAILED='implementation/p09/evidence/p09-361-crossref-preassigned-owner-recovery401.v1.json'
ORIGINAL='implementation/p09/evidence/p09-361-crossref-preassigned-owner400.v1.json'
PORTS='implementation/p09/tools/crossref-preassigned-case-ports.ps1'
TEST='implementation/p09/tools/test-crossref-preassigned-owner-recovery.ps1'
SHELL=Path(r'C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe')
NAMES={'successor_install_keeps_original','body_only_external_parameters_preserved','lease_references_released_once',
    'second_release_rejected','failed_release_retained_no_retry','document_failure_still_disposes_lease','managed_lease_never_com_authority',
    'canonical_proxy_preserves_cim','canonical_one_tick_mismatch_rejected','case_cleanup_retains_unverified_owner',
    'case_cleanup_no_second_quit','completion_keeps_cleanup_failure','reopen_failure_does_not_inherit_closed_latch'}

def run_worker(guard,env,row):
    c=r.c;owned=capture=None;started=last=time.monotonic();step=dict(stage='remaining11_affected_installation1_parameter1',cleanup=False);row['steps'].append(step)
    try:
        owned=r.shared.OwnedSQLJobProcess([str(SHELL),'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(c.ROOT/TEST),'-PostParameterFixOnly'],
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
            summary_observed='13 passed; 0 failed; 0 ignored; remaining11_affected1_parameters1_not_ROT_COM_or_Native'in stdout)
        c.require(step['exit_code']==0,'PREASSIGNED_OWNER_RECOVERY_WORKER_FAILED')
        c.require(len(tests)==13 and {name for name,status in tests}=={'preassigned_owner::'+n for n in NAMES}
            and all(status=='ok'for name,status in tests)and step['summary_observed']and not stderr,'EXACT13_REMAINING_AFFECTED_INSTALLATION_AND_PARAMETER_CASES')
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)


def restored_ports(text):
    addition="""        $inner=$body.Substring(1,$body.Length-2)
        # Function f($State) has parameters on the function AST, not in Body.
        # Preserve them explicitly when installing a body-only ScriptBlock.
        if ($null -ne $newNodes[0].Parameters -and $newNodes[0].Parameters.Count -gt 0) {
            $parameters=@($newNodes[0].Parameters | ForEach-Object {$_.Extent.Text})
            $inner='param('+($parameters -join ',')+")\u0060n"+$inner
        }
"""
    r.c.require(text.count(addition)==1,'ONE_BODY_ONLY_PORT_PARAMETER_FIX')
    return text.replace(addition,'').replace('inner=$inner;rewrites=$rules[$name]','inner=$body.Substring(1,$body.Length-2);rewrites=$rules[$name]')


def restored_test(text):
    current="""        $inner=$body.Substring(1,$body.Length-2)
        if ($null -ne $nodes[0].Parameters -and $nodes[0].Parameters.Count -gt 0) {
            $parameters=@($nodes[0].Parameters | ForEach-Object {$_.Extent.Text})
            $inner='param('+($parameters -join ',')+")\u0060n"+$inner
        }
        Set-Item -Path ('Function:global:'+$name) -Value ([scriptblock]::Create($inner))"""
    old="        Set-Item -Path ('Function:global:'+$name) -Value ([scriptblock]::Create($body.Substring(1,$body.Length-2)))"
    block="""    if ($PostParameterFixOnly) {
        # Recheck only the affected installation assertion from the old prefix.
        $before=(Get-Command Invoke-P09XrefNativeCaseStep).ScriptBlock.ToString()
        Initialize-P09XrefPreassignedCasePorts
        $definitions=@(Get-P09XrefPreassignedPortDefinitions)
        foreach ($d in $definitions) {Assert-P09XrefBinding ((Get-Command $d.name).ScriptBlock.ToString() -ceq $d.inner) 'PREASSIGNED_MODEL_EXACT_SUCCESSOR'}
        Assert-P09XrefBinding ($before -ceq (Get-Command Invoke-P09XrefNativeCaseStep).ScriptBlock.ToString()) 'PREASSIGNED_MODEL_ORIGINAL_UNCHANGED'
        [Console]::WriteLine('test preassigned_owner::successor_install_keeps_original ... ok')
        foreach ($name in @('Close-P09XrefPreassignedCaseOwner','Complete-P09XrefPreassignedCasePorts','New-PreassignedModelOwner')) {
            $block=(Get-Command $name).ScriptBlock
            Assert-P09XrefBinding ($null -ne $block.Ast.ParamBlock -and $block.Ast.ParamBlock.Parameters.Count -eq 1) 'PREASSIGNED_BODY_ONLY_PARAMETER_PRESERVED'
        }
        [Console]::WriteLine('test preassigned_owner::body_only_external_parameters_preserved ... ok')
    } else {
"""
    c=r.c;c.require(text.count(current)==text.count(block)==1,'ONE_TEST_HELPER_PARAMETER_FIX_AND_TWO_AFFECTED_CASES')
    text=text.replace(current,old).replace(block,'')
    text=text.replace("param([switch]$RemainingModelsOnly,[switch]$PostParameterFixOnly)","param([switch]$RemainingModelsOnly)")
    text=text.replace("if (($RemainingModelsOnly -and $PostParameterFixOnly) -or (-not $RemainingModelsOnly -and -not $PostParameterFixOnly))","if (-not $RemainingModelsOnly)")
    marker="    [Console]::WriteLine('test preassigned_owner::powershell_new_factory_name_collision ... ok')\n"
    c.require(text.count(marker+"    }\n")==1,'DIAGNOSTIC_BRANCH_CLOSED')
    text=text.replace(marker+"    }\n",marker)
    old_summary="    [Console]::WriteLine('test result: ok. 12 passed; 0 failed; 0 ignored; remaining_models_and_diagnostic_not_ROT_COM_or_Native')"
    new_summary="""    if ($PostParameterFixOnly) {[Console]::WriteLine('test result: ok. 13 passed; 0 failed; 0 ignored; remaining11_affected1_parameters1_not_ROT_COM_or_Native')}
    else {[Console]::WriteLine('test result: ok. 12 passed; 0 failed; 0 ignored; remaining_models_and_diagnostic_not_ROT_COM_or_Native')}"""
    c.require(text.count(new_summary)==1,'ONE_EXACT_POST_PARAMETER_FIX_SUMMARY')
    return text.replace(new_summary,old_summary)


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'PREASSIGNED_OWNER402_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_PREASSIGNED_OWNER_PARAMETERS402',steps=[],own_cpu_selection=selection,
        actual_Hangul_ROT_COM_or_native_started=False,readonly_x86_models_only=True,fixed_eight_executed=False,native_startup_qualified=False,
        Native011_executed=False,prior_Native_replayed=False,unaffected_successful_tests_replayed=False,affected_installation_reexecuted=True,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=r.compact.unpack(q.json(FAILED));original=r.compact.unpack(q.json(ORIGINAL))
        c.require(q.snapshots[FAILED]['sha256']=='4bd2ae17387612ab3c4c2a1fe5c9a043460755e3dfe0023c27f3ad4b033eb017'
            and failed['state']=='FAILED_PREASSIGNED_OWNER_RECOVERY401'and failed['cleanup']
            and failed['fresh_inputs']==failed['final_fresh_hashes']==215 and len(failed['steps'])==1
            and failed['steps'][0]['tests']==[['preassigned_owner::powershell_new_factory_name_collision','ok']]
            and failed['steps'][0]['exit_code']==2,'ORIGINAL401_FAILURE_AND_CONFIRMED_NEW_FACTORY_COLLISION_NOT_RELABELED_PASS')
        c.require(q.snapshots[ORIGINAL]['sha256']=='f9837ab547368eeb016b7426252d1678ce0700a6d8d2ff88533e157971108737'
            and original['cleanup']and original['fresh_inputs']==original['final_fresh_hashes']==212
            and original['steps'][0]['exit_code']==0 and len(original['steps'][0]['tests'])==1
            and len(original['steps'][1]['tests'])==7 and all(s=='ok'for n,s in original['steps'][1]['tests'])
            and original['steps'][1]['exit_code']==2,'ORIGINAL400_INIT_AND_PREFIX_EVIDENCE_PRESERVED')
        pins={p['path']:p for p in failed['source_pins']}
        for path,pin in sorted(pins.items()):
            if path not in(PORTS,TEST):c.require(q.pin(path)==pin,'ALL_OTHER_PRODUCTION_OWNER_ADAPTER_V2_AND_TEST_INPUTS_UNCHANGED')
        r.audit.inverse(restored_ports(q.text(PORTS)),pins[PORTS],'ONLY_EXPLICIT_FUNCTION_PARAMETERS_ADDED_TO_BODY_INSTALLATION')
        r.audit.inverse(restored_test(q.text(TEST)),pins[TEST],'ONLY_HELPER_PARAMETERS_AND_TWO_AFFECTED_CASES_DIAGNOSTIC_BRANCH_CHANGED')
        q.pin(DRIVER)
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        image=a.AcceptanceReader(SHELL.parent,guard.check);image.pin(SHELL.name)
        scratch=c.ROOT/'target/p09-crossref-preassigned-owner-scratch-402'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'PREASSIGNED_OWNER402_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        print(json.dumps(dict(state='PREASSIGNED_OWNER402_PREFLIGHT',inputs=len(q.snapshots),preserved_successes=8,remaining_models=11,affected_installation=1,new_parameter_case=1)),flush=True)
        run_worker(guard,env,row)
        entries=list(scratch.iterdir());c.require(len(entries)<=32,'PREASSIGNED_OWNER402_BOUNDED_SCRATCH');row['retained_compiler_scratch_entries']=len(entries)
        image.finish();q.finish();guard.check(force=True);row.update(state='PASS_PRESERVED8_REMAINING11_AFFECTED_INSTALL1_PARAMETER1_NOT_NATIVE_OR_GATE',
            current_distinct_cases=21,preserved_successful_cases=8,new_current_cases=13,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,external_shell_final_hashes=image.final_fresh_hashes,
            next_work='bounded_one_percent_worker_fixed_eight_controller_then_live_existing_owner_session_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'PREASSIGNED_OWNER_PARAMETERS_FAILURE_NO_RAW_VALUES')
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

