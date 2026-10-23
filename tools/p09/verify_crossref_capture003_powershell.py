"""489: fixed003 IO/probe/sidecar successor models, no entry wiring or Native."""
import hashlib,json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import resource_sample_table as layout
import character_detail_receipt as compiled_layout
import crossref_capture003_namespace as ns

SELF='tools/p09/verify_crossref_capture003_powershell.py'
OUTPUT='implementation/p09/evidence/p09-361-capture003-powershell489.v1.json'
BASE='implementation/p09/evidence/p09-361-capture003-namespace488.v1.json'
ROOT='implementation/p09/tools/'
MODEL=ROOT+'test-crossref-capture003-namespace.ps1'
PROFILE=ROOT+'crossref-capture003-namespace.ps1'
PS='C:/Windows/SysWOW64/WindowsPowerShell/v1.0/powershell.exe'
LIBS=('sdk-baseline-owned-session','crossref-owned-active-source','crossref-owned-artifact','crossref-save-reopen',
    'crossref-stage-probe','crossref-fixed-batch','crossref-canonical-runtime','crossref-preassigned-controller','crossref-native-case-ports',
    'inspect-crossref-worker-composition')
RECOVER=sys.argv[1:]==['--after-loader489']

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]in([],['--after-loader489']),'CAPTURE003_PS_CLOSED_MODE')
    output=OUTPUT.replace('489.v1','490.v1')if RECOVER else OUTPUT
    c.require(not(c.ROOT/output).exists(),'CAPTURE003_PS_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=shell=owned=capture=None
    row=dict(state='FAILED_CAPTURE003_POWERSHELL_NAMESPACE',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_ROT_or_Native_started=False,official249_replayed=False,old_namespace_or_native_attempts_replayed=False,
        new_native_generation_authorized=False,external003_entry_wired_or_ready=False,compiled488_tests_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);ns.require_absent(c.ROOT)
        paths={SELF,BASE,MODEL,PROFILE,ns.PROBE}|{ROOT+name+'.ps1'for name in LIBS}
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':paths.add(path.relative_to(c.ROOT).as_posix())
        for path in sorted(paths):q.pin(path)
        if RECOVER:
            failed=layout.unpack(q.json(OUTPUT))
            c.require(q.snapshots[OUTPUT]['sha256']=='fcf21a32c95a2fedbf5251e234c170847f29c653fa5f29479a21f42b7c56b570'
                and failed['cleanup']is True and failed['final_fresh_hashes']==0,'EXACT489_FAILURE_NOT_REPLACED_BY_PASS')
            archive='implementation/p09/source-archive/p361-capture003-namespace488/'
            for current,saved in((SELF,'runner489.py'),(MODEL,'models489.ps1'),(PROFILE,'namespace489.ps1')):
                pin=next(p for p in failed['source_pins']if p['path']==current);archived=q.pin(archive+saved)
                c.require((pin['bytes'],pin['sha256'])==(archived['bytes'],archived['sha256']),'EXACT489_ORIGINAL_CODE_ARCHIVED')
            for pin in failed['source_pins']:
                if pin['path']not in(SELF,MODEL,PROFILE):c.require(q.pin(pin['path'])==pin,'UNCHANGED_ORIGINAL489_RUNTIME_AND_COMPILED_INPUTS')
            row.update(original489_failure_and_missing_final_closure_preserved=True,loader_change_affects_all_five_ps_groups=True)
        c.require(q.snapshots[BASE]['sha256']=='37478f268b133a9995a686696e4f51b019da36605af269be21dceaa09cf3fd03','EXACT_COMPILED003_PROBE488')
        proof=compiled_layout.unpack(q.json(BASE))
        c.require(proof['cleanup']is True and proof['fresh_inputs']==proof['final_fresh_hashes']==732
            and proof['fixed003_binary']==q.snapshots[ns.PROBE],'SAME_EXACT_CURRENT_BINARY_NOT_A_NATIVE_PERMIT')
        for pin in proof['source_pins']:
            if pin['path']in('crates/product-cli/examples/p09_crossref_discovery_probe.rs','crates/product-cli/examples/p09_crossref_capture003_probe.rs'):
                c.require(q.pin(pin['path'])==pin,'COMPILED003_PROBE_SOURCE_UNCHANGED')
        profile=q.text(PROFILE)
        originals=dict(re.findall(r"'(crossref-[a-z-]+\.ps1)'='([0-9a-f]{64})'",profile))
        c.require(len(originals)==6,'EXACT_SIX_FROZEN_INPUT_FILES')
        for name,sha in originals.items():c.require(q.snapshots[ROOT+name]['sha256']==sha,'FROZEN_NAMESPACE_ORIGINAL_BYTES_MATCH')
        c.require(proof['fixed003_binary']['sha256']in profile and str(proof['fixed003_binary']['bytes'])in profile
            and 'p09-361-crossref-bookmark-native-20261021-g003-c'in profile,'CROSS_LANGUAGE_FIXED_NAMESPACE_AND_PIN_MATCH')
        expected=set(re.findall(r'test (capture003_namespace::[A-Za-z0-9_]+) \.\.\. ok',q.text(MODEL)))
        c.require(len(expected)==5,'FIVE_NEW_NAMESPACE_PS_GROUPS')
        shell=a.AcceptanceReader(Path(PS).parent,guard.check);shell.pin(Path(PS).name)
        step=dict(stage='capture003_powershell_paths_lease_and_original_boundaries',cleanup=False);row['steps'].append(step)
        child_started=time.monotonic()
        try:
            owned=shared.OwnedSQLJobProcess([PS,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(c.ROOT/MODEL),'-ModelsOnly'],
                windows=guard.windows,allowed_executables=[PS],cwd=c.ROOT,checkpoint=guard.check,env=r.audit.environment())
            capture=shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
            while True:
                guard.check();c.require(time.monotonic()-child_started<90,'STOP_CAPTURE003_PS_MODEL_DEADLINE')
                try:stdout,stderr=capture.communicate(timeout=.5);owned.observe();break
                except subprocess.TimeoutExpired:capture.progress();owned.observe()
            tests=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',stdout)
            step.update(exit_code=owned.returncode,tests=tests,closed_model_errors=re.findall(r'(?m)^Error: (P09_XREF_BIND_[A-Z_]+)\r?$',stdout),
                closed_model_locations=re.findall(r'(?m)^Diagnostic: ([a-z_]+):([A-Za-z]{1,80}):([0-9]+)\r?$',stdout),
                stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest())
            c.require(owned.returncode==0 and not stderr and len(tests)==5 and {n for n,s in tests}==expected and all(s=='ok'for n,s in tests),'EXACT_FIVE_NAMESPACE_GROUPS_NO_SKIPS')
        finally:
            if owned is not None:
                owned.kill();owned.wait(timeout=2)
                if capture is not None:capture.close()
                owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
            step['elapsed_seconds']=round(time.monotonic()-child_started,3)
        ns.require_absent(c.ROOT);shell.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_FIXED003_PS7_EXACT_FUNCTION_SUCCESSORS_40_PATHS_AND_BINARY_LEASE_NOT_NATIVE_OR_ENTRY_READY',
            readonly_namespace_groups=5,whole_function_inverse_successors=7,fixed_artifact_paths=40,external_shell_final_fresh_hashes=shell.final_fresh_hashes,
            original_owner_source_document_io_and_batch_core_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'CAPTURE003_PS_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,output,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cases=len(s.get('tests',[])),errors=s.get('closed_model_errors',[]),locations=s.get('closed_model_locations',[]),cleanup=s['cleanup'])for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
