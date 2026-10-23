"""Bounded current ROT-name diagnostic only. No Native/session worker, GetObject, activation or retry."""
import hashlib,json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import resource_sample_table as layout
DRIVER='tools/p09/inspect_crossref_rot_catalog.py'
SCRIPT='implementation/p09/tools/inspect-crossref-rot-catalog.ps1'
SOURCE='implementation/p09/tools/crossref-rot-catalog-inspection.cs'
ORIGINAL='implementation/p09/tools/crossref-existing-owner.cs'
OUTPUT='implementation/p09/evidence/p09-361-crossref-current-rot-catalog474.v1.json'
SHELL=Path(r'C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe')
NAMES={'empty','names_only','exact_limit','overflow','incomplete','invalid_name','null_name','release_failure'}
def main():
    c,a,shared=r.c,r.a,r.shared;owner=sys.argv[1:]==['--inspect-authorized-existing-29824-readonly']
    c.require(owner or sys.argv[1:]==['--inspect-current-names-only'],'ROT_CATALOG_FIXED_INSPECTION_ONLY')
    output='implementation/p09/evidence/p09-361-crossref-existing-owner-readonly475.v1.json'if owner else OUTPUT
    script='implementation/p09/tools/inspect-crossref-existing-owner-readonly.ps1'if owner else SCRIPT
    source='implementation/p09/tools/crossref-existing-owner-readback.cs'if owner else SOURCE
    c.require(not(c.ROOT/output).exists(),'ROT_CATALOG_IMMUTABLE_NO_REPLAY')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=owned=capture=None;started=time.monotonic();row=dict(state='FAILED_CURRENT_ROT_CATALOG_INSPECTION',own_cpu_selection=selection,
        GetObject_invoked=owner,activation_invoked=False,Hancom_started_or_closed=False,qualification_or_fixed_worker_started=False,
        document_or_permission_action_invoked=False,Native011_executed=False,fixed_eight_executed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);image=a.AcceptanceReader(SHELL.parent,guard.check)
        for path in(DRIVER,script,source,ORIGINAL):q.pin(path)
        c.require(q.snapshots[ORIGINAL]['sha256']=='92143ee252cb7c132bc819e24044e5b6dc0e9a17b9d3777575ab6b1ba8732733','ORIGINAL_ATTACH_AND_NO_ACTIVATION_POLICY_UNCHANGED')
        # Inspect implementation is separate from model methods (which must throw if Existing is called).
        code=q.text(source).split('    public static class CatalogReadbackModels {',1)[0]
        forbidden=('.BindToObject(','.Start(','.Kill(','.Quit(','.Open(','.Save(','.CreateInstance(','.GetTypeFromProgID(')
        if not owner:forbidden+=('.Existing(','.Read(','.Attach(','.InvokeMember(','.GetObject(')
        c.require(all(token not in code for token in forbidden),
            'CATALOG_ONLY_NEVER_OBJECT_READ_OR_ACTIVATION_OR_PROCESS_CONTROL')
        image.pin(SHELL.name);env=r.audit.environment();env['PYTHONDONTWRITEBYTECODE']='1'
        owned=shared.OwnedSQLJobProcess([str(SHELL),'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(c.ROOT/script),'-InspectExisting29824Only'if owner else'-ModelsAndCatalogOnly'],
            windows=guard.windows,allowed_executables=[str(SHELL)],cwd=c.ROOT,checkpoint=guard.check,env=env)
        capture=shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();c.require(time.monotonic()-started<60,'STOP_ROT_CATALOG_INSPECTION_DEADLINE')
            try:stdout,stderr=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        tests=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',stdout)
        rows=[json.loads(line)for line in stdout.splitlines()if line.startswith('{')]
        row.update(exit_code=owned.returncode,models=tests,stdout_bytes=len(stdout.encode()),stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
            stderr_bytes=len(stderr.encode()),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),observation=rows[-1]if len(rows)==1 else None)
        expected={'owner_readback::'+n for n in('closed_code','private_message_redacted','nested_hresult_only')}if owner else{'rot_catalog::'+n for n in NAMES}
        c.require(owned.returncode==0 and not stderr and len(tests)==len(expected) and {n for n,s in tests}==expected
            and all(s=='ok'for _,s in tests)and len(rows)==1,'ALL_EIGHT_MODELS_AND_ONE_CURRENT_CATALOG_OBSERVATION')
        observed=rows[0]
        if owner:c.require(observed['state'].startswith('OBSERVED_EXISTING_OWNER_')and observed['references_released']is True
            and observed['same_existing_kernel_process_after']is True and observed['expected_process_id']==29824
            and observed['activation_invoked']is False and observed['document_or_permission_action_invoked']is False,'CURRENT_READONLY_OWNER_OBSERVATION_AND_RELEASE_NO_ACTIVATION')
        else:c.require(observed['state']=='OBSERVED_CURRENT_ROT_NAMES_NOT_OWNER_OR_SESSION'and observed['enumeration_complete']is True
            and observed['catalog_released']is True and 0<=observed['candidate_names']<=observed['entries']<=256
            and observed['entries']==observed['candidate_names']+observed['other_names'],'EXACT_BOUNDED_CATALOG_COUNTS_AND_RELEASE')
        image.finish();q.finish();guard.check(force=True);row['state']='OBSERVED_EXISTING_OWNER_READONLY_DIAGNOSTIC_NOT_NATIVE_SESSION_OR_GATE'if owner else'OBSERVED_CURRENT_ROT_CATALOG_MODELS8_NO_OBJECT_OR_NATIVE_AUTHORITY'
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'ROT_CATALOG_FAILURE_NO_RAW_VALUES')
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();row.update(owned_job=owned.profile,owned_cleanup=owned.profile['cleanup_confirmed'])
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and row.get('owned_cleanup',owned is None),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            shell_pins=[]if image is None else list(image.snapshots.values()),shell_final_fresh_hashes=0 if image is None else image.final_fresh_hashes,resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,output,layout.pack(row),NS(require=c.require,exact=a.exact));print(json.dumps({**{k:v for k,v in row.items()if k not in('source_pins','shell_pins','resource_samples','owned_job')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('OBSERVED_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
